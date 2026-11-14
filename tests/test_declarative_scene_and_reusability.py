"""Automated Acceptance Tests: Reusable Animation Library & Declarative Scene Engine.

Verifies Workstream 5, Workstream 6, and Section 12 Step 7:
1. Canonical pose library invariance & Option C constraints.
2. Declarative scene compiler & SymPy mathematical verification.
3. Zero foot slip and length invariance during procedural locomotion.
4. Coordinated reach articulation (elbow bend >= 35 deg, 0.000px contact error).
5. Independent demonstration scene video integrity and QA metrics.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List

import pytest

from app.animation_library import (
    CANONICAL_POSES,
    AnimationLibrary,
    EasingType,
    apply_easing,
)
from app.cairo_character_rig import (
    OptionCCharacterSpec,
    SolvedCairoAnatomy,
    solve_cairo_anatomy,
)
from app.config import get_settings
from app.demo_reusable_scene import (
    build_chalkboard_reusable_scene,
    render_demonstration_scene,
)
from app.qc_mysterious_object import validate_animation_quality_metrics
from app.render_smoke import probe_video_metadata, resolve_ffmpeg_exe
from app.scene_engine import (
    ActionType,
    BackgroundSpec,
    BackgroundType,
    CharacterAction,
    DeclarativeSceneCompiler,
    MathTextElement,
    SceneDefinition,
)


@pytest.fixture
def spec() -> OptionCCharacterSpec:
    return OptionCCharacterSpec()


@pytest.fixture
def anim_lib(spec: OptionCCharacterSpec) -> AnimationLibrary:
    return AnimationLibrary(spec)


def test_canonical_poses_and_spec_invariance(spec: OptionCCharacterSpec, anim_lib: AnimationLibrary) -> None:
    """Verify that all canonical pose templates solve without anatomical deformation."""
    spec.validate()
    assert spec.has_pupils is False
    assert spec.has_backpack is False
    assert spec.speaks is False

    assert len(CANONICAL_POSES) >= 8

    for pose_name, template in CANONICAL_POSES.items():
        st = anim_lib.build_rig_state_from_pose(template, pelvis_x=412.0, floor_y=1520.0, scale=1.22)
        anat = solve_cairo_anatomy(spec, st)

        # Proportions must match spec exactly
        assert abs(anat.head_radius_px - spec.head_radius * 1.22) < 1e-4
        assert abs(anat.left_leg_total_length - (spec.thigh_length + spec.shin_length) * 1.22) < 1e-4
        assert abs(anat.right_leg_total_length - (spec.thigh_length + spec.shin_length) * 1.22) < 1e-4
        assert abs(anat.left_arm_total_length - (spec.upper_arm_length + spec.forearm_length) * 1.22) < 1e-4
        assert abs(anat.right_arm_total_length - (spec.upper_arm_length + spec.forearm_length) * 1.22) < 1e-4


def test_declarative_scene_math_verification() -> None:
    """Verify that the declarative scene compiler uses SymPy to validate mathematical elements."""
    compiler = DeclarativeSceneCompiler()

    valid_scene = SceneDefinition(
        scene_id="test_valid_math",
        title="Valid Identities",
        duration_seconds=2.0,
        math_elements=[
            MathTextElement("10 / 2", position=(100, 100), expected_result="5"),
            MathTextElement("(a - b) * (a + b) = a^2 - b^2", position=(100, 200)),
        ],
    )
    results = compiler.verify_scene_mathematics(valid_scene)
    assert len(results) == 2
    assert all(r.is_valid for r in results)


def test_walk_cycle_zero_foot_slip_and_continuity(spec: OptionCCharacterSpec, anim_lib: AnimationLibrary) -> None:
    """Verify that procedural locomotion achieves 0.0000px foot slip and bounded pelvis steps."""
    walk_states = anim_lib.generate_walk_cycle(
        start_x=140.0,
        end_x=390.0,
        total_frames=54,
        floor_y=1520.0,
        scale=1.22,
        step_length=65.0,
    )
    assert len(walk_states) == 54

    anatomies = [solve_cairo_anatomy(spec, st) for st in walk_states]
    qa = validate_animation_quality_metrics(walk_states, anatomies)

    assert qa["max_left_planted_foot_slip_px"] <= 0.0001
    assert qa["max_right_planted_foot_slip_px"] <= 0.0001
    assert qa["max_pelvis_velocity_px_per_frame"] < 25.0
    assert qa["max_head_velocity_px_per_frame"] < 38.0
    assert qa["all_qa_checks_passed"] is True


def test_coordinated_reach_elbow_bend_and_contact(spec: OptionCCharacterSpec, anim_lib: AnimationLibrary) -> None:
    """Verify that coordinated reach achieves subpixel contact while maintaining elbow bend >= 35 deg."""
    idle_pose = anim_lib.get_pose_template("standing_idle")
    base_state = anim_lib.build_rig_state_from_pose(idle_pose, pelvis_x=390.0, floor_y=1520.0, scale=1.22)

    target_touch = (520.0, 880.0)
    reach_states = anim_lib.generate_coordinated_reach(
        base_state=base_state,
        target_pos=target_touch,
        total_frames=30,
        hold_frames=6,
        max_reach_lean_deg=18.0,
    )
    assert len(reach_states) == 30

    # Check contact frame (frame 15)
    contact_st = reach_states[15]
    anat = solve_cairo_anatomy(spec, contact_st)

    contact_error = math.hypot(anat.right_wrist[0] - target_touch[0], anat.right_wrist[1] - target_touch[1])
    assert contact_error <= 0.0001

    # Check elbow bend angle at contact
    s_x, s_y = anat.right_shoulder
    e_x, e_y = anat.right_elbow
    w_x, w_y = anat.right_wrist

    v1 = (s_x - e_x, s_y - e_y)
    v2 = (w_x - e_x, w_y - e_y)
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.hypot(v1[0], v1[1])
    mag2 = math.hypot(v2[0], v2[1])
    cos_theta = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    elbow_angle_deg = math.degrees(math.acos(cos_theta))

    assert elbow_angle_deg >= 35.0, f"Elbow bend {elbow_angle_deg:.2f} deg was less than 35.0 deg requirement"


def test_reusable_chalkboard_demonstration_integrity() -> None:
    """Verify that the independent reusability demonstration renders with valid video and audio."""
    cfg = get_settings()
    video_path = cfg.MM_RENDERS_DIR / "previews" / "demo_reusable_chalkboard_scene.mp4"
    sheet_path = cfg.MM_RENDERS_DIR / "previews" / "demo_reusable_chalkboard_sheet.png"

    # If not already rendered, execute render
    if not video_path.exists() or not sheet_path.exists():
        res = render_demonstration_scene(output_mp4=video_path, contact_sheet_path=sheet_path)
        assert res["success"] is True

    assert video_path.exists() and video_path.stat().st_size > 50_000
    assert sheet_path.exists() and sheet_path.stat().st_size > 20_000

    ffmpeg_exe = resolve_ffmpeg_exe(cfg)
    probe = probe_video_metadata(video_path, ffmpeg_exe=ffmpeg_exe)

    assert probe["width"] == 1080
    assert probe["height"] == 1920
    assert abs(probe["fps"] - 30.0) < 0.1
    assert probe["frame_count"] == 180
    assert probe["has_audio"] is True
    assert probe["audio_codec"] == "aac"
