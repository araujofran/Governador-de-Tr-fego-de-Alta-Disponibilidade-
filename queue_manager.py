import os
import json
import asyncio
import logging
import hashlib
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union

from tokenizer import TokenizerManager
from rate_limiter import DynamicRateLimiter, MultiProviderRateLimiter
from concurrency_manager import ConcurrencyManager
from retry_manager import RetryManager
from base_provider import BaseLLMProvider, ProviderResult
from telemetry import TelemetryTracker
from preprocessor import TextPreprocessor
from evidence_engine import EvidenceEngine
from data_quality import DataQualityAnalyzer
from context_builder import ContextBuilder
from job_queue_db import JobQueueDB
from validator_post_llm import PostLLMValidator
from finops_engine import FinOpsEngine
from audit_schema import AuditAnalysisResult, parse_audit_json
from database import AuditDatabase

logger = logging.getLogger("TrafficController.QueueManager")

@dataclass
class TranscriptionTask:
    task_id: str
    filename: str
    text: str
    clean_text: str
    masked_pii_count: int
    expected_output_tokens: int = 500
    chunk_index: int = 0
    total_chunks: int = 1

class BatchQueueProcessor:
    """
    Producer-Consumer Queue Manager (Python First -> Database -> LLM Last).
    Orquestra as 13 camadas do pipeline: Ingestão, Normalização, Regex, Evidence Engine,
    Data Quality, Persistência SQLite Pre-LLM, Context Builder, Token Estimator,
    Rate Limiter, LLM Worker, Validador Pós-LLM e Persistência Final.
    """
    def __init__(
        self,
        provider: Union[BaseLLMProvider, List[BaseLLMProvider]],
        rate_limiter: Union[DynamicRateLimiter, MultiProviderRateLimiter],
        concurrency_manager: ConcurrencyManager,
        retry_manager: RetryManager,
        telemetry: TelemetryTracker,
        database: Optional[AuditDatabase] = None,
        tokenizer: Optional[TokenizerManager] = None,
        max_chunk_tokens: int = 2500
    ):
        if isinstance(provider, list):
            self.providers = provider
        else:
            self.providers = [provider]

        self.rate_limiter_obj = rate_limiter
        if isinstance(rate_limiter, MultiProviderRateLimiter):
            self.multi_rate_limiter = rate_limiter
        else:
            self.multi_rate_limiter = MultiProviderRateLimiter({
                p.name: rate_limiter for p in self.providers
            })

        self.concurrency_manager = concurrency_manager
        self.retry_manager = retry_manager
        self.telemetry = telemetry
        self.database = database or AuditDatabase()
        self.tokenizer = tokenizer or TokenizerManager()
        self.preprocessor = TextPreprocessor()
        self.evidence_engine = EvidenceEngine()
        self.quality_analyzer = DataQualityAnalyzer()
        self.context_builder = ContextBuilder()
        self.job_queue_db = JobQueueDB(self.database.db_path)
        self.post_validator = PostLLMValidator()
        self.finops_engine = FinOpsEngine()
        self.max_chunk_tokens = max_chunk_tokens

        # Load system prompt rules contract
        self.contract_prompt = self._load_contract_prompt()
        self.results: List[ProviderResult] = []
        self._provider_rr_index = 0
        self._lock = asyncio.Lock()

    def _load_contract_prompt(self) -> str:
        contract_path = r"C:\Users\fferr\Desktop\projetoRATE\contratoRegrasOuro\1-promptAnaliseAtendimentos.txt"
        if os.path.exists(contract_path):
            try:
                with open(contract_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Could not read contract prompt: {e}")
        return "Você é um Especialista Sênior em Auditoria de Atendimento do Banco Daycoval. Analise a transcrição com base estrita no texto."

    def add_transcriptions(self, raw_tasks: List[Dict[str, str]]):
        """
        Executa as CAMADAS 1 A 7 (PYTHON FIRST):
        Ingestão, Normalização, Regex, Evidências, Data Quality e Persistência no SQLite antes de qualquer chamada à LLM.
        """
        processed_count = 0
        for idx, item in enumerate(raw_tasks):
            filename = item.get("filename", f"transcription_{idx+1:03d}.txt")
            t_id = item.get("id", filename)
            raw_text = item.get("text", "")
            file_hash = hashlib.sha256(raw_text.encode('utf-8')).hexdigest()

            # Camada 2: Normalização Python & Indexação de Linhas
            preprocessed = self.preprocessor.preprocess(raw_text)

            # Camada 3 & 5: Extração Regex & Evidence Engine
            evidences = self.evidence_engine.extract_evidences(t_id, preprocessed.lines)

            # Camada 6: Data Quality & Scoring
            dq_metrics = self.quality_analyzer.analyze(preprocessed.clean_text, preprocessed.lines)

            # Camada 7: Persistência no Banco SQLite Pré-LLM
            self.database.save_python_preprocessing(
                atendimento_id=t_id,
                filename=filename,
                file_hash=file_hash,
                raw_text=raw_text,
                norm_text=preprocessed.clean_text,
                evidences=evidences,
                data_quality=dq_metrics
            )

            # Camada 8: Context Builder (Mínimo Contexto Orientado a Evidências)
            payload = self.context_builder.build_payload(
                atendimento_id=t_id,
                filename=filename,
                lines=preprocessed.lines,
                evidences=evidences,
                data_quality=dq_metrics,
                contract_prompt=self.contract_prompt,
                max_context_words=self.max_chunk_tokens
            )

            # Camada 9: Token Estimator
            full_prompt_payload = f"{self.contract_prompt}\n\nEVIDÊNCIAS INDEXADAS:\n{json.dumps(payload['evidences_indexed'], ensure_ascii=False)}\n\nTRANSCRIÇÃO:\n{payload['formatted_transcript']}"
            estimated_tokens = self.tokenizer.estimate_request_budget(full_prompt_payload, expected_output_tokens=500)

            # Camada 10: Criar Job na Fila DB Persistente
            self.job_queue_db.create_job(
                atendimento_id=t_id,
                filename=filename,
                file_hash=file_hash,
                payload_json=payload,
                estimated_input_tokens=estimated_tokens
            )
            processed_count += 1

        logger.info(f"[QueueManager] Python First completed: {processed_count} atendimentos processados e salvos no SQLite.")

    async def _select_provider_and_limiter(self, estimated_tokens: int):
        async with self._lock:
            candidate_providers = [
                self.providers[(self._provider_rr_index + i) % len(self.providers)]
                for i in range(len(self.providers))
            ]
            self._provider_rr_index = (self._provider_rr_index + 1) % len(self.providers)

        # Se for payload grande (>5000 tokens), priorizar Gemini/OpenRouter que suportam contexto longo
        if estimated_tokens > 5000:
            large_context_candidates = [p for p in candidate_providers if p.name.lower() != "groq"]
            if large_context_candidates:
                candidate_providers = large_context_candidates

        chosen = self.multi_rate_limiter.find_best_available_provider(candidate_providers, estimated_tokens)
        limiter = self.multi_rate_limiter.get_limiter(chosen.name)
        return chosen, limiter

    async def _worker(self, worker_id: int):
        while True:
            # Reservar atómicamente o próximo job pendente da Fila DB
            job = self.job_queue_db.claim_next_job()
            if not job:
                break
            
            job_id = job["job_id"]
            atendimento_id = job["atendimento_id"]
            payload = job["payload"]

            full_prompt_payload = f"{payload.get('contract_prompt', self.contract_prompt)}\n\nEVIDÊNCIAS INDEXADAS:\n{json.dumps(payload.get('evidences_indexed', []), ensure_ascii=False)}\n\nTRANSCRIÇÃO:\n{payload.get('formatted_transcript', '')}"
            estimated_tokens = job.get("estimated_input_tokens", 3000)

            # Provider failover loop
            success = False
            last_exception = None

            # Get ordered candidate providers starting from round-robin index
            async with self._lock:
                providers_to_try = [
                    self.providers[(self._provider_rr_index + i) % len(self.providers)]
                    for i in range(len(self.providers))
                ]
                self._provider_rr_index = (self._provider_rr_index + 1) % len(self.providers)

            if estimated_tokens > 5000:
                large_candidates = [p for p in providers_to_try if p.name.lower() != "groq"]
                if large_candidates:
                    providers_to_try = large_candidates

            for provider in providers_to_try:
                target_limiter = self.multi_rate_limiter.get_limiter(provider.name)
                if not target_limiter:
                    target_limiter = DynamicRateLimiter(QuotaLimits(), provider_name=provider.name)
                
                await target_limiter.acquire(estimated_tokens)

                async with self.concurrency_manager:
                    snapshot = target_limiter.get_snapshot()
                    await self.telemetry.update_limits_state(
                        rem_rpm=snapshot.rpm_remaining,
                        rem_tpm=snapshot.tpm_remaining,
                        rpm_reset=snapshot.rpm_reset_in_sec,
                        tpm_reset=snapshot.tpm_reset_in_sec,
                        active_workers=self.concurrency_manager.active_count,
                        status=f"Worker-{worker_id} [{provider.name}] {job['filename']}",
                        provider_name=provider.name
                    )

                    async def _call():
                        return await provider.process_transcription(
                            transcription_id=atendimento_id,
                            text=full_prompt_payload
                        )

                    def _on_retry(attempt: int, exc: Exception, delay: float):
                        asyncio.create_task(
                            self.telemetry.record_retry(attempt, str(exc), delay)
                        )

                    try:
                        self.retry_manager.rate_limiter = target_limiter

                        result: ProviderResult = await self.retry_manager.execute_with_retry(
                            _call,
                            on_retry_callback=_on_retry
                        )

                        if result.headers:
                            await target_limiter.update_from_headers(result.headers)

                        actual_tokens = result.input_tokens + result.output_tokens
                        await target_limiter.adjust_actual_tokens(estimated_tokens, actual_tokens)

                        # Camada 12: Validador Pós-LLM (Schema Pydantic + Inconsistências de Contrato)
                        val_res = self.post_validator.validate(result.output_text, payload.get("evidences_indexed", []))
                        if not val_res["is_valid"]:
                            logger.warning(f"Validation error for {job_id}: {val_res['errors']}")
                            self.job_queue_db.update_job_status(job_id, "VALIDATION_ERROR", error_message="; ".join(val_res["errors"]))
                            await self.telemetry.record_failure(job_id, "; ".join(val_res["errors"]))
                            success = True
                            break

                        audit_dict = val_res["parsed_data"]

                        # Camada 13: Persistência Final no SQLite (Retrocompatível + Métricas de Tokens)
                        telemetry_dict = {
                            "provider_used": provider.name,
                            "input_tokens": result.input_tokens,
                            "output_tokens": result.output_tokens,
                            "latency_sec": result.duration_sec,
                            "masked_pii_count": 0,
                            "status_code": result.status_code
                        }
                        self.database.save_audit(
                            task_id=atendimento_id,
                            filename=job["filename"],
                            audit_data=audit_dict,
                            telemetry_data=telemetry_dict
                        )

                        # Camada FinOps: Calcular custos comerciais e gravar no banco
                        finops_res = self.finops_engine.calculate_cost(
                            provider=provider.name,
                            model=getattr(provider, 'model_name', 'gemini-3.6-flash'),
                            input_tokens=result.input_tokens,
                            output_tokens=result.output_tokens,
                            is_free_tier=True
                        )
                        finops_res.atendimento_id = atendimento_id
                        self.database.save_llm_usage(finops_res, job_id=job_id)

                        self.job_queue_db.update_job_status(job_id, "SUCCESS")

                        # Record Telemetry Success com dados de Provider e FinOps
                        await self.telemetry.record_success(
                            input_tokens=result.input_tokens,
                            output_tokens=result.output_tokens,
                            duration_sec=result.duration_sec,
                            provider=provider.name,
                            model=getattr(provider, 'model_name', 'gemini-3.6-flash')
                        )

                        async with self._lock:
                            self.results.append(result)

                        success = True
                        break

                    except Exception as exc:
                        last_exception = exc
                        logger.warning(f"[Worker-{worker_id}] Provider {provider.name} failed for {job_id}: {exc}. Trying next provider...")

            if not success:
                err_msg = str(last_exception) if last_exception else "All providers failed"
                self.job_queue_db.update_job_status(job_id, "FAILED", error_message=err_msg)
                await self.telemetry.record_failure(job_id, err_msg)

    async def run(self, num_workers: int = 15):
        workers = [asyncio.create_task(self._worker(i+1)) for i in range(num_workers)]
        await asyncio.gather(*workers, return_exceptions=True)
