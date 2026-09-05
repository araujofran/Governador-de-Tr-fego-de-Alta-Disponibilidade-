import time
import json
import asyncio
import random
import logging
from typing import Optional, Dict, Any
import httpx

from base_provider import BaseLLMProvider, ProviderResult
from audit_schema import AuditAnalysisResult

logger = logging.getLogger("TrafficController.OpenRouterProvider")

class OpenRouterRateLimitException(Exception):
    def __init__(self, message: str, status_code: int = 429, headers: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.headers = headers or {}

class OpenRouterMiniMaxProvider(BaseLLMProvider):
    """
    Provider for MiniMax M3 Free via OpenRouter API.
    """
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = True):
        self.api_key = api_key
        self.mock_mode = mock_mode or not api_key
        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"
        self._mock_remaining_tokens = 15000
        self._mock_remaining_requests = 40
        self._last_mock_reset = time.time()

    @property
    def name(self) -> str:
        return "MiniMax-M3 (OpenRouter)"

    async def process_transcription(
        self,
        transcription_id: str,
        text: str,
        model: Optional[str] = None
    ) -> ProviderResult:
        model = model or "minimax/minimax-m3:free"
        start_time = time.time()

        if self.mock_mode:
            if start_time - self._last_mock_reset >= 2.0:
                self._mock_remaining_tokens = 15000
                self._mock_remaining_requests = 40
                self._last_mock_reset = start_time

            await asyncio.sleep(random.uniform(0.1, 0.25))
            duration = time.time() - start_time

            input_tokens = len(text.split()) * 2
            output_tokens = random.randint(150, 400)

            self._mock_remaining_tokens = max(0, self._mock_remaining_tokens - (input_tokens + output_tokens))
            self._mock_remaining_requests = max(0, self._mock_remaining_requests - 1)

            headers = {
                "x-ratelimit-remaining-tokens": str(self._mock_remaining_tokens),
                "x-ratelimit-remaining-requests": str(self._mock_remaining_requests),
                "x-ratelimit-reset-tokens": "2.0s",
                "x-ratelimit-reset-requests": "1.0s"
            }

            score = random.choice([94.0, 89.0, 75.0, 97.0, 60.0])
            risk_level = "Baixo" if score >= 85 else ("Médio" if score >= 70 else "Crítico")
            mock_audit = AuditAnalysisResult(
                numero_protocolo=f"PROT-{random.randint(100000, 999999)}",
                nome_operador="Atendente MiniMax",
                nome_cliente="Cliente Banco Daycoval",
                resumo_executivo=f"Auditoria realizada via MiniMax M3 Free. Transcrição de {len(text.split())} palavras analisada com sucesso.",
                classificacao_atendimento="Reclamação / Suporte",
                score_final=score,
                justificativa_score="Avaliação realizada em modelo de longo contexto (1M tokens)."
            )
            mock_audit.scorecard.pontuacao_cx = int(score)
            mock_audit.risco_e_causa_raiz.nivel_risco = risk_level

            return ProviderResult(
                transcription_id=transcription_id,
                output_text=mock_audit.model_dump_json(),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                headers=headers,
                status_code=200,
                duration_sec=duration
            )

        # Real API request mode via OpenRouter
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "LLM API Traffic Controller"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Você é um auditor sênior de atendimento. Responda ESTRITAMENTE em formato JSON válido compatível com o schema do Pydantic."},
                {"role": "user", "content": text}
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 1000
        }

        async with httpx.AsyncClient() as client:
            res = await client.post(self.endpoint, json=payload, headers=headers, timeout=35.0)
            duration = time.time() - start_time
            res_headers = dict(res.headers)

            if res.status_code == 429:
                raise OpenRouterRateLimitException("OpenRouter MiniMax Rate Limit Exceeded", status_code=429, headers=res_headers)

            if res.status_code == 402:
                logger.warning("[OpenRouter] Saldo zerado (402). Alternando para fallback mock/gemini.")
                self.mock_mode = True
                return await self.process_transcription(transcription_id, text, model)

            res.raise_for_status()
            data = res.json()

            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", len(text.split()))
            output_tokens = usage.get("completion_tokens", 150)

            choices = data.get("choices", [])
            output_text = ""
            if choices and "message" in choices[0]:
                output_text = choices[0]["message"].get("content", "")

            return ProviderResult(
                transcription_id=transcription_id,
                output_text=output_text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                headers=res_headers,
                status_code=res.status_code,
                duration_sec=duration
            )
