"""Phase 1 Acceptance Tests: Database Schema, Immutability & Safety Guards (T1.4)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from sqlalchemy import text

from app.database import create_db_engine, init_db, make_session_factory
from app.models import (
    Asset,
    Episode,
    EpisodeVersion,
    ImmutableRecordError,
    SafetyPolicyViolationError,
    SponsorLead,
    approve_episode_version,
    verify_publish_eligibility,
)


def test_sqlite_wal_mode_and_episode_version_immutability(tmp_path: Path) -> None:
    db_path = tmp_path / "test_mm.db"
    engine = create_db_engine(f"sqlite:///{db_path.as_posix()}")
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        journal_mode = session.execute(text("PRAGMA journal_mode;")).scalar()
        assert str(journal_mode).lower() == "wal"

        ep = Episode(
            code="EP001",
            title="Never Divide by Zero",
            concept_summary="10 / 0 is undefined",
            aspect_ratio="9:16",
        )
        session.add(ep)
        session.commit()

        v1 = EpisodeVersion(
            episode_id=ep.id,
            version_number=1,
            script_json='{"scenes": 5}',
            storyboard_json='[{"s": 1}]',
            math_verified=False,
        )
        session.add(v1)
        session.commit()

        # Cannot approve before math_verified=True
        with pytest.raises(SafetyPolicyViolationError):
            approve_episode_version(session, v1, approved_by="owner_primary")

        # Cannot publish while still in DRAFT
        with pytest.raises(SafetyPolicyViolationError):
            verify_publish_eligibility(session, ep.id, v1.id)

        # Mark math_verified=True and approve
        v1.math_verified = True
        session.commit()
        approve_episode_version(session, v1, approved_by="owner_primary")

        # Verify publish eligibility succeeds once approved
        verified = verify_publish_eligibility(session, ep.id, v1.id)
        assert verified.status == "APPROVED"

        # Attempting to mutate an APPROVED EpisodeVersion must raise ImmutableRecordError
        v1.script_json = '{"scenes": 999}'
        with pytest.raises(ImmutableRecordError):
            session.commit()
        session.rollback()

        # Attempting to delete an APPROVED EpisodeVersion must raise ImmutableRecordError
        v1_reloaded = session.get(EpisodeVersion, v1.id)
        assert v1_reloaded is not None
        session.delete(v1_reloaded)
        with pytest.raises(ImmutableRecordError):
            session.commit()
        session.rollback()

    engine.dispose()


def test_asset_provenance_and_sponsor_approval_guards(tmp_path: Path) -> None:
    db_path = tmp_path / "test_guards.db"
    engine = create_db_engine(f"sqlite:///{db_path.as_posix()}")
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        # Reject asset without commercial/sponsored clearance
        bad_asset = Asset(
            name="Unverified Track",
            asset_type="music",
            file_path="assets/audio/bad.wav",
            sha256="abc",
            source="Unknown",
            license_type="Unknown",
            provenance_record="None",
            commercial_use_cleared=False,
            sponsored_use_cleared=False,
        )
        session.add(bad_asset)
        with pytest.raises(SafetyPolicyViolationError):
            session.commit()
        session.rollback()

        # Accept valid procedural asset
        good_asset = Asset(
            name="Math Mayhem Curious Motif v1",
            asset_type="music",
            file_path="assets/audio/motif_curious.wav",
            sha256="0123456789abcdef",
            source="MathMayhem Procedural DSP Engine v1",
            license_type="100% Owner Original",
            provenance_record="Generated procedurally by app/render_smoke.py",
            commercial_use_cleared=True,
            sponsored_use_cleared=True,
        )
        session.add(good_asset)
        session.commit()
        assert good_asset.id is not None

        # Reject substantive sponsor email sent without approval
        body = "Hi Acme Math, here is our sponsorship proposal for $1,500."
        lead = SponsorLead(
            brand_name="Acme Math",
            contact_email="sponsors@acmemath.example",
            message_type="INITIAL_OUTREACH",
            subject="Math Mayhem Sponsorship Proposal",
            draft_body=body,
            proposed_terms="$1,500 for 1 integrated short",
            body_sha256=hashlib.sha256(body.encode("utf-8")).hexdigest(),
            status="PENDING_APPROVAL",
        )
        session.add(lead)
        session.commit()

        lead.status = "SENT"
        with pytest.raises(SafetyPolicyViolationError):
            session.commit()
        session.rollback()

    engine.dispose()
