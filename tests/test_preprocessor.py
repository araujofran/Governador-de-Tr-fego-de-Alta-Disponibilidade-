import pytest
from preprocessor import TextPreprocessor

def test_preprocessor_pii_masking():
    prep = TextPreprocessor()
    sample_text = "O cliente CPF 123.456.789-00 ligou do telefone (11) 98765-4321 com e-mail teste@bancodaycoval.com.br."
    
    result = prep.preprocess(sample_text)
    
    assert "[CPF_MASCARADO]" in result.clean_text
    assert "[EMAIL_MASCARADO]" in result.clean_text
    assert "[TELEFONE_MASCARADO]" in result.clean_text
    assert "123.456.789-00" not in result.clean_text
    assert result.masked_pii_count >= 3
