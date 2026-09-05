from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class ProviderResult:
    transcription_id: str
    output_text: str
    input_tokens: int
    output_tokens: int
    headers: Dict[str, Any]
    status_code: int
    duration_sec: float
    error: Optional[str] = None

class BaseLLMProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def process_transcription(
        self,
        transcription_id: str,
        text: str,
        model: Optional[str] = None
    ) -> ProviderResult:
        """Processes a single transcription text payload."""
        pass
