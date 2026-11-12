"""Overhaul v4.0 Demonstration Script:
Renders the complete 7.0-second required demonstration:
1. Natural stance beside resized calculator.
2. Character looks towards keypad.
3. Physically enters: 1 -> 0 -> ÷ -> 2 -> =
4. Display updates: "10 ÷ 2 = 5"
5. Subtle satisfied smirk reaction and natural settle.
6. Produces clean MP4, debug overlay MP4, contact sheet, and automated validation report.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cairo

sys.path.insert(0, str(Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem")))

from app.anim.calculator_prop import CairoCalculatorProp
from app.anim.calculator_state import CalculatorState
from app.anim.interaction_planner import InteractionPlanner
from app.anim.rig import CharacterRig, RigPose
from app.anim.scene import Camera, CameraShot, ShotType
from app.anim.scene_config import SCENE_CONFIG
from app.cairo_character_rig import OptionCCharacterSpec, SolvedCairoAnatomy, solve_cairo_anatomy
from app.config import get_settings
from app.render_smoke import resolve_ffmpeg_exe


def render_v4_demonstration(render_debug: bool = False) -> Tuple[Path, Path, Dict[str, Any]]:
    cfg = get_settings()
    out_dir = cfg.MM_RENDERS_DIR / "previews"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    mp4_filename = "v4_calculator_debug_preview.mp4" if render_debug else "v4_calculator_interaction_clean.mp4"
    mp4_path = out_dir / mp4_filename
    contact_sheet_path = out_dir / ("v4_debug_contact_sheet.png" if render_debug else "v4_clean_contact_sheet.png")

    fps = 30
    duration = 7.0
    total_frames = int(duration * fps)  # 210 frames

    scene_cfg = SCENE_CONFIG
    rig = CharacterRig()
    calc_prop = CairoCalculatorProp(config=scene_cfg.calculator)
    calc_state = CalculatorState()
    planner = InteractionPlanner(scene_config=scene_cfg)
    camera = Camera(1080, 1920)

    # 1. Plan exact sequence: 1 -> 0 -> ÷ -> 2 -> =
    sequence = ["1", "0", "÷", "2", "="]
    plans = planner.plan_sequence(sequence, t_start=0.9)

    # Base comfortable standing posture beside calculator
    base_pose = RigPose(
        root_x=scene_cfg.character.root_x,
        root_y=scene_cfg.character.root_y,
        floor_y=scene_cfg.character.floor_y,
        scale=scene_cfg.character.scale,
        facing=1,
        yaw_factor=0.22,
        torso_lean_deg=5.0,
        spine_arch_deg=6.0,
        head_tilt_deg=3.0,
        mouth_state="smirk",
    )

    # Medium Staging Shot for balanced character + calculator composition
    shot = CameraShot(
        shot_type=ShotType.CUSTOM,
        center_x=580.0,
        center_y=1120.0,
        zoom=1.35,
    )

    ffmpeg_exe = resolve_ffmpeg_exe(cfg)

    # Metrics & Validation Tracking
    validation_report = {
        "total_frames": total_frames,
        "sequence_expected": sequence,
        "input_events_logged": [],
        "max_contact_distance_px": 0.0,
        "teleport_count": 0,
        "arm_length_errors": [],
        "stance_foot_slip_count": 0,
        "final_expression": "",
        "final_result": "",
    }

    prev_anatomy: Optional[SolvedCairoAnatomy] = None
    processed_contacts = set()
    sampled_frames: List[Tuple[str, cairo.ImageSurface]] = []

    sample_targets = {
        int(0.6 * fps): "1. Stance Beside Calculator",
        int(1.4 * fps): "2. Press '1' (Contact Center)",
        int(2.2 * fps): "3. Press '0' (Contact Center)",
        int(3.0 * fps): "4. Press '÷' (Accurate Arc)",
        int(4.6 * fps): "5. Press '=' (Result '5')",
        int(6.4 * fps): "6. Settle & Satisfied Smirk",
    }

    with tempfile.TemporaryDirectory(prefix="mm_v4_") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)

        for frame_idx in range(total_frames):
            t_sec = frame_idx / float(fps)

            # 1. Evaluate Interaction Planner
            pose, active_contact_key, button_dep = planner.evaluate(t_sec, plans, base_pose)

            # 2. Check and Apply Calculator State on Physical Contact
            if active_contact_key is not None:
                # Find matching plan
                for plan in plans:
                    if plan.key_label == active_contact_key and plan.contact_time <= t_sec <= plan.release_time:
                        if plan.key_label not in processed_contacts:
                            calc_state.process_key_event(plan.key_label)
                            processed_contacts.add(plan.key_label)
                            validation_report["input_events_logged"].append({
                                "key": plan.key_label,
                                "timestamp_sec": round(t_sec, 3),
                                "frame": frame_idx,
                                "expression_display": calc_state.expression_text,
                                "result_display": calc_state.result_text,
                            })
            else:
                # Hand withdrawn
                calc_state.release_key()
                # Clear from processed once release phase ends so repeat keys could be pressed
                for plan in plans:
                    if t_sec > plan.release_time and plan.key_label in processed_contacts:
                        # Keep logged, but allow next button
                        pass

            # Subtle facial acting after result is displayed
            if t_sec > 4.7:
                pose.mouth_state = "smirk"
                pose.right_brow_raise_px = 6.0
                pose.head_tilt_deg = -3.0

            # 3. Render Frame to Cairo
            surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1080, 1920)
            ctx = cairo.Context(surf)
            
            ctx.set_source_rgb(1.0, 1.0, 1.0)
            ctx.paint()

            # Apply Medium Cinematic Camera
            ctx.save()
            camera.apply_transform(ctx, shot, t_sec)

            # Floor line
            ctx.set_source_rgb(0.06, 0.08, 0.12)
            ctx.set_line_width(6.0)
            ctx.move_to(-500.0, scene_cfg.floor_y)
            ctx.line_to(2000.0, scene_cfg.floor_y)
            ctx.stroke()

            # Calculator Prop
            calc_prop.draw(
                ctx,
                expression_text=calc_state.expression_text,
                result_text=calc_state.result_text,
                active_key=calc_state.active_key,
                error_mode=calc_state.error_mode,
                button_depression_px=calc_state.button_depression_px,
            )

            # Character Rig
            anat = rig.draw(ctx, pose)

            # 4. Optional Debug Visualizations
            if render_debug:
                ctx.save()
                # Draw skeleton bones
                ctx.set_source_rgba(0.12, 0.58, 0.95, 0.85)
                ctx.set_line_width(3.0)
                ctx.move_to(*anat.pelvis)
                ctx.line_to(*anat.shoulder_center)
                ctx.line_to(*anat.head_center)
                ctx.move_to(*anat.right_shoulder)
                ctx.line_to(*anat.right_elbow)
                ctx.line_to(*anat.right_wrist)
                ctx.stroke()

                # Draw joint points
                for j_pt in [anat.pelvis, anat.right_shoulder, anat.right_elbow, anat.right_wrist, anat.right_ankle]:
                    ctx.arc(j_pt[0], j_pt[1], 5.0, 0, 2*math.pi)
                    ctx.set_source_rgb(0.95, 0.20, 0.20)
                    ctx.fill()

                # Draw button hitboxes and interaction target
                for b_lbl, b_cfg in scene_cfg.calculator.buttons.items():
                    bx, by = scene_cfg.calculator.get_button_world_pos(b_lbl)
                    ctx.arc(bx, by, b_cfg.hit_radius, 0, 2*math.pi)
                    ctx.set_source_rgba(0.20, 0.80, 0.20, 0.35)
                    ctx.stroke()

                # Highlight active contact
                if active_contact_key:
                    target_w = scene_cfg.calculator.get_button_world_pos(active_contact_key)
                    ctx.arc(target_w[0], target_w[1], 10.0, 0, 2*math.pi)
                    ctx.set_source_rgba(0.95, 0.80, 0.10, 0.90)
                    ctx.fill()

                ctx.restore()

            ctx.restore()

            # 5. Continuous Frame-by-Frame QA Validation
            if prev_anatomy is not None:
                # Telescoping check: Upper arm + Forearm must remain invariant
                cur_arm = anat.right_arm_total_length
                expected_arm = round((scene_cfg.character.upper_arm_length + scene_cfg.character.forearm_length) * scene_cfg.character.scale, 2)
                if abs(cur_arm - expected_arm) > 0.05:
                    validation_report["arm_length_errors"].append((frame_idx, cur_arm, expected_arm))

                # Foot slip check
                if pose.left_foot_planted:
                    f_drift = math.hypot(anat.left_ankle[0] - prev_anatomy.left_ankle[0], anat.left_ankle[1] - prev_anatomy.left_ankle[1])
                    if f_drift > 0.01:
                        validation_report["stance_foot_slip_count"] += 1

                # Joint teleport check
                v_wrist = math.hypot(anat.right_wrist[0] - prev_anatomy.right_wrist[0], anat.right_wrist[1] - prev_anatomy.right_wrist[1])
                if v_wrist > 25.0:
                    validation_report["teleport_count"] += 1

            if active_contact_key is not None:
                target_w = scene_cfg.calculator.get_button_world_pos(active_contact_key)
                dist = math.hypot(anat.right_wrist[0] - target_w[0], anat.right_wrist[1] - (target_w[1] + 4.0))
                if dist > validation_report["max_contact_distance_px"]:
                    validation_report["max_contact_distance_px"] = round(dist, 2)

            prev_anatomy = anat

            if frame_idx in sample_targets:
                sampled_frames.append((sample_targets[frame_idx], surf))

            frame_png = tmp_dir / f"frame_{frame_idx:04d}.png"
            surf.write_to_png(str(frame_png))

        validation_report["final_expression"] = calc_state.expression_text
        validation_report["final_result"] = calc_state.result_text

        # Encode MP4
        cmd = [
            ffmpeg_exe,
            "-y",
            "-framerate", str(fps),
            "-i", str(tmp_dir / "frame_%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(mp4_path),
        ]
        proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg encoding failed: {proc.stderr}")

    # Generate 6-panel Contact Sheet
    card_w, card_h = 320, 568
    pad = 20
    sheet_w = len(sampled_frames) * card_w + (len(sampled_frames) + 1) * pad
    sheet_h = card_h + 100
    sheet_surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, sheet_w, sheet_h)
    sctx = cairo.Context(sheet_surf)
    sctx.set_source_rgb(0.06, 0.09, 0.16)
    sctx.paint()

    sctx.select_font_face("Segoe UI", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    sctx.set_font_size(20.0)
    sctx.set_source_rgb(1.0, 1.0, 1.0)
    sctx.move_to(pad, 34.0)
    sctx.show_text(f"MATH MAYHEM v4.0 — {'DEBUG' if render_debug else 'CLEAN'} DEMONSTRATION: 10 ÷ 2 = 5")

    for idx, (label, src_surf) in enumerate(sampled_frames):
        x0 = pad + idx * (card_w + pad)
        y0 = 55
        sctx.save()
        sctx.translate(x0, y0)
        sctx.scale(card_w / 1080.0, card_h / 1920.0)
        sctx.set_source_surface(src_surf, 0, 0)
        sctx.paint()
        sctx.restore()

        sctx.set_font_size(13.0)
        sctx.set_source_rgb(0.88, 0.92, 0.96)
        sctx.move_to(x0, y0 + card_h + 24.0)
        sctx.show_text(label)

    sheet_surf.write_to_png(str(contact_sheet_path))

    return mp4_path, contact_sheet_path, validation_report


if __name__ == "__main__":
    print("1. Rendering Clean Demonstration...")
    c_mp4, c_sheet, c_report = render_v4_demonstration(render_debug=False)
    print("   Clean Render Complete:", c_mp4)
    print("   Clean Contact Sheet:", c_sheet)
    print("   Validation Report:")
    print(json.dumps(c_report, indent=2))

    print("\n2. Rendering Debug Demonstration...")
    d_mp4, d_sheet, d_report = render_v4_demonstration(render_debug=True)
    print("   Debug Render Complete:", d_mp4)
    print("   Debug Contact Sheet:", d_sheet)
