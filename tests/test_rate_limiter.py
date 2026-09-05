import pytest
import asyncio
import time
from rate_limiter import QuotaLimits, DynamicRateLimiter

@pytest.mark.asyncio
async def test_rate_limiter_pre_flight_budget():
    limits = QuotaLimits(rpm=5, tpm=1000)
    limiter = DynamicRateLimiter(limits=limits)

    # Acquire 400 tokens (should succeed immediately)
    waited = await limiter.acquire(400)
    assert waited == 0.0
    
    snapshot = limiter.get_snapshot()
    assert snapshot.rpm_remaining == 4
    assert snapshot.tpm_remaining == 600

@pytest.mark.asyncio
async def test_rate_limiter_header_synchronization():
    limits = QuotaLimits(rpm=30, tpm=8000)
    limiter = DynamicRateLimiter(limits=limits)

    headers = {
        "x-ratelimit-remaining-tokens": "1200",
        "x-ratelimit-remaining-requests": "10",
        "x-ratelimit-reset-tokens": "5s"
    }

    await limiter.update_from_headers(headers)
    snapshot = limiter.get_snapshot()

    assert snapshot.tpm_remaining == 1200
    assert snapshot.rpm_remaining == 10
    assert snapshot.tpm_reset_in_sec <= 5.0
