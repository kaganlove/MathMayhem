# Math Mayhem — Active Blockers & Risks

## Current Active Gate (Not a Technical Failure — Planned Contract Gate)

| ID | Type | Description | Impact | Resolution / Action Required | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GATE-001** | **Owner Approval Gate** | Per `Math_Mayhem_Antigravity_Master_Prompt.md` ("First action in this Antigravity session" steps 4–5): Present proposed stack, costs, and tool installations for owner approval before starting Phase 1 implementation. | Blocks `T1.1`–`T1.9` until owner says "Proceed" / approves stack. | Owner approved stack (`DEC-001` to `DEC-006`) and Git initialization on 2026-11-11. | ✅ **RESOLVED** |

---

## Technical Risks & Mitigations Registry

| Risk ID | Category | Risk Description | Likelihood | Severity | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RISK-01** | Tooling | `ffmpeg` is not currently installed on `PATH`. Without `ffmpeg` (compiled with `--enable-nvenc`), video composition and RTX 5080 hardware encoding cannot run. | Confirmed | High | In `T1.2`, install FFmpeg (via `winget`/`scoop` or official gyan.dev/BtbN Windows build or `imageio-ffmpeg` bundle with NVENC support) and verify `h264_nvenc` against the RTX 5080. |
| **RISK-02** | Mathematical Accuracy | AI/LLM hallucinations could introduce subtle mathematical errors or false arithmetic explanations into scripts or visuals. | Medium | Critical | Enforce a deterministic `SymPy` mathematical verification gate (`MathVerifier`) in Phase 3+. Any expression shown on screen is symbolically validated; `10 / 0` and `0 / 0` are strictly enforced as `UNDEFINED` in ordinary arithmetic. |
| **RISK-03** | Character Consistency | Generative image/video models drift in character design (adding pupils, changing hair/beard, adding a backpack). | High (if using diffusion) | High | Do **not** use unguided diffusion for character animation. Build a **deterministic parametric 2D vector/skeletal rig** (Phase 2) so the stick-figure adventurer (messy short hair, short beard, blank-lens glasses, no pupils, no backpack, silent) is 100% consistent across every frame and episode. |
| **RISK-04** | Copyright / Content-ID | Third-party music or sound effects could trigger copyright claims or lack commercial/sponsorship clearance. | Low | High | Synthesize the 3–5s original musical signature and core SFX procedurally in Python DSP (`DEC-003`), and require explicit provenance + commercial/sponsored license records in the database for every asset. |
| **RISK-05** | Platform API Quotas & TikTok Direct Post | TikTok Direct Post requires app audit and often rejects private single-owner automated tools; YouTube Data API v3 default quota limits daily uploads (~6 uploads/day at 1,600 units/upload out of 10,000 default). | High | Medium | Never promise unverified API quotas. Build platform adapters (Phase 6) with explicit quota tracking, rate limiting, and a first-class **Compliant Scheduler / Manual Package Export Fallback** when direct API approval is pending or restricted. |
| **RISK-06** | Unapproved External Actions | Bug or bulk operation accidentally publishes an unapproved video or sends a substantive sponsor email. | Low | Critical | Enforce database-level and service-level `ApprovalGate`: every publish call requires an immutable `ApprovalLog` matching the exact `episode_id` + `version_id` + `video_sha256`; every substantive sponsor email stays locked until its exact recipient, body hash, and terms are approved. |
