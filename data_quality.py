from typing import Dict, Any, List

class DataQualityAnalyzer:
    """
    Camada 6: Data Quality & Validações de Integridade da Transcrição.
    Calcula um data_quality_score (0 a 100) e retorna flags de alerta.
    """

    def analyze(self, text: str, lines: List[Dict[str, Any]]) -> Dict[str, Any]:
        flags = []
        score = 100

        # Check 1: Vazio ou nulo
        if not text or not text.strip():
            return {
                "score": 0,
                "flags": ["EMPTY_TRANSCRIPTION"],
                "is_valid": False
            }

        # Check 2: Baixa quantidade de texto
        words = text.split()
        word_count = len(words)
        if word_count < 15:
            score -= 40
            flags.append("LOW_TEXT_QUANTITY")
        elif word_count < 50:
            score -= 20
            flags.append("MODERATE_TEXT_QUANTITY")

        # Check 3: Interlocutores / Speakers
        speakers = set(l.get("speaker") for l in lines if l.get("speaker"))
        if len(speakers) < 2:
            score -= 25
            flags.append("SPEAKER_SEPARATION_LOW_CONFIDENCE")

        # Check 4: Transcrição truncada (termina abruptamente sem pontuação final)
        clean_end = text.strip()[-1] if text.strip() else ""
        if clean_end not in [".", "!", "?", "]", ")", '"', "'"]:
            score -= 15
            flags.append("POSSIBLE_TRUNCATED_AUDIO")

        # Guarantee bounds [0, 100]
        score = max(0, min(100, score))
        is_valid = score >= 30

        return {
            "score": score,
            "flags": flags,
            "is_valid": is_valid,
            "word_count": word_count,
            "line_count": len(lines)
        }
