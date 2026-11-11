# Math Mayhem — Task Tracker

**Status Legend:** `not started` | `in progress` | `blocked` | `testing` | `completed`

---

## Pre-Phase 1 — Discovery & Planning

| Task ID | Title | Owner | Prerequisites | Status | Acceptance Criteria | Evidence | Next Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T0.1** | Environment & Hardware Inspection | Agent (Architect) | None | `completed` | OS, CPU, GPU, CUDA, RAM/Disk, Python, Node, Git, FFmpeg, Blender inspected and recorded. | `ARCHITECTURE.md` §1 (Environment Inventory) | None |
| **T0.2** | Initialize Persistent Tracking Docs | Agent (PM) | T0.1 | `completed` | `PROJECT_STATUS.md`, `TASKS.md`, `DECISIONS.md`, `ARCHITECTURE.md`, `TEST_RESULTS.md`, `BLOCKERS.md`, `RUNBOOK.md` created on disk. | All 7 files present in workspace root. | None |
| **T0.3** | Propose Stack & Request Owner Approval | Agent (Architect) | T0.1, T0.2 | `in progress` | Stack options, trade-offs, cost/permission implications documented in `DECISIONS.md` and presented to owner. | `DECISIONS.md` (`DEC-001` to `DEC-006`) | Owner approves stack to unlock `T1.1`. |

---

## Phase 1 — Foundation
*Goal: Inspect environment; choose stack; create repository, configuration, project files, database, asset directories, test harness, local dashboard shell, GPU render smoke test, logs, backup and runbook.*

| Task ID | Title | Owner | Prerequisites | Status | Acceptance Criteria | Evidence | Next Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **T1.1** | Repository & Directory Scaffolding | Agent (Engineer) | T0.3 (Owner Approval) | `not started` | Git repo initialized (`main` branch), `.gitignore` configured, standard directories (`app/`, `assets/`, `renders/`, `data/`, `backups/`, `logs/`, `tests/`, `scripts/`), `CHANGELOG.md` created, initial commit recorded. | `git log -n 1` & directory check test | Run after owner approves Phase 1 start. |
| **T1.2** | Python Environment & FFmpeg/NVENC Provisioning | Agent (Engineer) | T1.1 | `not started` | Reproducible `.venv` with pinned dependencies (`pyproject.toml` / `requirements.txt`); FFmpeg binary with `h264_nvenc` / `hevc_nvenc` verified against RTX 5080; `sympy`, `pytest`, `numpy`, `scipy`, `pycairo`/`pillow` installed. | `pytest tests/test_env.py` passes | Install/verify FFmpeg and Python packages. |
| **T1.3** | Configuration, Secrets Encryption & Structured Logging | Agent (Engineer) | T1.2 | `not started` | Pydantic `Settings` (`app/config.py`) loads `.env`; Fernet/AES-GCM credential vault (`app/security.py`) encrypts/decrypts secrets at rest; rotating JSON/text logger (`app/logging_config.py`) writes to `logs/math_mayhem.log`. | `pytest tests/test_config_security.py` passes | Implement config, vault, and logger. |
| **T1.4** | Database Schema, Immutable Versioning & Audit Log | Agent (Engineer) | T1.3 | `not started` | SQLite WAL database (`data/math_mayhem.db`) via SQLAlchemy 2.0; tables for `Episode`, `EpisodeVersion` (with immutability trigger/guard once approved), `Scene`, `Asset` (with provenance/license fields), `Job`, `ApprovalLog`, `SponsorLead`, `AuditEvent`. | `pytest tests/test_database.py` passes | Implement models and repository layer. |
| **T1.5** | Persistent Job Queue Worker & Recovery | Agent (Engineer) | T1.4 | `not started` | SQLite-backed persistent job queue (`app/queue.py`) supporting idempotency keys, retries with backoff, crash recovery across restarts, and background task execution. | `pytest tests/test_job_queue.py` passes | Implement persistent queue and worker loop. |
| **T1.6** | GPU & FFmpeg Render Smoke Test Pipeline | Agent (Animator / Engineer) | T1.2, T1.5 | `not started` | Synthetic 2-second (60-frame, 1080x1920, 30fps) test animation rendered via Python frame generator + RTX 5080 `h264_nvenc` (with CPU `libx264` fallback) and procedural WAV audio muxed; `ffprobe` verifies exact resolution, frame count, FPS, and audio stream. | `pytest tests/test_render_smoke.py` & `renders/smoke_test.mp4` | Build frame pipeline + NVENC encoder wrapper + `ffprobe` validator. |
| **T1.7** | Local Mobile-Responsive Dashboard Shell & Auth | Agent (Engineer) | T1.4, T1.5, T1.6 | `not started` | FastAPI web app (`app/main.py`) with token/session authentication, health telemetry (GPU/Disk/Queue), episode/job status view, and one-click "Run GPU Smoke Test" button; responsive on mobile viewports (390x844). | `pytest tests/test_dashboard_api.py` passes | Build FastAPI routes & mobile-first UI shell. |
| **T1.8** | Automated Backup & Restore Utility | Agent (Engineer) | T1.4 | `not started` | `scripts/backup.py` performs online SQLite backup (`sqlite3.Connection.backup`), snapshots configuration/manifests into timestamped archives in `backups/`, and verifies restore integrity. | `pytest tests/test_backup.py` passes | Build backup/restore script and test. |
| **T1.9** | Phase 1 Full Acceptance Suite & Gate Review | Agent (QA Lead) | T1.1–T1.8 | `not started` | 100% of Phase 1 automated tests pass; `TEST_RESULTS.md`, `RUNBOOK.md`, `PROJECT_STATUS.md` updated; clean git checkpoint committed; owner presented with Phase 1 completion report. | Full `pytest` output in `TEST_RESULTS.md` | Present Phase 1 gate review to owner. |

---

## Subsequent Phases (High-Level Placeholders — Do Not Start Until Phase 1 Approved)
- **Phase 2 (`T2.x`):** Character Animation (Canonical stick-figure rig, messy short hair, short beard, blank-lens glasses, no backpack, silent expressive poses, ≥3 movements, ≥2 scenes).
- **Phase 3 (`T3.x`):** Mathematical Animation (Exact notation renderer, SymPy verification gate, Episode 001 10-second pilot: `10 ÷ 2 = 5`, `10 ÷ 1 = 10`, `10 ÷ 0 = UNDEFINED`).
- **Phase 4 (`T4.x`):** AI Production Agents (Idea/Script/Storyboard/MathVerifier/ScenePlanner/Animator/ProceduralMusic+SFX/Mixer/QC/Packager; full Episode 001 continuation).
- **Phase 5 (`T5.x`):** Remote Phone Control (Mobile PWA/responsive controls, voice/text idea submission, preview player, approval & batch approval gates, Tailscale/tunnel auth).
- **Phase 6 (`T6.x`):** Account Onboarding, Distribution, Monetization & Sponsors (Field-by-field setup wizard, YouTube/Instagram/TikTok adapters & compliant scheduler fallback, Maximum Publishing Mode for approved inventory, Sponsor CRM with mandatory exact-message approval gate).
- **Phase 7 (`T7.x`):** Analytics & Optimization (Inventory/revenue/cost/profit tracking, monetization eligibility tracker, recommendation engine, comment moderation queue, weekly report).
