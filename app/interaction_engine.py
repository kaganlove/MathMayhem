"""Phase 3R — Reusable General-Purpose Physical Interaction Engine (`app/interaction_engine.py`).

Provides a reusable, contact-gated physical interaction system for AI production agents across all
Math Mayhem episodes. Supports:
1. Pressing buttons, keypad keys, and switches (`PRESS_BUTTON`).
2. Picking up, holding, moving, and releasing objects (`PICK_UP`, `MOVE_OBJECT`, `RELEASE_OBJECT`).
3. Opening and closing hinged/sliding doors (`OPEN_DOOR`, `CLOSE_DOOR`).
4. Pushing and pulling heavy objects (`PUSH_OBJECT`, `PULL_OBJECT`).
5. Touching mathematical symbols and geometric shapes (`TOUCH_MATH_SYMBOL`, `TOUCH_GEOMETRIC_SHAPE`).

Core Invariants:
- Every `InteractiveObject` uses object-local coordinates (`local_to_world` / `world_to_local`), collision bounds,
  and named `ContactTarget` regions (`local_pos`, `radius_px`, `depression_offset_local`).
- Every `InteractionStep` defines an explicit target, action, contact event, resulting state change, and completion condition.
- **Strict Contact-Before-Activation Rule:** Object state updates and sound effects trigger ONLY when the character's
  solved hand effector physically enters the target's collision region (`distance <= target.radius_px`).
- **Keypad Mutual Exclusion Rule:** Only one button on a keypad may be depressed/registered at any time.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from PIL import ImageDraw

from app.math_renderer import load_math_font
from app.math_verifier import verify_math_statement
from app.models import SafetyPolicyViolationError


Point = Tuple[float, float]
Box = Tuple[float, float, float, float]


def _smootherstep(t: float) -> float:
    x = max(0.0, min(1.0, t))
    return x * x * x * (x * (x * 6.0 - 15.0) + 10.0)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


class InteractionActionType(str, Enum):
    """Supported physical interaction actions across Math Mayhem episodes."""

    PRESS_BUTTON = "press_button"
    PICK_UP = "pick_up"
    MOVE_OBJECT = "move_object"
    RELEASE_OBJECT = "release_object"
    OPEN_DOOR = "open_door"
    CLOSE_DOOR = "close_door"
    PUSH_OBJECT = "push_object"
    PULL_OBJECT = "pull_object"
    TOUCH_MATH_SYMBOL = "touch_math_symbol"
    TOUCH_GEOMETRIC_SHAPE = "touch_geometric_shape"


@dataclass
class ContactTarget:
    """Named contact point and collision sphere in object-local coordinates."""

    target_id: str
    label: str
    local_pos: Point
    radius_px: float = 20.0
    depression_offset_local: Point = (0.0, 4.0)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContactEvent:
    """Emitted on the exact frame/timestamp when physical hand-to-target contact occurs."""

    step_id: str
    object_id: str
    target_id: str
    action: InteractionActionType
    timestamp_sec: float
    frame_idx: int
    world_contact_point: Point
    effector_pos: Point
    contact_distance_px: float
    sfx_cue: str
    state_change_summary: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InteractiveObject:
    """General-purpose interactive scene prop with object-local coordinates, collision bounds, and state."""

    object_id: str
    object_type: str  # `calculator` | `grabbable` | `door` | `push_block` | `math_symbol` | `geometric_shape`
    origin_x: float
    origin_y: float
    rotation_deg: float = 0.0
    scale: float = 1.0
    collision_box_local: Box = (0.0, 0.0, 100.0, 100.0)
    targets: Dict[str, ContactTarget] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)

    def local_to_world(self, local_pt: Point) -> Point:
        """Transform object-local `(lx, ly)` into world-space `(wx, wy)`."""
        rad = math.radians(self.rotation_deg)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)
        sx = local_pt[0] * self.scale
        sy = local_pt[1] * self.scale
        wx = self.origin_x + sx * cos_r - sy * sin_r
        wy = self.origin_y + sx * sin_r + sy * cos_r
        return (wx, wy)

    def world_to_local(self, world_pt: Point) -> Point:
        """Transform world-space `(wx, wy)` into object-local `(lx, ly)`."""
        dx = world_pt[0] - self.origin_x
        dy = world_pt[1] - self.origin_y
        rad = math.radians(-self.rotation_deg)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)
        s = max(1e-6, self.scale)
        lx = (dx * cos_r - dy * sin_r) / s
        ly = (dx * sin_r + dy * cos_r) / s
        return (lx, ly)

    def get_target_world_pos(self, target_id: str) -> Point:
        if target_id not in self.targets:
            raise KeyError(f"Unknown target '{target_id}' on object '{self.object_id}'")
        return self.local_to_world(self.targets[target_id].local_pos)

    def get_world_collision_box(self) -> Box:
        x1, y1, x2, y2 = self.collision_box_local
        corners = [
            self.local_to_world((x1, y1)),
            self.local_to_world((x2, y1)),
            self.local_to_world((x2, y2)),
            self.local_to_world((x1, y2)),
        ]
        xs = [p[0] for p in corners]
        ys = [p[1] for p in corners]
        return (min(xs), min(ys), max(xs), max(ys))


@dataclass
class InteractionStep:
    """Declarative specification of a single physical interaction with explicit target, contact window, and completion."""

    step_id: str
    object_id: str
    target_id: str
    action: InteractionActionType
    start_time_sec: float
    contact_time_sec: float
    end_time_sec: float
    effector: str = "right_hand"
    sfx_cue: str = "button_click"
    payload: Dict[str, Any] = field(default_factory=dict)
    # Runtime tracking
    contact_triggered: bool = False
    completed: bool = False
    contact_distance_at_trigger_px: Optional[float] = None


# ---------------------------------------------------------------------------
# Factory Builders for Standard Interactive Props
# ---------------------------------------------------------------------------

CALCULATOR_KEYPAD_GRID: List[List[str]] = [
    ["7", "8", "9", "÷"],
    ["4", "5", "6", "×"],
    ["1", "2", "3", "−"],
    ["C", "0", "+", "="],
]


def create_calculator_interactive_object(
    object_id: str = "pedestal_calculator",
    box: Tuple[int, int, int, int] = (565, 560, 1015, 1280),
) -> InteractiveObject:
    """Create a 4x4 interactive calculator prop with exact local coordinates for all 16 keys."""
    x1, y1, x2, y2 = box
    width = float(x2 - x1)
    height = float(y2 - y1)

    scr_bottom_local = 250.0
    grid_top_local = scr_bottom_local + 32.0
    pad_x = 24.0
    gap = 8.0
    col_w = (width - 2.0 * pad_x - 3.0 * gap) / 4.0
    row_h = (height - grid_top_local - 28.0 - 3.0 * gap) / 4.0

    targets: Dict[str, ContactTarget] = {}
    for r_idx, row in enumerate(CALCULATOR_KEYPAD_GRID):
        for c_idx, key_label in enumerate(row):
            bx1 = pad_x + c_idx * (col_w + gap)
            by1 = grid_top_local + r_idx * (row_h + gap)
            cx = bx1 + col_w * 0.5
            cy = by1 + row_h * 0.5
            t_id = f"key_{key_label}"
            targets[t_id] = ContactTarget(
                target_id=t_id,
                label=key_label,
                local_pos=(cx, cy),
                radius_px=24.0,
                depression_offset_local=(0.0, 4.0),
                metadata={
                    "row": r_idx,
                    "col": c_idx,
                    "key": key_label,
                    "box_local": (bx1, by1, bx1 + col_w, by1 + row_h),
                },
            )

    return InteractiveObject(
        object_id=object_id,
        object_type="calculator",
        origin_x=float(x1),
        origin_y=float(y1),
        collision_box_local=(0.0, 0.0, width, height),
        targets=targets,
        state={
            "expression_tokens": [],
            "expression_text": "READY",
            "result_text": "0",
            "active_key": None,
            "active_target_id": None,
            "button_depression_px": 0.0,
            "error_mode": False,
            "just_evaluated": False,
            "history": [],
        },
    )


def create_grabbable_object(
    object_id: str,
    origin_x: float,
    origin_y: float,
    width: float = 64.0,
    height: float = 64.0,
) -> InteractiveObject:
    """Create a grabbable prop that can be picked up, held, moved, and released."""
    return InteractiveObject(
        object_id=object_id,
        object_type="grabbable",
        origin_x=origin_x,
        origin_y=origin_y,
        collision_box_local=(-width * 0.5, -height * 0.5, width * 0.5, height * 0.5),
        targets={
            "grip_center": ContactTarget(
                target_id="grip_center",
                label="Grip",
                local_pos=(0.0, 0.0),
                radius_px=24.0,
            )
        },
        state={"held_by": None, "pick_count": 0, "release_count": 0},
    )


def create_door_object(
    object_id: str,
    origin_x: float,
    origin_y: float,
    width: float = 160.0,
    height: float = 340.0,
) -> InteractiveObject:
    """Create a hinged door prop with a movable handle target that opens (`0.0 -> 1.0`) and closes (`1.0 -> 0.0`)."""
    return InteractiveObject(
        object_id=object_id,
        object_type="door",
        origin_x=origin_x,
        origin_y=origin_y,
        collision_box_local=(0.0, -height, width, 0.0),
        targets={
            "handle": ContactTarget(
                target_id="handle",
                label="Door Handle",
                local_pos=(width * 0.82, -height * 0.48),
                radius_px=26.0,
            )
        },
        state={"open_fraction": 0.0, "is_open": False, "width": width, "height": height},
    )


def create_pushable_block_object(
    object_id: str,
    origin_x: float,
    origin_y: float,
    width: float = 120.0,
    height: float = 120.0,
) -> InteractiveObject:
    """Create a heavy block prop with left/right push/pull contact surfaces."""
    return InteractiveObject(
        object_id=object_id,
        object_type="push_block",
        origin_x=origin_x,
        origin_y=origin_y,
        collision_box_local=(-width * 0.5, -height, width * 0.5, 0.0),
        targets={
            "left_side": ContactTarget(
                target_id="left_side",
                label="Push Surface",
                local_pos=(-width * 0.5, -height * 0.5),
                radius_px=26.0,
            ),
            "right_side": ContactTarget(
                target_id="right_side",
                label="Pull Surface",
                local_pos=(width * 0.5, -height * 0.5),
                radius_px=26.0,
            ),
        },
        state={"displaced_px": 0.0},
    )


def create_math_symbol_object(
    object_id: str,
    symbol_text: str,
    origin_x: float,
    origin_y: float,
    radius_px: float = 28.0,
) -> InteractiveObject:
    """Create a touchable floating mathematical symbol or geometric shape prop."""
    return InteractiveObject(
        object_id=object_id,
        object_type="math_symbol",
        origin_x=origin_x,
        origin_y=origin_y,
        collision_box_local=(-radius_px, -radius_px, radius_px, radius_px),
        targets={
            "center": ContactTarget(
                target_id="center",
                label=symbol_text,
                local_pos=(0.0, 0.0),
                radius_px=radius_px,
            )
        },
        state={"symbol": symbol_text, "touched": False, "glow_intensity": 0.0},
    )


# ---------------------------------------------------------------------------
# Contact-Gated Physical Interaction Engine
# ---------------------------------------------------------------------------


class PhysicalInteractionEngine:
    """Manages interactive scene objects, solves contact-aware hand trajectories, and enforces contact-before-activation."""

    def __init__(
        self,
        objects: Dict[str, InteractiveObject],
        steps: List[InteractionStep],
        rest_right_wrist_offset: Point = (96.0, -145.0),
        rest_left_wrist_offset: Point = (-44.0, -12.0),
    ) -> None:
        self.initial_objects = copy.deepcopy(objects)
        self.initial_steps = copy.deepcopy(steps)
        self.rest_right_wrist_offset = rest_right_wrist_offset
        self.rest_left_wrist_offset = rest_left_wrist_offset
        self.reset()

    def reset(self) -> None:
        self.objects: Dict[str, InteractiveObject] = copy.deepcopy(self.initial_objects)
        self.steps: List[InteractionStep] = copy.deepcopy(self.initial_steps)
        self.contact_events: List[ContactEvent] = []
        self.last_frame_idx: int = -1

    def solve_effector_target(
        self,
        t_sec: float,
        pelvis_pos: Point,
        effector: str = "right_hand",
    ) -> Tuple[Point, Optional[InteractionStep], float]:
        """Compute smooth, collision-aware world-space wrist target `(x, y)` for `effector` at `t_sec`.

        Returns `(wrist_world_pos, active_step, contact_blend_weight)`.
        When transitioning between consecutive steps on the same object within `0.45s`, uses a compact
        inter-key arc (`42 px` pullback) so typing multi-key sequences looks fluid and natural.
        """
        default_offset = self.rest_right_wrist_offset if effector == "right_hand" else self.rest_left_wrist_offset
        rest_pt: Point = (pelvis_pos[0] + default_offset[0], pelvis_pos[1] + default_offset[1])

        rel_steps = [s for s in self.steps if s.effector == effector]
        if not rel_steps:
            return rest_pt, None, 0.0

        # Find if t_sec is inside an active step
        for idx, step in enumerate(rel_steps):
            if step.start_time_sec <= t_sec <= step.end_time_sec:
                obj = self.objects[step.object_id]
                target_pt = obj.get_target_world_pos(step.target_id)

                # Determine start anchor of this reach: either rest_pt or a compact inter-key hover from previous key
                prev_step = rel_steps[idx - 1] if idx > 0 else None
                if prev_step is not None and (step.start_time_sec - prev_step.end_time_sec) <= 0.35:
                    prev_obj = self.objects[prev_step.object_id]
                    prev_pt = prev_obj.get_target_world_pos(prev_step.target_id)
                    start_pt: Point = (prev_pt[0] - 38.0, prev_pt[1] - 12.0)
                    is_compact_hop = True
                else:
                    start_pt = rest_pt
                    is_compact_hop = False

                # Determine end anchor after contact: either rest_pt or compact inter-key hover before next key
                next_step = rel_steps[idx + 1] if idx + 1 < len(rel_steps) else None
                if next_step is not None and (next_step.start_time_sec - step.end_time_sec) <= 0.35:
                    end_pt: Point = (target_pt[0] - 38.0, target_pt[1] - 12.0)
                    is_compact_exit = True
                else:
                    end_pt = rest_pt
                    is_compact_exit = False

                # Continuous actions (`MOVE_OBJECT`, `PUSH_OBJECT`, `PULL_OBJECT`, `OPEN_DOOR`, `CLOSE_DOOR`)
                if step.action in (
                    InteractionActionType.MOVE_OBJECT,
                    InteractionActionType.PUSH_OBJECT,
                    InteractionActionType.PULL_OBJECT,
                    InteractionActionType.OPEN_DOOR,
                    InteractionActionType.CLOSE_DOOR,
                ):
                    if t_sec <= step.contact_time_sec:
                        span = max(1e-4, step.contact_time_sec - step.start_time_sec)
                        p = _smootherstep((t_sec - step.start_time_sec) / span)
                        arc = -24.0 * math.sin(math.pi * p)
                        return (_lerp(start_pt[0], target_pt[0], p), _lerp(start_pt[1], target_pt[1], p) + arc), step, p
                    else:
                        span = max(1e-4, step.end_time_sec - step.contact_time_sec)
                        p = _smootherstep((t_sec - step.contact_time_sec) / span)
                        if step.action == InteractionActionType.OPEN_DOOR:
                            w = float(obj.state["width"])
                            ly = obj.targets[step.target_id].local_pos[1]
                            return obj.local_to_world((w * (0.82 - 0.55 * p), ly)), step, 1.0
                        if step.action == InteractionActionType.CLOSE_DOOR:
                            w = float(obj.state["width"])
                            ly = obj.targets[step.target_id].local_pos[1]
                            return obj.local_to_world((w * (0.27 + 0.55 * p), ly)), step, 1.0
                        dx = float(step.payload.get("delta_x", 0.0))
                        dy = float(step.payload.get("delta_y", 0.0))
                        base_ox = float(step.payload.get("_start_origin_x", obj.origin_x))
                        base_oy = float(step.payload.get("_start_origin_y", obj.origin_y))
                        local_t = obj.targets[step.target_id].local_pos
                        moved_pt: Point = (base_ox + local_t[0] + dx * p, base_oy + local_t[1] + dy * p)
                        return moved_pt, step, 1.0

                # Discrete contact actions (`PRESS_BUTTON`, `PICK_UP`, `RELEASE_OBJECT`, `TOUCH_MATH_SYMBOL`, `TOUCH_GEOMETRIC_SHAPE`)
                hold_half = 0.045
                contact_start = max(step.start_time_sec + 0.02, step.contact_time_sec - hold_half)
                contact_end = min(step.end_time_sec - 0.02, step.contact_time_sec + hold_half)

                if t_sec < contact_start:
                    p = _smootherstep((t_sec - step.start_time_sec) / max(1e-4, contact_start - step.start_time_sec))
                    arc_amp = -16.0 if is_compact_hop else -28.0
                    arc = arc_amp * math.sin(math.pi * p)
                    wx = _lerp(start_pt[0], target_pt[0], p)
                    wy = _lerp(start_pt[1], target_pt[1], p) + arc
                    return (wx, wy), step, p
                elif t_sec <= contact_end:
                    # Physically on the target (with slight downward button depression)
                    dep = obj.targets[step.target_id].depression_offset_local
                    return (target_pt[0] + dep[0], target_pt[1] + dep[1]), step, 1.0
                else:
                    p = _smootherstep((t_sec - contact_end) / max(1e-4, step.end_time_sec - contact_end))
                    arc_amp = -12.0 if is_compact_exit else -22.0
                    arc = arc_amp * math.sin(math.pi * p)
                    wx = _lerp(target_pt[0], end_pt[0], p)
                    wy = _lerp(target_pt[1], end_pt[1], p) + arc
                    return (wx, wy), step, 1.0 - p

        # Check if t_sec sits in a brief gap between two consecutive compact-hop steps
        for idx in range(len(rel_steps) - 1):
            s_prev = rel_steps[idx]
            s_next = rel_steps[idx + 1]
            if s_prev.end_time_sec < t_sec < s_next.start_time_sec:
                gap = s_next.start_time_sec - s_prev.end_time_sec
                if gap <= 0.35:
                    prev_pt = self.objects[s_prev.object_id].get_target_world_pos(s_prev.target_id)
                    return (prev_pt[0] - 38.0, prev_pt[1] - 12.0), None, 0.0

        return rest_pt, None, 0.0

    def step_simulation(
        self,
        frame_idx: int,
        t_sec: float,
        solved_right_wrist: Point,
        solved_left_wrist: Point,
    ) -> List[ContactEvent]:
        """Advance object states for `frame_idx` based strictly on physical effector contact."""
        new_events: List[ContactEvent] = []

        # Clear transient button highlights from previous frames before checking current frame contacts
        for obj in self.objects.values():
            if obj.object_type == "calculator":
                obj.state["active_key"] = None
                obj.state["active_target_id"] = None
                obj.state["button_depression_px"] = 0.0

        for step in self.steps:
            obj = self.objects[step.object_id]
            target = obj.targets[step.target_id]
            target_world = obj.get_target_world_pos(step.target_id)
            eff_pos = solved_right_wrist if step.effector == "right_hand" else solved_left_wrist
            dist = math.hypot(eff_pos[0] - target_world[0], eff_pos[1] - target_world[1])

            is_in_contact = dist <= target.radius_px

            # Keep button visually depressed while effector is physically in contact during step window
            if step.start_time_sec <= t_sec <= step.end_time_sec and is_in_contact:
                if step.action == InteractionActionType.PRESS_BUTTON and obj.object_type == "calculator":
                    # Enforce mutual exclusion: never allow two keys depressed at once
                    if obj.state["active_target_id"] not in (None, target.target_id):
                        raise SafetyPolicyViolationError(
                            f"Keypad mutual exclusion violated: '{obj.state['active_target_id']}' and '{target.target_id}'"
                        )
                    obj.state["active_key"] = target.label
                    obj.state["active_target_id"] = target.target_id
                    obj.state["button_depression_px"] = target.depression_offset_local[1]

            # Check if step has reached its contact trigger moment
            if not step.contact_triggered and t_sec >= step.contact_time_sec - 1e-4:
                if not is_in_contact:
                    raise SafetyPolicyViolationError(
                        f"Interaction step '{step.step_id}' reached contact_time={step.contact_time_sec:.2f}s "
                        f"without physical contact (dist={dist:.2f}px > radius={target.radius_px:.2f}px)."
                    )
                step.contact_triggered = True
                step.contact_distance_at_trigger_px = round(dist, 3)
                summary, sfx = self._apply_contact_state_change(step, obj, target, t_sec)
                ev = ContactEvent(
                    step_id=step.step_id,
                    object_id=step.object_id,
                    target_id=step.target_id,
                    action=step.action,
                    timestamp_sec=round(t_sec, 4),
                    frame_idx=frame_idx,
                    world_contact_point=target_world,
                    effector_pos=eff_pos,
                    contact_distance_px=round(dist, 3),
                    sfx_cue=sfx,
                    state_change_summary=summary,
                    payload=dict(step.payload),
                )
                self.contact_events.append(ev)
                new_events.append(ev)

            # Continuous state updates while held/pushed/pulled/hinged after initial physical contact
            if step.contact_triggered and step.contact_time_sec <= t_sec <= step.end_time_sec:
                span = max(1e-4, step.end_time_sec - step.contact_time_sec)
                p = _smootherstep((t_sec - step.contact_time_sec) / span)
                if step.action == InteractionActionType.MOVE_OBJECT and obj.state.get("held_by") == step.effector:
                    obj.origin_x = eff_pos[0]
                    obj.origin_y = eff_pos[1]
                elif step.action in (InteractionActionType.PUSH_OBJECT, InteractionActionType.PULL_OBJECT):
                    base_ox = float(step.payload.get("_start_origin_x", obj.origin_x))
                    dx = float(step.payload.get("delta_x", 0.0))
                    obj.origin_x = base_ox + dx * p
                    obj.state["displaced_px"] = round(obj.origin_x - self.initial_objects[obj.object_id].origin_x, 2)
                    updated_target = obj.get_target_world_pos(step.target_id)
                    if math.hypot(eff_pos[0] - updated_target[0], eff_pos[1] - updated_target[1]) > target.radius_px:
                        raise SafetyPolicyViolationError(f"Lost contact during {step.action} on '{obj.object_id}'")
                elif step.action == InteractionActionType.OPEN_DOOR:
                    obj.state["open_fraction"] = round(p, 3)
                    obj.state["is_open"] = p >= 0.95
                    w = float(obj.state["width"])
                    target.local_pos = (w * (0.82 - 0.55 * p), target.local_pos[1])
                elif step.action == InteractionActionType.CLOSE_DOOR:
                    obj.state["open_fraction"] = round(1.0 - p, 3)
                    obj.state["is_open"] = (1.0 - p) > 0.05
                    w = float(obj.state["width"])
                    target.local_pos = (w * (0.27 + 0.55 * p), target.local_pos[1])

            if not step.completed and step.contact_triggered and t_sec >= step.end_time_sec - 1e-4:
                step.completed = True

        # Keep any held grabbable object attached to its holding effector between steps
        for obj in self.objects.values():
            if obj.object_type == "grabbable" and obj.state.get("held_by") in ("right_hand", "left_hand"):
                holder = solved_right_wrist if obj.state["held_by"] == "right_hand" else solved_left_wrist
                obj.origin_x = holder[0]
                obj.origin_y = holder[1]

        self.last_frame_idx = frame_idx
        return new_events

    def _apply_contact_state_change(
        self,
        step: InteractionStep,
        obj: InteractiveObject,
        target: ContactTarget,
        t_sec: float,
    ) -> Tuple[str, str]:
        """Apply the deterministic object state transition upon verified physical contact."""
        if step.action == InteractionActionType.PRESS_BUTTON and obj.object_type == "calculator":
            key = target.label
            expected_key = step.payload.get("expected_key", key)
            if key != expected_key:
                raise SafetyPolicyViolationError(
                    f"Calculator button mismatch in '{step.step_id}': touched '{key}', expected '{expected_key}'"
                )
            obj.state["active_key"] = key
            obj.state["active_target_id"] = target.target_id
            obj.state["button_depression_px"] = target.depression_offset_local[1]

            if key == "C":
                obj.state["expression_tokens"] = []
                obj.state["expression_text"] = "READY"
                obj.state["result_text"] = "0"
                obj.state["error_mode"] = False
                obj.state["just_evaluated"] = False
                return "Calculator cleared to READY / 0", step.sfx_cue

            if obj.state.get("just_evaluated") and key in "0123456789":
                obj.state["expression_tokens"] = []
                obj.state["result_text"] = ""
                obj.state["error_mode"] = False
                obj.state["just_evaluated"] = False

            if key in ("÷", "×", "−", "+"):
                obj.state["expression_tokens"].append(f" {key} ")
                expr_str = "".join(obj.state["expression_tokens"]).strip()
                obj.state["expression_text"] = expr_str
                return f"Operator '{key}' appended -> '{expr_str}'", step.sfx_cue

            if key == "=":
                obj.state["expression_tokens"].append(" =")
                expr_str = "".join(obj.state["expression_tokens"]).strip()
                obj.state["expression_text"] = expr_str
                expected_res = str(step.payload.get("expected_result", ""))
                check = verify_math_statement(expr_str, expected_res)
                obj.state["result_text"] = check.computed_result
                obj.state["error_mode"] = check.is_undefined_division_by_zero
                obj.state["just_evaluated"] = True
                obj.state["history"].append((expr_str, check.computed_result, round(t_sec, 3)))
                sfx = "division_by_zero_alarm" if check.is_undefined_division_by_zero else step.sfx_cue
                return f"Evaluated '{expr_str}' -> '{check.computed_result}'", sfx

            # Digit key (`0`..`9`)
            obj.state["expression_tokens"].append(key)
            expr_str = "".join(obj.state["expression_tokens"]).strip()
            obj.state["expression_text"] = expr_str
            # Show current number being typed in result line before `=`
            parts = expr_str.split()
            obj.state["result_text"] = parts[-1] if parts else key
            return f"Digit '{key}' appended -> '{expr_str}'", step.sfx_cue

        if step.action == InteractionActionType.PRESS_BUTTON:
            obj.state["pressed"] = not obj.state.get("pressed", False)
            return f"Button '{target.label}' toggled to {obj.state['pressed']}", step.sfx_cue

        if step.action == InteractionActionType.PICK_UP:
            obj.state["held_by"] = step.effector
            obj.state["pick_count"] = int(obj.state.get("pick_count", 0)) + 1
            return f"Object '{obj.object_id}' picked up by {step.effector}", step.sfx_cue

        if step.action == InteractionActionType.MOVE_OBJECT:
            if obj.state.get("held_by") != step.effector:
                raise SafetyPolicyViolationError(f"Cannot move '{obj.object_id}' before picking it up")
            step.payload["_start_origin_x"] = obj.origin_x
            step.payload["_start_origin_y"] = obj.origin_y
            return f"Moving held object '{obj.object_id}'", step.sfx_cue

        if step.action == InteractionActionType.RELEASE_OBJECT:
            obj.state["held_by"] = None
            obj.state["release_count"] = int(obj.state.get("release_count", 0)) + 1
            return f"Object '{obj.object_id}' released at ({obj.origin_x:.1f}, {obj.origin_y:.1f})", step.sfx_cue

        if step.action == InteractionActionType.OPEN_DOOR:
            step.payload["_start_origin_x"] = obj.origin_x
            step.payload["_start_origin_y"] = obj.origin_y
            return f"Door '{obj.object_id}' handle contacted -> opening", step.sfx_cue

        if step.action == InteractionActionType.CLOSE_DOOR:
            step.payload["_start_origin_x"] = obj.origin_x
            step.payload["_start_origin_y"] = obj.origin_y
            return f"Door '{obj.object_id}' handle contacted -> closing", step.sfx_cue

        if step.action in (InteractionActionType.PUSH_OBJECT, InteractionActionType.PULL_OBJECT):
            step.payload["_start_origin_x"] = obj.origin_x
            step.payload["_start_origin_y"] = obj.origin_y
            return f"Block '{obj.object_id}' contacted for {step.action.value}", step.sfx_cue

        if step.action in (InteractionActionType.TOUCH_MATH_SYMBOL, InteractionActionType.TOUCH_GEOMETRIC_SHAPE):
            obj.state["touched"] = True
            obj.state["glow_intensity"] = 1.0
            return f"Math entity '{obj.object_id}' activated on physical contact", step.sfx_cue

        return f"Executed {step.action.value} on {obj.object_id}.{target.target_id}", step.sfx_cue


def draw_interaction_debug_overlay(
    draw: ImageDraw.ImageDraw,
    engine: PhysicalInteractionEngine,
    solved_right_wrist: Point,
    solved_left_wrist: Point,
    active_step: Optional[InteractionStep],
    t_sec: float,
    frame_idx: int,
    hud_override: Optional[Dict[str, Any]] = None,
) -> None:
    """Draw collision boxes, contact target spheres, effector crosshairs, and contact telemetry onto `draw`."""
    dbg_font = load_math_font(20)
    small_font = load_math_font(16)

    for obj in engine.objects.values():
        bx1, by1, bx2, by2 = obj.get_world_collision_box()
        draw.rectangle([bx1, by1, bx2, by2], outline=(0, 180, 216), width=3)

        for target in obj.targets.values():
            wx, wy = obj.get_target_world_pos(target.target_id)
            r = target.radius_px
            dist_r = math.hypot(solved_right_wrist[0] - wx, solved_right_wrist[1] - wy)
            dist_l = math.hypot(solved_left_wrist[0] - wx, solved_left_wrist[1] - wy)
            is_contact = min(dist_r, dist_l) <= r
            is_scheduled = active_step is not None and active_step.target_id == target.target_id

            if is_contact and is_scheduled:
                col = (16, 185, 129)  # Emerald green: verified physical contact!
                w = 5
            elif is_scheduled:
                col = (245, 158, 11)  # Amber: active target being approached
                w = 4
            else:
                col = (148, 163, 184)  # Slate: inactive target region
                w = 2

            draw.ellipse([wx - r, wy - r, wx + r, wy + r], outline=col, width=w)
            draw.ellipse([wx - 3, wy - 3, wx + 3, wy + 3], fill=col)

    # Effector crosshairs
    for pt, col, tag in ((solved_right_wrist, (239, 68, 68), "R_HAND"), (solved_left_wrist, (59, 130, 246), "L_HAND")):
        ex, ey = pt
        draw.ellipse([ex - 9, ey - 9, ex + 9, ey + 9], outline=col, width=3)
        draw.line([(ex - 14, ey), (ex + 14, ey)], fill=col, width=2)
        draw.line([(ex, ey - 14), (ex, ey + 14)], fill=col, width=2)
        draw.text((ex - 28, ey - 30), tag, fill=col, font=small_font)

    # Telemetry HUD panel at bottom of frame
    hud_x1, hud_y1, hud_x2, hud_y2 = 48, 1560, 1032, 1850
    draw.rounded_rectangle([hud_x1, hud_y1, hud_x2, hud_y2], radius=16, fill=(15, 23, 42), outline=(0, 180, 216), width=4)
    step_str = (
        f"ACTIVE STEP: {active_step.step_id} -> {active_step.object_id}.{active_step.target_id} ({active_step.action.value})"
        if active_step
        else "ACTIVE STEP: IDLE / LOCOMOTION"
    )
    if hud_override is not None:
        calc_expr = hud_override.get("expression_text", "")
        calc_res = hud_override.get("result_text", "")
        total_contacts = hud_override.get("contacts_so_far", 0)
        last_ev = hud_override.get("last_contact_event")
    else:
        calc_obj = engine.objects.get("pedestal_calculator")
        calc_expr = calc_obj.state.get("expression_text", "") if calc_obj else ""
        calc_res = calc_obj.state.get("result_text", "") if calc_obj else ""
        total_contacts = len(engine.contact_events)
        last_ev = engine.contact_events[-1] if engine.contact_events else None

    ev_str = (
        f"LAST CONTACT EVENT: [{last_ev.timestamp_sec:.2f}s / f{last_ev.frame_idx}] {last_ev.target_id} "
        f"(dist={last_ev.contact_distance_px:.1f}px) -> {last_ev.state_change_summary}"
        if last_ev
        else "LAST CONTACT EVENT: None yet"
    )

    draw.text((hud_x1 + 24, hud_y1 + 20), f"INTERACTION ENGINE DEBUG HUD | Frame {frame_idx:03d} ({t_sec:05.2f}s)", fill=(56, 189, 248), font=dbg_font)
    draw.text((hud_x1 + 24, hud_y1 + 60), step_str, fill=(248, 250, 252), font=dbg_font)
    draw.text((hud_x1 + 24, hud_y1 + 100), f"CALCULATOR STATE: expr='{calc_expr}' | result='{calc_res}' | total_contacts={total_contacts}", fill=(167, 243, 208), font=dbg_font)
    draw.text((hud_x1 + 24, hud_y1 + 140), ev_str, fill=(253, 230, 138), font=small_font)
