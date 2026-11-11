# Math Mayhem — Changelog

All notable changes to the **Math Mayhem** project are documented in this file.

## [0.1.0-phase1] — 2026-11-11
### Added
- Initialized persistent tracking suite (`PROJECT_STATUS.md`, `TASKS.md`, `DECISIONS.md`, `ARCHITECTURE.md`, `TEST_RESULTS.md`, `BLOCKERS.md`, `RUNBOOK.md`).
- Inspected CLX host environment (Windows 11, 16-core CPU, NVIDIA GeForce RTX 5080 16GB, Python 3.13.9).
- Owner approved Phase 1 architecture decisions (`DEC-001` through `DEC-006`).
- Initialized Git repository (`main` branch) and Phase 1 directory structure (`T1.1`).
- Configured `.venv` with pinned `requirements.txt` and FFmpeg v9.0.2 with verified `h264_nvenc` / `hevc_nvenc` / `av1_nvenc` hardware encoders (`T1.2`).
- Implemented `app/config.py`, `app/security.py` (Fernet-encrypted credential vault + token/session auth), and `app/logging_config.py` (rotating JSON logger) (`T1.3`).
- Implemented SQLite WAL database and ORM models (`app/database.py`, `app/models.py`) with strict immutability triggers for approved `EpisodeVersion` records, asset provenance validation, and sponsor email approval guards (`T1.4`).
- Implemented `PersistentJobQueue` (`app/queue.py`) with idempotency, retry backoff, and crash recovery (`T1.5`).
- Implemented RTX 5080 NVENC + FFmpeg + procedural DSP audio smoke test renderer (`app/render_smoke.py`) producing verified 60-frame `1080x1920 @ 30fps` vertical MP4 output (`T1.6`).
- Implemented mobile-responsive FastAPI control dashboard (`app/main.py`, `app/templates/dashboard.html`) (`T1.7`).
- Implemented atomic online SQLite backup, checksum verification, and restore CLI (`scripts/backup.py`) (`T1.8`).
- Completed 14-test Phase 1 automated acceptance suite (`tests/test_*.py`) with 100% pass rate (`T1.9`).
