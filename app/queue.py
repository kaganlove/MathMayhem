"""Persistent SQLite-backed job queue with idempotency, retry backoff, and crash recovery."""

from __future__ import annotations

import json
import traceback
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional

from sqlalchemy.orm import Session, sessionmaker

from app.models import AuditEvent, Job, utcnow


JobHandler = Callable[[Dict[str, Any]], Dict[str, Any]]


class PersistentJobQueue:
    """Manages persistent jobs across restarts with idempotent enqueueing and retry backoff."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._handlers: Dict[str, JobHandler] = {}

    def register_handler(self, job_type: str, handler: JobHandler) -> None:
        self._handlers[job_type] = handler

    def enqueue(
        self,
        job_type: str,
        payload: Dict[str, Any],
        idempotency_key: str,
        max_attempts: int = 3,
        owner_id: str = "owner_primary",
    ) -> Job:
        """Enqueue a job or return the existing job if idempotency_key already exists."""
        with self._session_factory() as session:
            existing = session.query(Job).filter_by(idempotency_key=idempotency_key).first()
            if existing is not None:
                return existing

            job = Job(
                job_type=job_type,
                idempotency_key=idempotency_key,
                status="QUEUED",
                payload_json=json.dumps(payload, sort_keys=True),
                attempts=0,
                max_attempts=max_attempts,
                next_run_at=utcnow(),
                owner_id=owner_id,
            )
            session.add(job)
            session.add(
                AuditEvent(
                    event_type="JOB_ENQUEUED",
                    actor=owner_id,
                    entity_type="Job",
                    entity_id=idempotency_key,
                    details_json=json.dumps({"job_type": job_type}),
                )
            )
            session.commit()
            session.refresh(job)
            return job

    def recover_interrupted_jobs(self) -> int:
        """Reset any jobs stranded in RUNNING state (e.g., from power loss or restart) back to QUEUED."""
        with self._session_factory() as session:
            stranded = session.query(Job).filter_by(status="RUNNING").all()
            count = len(stranded)
            for job in stranded:
                job.status = "QUEUED"
                job.next_run_at = utcnow()
                session.add(
                    AuditEvent(
                        event_type="JOB_RECOVERED_AFTER_RESTART",
                        actor="system",
                        entity_type="Job",
                        entity_id=str(job.id),
                        details_json=json.dumps({"idempotency_key": job.idempotency_key}),
                    )
                )
            if count > 0:
                session.commit()
            return count

    def process_next(self, now: Optional[datetime] = None) -> Optional[Job]:
        """Claim and execute the next ready QUEUED job."""
        current_time = now or utcnow()
        with self._session_factory() as session:
            job = (
                session.query(Job)
                .filter(Job.status == "QUEUED", Job.next_run_at <= current_time)
                .order_by(Job.id.asc())
                .first()
            )
            if job is None:
                return None

            job.status = "RUNNING"
            job.started_at = current_time
            job.attempts += 1
            session.commit()
            job_id = job.id
            job_type = job.job_type
            payload = json.loads(job.payload_json or "{}")

        handler = self._handlers.get(job_type)
        with self._session_factory() as session:
            job = session.get(Job, job_id)
            assert job is not None
            if handler is None:
                job.status = "FAILED"
                job.error_message = f"No handler registered for job_type='{job_type}'"
                session.commit()
                session.refresh(job)
                return job

            try:
                result = handler(payload)
                job.status = "COMPLETED"
                job.result_json = json.dumps(result or {})
                job.error_message = None
                job.completed_at = utcnow()
                session.add(
                    AuditEvent(
                        event_type="JOB_COMPLETED",
                        actor="worker",
                        entity_type="Job",
                        entity_id=str(job.id),
                        details_json=json.dumps({"job_type": job_type, "attempts": job.attempts}),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                err_msg = f"{type(exc).__name__}: {exc}"
                job.error_message = err_msg
                if job.attempts < job.max_attempts:
                    backoff_seconds = min(60, 2 ** job.attempts)
                    job.status = "QUEUED"
                    job.next_run_at = utcnow() + timedelta(seconds=backoff_seconds)
                else:
                    job.status = "FAILED"
                    job.completed_at = utcnow()
                session.add(
                    AuditEvent(
                        event_type="JOB_ERROR",
                        actor="worker",
                        entity_type="Job",
                        entity_id=str(job.id),
                        details_json=json.dumps(
                            {
                                "job_type": job_type,
                                "attempts": job.attempts,
                                "status": job.status,
                                "error": err_msg,
                                "trace": traceback.format_exc(limit=3),
                            }
                        ),
                    )
                )
            session.commit()
            session.refresh(job)
            return job
