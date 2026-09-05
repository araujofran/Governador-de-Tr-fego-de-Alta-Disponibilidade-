from typing import List, Dict, Any
from evidence_engine import Evidence

class ContextBuilder:
    """
    Camada 8: Construtor de Contexto Mínimo (Evidence-Based Context Reduction).
    Prepara o payload otimizado sem perda de informação semântica para o Contrato Daycoval.
    """

    def build_payload(
        self,
        atendimento_id: str,
        filename: str,
        lines: List[Dict[str, Any]],
        evidences: List[Evidence],
        data_quality: Dict[str, Any],
        contract_prompt: str,
        max_context_words: int = 2500
    ) -> Dict[str, Any]:
        
        total_words = sum(len(l.get("text", "").split()) for l in lines)
        
        # Se for pequeno/médio (< 2500 palavras), preserva todas as linhas indexadas
        if total_words <= max_context_words:
            selected_lines = lines
            is_reduced = False
        else:
            # Evidence-Based Context Reduction: Seleciona início, fim e linhas com evidência
            is_reduced = True
            lines_by_no = {l.get("line_number"): l for l in lines}
            evidence_line_nos = set()
            for ev in evidences:
                for ln in range(ev.linha_inicio, ev.linha_fim + 1):
                    evidence_line_nos.add(ln)
            
            selected_indices = set()
            max_line = max(lines_by_no.keys()) if lines_by_no else 1
            
            # 1. Primeiras 15 linhas (saudação, identificação, motivo)
            for i in range(1, min(16, max_line + 1)):
                selected_indices.add(i)
                
            # 2. Linhas com evidências registradas + contexto vizinho (+- 1 linha)
            for eln in evidence_line_nos:
                for offset in [-1, 0, 1]:
                    target = eln + offset
                    if target in lines_by_no:
                        selected_indices.add(target)
                        
            # 3. Últimas 15 linhas (fechamento, acordo, desfecho)
            for i in range(max(1, max_line - 14), max_line + 1):
                selected_indices.add(i)
                
            selected_lines = [lines_by_no[idx] for idx in sorted(selected_indices) if idx in lines_by_no]

        formatted_transcript = "\n".join([
            f"[Linha {l.get('line_number'):03d}] [{l.get('speaker', 'SPEAKER')}] {l.get('text', '')}"
            for l in selected_lines
        ])

        evidences_summary = [
            {
                "id": ev.evidence_id,
                "tipo": ev.tipo,
                "valor": ev.valor,
                "speaker": ev.speaker,
                "linha": f"L{ev.linha_inicio}-L{ev.linha_fim}",
                "trecho": ev.trecho
            }
            for ev in evidences
        ]

        return {
            "atendimento_id": atendimento_id,
            "filename": filename,
            "is_context_reduced": is_reduced,
            "total_lines_original": len(lines),
            "lines_in_context": len(selected_lines),
            "evidences_count": len(evidences),
            "evidences_indexed": evidences_summary,
            "data_quality": data_quality,
            "formatted_transcript": formatted_transcript,
            "contract_prompt": contract_prompt
        }
