import pytest
import os
import tempfile
from job_queue_db import JobQueueDB

def test_job_queue_db_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_queue.db")
        
        # Init SQLite tables
        from database import AuditDatabase
        AuditDatabase(db_path)

        queue_db = JobQueueDB(db_path)
        job_id = queue_db.create_job(
            atendimento_id="AT_TEST_01",
            filename="file1.txt",
            file_hash="hash123",
            payload_json={"test": 123},
            estimated_input_tokens=1500
        )
        assert job_id == "JOB_AT_TEST_01"

        pending = queue_db.fetch_pending_jobs()
        assert len(pending) == 1
        assert pending[0]["job_id"] == job_id

        queue_db.update_job_status(job_id, "SUCCESS")
        pending_after = queue_db.fetch_pending_jobs()
        assert len(pending_after) == 0
