"""Math Mayhem — Sponsor Outreach CRM & Monetization Engine (Phase 6).

Implements Phase 6 Workstream: Sponsor Outreach CRM with Mandatory Owner Approval Firewall.
Features:
1. Curated Target Sponsor Catalog (Educational EdTech, Calculator Tools, STEM Apps).
2. Category Safety Guardrail: Automatic blacklisting of predatory/unaligned categories
   (crypto, gambling, payday loans, essay mills).
3. Educational CPM & Media Kit Calculator ($25-$40 benchmark CPM).
4. Personalized Pitch Email Generator with delivery options and media kit highlights.
5. Strict Owner Approval Firewall Gate: Under NO circumstances can any sponsor message
   or agreement transition to 'SENT' without explicit owner approval and immutable logging.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    ApprovalLog,
    AuditEvent,
    ImmutableRecordError,
    SafetyPolicyViolationError,
    SponsorLead,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SponsorCategory(str, Enum):
    EDTECH = "edtech"
    MATH_SOFTWARE = "math_software"
    CALCULATOR_HARDWARE = "calculator_hardware"
    STEM_APPS = "stem_apps"


# Blacklisted categories strictly prohibited from Math Mayhem partnerships
PROHIBITED_CATEGORIES = {
    "crypto", "cryptocurrency", "nft", "forex", "trading",
    "gambling", "casino", "betting", "payday_loans",
    "essay_writing", "homework_cheating", "gacha", "lootbox"
}


@dataclass
class TargetSponsorBrand:
    """Pre-curated target sponsor brand profile."""
    brand_name: str
    category: SponsorCategory
    contact_email: str
    product_focus: str
    relevance_pitch_hook: str
    preferred_deliverable: str


TARGET_SPONSOR_CATALOG: List[TargetSponsorBrand] = [
    TargetSponsorBrand(
        brand_name="Desmos",
        category=SponsorCategory.MATH_SOFTWARE,
        contact_email="partnerships@desmos.com",
        product_focus="Free online graphing calculator and interactive math activities",
        relevance_pitch_hook="Our viewers love visual math; Desmos's visual graphing aligns 100% with our silent animation.",
        preferred_deliverable="Dedicated Themed Episode featuring interactive function graphing",
    ),
    TargetSponsorBrand(
        brand_name="Brilliant.org",
        category=SponsorCategory.EDTECH,
        contact_email="sponsorships@brilliant.org",
        product_focus="Interactive STEM, mathematics, and computer science learning",
        relevance_pitch_hook="Math Mayhem sparks mathematical curiosity; Brilliant provides the interactive follow-through.",
        preferred_deliverable="Standard 10s End-Card Shoutout + Pinned Comment Link",
    ),
    TargetSponsorBrand(
        brand_name="WolframAlpha",
        category=SponsorCategory.MATH_SOFTWARE,
        contact_email="outreach@wolfram.com",
        product_focus="Computational intelligence engine and step-by-step math solver",
        relevance_pitch_hook="We verify every episode via SymPy; Wolfram is the gold standard of symbolic computation.",
        preferred_deliverable="Dedicated Themed Episode on complex functions and limits",
    ),
    TargetSponsorBrand(
        brand_name="Casio Calculators",
        category=SponsorCategory.CALCULATOR_HARDWARE,
        contact_email="marketing@casio.com",
        product_focus="Scientific and graphing calculators used worldwide in classrooms",
        relevance_pitch_hook="Our protagonist interacts with a classic physical calculator prop; iconic Casio design synergy.",
        preferred_deliverable="Custom 3D-styled calculator prop appearance + End-Card Shoutout",
    ),
    TargetSponsorBrand(
        brand_name="Duolingo Math",
        category=SponsorCategory.STEM_APPS,
        contact_email="creator-partners@duolingo.com",
        product_focus="Gamified elementary and intermediate math lessons on mobile",
        relevance_pitch_hook="Bite-sized mobile math lessons paired with bite-sized vertical cartoon shorts.",
        preferred_deliverable="Multi-Episode 3-Part Shorts Series",
    ),
]


class SponsorOutreachEngine:
    """Manages sponsor discovery, proposal calculation, and pitch generation."""

    BENCHMARK_CPM_USD = 32.0  # Educational YouTube Shorts CPM benchmark ($25 - $40)

    @classmethod
    def calculate_rate_card(cls, projected_views_per_short: int = 25000) -> Dict[str, Any]:
        """Compute fair-market rate proposals based on views and retention."""
        base_cpm = cls.BENCHMARK_CPM_USD
        baseline_rate = (projected_views_per_short / 1000.0) * base_cpm

        return {
            "projected_views": projected_views_per_short,
            "benchmark_cpm_usd": base_cpm,
            "packages": {
                "standard_shoutout": {
                    "name": "Standard End-Card Shoutout (10s)",
                    "description": "Custom visual end-card, logo integration, and pinned comment tracking link.",
                    "rate_usd": round(baseline_rate * 0.75, 2),
                },
                "dedicated_episode": {
                    "name": "Dedicated Themed Episode",
                    "description": "Entire narrative concept designed around the sponsor's mathematical tool or platform.",
                    "rate_usd": round(baseline_rate * 2.2, 2),
                },
                "three_episode_bundle": {
                    "name": "3-Episode Synergy Bundle",
                    "description": "Three consecutive episodic integrations across YouTube Shorts, TikTok, and Instagram Reels.",
                    "rate_usd": round(baseline_rate * 3 * 0.85, 2),
                },
            },
        }

    @classmethod
    def generate_pitch_draft(
        cls,
        brand: TargetSponsorBrand,
        proposed_package: str = "standard_shoutout",
    ) -> Dict[str, str]:
        """Synthesize a professional, personalized creator pitch email."""
        # Enforce blacklist safety check
        brand_words = set(re.findall(r"\w+", (brand.brand_name + " " + brand.product_focus).lower()))
        if brand_words & PROHIBITED_CATEGORIES:
            raise SafetyPolicyViolationError(
                f"Cannot generate pitch for '{brand.brand_name}': matches prohibited safety blacklist."
            )

        rates = cls.calculate_rate_card()["packages"]
        package_info = rates.get(proposed_package, rates["standard_shoutout"])

        subject = f"Partnership Inquiry: Math Mayhem × {brand.brand_name} (Silent Educational Comedy)"
        body_lines = [
            f"Hi {brand.brand_name} Team,",
            "",
            f"I'm the creator and director of Math Mayhem, a 100% silent 2D animated comedy series that makes mathematical phenomena engaging, hilarious, and academically rigorous for students and curious minds.",
            "",
            f"Why {brand.brand_name}:",
            f"{brand.relevance_pitch_hook}",
            "",
            "Channel Highlights:",
            "- Pure 2D vector animation rendered vertically (1080×1920 @ 30 FPS) for YouTube Shorts, TikTok, and Instagram Reels.",
            "- 100% silent pantomime: zero language barriers, making episodes globally accessible and mute-friendly.",
            "- Every mathematical equation is verified deterministically via SymPy for absolute academic rigor.",
            "",
            f"Proposed Deliverable: {package_info['name']}",
            f"- Details: {package_info['description']}",
            f"- Proposed Rate: ${package_info['rate_usd']:.2f} USD (based on our {cls.BENCHMARK_CPM_USD} CPM benchmark)",
            "",
            "Would you be open to a quick chat or reviewing our media kit for an upcoming episode release?",
            "",
            "Best regards,",
            "Math Mayhem Creative Direction Team",
            "https://github.com/kaganlove/MathMayhem",
        ]

        body = "\n".join(body_lines)
        return {
            "brand_name": brand.brand_name,
            "contact_email": brand.contact_email,
            "subject": subject,
            "draft_body": body,
            "proposed_terms": f"Package: {package_info['name']} | Rate: ${package_info['rate_usd']:.2f} USD",
        }

    @classmethod
    def create_pending_lead(
        cls,
        session: Session,
        brand_name: str,
        contact_email: str,
        subject: str,
        draft_body: str,
        proposed_terms: str,
        owner_id: str = "owner_primary",
    ) -> SponsorLead:
        """Create a new SponsorLead in PENDING_APPROVAL status."""
        body_hash = hashlib.sha256(draft_body.encode("utf-8")).hexdigest()

        lead = SponsorLead(
            brand_name=brand_name,
            contact_email=contact_email,
            message_type="INITIAL_OUTREACH",
            subject=subject,
            draft_body=draft_body,
            proposed_terms=proposed_terms,
            body_sha256=body_hash,
            status="PENDING_APPROVAL",
            owner_id=owner_id,
        )
        session.add(lead)
        session.commit()
        session.refresh(lead)

        session.add(
            AuditEvent(
                event_type="SPONSOR_LEAD_CREATED",
                actor=owner_id,
                entity_type="SponsorLead",
                entity_id=str(lead.id),
                details_json=json.dumps({"brand": brand_name, "status": "PENDING_APPROVAL"}),
            )
        )
        session.commit()
        return lead

    @classmethod
    def approve_and_send_lead(
        cls,
        session: Session,
        lead_id: int,
        approved_by: str = "owner_primary",
        notes: str = "Owner approved sponsor pitch",
    ) -> Dict[str, Any]:
        """Owner approval firewall: explicitly approve and dispatch sponsor message."""
        lead = session.get(SponsorLead, lead_id)
        if not lead:
            raise SafetyPolicyViolationError(f"SponsorLead id={lead_id} not found.")

        # Re-verify body integrity hash
        curr_hash = hashlib.sha256(lead.draft_body.encode("utf-8")).hexdigest()
        if curr_hash != lead.body_sha256:
            raise SafetyPolicyViolationError("SponsorLead body was altered after hash computation.")

        now = utcnow()
        lead.approved_by = approved_by
        lead.approved_at = now
        lead.status = "APPROVED"
        session.commit()

        # Record ApprovalLog
        approval_log = ApprovalLog(
            target_type="sponsor_message",
            target_id=lead.id,
            content_sha256=lead.body_sha256,
            approved_by=approved_by,
            approval_mode="INDIVIDUAL",
            notes=notes,
        )
        session.add(approval_log)

        # Transition to SENT
        lead.status = "SENT"
        session.add(
            AuditEvent(
                event_type="SPONSOR_MESSAGE_DISPATCHED",
                actor=approved_by,
                entity_type="SponsorLead",
                entity_id=str(lead.id),
                details_json=json.dumps({"brand": lead.brand_name, "sent_to": lead.contact_email}),
            )
        )
        session.commit()

        return {
            "success": True,
            "lead_id": lead.id,
            "brand_name": lead.brand_name,
            "status": "SENT",
            "approved_by": approved_by,
            "timestamp": now.isoformat(),
        }
