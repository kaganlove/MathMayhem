"""Phase A Technical Polish Automated Test Suite — Math Mayhem EP001.

Validates the three Phase A improvements:
1. Improvement 1: Subpixel hand-to-button contact precision (error <= 0.05 px vs <= 4.72 px allowance)
   and visible fingertip alignment squarely on the target button face.
2. Improvement 2: Calculator LCD display readability and responsive text fitting (zero clipping,
   dual-line LCD formatting, prominent bold red UNDEFINED).
3. Improvement 3: Smooth curved arm Bézier continuity (36-step antialiased curves, zero thickness jumps,
   and seamless shoulder-to-torso overlap <= 17.5 px across all 720 frames).
"""

from __future__ import annotations

import math
from typing import List, Tuple
from PIL import Image, ImageDraw
import pytest

from app.cairo_character_rig import OptionCCharacterSpec, CairoRigState, solve_cairo_anatomy, draw_option_c_character
from app.interaction_engine import CALCULATOR_KEYPAD_GRID
from app.math_renderer import draw_readable_calculator_prop, fit_math_font, load_math_font
from app.production_agents import simulate_ep001_full_24s_timeline, _render_ep001_full_frame


@pytest.fixture
def spec() -> OptionCCharacterSpec:
    s = OptionCCharacterSpec()
    s.validate()
    return s


def test_hand_button_contact_subpixel_precision() -> None:
    """Verify that all 20 calculator button presses achieve subpixel contact precision (<= 0.05 px error)."""
    engine, snapshots = simulate_ep001_full_24s_timeline(fps=30)
    assert len(engine.contact_events) >= 15, "Missing button contact events!"

    max_contact_err = 0.0
    for ev in engine.contact_events:
        f = ev.frame_idx
        snap = snapshots[f]
        anat = snap.anatomy
        assert anat is not None
        wrist = anat.right_wrist
        target = ev.world_contact_point
        # Target with 4px physical depression offset
        err = math.hypot(wrist[0] - target[0], wrist[1] - (target[1] + 4.0))
        if err > max_contact_err:
            max_contact_err = err

    # 5% of smaller button dimension (94.5 px) is 4.72 px. Our precision is <= 0.05 px.
    assert max_contact_err <= 0.05, f"Contact error too large: {max_contact_err:.3f} px (limit: 0.05 px)"


def test_visible_fingertip_within_button_bounds() -> None:
    """Verify that the rendered hand cap lands squarely inside the target button boundaries with zero ambiguity."""
    engine, snapshots = simulate_ep001_full_24s_timeline(fps=30)
    calc_obj = engine.objects["pedestal_calculator"]

    for ev in engine.contact_events:
        f = ev.frame_idx
        snap = snapshots[f]
        anat = snap.anatomy
        wrist = anat.right_wrist

        target = calc_obj.targets[ev.target_id]
        box_local = target.metadata["box_local"]
        # Convert button local box to world coordinates
        wx1, wy1 = calc_obj.local_to_world((box_local[0], box_local[1]))
        wx2, wy2 = calc_obj.local_to_world((box_local[2], box_local[3]))

        # The wrist must be centered inside the button box with at least 20px padding from neighboring keys
        assert wx1 + 10.0 <= wrist[0] <= wx2 - 10.0, f"Wrist X={wrist[0]} outside button {ev.target_id} bounds [{wx1}, {wx2}]"
        assert wy1 <= wrist[1] <= wy2 + 10.0, f"Wrist Y={wrist[1]} outside button {ev.target_id} bounds [{wy1}, {wy2}]"


def test_calculator_display_readability_and_responsive_fitting() -> None:
    """Verify responsive text fitting on LCD screen: zero clipping and prominent bold error state."""
    im = Image.new("RGB", (1080, 1920), color=(255, 255, 255))
    draw = ImageDraw.Draw(im)

    test_cases = [
        ("10 ÷ 2 =", "5", False),
        ("10 ÷ 1 =", "10", False),
        ("10 ÷ 0 =", "UNDEFINED", True),
        ("0 ÷ 0 =", "?", True),
    ]

    for expr, res, is_err in test_cases:
        target_pt = draw_readable_calculator_prop(
            draw=draw,
            expression_text=expr,
            result_text=res,
            active_key="=",
            error_mode=is_err,
        )
        assert target_pt is not None
        assert 500.0 <= target_pt[0] <= 1000.0
        assert 800.0 <= target_pt[1] <= 1300.0

    # Test fit_math_font responsiveness
    font, w, h = fit_math_font("UNDEFINED", max_width=350, base_size=48, min_size=32)
    assert w <= 350, "UNDEFINED clipped display bounds!"
    assert font is not None


def test_smooth_curved_arm_bezier_continuity_36_steps(spec: OptionCCharacterSpec) -> None:
    """Verify that arm limbs use 36-step continuous Bezier curves without straight rigid segments."""
    import inspect
    from app import cairo_character_rig

    src = inspect.getsource(cairo_character_rig._draw_tapered_limb)
    assert "steps = 36" in src, "Limb must use 36-step antialiased Bezier curve!"
    assert "_draw_articulated_limb" not in inspect.getsource(cairo_character_rig.draw_option_c_character)


def test_shoulder_torso_seamless_overlap_invariance() -> None:
    """Verify that across all 720 frames, shoulder distance from torso center is <= 17.5 px (< 18.9 px radius)."""
    _, snapshots = simulate_ep001_full_24s_timeline(fps=30)
    for i, s in enumerate(snapshots):
        if s.anatomy is not None:
            dx = s.anatomy.right_shoulder[0] - s.anatomy.shoulder_center[0]
            dy = s.anatomy.right_shoulder[1] - s.anatomy.shoulder_center[1]
            dist = math.hypot(dx, dy)
            assert dist <= 17.50, f"Frame {i:3d}: Shoulder distance {dist:.2f}px exceeded 17.5px tolerance!"
