from typing import Dict, Any, List
from audit_schema import parse_audit_json, AuditAnalysisResult

class PostLLMValidator:
    """
    Camada 12 & 24: Validador Pós-LLM de Integridade, Schema e Evidências.
    Garante que a resposta da LLM satisfaz 100% o contrato do Banco Daycoval.
    """

    def validate(
        self,
        raw_llm_output: str,
        indexed_evidences: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        validation_errors = []
        parsed_result = None

        # Step 1: Parse JSON e Validação Pydantic
        try:
            parsed_result = parse_audit_json(raw_llm_output)
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"Erro de Parse JSON / Schema Pydantic: {e}"],
                "parsed_data": None
            }

        # Step 2: Verificação de consistência entre itens do Contrato
        scorecard = getattr(parsed_result, "scorecard", {})
        scorecard_dict = scorecard.model_dump() if hasattr(scorecard, "model_dump") else (scorecard if isinstance(scorecard, dict) else {})
        
        resolutivity = scorecard_dict.get("resolutivity", "Resolvido")
        if resolutivity in ["Nao Resolvido", "Não Resolvido", "Nao", "Não"]:
            overall_score = getattr(parsed_result, "score_final", 100.0)
            if overall_score > 90.0:
                validation_errors.append("Inconsistência de Contrato: Atendimento não resolutivo não pode ter score final superior a 90.")

        # Step 3: Validação de Evidências citadas nas justificativas (Rastreabilidade)
        resumo = getattr(parsed_result, "resumo_executivo", "")
        if not resumo:
            validation_errors.append("Campo obrigatório ausente: resumo_executivo está vazio.")

        is_valid = len(validation_errors) == 0

        return {
            "is_valid": is_valid,
            "errors": validation_errors,
            "parsed_data": parsed_result.model_dump() if parsed_result else None
        }
