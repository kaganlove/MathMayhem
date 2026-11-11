"""Shared world coordinate Scene Graph and 2D Camera system for cinematography.

Supports wide, medium, close-up, reaction shots, push-in, and camera shake in Cairo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional, Tuple

import cairo


class ShotType(str, Enum):
    WIDE = "wide"                 # Full stage view (default 1080x1920)
    MEDIUM = "medium"             # Character + pedestal
    CLOSEUP_CALC = "closeup_calc" # Close-up of keypad and display
    REACTION = "reaction"         # Character bust shot (waist up, glasses/eyes)
    CUSTOM = "custom"


@dataclass
class CameraShot:
    shot_type: ShotType = ShotType.WIDE
    center_x: float = 540.0
    center_y: float = 1200.0
    zoom: float = 1.0
    rotation_deg: float = 0.0
    shake_intensity: float = 0.0  # Pixels of screen shake


class Camera:
    """Manages viewport framing, zooms, cuts, and screen shake."""

    def __init__(self, viewport_width: int = 1080, viewport_height: int = 1920) -> None:
        self.vw = viewport_width
        self.vh = viewport_height

    def get_shot_preset(self, shot_type: ShotType) -> CameraShot:
        if shot_type == ShotType.WIDE:
            return CameraShot(ShotType.WIDE, 540.0, 960.0, 1.0)
        elif shot_type == ShotType.MEDIUM:
            return CameraShot(ShotType.MEDIUM, 560.0, 1250.0, 1.25)
        elif shot_type == ShotType.CLOSEUP_CALC:
            return CameraShot(ShotType.CLOSEUP_CALC, 700.0, 930.0, 2.05)
        elif shot_type == ShotType.REACTION:
            return CameraShot(ShotType.REACTION, 412.0, 850.0, 2.10)
        return CameraShot(ShotType.WIDE, 540.0, 960.0, 1.0)

    def apply_transform(self, ctx: cairo.Context, shot: CameraShot, t: float = 0.0) -> None:
        """Apply camera matrix to Cairo context."""
        # Calculate screen shake
        shake_x, shake_y = 0.0, 0.0
        if shot.shake_intensity > 0.0:
            shake_x = math.sin(t * 37.0) * shot.shake_intensity
            shake_y = math.cos(t * 43.0) * shot.shake_intensity

        ctx.translate(self.vw * 0.5 + shake_x, self.vh * 0.5 + shake_y)
        ctx.scale(shot.zoom, shot.zoom)
        if shot.rotation_deg != 0.0:
            ctx.rotate(math.radians(shot.rotation_deg))
        ctx.translate(-shot.center_x, -shot.center_y)


class Scene:
    """World-space scene graph holding background, props, character, and visual effects."""

    def __init__(self, width: int = 1080, height: int = 1920) -> None:
        self.width = width
        self.height = height
        self.camera = Camera(width, height)
        self.render_layers: List[Tuple[int, Callable[[cairo.Context, float], None]]] = []

    def add_layer(self, z_order: int, draw_fn: Callable[[cairo.Context, float], None]) -> None:
        """Add a drawable layer to the scene at z_order."""
        self.render_layers.append((z_order, draw_fn))
        self.render_layers.sort(key=lambda item: item[0])

    def render(self, ctx: cairo.Context, shot: CameraShot, t: float) -> None:
        """Render all layers in z-order transformed through the camera."""
        ctx.save()
        self.camera.apply_transform(ctx, shot, t)
        for _, draw_fn in self.render_layers:
            ctx.save()
            draw_fn(ctx, t)
            ctx.restore()
        ctx.restore()
