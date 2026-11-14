"""Math Mayhem — Director Persistent Memory & Episode Context Engine (Phase 5.5).

Provides long-term persistent state for the conversational Math Mayhem Director:
1. `DirectorSession`: Active conversation focus, active episode code, latest preview artifacts.
2. `DirectorEpisodeContext`: Epistemic memory of an episode (mathematical topic, comedy premise,
   declarative scene parameters, current revision number, script & storyboard data).
3. `DirectorRevisionSnapshot`: Immutable history of conversational revision requests,
   targeted scene indexes, parameter diffs, and previous states enabling 1-click rollback.
4. `ProjectMemoryRegistry`: Authoritative record of approved character specifications,
   approved masters (EP001), active roadmap phase, and creative guardrails.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from app.database import Base, create_db_engine, make_session_factory


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DirectorSession(Base):
    """Tracks the live conversational focus of the Director Agent."""

    __tablename__ = "director_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_key: Mapped[str] = mapped_column(String(64), unique=True, default="default", index=True)
    active_episode_code: Mapped[str] = mapped_column(String(32), default="EP002", nullable=False)
    active_version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    active_preview_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    active_contact_sheet_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    last_user_intent: Mapped[str] = mapped_column(String(128), default="IDLE", nullable=False)
    last_user_message: Mapped[str] = mapped_column(Text, default="", nullable=False)
    last_director_response: Mapped[str] = mapped_column(Text, default="", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class DirectorEpisodeContext(Base):
    """Deep persistent memory of an episode being directed."""

    __tablename__ = "director_episode_contexts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    episode_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    math_topic: Mapped[str] = mapped_column(String(200), nullable=False)
    creative_premise: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", nullable=False)  # DRAFT | PREVIEW_READY | REVISED | APPROVED
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    script_data_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    storyboard_data_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    scene_parameters_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    math_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    math_report: Mapped[str] = mapped_column(Text, default="", nullable=False)
    master_video_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class DirectorRevisionSnapshot(Base):
    """Historical revision log for conversational rollback and auditability."""

    __tablename__ = "director_revision_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    episode_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    user_instruction: Mapped[str] = mapped_column(Text, nullable=False)
    targeted_scenes_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    parameter_deltas_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    snapshot_before_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    preview_video_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    contact_sheet_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class ProjectMemoryRegistry:
    """Read-only access to immutable project invariants and canonical standards."""

    CANONICAL_CHARACTER_RATIO = "1:3.4"
    CANONICAL_RENDER_RESOLUTION = (1080, 1920)
    CANONICAL_FPS = 30
    APPROVED_MUSIC_THEME = "option_a_orchestral_cartoon"
    CURRENT_ROADMAP_PHASE = "Phase 5.5: Conversational Director Agent Integration"
    APPROVED_EPISODES = ["EP001"]

    @classmethod
    def get_canonical_character_guidelines(cls) -> Dict[str, Any]:
        return {
            "head_silhouette": "Round circular head, 1:3.4 head-to-body proportion",
            "glasses": "Bold circular spectacles resting centered across facial profile",
            "limbs": "Fingerless stick-figure extremities with smooth cubic Bezier curvature",
            "footwear": "Dual oval shoes with strictly 0.0px ground penetration/slippage",
            "facial_expressions": [
                "neutral", "curious", "focused", "surprised", "panicked",
                "relieved", "proud", "mischievous", "confused", "determined"
            ],
            "dialogue_mode": "100% silent visual pantomime (zero spoken dialogue, zero floating punctuation)",
            "music_style": cls.APPROVED_MUSIC_THEME,
        }


class DirectorMemoryEngine:
    """High-level persistence manager for the Director Agent."""

    def __init__(self, session_factory=None):
        if session_factory is None:
            engine = create_db_engine()
            Base.metadata.create_all(bind=engine)
            self.session_factory = make_session_factory(engine)
        else:
            self.session_factory = session_factory

    def get_or_create_session(self, session_key: str = "default") -> Dict[str, Any]:
        with self.session_factory() as session:
            sess = session.execute(
                select(DirectorSession).where(DirectorSession.session_key == session_key)
            ).scalar_one_or_none()
            if not sess:
                sess = DirectorSession(
                    session_key=session_key,
                    active_episode_code="EP002",
                    active_version_number=1,
                    last_user_intent="IDLE",
                )
                session.add(sess)
                session.commit()
                session.refresh(sess)

            return {
                "session_key": sess.session_key,
                "active_episode_code": sess.active_episode_code,
                "active_version_number": sess.active_version_number,
                "active_preview_path": sess.active_preview_path,
                "active_contact_sheet_path": sess.active_contact_sheet_path,
                "last_user_intent": sess.last_user_intent,
                "last_user_message": sess.last_user_message,
                "last_director_response": sess.last_director_response,
                "updated_at": sess.updated_at.isoformat() if sess.updated_at else None,
            }

    def update_session(
        self,
        session_key: str = "default",
        active_episode_code: Optional[str] = None,
        active_version_number: Optional[int] = None,
        active_preview_path: Optional[str] = None,
        active_contact_sheet_path: Optional[str] = None,
        last_user_intent: Optional[str] = None,
        last_user_message: Optional[str] = None,
        last_director_response: Optional[str] = None,
    ) -> None:
        with self.session_factory() as session:
            sess = session.execute(
                select(DirectorSession).where(DirectorSession.session_key == session_key)
            ).scalar_one_or_none()
            if not sess:
                sess = DirectorSession(session_key=session_key)
                session.add(sess)

            if active_episode_code is not None:
                sess.active_episode_code = active_episode_code
            if active_version_number is not None:
                sess.active_version_number = active_version_number
            if active_preview_path is not None:
                sess.active_preview_path = active_preview_path
            if active_contact_sheet_path is not None:
                sess.active_contact_sheet_path = active_contact_sheet_path
            if last_user_intent is not None:
                sess.last_user_intent = last_user_intent
            if last_user_message is not None:
                sess.last_user_message = last_user_message
            if last_director_response is not None:
                sess.last_director_response = last_director_response

            sess.updated_at = utcnow()
            session.commit()

    def get_episode_context(self, episode_code: str) -> Optional[Dict[str, Any]]:
        with self.session_factory() as session:
            ep = session.execute(
                select(DirectorEpisodeContext).where(DirectorEpisodeContext.episode_code == episode_code)
            ).scalar_one_or_none()
            if not ep:
                return None
            return {
                "episode_code": ep.episode_code,
                "title": ep.title,
                "math_topic": ep.math_topic,
                "creative_premise": ep.creative_premise,
                "status": ep.status,
                "current_version": ep.current_version,
                "script_data": json.loads(ep.script_data_json),
                "storyboard_data": json.loads(ep.storyboard_data_json),
                "scene_parameters": json.loads(ep.scene_parameters_json),
                "math_verified": ep.math_verified,
                "math_report": ep.math_report,
                "master_video_path": ep.master_video_path,
                "created_at": ep.created_at.isoformat() if ep.created_at else None,
                "updated_at": ep.updated_at.isoformat() if ep.updated_at else None,
            }

    def save_episode_context(
        self,
        episode_code: str,
        title: str,
        math_topic: str,
        creative_premise: str,
        status: str = "DRAFT",
        current_version: int = 1,
        script_data: Optional[Dict[str, Any]] = None,
        storyboard_data: Optional[List[Dict[str, Any]]] = None,
        scene_parameters: Optional[Dict[str, Any]] = None,
        math_verified: bool = False,
        math_report: str = "",
        master_video_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        with self.session_factory() as session:
            ep = session.execute(
                select(DirectorEpisodeContext).where(DirectorEpisodeContext.episode_code == episode_code)
            ).scalar_one_or_none()
            if not ep:
                ep = DirectorEpisodeContext(
                    episode_code=episode_code,
                    title=title,
                    math_topic=math_topic,
                    creative_premise=creative_premise,
                )
                session.add(ep)

            ep.title = title
            ep.math_topic = math_topic
            ep.creative_premise = creative_premise
            ep.status = status
            ep.current_version = current_version
            if script_data is not None:
                ep.script_data_json = json.dumps(script_data)
            if storyboard_data is not None:
                ep.storyboard_data_json = json.dumps(storyboard_data)
            if scene_parameters is not None:
                ep.scene_parameters_json = json.dumps(scene_parameters)
            ep.math_verified = math_verified
            ep.math_report = math_report
            if master_video_path is not None:
                ep.master_video_path = master_video_path
            ep.updated_at = utcnow()

            session.commit()
            session.refresh(ep)

            return {
                "episode_code": ep.episode_code,
                "title": ep.title,
                "math_topic": ep.math_topic,
                "creative_premise": ep.creative_premise,
                "status": ep.status,
                "current_version": ep.current_version,
                "script_data": json.loads(ep.script_data_json),
                "storyboard_data": json.loads(ep.storyboard_data_json),
                "scene_parameters": json.loads(ep.scene_parameters_json),
                "math_verified": ep.math_verified,
                "math_report": ep.math_report,
                "master_video_path": ep.master_video_path,
            }

    def record_revision(
        self,
        episode_code: str,
        user_instruction: str,
        targeted_scenes: List[int],
        parameter_deltas: Dict[str, Any],
        preview_video_path: Optional[str] = None,
        contact_sheet_path: Optional[str] = None,
    ) -> int:
        with self.session_factory() as session:
            ep = session.execute(
                select(DirectorEpisodeContext).where(DirectorEpisodeContext.episode_code == episode_code)
            ).scalar_one_or_none()
            if not ep:
                raise ValueError(f"Episode {episode_code} not found in memory.")

            snapshot_before = {
                "current_version": ep.current_version,
                "scene_parameters": json.loads(ep.scene_parameters_json),
                "status": ep.status,
            }

            next_rev = ep.current_version + 1
            rev = DirectorRevisionSnapshot(
                episode_code=episode_code,
                revision_number=next_rev,
                user_instruction=user_instruction,
                targeted_scenes_json=json.dumps(targeted_scenes),
                parameter_deltas_json=json.dumps(parameter_deltas),
                snapshot_before_json=json.dumps(snapshot_before),
                preview_video_path=preview_video_path,
                contact_sheet_path=contact_sheet_path,
            )
            session.add(rev)

            # Update episode context with next version
            ep.current_version = next_rev
            ep.status = "REVISED"
            ep.updated_at = utcnow()

            session.commit()
            return next_rev

    def rollback_last_revision(self, episode_code: str) -> Optional[Dict[str, Any]]:
        with self.session_factory() as session:
            rev = session.execute(
                select(DirectorRevisionSnapshot)
                .where(DirectorRevisionSnapshot.episode_code == episode_code)
                .order_by(DirectorRevisionSnapshot.revision_number.desc())
            ).scalars().first()

            if not rev:
                return None

            snapshot_before = json.loads(rev.snapshot_before_json)
            ep = session.execute(
                select(DirectorEpisodeContext).where(DirectorEpisodeContext.episode_code == episode_code)
            ).scalar_one_or_none()

            if ep:
                ep.current_version = snapshot_before.get("current_version", 1)
                ep.scene_parameters_json = json.dumps(snapshot_before.get("scene_parameters", {}))
                ep.status = snapshot_before.get("status", "PREVIEW_READY")
                ep.updated_at = utcnow()

            session.delete(rev)
            session.commit()

            return snapshot_before

    def list_revision_history(self, episode_code: str) -> List[Dict[str, Any]]:
        with self.session_factory() as session:
            revs = session.execute(
                select(DirectorRevisionSnapshot)
                .where(DirectorRevisionSnapshot.episode_code == episode_code)
                .order_by(DirectorRevisionSnapshot.revision_number.asc())
            ).scalars().all()

            return [
                {
                    "revision_number": r.revision_number,
                    "user_instruction": r.user_instruction,
                    "targeted_scenes": json.loads(r.targeted_scenes_json),
                    "parameter_deltas": json.loads(r.parameter_deltas_json),
                    "preview_video_path": r.preview_video_path,
                    "contact_sheet_path": r.contact_sheet_path,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in revs
            ]
