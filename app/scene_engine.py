"""Math Mayhem — Declarative Scene & Episode Engine.

Implements Workstream 6 of the Master Production Specification:
1. Separation of narrative/scene content from low-level Cairo rendering code.
2. Structured schemas for backgrounds, props, math typography, character actions, and sound cues.
3. Declarative scene compiler that transforms high-level actions into Cairo keyframes without manual loop math.
4. Deterministic rendering with SymPy mathematical verification and RTX 5080 NVENC composition.
"""

from __future__ import annotations

import math
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import cairo
from PIL import Image

from app.animation_library import (
    CANONICAL_POSES,
    AnimationLibrary,
    EasingType,
    EmotionalState,
    PoseTemplate,
    apply_easing,
)
from app.cairo_character_rig import (
    CairoRigState,
    OptionCCharacterSpec,
    SolvedCairoAnatomy,
    draw_option_c_character,
    solve_cairo_anatomy,
)
from app.math_verifier import MathStatementCheck, verify_math_statement


# ---------------------------------------------------------------------------
# Declarative Data Schemas
# ---------------------------------------------------------------------------

class BackgroundType(str, Enum):
    """Supported background environments."""
    WHITE_MINIMALIST = "white_minimalist"
    CHALKBOARD = "chalkboard"
    BLUEPRINT_GRID = "blueprint_grid"
    DARK_VOID = "dark_void"


@dataclass
class BackgroundSpec:
    """Environment staging parameters."""
    bg_type: BackgroundType = BackgroundType.WHITE_MINIMALIST
    floor_y: float = 1520.0
    primary_color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    floor_line_color: Tuple[float, float, float] = (0.88, 0.90, 0.94)
    has_ground_shadow: bool = True


@dataclass
class CameraSpec:
    """Virtual 2D camera framing parameters."""
    center_x: float = 540.0
    center_y: float = 960.0
    zoom: float = 1.0
    shake_intensity: float = 0.0


@dataclass
class MathTextElement:
    """Declarative mathematical notation element."""
    expression_text: str
    position: Tuple[float, float]
    font_size: float = 48.0
    color: Tuple[float, float, float] = (0.08, 0.10, 0.15)
    is_bold: bool = True
    must_verify: bool = True
    expected_result: Optional[str] = None


class ActionType(str, Enum):
    """High-level character action primitives."""
    IDLE = "idle"
    WALK_TO = "walk_to"
    POSE = "pose"
    REACH_AND_TOUCH = "reach_and_touch"
    LOOK_AT = "look_at"
    ADJUST_GLASSES = "adjust_glasses"
    EMOTE = "emote"


@dataclass
class CharacterAction:
    """Declarative character action instruction."""
    action_type: ActionType
    start_sec: float
    duration_sec: float
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SoundCueSpec:
    """Frame-accurate sound effect cue."""
    sfx_name: str
    timestamp_sec: float
    gain: float = 0.85
    target_id: str = "environment"


@dataclass
class SceneDefinition:
    """Structured, declarative scene specification."""
    scene_id: str
    title: str
    duration_seconds: float
    background: BackgroundSpec = field(default_factory=BackgroundSpec)
    camera: CameraSpec = field(default_factory=CameraSpec)
    math_elements: List[MathTextElement] = field(default_factory=list)
    actions: List[CharacterAction] = field(default_factory=list)
    sound_cues: List[SoundCueSpec] = field(default_factory=list)


@dataclass
class EpisodeDefinition:
    """Complete declarative episode specification."""
    episode_code: str
    title: str
    educational_topic: str
    scenes: List[SceneDefinition]
    resolution: Tuple[int, int] = (1080, 1920)
    fps: int = 30
    audio_theme: str = "option_a_orchestral_cartoon"


# ---------------------------------------------------------------------------
# Declarative Scene Compiler
# ---------------------------------------------------------------------------

class DeclarativeSceneCompiler:
    """Compiles declarative SceneDefinitions into frame-by-frame Cairo state timelines."""

    def __init__(self, spec: Optional[OptionCCharacterSpec] = None):
        self.spec = spec or OptionCCharacterSpec()
        self.anim_lib = AnimationLibrary(self.spec)

    def verify_scene_mathematics(self, scene: SceneDefinition) -> List[MathStatementCheck]:
        """Verify all mathematical expressions within the scene using SymPy."""
        results: List[MathStatementCheck] = []
        for elem in scene.math_elements:
            if not elem.must_verify:
                continue
            expr = elem.expression_text
            res = verify_math_statement(expr, elem.expected_result or "")
            results.append(res)
        return results

    def compile_character_states(
        self,
        scene: SceneDefinition,
        fps: int = 30,
        initial_pelvis_x: float = 412.0,
        scale: float = 1.22,
    ) -> List[Optional[CairoRigState]]:
        """Compile high-level actions into frame-indexed CairoRigStates."""
        total_frames = int(round(scene.duration_seconds * fps))
        states: List[Optional[CairoRigState]] = [None] * total_frames
        floor_y = scene.background.floor_y

        # Base resting idle state
        current_pose = self.anim_lib.get_pose_template("standing_idle")
        current_state = self.anim_lib.build_rig_state_from_pose(
            current_pose,
            pelvis_x=initial_pelvis_x,
            floor_y=floor_y,
            scale=scale,
        )

        # Sort actions chronologically
        sorted_actions = sorted(scene.actions, key=lambda a: a.start_sec)

        for act in sorted_actions:
            start_f = max(0, int(round(act.start_sec * fps)))
            dur_f = max(1, int(round(act.duration_sec * fps)))
            end_f = min(total_frames, start_f + dur_f)
            params = act.parameters

            if act.action_type == ActionType.WALK_TO:
                target_x = float(params.get("target_x", current_state.pelvis_x))
                facing = int(params.get("facing", 1 if target_x >= current_state.pelvis_x else -1))
                step_len = float(params.get("step_length", 65.0))
                walk_states = self.anim_lib.generate_walk_cycle(
                    start_x=current_state.pelvis_x,
                    end_x=target_x,
                    total_frames=dur_f,
                    floor_y=floor_y,
                    scale=scale,
                    facing=facing,
                    step_length=step_len,
                )
                for i in range(len(walk_states)):
                    idx = start_f + i
                    if idx < total_frames:
                        states[idx] = walk_states[i]
                if walk_states:
                    current_state = walk_states[-1]

            elif act.action_type == ActionType.POSE:
                pose_name = str(params.get("pose_name", "standing_idle"))
                target_pose = self.anim_lib.get_pose_template(pose_name)
                target_state = self.anim_lib.build_rig_state_from_pose(
                    target_pose,
                    pelvis_x=current_state.pelvis_x,
                    floor_y=floor_y,
                    scale=scale,
                    facing=current_state.facing,
                    left_ankle_pos=current_state.left_ankle_pos,
                    right_ankle_pos=current_state.right_ankle_pos,
                )
                # Blend into pose over first 6 frames
                blend_f = min(dur_f, int(params.get("blend_frames", 6)))
                for f_idx in range(start_f, end_f):
                    rel = f_idx - start_f
                    if rel < blend_f:
                        p = rel / float(max(1, blend_f))
                        states[f_idx] = self.anim_lib.blend_states(current_state, target_state, p)
                    else:
                        states[f_idx] = target_state
                current_state = target_state

            elif act.action_type == ActionType.REACH_AND_TOUCH:
                target_pos = (float(params["target_x"]), float(params["target_y"]))
                hold_f = int(params.get("hold_frames", 4))
                max_lean = float(params.get("max_lean_deg", 21.0))
                reach_states = self.anim_lib.generate_coordinated_reach(
                    base_state=current_state,
                    target_pos=target_pos,
                    total_frames=dur_f,
                    hold_frames=hold_f,
                    max_reach_lean_deg=max_lean,
                )
                for i in range(len(reach_states)):
                    idx = start_f + i
                    if idx < total_frames:
                        states[idx] = reach_states[i]
                if reach_states:
                    current_state = reach_states[-1]

            elif act.action_type == ActionType.IDLE:
                # Hold current state
                for idx in range(start_f, end_f):
                    states[idx] = current_state

        # Forward-fill any empty gaps with last active state
        last_valid = current_state
        for i in range(total_frames):
            if states[i] is None:
                states[i] = last_valid
            else:
                last_valid = states[i]

        return states


# ---------------------------------------------------------------------------
# Declarative Scene Frame Renderer
# ---------------------------------------------------------------------------

def draw_background(ctx: cairo.Context, width: int, height: int, spec: BackgroundSpec) -> None:
    """Render background environment and floor surface."""
    if spec.bg_type == BackgroundType.CHALKBOARD:
        # Deep slate-green chalkboard
        ctx.set_source_rgb(0.12, 0.18, 0.16)
        ctx.paint()

        # Wooden frame border
        border_w = 42.0
        ctx.set_source_rgb(0.48, 0.32, 0.18)
        ctx.set_line_width(border_w)
        ctx.rectangle(border_w / 2.0, border_w / 2.0, width - border_w, height - border_w)
        ctx.stroke()

        # Chalk dust tray / floor
        ctx.set_source_rgb(0.38, 0.25, 0.14)
        ctx.rectangle(0, spec.floor_y, width, height - spec.floor_y)
        ctx.fill()

        # Chalk dust accents
        ctx.set_source_rgba(0.92, 0.95, 0.98, 0.08)
        ctx.rectangle(border_w, border_w, width - border_w * 2, spec.floor_y - border_w)
        ctx.fill()

    elif spec.bg_type == BackgroundType.WHITE_MINIMALIST:
        # Crisp white studio environment
        ctx.set_source_rgb(spec.primary_color[0], spec.primary_color[1], spec.primary_color[2])
        ctx.paint()

        # Subtle floor horizon line
        ctx.set_source_rgb(spec.floor_line_color[0], spec.floor_line_color[1], spec.floor_line_color[2])
        ctx.set_line_width(2.0)
        ctx.move_to(0, spec.floor_y)
        ctx.line_to(width, spec.floor_y)
        ctx.stroke()

    elif spec.bg_type == BackgroundType.BLUEPRINT_GRID:
        # Technical blueprint blue with fine grid
        ctx.set_source_rgb(0.08, 0.18, 0.36)
        ctx.paint()
        ctx.set_source_rgba(0.20, 0.40, 0.65, 0.4)
        ctx.set_line_width(1.0)
        step = 60
        for x in range(0, width, step):
            ctx.move_to(x, 0)
            ctx.line_to(x, height)
        for y in range(0, height, step):
            ctx.move_to(0, y)
            ctx.line_to(width, y)
        ctx.stroke()


def draw_math_elements(ctx: cairo.Context, elements: List[MathTextElement], bg_type: BackgroundType) -> None:
    """Render high-legibility mathematical notation on the scene."""
    for elem in elements:
        ctx.save()
        x, y = elem.position

        # Font setup
        weight = cairo.FONT_WEIGHT_BOLD if elem.is_bold else cairo.FONT_WEIGHT_NORMAL
        ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, weight)
        ctx.set_font_size(elem.font_size)

        # Drop shadow for chalkboard chalk aesthetic
        if bg_type == BackgroundType.CHALKBOARD:
            # Chalk texture shadow
            ctx.set_source_rgba(0.0, 0.0, 0.0, 0.4)
            ctx.move_to(x + 2.0, y + 2.0)
            ctx.show_text(elem.expression_text)
            # Chalk white/yellow text
            ctx.set_source_rgb(0.96, 0.98, 0.92)
            ctx.move_to(x, y)
            ctx.show_text(elem.expression_text)
        else:
            # Clean dark text
            ctx.set_source_rgb(elem.color[0], elem.color[1], elem.color[2])
            ctx.move_to(x, y)
            ctx.show_text(elem.expression_text)

        ctx.restore()


def render_scene_frame(
    scene: SceneDefinition,
    char_state: Optional[CairoRigState],
    spec: OptionCCharacterSpec,
    width: int = 1080,
    height: int = 1920,
) -> Image.Image:
    """Render a single declarative scene frame to a PIL Image."""
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    # 1. Background
    draw_background(ctx, width, height, scene.background)

    # 2. Math Elements
    draw_math_elements(ctx, scene.math_elements, scene.background.bg_type)

    # 3. Character (if present)
    if char_state is not None:
        draw_option_c_character(ctx, spec, char_state)

    surface.flush()
    # Convert ARGB Cairo surface to PIL RGB
    data = bytes(surface.get_data())
    img = Image.frombuffer("RGBA", (width, height), data, "raw", "BGRA", 0, 1)
    return img.convert("RGB")
