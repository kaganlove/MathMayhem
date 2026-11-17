"""Test suite for Episode 001 Director's Cut (Enhanced Edition)."""

from pathlib import Path
import pytest

from app.render_smoke import probe_video_metadata


def test_ep001_directors_cut_spec_and_artifacts():
    """Verify Episode 001 Director's Cut meets all canonical production standards."""
    vid_path = Path("renders/episodes/ep001_directors_cut_master_1080x1920.mp4")
    sheet_path = Path("renders/episodes/ep001_directors_cut_8panel_contact_sheet.png")

    assert vid_path.exists()
    assert sheet_path.exists()

    meta = probe_video_metadata(vid_path)
    assert meta["width"] == 1080
    assert meta["height"] == 1920
    assert meta["fps"] == 30.0
    assert meta["frame_count"] == 1200
    assert meta["has_audio"] is True
    assert meta["audio_codec"] == "aac"
