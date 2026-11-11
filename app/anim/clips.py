"""Animation Clip system: keyframes, timing curves, anticipation and follow-through."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple, Any

from app.anim.rig import RigPose


class Easing(str, Enum):
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    OVERSHOOT = "overshoot"     # Anticipation / bounce
    ELASTIC = "elastic"
    HOLD = "hold"


def evaluate_easing(t: float, curve: Easing = Easing.EASE_IN_OUT) -> float:
    """Evaluate normalized timing curve t in [0.0, 1.0]."""
    t = max(0.0, min(1.0, t))
    if curve == Easing.LINEAR:
        return t
    elif curve == Easing.EASE_IN:
        return t * t * t
    elif curve == Easing.EASE_OUT:
        u = 1.0 - t
        return 1.0 - u * u * u
    elif curve == Easing.EASE_IN_OUT:
        # Hermite smootherstep
        return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)
    elif curve == Easing.OVERSHOOT:
        # Anticipation or overshoot back curve
        s = 1.5
        t -= 1.0
        return t * t * ((s + 1.0) * t + s) + 1.0
    elif curve == Easing.HOLD:
        return 0.0 if t < 1.0 else 1.0
    return t


@dataclass
class Keyframe:
    """A single keyframe at a relative time offset with pose channels and easing to next key."""
    time_offset: float
    channels: Dict[str, Any]
    easing: Easing = Easing.EASE_IN_OUT


@dataclass
class AnimationClip:
    """Reusable, authorable keyframed animation clip with intentional timing."""
    name: str
    duration: float
    keyframes: List[Keyframe]
    loop: bool = False

    def sample(self, t: float, base_pose: RigPose) -> RigPose:
        """Sample the clip at time t (in seconds) and blend into a copy of base_pose."""
        import copy
        result = copy.deepcopy(base_pose)
        if not self.keyframes:
            return result

        local_t = t % self.duration if self.loop else max(0.0, min(self.duration, t))
        sorted_keys = sorted(self.keyframes, key=lambda k: k.time_offset)

        # Before first keyframe
        if local_t <= sorted_keys[0].time_offset:
            for ch, val in sorted_keys[0].channels.items():
                if hasattr(result, ch):
                    setattr(result, ch, val)
            return result

        # After last keyframe
        if local_t >= sorted_keys[-1].time_offset:
            for ch, val in sorted_keys[-1].channels.items():
                if hasattr(result, ch):
                    setattr(result, ch, val)
            return result

        # Between two keyframes
        for idx in range(len(sorted_keys) - 1):
            k0 = sorted_keys[idx]
            k1 = sorted_keys[idx + 1]
            if k0.time_offset <= local_t <= k1.time_offset:
                span = max(1e-4, k1.time_offset - k0.time_offset)
                norm_p = (local_t - k0.time_offset) / span
                eased_p = evaluate_easing(norm_p, k0.easing)

                # Interpolate each channel
                for ch, val1 in k1.channels.items():
                    if not hasattr(result, ch):
                        continue
                    val0 = k0.channels.get(ch, getattr(result, ch))
                    if isinstance(val1, (int, float)) and isinstance(val0, (int, float)):
                        interp = val0 + (val1 - val0) * eased_p
                        setattr(result, ch, interp)
                    elif isinstance(val1, tuple) and len(val1) == 2 and isinstance(val0, tuple) and len(val0) == 2:
                        interp_tuple = (
                            val0[0] + (val1[0] - val0[0]) * eased_p,
                            val0[1] + (val1[1] - val0[1]) * eased_p,
                        )
                        setattr(result, ch, interp_tuple)
                    else:
                        # Discrete property (e.g. mouth_state, bool)
                        setattr(result, ch, val1 if norm_p >= 0.5 else val0)
                break

        return result
