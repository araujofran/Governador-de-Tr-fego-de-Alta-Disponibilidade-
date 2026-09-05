import asyncio
from typing import Optional

class ConcurrencyManager:
    """
    Manages maximum concurrent HTTP connections using asyncio.Semaphore,
    and tracks active worker slots.
    """
    def __init__(self, max_concurrency: int = 10):
        self.max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._active_count = 0
        self._lock = asyncio.Lock()

    @property
    def active_count(self) -> int:
        return self._active_count

    async def acquire(self):
        await self._semaphore.acquire()
        async with self._lock:
            self._active_count += 1

    async def release(self):
        async with self._lock:
            self._active_count = max(0, self._active_count - 1)
        self._semaphore.release()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()
