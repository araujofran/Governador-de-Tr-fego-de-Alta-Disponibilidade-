import os
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("TrafficController.KeyLoader")

@dataclass
class LoadedKeys:
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None

class KeyLoader:
    """
    Reads API keys automatically from TXT files inside chavesFree/ directory,
    or falls back to environment variables.
    """
    def __init__(self, chaves_dir: str = r"C:\Users\fferr\Desktop\projetoRATE\chavesFree"):
        self.chaves_dir = chaves_dir

    def load_keys(self) -> LoadedKeys:
        keys = LoadedKeys()

        # 1. Load Groq key
        groq_path = os.path.join(self.chaves_dir, "groq.txt")
        if os.path.exists(groq_path):
            with open(groq_path, "r", encoding="utf-8") as f:
                val = f.read().strip()
                if val:
                    keys.groq_api_key = val
        if not keys.groq_api_key:
            keys.groq_api_key = os.getenv("GROQ_API_KEY")

        # 2. Load Gemini key
        gemini_path = os.path.join(self.chaves_dir, "Gemini 3.6 Flash.txt")
        if os.path.exists(gemini_path):
            with open(gemini_path, "r", encoding="utf-8") as f:
                val = f.read().strip()
                if val:
                    keys.gemini_api_key = val
        if not keys.gemini_api_key:
            keys.gemini_api_key = os.getenv("GEMINI_API_KEY")

        # 3. Load OpenRouter (MiniMax M3) key
        minimax_path = os.path.join(self.chaves_dir, "MiniMax M3 free.txt")
        if os.path.exists(minimax_path):
            with open(minimax_path, "r", encoding="utf-8") as f:
                val = f.read().strip()
                if val:
                    keys.openrouter_api_key = val
        if not keys.openrouter_api_key:
            keys.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

        logger.info(
            f"[KeyLoader] Keys status -> Groq: {'OK' if keys.groq_api_key else 'Missing'}, "
            f"Gemini: {'OK' if keys.gemini_api_key else 'Missing'}, "
            f"OpenRouter: {'OK' if keys.openrouter_api_key else 'Missing'}"
        )
        return keys
