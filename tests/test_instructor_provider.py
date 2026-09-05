"""
test_instructor_provider.py - Testes de unidade para o módulo InstructorProvider.
"""

import pytest
from instructor_provider import instructor_provider


def test_instructor_provider_fallback_graceful():
    res, meta = instructor_provider.generate_structured_audit(
        prompt="Teste de prompt",
        system_instruction="Sistema",
        model_name="modelo_inexistente_para_fallback"
    )
    # Deve retornar None ou objeto sem lançar exceção não capturada
    assert res is None or meta["error"] is not None
