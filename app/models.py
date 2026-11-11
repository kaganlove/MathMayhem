"""SQLAlchemy 2.0 ORM models and immutability/safety guards for Math Mayhem."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
    inspect,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ImmutableRecordError(RuntimeError):
    """Raised when attempting to modify or delete an immutable approved record."""


class SafetyPolicyViolationError(RuntimeError):
    """Raised when an operation violates a global Math Mayhem safety guardrail."""


class Episode(Base):
    """Top-level mathematical adventure episode."""

    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    concept_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    aspect_ratio: Mapped[str] = mapped_column(String(16), default="9:16", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", nullable=False)
    owner_id: Mapped[str] = mapped_column(String(64), default="owner_primary", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    versions: Mapped[list["EpisodeVersion"]] = relationship(
        "EpisodeVersion", back_populates="episode", cascade="all, delete-orphan"
    )


class EpisodeVersion(Base):
    """Versioned snapshot of an episode. Becomes strictly IMMUTABLE once status=='APPROVED'."""

    __tablename__ = "episode_versions"
    __table_args__ = (UniqueConstraint("episode_id", "version_number", name="uq_episode_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    episode_id: Mapped[int] = mapped_column(ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", nullable=False)

    script_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    storyboard_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    math_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    math_verification_report: Mapped[str] = mapped_column(Text, default="", nullable=False)

    preview_video_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    master_video_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    video_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    frame_count: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    fps: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    width: Mapped[int] = mapped_column(Integer, default=1080, nullable=False)
    height: Mapped[int] = mapped_column(Integer, default=1920, nullable=False)

    approved_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    owner_id: Mapped[str] = mapped_column(String(64), default="owner_primary", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    episode: Mapped["Episode"] = relationship("Episode", back_populates="versions")
    scenes: Mapped[list["Scene"]] = relationship(
        "Scene", back_populates="episode_version", cascade="all, delete-orphan"
    )


class Scene(Base):
    """Individual scene inside an EpisodeVersion."""

    __tablename__ = "scenes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    episode_version_id: Mapped[int] = mapped_column(
        ForeignKey("episode_versions.id", ondelete="CASCADE"), nullable=False
    )
    scene_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_frame: Mapped[int] = mapped_column(Integer, nullable=False)
    end_frame: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    math_expression: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    math_expected_display: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    is_fictional_metaphor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    audio_cue: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    episode_version: Mapped["EpisodeVersion"] = relationship("EpisodeVersion", back_populates="scenes")


class Asset(Base):
    """Registered visual, character, music, or SFX asset with mandatory rights provenance."""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False)  # character | music | sfx | prop | render
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(256), nullable=False)
    license_type: Mapped[str] = mapped_column(String(128), nullable=False)
    provenance_record: Mapped[str] = mapped_column(Text, nullable=False)
    commercial_use_cleared: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sponsored_use_cleared: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    owner_id: Mapped[str] = mapped_column(String(64), default="owner_primary", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class ApprovalLog(Base):
    """Explicit owner approval log for an EpisodeVersion or SponsorMessage."""

    __tablename__ = "approval_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)  # episode_version | sponsor_message
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    episode_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    version_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    approved_by: Mapped[str] = mapped_column(String(64), nullable=False)
    approval_mode: Mapped[str] = mapped_column(String(32), default="INDIVIDUAL", nullable=False)  # INDIVIDUAL | ENUMERATED_BATCH
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Job(Base):
    """Persistent background job with idempotency, retry backoff, and crash recovery."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="QUEUED", nullable=False, index=True)
    payload_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    result_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    owner_id: Mapped[str] = mapped_column(String(64), default="owner_primary", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class SponsorLead(Base):
    """Sponsor CRM lead and outreach/negotiation message with mandatory approval gate."""

    __tablename__ = "sponsor_leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(256), nullable=False)
    message_type: Mapped[str] = mapped_column(
        String(64), default="INITIAL_OUTREACH", nullable=False
    )  # ADMIN_ACK | INITIAL_OUTREACH | SUBSTANTIVE_REPLY | COUNTEROFFER | CONTRACT_DISCUSSION
    subject: Mapped[str] = mapped_column(String(256), nullable=False)
    draft_body: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_terms: Mapped[str] = mapped_column(Text, default="", nullable=False)
    body_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="PENDING_APPROVAL", nullable=False
    )  # PENDING_APPROVAL | APPROVED | SENT
    approved_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    owner_id: Mapped[str] = mapped_column(String(64), default="owner_primary", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class AuditEvent(Base):
    """Append-only system and security audit log."""

    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(64), default="system", nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    details_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


# ---------------------------------------------------------------------------
# Guardrail Event Listeners: Immutability & Asset Provenance Enforcement
# ---------------------------------------------------------------------------

IMMUTABLE_VERSION_FIELDS = (
    "script_json",
    "storyboard_json",
    "math_verified",
    "math_verification_report",
    "preview_video_path",
    "master_video_path",
    "video_sha256",
    "duration_seconds",
    "frame_count",
    "fps",
    "width",
    "height",
    "version_number",
    "episode_id",
)


@event.listens_for(EpisodeVersion, "before_update")
def _guard_approved_episode_version(_mapper, _connection, target: EpisodeVersion) -> None:
    """Prevent any mutation to an EpisodeVersion after it has been APPROVED."""
    state = inspect(target)
    status_hist = state.attrs.status.history
    was_approved = (
        (status_hist.deleted and status_hist.deleted[0] == "APPROVED")
        or (not status_hist.deleted and target.status == "APPROVED")
    )
    if not was_approved:
        return

    # If it was already APPROVED before this update, reject any modification to immutable fields or status downgrade
    if status_hist.has_changes() and target.status != "APPROVED":
        raise ImmutableRecordError(
            f"EpisodeVersion id={target.id} (v{target.version_number}) is APPROVED and immutable; status cannot change to {target.status}."
        )
    for field_name in IMMUTABLE_VERSION_FIELDS:
        attr_hist = getattr(state.attrs, field_name).history
        if attr_hist.has_changes():
            raise ImmutableRecordError(
                f"EpisodeVersion id={target.id} (v{target.version_number}) is APPROVED and immutable; field '{field_name}' cannot be modified."
            )


@event.listens_for(EpisodeVersion, "before_delete")
def _guard_delete_approved_episode_version(_mapper, _connection, target: EpisodeVersion) -> None:
    if target.status == "APPROVED":
        raise ImmutableRecordError(
            f"EpisodeVersion id={target.id} (v{target.version_number}) is APPROVED and cannot be deleted."
        )


@event.listens_for(Asset, "before_insert")
@event.listens_for(Asset, "before_update")
def _guard_asset_provenance(_mapper, _connection, target: Asset) -> None:
    """Ensure every asset has documented source, license, provenance, and commercial/sponsored clearance."""
    if not target.source or not target.source.strip():
        raise SafetyPolicyViolationError("Asset must specify a non-empty 'source'.")
    if not target.license_type or not target.license_type.strip():
        raise SafetyPolicyViolationError("Asset must specify a non-empty 'license_type'.")
    if not target.provenance_record or not target.provenance_record.strip():
        raise SafetyPolicyViolationError("Asset must specify a non-empty 'provenance_record'.")
    if not target.commercial_use_cleared or not target.sponsored_use_cleared:
        raise SafetyPolicyViolationError(
            "Asset must have both commercial_use_cleared=True and sponsored_use_cleared=True."
        )


@event.listens_for(SponsorLead, "before_update")
def _guard_approved_sponsor_lead(_mapper, _connection, target: SponsorLead) -> None:
    """Approved sponsor messages are immutable; substantive messages cannot transition to SENT without approval."""
    state = inspect(target)
    status_hist = state.attrs.status.history
    was_approved = (
        (status_hist.deleted and status_hist.deleted[0] in ("APPROVED", "SENT"))
        or (not status_hist.deleted and target.status in ("APPROVED", "SENT") and not status_hist.has_changes())
    )
    if was_approved:
        for field_name in ("contact_email", "subject", "draft_body", "proposed_terms", "body_sha256"):
            if getattr(state.attrs, field_name).history.has_changes():
                raise ImmutableRecordError(
                    f"SponsorLead id={target.id} is {target.status} and immutable; field '{field_name}' cannot be modified."
                )

    if target.status == "SENT" and target.message_type != "ADMIN_ACK":
        if not target.approved_by or not target.approved_at:
            raise SafetyPolicyViolationError(
                f"Substantive sponsor correspondence (type={target.message_type}) cannot be marked SENT without explicit owner approval."
            )


def approve_episode_version(
    session: Session,
    version: EpisodeVersion,
    approved_by: str,
    approval_mode: str = "INDIVIDUAL",
    notes: str = "",
) -> ApprovalLog:
    """Approve an EpisodeVersion, locking it as immutable and writing an ApprovalLog + AuditEvent."""
    if not version.math_verified:
        raise SafetyPolicyViolationError(
            f"EpisodeVersion id={version.id} cannot be approved before math_verified=True."
        )
    content_hash = version.video_sha256 or hashlib.sha256(
        f"{version.episode_id}:{version.version_number}:{version.script_json}:{version.storyboard_json}".encode("utf-8")
    ).hexdigest()

    version.video_sha256 = content_hash
    version.status = "APPROVED"
    version.approved_by = approved_by
    version.approved_at = utcnow()

    log_entry = ApprovalLog(
        target_type="episode_version",
        target_id=version.id,
        episode_id=version.episode_id,
        version_number=version.version_number,
        content_sha256=content_hash,
        approved_by=approved_by,
        approval_mode=approval_mode,
        notes=notes,
    )
    session.add(log_entry)
    session.add(
        AuditEvent(
            event_type="EPISODE_VERSION_APPROVED",
            actor=approved_by,
            entity_type="EpisodeVersion",
            entity_id=str(version.id),
            details_json=f'{{"episode_id": {version.episode_id}, "version": {version.version_number}, "sha256": "{content_hash}"}}',
        )
    )
    session.commit()
    return log_entry


def verify_publish_eligibility(session: Session, episode_id: int, version_id: int) -> EpisodeVersion:
    """Enforce global guardrail: never publish an unapproved video."""
    version = session.get(EpisodeVersion, version_id)
    if not version or version.episode_id != episode_id:
        raise SafetyPolicyViolationError("EpisodeVersion not found or mismatched episode_id.")
    if version.status != "APPROVED":
        raise SafetyPolicyViolationError(
            f"Cannot publish EpisodeVersion id={version_id}: status is '{version.status}', must be 'APPROVED'."
        )
    approval = (
        session.query(ApprovalLog)
        .filter_by(
            target_type="episode_version",
            target_id=version.id,
            episode_id=episode_id,
            version_number=version.version_number,
            content_sha256=version.video_sha256,
        )
        .first()
    )
    if not approval:
        raise SafetyPolicyViolationError(
            f"Cannot publish EpisodeVersion id={version_id}: no matching immutable ApprovalLog found."
        )
    return version
