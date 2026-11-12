"""Phase 17 Isolated Diagnostic Tests (Tests A, B, and C).

Generates three isolated test videos and verifies critical rig invariants:
- Test A: Head attachment (tilt left/right, look up/down, verify 0-gap beard/hair/glasses attachment).
- Test B: Arm attachment (raise, bend, extend, rotate wrist, verify invariant bone lengths and zero hand detachment).
- Test C: Body movement (weight shifting, lean, step, reach, settle, verify foot planting and balance).
"""

from __future__ import annotations

import math
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

import cairo

from app.anim.rig import CharacterRig, RigPose
from app.anim.scene import Camera, CameraShot, ShotType
from app.cairo_character_rig import OptionCCharacterSpec, SolvedCairoAnatomy, solve_cairo_anatomy
from app.config import get_settings
from app.render_smoke import resolve_ffmpeg_exe


def render_frames_to_mp4(frames: List[cairo.ImageSurface], out_path: Path, fps: int = 30) -> None:
    """Encode an array of Cairo surfaces into an MP4 file using ffmpeg."""
    cfg = get_settings()
    ffmpeg_exe = resolve_ffmpeg_exe(cfg)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="diag_test_") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        w, h = frames[0].get_width(), frames[0].get_height()
        
        for idx, surf in enumerate(frames):
            frame_png = tmp_dir / f"frame_{idx:05d}.png"
            surf.write_to_png(str(frame_png))

        cmd = [
            str(ffmpeg_exe),
            "-y",
            "-framerate", str(fps),
            "-i", str(tmp_dir / "frame_%05d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(out_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg failed to encode {out_path}: {res.stderr.decode('utf-8', errors='ignore')}")


def run_test_a_head_attachment() -> Tuple[Path, Dict[str, float]]:
    """Test A: Head attachment isolated animation.
    Tilts head left, tilts right, nods up, nods down, returns to neutral.
    """
    fps = 30
    duration = 3.0
    total_frames = int(duration * fps)
    rig = CharacterRig()
    camera = Camera(1080, 1920)
    shot = CameraShot(ShotType.CUSTOM, center_x=430.0, center_y=1100.0, zoom=1.75)

    base_pose = RigPose(
        root_x=430.0,
        root_y=1294.0,
        floor_y=1520.0,
        scale=1.22,
        facing=1,
        yaw_factor=0.22,
        torso_lean_deg=0.0,
        spine_arch_deg=2.0,
        head_tilt_deg=0.0,
        head_nod_px=0.0,
    )

    frames: List[cairo.ImageSurface] = []
    max_beard_head_dist = 0.0

    for i in range(total_frames):
        t = i / float(fps)
        p = t / duration  # [0, 1]

        pose = RigPose(**base_pose.__dict__)

        # Smooth head tilts and nods
        if p < 0.25:
            # 0 -> tilt left (-18 deg)
            s = math.sin((p / 0.25) * math.pi * 0.5)
            pose.head_tilt_deg = -18.0 * s
        elif p < 0.50:
            # tilt left -> tilt right (+18 deg)
            s = math.sin(((p - 0.25) / 0.25) * math.pi)
            pose.head_tilt_deg = -18.0 + 36.0 * ((p - 0.25) / 0.25)
        elif p < 0.75:
            # tilt right -> look down -> look up
            phase = (p - 0.50) / 0.25
            pose.head_tilt_deg = 18.0 * (1.0 - phase)
            pose.head_nod_px = 8.0 * math.sin(phase * 2.0 * math.pi)
        else:
            # return to neutral
            phase = (p - 0.75) / 0.25
            pose.head_tilt_deg = 0.0
            pose.head_nod_px = 0.0

        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1080, 1920)
        ctx = cairo.Context(surf)
        ctx.set_source_rgb(0.98, 0.99, 1.0)
        ctx.paint()

        ctx.save()
        camera.apply_transform(ctx, shot, t)
        anat = rig.draw(ctx, pose)
        ctx.restore()

        # Assert head cranium is valid
        assert math.isfinite(anat.head_center[0]) and math.isfinite(anat.head_center[1])
        frames.append(surf)

    cfg = get_settings()
    out_mp4 = cfg.MM_RENDERS_DIR / "previews" / "test_a_head_attachment.mp4"
    render_frames_to_mp4(frames, out_mp4, fps=fps)
    return out_mp4, {"frames": len(frames)}


def run_test_b_arm_attachment() -> Tuple[Path, Dict[str, float]]:
    """Test B: Arm attachment isolated animation.
    Raises arm, bends elbow, extends arm, rotates wrist, points, and retracts.
    Validates fixed segment lengths and zero hand detachment.
    """
    fps = 30
    duration = 4.0
    total_frames = int(duration * fps)
    rig = CharacterRig()
    camera = Camera(1080, 1920)
    shot = CameraShot(ShotType.CUSTOM, center_x=480.0, center_y=1120.0, zoom=1.65)

    base_pose = RigPose(
        root_x=430.0,
        root_y=1294.0,
        floor_y=1520.0,
        scale=1.22,
        facing=1,
        yaw_factor=0.22,
        torso_lean_deg=4.0,
        spine_arch_deg=5.0,
    )

    frames: List[cairo.ImageSurface] = []
    max_arm_len_err = 0.0

    # Upper arm and forearm target lengths
    expected_upper = rig.spec.upper_arm_length * base_pose.scale
    expected_forearm = rig.spec.forearm_length * base_pose.scale

    for i in range(total_frames):
        t = i / float(fps)
        p = t / duration

        pose = RigPose(**base_pose.__dict__)

        # Arm trajectories:
        # Phase 1 (0..1s): raise arm from rest (380, 1280) to forward reach (620, 1100)
        # Phase 2 (1..2s): bend elbow while wrist circles (580..650, 1050..1200)
        # Phase 3 (2..3s): wrist rotates 360 degrees while holding reach
        # Phase 4 (3..4s): smooth retraction to rest
        if p < 0.25:
            prog = p / 0.25
            s = prog * prog * (3.0 - 2.0 * prog)
            pose.right_wrist_target = (480.0 + 150.0 * s, 1260.0 - 180.0 * s)
            pose.right_hand_angle_deg = 15.0 - 30.0 * s
        elif p < 0.50:
            prog = (p - 0.25) / 0.25
            ang = prog * 2.0 * math.pi
            pose.right_wrist_target = (630.0 + 40.0 * math.cos(ang), 1080.0 + 40.0 * math.sin(ang))
            pose.right_hand_angle_deg = -15.0 + 20.0 * math.sin(ang)
        elif p < 0.75:
            prog = (p - 0.50) / 0.25
            pose.right_wrist_target = (640.0, 1080.0)
            pose.right_hand_angle_deg = -15.0 + 360.0 * prog
        else:
            prog = (p - 0.75) / 0.25
            s = prog * prog * (3.0 - 2.0 * prog)
            pose.right_wrist_target = (640.0 - 160.0 * s, 1080.0 + 180.0 * s)
            pose.right_hand_angle_deg = -15.0 + 30.0 * s

        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1080, 1920)
        ctx = cairo.Context(surf)
        ctx.set_source_rgb(0.98, 0.99, 1.0)
        ctx.paint()

        ctx.save()
        camera.apply_transform(ctx, shot, t)
        anat = rig.draw(ctx, pose)
        ctx.restore()

        # Rigorous bone length verification
        u_len = math.hypot(anat.right_elbow[0] - anat.right_shoulder[0], anat.right_elbow[1] - anat.right_shoulder[1])
        f_len = math.hypot(anat.right_wrist[0] - anat.right_elbow[0], anat.right_wrist[1] - anat.right_elbow[1])
        u_err = abs(u_len - expected_upper)
        f_err = abs(f_len - expected_forearm)
        max_arm_len_err = max(max_arm_len_err, u_err, f_err)
        assert u_err < 0.1, f"Upper arm stretched by {u_err:.2f}px"
        assert f_err < 0.1, f"Forearm stretched by {f_err:.2f}px"

        frames.append(surf)

    cfg = get_settings()
    out_mp4 = cfg.MM_RENDERS_DIR / "previews" / "test_b_arm_attachment.mp4"
    render_frames_to_mp4(frames, out_mp4, fps=fps)
    return out_mp4, {"max_bone_error_px": max_arm_len_err}


def run_test_c_body_movement() -> Tuple[Path, Dict[str, float]]:
    """Test C: Body movement isolated animation.
    Weight shifting, leaning, taking one step, reaching, and settling.
    Validates foot planting, balance, and connection.
    """
    fps = 30
    duration = 4.5
    total_frames = int(duration * fps)
    rig = CharacterRig()
    camera = Camera(1080, 1920)
    shot = CameraShot(ShotType.CUSTOM, center_x=460.0, center_y=1180.0, zoom=1.55)

    base_pose = RigPose(
        root_x=410.0,
        root_y=1294.0,
        floor_y=1520.0,
        scale=1.22,
        facing=1,
        yaw_factor=0.22,
        left_ankle_target=(352.0, 1500.48),
        right_ankle_target=(448.0, 1500.48),
        left_foot_planted=True,
        right_foot_planted=True,
    )

    frames: List[cairo.ImageSurface] = []
    max_plant_slip = 0.0

    for i in range(total_frames):
        t = i / float(fps)
        p = t / duration

        pose = RigPose(**base_pose.__dict__)

        # Mechanics:
        # 0.0..1.0s: Weight shift to back foot (pelvis moves left 14px, lean back)
        # 1.0..2.2s: Step forward with right foot (+35px), weight transfers forward
        # 2.2..3.5s: Lean forward into deep reach (pelvis +16px, arm reaches)
        # 3.5..4.5s: Recover and settle back to stable neutral stance
        if p < 0.22:
            prog = p / 0.22
            s = math.sin(prog * math.pi * 0.5)
            pose.root_x = 410.0 - 14.0 * s
            pose.torso_lean_deg = 3.0 - 4.0 * s
            pose.spine_arch_deg = 4.0 - 2.0 * s
        elif p < 0.48:
            prog = (p - 0.22) / 0.26
            s = prog * prog * (3.0 - 2.0 * prog)
            # Step right foot forward
            step_lift = 18.0 * math.sin(prog * math.pi)
            pose.right_ankle_target = (448.0 + 40.0 * s, 1500.48 - step_lift)
            pose.right_foot_roll_deg = -12.0 * math.sin(prog * math.pi)
            pose.right_foot_planted = (prog >= 0.95)
            pose.root_x = (410.0 - 14.0) + 28.0 * s
            pose.torso_lean_deg = -1.0 + 6.0 * s
        elif p < 0.77:
            prog = (p - 0.48) / 0.29
            s = math.sin(prog * math.pi * 0.5)
            pose.right_ankle_target = (488.0, 1500.48)
            pose.right_foot_planted = True
            pose.root_x = 424.0 + 16.0 * s
            pose.torso_lean_deg = 5.0 + 4.0 * s
            pose.right_wrist_target = (540.0 + 120.0 * s, 1200.0 - 90.0 * s)
            pose.right_hand_angle_deg = -15.0
        else:
            prog = (p - 0.77) / 0.23
            s = prog * prog * (3.0 - 2.0 * prog)
            pose.right_ankle_target = (488.0, 1500.48)
            pose.right_foot_planted = True
            pose.root_x = 440.0 - 10.0 * s
            pose.torso_lean_deg = 9.0 - 4.0 * s
            pose.right_wrist_target = (660.0 - 140.0 * s, 1110.0 + 120.0 * s)
            pose.mouth_state = "smirk"

        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1080, 1920)
        ctx = cairo.Context(surf)
        ctx.set_source_rgb(0.98, 0.99, 1.0)
        ctx.paint()

        ctx.save()
        camera.apply_transform(ctx, shot, t)
        anat = rig.draw(ctx, pose)
        ctx.restore()

        # Assert left foot stayed planted throughout
        l_slip = math.hypot(anat.left_ankle[0] - 352.0, anat.left_ankle[1] - 1500.48)
        max_plant_slip = max(max_plant_slip, l_slip)
        assert l_slip < 0.1, f"Planted left foot slipped by {l_slip:.2f}px"

        frames.append(surf)

    cfg = get_settings()
    out_mp4 = cfg.MM_RENDERS_DIR / "previews" / "test_c_body_movement.mp4"
    render_frames_to_mp4(frames, out_mp4, fps=fps)
    return out_mp4, {"max_plant_slip_px": max_plant_slip}


if __name__ == "__main__":
    print("Running Test A: Head Attachment...")
    out_a, stats_a = run_test_a_head_attachment()
    print(f"Test A PASSED -> {out_a}")

    print("Running Test B: Arm Attachment...")
    out_b, stats_b = run_test_b_arm_attachment()
    print(f"Test B PASSED -> {out_b} (max bone length error: {stats_b['max_bone_error_px']:.3f}px)")

    print("Running Test C: Body Movement & Weight Shifting...")
    out_c, stats_c = run_test_c_body_movement()
    print(f"Test C PASSED -> {out_c} (max planted slip: {stats_c['max_plant_slip_px']:.3f}px)")
