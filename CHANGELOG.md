# Math Mayhem — Changelog

All notable changes to the **Math Mayhem** project are documented in this file.

## [0.3.0-phase3] — 2026-11-11
### Added
- Implemented deterministic symbolic and numerical mathematical verifier (`app/math_verifier.py`) via `SymPy`, enforcing that `10 ÷ 0` and `0 ÷ 0` evaluate strictly to `UNDEFINED` in ordinary arithmetic and requiring explicit disclaimers for fictional visual metaphors (`T3.1`).
- Implemented high-contrast mathematical notation, interactive pedestal calculator prop, Cartesian function graph plotter (`f(x) = 10 / x`), and geometric right-triangle renderer (`app/math_renderer.py`) (`T3.2`).
- Implemented Episode 001 (*Never Divide by Zero*) 10-second pilot builder, procedural 10s audio synthesizer (curious motif, pleasant beep, faster double beep, abrupt music cut, error buzzer), and `300`-frame @ `30fps` renderer (`app/episode001_pilot.py`) producing both `540x960` low-res preview and `1080x1920` full-res renders via RTX 5080 `h264_nvenc` (`T3.3`).
- Added `/api/math/verify`, `/api/episodes/ep001/render-pilot`, and `/api/episodes/ep001/approve-pilot` endpoints and dashboard UI button (`T3.4`).
- Added 5-test Phase 3 acceptance suite (`tests/test_math_animation.py`); all 24/24 project tests pass (`T3.5`).

## [0.2.0-phase2] — 2026-11-11
### Added
- Implemented canonical stick-figure adventurer rig and pose/motion library (`app/character_rig.py`) enforcing messy short hair, short beard, blank-lens glasses (no pupils), no backpack, and silent rules (`T2.1`, `T2.2`).
- Generated canonical character model sheet (`assets/character/canonical_model_sheet.png` and `.json`) and registered it in the SQLite `Asset` registry (`T2.1`).
- Implemented multi-scene framing, prop interaction, and pixel/geometric consistency validator (`app/character_scenes.py`) across 2 scenes (`scene_white_calculator`, `scene_chalkboard_lab`) and 5 movements (`walk`, `head_tilt_gesture`, `button_press_prop_interaction`, `freeze_reaction`, `run`) (`T2.3`).
- Added character rig inspection and showcase rendering endpoints to the FastAPI dashboard (`app/main.py`, `app/templates/dashboard.html`) (`T2.4`).
- Added 5-test Phase 2 acceptance suite (`tests/test_character_animation.py`); all 19/19 project tests pass (`T2.5`).

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
