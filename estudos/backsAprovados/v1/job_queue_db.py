import sqlite3
import json
import hashlib
from typing import List, Dict, Any, Optional

class JobQueueDB:
    """
    Gerenciador de Fila de Jobs Persistente no SQLite (Camadas 7, 10, 14, 17, 18).
    Garante idempotência, checkpoint de reinício e gerenciamento de transição de estados.
    """

    def __init__(self, db_path: str = r"C:\Users\fferr\Desktop\projetoRATE\repositoy\audit_database.db"):
        self.db_path = db_path
        self.reset_failed_and_stuck_jobs()

    def reset_failed_and_stuck_jobs(self):
        """Reseta jobs FAILED ou travados em LLM_PROCESSING de volta para READY_FOR_LLM."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE llm_jobs
                SET status = 'READY_FOR_LLM', error_message = NULL
                WHERE status IN ('FAILED', 'LLM_PROCESSING', 'VALIDATION_ERROR')
            """)
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def create_job(
        self,
        atendimento_id: str,
        filename: str,
        file_hash: str,
        payload_json: Dict[str, Any],
        estimated_input_tokens: int,
        contract_version: str = "v1.0"
    ) -> str:
        payload_str = json.dumps(payload_json, ensure_ascii=False)
        import re
        clean_id = re.sub(r'[^a-zA-Z0-9_]', '_', atendimento_id)
        job_id = f"JOB_{clean_id}"

        request_hash = hashlib.sha256(f"{file_hash}_{contract_version}".encode()).hexdigest()
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Idempotência: verificar se já existe SUCCESS
            cursor.execute(
                "SELECT job_id, status FROM llm_jobs WHERE request_hash = ? AND status = 'SUCCESS'",
                (request_hash,)
            )
            row = cursor.fetchone()
            if row:
                return row["job_id"]

            cursor.execute("""
                INSERT INTO llm_jobs (
                    job_id, atendimento_id, filename, file_hash, request_hash, contract_version,
                    status, estimated_input_tokens, payload_json, attempt, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'READY_FOR_LLM', ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(job_id) DO UPDATE SET
                    status = CASE WHEN status = 'SUCCESS' THEN 'SUCCESS' ELSE 'READY_FOR_LLM' END,
                    payload_json = excluded.payload_json,
                    estimated_input_tokens = excluded.estimated_input_tokens,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                job_id, atendimento_id, filename, file_hash, request_hash, contract_version,
                estimated_input_tokens, payload_str
            ))
            conn.commit()
            return job_id
        finally:
            conn.close()

    def claim_next_job(self) -> Optional[Dict[str, Any]]:
        """Reserva atómicamente o próximo job pendente para evitar colisão entre workers."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT job_id, atendimento_id, filename, file_hash, request_hash,
                       estimated_input_tokens, payload_json, attempt, status
                FROM llm_jobs
                WHERE status IN ('READY_FOR_LLM', 'WAITING_QUOTA', 'RETRY')
                ORDER BY created_at ASC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if not row:
                return None
            
            job = dict(row)
            job_id = job["job_id"]
            
            cursor.execute("""
                UPDATE llm_jobs
                SET status = 'LLM_PROCESSING', attempt = attempt + 1, updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ? AND status IN ('READY_FOR_LLM', 'WAITING_QUOTA', 'RETRY')
            """, (job_id,))
            conn.commit()
            
            if cursor.rowcount > 0:
                job["payload"] = json.loads(job["payload_json"]) if job.get("payload_json") else {}
                return job
            return None
        finally:
            conn.close()

    def fetch_pending_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Recupera jobs prontos para execução respeitando o checkpoint."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT job_id, atendimento_id, filename, file_hash, request_hash,
                       estimated_input_tokens, payload_json, attempt, status
                FROM llm_jobs
                WHERE status IN ('READY_FOR_LLM', 'WAITING_QUOTA', 'RETRY')
                ORDER BY created_at ASC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            result = []
            for r in rows:
                item = dict(r)
                item["payload"] = json.loads(item["payload_json"]) if item.get("payload_json") else {}
                result.append(item)
            return result
        finally:
            conn.close()

    def update_job_status(self, job_id: str, status: str, error_message: str = None, attempts_inc: bool = False):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if attempts_inc:
                cursor.execute("""
                    UPDATE llm_jobs
                    SET status = ?, error_message = ?, attempt = attempt + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE job_id = ?
                """, (status, error_message, job_id))
            else:
                cursor.execute("""
                    UPDATE llm_jobs
                    SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE job_id = ?
                """, (status, error_message, job_id))
            conn.commit()
        finally:
            conn.close()
