import time
import json
import asyncio
import random
import logging
from typing import Optional, Dict, Any
import httpx

from base_provider import BaseLLMProvider, ProviderResult
from audit_schema import AuditAnalysisResult

logger = logging.getLogger("TrafficController.GeminiProvider")

class GeminiRateLimitException(Exception):
    def __init__(self, message: str, status_code: int = 429, headers: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.headers = headers or {}

class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = True):
        self.api_key = api_key
        self.mock_mode = mock_mode or not api_key
        self._mock_remaining_tokens = 10000
        self._mock_remaining_requests = 60
        self._last_mock_reset = time.time()
        self._sem = asyncio.Semaphore(2)

    @property
    def name(self) -> str:
        return "Gemini"

    async def process_transcription(
        self,
        transcription_id: str,
        text: str,
        model: Optional[str] = None
    ) -> ProviderResult:
        model = model or "gemini-3.6-flash"
        start_time = time.time()

        if self.mock_mode:
            if start_time - self._last_mock_reset >= 1.8:
                self._mock_remaining_tokens = 10000
                self._mock_remaining_requests = 60
                self._last_mock_reset = start_time

            await asyncio.sleep(random.uniform(0.05, 0.15))
            duration = time.time() - start_time

            input_tokens = len(text.split()) * 2
            output_tokens = random.randint(120, 350)

            self._mock_remaining_tokens = max(0, self._mock_remaining_tokens - (input_tokens + output_tokens))
            self._mock_remaining_requests = max(0, self._mock_remaining_requests - 1)

            headers = {
                "x-ratelimit-remaining-tokens": str(self._mock_remaining_tokens),
                "x-ratelimit-remaining-requests": str(self._mock_remaining_requests),
                "x-ratelimit-reset-tokens": "1.8s",
                "x-ratelimit-reset-requests": "0.8s"
            }

            score = random.choice([96.0, 91.0, 84.0, 72.0, 98.0])
            risk_level = "Baixo" if score >= 85 else "Médio"
            mock_audit = AuditAnalysisResult(
                numero_protocolo=f"PROT-{random.randint(100000, 999999)}",
                nome_operador="Atendente Gemini",
                nome_cliente="Cliente Banco Engineer AI",
                resumo_executivo=f"Auditoria realizada via Gemini 3.6 Flash. Transcrição de {len(text.split())} palavras analisada com sucesso.",
                classificacao_atendimento="Consulta Financeira",
                score_final=score,
                justificativa_score="Aderência técnica aos manuais operacionais do banco."
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

        # Real API request mode
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{
                "parts": [{"text": f"Responda estritamente em JSON válido compatível com o contrato de auditoria:\n\n{text}"}]
            }],
            "generationConfig": {
                "responseMimeType": "application/json",
                "maxOutputTokens": 1000
            }
        }

        async with self._sem:
            async with httpx.AsyncClient() as client:
                res = await client.post(endpoint, json=payload, timeout=35.0)
            duration = time.time() - start_time
            res_headers = dict(res.headers)

            if res.status_code == 429:
                raise GeminiRateLimitException("Gemini API Rate Limit Exceeded", status_code=429, headers=res_headers)

            res.raise_for_status()
            data = res.json()

            usage = data.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", len(text.split()))
            output_tokens = usage.get("candidatesTokenCount", 150)

            candidates = data.get("candidates", [])
            output_text = ""
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts:
                    output_text = parts[0].get("text", "")

            return ProviderResult(
                transcription_id=transcription_id,
                output_text=output_text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                headers=res_headers,
                status_code=res.status_code,
                duration_sec=duration
            )
