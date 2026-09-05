import random
import asyncio
import logging
from typing import Callable, Awaitable, Any, Dict, Optional
from rate_limiter import parse_time_duration, DynamicRateLimiter

logger = logging.getLogger("TrafficController.RetryManager")

class RetryManager:
    """
    Handles exponential backoff with Full Jitter and Retry-After header compliance.
    Only retries transient errors (HTTP 429, 5xx, timeouts). Permanent errors (404, 401, 403) fail fast.
    """
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        rate_limiter: Optional[DynamicRateLimiter] = None
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.rate_limiter = rate_limiter

    def calculate_jitter_delay(self, attempt: int, retry_after_header: Optional[str] = None, is_rate_limit: bool = False) -> float:
        exp_backoff = min(self.max_delay, self.base_delay * (2 ** attempt))
        full_jitter_delay = random.uniform(self.base_delay if is_rate_limit else 0, exp_backoff)

        if retry_after_header:
            server_delay = parse_time_duration(retry_after_header)
            if server_delay > 0:
                logger.info(f"[RetryManager] Respecting Retry-After header: {server_delay:.2f}s")
                return max(full_jitter_delay, server_delay)

        if is_rate_limit:
            # Enforce a minimum delay for rate limit errors to avoid rapid exhaustion
            min_rate_limit_delay = min(self.max_delay, max(3.0, self.base_delay * (attempt * 2)))
            return max(full_jitter_delay, min_rate_limit_delay)

        return full_jitter_delay

    async def execute_with_retry(
        self,
        request_func: Callable[[], Awaitable[Any]],
        on_retry_callback: Optional[Callable[[int, Exception, float], None]] = None
    ) -> Any:
        attempt = 0
        while True:
            try:
                return await request_func()
            except Exception as exc:
                status_code = getattr(exc, "status_code", None)
                if hasattr(exc, "response") and hasattr(exc.response, "status_code"):
                    status_code = exc.response.status_code

                # Do NOT retry non-transient client errors (401, 403, 404)
                if status_code in (401, 403, 404):
                    logger.error(f"[RetryManager] Non-retryable HTTP {status_code} error: {exc}")
                    raise exc

                attempt += 1
                if attempt > self.max_retries:
                    logger.error(f"[RetryManager] Request failed after {self.max_retries} attempts: {exc}")
                    raise exc

                headers = getattr(exc, "headers", {}) or {}
                if hasattr(exc, "response") and hasattr(exc.response, "headers"):
                    headers = dict(exc.response.headers)

                retry_after_val = headers.get("retry-after") or headers.get("Retry-After")

                if status_code == 429:
                    logger.warning(f"[RetryManager] HTTP 429 Rate Limit hit (Attempt {attempt}/{self.max_retries})")
                    if self.rate_limiter and headers:
                        await self.rate_limiter.update_from_headers(headers)

                delay = self.calculate_jitter_delay(attempt, retry_after_val, is_rate_limit=(status_code == 429))

                if on_retry_callback:
                    on_retry_callback(attempt, exc, delay)

                await asyncio.sleep(delay)
