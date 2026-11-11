"""Standard clip library implementing the core acting actions:
Curiosity, Hesitation, Confusion, Suspicion, Surprise, Fear,
Frustration, Excitement, Realization, Embarrassment, Celebration, Recovery.
"""

from __future__ import annotations

from app.anim.clips import AnimationClip, Easing, Keyframe


def make_curiosity_clip() -> AnimationClip:
    """Subtle head tilt, brow lift, leaning in towards target."""
    return AnimationClip(
        name="curiosity",
        duration=1.2,
        keyframes=[
            Keyframe(0.0, {
                "torso_lean_deg": 4.0,
                "spine_arch_deg": 6.0,
                "head_tilt_deg": 2.0,
                "head_nod_px": 0.0,
                "left_brow_raise_px": 0.0,
                "right_brow_raise_px": 0.0,
                "brow_slant_deg": 0.0,
                "mouth_state": "smirk",
            }, Easing.EASE_OUT),
            Keyframe(0.6, {
                "torso_lean_deg": 7.5,
                "spine_arch_deg": 8.5,
                "head_tilt_deg": 6.5,
                "head_nod_px": 2.0,
                "left_brow_raise_px": 5.0,
                "right_brow_raise_px": 8.5,
                "brow_slant_deg": 8.0,
                "mouth_state": "curious_o",
            }, Easing.EASE_IN_OUT),
            Keyframe(1.2, {
                "torso_lean_deg": 7.0,
                "spine_arch_deg": 8.0,
                "head_tilt_deg": 5.5,
                "head_nod_px": 1.5,
                "left_brow_raise_px": 4.5,
                "right_brow_raise_px": 7.5,
                "brow_slant_deg": 7.0,
                "mouth_state": "curious_o",
            }, Easing.EASE_OUT),
        ]
    )


def make_surprise_clip() -> AnimationClip:
    """Sudden anticipation dip, upward recoil, gasping mouth, high brows, glasses slip."""
    return AnimationClip(
        name="surprise",
        duration=1.0,
        keyframes=[
            Keyframe(0.0, {
                "torso_lean_deg": 7.0,
                "spine_arch_deg": 8.0,
                "head_tilt_deg": 4.0,
                "shoulder_shrug_px": 0.0,
                "glasses_slip_px": 0.0,
                "mouth_state": "smirk",
            }, Easing.EASE_IN),
            # Quick anticipation dip
            Keyframe(0.12, {
                "torso_lean_deg": 9.0,
                "spine_arch_deg": 9.5,
                "shoulder_shrug_px": -2.0,
                "mouth_state": "firm",
            }, Easing.OVERSHOOT),
            # Sudden shock recoil
            Keyframe(0.40, {
                "torso_lean_deg": -10.0,
                "spine_arch_deg": -9.0,
                "head_tilt_deg": -8.0,
                "head_nod_px": -3.5,
                "shoulder_shrug_px": 10.0,
                "glasses_slip_px": 4.5,
                "left_brow_raise_px": 11.0,
                "right_brow_raise_px": 11.0,
                "brow_slant_deg": 10.0,
                "mouth_state": "open_gasp",
            }, Easing.EASE_OUT),
            # Settle
            Keyframe(1.0, {
                "torso_lean_deg": -8.0,
                "spine_arch_deg": -7.5,
                "head_tilt_deg": -6.0,
                "head_nod_px": -2.0,
                "shoulder_shrug_px": 8.0,
                "glasses_slip_px": 4.0,
                "left_brow_raise_px": 9.0,
                "right_brow_raise_px": 9.0,
                "mouth_state": "open_gasp",
            }, Easing.EASE_IN_OUT),
        ]
    )


def make_recovery_clip() -> AnimationClip:
    """Relief sigh, shoulders drop, hand adjusts glasses back up, smirk returns."""
    return AnimationClip(
        name="recovery",
        duration=1.5,
        keyframes=[
            Keyframe(0.0, {
                "torso_lean_deg": -8.0,
                "shoulder_shrug_px": 8.0,
                "glasses_slip_px": 4.0,
                "mouth_state": "open_gasp",
            }, Easing.EASE_IN_OUT),
            # Exhale & settle
            Keyframe(0.6, {
                "torso_lean_deg": 2.0,
                "shoulder_shrug_px": 2.0,
                "glasses_slip_px": 3.0,
                "left_brow_raise_px": 3.0,
                "right_brow_raise_px": 4.0,
                "mouth_state": "firm",
            }, Easing.EASE_OUT),
            # Pushing glasses back into place & confident smirk
            Keyframe(1.5, {
                "torso_lean_deg": 5.0,
                "spine_arch_deg": 7.0,
                "shoulder_shrug_px": 0.0,
                "glasses_slip_px": 0.0,
                "left_brow_raise_px": 2.0,
                "right_brow_raise_px": 4.0,
                "brow_slant_deg": -2.0,
                "mouth_state": "smirk",
            }, Easing.EASE_OUT),
        ]
    )
