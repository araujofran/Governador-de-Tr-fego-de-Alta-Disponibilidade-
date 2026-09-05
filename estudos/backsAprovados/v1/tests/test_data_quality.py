import pytest
from data_quality import DataQualityAnalyzer

def test_data_quality_valid_text():
    analyzer = DataQualityAnalyzer()
    text = "Cliente solicita informação sobre saldo de contrato. Atendente confirma dados e passa informação."
    lines = [
        {"line_number": 1, "speaker": "ATENDENTE", "text": "Bom dia!"},
        {"line_number": 2, "speaker": "CLIENTE", "text": "Quero meu saldo."}
    ]
    res = analyzer.analyze(text, lines)
    assert res["score"] > 50
    assert res["is_valid"] is True

def test_data_quality_empty_text():
    analyzer = DataQualityAnalyzer()
    res = analyzer.analyze("", [])
    assert res["score"] == 0
    assert res["is_valid"] is False
    assert "EMPTY_TRANSCRIPTION" in res["flags"]
