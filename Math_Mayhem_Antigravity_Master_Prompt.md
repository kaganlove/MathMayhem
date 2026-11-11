# MATH MAYHEM — ANTIGRAVITY MASTER BUILD PROMPT
Version 1.0 — 11 November 2026

## Role and execution contract
Act as principal architect, engineer, technical producer, animator, QA lead and project manager. Build a private, owner-operated, largely automated animation and media business called **Math Mayhem**. The owner has a CLX desktop with an NVIDIA RTX 5080 and wants secure phone-based control. Design for possible multi-user expansion later, but do not build multi-tenancy now.

**Start with Phase 1 only.** Before coding, inspect the actual OS, GPU, drivers, tools, storage and installed software. Propose a stack with trade-offs and ask approval for paid services, destructive changes, account permissions and architecture decisions with material cost. Do not assume APIs, model licenses, platform quotas or integration permissions are available. Never claim completion without passing acceptance tests.

Break all work into small, independently testable tasks. Persist `PROJECT_STATUS.md`, `TASKS.md`, `DECISIONS.md`, `ARCHITECTURE.md`, `TEST_RESULTS.md`, `BLOCKERS.md`, and `RUNBOOK.md`. Each task has owner, prerequisites, status (not started/in progress/blocked/testing/completed), acceptance criteria, evidence and next action. Resume from last verified checkpoint. Maintain git commits, backups, reproducible setup and a changelog.

## Creative bible
**Math Mayhem** is funny, visually clear, mostly dialogue-free mathematical adventure. The main character is a simple stick-figure adventurer with messy short hair, short beard, blank-lens glasses (no pupils), and **no backpack**. Curious, intelligent, impulsive and expressive through posture, gesture and timing; **never speaks or vocalizes**. No narrator. Videos must work muted. Environments are flexible; a chalkboard may recur but is not mandatory. Humor comes from mathematically accurate concepts interacting with exaggerated fictional consequences. Never present incorrect arithmetic as true. Show mathematical notation clearly and validate it. Avoid rote educational lectures.

Create a recognizable **original** 3–5-second musical signature with playful, suspense, chaos and ending variations. Sound effects can be procedural, locally generated, or from rights-cleared libraries. Maintain source/license/provenance records for every sound and music asset; verify commercial and sponsored-use rights. Do not imitate copyrighted themes.

Content formats: 9:16 short discovery videos (~15–45 sec); extended originals (>60 sec when relevant to program eligibility); 16:9 longer YouTube episodes/compilations where appropriate. Use original, varied stories; avoid repetitive mass-produced content. Provide captions, thumbnails and platform-specific packaging.

## Episode 001: Never Divide by Zero
**Pilot goal:** a ten-second animation proof of concept before full episode production. 1080x1920, 30 fps, 300 frames, white environment, black line art, red error accent, silent character, readable calculator, original musical motif.
Storyboard (initial timing, refine for readable interaction):
- 0–2 s: calculator appears in a simple environment; curious musical motif.
- 2–4 s: adventurer enters, notices it, tilts head.
- 4–6 s: enters `10 ÷ 2 =`; display `5`, pleasant beep.
- 6–8 s: enters `10 ÷ 1 =`; display `10`, slightly faster sound.
- 8–10 s: enters `10 ÷ 0 =`; display `UNDEFINED`; music cuts, error tone, character freezes.
The calculator can display full expressions at once to ensure legibility. In ordinary arithmetic, 10/0 is undefined. Do not depict a numerical answer.
**Full episode continuation:** calculator glitches; a cartoon void opens (explicitly fantasy metaphor, not a literal mathematical consequence); character scrambles to clear it; reality resets; final cliffhanger `0 ÷ 0 = ?`, also undefined. No false math explanations.
For pilot, render low-res preview, check exact frame count, notation, character consistency, timing, audio sync, media integrity; request owner approval before final 1080x1920 render. Keep source projects and assets.

## Architecture requirements
Use modular components: mobile-responsive dashboard; structured episode/scene model; script/storyboard agent; mathematical verifier; animation asset registry and character rig; scene renderer; audio/SFX/music engine; FFmpeg composition; QC; content library; approval workflow; publishing adapters; analytics; sponsor CRM; notification service; job queue; database and audit logs. Evaluate Python, Blender, Manim, FFmpeg, and web technologies based on actual compatibility; do not blindly install all. Prefer local GPU rendering where useful and economical. Secure remote access with authentication and encrypted credentials, OAuth and least-privilege scopes; never expose an unsecured local service. Queue tasks persistently across restarts, support retries/idempotency, handle offline desktop gracefully. Keep episode versions immutable after approval.

## Seven phases and acceptance gates

### Phase 1 — Foundation
Inspect environment; choose stack; create repository, configuration, project files, database, asset directories, test harness, local dashboard shell, GPU render smoke test, logs, backup and runbook. Acceptance: reproducible setup, basic dashboard runs, simple test render completes, tests documented. **Stop and request review.**

### Phase 2 — Character animation
Create canonical character model sheet, reusable vector/rig assets, pose library, walk/run/reaction/gesture motions, prop interactions, consistent camera framing and preview pipeline. Acceptance: character remains visually consistent across at least three movements and two scenes. **Stop and request review.**

### Phase 3 — Mathematical animation
Support exact notation, algebra, graphs, geometry, mathematical props, scene synchronization and symbolic/numerical validation. Separate correct math from fictional effects. Build and test Episode 001 opening ten seconds. Acceptance: mathematical verification, frame-perfect render and owner approval. **Stop and request review.**

### Phase 4 — AI production agents
Implement structured pipeline for research, ideas, script, storyboard, math verification, scene planning, animation, audio, render, QA and packaging. Use clear schemas and per-stage logs. Support revision requests and cost tracking. Music agent creates original brand motif and variations; SFX agent uses rights-cleared sources; mixer syncs events and checks levels. Acceptance: one full pilot episode produced end-to-end with review checkpoints and source files retained. **Stop and request review.**

### Phase 5 — Remote phone control
Mobile-friendly dashboard for text/voice episode ideas, progress, previews, approvals, revisions, batch approvals, notifications, library and sponsor proposals. Secure remote access and recovery after disconnection. Acceptance: owner can submit an idea from phone, see status and approve a test preview securely. **Stop and request review.**

### Phase 6 — Account onboarding, distribution, monetization and sponsors
Create **guided account setup wizard** with exact current field-by-field instructions for YouTube channel, Instagram professional account/Meta assets, TikTok account type and authorized scheduler, business email, developer console and payment/tax setup when eligible. Owner personally creates/verifies accounts and authorizes OAuth. Never request or store account passwords.

Create platform-specific adapters, permission checks, video validation, caption/title/description/hashtag/thumbnail generation, scheduling, upload logs, post IDs, retries and duplicate prevention. Verify **current official documentation** and account-specific quotas at integration time. Do not treat an API quota as guaranteed channel capacity. TikTok private single-account Direct Post tools may not qualify for approval; implement compliant approved scheduler/manual fallback rather than bypassing restrictions.

**Publishing policy:** Owner approves every episode individually or as an explicitly enumerated batch. After approval, Maximum Publishing Mode may publish those exact approved versions **publicly** at the highest verified permitted daily frequency per platform when inventory exists. Maintain independent quotas, rate limiting and schedules. Respect account health, platform rules and technical constraints. Do not promise maximum daily API quota equals safe public publishing rate. Track performance and recommend adjustments, but don't silently override owner's publishing strategy except to prevent violations or failures. Optionally target a 30-day approved reserve. Support local library and on-platform publication separately.

**Business model:** initially ads and sponsorships only; no products/merchandise until owner chooses expansion. Track platform monetization eligibility from current official rules; note Shorts watch-time distinctions, TikTok video length/originality requirements, sponsored-content disclosures and changing program rules. Goal: recurring $500/month, aspirational 6–12 months after launch, **not guaranteed**. Record revenue, costs and net profit.

**Sponsor agent:** research relevant brands and verified contacts, recommend rates and negotiation strategy, draft individualized outreach, counteroffers, media kits, contracts review summaries and CRM updates. Automatically send **only neutral administrative acknowledgments** if explicitly configured. **All initial outreach, substantive replies, rates, negotiations, counteroffers and contract discussions require approval of the exact recipient, message and terms before sending.** Approved messages are immutable. Never autonomously sign contracts, accept binding terms, promise deliverables, agree to exclusivity or pay money. Audit every action and comply with email/anti-spam rules. Acceptance: authorized test publishing per supported platform (or documented fallback), correct approval gate, no duplicates, sponsor dry-run proves no substantive email sent without approval. **Stop and request review.**

### Phase 7 — Analytics and optimization
Dashboard: produced/approved/published inventory, views, retention, engagement, followers/subscribers, eligible watch time, monetization thresholds, platform revenue, sponsorship pipeline, costs, net profit, posting performance, API/account health. Agents recommend topic selection, scheduling, publishing frequency, creative changes, sponsor targets and weekly summaries. Monitor comments and draft responses; substantive external replies require review. Acceptance: real authorized metrics or clearly labeled simulated data, traceable recommendations and reliable weekly report.

## Global guardrails
- Never publish an unapproved video, including via a bulk action that omits its episode ID/version.
- Never send substantive sponsorship correspondence without exact-message approval.
- No copyrighted third-party media without documented commercial rights.
- Do not present invented platform limits, API access, earnings or view metrics as verified.
- Never evade rate limits or platform review.
- Do not automatically incur charges or sign contracts.
- Protect account tokens, personal information and private production assets.
- Automated tests, human approval and evidence are required before a phase is marked complete.

## First action in this Antigravity session
1. Read this entire specification and restate the architecture, dependencies, risks and seven phase gates in concise form.
2. Inspect this machine and identify feasible tools and GPU support.
3. Create the persistent tracker and break **Phase 1** into small tasks with acceptance tests.
4. Present a proposed stack and any costs/permissions for approval.
5. Start Phase 1 after approval. **Do not start later phases yet.**
