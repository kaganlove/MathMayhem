# Math Mayhem — Acceptance Test Results

**Policy:** Never claim completion of any task or phase without passing automated acceptance tests and recording verifiable evidence here.

---

## Pre-Phase 1 — Environment Inspection Verification
- **Date:** 2026-11-11
- **Status:** ✅ PASSED

| Check ID | Verification Check | Method | Result | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| `ENV-01` | NVIDIA RTX 5080 & Driver Detection | `nvidia-smi` | **PASS** | `NVIDIA GeForce RTX 5080`, Driver `610.88`, CUDA `13.3`, `16303MiB` VRAM |
| `ENV-02` | OS, CPU & Storage Inspection | Python `platform` / `shutil.disk_usage` | **PASS** | `Windows-11-10.0.26200-SP0`, 16 CPU cores, `1,696.79 GB` free on `C:\` |
| `ENV-03` | Core Runtimes Installed | `python --version`, `node --version`, `git --version` | **PASS** | Python `3.13.9`, Node `v24.11.0`, Git `2.51.1.windows.1` |

---

## Phase 1 — Foundation Acceptance Test Suite (`T1.1` – `T1.9`)
- **Date:** 2026-11-11
- **Command:** `.\.venv\Scripts\python.exe -m pytest -v` (with 30s per-test `faulthandler` watchdog fixture in `tests/conftest.py`)
- **Execution Time:** `3.19s`
- **Summary:** ✅ **14 PASSED, 0 FAILED**

### Root-Cause Investigation & Fix Log for `test_dashboard_api.py` Hang
1. **Symptom:** `tests/test_dashboard_api.py::test_dashboard_auth_and_endpoints` hung when running under Windows sandboxed `pytest`.
2. **Diagnostic Evidence (`faulthandler.dump_traceback_later`):**
   - **Blocking Operation #1:** `asyncio.ProactorEventLoop._make_self_pipe` called `socket._fallback_socketpair()` (`Lib\socket.py:295 in accept`), which attempts a TCP loopback connection (`127.0.0.1`). Inside the Windows process sandbox, non-whitelisted socket connects fail silently on the non-blocking client socket (`WinError 10013`), leaving `lsock.accept()` waiting indefinitely.
   - **Blocking Operation #2:** Once the event loop initialized with a loopback-free self-pipe, FastAPI `def` (synchronous) route handlers and dependencies were dispatched by `anyio.to_thread.run_sync` (`anyio\_backends\_asyncio.py:975`), which signals completion back to the event loop thread via `loop.call_soon_threadsafe` -> `_write_to_self()` over the self-pipe.
3. **Permanent Fix Applied:**
   - Added a sandbox-aware `_LoopbackFreeProactorEventLoop` policy and an automatic 30-second per-test `faulthandler` watchdog timeout in [conftest.py](file:///c:/Users/Kagan%20Love/Documents/Projects/MathMayhem/tests/conftest.py).
   - Converted the FastAPI route handlers in [main.py](file:///c:/Users/Kagan%20Love/Documents/Projects/MathMayhem/app/main.py) and `require_owner_auth` in [security.py](file:///c:/Users/Kagan%20Love/Documents/Projects/MathMayhem/app/security.py) to `async def` so ASGI requests execute directly on the event loop without requiring cross-thread self-pipe wakeups.
   - Also fixed `event.inspect(target)` -> `sqlalchemy.inspect(target)` in [models.py](file:///c:/Users/Kagan%20Love/Documents/Projects/MathMayhem/app/models.py) uncovered once `test_database.py` ran after `test_dashboard_api.py`.

| Test Case | Target Task | Acceptance Criteria Verified | Result |
| :--- | :--- | :--- | :--- |
| `tests/test_env.py::test_git_repository_initialized` | `T1.1` | `.git` directory exists and active branch is `main`. | ✅ **PASSED** |
| `tests/test_env.py::test_required_project_directories_and_tracking_docs_exist` | `T1.1` | All required runtime directories (`app/`, `assets/`, `renders/`, `data/`, `backups/`, `logs/`, `scripts/`, `tests/`) and all 8 tracking/changelog markdown files exist and are non-empty. | ✅ **PASSED** |
| `tests/test_env.py::test_ffmpeg_and_nvenc_available` | `T1.2` | FFmpeg v9.0.2 binary resolved and `h264_nvenc` / `hevc_nvenc` hardware encoders verified. | ✅ **PASSED** |
| `tests/test_env.py::test_gpu_rtx_5080_detected` | `T1.2` | `nvidia-smi` telemetry confirms `NVIDIA GeForce RTX 5080` with `16,303 MiB` VRAM. | ✅ **PASSED** |
| `tests/test_env.py::test_math_and_scientific_dependencies_importable` | `T1.2` | `sympy`, `numpy`, `scipy`, and `PIL` import cleanly; `SymPy` evaluates `10 / 0` as `zoo` (ComplexInfinity / undefined), never a finite number. | ✅ **PASSED** |
| `tests/test_config_security.py::test_settings_bootstrap_and_safe_defaults` | `T1.3` | `.env` auto-bootstraps secure random `MM_ADMIN_TOKEN`, `MM_VAULT_KEY`, and `MM_SESSION_SECRET`; paid LLM calls default to `False` (`$0.00` budget). | ✅ **PASSED** |
| `tests/test_config_security.py::test_credential_vault_encryption_and_tamper_detection` | `T1.3` | `CredentialVault` encrypts secrets on disk (no plaintext on disk) and raises `InvalidToken` if ciphertext is tampered with. | ✅ **PASSED** |
| `tests/test_config_security.py::test_structured_json_logging` | `T1.3` | Rotating JSON logger writes structured JSON log lines with UTC timestamps and levels. | ✅ **PASSED** |
| `tests/test_database.py::test_sqlite_wal_mode_and_episode_version_immutability` | `T1.4` | SQLite runs in `WAL` mode; unverified math blocks approval; unapproved version blocks publishing; `APPROVED` `EpisodeVersion` raises `ImmutableRecordError` on any update or delete attempt. | ✅ **PASSED** |
| `tests/test_database.py::test_asset_provenance_and_sponsor_approval_guards` | `T1.4` | Assets without source/license/provenance or commercial/sponsored clearance raise `SafetyPolicyViolationError`; substantive `SponsorLead` cannot be marked `SENT` without owner approval. | ✅ **PASSED** |
| `tests/test_job_queue.py::test_persistent_job_queue_idempotency_retry_and_recovery` | `T1.5` | Duplicate `idempotency_key` deduplicates; transient failures retry with backoff and succeed; stranded `RUNNING` jobs recover to `QUEUED` on restart. | ✅ **PASSED** |
| `tests/test_render_smoke.py::test_gpu_nvenc_render_smoke_test_produces_valid_1080x1920_mp4` | `T1.6` | Renders 60-frame (`2.0s @ 30fps`, `1080x1920`) vertical MP4 via RTX 5080 `h264_nvenc` + procedural WAV motif (`aac` audio); verified via FFmpeg stream/frame inspection. | ✅ **PASSED** |
| `tests/test_dashboard_api.py::test_dashboard_auth_and_endpoints` | `T1.7` | Unauthenticated requests return `401`; valid token login sets session cookie; mobile-responsive dashboard renders GPU/storage/queue telemetry; episode creation API logs audit events. | ✅ **PASSED** |
| `tests/test_backup.py::test_atomic_backup_verify_and_restore_parity` | `T1.8` | Online `sqlite3.backup` creates timestamped zip with SHA-256 manifest, passes `PRAGMA integrity_check`, and restores with 100% row parity. | ✅ **PASSED** |

---

## Phase 2 — Character Animation Acceptance Test Suite (`T2.1` – `T2.5`)
- **Date:** 2026-11-11
- **Command:** `.\.venv\Scripts\python.exe -m pytest -v`
- **Execution Time:** `4.97s` (All 19 Phase 1 + Phase 2 tests)
- **Summary:** ✅ **19 PASSED, 0 FAILED**

| Test Case | Target Task | Acceptance Criteria Verified | Result |
| :--- | :--- | :--- | :--- |
| `tests/test_character_animation.py::test_canonical_character_invariants_and_violation_guards` | `T2.1` | Verifies messy short hair (`6` spikes), short beard, blank-lens glasses (`has_pupils=False`), `has_backpack=False`, and silent rules (`speaks=False`, `vocalizes=False`, `has_narrator=False`); raises `SafetyPolicyViolationError` if any invariant is violated. | ✅ **PASSED** |
| `tests/test_character_animation.py::test_canonical_model_sheet_generation_and_db_registration` | `T2.1` | Generates `assets/character/canonical_model_sheet.png` + `.json` across 5 canonical poses and registers the asset in the SQLite `Asset` table with commercial & sponsored clearance. | ✅ **PASSED** |
| `tests/test_character_animation.py::test_character_consistency_across_movements_and_poses` | `T2.2`, `T2.3` | Evaluates 5 continuous movements (`walk`, `run`, `head_tilt_gesture`, `button_press_prop_interaction`, `freeze_reaction`) across multiple phases and verifies blank-lens white interior pixels (`(255, 255, 255)`), 6 hair spikes, no backpack, and invariant torso geometry (`165.0 px`). | ✅ **PASSED** |
| `tests/test_character_animation.py::test_phase2_multi_scene_multi_movement_showcase_render` | `T2.3` | Renders `1080x1920 @ 30fps` showcase MP4 via RTX 5080 `h264_nvenc` across **2 scenes** (`scene_white_calculator`, `scene_chalkboard_lab`) and **5 movements** (`walk`, `head_tilt_gesture`, `button_press_prop_interaction`, `freeze_reaction`, `run`) with verified frame/pixel consistency. | ✅ **PASSED** |
| `tests/test_character_animation.py::test_dashboard_character_endpoints` | `T2.4` | Verifies `/api/character/spec` and `/api/character/model-sheet` endpoints on the authenticated dashboard. | ✅ **PASSED** |
