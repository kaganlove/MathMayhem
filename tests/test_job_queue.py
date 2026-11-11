"""Phase 1 Acceptance Tests: Persistent Job Queue, Retries & Crash Recovery (T1.5)."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from app.database import create_db_engine, init_db, make_session_factory
from app.models import Job, utcnow
from app.queue import PersistentJobQueue


def test_persistent_job_queue_idempotency_retry_and_recovery(tmp_path: Path) -> None:
    db_path = tmp_path / "test_queue.db"
    engine = create_db_engine(f"sqlite:///{db_path.as_posix()}")
    init_db(engine)
    session_factory = make_session_factory(engine)
    queue = PersistentJobQueue(session_factory)

    # 1. Idempotent enqueue
    j1 = queue.enqueue("echo_job", {"value": 42}, idempotency_key="idem_001")
    j1_dup = queue.enqueue("echo_job", {"value": 999}, idempotency_key="idem_001")
    assert j1.id == j1_dup.id

    queue.register_handler("echo_job", lambda payload: {"doubled": payload["value"] * 2})
    processed = queue.process_next()
    assert processed is not None
    assert processed.status == "COMPLETED"
    assert '"doubled": 84' in (processed.result_json or "")

    # 2. Retry with backoff on transient failure, then succeed
    attempts_counter = {"count": 0}

    def flaky_handler(payload):
        attempts_counter["count"] += 1
        if attempts_counter["count"] == 1:
            raise RuntimeError("Transient GPU busy error")
        return {"ok": True}

    queue.register_handler("flaky_job", flaky_handler)
    queue.enqueue("flaky_job", {}, idempotency_key="idem_flaky", max_attempts=3)

    first_try = queue.process_next()
    assert first_try is not None
    assert first_try.status == "QUEUED"
    assert first_try.attempts == 1
    assert "Transient GPU busy error" in (first_try.error_message or "")

    # Advance time past backoff window and process again
    second_try = queue.process_next(now=utcnow() + timedelta(seconds=10))
    assert second_try is not None
    assert second_try.status == "COMPLETED"
    assert second_try.attempts == 2

    # 3. Crash recovery of stranded RUNNING jobs across restarts
    with session_factory() as session:
        stranded = Job(
            job_type="echo_job",
            idempotency_key="idem_stranded",
            status="RUNNING",
            payload_json='{"value": 10}',
            attempts=1,
            max_attempts=3,
        )
        session.add(stranded)
        session.commit()

    recovered_count = queue.recover_interrupted_jobs()
    assert recovered_count == 1
    recovered_job = queue.process_next()
    assert recovered_job is not None
    assert recovered_job.status == "COMPLETED"

    engine.dispose()
