# Math Mayhem — Operations Runbook

## 1. Overview
This runbook documents how to set up, run, test, back up, and recover the **Math Mayhem** platform on the owner's CLX desktop (Windows 11 + NVIDIA GeForce RTX 5080).

*(Note: Commands in §2–§5 will be finalized and verified during Phase 1 implementation `T1.1`–`T1.9` once the owner approves the stack.)*

---

## 2. Environment Prerequisites
- **OS:** Windows 11 (`10.0.26200`)
- **GPU:** NVIDIA GeForce RTX 5080 (Driver `610.88+`, CUDA `13.3+`)
- **Python:** Python `3.13.9`
- **FFmpeg:** FFmpeg with NVIDIA NVENC (`h264_nvenc`, `hevc_nvenc`) and `ffprobe` on `PATH` or configured via `MM_FFMPEG_PATH` in `.env`
- **Git:** Git `2.51+`

---

## 3. Reproducible Setup (Phase 1 Target)
```powershell
# 1. Clone / navigate to workspace
cd "C:\Users\Kagan Love\Documents\Projects\MathMayhem"

# 2. Create or activate virtual environment & install dependencies
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# 3. Initialize configuration and encrypted vault key
python -m app.cli init-env

# 4. Initialize SQLite WAL database
python -m app.cli init-db
```

---

## 4. Running the Local Dashboard & Worker
```powershell
# Start the local FastAPI dashboard and persistent background job worker (bound to 127.0.0.1:8000)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- **Dashboard URL:** `http://127.0.0.1:8000`
- **Authentication:** Use the owner admin token generated in `.env` (`MM_ADMIN_TOKEN`) to log in.

---

## 5. Running Acceptance Tests & GPU Smoke Test
```powershell
# Run the full automated acceptance test suite
python -m pytest -v

# Run only the RTX 5080 NVENC + FFmpeg render smoke test
python -m pytest tests/test_render_smoke.py -v
```

---

## 6. Backup & Disaster Recovery
```powershell
# Create an atomic online backup of the SQLite database and configuration manifests
python scripts/backup.py create

# Verify the latest backup archive
python scripts/backup.py verify --latest

# Restore from a specific backup archive
python scripts/backup.py restore --archive backups/backup_YYYYMMDD_HHMMSS.zip
```

---

## 7. Resuming From Last Checkpoint
If a session is interrupted or the desktop restarts:
1. Check [PROJECT_STATUS.md](file:///c:/Users/Kagan%20Love/Documents/Projects/MathMayhem/PROJECT_STATUS.md) and [TASKS.md](file:///c:/Users/Kagan%20Love/Documents/Projects/MathMayhem/TASKS.md) for the last verified checkpoint.
2. On startup, the persistent job queue (`app/queue.py`) automatically detects any jobs left in `RUNNING` state from an interrupted process, logs a recovery audit event, and safely re-queues them according to their idempotency key.
