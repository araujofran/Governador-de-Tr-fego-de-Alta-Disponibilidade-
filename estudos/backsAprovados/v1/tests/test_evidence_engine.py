import pytest
from evidence_engine import EvidenceEngine

def test_evidence_engine_extraction():
    engine = EvidenceEngine()
    lines = [
        {"line_number": 1, "speaker": "ATENDENTE", "text": "Banco Daycoval, bom dia! Como posso ajudar?"},
        {"line_number": 2, "speaker": "CLIENTE", "text": "Meu CPF é 123.456.789-00 e meu protocolo é 987654321."},
        {"line_number": 3, "speaker": "CLIENTE", "text": "Vou processar o banco no Procon e entrar com advogado por causa de R$ 1.500,00 reais."},
        {"line_number": 4, "speaker": "ATENDENTE", "text": "Sim, confirmo a solicitação de portabilidade."}
    ]

    evidences = engine.extract_evidences("TEST_001", lines)
    assert len(evidences) >= 4

    tipos = [e.tipo for e in evidences]
    assert "CPF" in tipos
    assert "PROTOCOLO" in tipos
    assert "VALOR_MONETARIO" in tipos
    assert "FRICCAO_OFENSIVA" in tipos
    assert "PORTABILIDADE" in tipos

    cpf_ev = next(e for e in evidences if e.tipo == "CPF")
    assert cpf_ev.valor == "123.456.789-00"
    assert cpf_ev.linha_inicio == 2
    assert cpf_ev.speaker == "CLIENTE"
