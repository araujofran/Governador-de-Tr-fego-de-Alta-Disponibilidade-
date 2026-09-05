import pytest
from retry_manager import RetryManager

def test_full_jitter_bounds():
    retry_mgr = RetryManager(base_delay=1.0, max_delay=10.0)
    
    for attempt in range(1, 5):
        delay = retry_mgr.calculate_jitter_delay(attempt)
        max_possible = min(10.0, 1.0 * (2 ** attempt))
        assert 0.0 <= delay <= max_possible

def test_retry_after_header_override():
    retry_mgr = RetryManager(base_delay=1.0, max_delay=10.0)
    
    delay = retry_mgr.calculate_jitter_delay(attempt=1, retry_after_header="4.5s")
    assert delay >= 4.5
