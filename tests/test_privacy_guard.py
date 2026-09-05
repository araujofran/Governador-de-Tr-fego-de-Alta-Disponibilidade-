"""
test_privacy_guard.py - Testes de unidade para o módulo PrivacyGuard (Microsoft Presidio & LGPD).
"""

import pytest
from privacy_guard import privacy_guard


def test_privacy_guard_cpf_anonymization():
    raw_text = "O cliente com CPF 123.456.789-00 solicitou cancelamento da conta agência 1234-5."
    sanitized, meta = privacy_guard.anonymize_transcript(raw_text)

    assert "123.456.789-00" not in sanitized
    assert "[CPF_MASCARADO]" in sanitized
    assert meta["pii_detected_count"] >= 1


def test_privacy_guard_phone_and_card():
    raw_text = "Ligue no telefone (11) 98765-4321 ou use o cartão 4111-2222-3333-4444."
    sanitized, meta = privacy_guard.anonymize_transcript(raw_text)

    assert "4111-2222-3333-4444" not in sanitized
    assert meta["pii_detected_count"] >= 1


def test_privacy_guard_empty_string():
    sanitized, meta = privacy_guard.anonymize_transcript("")
    assert sanitized == ""
    assert meta["pii_detected_count"] == 0
