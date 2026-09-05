import pytest
import json
from validator_post_llm import PostLLMValidator

def test_post_llm_validator_success():
    validator = PostLLMValidator()
    raw_json = json.dumps({
        "identificacao_atendimento": {
            "nome_cliente": "Fulano",
            "nome_operador": "Atendente",
            "produto": "Consignado",
            "motivo_principal": "Saldo",
            "atendimento_resolutivo": "Sim"
        },
        "resumo_executivo": {
            "resumo_completo": "Cliente solicitou saldo e o atendente informou com clareza."
        },
        "classificacao_humor": {
            "humor_cliente": "Neutro",
            "humor_atendente": "Profissional"
        },
        "experiencia_cliente": {
            "nivel_esforco": "Baixo",
            "probabilidade_recontato": "Baixa",
            "potencial_ouvidoria": "Nao"
        },
        "scorecard": {
            "pontuacao_cx": 90,
            "pontuacao_qualidade_operador": 95,
            "pontuacao_tecnica": 90,
            "pontuacao_comportamental": 100,
            "score_final": 93.5,
            "justificativa_score": "Atendimento satisfatorio"
        },
        "risco_e_causa_raiz": {
            "nivel_risco": "Baixo",
            "riscos_identificados": [],
            "causa_raiz": "Nao identificado",
            "responsavel_problema": "Nao identificado",
            "citacao_evidencia": "Nenhuma"
        },
        "oportunidades": {
            "oportunidades_operador": [],
            "oportunidades_operacionais": []
        }
    })

    res = validator.validate(raw_json, [])
    assert res["is_valid"] is True
    assert res["parsed_data"] is not None
