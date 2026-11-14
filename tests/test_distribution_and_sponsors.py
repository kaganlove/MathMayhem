"""Integration and safety policy tests for Phase 6 Distribution & Sponsor Outreach CRM."""

from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.director_adapter import ConversationalIntent, DirectorProductionAdapter
from app.distribution_adapters import (
    InstagramReelsAdapter,
    PlatformDistributionHub,
    PublishingPlatform,
    TikTokAdapter,
    YouTubeShortsAdapter,
)
from app.models import (
    ApprovalLog,
    AuditEvent,
    Episode,
    EpisodeVersion,
    SafetyPolicyViolationError,
    SponsorLead,
    approve_episode_version,
)
from app.publishing_scheduler import PublishingScheduler
from app.sponsor_crm import (
    TARGET_SPONSOR_CATALOG,
    SponsorCategory,
    SponsorOutreachEngine,
    TargetSponsorBrand,
)


@pytest.fixture
def db_session(tmp_path):
    """Provide an isolated SQLite database and test session."""
    db_file = tmp_path / "test_dist.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    with session_factory() as session:
        yield session


@pytest.fixture
def dummy_video(tmp_path):
    """Create a temporary video file on disk for publish testing."""
    vid = tmp_path / "test_render_1080x1920.mp4"
    vid.write_bytes(b"MOCK_MP4_HEADER_DATA_1080x1920")
    return vid


def test_youtube_metadata_and_approval_guardrail(db_session, dummy_video):
    """Verify YouTube Shorts metadata formatting and strict rejection of unapproved episodes."""
    adapter = YouTubeShortsAdapter()

    ep = Episode(code="EP001", title="Never Divide by Zero", concept_summary="Test")
    db_session.add(ep)
    db_session.commit()

    ver = EpisodeVersion(
        episode_id=ep.id,
        version_number=1,
        status="DRAFT",  # UNAPPROVED
        preview_video_path=str(dummy_video),
        video_sha256="0123456789abcdef0123456789abcdef",
        math_verified=True,
    )
    db_session.add(ver)
    db_session.commit()

    meta = adapter.build_metadata(ep, ver)
    assert "#Shorts" in meta.title
    assert "SymPy" in meta.description
    assert meta.category == "Education"

    # Must raise SafetyPolicyViolationError because status is DRAFT
    with pytest.raises(SafetyPolicyViolationError, match="must be 'APPROVED'"):
        adapter.publish_version(db_session, ep.id, ver.id)

    # Now approve the version
    approve_episode_version(db_session, ver, approved_by="owner_primary")
    assert ver.status == "APPROVED"

    # Should succeed now
    res = adapter.publish_version(db_session, ep.id, ver.id, force_simulation=True)
    assert res.success is True
    assert res.platform == PublishingPlatform.YOUTUBE_SHORTS
    assert "youtube.com/shorts" in res.published_url


def test_multi_platform_distribution_hub(db_session, dummy_video):
    """Verify simultaneous publishing across YouTube Shorts, TikTok, and Instagram Reels."""
    hub = PlatformDistributionHub()

    ep = Episode(code="EP002", title="The 90-Degree Twist", concept_summary="Test i")
    db_session.add(ep)
    db_session.commit()

    ver = EpisodeVersion(
        episode_id=ep.id,
        version_number=1,
        status="DRAFT",
        master_video_path=str(dummy_video),
        video_sha256="fedcba9876543210fedcba9876543210",
        math_verified=True,
    )
    db_session.add(ver)
    db_session.commit()

    # Rejects unapproved episode
    with pytest.raises(SafetyPolicyViolationError):
        hub.publish_to_all_platforms(db_session, ep.id, ver.id)

    # Approve
    approve_episode_version(db_session, ver, approved_by="owner_primary")

    # Publish to all 3 platforms
    res = hub.publish_to_all_platforms(db_session, ep.id, ver.id, force_simulation=True)
    assert len(res) == 3
    assert "youtube_shorts" in res
    assert "tiktok" in res
    assert "instagram_reels" in res
    assert res["youtube_shorts"].success is True
    assert res["tiktok"].success is True
    assert res["instagram_reels"].success is True


def test_maximum_publishing_scheduler_cycle(db_session, dummy_video):
    """Verify Maximum Publishing Mode identifies approved inventory and dispatches releases."""
    scheduler = PublishingScheduler()
    assert scheduler.maximum_publishing_mode is True

    # Check peak slots
    slots = scheduler.get_optimal_release_slots(count=4)
    assert len(slots) == 4
    for slot in slots:
        assert slot.hour in (11, 17)  # 11:30 or 17:00

    ep = Episode(code="EP001", title="Never Divide by Zero", concept_summary="Test")
    db_session.add(ep)
    db_session.commit()

    ver = EpisodeVersion(
        episode_id=ep.id,
        version_number=1,
        status="DRAFT",
        master_video_path=str(dummy_video),
        video_sha256="aaaa0000bbbb1111cccc2222dddd3333",
        math_verified=True,
    )
    db_session.add(ver)
    db_session.commit()

    # When unapproved, inventory is empty
    inv = scheduler.get_approved_unpublished_inventory(db_session)
    assert len(inv) == 0

    # Approve version
    approve_episode_version(db_session, ver, approved_by="owner_primary")
    inv = scheduler.get_approved_unpublished_inventory(db_session)
    assert len(inv) == 1
    assert inv[0][0].code == "EP001"

    # Run cycle
    cycle_res = scheduler.run_maximum_publishing_cycle(db_session, force_simulation=True)
    assert cycle_res["published_count"] == 1
    assert cycle_res["results"][0]["episode_code"] == "EP001"

    # Subsequent run finds zero unpublished
    cycle_res2 = scheduler.run_maximum_publishing_cycle(db_session, force_simulation=True)
    assert cycle_res2["published_count"] == 0


def test_sponsor_outreach_rate_card_and_pitch():
    """Verify CPM rate card calculations and pitch email generation."""
    rates = SponsorOutreachEngine.calculate_rate_card(projected_views_per_short=25000)
    assert rates["benchmark_cpm_usd"] == 32.0
    packages = rates["packages"]
    assert "standard_shoutout" in packages
    assert "dedicated_episode" in packages
    assert packages["standard_shoutout"]["rate_usd"] > 0

    desmos_brand = next(b for b in TARGET_SPONSOR_CATALOG if b.brand_name == "Desmos")
    pitch = SponsorOutreachEngine.generate_pitch_draft(desmos_brand, proposed_package="standard_shoutout")
    assert "Desmos" in pitch["subject"]
    assert "SymPy" in pitch["draft_body"]
    assert "partnerships@desmos.com" in pitch["contact_email"]


def test_sponsor_blacklist_filtering():
    """Verify that prohibited partnership categories are blocked by the safety firewall."""
    bad_brand = TargetSponsorBrand(
        brand_name="CryptoBet Forex Casino",
        category=SponsorCategory.STEM_APPS,
        contact_email="spam@cryptobet.com",
        product_focus="Automated crypto trading and casino games",
        relevance_pitch_hook="Earn crypto while watching math!",
        preferred_deliverable="Shoutout",
    )

    with pytest.raises(SafetyPolicyViolationError, match="prohibited safety blacklist"):
        SponsorOutreachEngine.generate_pitch_draft(bad_brand)


def test_sponsor_approval_firewall_lifecycle(db_session):
    """Verify that sponsor pitches start in PENDING_APPROVAL and strictly require owner signoff to send."""
    lead = SponsorOutreachEngine.create_pending_lead(
        session=db_session,
        brand_name="Brilliant.org",
        contact_email="sponsorships@brilliant.org",
        subject="Partnership Inquiry",
        draft_body="Draft content for Brilliant sponsorship.",
        proposed_terms="Package: Standard Shoutout | Rate: $600.00 USD",
    )

    assert lead.status == "PENDING_APPROVAL"
    assert lead.approved_by is None
    assert lead.approved_at is None

    # Database event guardrail prevents direct setting to SENT without approval fields
    lead.status = "SENT"
    with pytest.raises(SafetyPolicyViolationError, match="cannot be marked SENT without explicit owner approval"):
        db_session.commit()
    db_session.rollback()

    # Proper owner approval gate
    appr_res = SponsorOutreachEngine.approve_and_send_lead(
        session=db_session,
        lead_id=lead.id,
        approved_by="owner_primary",
    )

    assert appr_res["success"] is True
    assert appr_res["status"] == "SENT"
    assert appr_res["approved_by"] == "owner_primary"

    # Verify immutable ApprovalLog created
    appr_log = db_session.query(ApprovalLog).filter_by(target_id=lead.id).first()
    assert appr_log is not None
    assert appr_log.approved_by == "owner_primary"


def test_conversational_distribution_and_sponsor_intents():
    """Verify the Director agent handles natural language commands for publishing and sponsorships."""
    adapter = DirectorProductionAdapter()

    # 1. Distribution Intent
    res_pub = adapter.parse_intent("Publish Episode 001 across all channels in Maximum Publishing Mode")
    assert res_pub.intent == ConversationalIntent.DISTRIBUTE_EPISODE

    # 2. Sponsor Intent
    res_sp = adapter.parse_intent("Draft a sponsorship pitch for Desmos")
    assert res_sp.intent == ConversationalIntent.SPONSOR_PITCH
    assert res_sp.extracted_topic == "Desmos"

    # 3. Conversational Dispatch
    turn_res = adapter.handle_conversational_turn("Draft a sponsorship pitch for Desmos")
    assert turn_res["intent"] == "SPONSOR_PITCH"
    assert "Desmos" in turn_res["response_text"]
    assert "PENDING_APPROVAL" in turn_res["response_text"]
