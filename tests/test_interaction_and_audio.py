"""Phase 3R Acceptance Tests — Reusable Physical Interaction Engine, 15-Key Calculator Simulation & Adaptive Audio.

Verifies:
1. All general-purpose physical interaction capabilities (`PRESS_BUTTON`, `PICK_UP`, `MOVE_OBJECT`, `RELEASE_OBJECT`,
   `OPEN_DOOR`, `CLOSE_DOOR`, `PUSH_OBJECT`, `PULL_OBJECT`, `TOUCH_MATH_SYMBOL`, `TOUCH_GEOMETRIC_SHAPE`) and strict
   contact-before-activation enforcement.
2. Exact 15-key calculator sequence (`1, 0, ÷, 2, =` -> `5`; `1, 0, ÷, 1, =` -> `10`; `1, 0, ÷, 0, =` -> `UNDEFINED`),
   verifying hand-to-button contact distance (`<= radius_px`) before every state change and zero simultaneous key conflicts.
3. Character motion quality, obstacle collision avoidance, `0.0 px` planted foot slip, and `0.0 px` limb length drift.
4. Generation, distinctness, and commercial provenance registration of all three musical candidates (`Option A`, `Option B`,
   `Option C`) plus adaptive audio state variations, comedic musical pause, and frame-synchronized SFX cues.
5. Output video integrity for both the 16s Debug Preview (`ep001_interaction_debug_preview.mp4`) and 16s Clean Production
   Render (`ep001_pilot_16s_1080x1920.mp4`).
"""

from __future__ import annotations

from pathlib import Path
import pytest

from app.adaptive_audio import (
    AdaptiveAudioEngine,
    AdaptiveMusicState,
    MusicCandidateOption,
    generate_three_music_candidates,
    verify_and_register_audio_provenance,
)
from app.config import get_settings
from app.database import create_db_engine, init_db, make_session_factory
from app.episode001_pilot import (
    EP001_CALC_BOX,
    render_ep001_interaction_upgrade_deliverables,
    simulate_ep001_timeline,
)
from app.interaction_engine import (
    InteractionActionType,
    InteractionStep,
    PhysicalInteractionEngine,
    create_door_object,
    create_grabbable_object,
    create_math_symbol_object,
    create_pushable_block_object,
)
from app.models import SafetyPolicyViolationError
from app.qc_mysterious_object import validate_animation_quality_metrics


def test_reusable_physical_interaction_engine_all_capabilities() -> None:
    """Verify pickup/hold/move/release, door open/close, push/pull, touch math symbol/shape, and no-contact rejection."""
    cube = create_grabbable_object("prop_cube", origin_x=300.0, origin_y=1100.0)
    door = create_door_object("lab_door", origin_x=700.0, origin_y=900.0)
    block = create_pushable_block_object("heavy_block", origin_x=500.0, origin_y=1400.0)
    symbol = create_math_symbol_object("pi_glyph", symbol_text="π", origin_x=450.0, origin_y=800.0)
    triangle = create_math_symbol_object("tri_shape", symbol_text="△", origin_x=620.0, origin_y=800.0)

    # Verify object-local coordinate roundtrip
    world_pt = cube.local_to_world((15.0, -20.0))
    local_pt = cube.world_to_local(world_pt)
    assert abs(local_pt[0] - 15.0) < 1e-6 and abs(local_pt[1] + 20.0) < 1e-6

    steps = [
        InteractionStep(
            step_id="act_pickup",
            object_id="prop_cube",
            target_id="grip_center",
            action=InteractionActionType.PICK_UP,
            start_time_sec=0.0,
            contact_time_sec=0.2,
            end_time_sec=0.4,
            effector="right_hand",
            sfx_cue="object_pickup",
        ),
        InteractionStep(
            step_id="act_move",
            object_id="prop_cube",
            target_id="grip_center",
            action=InteractionActionType.MOVE_OBJECT,
            start_time_sec=0.5,
            contact_time_sec=0.7,
            end_time_sec=0.9,
            effector="right_hand",
            sfx_cue="object_pickup",
            payload={"delta_x": 80.0, "delta_y": -50.0},
        ),
        InteractionStep(
            step_id="act_release",
            object_id="prop_cube",
            target_id="grip_center",
            action=InteractionActionType.RELEASE_OBJECT,
            start_time_sec=1.0,
            contact_time_sec=1.2,
            end_time_sec=1.4,
            effector="right_hand",
            sfx_cue="object_pickup",
        ),
        InteractionStep(
            step_id="act_open_door",
            object_id="lab_door",
            target_id="handle",
            action=InteractionActionType.OPEN_DOOR,
            start_time_sec=1.5,
            contact_time_sec=1.7,
            end_time_sec=1.9,
            effector="right_hand",
            sfx_cue="door_creak",
        ),
        InteractionStep(
            step_id="act_close_door",
            object_id="lab_door",
            target_id="handle",
            action=InteractionActionType.CLOSE_DOOR,
            start_time_sec=2.0,
            contact_time_sec=2.2,
            end_time_sec=2.4,
            effector="right_hand",
            sfx_cue="door_creak",
        ),
        InteractionStep(
            step_id="act_push_block",
            object_id="heavy_block",
            target_id="left_side",
            action=InteractionActionType.PUSH_OBJECT,
            start_time_sec=2.5,
            contact_time_sec=2.7,
            end_time_sec=2.9,
            effector="right_hand",
            sfx_cue="block_slide",
            payload={"delta_x": 65.0},
        ),
        InteractionStep(
            step_id="act_pull_block",
            object_id="heavy_block",
            target_id="right_side",
            action=InteractionActionType.PULL_OBJECT,
            start_time_sec=3.0,
            contact_time_sec=3.2,
            end_time_sec=3.4,
            effector="right_hand",
            sfx_cue="block_slide",
            payload={"delta_x": -25.0},
        ),
        InteractionStep(
            step_id="act_touch_symbol",
            object_id="pi_glyph",
            target_id="center",
            action=InteractionActionType.TOUCH_MATH_SYMBOL,
            start_time_sec=3.5,
            contact_time_sec=3.7,
            end_time_sec=3.9,
            effector="right_hand",
            sfx_cue="math_symbol_chime",
        ),
        InteractionStep(
            step_id="act_touch_shape",
            object_id="tri_shape",
            target_id="center",
            action=InteractionActionType.TOUCH_GEOMETRIC_SHAPE,
            start_time_sec=4.0,
            contact_time_sec=4.2,
            end_time_sec=4.4,
            effector="right_hand",
            sfx_cue="math_symbol_chime",
        ),
    ]

    engine = PhysicalInteractionEngine(
        objects={
            "prop_cube": cube,
            "lab_door": door,
            "heavy_block": block,
            "pi_glyph": symbol,
            "tri_shape": triangle,
        },
        steps=steps,
    )

    # 1. Verify SafetyPolicyViolationError is raised if contact_time is reached without physical contact!
    with pytest.raises(SafetyPolicyViolationError):
        engine.step_simulation(
            frame_idx=6,
            t_sec=0.2,
            solved_right_wrist=(0.0, 0.0),
            solved_left_wrist=(0.0, 0.0),
        )
    assert engine.objects["prop_cube"].state["held_by"] is None

    # 2. Reset and step through all scheduled contact times with the solved effector target position
    engine.reset()
    eval_times = [0.2, 0.4, 0.7, 0.9, 1.2, 1.4, 1.7, 1.9, 2.2, 2.4, 2.7, 2.9, 3.2, 3.4, 3.7, 3.9, 4.2, 4.4]
    for f_idx, t_c in enumerate(eval_times, start=10):
        target_pt, _, _ = engine.solve_effector_target(t_c, pelvis_pos=(250.0, 1100.0), effector="right_hand")
        engine.step_simulation(
            frame_idx=f_idx,
            t_sec=t_c,
            solved_right_wrist=target_pt,
            solved_left_wrist=(200.0, 1100.0),
        )

    assert engine.objects["prop_cube"].state["held_by"] is None
    assert engine.objects["prop_cube"].state["pick_count"] == 1
    assert engine.objects["prop_cube"].state["release_count"] == 1
    assert engine.objects["lab_door"].state["is_open"] is False
    assert engine.objects["heavy_block"].state["displaced_px"] == 40.0
    assert engine.objects["pi_glyph"].state["touched"] is True
    assert engine.objects["tri_shape"].state["touched"] is True
    assert len(engine.contact_events) == 9
    for ev in engine.contact_events:
        assert ev.contact_distance_px <= 28.0


def test_ep001_fifteen_calculator_presses_contact_and_math_states() -> None:
    """Verify all 15 Episode 001 calculator presses occur in order with physical contact and exact math results."""
    engine, snapshots = simulate_ep001_timeline(duration_seconds=16.0, fps=30)
    assert len(snapshots) == 480

    # Verify all 15 scheduled interactions completed via physical contact
    assert len(engine.contact_events) == 15
    pressed_keys = [ev.target_id.replace("key_", "") for ev in engine.contact_events]
    assert pressed_keys == [
        "1", "0", "÷", "2", "=",
        "1", "0", "÷", "1", "=",
        "1", "0", "÷", "0", "=",
    ]

    # Verify every single ContactEvent had physical hand-to-button contact (`contact_distance_px <= 24.0`)
    for ev in engine.contact_events:
        assert ev.contact_distance_px <= 24.0
        assert ev.contact_distance_px <= 6.0  # Exact 2-bone IK reach within button depression offset

    # Verify intermediate and final calculator display states at contact frames
    ev_eq_1 = engine.contact_events[4]   # 5th press: `10 ÷ 2 =` -> `5`
    ev_eq_2 = engine.contact_events[9]   # 10th press: `10 ÷ 1 =` -> `10`
    ev_eq_3 = engine.contact_events[14]  # 15th press: `10 ÷ 0 =` -> `UNDEFINED`

    snap_1 = snapshots[ev_eq_1.frame_idx]
    assert snap_1.expression_text == "10 ÷ 2 ="
    assert snap_1.result_text == "5"
    assert snap_1.error_mode is False
    assert snap_1.active_key == "="
    assert snap_1.button_depression_px >= 4.0

    snap_2 = snapshots[ev_eq_2.frame_idx]
    assert snap_2.expression_text == "10 ÷ 1 ="
    assert snap_2.result_text == "10"
    assert snap_2.error_mode is False
    assert snap_2.active_key == "="

    snap_3 = snapshots[ev_eq_3.frame_idx]
    assert snap_3.expression_text == "10 ÷ 0 ="
    assert snap_3.result_text == "UNDEFINED"
    assert snap_3.error_mode is True
    assert snap_3.active_key == "="


def test_ep001_rig_motion_collision_foot_locking_and_continuity() -> None:
    """Verify 0.0 px planted foot slip, 0.0 px limb length drift, obstacle clearance, and smooth continuity."""
    _, snapshots = simulate_ep001_timeline(duration_seconds=16.0, fps=30)
    states = [s.char_state for s in snapshots if s.char_state is not None]
    anatomies = [s.anatomy for s in snapshots if s.anatomy is not None]

    qa = validate_animation_quality_metrics(states, anatomies)
    assert qa["all_qa_checks_passed"] is True
    assert qa["max_left_planted_foot_slip_px"] == 0.0
    assert qa["max_right_planted_foot_slip_px"] == 0.0
    assert qa["leg_length_spread_px"] == 0.0
    assert qa["arm_length_spread_px"] == 0.0
    assert qa["head_radius_spread_px"] == 0.0
    assert qa["max_pelvis_velocity_px_per_frame"] < 25.0
    assert qa["max_head_velocity_px_per_frame"] < 32.0

    # Verify character pelvis never penetrates the calculator body box horizontally
    calc_x1 = float(EP001_CALC_BOX[0])
    for anat in anatomies:
        assert anat.pelvis[0] < calc_x1 - 30.0


def test_three_music_candidates_and_adaptive_audio_synchronization(tmp_path: Path) -> None:
    """Verify all 3 musical candidates (Options A, B, C), commercial provenance, and AdaptiveAudioEngine cues."""
    cfg = get_settings(tmp_path / ".env")
    cfg.MM_DATA_DIR = tmp_path / "data"
    cfg.MM_ASSETS_DIR = tmp_path / "assets"
    cfg.MM_RENDERS_DIR = tmp_path / "renders"
    cfg.ensure_directories()

    engine_db = create_db_engine(cfg.database_url, cfg)
    init_db(engine_db)
    session_factory = make_session_factory(engine_db)

    candidates = generate_three_music_candidates(
        out_dir=cfg.MM_ASSETS_DIR / "audio" / "candidates",
        duration_seconds=16.0,
    )
    assert set(candidates.keys()) == {
        MusicCandidateOption.OPTION_A_ORCHESTRAL_CARTOON.value,
        MusicCandidateOption.OPTION_B_ELECTRO_ACOUSTIC_ADVENTURE.value,
        MusicCandidateOption.OPTION_C_QUIRKY_MINIMALIST_PLUCKED.value,
    }
    hashes = set()
    for opt_id, art in candidates.items():
        assert art.wav_path.exists() and art.wav_path.stat().st_size > 1_000_000
        assert art.duration_seconds == 16.0
        assert 0.35 <= art.peak_amplitude <= 0.98
        assert art.rms_amplitude > 0.03
        hashes.add(art.sha256)
    # All three candidates must be acoustically distinct
    assert len(hashes) == 3

    # Verify AdaptiveAudioEngine synchronizes with all 15 ContactEvents + 3 evaluation chimes/alarms (18 cues)
    phys_engine, _ = simulate_ep001_timeline(duration_seconds=16.0, fps=30)
    audio_engine = AdaptiveAudioEngine(
        duration_seconds=16.0,
        fps=30,
        candidate_option=MusicCandidateOption.OPTION_A_ORCHESTRAL_CARTOON.value,
    )
    audio_engine.add_state_window(0.0, 10.35, AdaptiveMusicState.EXPLORATION)
    audio_engine.add_state_window(10.35, 12.68, AdaptiveMusicState.SUSPENSE)
    audio_engine.add_musical_pause(12.68, 13.25)
    audio_engine.add_state_window(13.25, 16.0, AdaptiveMusicState.CHAOS)

    cues = audio_engine.register_contact_events(phys_engine.contact_events)
    assert len(cues) == 18  # 15 key clicks + 3 result cues (`5`, `10`, `UNDEFINED`)
    sfx_names = [c.sfx_name for c in cues]
    assert sfx_names.count("button_click") == 15
    assert "positive_calc_chime" in sfx_names
    assert "intrigued_calc_double_chime" in sfx_names
    assert "division_by_zero_alarm" in sfx_names
    assert audio_engine.is_in_musical_pause(12.90) is True

    mix_wav = cfg.MM_ASSETS_DIR / "audio" / "ep001_adaptive_16s_audio.wav"
    mix_meta = audio_engine.render_adaptive_episode_mix(mix_wav)
    assert mix_wav.exists()
    assert mix_meta["sound_cue_count"] == 18

    with session_factory() as session:
        reg_assets = verify_and_register_audio_provenance(session, candidates, episode_mix_path=mix_wav)
        assert len(reg_assets) == 4
        for a in reg_assets:
            assert a.commercial_use_cleared is True
            assert a.sponsored_use_cleared is True


def test_ep001_debug_preview_and_clean_16s_production_render() -> None:
    """Verify the workspace 16s Debug Preview, 16s Clean Production Render, and 3 Music Candidates exist and pass QA."""
    from app.render_smoke import probe_video_metadata, resolve_ffmpeg_exe

    cfg = get_settings()
    ffmpeg_exe = resolve_ffmpeg_exe(cfg)

    cand_dir = cfg.MM_ASSETS_DIR / "audio" / "candidates"
    dbg_mp4 = cfg.MM_RENDERS_DIR / "previews" / "ep001_interaction_debug_preview.mp4"
    dbg_sheet = cfg.MM_RENDERS_DIR / "previews" / "ep001_interaction_debug_contact_sheet.png"
    cln_mp4 = cfg.MM_RENDERS_DIR / "previews" / "ep001_pilot_16s_1080x1920.mp4"
    cln_sheet = cfg.MM_RENDERS_DIR / "previews" / "ep001_pilot_contact_sheet.png"

    if not (dbg_mp4.exists() and cln_mp4.exists() and (cand_dir / "candidate_a_orchestral_cartoon.wav").exists()):
        engine_db = create_db_engine(cfg.database_url, cfg)
        init_db(engine_db)
        session_factory = make_session_factory(engine_db)
        with session_factory() as session:
            render_ep001_interaction_upgrade_deliverables(settings=cfg, session=session)

    for fname in (
        "candidate_a_orchestral_cartoon.wav",
        "candidate_b_electro_acoustic_adventure.wav",
        "candidate_c_quirky_minimalist_plucked.wav",
    ):
        p = cand_dir / fname
        assert p.exists() and p.stat().st_size > 1_000_000, f"Missing candidate {fname}"

    assert dbg_mp4.exists() and dbg_mp4.stat().st_size > 80_000
    assert dbg_sheet.exists() and dbg_sheet.stat().st_size > 50_000
    dbg_probe = probe_video_metadata(dbg_mp4, ffmpeg_exe=ffmpeg_exe)
    assert dbg_probe["width"] == 1080 and dbg_probe["height"] == 1920
    assert dbg_probe["frame_count"] == 480
    assert dbg_probe["fps"] == 30.0
    assert dbg_probe["has_audio"] is True

    assert cln_mp4.exists() and cln_mp4.stat().st_size > 80_000
    assert cln_sheet.exists() and cln_sheet.stat().st_size > 50_000
    cln_probe = probe_video_metadata(cln_mp4, ffmpeg_exe=ffmpeg_exe)
    assert cln_probe["width"] == 1080 and cln_probe["height"] == 1920
    assert cln_probe["frame_count"] == 480
    assert cln_probe["fps"] == 30.0
    assert cln_probe["has_audio"] is True
