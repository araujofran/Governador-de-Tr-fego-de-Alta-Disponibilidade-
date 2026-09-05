import pytest
from context_builder import ContextBuilder
from evidence_engine import Evidence

def test_context_builder_preserves_evidences():
    builder = ContextBuilder()
    lines = [
        {"line_number": i, "speaker": "ATENDENTE" if i % 2 == 0 else "CLIENTE", "text": f"Linha de teste {i}"}
        for i in range(1, 50)
    ]
    ev = Evidence("EV_001", "AT_01", "CPF", "123.456.789-00", "CLIENTE", 25, 25, "Trecho", "REGEX", 0.99)
    
    payload = builder.build_payload(
        atendimento_id="AT_01",
        filename="test.txt",
        lines=lines,
        evidences=[ev],
        data_quality={"score": 100},
        contract_prompt="PROMPT",
        max_context_words=2000
    )

    assert payload["atendimento_id"] == "AT_01"
    assert len(payload["evidences_indexed"]) == 1
    assert "formatted_transcript" in payload
