import time
import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

logger = logging.getLogger("TrafficController.RateLimiter")

def parse_time_duration(val: str) -> float:
    """Parses duration strings like '2m30s', '500ms', '4.2s', or plain floats into seconds."""
    if not val:
        return 0.0
    val_str = str(val).strip()
    try:
        return float(val_str)
    except ValueError:
        pass
    
    total_seconds = 0.0
    ms_match = re.search(r'(\d+(?:\.\d+)?)ms', val_str)
    if ms_match:
        total_seconds += float(ms_match.group(1)) / 1000.0
        val_str = re.sub(r'\d+(?:\.\d+)?ms', '', val_str)
    
    m_match = re.search(r'(\d+(?:\.\d+)?)m', val_str)
    if m_match:
        total_seconds += float(m_match.group(1)) * 60.0
        val_str = re.sub(r'\d+(?:\.\d+)?m', '', val_str)

    s_match = re.search(r'(\d+(?:\.\d+)?)s', val_str)
    if s_match:
        total_seconds += float(s_match.group(1))
        val_str = re.sub(r'\d+(?:\.\d+)?s', '', val_str)

    return total_seconds

@dataclass
class QuotaLimits:
    rpm: int = 30           # Requests Per Minute
    tpm: int = 8000         # Tokens Per Minute
    rpd: int = 14400        # Requests Per Day
    tpd: int = 1000000      # Tokens Per Day

@dataclass
class QuotaSnapshot:
    rpm_remaining: int
    tpm_remaining: int
    rpd_remaining: int
    tpd_remaining: int
    rpm_reset_in_sec: float
    tpm_reset_in_sec: float

class DynamicRateLimiter:
    """
    Governor adaptativo de API para um provedor específico.
    Pre-calculates token budgets before allowing requests through,
    and dynamically syncs with server response headers.
    """
    def __init__(self, limits: QuotaLimits, provider_name: str = "Default", safe_tpm_percentage: float = 1.0):
        self.limits = limits
        self.provider_name = provider_name
        self.safe_tpm_percentage = safe_tpm_percentage
        self._lock = asyncio.Lock()

        # Rolling window track state
        self.rpm_used = 0
        self.tpm_used = 0
        self.rpd_used = 0
        self.tpd_used = 0

        # Window reset timestamps (unix timestamps)
        now = time.time()
        self.minute_window_start = now
        self.day_window_start = now

        # Server overrides (if header feedback is received)
        self.server_remaining_tokens: Optional[int] = None
        self.server_remaining_requests: Optional[int] = None
        self.server_tokens_reset_at: Optional[float] = None
        self.server_requests_reset_at: Optional[float] = None

    def _refresh_windows(self, now: float):
        """Resets local rolling usage windows if minute/day boundaries have passed."""
        if self.server_tokens_reset_at and now >= self.server_tokens_reset_at:
            self.server_remaining_tokens = None
            self.server_tokens_reset_at = None

        if self.server_requests_reset_at and now >= self.server_requests_reset_at:
            self.server_remaining_requests = None
            self.server_requests_reset_at = None

        # Reset minute window
        if now - self.minute_window_start >= 60.0:
            self.minute_window_start = now
            self.rpm_used = 0
            self.tpm_used = 0
            self.server_remaining_tokens = None
            self.server_remaining_requests = None

        # Reset day window
        if now - self.day_window_start >= 86400.0:
            self.day_window_start = now
            self.rpd_used = 0
            self.tpd_used = 0

    def get_snapshot(self) -> QuotaSnapshot:
        now = time.time()
        self._refresh_windows(now)

        rem_rpm = max(0, self.limits.rpm - self.rpm_used)
        if self.server_remaining_requests is not None:
            rem_rpm = min(rem_rpm, self.server_remaining_requests)

        effective_tpm_limit = int(self.limits.tpm * self.safe_tpm_percentage)
        rem_tpm = max(0, effective_tpm_limit - self.tpm_used)
        if self.server_remaining_tokens is not None:
            rem_tpm = min(rem_tpm, int(self.server_remaining_tokens * self.safe_tpm_percentage))

        rem_rpd = max(0, self.limits.rpd - self.rpd_used)
        rem_tpd = max(0, self.limits.tpd - self.tpd_used)

        rpm_reset = max(0.1, 60.0 - (now - self.minute_window_start))
        if self.server_requests_reset_at and self.server_requests_reset_at > now:
            rpm_reset = self.server_requests_reset_at - now

        tpm_reset = max(0.1, 60.0 - (now - self.minute_window_start))
        if self.server_tokens_reset_at and self.server_tokens_reset_at > now:
            tpm_reset = self.server_tokens_reset_at - now

        return QuotaSnapshot(
            rpm_remaining=rem_rpm,
            tpm_remaining=rem_tpm,
            rpd_remaining=rem_rpd,
            tpd_remaining=rem_tpd,
            rpm_reset_in_sec=rpm_reset,
            tpm_reset_in_sec=tpm_reset
        )

    def can_consume_immediately(self, estimated_tokens: int) -> bool:
        """Returns True if request can fit immediately without pausing."""
        snapshot = self.get_snapshot()
        return (
            snapshot.rpm_remaining >= 1 and
            snapshot.tpm_remaining >= estimated_tokens and
            snapshot.rpd_remaining >= 1 and
            snapshot.tpd_remaining >= estimated_tokens
        )

    async def acquire(self, estimated_tokens: int) -> float:
        """
        Pre-flight check:
        Calculates if the request fits within remaining TPM/RPM window.
        If YES -> reserves budget immediately and proceeds.
        If NO  -> pauses execution asynchronously until quota window resets.
        """
        waited_total = 0.0

        while True:
            async with self._lock:
                now = time.time()
                self._refresh_windows(now)
                snapshot = self.get_snapshot()

                fits_rpm = snapshot.rpm_remaining >= 1
                fits_tpm = snapshot.tpm_remaining >= estimated_tokens
                fits_rpd = snapshot.rpd_remaining >= 1
                fits_tpd = snapshot.tpd_remaining >= estimated_tokens

                if fits_rpm and fits_tpm and fits_rpd and fits_tpd:
                    self.rpm_used += 1
                    self.tpm_used += estimated_tokens
                    self.rpd_used += 1
                    self.tpd_used += estimated_tokens
                    
                    if self.server_remaining_tokens is not None:
                        self.server_remaining_tokens = max(0, self.server_remaining_tokens - estimated_tokens)
                    if self.server_remaining_requests is not None:
                        self.server_remaining_requests = max(0, self.server_remaining_requests - 1)

                    return waited_total

                wait_time = 1.0
                if not fits_tpm:
                    wait_time = max(wait_time, snapshot.tpm_reset_in_sec)
                if not fits_rpm:
                    wait_time = max(wait_time, snapshot.rpm_reset_in_sec)

                logger.info(
                    f"[{self.provider_name} RateLimiter] Need {estimated_tokens} tokens, {snapshot.tpm_remaining} TPM left, {snapshot.rpm_remaining} RPM left. "
                    f"Pausing for {wait_time:.2f}s..."
                )

            await asyncio.sleep(wait_time)
            waited_total += wait_time

    async def update_from_headers(self, headers: Dict[str, Any]):
        if not headers:
            return

        async with self._lock:
            now = time.time()
            h = {k.lower(): str(v) for k, v in headers.items()}

            if 'x-ratelimit-remaining-tokens' in h:
                try:
                    rem_t = int(h['x-ratelimit-remaining-tokens'])
                    self.server_remaining_tokens = rem_t
                except ValueError:
                    pass

            if 'x-ratelimit-remaining-requests' in h:
                try:
                    rem_r = int(h['x-ratelimit-remaining-requests'])
                    self.server_remaining_requests = rem_r
                except ValueError:
                    pass

            if 'x-ratelimit-reset-tokens' in h:
                dur = parse_time_duration(h['x-ratelimit-reset-tokens'])
                if dur > 0:
                    self.server_tokens_reset_at = now + dur

            if 'x-ratelimit-reset-requests' in h:
                dur = parse_time_duration(h['x-ratelimit-reset-requests'])
                if dur > 0:
                    self.server_requests_reset_at = now + dur

            if 'retry-after' in h:
                dur = parse_time_duration(h['retry-after'])
                if dur > 0:
                    self.server_requests_reset_at = now + dur
                    self.server_tokens_reset_at = now + dur

    async def adjust_actual_tokens(self, estimated_tokens: int, actual_tokens: int):
        diff = actual_tokens - estimated_tokens
        if diff == 0:
            return
        async with self._lock:
            self.tpm_used += diff
            self.tpd_used += diff

class MultiProviderRateLimiter:
    """
    Manages independent DynamicRateLimiters for multiple LLM providers (Groq, Gemini, MiniMax).
    """
    def __init__(self, limiters: Dict[str, DynamicRateLimiter]):
        self.limiters = limiters

    def get_limiter(self, provider_name: str) -> Optional[DynamicRateLimiter]:
        return self.limiters.get(provider_name)

    def find_best_available_provider(self, providers: List[Any], estimated_tokens: int) -> Any:
        """
        Finds the first provider with immediate headroom for estimated_tokens.
        Falls back to the first provider if all are temporarily at limit.
        """
        for p in providers:
            limiter = self.limiters.get(p.name)
            if limiter and limiter.can_consume_immediately(estimated_tokens):
                return p
        return providers[0]
