"""Test suite for the Math Mayhem channel branding kit generator."""

from pathlib import Path
from PIL import Image
import pytest

from app.branding_generator import build_full_branding_kit


def test_branding_kit_generation(tmp_path):
    """Verify all 5 official channel branding assets generate with exact target dimensions."""
    assets = build_full_branding_kit(output_dir=tmp_path)

    # 1. Avatar (1024x1024)
    avatar_path = assets["avatar"]
    assert avatar_path.exists()
    with Image.open(avatar_path) as img:
        assert img.size == (1024, 1024)
        assert img.mode == "RGBA"

    # 2. YouTube Banner (2560x1440)
    yt_path = assets["youtube_banner"]
    assert yt_path.exists()
    with Image.open(yt_path) as img:
        assert img.size == (2560, 1440)

    # 3. Social Header (1200x630)
    social_path = assets["social_header"]
    assert social_path.exists()
    with Image.open(social_path) as img:
        assert img.size == (1200, 630)

    # 4. Mobile Banner (1080x1920)
    mob_path = assets["mobile_banner"]
    assert mob_path.exists()
    with Image.open(mob_path) as img:
        assert img.size == (1080, 1920)

    # 5. Watermark (512x512)
    wm_path = assets["watermark"]
    assert wm_path.exists()
    with Image.open(wm_path) as img:
        assert img.size == (512, 512)
        assert img.mode == "RGBA"
