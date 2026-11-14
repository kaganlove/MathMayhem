"""Execute end-to-end demonstration for Phase 7 Analytics, Financial Tracking & Optimization.

Demonstrates:
1. Multi-platform engagement telemetry ingestion across YouTube Shorts, TikTok, and Instagram Reels.
2. Financial Tracking & $0.00 compute cost calculation, verifying 100% net margin.
3. Tracking progress toward the $500.00/month recurring revenue milestone.
4. Algorithmic topic recommendations for upcoming episodes based on engagement and SymPy rigor.
5. Audience comment ingestion, sentiment classification, math question detection, and witty draft replies.
6. The Owner Approval Firewall Gate: approving and dispatching comment replies safely.
7. Automated Weekly Executive Report compilation and persistence.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.analytics_engine import (
    CommentModerationService,
    ExecutiveReportCompiler,
    FinancialTracker,
    PerformanceTracker,
    TopicRecommendationEngine,
)
from app.config import get_settings
from app.database import create_db_engine, init_db, make_session_factory
from app.models import AudienceComment, Episode, PerformanceMetric, SponsorLead


def run_phase7_demo() -> None:
    print("=" * 80)
    print("MATH MAYHEM — PHASE 7 ANALYTICS, FINANCIAL TRACKING & GROWTH OPTIMIZATION")
    print("=" * 80)

    settings = get_settings()
    engine = create_db_engine()
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        # Step 1: Ingest multi-platform telemetry for EP001 and EP002
        print("\n[Step 1] Ingesting multi-platform telemetry across YouTube, TikTok, and Instagram...")
        PerformanceTracker.record_episode_metrics(
            session=session,
            episode_code="EP001",
            platform="youtube_shorts",
            views=62400,
            likes=5310,
            comments=420,
            shares=1180,
            retention_pct=91.4,
            ad_revenue=199.68,
        )
        PerformanceTracker.record_episode_metrics(
            session=session,
            episode_code="EP001",
            platform="tiktok",
            views=48200,
            likes=5980,
            comments=310,
            shares=1420,
            retention_pct=84.2,
            ad_revenue=96.40,
        )
        PerformanceTracker.record_episode_metrics(
            session=session,
            episode_code="EP001",
            platform="instagram_reels",
            views=28500,
            likes=2740,
            comments=145,
            shares=520,
            retention_pct=86.8,
            ad_revenue=91.20,
        )
        # EP002 preview performance
        PerformanceTracker.record_episode_metrics(
            session=session,
            episode_code="EP002",
            platform="youtube_shorts",
            views=31200,
            likes=2890,
            comments=260,
            shares=640,
            retention_pct=89.5,
            ad_revenue=99.84,
        )
        print("  ✓ Telemetry successfully recorded across all platforms.")

        # Step 2: Financial Tracking & $500/Month Milestone Status
        print("\n[Step 2] Evaluating financial tracking and local compute efficiency...")
        fin = FinancialTracker.calculate_financial_summary(session)
        print(f"  - Target Monthly Recurring Revenue: ${fin['monthly_target_usd']:.2f} USD")
        print(f"  - Total Gross Revenue (30d):       ${fin['gross_revenue_usd']:.2f} USD")
        print(f"    - Platform AdSense:              ${fin['ad_revenue_usd']:.2f} USD")
        print(f"    - Brand Sponsorships:            ${fin['sponsor_revenue_usd']:.2f} USD")
        print(f"  - Operating Compute Costs:         ${fin['operating_compute_cost_usd']:.2f} USD (100% Local RTX 5080 NVENC)")
        print(f"  - Net Profit:                      ${fin['net_profit_usd']:.2f} USD ({fin['profit_margin_pct']:.0f}% Margin)")
        gap_str = f"${fin['gap_to_milestone_usd']:.2f} remaining"
        status_str = "✅ ACHIEVED" if fin["milestone_achieved"] else gap_str
        print(f"  - Milestone Progress:              {fin['milestone_progress_pct']}% ({status_str})")

        # Step 3: Algorithmic Topic Recommendations
        print("\n[Step 3] Querying data-driven topic recommendations for upcoming episodes...")
        recs = TopicRecommendationEngine.get_recommendations(3)
        for i, rec in enumerate(recs, 1):
            print(f"  {i}. {rec['topic']} [{rec['category']}]")
            print(f"     Virality Score: {rec['projected_virality_score']}/100")
            print(f"     Premise: {rec['premise']}")
            print(f"     SymPy Validation: {rec['sympy_validation']}")

        # Step 4: Audience Comment Moderation & Drafting
        print("\n[Step 4] Ingesting audience questions & staging polite/witty draft replies...")
        c1 = CommentModerationService.ingest_comment(
            session=session,
            episode_code="EP001",
            platform="youtube_shorts",
            author="MathLover_99",
            comment_text="Why does dividing by zero cause the calculator to explode?",
        )
        c2 = CommentModerationService.ingest_comment(
            session=session,
            episode_code="EP002",
            platform="tiktok",
            author="ComplexPlaneFan",
            comment_text="Is multiplying by i really rotating 90 degrees? What if you multiply by i twice?",
        )
        print(f"  - Ingested Comment 1 by @{c1.author} ({c1.sentiment}): \"{c1.comment_text}\"")
        print(f"    Draft Reply (Status: {c1.status}): \"{c1.draft_reply}\"")
        print(f"  - Ingested Comment 2 by @{c2.author} ({c2.sentiment}): \"{c2.comment_text}\"")
        print(f"    Draft Reply (Status: {c2.status}): \"{c2.draft_reply}\"")

        # Step 5: Owner Approval Gate for Comment Replies
        print("\n[Step 5] Triggering Owner Approval Gate to dispatch comment reply...")
        approval_res = CommentModerationService.approve_reply(
            session=session,
            comment_id=c1.id,
            approved_by="owner_primary",
        )
        print(f"  ✓ Comment reply approved by {approval_res['approved_by']} and dispatched to @{approval_res['author']}!")
        print(f"    Final Status: {approval_res['status']}")

        # Step 6: Weekly Executive Summary Report Generation
        print("\n[Step 6] Compiling Weekly Executive Report...")
        report = ExecutiveReportCompiler.compile_weekly_report(session, period_days=7)
        print(f"  ✓ Generated: {report.report_title}")
        print(f"    Total Multi-Platform Views: {report.total_views:,}")
        print(f"    Total Net Profit:           ${report.net_profit_usd:.2f} USD")
        print(f"    $500/Mo Milestone Progress: {report.milestone_progress_pct}%")

        # Save report markdown to file
        report_path = ROOT_DIR / "renders" / "reports" / "weekly_executive_summary_latest.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report.summary_markdown, encoding="utf-8")
        print(f"    Report Markdown Artifact:   {report_path}")

    print("\n" + "=" * 80)
    print("PHASE 7 DEMONSTRATION COMPLETE — 100% SUCCESS")
    print("=" * 80)


if __name__ == "__main__":
    run_phase7_demo()
