# Math Mayhem — Task Tracker

**Status Legend:** `not started` | `in progress` | `blocked` | `testing` | `completed`

---

## Pre-Phase 1 — Discovery & Planning

| Task ID | Title | Owner | Prerequisites | Status | Acceptance Criteria | Evidence | Next Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T0.1** | Environment & Hardware Inspection | Agent (Architect) | None | `completed` | OS, CPU, GPU, CUDA, RAM/Disk, Python, Node, Git, FFmpeg, Blender inspected and recorded. | `ARCHITECTURE.md` §1 (Environment Inventory) | None |
| **T0.2** | Initialize Persistent Tracking Docs | Agent (PM) | T0.1 | `completed` | `PROJECT_STATUS.md`, `TASKS.md`, `DECISIONS.md`, `ARCHITECTURE.md`, `TEST_RESULTS.md`, `BLOCKERS.md`, `RUNBOOK.md` created on disk. | All 7 files present in workspace root. | None |
| **T0.3** | Propose Stack & Request Owner Approval | Agent (Architect) | T0.1, T0.2 | `completed` | Stack options, trade-offs, cost/permission implications documented in `DECISIONS.md` and approved by owner. | `DECISIONS.md` (`DEC-001` to `DEC-006` marked `APPROVED`) | Completed |

---

## Phase 1 — Foundation
*Goal: Inspect environment; choose stack; create repository, configuration, project files, database, asset directories, test harness, local dashboard shell, GPU render smoke test, logs, backup and runbook.*

| Task ID | Title | Owner | Prerequisites | Status | Acceptance Criteria | Evidence | Next Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T1.1** | Repository & Directory Scaffolding | Agent (Engineer) | T0.3 | `completed` | Git repo initialized (`main` branch), `.gitignore` configured, standard directories (`app/`, `assets/`, `renders/`, `data/`, `backups/`, `logs/`, `tests/`, `scripts/`), `CHANGELOG.md` created, initial commit recorded. | Commit `0a61c2c`, `tests/test_env.py::test_git_repository_initialized` | Completed |
| **T1.2** | Python Environment & FFmpeg/NVENC Provisioning | Agent (Engineer) | T1.1 | `completed` | Reproducible `.venv` with pinned dependencies (`requirements.txt`); FFmpeg v9.0.2 binary with `h264_nvenc` / `hevc_nvenc` / `av1_nvenc` verified against RTX 5080; `sympy`, `pytest`, `numpy`, `scipy`, `pillow` installed. | `tests/test_env.py` (5/5 passed) | Completed |
| **T1.3** | Configuration, Secrets Encryption & Structured Logging | Agent (Engineer) | T1.2 | `completed` | Pydantic `Settings` (`app/config.py`) loads `.env`; Fernet credential vault (`app/security.py`) encrypts/decrypts secrets at rest and detects tampering; rotating JSON logger (`app/logging_config.py`) writes to `logs/math_mayhem.log`. | `tests/test_config_security.py` (3/3 passed) | Completed |
| **T1.4** | Database Schema, Immutable Versioning & Audit Log | Agent (Engineer) | T1.3 | `completed` | SQLite WAL database (`data/math_mayhem.db`) via SQLAlchemy 2.0 (`app/database.py`, `app/models.py`); tables for `Episode`, `EpisodeVersion` (immutable once approved), `Scene`, `Asset` (mandatory provenance/license fields), `Job`, `ApprovalLog`, `SponsorLead`, `AuditEvent`. | `tests/test_database.py` (2/2 passed) | Completed |
| **T1.5** | Persistent Job Queue Worker & Recovery | Agent (Engineer) | T1.4 | `completed` | SQLite-backed persistent job queue (`app/queue.py`) supporting idempotency keys, retries with exponential backoff, and crash recovery of stranded `RUNNING` jobs across restarts. | `tests/test_job_queue.py` (1/1 passed) | Completed |
| **T1.6** | GPU & FFmpeg Render Smoke Test Pipeline | Agent (Animator / Engineer) | T1.2, T1.5 | `completed` | Synthetic 2-second (60-frame, `1080x1920`, `30fps`) test animation rendered via Python frame generator (`app/render_smoke.py`) + RTX 5080 `h264_nvenc` and procedural WAV audio muxed; verified exact resolution, frame count, FPS, and AAC audio stream. | `tests/test_render_smoke.py` & `renders/smoke_test.mp4` (`82,015` bytes) | Completed |
| **T1.7** | Local Mobile-Responsive Dashboard Shell & Auth | Agent (Engineer) | T1.4, T1.5, T1.6 | `completed` | FastAPI web app (`app/main.py`, `app/templates/dashboard.html`) with token/session authentication (`401` on unauthenticated requests), health telemetry (RTX 5080/Disk/Queue), episode/job status view, and one-click GPU Smoke Test trigger. | `tests/test_dashboard_api.py` (1/1 passed) | Completed |
| **T1.8** | Automated Backup & Restore Utility | Agent (Engineer) | T1.4 | `completed` | `scripts/backup.py` performs online SQLite backup (`sqlite3.Connection.backup`), snapshots configuration/vault manifests into timestamped archives in `backups/`, and verifies checksum + SQLite `PRAGMA integrity_check` on restore. | `tests/test_backup.py` (1/1 passed) | Completed |
| **T1.9** | Phase 1 Full Acceptance Suite & Gate Review | Agent (QA Lead) | T1.1–T1.8 | `completed` | 100% of Phase 1 automated tests pass (14/14); `TEST_RESULTS.md`, `RUNBOOK.md`, `PROJECT_STATUS.md` updated; clean git checkpoint committed; owner approved Phase 1 gate. | `TEST_RESULTS.md` (14 passed), Owner Approved | Completed |

---

## Phase 2 — Character Animation
*Goal: Create canonical character model sheet, reusable vector/rig assets, pose library, walk/run/reaction/gesture motions, prop interactions, consistent camera framing and preview pipeline. Acceptance: character remains visually consistent across at least three movements and two scenes. Stop and request review.*

| Task ID | Title | Owner | Prerequisites | Status | Acceptance Criteria | Evidence | Next Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T2.1** | Canonical Character Spec & Parametric Rig (`app/character_rig.py`) | Agent (Animator / Engineer) | T1.9 | `completed` | Enforces messy short hair (deterministic spike geometry), short beard, blank-lens glasses (explicit `has_pupils=False`), `has_backpack=False`, `speaks=False`, `vocalizes=False`, `narrator=False`, hierarchical joints (pelvis, torso, neck, head, shoulders, elbows, hands, hips, knees, feet), and renders canonical multi-pose model sheet (`assets/character/canonical_model_sheet.png` + `.json`) registered in DB `Asset` table. | `tests/test_character_animation.py` (passed) | Completed |
| **T2.2** | Pose Library & Motion Solvers (≥3 Movements + Prop Interaction) | Agent (Animator) | T2.1 | `completed` | Implements reusable poses (`idle`, `curious_tilt`, `typing_reach`, `freeze_shock`, `scramble_panic`) and continuous motion solvers (`walk`, `run`, `head_tilt_gesture`, `button_press_prop_interaction`, `freeze_reaction`) with smooth interpolation. | `tests/test_character_animation.py` (passed) | Completed |
| **T2.3** | Multi-Scene Framing, Prop Interaction & Consistency Validator (`app/character_scenes.py`) | Agent (Animator / QA) | T2.2 | `completed` | Renders ≥2 distinct environments (`scene_white_calculator`, `scene_chalkboard_lab`) across 5 movements (`walk`, `head_tilt_gesture`, `button_press_prop_interaction`, `freeze_reaction`, `run`) into an RTX 5080 NVENC preview (`renders/previews/phase2_character_showcase.mp4`) and validates visual consistency across frames. | `tests/test_character_animation.py` & `renders/previews/phase2_character_showcase.mp4` | Completed |
| **T2.4** | Dashboard Integration for Character Model Sheet & Showcase Preview | Agent (Engineer) | T2.3 | `completed` | Dashboard serves `/api/character/spec`, `/api/character/model-sheet`, and `/api/character/render-showcase` so owner can inspect character invariants and trigger/view the Phase 2 showcase preview. | `tests/test_character_animation.py::test_dashboard_character_endpoints` (passed) | Completed |
| **T2.5** | Phase 2 Full Acceptance Suite, Git Commit & Gate Review | Agent (QA Lead) | T2.1–T2.4 | `completed` | All 19 Phase 1 + Phase 2 tests pass (`4.97s`); `TEST_RESULTS.md`, `PROJECT_STATUS.md`, `CHANGELOG.md` updated; committed and pushed to `origin/main`; owner approved Phase 2 gate. | `TEST_RESULTS.md` (19 passed), Owner Approved | Completed |

---

## Phase 3 — Mathematical Animation
*Goal: Support exact notation, algebra, graphs, geometry, mathematical props, scene synchronization and symbolic/numerical validation. Separate correct math from fictional effects. Build and test Episode 001 opening ten seconds. Acceptance: mathematical verification, frame-perfect render and owner approval. Stop and request review.*

| Task ID | Title | Owner | Prerequisites | Status | Acceptance Criteria | Evidence | Next Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T3.1** | Symbolic & Numerical Mathematical Verifier (`app/math_verifier.py`) | Agent (Engineer / Math Lead) | T2.5 | `completed` | Deterministically verifies arithmetic, algebra, trig/geometry identities, and division-by-zero rules via `SymPy`; classifies `10 ÷ 0` and `0 ÷ 0` strictly as `UNDEFINED` in ordinary arithmetic; rejects any false numerical answer or untagged fictional effect (`SafetyPolicyViolationError`). | `tests/test_math_animation.py` (passed) | Completed |
| **T3.2** | Mathematical Notation, Algebra, Graph, Geometry & Calculator Prop Renderer (`app/math_renderer.py`) | Agent (Animator / Engineer) | T3.1 | `completed` | Crisp high-contrast 2D rendering of exact notation (`÷`, `=`, superscripts, fractions), interactive calculator prop (full readable expression + result display + highlighted key presses + red `UNDEFINED` error state), Cartesian function graph plotter, and geometric figure renderer. | `tests/test_math_animation.py` (passed) | Completed |
| **T3.3** | Episode 001 ("Never Divide by Zero") 10-Second Pilot Audio & Scene Synchronizer (`app/episode001_pilot.py`) | Agent (Animator / Audio Lead) | T3.1, T3.2 | `completed` | Builds exact 5-scene storyboard (`0–2s`, `2–4s`, `4–6s`, `6–8s`, `8–10s`, 300 frames @ 30fps), verifies all math via `MathVerifier`, synthesizes 10s original audio track (curious motif `0–8s`, pleasant beep at `10 ÷ 2 = 5`, slightly faster beep at `10 ÷ 1 = 10`, music cut + error tone at `10 ÷ 0 = UNDEFINED`), renders low-res preview (`540x960`) and `1080x1920` pilot (`300 frames`), registers DB records & assets. | `renders/previews/ep001_pilot_10s_540x960.mp4` & `renders/previews/ep001_pilot_10s_1080x1920.mp4` | Completed |
| **T3.4** | Dashboard Integration for Math Verifier & Episode 001 Pilot Preview/Approval | Agent (Engineer) | T3.3 | `completed` | Adds `/api/math/verify`, `/api/episodes/ep001/render-pilot`, and `/api/episodes/ep001/approve-pilot` endpoints and dashboard UI controls. | `tests/test_math_animation.py::test_dashboard_math_and_ep001_approval_endpoints` (passed) | Completed |
| **T3.5** | Phase 3 Full Acceptance Suite, Git Commit & Gate Review | Agent (QA Lead) | T3.1–T3.4 | `completed` | All 24 Phase 1 + Phase 2 + Phase 3 automated tests pass (`25.79s`); exact `300` frame count, notation, character consistency, audio sync verified; committed and pushed to `origin/main`; stop and request owner review. | `TEST_RESULTS.md` (24 passed) | **STOP & Request Owner Review for Phase 3 Gate** |

---

## Subsequent Phases (Locked Until Owner Approves Phase 3 Gate)
- **Phase 4 (`T4.x`):** AI Production Agents (Idea/Script/Storyboard/MathVerifier/ScenePlanner/Animator/ProceduralMusic+SFX/Mixer/QC/Packager; full Episode 001 continuation).
- **Phase 5 (`T5.x`):** Remote Phone Control (Mobile PWA/responsive controls, voice/text idea submission, preview player, approval & batch approval gates, Tailscale/tunnel auth).
- **Phase 6 (`T6.x`):** Account Onboarding, Distribution, Monetization & Sponsors (Field-by-field setup wizard, YouTube/Instagram/TikTok adapters & compliant scheduler fallback, Maximum Publishing Mode for approved inventory, Sponsor CRM with mandatory exact-message approval gate).
- **Phase 7 (`T7.x`):** Analytics & Optimization (Inventory/revenue/cost/profit tracking, monetization eligibility tracker, recommendation engine, comment moderation queue, weekly report).
