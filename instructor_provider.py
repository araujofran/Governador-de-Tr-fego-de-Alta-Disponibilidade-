"""
instructor_provider.py - Provider de Saída Estruturada com Instructor e LiteLLM.

Força as LLMs (Groq, Gemini, MiniMax, OpenAI) a responderem garantidamente no
schema Pydantic `AuditAnalysisResult`, aplicando retentativas automáticas no nível da LLM.
"""

import logging
from typing import Optional, Tuple, Dict, Any

from audit_schema import AuditAnalysisResult, parse_audit_json

# Tentar importar Instructor e LiteLLM
try:
    import instructor
    import litellm
    HAS_INSTRUCTOR = True
except ImportError:
    HAS_INSTRUCTOR = False

logger = logging.getLogger("TrafficController.InstructorProvider")


class InstructorProvider:
    """Provider Especializado para Execução com Contrato Pydantic Rígido."""

    def __init__(self):
        self.active = HAS_INSTRUCTOR

    def generate_structured_audit(
        self,
        prompt: str,
        system_instruction: str,
        model_name: str = "groq/llama-3.3-70b-versatile",
        api_key: Optional[str] = None
    ) -> Tuple[Optional[AuditAnalysisResult], Dict[str, Any]]:
        """
        Gera uma análise de auditoria estruturada utilizando Instructor + LiteLLM.

        Returns:
            Tuple[Optional[AuditAnalysisResult], Dict[str, Any]]: (resultado_pydantic, telemetria)
        """
        telemetry = {
            "used_instructor": False,
            "model_name": model_name,
            "error": None
        }

        if not HAS_INSTRUCTOR:
            telemetry["error"] = "Instructor/LiteLLM não instalados."
            return None, telemetry

        try:
            # Patch LiteLLM com Instructor
            client = instructor.from_litellm(litellm.completion)

            response = client.chat.completions.create(
                model=model_name,
                api_key=api_key,
                response_model=AuditAnalysisResult,
                max_retries=2,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ]
            )

            telemetry["used_instructor"] = True
            return response, telemetry

        except Exception as e:
            logger.warning(f"Fallback Instructor -> Provider Padrão: {e}")
            telemetry["error"] = str(e)
            return None, telemetry


# Singleton Instance
instructor_provider = InstructorProvider()
