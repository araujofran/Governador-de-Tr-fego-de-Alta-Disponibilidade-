import pytest
from tokenizer import TokenizerManager

def test_tokenizer_count():
    tok = TokenizerManager()
    text = "Hello world! This is a test transcription string."
    count = tok.count_tokens(text)
    assert count > 0

def test_smart_chunking():
    tok = TokenizerManager()
    long_text = "Paragraph one is here.\n\n" + ("Paragraph two has words. " * 300)
    chunks = tok.smart_chunk_text(long_text, max_chunk_tokens=100)
    
    assert len(chunks) > 1
    for chunk in chunks:
        assert tok.count_tokens(chunk) <= 150  # Reasonable boundary allowance
