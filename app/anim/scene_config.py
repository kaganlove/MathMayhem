"""Unified Scene Configuration and Central Source of Truth for Math Mayhem.

Defines the physical, kinematic, and visual properties of the Character, Calculator,
and Environment in a single authoritative structure with coordinate transformations
and automated configuration validation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

Point = Tuple[float, float]
Box = Tuple[float, float, float, float]


@dataclass(frozen=True)
class CharacterConfig:
    """Authoritative physical dimensions and kinematic limits for the approved character."""
    scale: float = 1.22
    root_x: float = 430.0
    root_y: float = 1294.0
    floor_y: float = 1520.0

    # Anatomical segment lengths (canonical scale 1.0)
    head_radius: float = 78.0
    neck_length: float = 22.0
    torso_length: float = 158.0
    shoulder_half_width: float = 10.0
    hip_half_width: float = 13.0
    upper_arm_length: float = 144.0
    forearm_length: float = 140.0
    thigh_length: float = 92.0
    shin_length: float = 90.0
    ankle_height: float = 16.0
    boot_length: float = 44.0

    # Stroke widths
    spine_widths: Tuple[float, float, float] = (23.0, 18.5, 20.5)
    leg_widths: Tuple[float, float, float] = (17.0, 13.5, 11.0)
    arm_widths: Tuple[float, float, float] = (15.5, 12.2, 9.8)
    outline_width: float = 6.8

    # Kinematic joint limits (degrees)
    torso_lean_range: Tuple[float, float] = (-22.0, 22.0)
    spine_arch_range: Tuple[float, float] = (-18.0, 20.0)
    head_tilt_range: Tuple[float, float] = (-25.0, 25.0)
    max_shoulder_protract_px: float = 38.0

    @property
    def max_arm_reach(self) -> float:
        """Maximum physical reach of the 2-bone arm."""
        return (self.upper_arm_length + self.forearm_length) * self.scale


@dataclass(frozen=True)
class ButtonConfig:
    """Precise dimensions and hit region for an individual calculator button."""
    key_label: str
    target_id: str
    local_center: Point         # Center relative to calculator origin (top-left)
    width: float
    height: float
    hit_radius: float = 24.0
    depression_offset_px: float = 4.0


@dataclass
class CalculatorConfig:
    """Authoritative geometry and layout for the resized, naturally accessible calculator."""
    # Staging position in World Space
    # Resized to 220px wide by 390px tall, positioned so buttons sit comfortably
    # in front of character's chest/pelvis height (y=1000..1360).
    pos_x: float = 580.0
    pos_y: float = 960.0
    width: float = 220.0
    height: float = 390.0

    # Display dimensions (local to calculator origin)
    display_pad_x: float = 16.0
    display_pad_y: float = 18.0
    display_width: float = 188.0
    display_height: float = 100.0

    # Keypad grid specifications
    grid_pad_x: float = 16.0
    grid_gap_x: float = 7.0
    grid_gap_y: float = 7.0
    grid_top_offset: float = 135.0
    btn_width: float = 42.0
    btn_height: float = 42.0

    # Pedestal stand
    stand_width: float = 40.0
    foot_width: float = 160.0
    foot_height: float = 18.0

    buttons: Dict[str, ButtonConfig] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.buttons:
            self._build_buttons()

    def _build_buttons(self) -> None:
        keys = [
            ["7", "8", "9", "÷"],
            ["4", "5", "6", "×"],
            ["1", "2", "3", "−"],
            ["C", "0", "+", "="],
        ]
        btns: Dict[str, ButtonConfig] = {}
        for r_idx, row in enumerate(keys):
            for c_idx, label in enumerate(row):
                lx = self.grid_pad_x + c_idx * (self.btn_width + self.grid_gap_x) + self.btn_width * 0.5
                ly = self.grid_top_offset + r_idx * (self.btn_height + self.grid_gap_y) + self.btn_height * 0.5
                btns[label] = ButtonConfig(
                    key_label=label,
                    target_id=f"key_{label}",
                    local_center=(round(lx, 2), round(ly, 2)),
                    width=self.btn_width,
                    height=self.btn_height,
                    hit_radius=22.0,
                    depression_offset_px=4.0,
                )
        self.buttons = btns

    @property
    def bounding_box(self) -> Box:
        """World-space bounding box: (x1, y1, x2, y2)."""
        return (self.pos_x, self.pos_y, self.pos_x + self.width, self.pos_y + self.height)

    def get_button_world_pos(self, key_label: str) -> Point:
        """Convert button local center to authoritative world coordinates."""
        btn = self.buttons[key_label]
        return (self.pos_x + btn.local_center[0], self.pos_y + btn.local_center[1])


@dataclass(frozen=True)
class SceneConfig:
    """Centralized authoritative configuration for the complete Math Mayhem stage."""
    render_width: int = 1080
    render_height: int = 1920
    fps: int = 30
    floor_y: float = 1520.0
    character: CharacterConfig = field(default_factory=CharacterConfig)
    calculator: CalculatorConfig = field(default_factory=CalculatorConfig)

    def validate(self) -> None:
        """Run automated assertions ensuring physical reachability and dimensional consistency."""
        assert self.render_width > 0 and self.render_height > 0, "Invalid render dimensions"
        assert self.character.scale > 0, "Character scale must be positive"
        assert self.calculator.width > 0 and self.calculator.height > 0, "Invalid calculator size"

        # Reachability verification:
        # Check that all buttons can be reached from a character standing posture
        char_sh_x = self.character.root_x + self.character.shoulder_half_width * self.character.scale + 30.0
        char_sh_y = self.character.root_y - (self.character.torso_length * 0.85) * self.character.scale

        max_reach = self.character.max_arm_reach * 0.96  # Allow comfortable 4% elbow bend margin

        for key, btn in self.calculator.buttons.items():
            bx, by = self.calculator.get_button_world_pos(key)
            dist = math.hypot(bx - char_sh_x, by - char_sh_y)
            assert dist <= max_reach, (
                f"Button '{key}' at ({bx:.1f}, {by:.1f}) is unreachable from shoulder ({char_sh_x:.1f}, {char_sh_y:.1f}): "
                f"dist={dist:.1f}px > max_reach={max_reach:.1f}px"
            )


# Default global scene configuration instance
SCENE_CONFIG = SceneConfig()
SCENE_CONFIG.validate()
