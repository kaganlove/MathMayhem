"""Phase 1 Acceptance Tests: GPU (RTX 5080 NVENC) + FFmpeg + Procedural Audio Render Smoke Test (T1.6)."""

from __future__ import annotations

from pathlib import Path

from app.render_smoke import run_gpu_render_smoke_test


def test_gpu_nvenc_render_smoke_test_produces_valid_1080x1920_mp4(tmp_path: Path) -> None:
    output_mp4 = tmp_path / "smoke_test_1080x1920.mp4"
    result = run_gpu_render_smoke_test(
        output_path=output_mp4,
        frame_count=60,
        fps=30,
        width=1080,
        height=1920,
    )

    assert output_mp4.exists()
    assert result["size_bytes"] > 10_000
    assert result["width"] == 1080
    assert result["height"] == 1920
    assert result["fps"] == 30.0
    assert result["frame_count"] == 60
    assert result["has_audio"] is True
    assert result["audio_codec"] == "aac"
    assert result["encoder"] == "h264_nvenc"
    assert len(result["sha256"]) == 64
