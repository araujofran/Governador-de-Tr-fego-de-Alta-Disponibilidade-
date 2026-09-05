import re
import json
import logging
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

logger = logging.getLogger("TrafficController.AuditSchema")

class CXScorecard(BaseModel):
    pontuacao_cx: int = Field(default=80, ge=0, le=100, description="Nota de experiência do cliente (0-100)")
    pontuacao_qualidade_operador: int = Field(default=80, ge=0, le=100, description="Nota de qualidade do operador (0-100)")
    pontuacao_tecnica: int = Field(default=80, ge=0, le=100, description="Nota de aderência técnica e procedimentos (0-100)")
    pontuacao_comportamental: int = Field(default=80, ge=0, le=100, description="Nota de tom e empatia comportamental (0-100)")
    resolutividade: str = Field(default="Resolvido", description="Status de resolutividade do atendimento")

class RiskAnalysis(BaseModel):
    nivel_risco: str = Field(default="Baixo", description="Nível de risco (Baixo, Médio, Alto, Crítico)")
    riscos_identificados: List[str] = Field(default_factory=list, description="Lista de riscos encontrados")
    causa_raiz: str = Field(default="Nao identificado", description="Causa raiz principal do problema")
    responsavel_problema: str = Field(default="Nao identificado", description="Responsável pelo problema (Operador, Cliente, Sistema/Processo, etc.)")
    citacao_evidencia: str = Field(default="Evidência presente na conversa.", description="Citação literal ou evidência direta extraída da transcrição")

class Opportunities(BaseModel):
    oportunidades_operador: List[str] = Field(default_factory=list, description="Oportunidades de desenvolvimento para o operador")
    oportunidades_operacionais: List[str] = Field(default_factory=list, description="Oportunidades de melhoria de processos/sistemas do banco")

class AuditAnalysisResult(BaseModel):
    numero_protocolo: str = Field(default="Nao identificado", description="Número de protocolo do atendimento se houver")
    nome_operador: str = Field(default="Operador", description="Nome ou identificação do operador")
    nome_cliente: str = Field(default="Cliente", description="Nome do cliente")
    resumo_executivo: str = Field(default="Atendimento realizado conforme fluxo padrão.", description="Resumo crítico e objetivo do atendimento")
    classificacao_atendimento: str = Field(default="Dúvida / Informação", description="Classificação do motivo do atendimento")
    
    scorecard: CXScorecard = Field(default_factory=CXScorecard)
    risco_e_causa_raiz: RiskAnalysis = Field(default_factory=RiskAnalysis)
    oportunidades: Opportunities = Field(default_factory=Opportunities)
    
    score_final: float = Field(default=85.0, ge=0.0, le=100.0, description="Pontuação final calculada de 0.0 a 100.0")
    justificativa_score: str = Field(default="Atendimento satisfatório com evidências observadas na conversa.", description="Justificativa técnica fundamentada para a nota final")

def repair_truncated_json(json_str: str) -> str:
    """Attempts to fix common unclosed strings, trailing commas, and brackets in truncated LLM JSON."""
    s = json_str.strip()

    # 1. Strip markdown fences if present
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\n?", "", s)
        s = re.sub(r"\n?```$", "", s).strip()

    # 2. Extract first '{' to last '}' if extra preamble text exists
    first_brace = s.find("{")
    if first_brace != -1:
        last_brace = s.rfind("}")
        if last_brace != -1 and last_brace > first_brace:
            s = s[first_brace:last_brace+1]
        else:
            s = s[first_brace:]

    # 3. If string was cut off inside a double quote string
    # Count unescaped double quotes
    quotes = re.findall(r'(?<!\\)"', s)
    if len(quotes) % 2 != 0:
        s += '"'

    # 4. Auto-close missing brackets and braces
    open_braces = s.count("{") - s.count("}")
    open_brackets = s.count("[") - s.count("]")

    if open_brackets > 0:
        s += "]" * open_brackets
    if open_braces > 0:
        s += "}" * open_braces

    return s

def sanitize_data_dict(data: dict) -> dict:
    """Converts nested dicts or lists in expected string fields to valid strings."""
    if not isinstance(data, dict):
        return data
    string_fields = [
        "numero_protocolo", "nome_operador", "nome_cliente", 
        "resumo_executivo", "classificacao_atendimento", "justificativa_score"
    ]
    for field in string_fields:
        if field in data and not isinstance(data[field], str):
            val = data[field]
            if isinstance(val, dict):
                data[field] = " | ".join(f"{k}: {v}" for k, v in val.items() if v)
            elif isinstance(val, list):
                data[field] = " ".join(str(x) for x in val)
            else:
                data[field] = str(val)
    return data

def parse_audit_json(raw_text: str) -> AuditAnalysisResult:
    """
    Robustly parses raw text into a valid AuditAnalysisResult Pydantic model.
    Falls back gracefully if LLM output is malformed.
    """
    if not raw_text or not raw_text.strip():
        return AuditAnalysisResult()

    try:
        data = json.loads(raw_text)
        sanitized = sanitize_data_dict(data)
        return AuditAnalysisResult.model_validate(sanitized)
    except Exception:
        pass

    try:
        repaired = repair_truncated_json(raw_text)
        data = json.loads(repaired)
        sanitized = sanitize_data_dict(data)
        return AuditAnalysisResult.model_validate(sanitized)
    except Exception as e:
        logger.warning(f"Could not parse Pydantic JSON from LLM response ({e}). Using default schema.")
        return AuditAnalysisResult()
