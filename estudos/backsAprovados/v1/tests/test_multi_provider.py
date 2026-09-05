import pytest
import os
from key_loader import KeyLoader
from provider_openrouter import OpenRouterMiniMaxProvider
from rate_limiter import QuotaLimits, DynamicRateLimiter, MultiProviderRateLimiter

def test_key_loader_reads_chaves_free():
    loader = KeyLoader()
    keys = loader.load_keys()
    
    assert keys.groq_api_key is not None
    assert keys.gemini_api_key is not None
    assert keys.openrouter_api_key is not None

def test_multi_provider_limiter_failover():
    lim_groq = DynamicRateLimiter(QuotaLimits(rpm=1, tpm=100), provider_name="Groq")
    lim_gemini = DynamicRateLimiter(QuotaLimits(rpm=10, tpm=10000), provider_name="Gemini")
    
    multi = MultiProviderRateLimiter({
        "Groq": lim_groq,
        "Gemini": lim_gemini
    })

    # Exhaust Groq limit
    lim_groq.tpm_used = 100

    p_groq = type("MockP", (), {"name": "Groq"})()
    p_gemini = type("MockP", (), {"name": "Gemini"})()

    chosen = multi.find_best_available_provider([p_groq, p_gemini], estimated_tokens=500)
    assert chosen.name == "Gemini"
