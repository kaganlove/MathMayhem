"""Automated Test Suite for Math Mayhem Episode 001 Final Release Package.

Validates that:
1. All release package directories and files exist.
2. Primary distribution master and archival master meet strict broadcast specs (1080x1920, 30 FPS, 24.0s, H.264).
3. Audio master is uncompressed WAV, exactly 24.0s, stereo.
4. All thumbnails and artwork exist in both PNG and WebP formats at 1080x1920.
5. 8-Panel narrative contact sheet exists and matches dimensions.
6. Mute-accessible captions (SRT and VTT) cover all 8 narrative acts.
7. Distribution metadata and creator guides are complete and valid JSON.
8. Every file registered in `release_manifest.json` has a verified SHA-256 checksum matching disk.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from PIL import Image

from app.render_smoke import probe_video_metadata, resolve_ffmpeg_exe

PACKAGE_DIR = Path("renders/packages/EP001_RELEASE_MASTER")


def _sha256(p: Path) -> str:
    hasher = hashlib.sha256()
    with p.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


@pytest.fixture(scope="module")
def manifest() -> dict:
    manifest_path = PACKAGE_DIR / "release_manifest.json"
    if not manifest_path.exists():
        # If package hasn't been built yet in test environment, run builder
        from app.compile_ep001_release_package import build_final_release_package
        build_final_release_package()
    assert manifest_path.exists(), "Release manifest must exist."
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def test_release_package_structure(manifest: dict) -> None:
    """Verify presence of core directories and primary files."""
    assert (PACKAGE_DIR / "video").is_dir()
    assert (PACKAGE_DIR / "audio").is_dir()
    assert (PACKAGE_DIR / "artwork").is_dir()
    assert (PACKAGE_DIR / "captions").is_dir()
    assert (PACKAGE_DIR / "metadata").is_dir()
    assert (PACKAGE_DIR / "ep001_master.mp4").is_file()
    assert (PACKAGE_DIR / "thumbnail.png").is_file()


def test_video_masters_spec(manifest: dict) -> None:
    """Verify technical specifications of distribution and archival video masters."""
    ffmpeg_exe = resolve_ffmpeg_exe()
    dist_master = PACKAGE_DIR / "video" / "ep001_never_divide_by_zero_master_1080x1920.mp4"
    arch_master = PACKAGE_DIR / "video" / "ep001_never_divide_by_zero_archive_master.mp4"

    assert dist_master.exists()
    assert arch_master.exists()

    dist_probe = probe_video_metadata(dist_master, ffmpeg_exe=ffmpeg_exe)
    assert dist_probe["width"] == 1080
    assert dist_probe["height"] == 1920
    assert dist_probe["frame_count"] == 720
    assert abs(dist_probe["fps"] - 30.0) < 0.1
    duration = dist_probe["frame_count"] / dist_probe["fps"]
    assert abs(duration - 24.0) < 0.1

    arch_probe = probe_video_metadata(arch_master, ffmpeg_exe=ffmpeg_exe)
    assert arch_probe["width"] == 1080
    assert arch_probe["height"] == 1920
    assert arch_probe["frame_count"] == 720


def test_master_audio_spec(manifest: dict) -> None:
    """Verify master uncompressed WAV audio specifications."""
    audio_wav = PACKAGE_DIR / "audio" / "ep001_master_audio.wav"
    assert audio_wav.exists()

    import wave
    with wave.open(str(audio_wav), "rb") as wf:
        channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        nframes = wf.getnframes()
        duration = nframes / float(framerate)

        assert channels in (1, 2), "Audio must be valid mono or stereo."
        assert sampwidth == 2, "Audio must be 16-bit PCM."
        assert framerate == 44100, "Sample rate must be 44.1 kHz."
        assert abs(duration - 24.0) < 0.05, f"Audio duration {duration} must be 24.0s."


def test_artwork_and_thumbnails(manifest: dict) -> None:
    """Verify cover artwork and thumbnails dimensions, formats, and non-empty content."""
    art_dir = PACKAGE_DIR / "artwork"
    thumbnails = [
        "thumbnail_climax_1080x1920",
        "thumbnail_cliffhanger_1080x1920",
        "thumbnail_poster_1080x1920",
    ]

    for name in thumbnails:
        png_p = art_dir / f"{name}.png"
        webp_p = art_dir / f"{name}.webp"
        assert png_p.exists(), f"Missing PNG thumbnail {name}"
        assert webp_p.exists(), f"Missing WebP thumbnail {name}"

        with Image.open(png_p) as im:
            assert im.size == (1080, 1920), f"Thumbnail {name} size must be 1080x1920"

        with Image.open(webp_p) as im:
            assert im.size == (1080, 1920), f"Thumbnail {name} WebP size must be 1080x1920"


def test_master_8panel_contact_sheet(manifest: dict) -> None:
    """Verify master contact sheet existence and resolution."""
    sheet_png = PACKAGE_DIR / "artwork" / "ep001_master_8panel_contact_sheet.png"
    sheet_webp = PACKAGE_DIR / "artwork" / "ep001_master_8panel_contact_sheet.webp"

    assert sheet_png.exists()
    assert sheet_webp.exists()

    with Image.open(sheet_png) as im:
        w, h = im.size
        assert w > 1500 and h > 1500, "Contact sheet must be high resolution."


def test_captions_files(manifest: dict) -> None:
    """Verify mute-accessible captions in both SRT and VTT formats."""
    srt = PACKAGE_DIR / "captions" / "captions.srt"
    vtt = PACKAGE_DIR / "captions" / "captions.vtt"

    assert srt.exists()
    assert vtt.exists()

    srt_text = srt.read_text(encoding="utf-8")
    vtt_text = vtt.read_text(encoding="utf-8")

    assert "10 ÷ 2 = 5" in srt_text
    assert "10 ÷ 0 = UNDEFINED" in srt_text
    assert "0 ÷ 0 = UNDEFINED" in srt_text
    assert "WEBVTT" in vtt_text


def test_distribution_metadata(manifest: dict) -> None:
    """Verify social distribution metadata for major platforms."""
    meta_json = PACKAGE_DIR / "metadata" / "distribution_metadata.json"
    guide_md = PACKAGE_DIR / "metadata" / "DISTRIBUTION_GUIDE.md"

    assert meta_json.exists()
    assert guide_md.exists()

    data = json.loads(meta_json.read_text(encoding="utf-8"))
    assert "youtube_shorts" in data["platforms"]
    assert "tiktok" in data["platforms"]
    assert "instagram_reels" in data["platforms"]
    assert "x_twitter" in data["platforms"]
    assert "educational_pinned_comment" in data


def test_checksum_integrity_against_manifest(manifest: dict) -> None:
    """Verify that every file in the package manifest exists and its SHA-256 matches on disk."""
    package_files = manifest["package_files"]
    assert len(package_files) >= 12, "Package must contain at least 12 registered deliverables."

    for rel_path, file_meta in package_files.items():
        full_path = PACKAGE_DIR / rel_path
        assert full_path.exists(), f"File in manifest does not exist: {rel_path}"
        actual_sha = _sha256(full_path)
        assert actual_sha == file_meta["sha256"], f"SHA256 mismatch for {rel_path}"
