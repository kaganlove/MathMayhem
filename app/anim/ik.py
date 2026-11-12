"""Exact 2-Bone Inverse Kinematics solver with strict bone length preservation,
analytical Law of Cosines knee/elbow angles, and reachable workspace limits.
"""

from __future__ import annotations

import math
from typing import Tuple

Point = Tuple[float, float]


def solve_two_bone_ik(
    root: Point,
    target: Point,
    len1: float,
    len2: float,
    pole_dir: int = 1,
) -> Tuple[Point, Point, float]:
    """Solve 2-bone analytic IK strictly preserving bone segment lengths len1 and len2.

    Returns:
        mid_joint: (x, y) coordinates of the elbow / knee.
        effector_pos: (x, y) coordinates of the wrist / ankle (guaranteed dist = len2 from mid_joint).
        reach_fraction: actual target distance / (len1 + len2) clamped to [0.0, 1.0].
    """
    dx = target[0] - root[0]
    dy = target[1] - root[1]
    dist = math.hypot(dx, dy)

    max_reach = (len1 + len2) - 1e-4
    min_reach = abs(len1 - len2) + 1e-4

    reach_fraction = min(1.0, dist / (len1 + len2))
    clamped_dist = max(min_reach, min(max_reach, dist))

    base_ang = math.atan2(dy, dx)

    # Law of Cosines: c^2 = a^2 + b^2 - 2ab cos(C)
    cos_a = (len1 * len1 + clamped_dist * clamped_dist - len2 * len2) / (2.0 * len1 * clamped_dist)
    cos_a = max(-1.0, min(1.0, cos_a))
    ang_a = math.acos(cos_a)

    joint_ang = base_ang + pole_dir * ang_a
    mid_joint: Point = (
        root[0] + len1 * math.cos(joint_ang),
        root[1] + len1 * math.sin(joint_ang),
    )

    # Calculate final effector position ensuring exact len2 length
    end_dx = target[0] - mid_joint[0]
    end_dy = target[1] - mid_joint[1]
    end_ang = math.atan2(end_dy, end_dx)

    effector_pos: Point = (
        mid_joint[0] + len2 * math.cos(end_ang),
        mid_joint[1] + len2 * math.sin(end_ang),
    )

    return mid_joint, effector_pos, reach_fraction
