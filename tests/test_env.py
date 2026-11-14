"""Phase 1 Acceptance Tests: Environment, Repository, FFmpeg/NVENC & Dependencies (T1.1, T1.2)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import scipy
import sympy as sp
from PIL import Image

from app.config import BASE_DIR
from app.render_smoke import detect_gpu_info, resolve_ffmpeg_exe


def test_git_repository_initialized() -> None:
    git_dir = BASE_DIR / ".git"
    assert git_dir.exists() and git_dir.is_dir()
    out = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(BASE_DIR), text=True).strip()
    assert len(out) > 0 and out != "HEAD"


def test_required_project_directories_and_tracking_docs_exist() -> None:
    required_dirs = [
        "app",
        "assets/character",
        "assets/audio",
        "assets/props",
        "renders/previews",
        "renders/masters",
        "data",
        "backups",
        "logs",
        "scripts",
        "tests",
    ]
    for rel in required_dirs:
        p = BASE_DIR / rel
        assert p.exists() and p.is_dir(), f"Missing directory: {rel}"

    required_docs = [
        "PROJECT_STATUS.md",
        "TASKS.md",
        "DECISIONS.md",
        "ARCHITECTURE.md",
        "TEST_RESULTS.md",
        "BLOCKERS.md",
        "RUNBOOK.md",
        "CHANGELOG.md",
    ]
    for doc in required_docs:
        p = BASE_DIR / doc
        assert p.exists() and p.stat().st_size > 0, f"Missing or empty tracking doc: {doc}"


def test_ffmpeg_and_nvenc_available() -> None:
    exe = resolve_ffmpeg_exe()
    assert Path(exe).exists()
    out = subprocess.check_output([exe, "-encoders"], text=True)
    assert "h264_nvenc" in out
    assert "hevc_nvenc" in out


def test_gpu_rtx_5080_detected() -> None:
    info = detect_gpu_info()
    assert info["available"] is True
    assert "5080" in info["name"]
    assert info["vram_total_mib"] >= 15000


def test_math_and_scientific_dependencies_importable() -> None:
    x = sp.Symbol("x")
    assert sp.simplify((x**2 - 1) / (x - 1)) == x + 1
    # Verify division by zero yields ComplexInfinity (zoo) in SymPy, never a finite number
    div_zero = sp.sympify("10 / 0", evaluate=True)
    assert div_zero == sp.zoo
    arr = np.array([1.0, 2.0, 3.0])
    assert float(arr.mean()) == 2.0
    assert scipy.__version__ is not None
    img = Image.new("RGB", (16, 16), color=(255, 255, 255))
    assert img.size == (16, 16)
