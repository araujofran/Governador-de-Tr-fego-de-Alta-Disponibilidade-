import re
import logging
from typing import List

try:
    import tiktoken
    _HAS_TIKTOKEN = True
except ImportError:
    _HAS_TIKTOKEN = False

logger = logging.getLogger("TrafficController.Tokenizer")

class TokenizerManager:
    """
    Estimates input and output tokens for LLM requests, and performs smart chunking
    for large text payloads to ensure they fit within specified per-request token budgets.
    """
    def __init__(self, default_encoding: str = "cl100k_base"):
        self.default_encoding = default_encoding
        self._encoder = None
        if _HAS_TIKTOKEN:
            try:
                self._encoder = tiktoken.get_encoding(default_encoding)
            except Exception as e:
                logger.warning(f"Could not load tiktoken encoding '{default_encoding}': {e}. Using fallback heuristic.")

    def count_tokens(self, text: str) -> int:
        """Counts or estimates token length of a given text."""
        if not text:
            return 0
        if self._encoder:
            try:
                return len(self._encoder.encode(text))
            except Exception:
                pass
        
        # Fallback estimation heuristic: ~1 token per 4 chars or 0.75 words
        words = len(text.split())
        chars = len(text)
        return max(1, int(max(words * 1.3, chars / 4.0)))

    def estimate_request_budget(self, input_text: str, expected_output_tokens: int = 500) -> int:
        """Estimates total tokens (input + output headroom) required for a request."""
        input_tokens = self.count_tokens(input_text)
        return input_tokens + expected_output_tokens

    def smart_chunk_text(self, text: str, max_chunk_tokens: int = 1500) -> List[str]:
        """
        Splits large text into smaller semantic chunks (by paragraphs/sentences)
        where each chunk is guaranteed to be under max_chunk_tokens.
        """
        if self.count_tokens(text) <= max_chunk_tokens:
            return [text]

        # Split into paragraphs first
        paragraphs = re.split(r'\n\s*\n', text)
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_tokens = 0

        for p in paragraphs:
            p_tokens = self.count_tokens(p)
            
            # If paragraph itself is larger than max_chunk_tokens, split by sentences
            if p_tokens > max_chunk_tokens:
                sentences = re.split(r'(?<=[.!?])\s+', p)
                for s in sentences:
                    s_tokens = self.count_tokens(s)
                    if current_tokens + s_tokens > max_chunk_tokens and current_chunk:
                        chunks.append(" ".join(current_chunk))
                        current_chunk = []
                        current_tokens = 0
                    current_chunk.append(s)
                    current_tokens += s_tokens
            else:
                if current_tokens + p_tokens > max_chunk_tokens and current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_tokens = 0
                current_chunk.append(p)
                current_tokens += p_tokens

        if current_chunk:
            chunks.append("\n\n".join(current_chunk) if "\n\n" in text else " ".join(current_chunk))

        return chunks
