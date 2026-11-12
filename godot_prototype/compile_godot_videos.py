"""Compilation, QA Analysis, and Contact Sheet Generator for Godot 2D Prototype (v8.0).

Encodes:
1. `godot_character_clean.mp4`
2. `godot_character_debug.mp4`
3. `godot_clean_contact_sheet.png`
4. `godot_debug_contact_sheet.png`
5. `comparison_procedural_vs_godot.mp4` (Side-by-side)
6. `comparison_contact_sheet.png`
"""

import json
import math
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem")))

from app.config import get_settings
from app.render_smoke import resolve_ffmpeg_exe


def encode_mp4(frame_dir: Path, out_mp4: Path, fps: int = 30) -> None:
    ffmpeg_exe = resolve_ffmpeg_exe()
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    if out_mp4.exists():
        out_mp4.unlink()

    cmd = [
        str(ffmpeg_exe),
        "-y",
        "-framerate", str(fps),
        "-i", str(frame_dir / "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "18",
        str(out_mp4)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg encoding failed for {out_mp4}: {res.stderr}")
    print(f"Encoded MP4: {out_mp4} ({out_mp4.stat().st_size} bytes)")


def generate_6panel_contact_sheet(frame_dir: Path, out_png: Path, key_frame_indices: list, title: str) -> None:
    out_png.parent.mkdir(parents=True, exist_ok=True)
    
    # 3 cols x 2 rows
    cols = 3
    rows = 2
    thumb_w = 420
    thumb_h = 746
    pad = 24
    header_h = 100
    
    sheet_w = cols * thumb_w + (cols + 1) * pad
    sheet_h = rows * thumb_h + (rows + 1) * pad + header_h
    
    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 247, 250))
    draw = ImageDraw.Draw(sheet)
    
    # Header
    draw.rectangle([(0, 0), (sheet_w, header_h)], fill=(16, 20, 28))
    draw.text((pad, 20), title, fill=(255, 255, 255))
    draw.text((pad, 54), "Godot 2D Prototype — Authored Poses, Natural Body Mechanics, Invariant Anatomy", fill=(0, 215, 255))
    
    labels = [
        "Phase 1: Neutral Idle (0.5s)",
        "Phase 2: Curiosity Focus (1.5s)",
        "Phase 3: Believable Step (2.6s)",
        "Phase 4: Coordinated Reach (3.8s)",
        "Phase 5: Expressive Surprise (4.6s)",
        "Phase 6: Confident Smirk Settle (5.5s)"
    ]
    
    for idx, frame_idx in enumerate(key_frame_indices[:6]):
        fpath = frame_dir / f"frame_{frame_idx:04d}.png"
        if not fpath.exists():
            continue
        im = Image.open(fpath)
        im_resized = im.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        
        c = idx % cols
        r = idx // cols
        x = pad + c * (thumb_w + pad)
        y = header_h + pad + r * (thumb_h + pad)
        
        sheet.paste(im_resized, (x, y))
        draw.rectangle([(x, y), (x + thumb_w, y + thumb_h)], outline=(180, 190, 205), width=2)
        
        # Panel caption banner
        draw.rectangle([(x, y + thumb_h - 38), (x + thumb_w, y + thumb_h)], fill=(16, 20, 28))
        draw.text((x + 12, y + thumb_h - 28), labels[idx], fill=(255, 255, 255))
        
    sheet.save(out_png)
    print(f"Generated Contact Sheet: {out_png}")


def create_side_by_side_comparison(procedural_mp4: Path, godot_mp4: Path, out_mp4: Path) -> None:
    ffmpeg_exe = resolve_ffmpeg_exe()
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    if out_mp4.exists():
        out_mp4.unlink()

    # Create 1080x1920 side-by-side or dual-stack video
    # Input 0: Procedural (scaled to 540x960), Input 1: Godot (scaled to 540x960)
    # Stacked vertically or horizontally with clear labels
    filter_complex = (
        "[0:v]scale=540:960,drawtext=text='Version A: Procedural Interpolation':fontcolor=white:fontsize=28:box=1:boxcolor=black@0.6:boxborderw=8:x=(w-text_w)/2:y=20[v0];"
        "[1:v]scale=540:960,drawtext=text='Version B: Godot 2D Authored Poses':fontcolor=white:fontsize=28:box=1:boxcolor=black@0.6:boxborderw=8:x=(w-text_w)/2:y=20[v1];"
        "[v0][v1]vstack=inputs=2[outv]"
    )

    cmd = [
        str(ffmpeg_exe),
        "-y",
        "-i", str(procedural_mp4),
        "-i", str(godot_mp4),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "18",
        "-t", "5.2",
        str(out_mp4)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Note on side-by-side video:", res.stderr[:300])
    else:
        print(f"Generated Side-by-Side Comparison MP4: {out_mp4}")


def create_side_by_side_contact_sheet(procedural_dir: Path, godot_dir: Path, out_png: Path) -> None:
    # 4 comparison keyframe pairs: Neutral, Walk, Reach, Surprise
    pairs = [
        ("Neutral Idle", 15, 15),
        ("Walk / Step", 82, 78),
        ("Reach Apex", 112, 114),
        ("Surprise Gasp", 125, 138),
    ]
    
    thumb_w = 260
    thumb_h = 462
    pad = 16
    header_h = 90
    
    cols = 4
    rows = 2 # Row 0: Version A Procedural, Row 1: Version B Godot
    
    sheet_w = cols * thumb_w + (cols + 1) * pad
    sheet_h = rows * thumb_h + (rows + 1) * pad + header_h
    
    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 247, 250))
    draw = ImageDraw.Draw(sheet)
    
    draw.rectangle([(0, 0), (sheet_w, header_h)], fill=(16, 20, 28))
    draw.text((pad, 18), "MATH MAYHEM — DIRECT ANIMATION ARCHITECTURE COMPARISON", fill=(255, 255, 255))
    draw.text((pad, 50), "Version A (Existing Procedural) vs Version B (Godot 2D Authored Poses)", fill=(0, 215, 255))
    
    for c_idx, (label, proc_f, godot_f) in enumerate(pairs):
        # Top: Procedural
        p_path = procedural_dir / f"frame_{proc_f:04d}.png"
        g_path = godot_dir / f"frame_{godot_f:04d}.png"
        
        x = pad + c_idx * (thumb_w + pad)
        
        if p_path.exists():
            pim = Image.open(p_path).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            y0 = header_h + pad
            sheet.paste(pim, (x, y0))
            draw.rectangle([(x, y0), (x + thumb_w, y0 + thumb_h)], outline=(180, 190, 205), width=2)
            draw.rectangle([(x, y0 + thumb_h - 32), (x + thumb_w, y0 + thumb_h)], fill=(16, 20, 28))
            draw.text((x + 8, y0 + thumb_h - 24), f"Ver A: {label}", fill=(255, 200, 100))
            
        if g_path.exists():
            gim = Image.open(g_path).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            y1 = header_h + pad + thumb_h + pad
            sheet.paste(gim, (x, y1))
            draw.rectangle([(x, y1), (x + thumb_w, y1 + thumb_h)], outline=(0, 200, 255), width=2)
            draw.rectangle([(x, y1 + thumb_h - 32), (x + thumb_w, y1 + thumb_h)], fill=(16, 20, 28))
            draw.text((x + 8, y1 + thumb_h - 24), f"Ver B (Godot): {label}", fill=(0, 230, 255))
            
    sheet.save(out_png)
    print(f"Generated Comparison Contact Sheet: {out_png}")


def main():
    pdir = Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem")
    clean_frames = pdir / "godot_prototype" / "temp_clean_frames"
    debug_frames = pdir / "godot_prototype" / "temp_debug_frames"
    out_dir = pdir / "renders" / "previews"
    
    clean_mp4 = out_dir / "godot_character_clean.mp4"
    debug_mp4 = out_dir / "godot_character_debug.mp4"
    clean_sheet = out_dir / "godot_clean_contact_sheet.png"
    debug_sheet = out_dir / "godot_debug_contact_sheet.png"
    comp_mp4 = out_dir / "comparison_procedural_vs_godot.mp4"
    comp_sheet = out_dir / "comparison_contact_sheet.png"
    
    # 1. Encode Videos
    encode_mp4(clean_frames, clean_mp4, fps=30)
    encode_mp4(debug_frames, debug_mp4, fps=30)
    
    # 2. Keyframes at t=0.5s, 1.5s, 2.6s, 3.8s, 4.6s, 5.5s (indices 15, 45, 78, 114, 138, 165)
    key_indices = [15, 45, 78, 114, 138, 165]
    generate_6panel_contact_sheet(clean_frames, clean_sheet, key_indices, "Math Mayhem v8.0 — Godot 2D Character Prototype (Clean)")
    generate_6panel_contact_sheet(debug_frames, debug_sheet, key_indices, "Math Mayhem v8.0 — Godot 2D Prototype Technical QA (Debug)")
    
    # 3. Side-by-Side Comparison with Existing Procedural System
    proc_mp4 = out_dir / "poc_character_clean.mp4"
    if proc_mp4.exists():
        create_side_by_side_comparison(proc_mp4, clean_mp4, comp_mp4)
        
    # Extract temporary procedural frames for comparison sheet if needed
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_proc_dir:
        tmp_proc = Path(tmp_proc_dir)
        ffmpeg_exe = resolve_ffmpeg_exe()
        subprocess.run([
            str(ffmpeg_exe), "-y", "-i", str(proc_mp4),
            "-vf", "fps=30", str(tmp_proc / "frame_%04d.png")
        ], capture_output=True)
        create_side_by_side_contact_sheet(tmp_proc, clean_frames, comp_sheet)


if __name__ == "__main__":
    main()
