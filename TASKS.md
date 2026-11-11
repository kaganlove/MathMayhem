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
| **T1.9** | Phase 1 Full Acceptance Suite & Gate Review | Agent (QA Lead) | T1.1–T1.8 | `completed` | 100% of Phase 1 automated tests pass (14/14); `TEST_RESULTS.md`, `RUNBOOK.md`, `PROJECT_STATUS.md` updated; clean git checkpoint committed; owner presented with Phase 1 completion report. | `TEST_RESULTS.md` (14 passed) | **STOP & Request Owner Review for Phase 1 Gate** |

---

## Subsequent Phases (Locked Until Owner Approves Phase 1 Gate)
- **Phase 2 (`T2.x`):** Character Animation (Canonical stick-figure rig, messy short hair, short beard, blank-lens glasses, no backpack, silent expressive poses, ≥3 movements, ≥2 scenes).
- **Phase 3 (`T3.x`):** Mathematical Animation (Exact notation renderer, SymPy verification gate, Episode 001 10-second pilot: `10 ÷ 2 = 5`, `10 ÷ 1 = 10`, `10 ÷ 0 = UNDEFINED`).
- **Phase 4 (`T4.x`):** AI Production Agents (Idea/Script/Storyboard/MathVerifier/ScenePlanner/Animator/ProceduralMusic+SFX/Mixer/QC/Packager; full Episode 001 continuation).
- **Phase 5 (`T5.x`):** Remote Phone Control (Mobile PWA/responsive controls, voice/text idea submission, preview player, approval & batch approval gates, Tailscale/tunnel auth).
- **Phase 6 (`T6.x`):** Account Onboarding, Distribution, Monetization & Sponsors (Field-by-field setup wizard, YouTube/Instagram/TikTok adapters & compliant scheduler fallback, Maximum Publishing Mode for approved inventory, Sponsor CRM with mandatory exact-message approval gate).
- **Phase 7 (`T7.x`):** Analytics & Optimization (Inventory/revenue/cost/profit tracking, monetization eligibility tracker, recommendation engine, comment moderation queue, weekly report).
