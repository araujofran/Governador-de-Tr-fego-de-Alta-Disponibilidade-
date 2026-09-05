import re
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class PreprocessedText:
    clean_text: str
    masked_pii_count: int
    lines: List[Dict[str, Any]] = None

class TextPreprocessor:
    """
    Camada 2: Normalização em Python.
    Limpa caracteres corrompidos, normaliza espaços, mascara PII e
    gera a estrutura indexada por linhas e turnos de interlocutor (CLIENTE/ATENDENTE).
    """
    def __init__(self):
        # Regex patterns para mascaramento de PII mantendo o texto legível
        self.cpf_pattern = re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b')
        self.card_pattern = re.compile(r'\b(?:\d[ -]*?){13,16}\b')
        self.phone_pattern = re.compile(r'\b(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?9?\d{4}[-.\s]?\d{4}\b')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

    def preprocess(self, raw_text: str) -> PreprocessedText:
        if not raw_text:
            return PreprocessedText(clean_text="", masked_pii_count=0, lines=[])

        # 1. Normalização básica de texto
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw_text)
        text = re.sub(r'\r\n|\r', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text)

        masked_count = 0

        # 2. Mascaramento de PII
        text, n_email = self.email_pattern.subn('[EMAIL_MASCARADO]', text)
        masked_count += n_email

        text, n_cpf = self.cpf_pattern.subn('[CPF_MASCARADO]', text)
        masked_count += n_cpf

        text, n_phone = self.phone_pattern.subn('[TELEFONE_MASCARADO]', text)
        masked_count += n_phone

        text = re.sub(r'\n{3,}', '\n\n', text).strip()

        # 3. Indexação de linhas e identificação de turnos
        raw_lines = text.split('\n')
        indexed_lines = []
        current_speaker = "ATENDENTE"

        for idx, line_str in enumerate(raw_lines, 1):
            line_clean = line_str.strip()
            if not line_clean:
                continue

            # Tentativa heurística de identificação de speaker
            upper = line_clean.upper()
            if upper.startswith("CLIENTE:") or upper.startswith("USUÁRIO:") or upper.startswith("CONSUMIDOR:"):
                current_speaker = "CLIENTE"
                line_clean = re.sub(r'^(CLIENTE|USUÁRIO|CONSUMIDOR):\s*', '', line_clean, flags=re.IGNORECASE)
            elif upper.startswith("ATENDENTE:") or upper.startswith("OPERADOR:") or upper.startswith("BANCO:"):
                current_speaker = "ATENDENTE"
                line_clean = re.sub(r'^(ATENDENTE|OPERADOR|BANCO):\s*', '', line_clean, flags=re.IGNORECASE)

            indexed_lines.append({
                "line_number": idx,
                "speaker": current_speaker,
                "text": line_clean
            })

        return PreprocessedText(clean_text=text, masked_pii_count=masked_count, lines=indexed_lines)
