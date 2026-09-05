import re
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class Evidence:
    evidence_id: str
    atendimento_id: str
    tipo: str
    valor: str
    speaker: str
    linha_inicio: int
    linha_fim: int
    trecho: str
    metodo_extracao: str  # REGEX, RULE, NLP, METADATA
    confianca: float

class EvidenceEngine:
    """
    Motor de Extração de Evidências Determinísticas via Regex e Regras Locais (Camada 5).
    Indexa trechos com coordenadas de linha, identificação do interlocutor e IDs únicos.
    """

    PATTERNS = {
        "CPF": r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
        "PROTOCOLO": r"\bprotocolo\s*(?:é|e|nº|numero|num|:\s*|\.-)?\s*(\d{6,16})\b",
        "VALOR_MONETARIO": r"R\$\s*\d+(?:\.\d{3})*(?:,\d{2})?|\b\d+(?:\.\d{3})*,\d{2}\s*reais\b",
        "TELEFONE": r"\b(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?(?:9?\d{4}[-\s]?\d{4})\b",
        "DATA": r"\b\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4}\b",
        "CARTAO": r"\b(?:\d{4}[-\s]?){3}\d{4}\b|\bfinal\s+\d{4}\b",
        "TRANSFERENCIA": r"\b(transferir|transferindo|transferencia|setor responsável|outra área)\b",
        "FRICCAO_OFENSIVA": r"\b(processo|advogado|procon|ouvidoria|absurdo|incompetente|vergonha|pessimo|péssimo|processar)\b",
        "CONFIRMACAO_EXPLICITA": r"\b(confirmo|confirmado|está correto|correto|com certeza|de acordo|sim, confirmo)\b",
        "NEGATIVA_EXPLICITA": r"\b(não aceito|não concordo|recuso|não autorizo|discordo|negado)\b",
        "PORTABILIDADE": r"\b(portabilidade|portar contrato|transferir contrato)\b"
    }

    def __init__(self):
        self.compiled_patterns = {k: re.compile(v, re.IGNORECASE) for k, v in self.PATTERNS.items()}

    def extract_evidences(self, atendimento_id: str, lines: List[Dict[str, Any]]) -> List[Evidence]:
        """
        Extrai todas as evidências determinísticas de uma lista de linhas indexadas.
        lines = [{'line_number': int, 'speaker': str, 'text': str}]
        """
        evidences: List[Evidence] = []
        ev_counter = 1

        for line in lines:
            line_no = line.get("line_number", 1)
            speaker = line.get("speaker", "DESCONHECIDO")
            text = line.get("text", "")

            if not text:
                continue

            for tipo, pattern in self.compiled_patterns.items():
                for match in pattern.finditer(text):
                    valor = match.group(0)
                    ev_id = f"EV_{atendimento_id[:8]}_{ev_counter:04d}"
                    ev_counter += 1

                    ev = Evidence(
                        evidence_id=ev_id,
                        atendimento_id=atendimento_id,
                        tipo=tipo,
                        valor=valor,
                        speaker=speaker,
                        linha_inicio=line_no,
                        linha_fim=line_no,
                        trecho=text[:250],
                        metodo_extracao="REGEX",
                        confianca=0.98 if tipo in ["CPF", "PROTOCOLO", "VALOR_MONETARIO"] else 0.85
                    )
                    evidences.append(ev)

        return evidences
