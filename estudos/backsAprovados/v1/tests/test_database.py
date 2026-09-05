import pytest
import os
import tempfile
from database import AuditDatabase
from audit_schema import AuditAnalysisResult

def test_database_audit_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_audit.db")
        db = AuditDatabase(db_path=db_path)

        mock_audit = AuditAnalysisResult(
            numero_protocolo="PROT-999888",
            nome_operador="Operador Teste",
            nome_cliente="Cliente Teste",
            resumo_executivo="Atendimento teste de auditoria.",
            score_final=92.5
        ).model_dump()

        telemetry = {
            "provider_used": "Groq",
            "input_tokens": 500,
            "output_tokens": 200,
            "latency_sec": 0.45,
            "masked_pii_count": 2,
            "status_code": 200
        }

        audit_id = db.save_audit(
            task_id="task_001.txt",
            filename="000000004739775_correctedtranscription.txt",
            audit_data=mock_audit,
            telemetry_data=telemetry
        )

        assert audit_id > 0

        audits = db.get_all_audits(limit=10)
        assert len(audits) == 1
        assert audits[0]["protocol_number"] == "PROT-999888"
        assert audits[0]["overall_score"] == 92.5

        kpis = db.get_kpi_summary()
        assert kpis["total_audits"] == 1
        assert kpis["avg_score"] == 92.5
        assert kpis["total_tokens"] == 700
