"""Integration and unit tests for Phase 7 Analytics, Financial Tracking & Growth Optimization."""

from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.analytics_engine import (
    CommentModerationService,
    ExecutiveReportCompiler,
    FinancialTracker,
    PerformanceTracker,
    TopicRecommendationEngine,
)
from app.database import Base
from app.director_adapter import ConversationalIntent, DirectorProductionAdapter
from app.director_memory import DirectorMemoryEngine
from app.models import (
    AudienceComment,
    Episode,
    EpisodeVersion,
    ExecutiveReport,
    PerformanceMetric,
    SafetyPolicyViolationError,
    SponsorLead,
)


@pytest.fixture
def db_session(tmp_path):
    """Provide an isolated SQLite database and test session."""
    db_file = tmp_path / "test_analytics.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    with session_factory() as session:
        yield session


def test_financial_tracker_zero_compute_and_margin(db_session):
    """Verify $0.00 local compute invariant, 100% net margin, and $500/mo milestone tracking."""
    # Seed platform metric with ad revenue
    m1 = PerformanceMetric(
        episode_code="EP001",
        platform="youtube_shorts",
        views=50000,
        likes=4500,
        comments=320,
        shares=850,
        average_retention_pct=92.5,
        estimated_revenue_usd=160.00,
    )
    db_session.add(m1)

    # Seed an approved sponsor lead
    body = "Hi Desmos team, we'd love to feature graphing calculator antics in Math Mayhem."
    import hashlib
    lead = SponsorLead(
        brand_name="Desmos",
        contact_email="partnerships@desmos.com",
        subject="Math Mayhem x Desmos",
        draft_body=body,
        body_sha256=hashlib.sha256(body.encode()).hexdigest(),
        proposed_terms="Integration Rate: $600.00 USD for standard end-card",
        status="APPROVED",
    )
    db_session.add(lead)
    db_session.commit()

    fin = FinancialTracker.calculate_financial_summary(db_session)
    assert fin["monthly_target_usd"] == 500.0
    assert fin["ad_revenue_usd"] == 160.00
    assert fin["sponsor_revenue_usd"] == 600.00
    assert fin["gross_revenue_usd"] == 760.00
    assert fin["operating_compute_cost_usd"] == 0.00  # Local RTX 5080 hardware
    assert fin["net_profit_usd"] == 760.00
    assert fin["profit_margin_pct"] == 100.0
    assert fin["milestone_achieved"] is True
    assert fin["milestone_progress_pct"] == 100.0


def test_performance_tracker_aggregation(db_session):
    """Verify multi-platform metric ingestion and dashboard summary aggregation."""
    # Ingest metrics across YouTube Shorts, TikTok, and Instagram Reels
    PerformanceTracker.record_episode_metrics(
        session=db_session,
        episode_code="EP001",
        platform="youtube_shorts",
        views=45000,
        likes=3800,
        comments=290,
        shares=610,
        retention_pct=88.0,
        ad_revenue=144.0,
    )
    PerformanceTracker.record_episode_metrics(
        session=db_session,
        episode_code="EP001",
        platform="tiktok",
        views=35000,
        likes=4200,
        comments=180,
        shares=950,
        retention_pct=82.5,
        ad_revenue=70.0,
    )
    PerformanceTracker.record_episode_metrics(
        session=db_session,
        episode_code="EP001",
        platform="instagram_reels",
        views=20000,
        likes=1900,
        comments=95,
        shares=340,
        retention_pct=85.0,
        ad_revenue=64.0,
    )

    summary = PerformanceTracker.get_dashboard_summary(db_session)
    assert summary["total_views"] == 100000
    assert summary["total_likes"] == 9900
    assert summary["total_comments"] == 565
    assert summary["total_shares"] == 1900
    assert round(summary["average_retention_pct"], 1) == 85.2
    assert summary["platforms"]["youtube_shorts"]["views"] == 45000
    assert summary["platforms"]["tiktok"]["views"] == 35000
    assert summary["platforms"]["instagram_reels"]["views"] == 20000


def test_topic_recommendation_engine():
    """Verify data-driven topic recommendations return high-virality candidates with SymPy rigor."""
    recs = TopicRecommendationEngine.get_recommendations(count=4)
    assert len(recs) == 4
    # All topics must have positive projected virality scores
    for r in recs:
        assert r["projected_virality_score"] >= 80
        assert "premise" in r
        assert "sympy_validation" in r
        assert "category" in r
    # First recommendation should be top scoring
    assert recs[0]["projected_virality_score"] >= recs[1]["projected_virality_score"]


def test_comment_moderation_ingest_and_sentiment(db_session):
    """Verify comment ingestion, math question classification, and on-brand draft replies."""
    comment = CommentModerationService.ingest_comment(
        session=db_session,
        episode_code="EP001",
        platform="youtube_shorts",
        author="MathGeek42",
        comment_text="Why does dividing by zero break math? Can you explain 0/0?",
    )

    assert comment.id is not None
    assert comment.status == "PENDING_REVIEW"
    assert comment.math_question is True
    assert comment.sentiment == "CURIOUS"
    assert "paradox" in comment.draft_reply.lower() or "arithmetic" in comment.draft_reply.lower()


def test_comment_moderation_owner_approval_firewall(db_session):
    """Verify owner approval firewall for dispatched comments."""
    comment = CommentModerationService.ingest_comment(
        session=db_session,
        episode_code="EP002",
        platform="tiktok",
        author="GeometryLover",
        comment_text="Wait so multiplying by i is really a 90 degree rotation?!",
    )
    assert comment.status == "PENDING_REVIEW"

    # Approving dispatches the comment safely
    result = CommentModerationService.approve_reply(
        session=db_session,
        comment_id=comment.id,
        approved_by="owner_primary",
    )
    assert result["success"] is True
    assert result["status"] == "SENT"
    assert result["approved_by"] == "owner_primary"

    # Reject non-existent comment
    with pytest.raises(SafetyPolicyViolationError):
        CommentModerationService.approve_reply(session=db_session, comment_id=999999)


def test_executive_report_compiler(db_session):
    """Verify automated weekly executive report generation and DB persistence."""
    # Seed metrics
    PerformanceTracker.record_episode_metrics(
        session=db_session,
        episode_code="EP001",
        platform="youtube_shorts",
        views=60000,
        likes=5000,
        comments=400,
        shares=1200,
        retention_pct=90.0,
        ad_revenue=192.0,
    )

    report = ExecutiveReportCompiler.compile_weekly_report(db_session, period_days=7)
    assert report.id is not None
    assert "Weekly Executive Summary" in report.report_title
    assert report.total_views == 60000
    assert report.total_ad_revenue_usd == 192.0
    assert report.milestone_progress_pct == 38.4
    assert "# Math Mayhem — Executive Summary" in report.summary_markdown
    assert "100% Local GPU RTX 5080" in report.summary_markdown


def test_conversational_director_phase7_intent_dispatch(tmp_path):
    """Verify Director agent responds conversationally to Phase 7 analytics queries."""
    db_file = tmp_path / "director_phase7.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    mem_engine = DirectorMemoryEngine(session_factory=session_factory)
    adapter = DirectorProductionAdapter(memory_engine=mem_engine)

    # 1. Financial query intent
    r1 = adapter.handle_conversational_turn("How are our financials doing toward the $500 milestone?")
    assert r1["intent"] == ConversationalIntent.FINANCIAL_QUERY
    assert "$500.00 USD" in r1["response_text"]
    assert "Local GPU RTX 5080" in r1["response_text"]

    # 2. Topic recommendation query intent
    r2 = adapter.handle_conversational_turn("What should we make next based on audience data?")
    assert r2["intent"] == ConversationalIntent.RECOMMENDATION_QUERY
    assert "Recommendations" in r2["response_text"]
    assert len(r2["artifacts"]["recommendations"]) == 3

    # 3. Comment moderation query intent
    r3 = adapter.handle_conversational_turn("Show me audience comments and questions")
    assert r3["intent"] == ConversationalIntent.COMMENT_MODERATION
    assert "Audience Comment" in r3["response_text"]

    # 4. Executive report generation query intent
    r4 = adapter.handle_conversational_turn("Compile a weekly executive report on channel health")
    assert r4["intent"] == ConversationalIntent.REPORT_GENERATION
    assert "Executive Report Generated" in r4["response_text"]
