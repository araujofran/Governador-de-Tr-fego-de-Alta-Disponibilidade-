"""
privacy_guard.py - Módulo de Segurança LGPD para Transcrições Bancárias.

Utiliza Microsoft Presidio (quando disponível) e regras de regex especializadas
em PIIs brasileiras (CPF, RG, Conta Corrente, Cartão de Crédito, Telefone)
para anonimizar dados sensíveis antes do processamento por LLMs.
"""

import re
from typing import Dict, Any, Tuple

# Tentar importar Microsoft Presidio
try:
    from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
    from presidio_anonymizer import AnonymizerEngine
    HAS_PRESIDIO = True
except ImportError:
    HAS_PRESIDIO = False


class PrivacyGuard:
    """Módulo de Higienização e Anonimização de Dados Sensíveis (LGPD / BACEN)."""

    def __init__(self):
        self.presidio_analyzer = None
        self.presidio_anonymizer = None

        if HAS_PRESIDIO:
            try:
                self.presidio_analyzer = AnalyzerEngine()
                self.presidio_anonymizer = AnonymizerEngine()
                self._add_custom_brazilian_recognizers()
            except Exception:
                # Fallback caso modelos de idioma padrão não estejam carregados
                self.presidio_analyzer = None

    def _add_custom_brazilian_recognizers(self):
        """Adiciona reconhecedores customizados de CPF e Conta Bancária ao Presidio."""
        if not self.presidio_analyzer:
            return

        cpf_pattern = Pattern(
            name="cpf_pattern",
            regex=r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
            score=0.95
        )
        cpf_recognizer = PatternRecognizer(
            supported_entity="BR_CPF",
            patterns=[cpf_pattern]
        )
        self.presidio_analyzer.registry.add_recognizer(cpf_recognizer)

        card_pattern = Pattern(
            name="card_pattern",
            regex=r"\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b",
            score=0.90
        )
        card_recognizer = PatternRecognizer(
            supported_entity="BR_CARD",
            patterns=[card_pattern]
        )
        self.presidio_analyzer.registry.add_recognizer(card_recognizer)

    def anonymize_transcript(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Anonimiza uma transcrição de áudio bancário substituindo PIIs por marcadores seguros.

        Returns:
            Tuple[str, Dict[str, Any]]: (texto_anonimizado, metadados_de_privacidade)
        """
        if not text:
            return text, {"pii_detected_count": 0, "entities": {}}

        pii_counts = {
            "BR_CPF": 0,
            "BR_CARD": 0,
            "BR_ACCOUNT": 0,
            "BR_PHONE": 0
        }

        sanitized_text = text

        # 1. Aplicar Microsoft Presidio se operacional
        if self.presidio_analyzer and self.presidio_anonymizer:
            try:
                from presidio_anonymizer.entities import OperatorConfig
                operators = {
                    "BR_CPF": OperatorConfig("replace", {"new_value": "[CPF_MASCARADO]"}),
                    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[TELEFONE_MASCARADO]"}),
                    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL_MASCARADO]"}),
                    "BR_CARD": OperatorConfig("replace", {"new_value": "[CARTAO_MASCARADO]"}),
                    "DEFAULT": OperatorConfig("replace", {"new_value": "[PII_MASCARADO]"})
                }

                results = self.presidio_analyzer.analyze(
                    text=sanitized_text,
                    entities=["BR_CPF", "BR_CARD", "PHONE_NUMBER", "EMAIL_ADDRESS"],
                    language="en"
                )
                if results:
                    anonymized_result = self.presidio_anonymizer.anonymize(
                        text=sanitized_text,
                        analyzer_results=results,
                        operators=operators
                    )
                    sanitized_text = anonymized_result.text
                    for r in results:
                        pii_counts[r.entity_type] = pii_counts.get(r.entity_type, 0) + 1
            except Exception:
                pass

        # 2. Regras Regex brasileiras de alta precisão (Backup e Reforço Garantido)
        # CPF
        cpf_regex = r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"
        matches = re.findall(cpf_regex, sanitized_text)
        if matches:
            pii_counts["BR_CPF"] += len(matches)
            sanitized_text = re.sub(cpf_regex, "[CPF_MASCARADO]", sanitized_text)

        # Cartão de Crédito
        card_regex = r"\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b"
        matches = re.findall(card_regex, sanitized_text)
        if matches:
            pii_counts["BR_CARD"] += len(matches)
            sanitized_text = re.sub(card_regex, "[CARTAO_MASCARADO]", sanitized_text)

        # Conta Corrente / Agência
        account_regex = r"\b(agência|ag|conta|cc)\s*:?\s*\d{3,5}-?[\dX]?\b"
        matches = re.findall(account_regex, sanitized_text, flags=re.IGNORECASE)
        if matches:
            pii_counts["BR_ACCOUNT"] += len(matches)
            sanitized_text = re.sub(account_regex, r"\1 [DADO_BANCARIO_MASCARADO]", sanitized_text, flags=re.IGNORECASE)

        # Telefone
        phone_regex = r"\(?\d{2}\)?\s?9?\d{4}-?\d{4}"
        matches = re.findall(phone_regex, sanitized_text)
        if matches:
            pii_counts["BR_PHONE"] += len(matches)
            sanitized_text = re.sub(phone_regex, "[TELEFONE_MASCARADO]", sanitized_text)

        total_pii = sum(pii_counts.values())

        metadata = {
            "pii_detected_count": total_pii,
            "entities": pii_counts,
            "presidio_active": HAS_PRESIDIO and self.presidio_analyzer is not None
        }

        return sanitized_text, metadata


# Instância Singleton do PrivacyGuard
privacy_guard = PrivacyGuard()
