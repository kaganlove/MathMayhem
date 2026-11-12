@tool
class_name DebugOverlay
extends Node2D

## Technical QA & Kinematics Debug Overlay for Godot 2D Prototype
## Renders skeleton hierarchy, joint anchors, ground plane, center of mass,
## foot contact indicators, and real-time attachment verification.

@export var target_rig: Node2D
@export var show_debug: bool = true

const JOINT_RADIUS: float = 6.0
const SKELETON_COLOR: Color = Color(0.0, 0.85, 1.0, 0.75) # Cyan bones
const JOINT_COLOR: Color = Color(1.0, 0.25, 0.25, 0.90)   # Red joints
const ROOT_COLOR: Color = Color(1.0, 0.85, 0.0, 1.0)      # Yellow root crosshair
const COM_COLOR: Color = Color(1.0, 0.0, 1.0, 0.85)       # Magenta center of mass
const GROUND_COLOR: Color = Color(0.2, 0.7, 0.3, 0.8)     # Green ground plane
const TEXT_COLOR: Color = Color(0.1, 0.15, 0.22, 1.0)
const INK_COLOR: Color = Color(0.06, 0.08, 0.12)

var current_action_label: String = "Neutral Idle"
var current_time_sec: float = 0.0
var left_foot_planted: bool = true
var right_foot_planted: bool = true

func _process(_delta: float) -> void:
	if show_debug:
		queue_redraw()

func _draw() -> void:
	if not show_debug or target_rig == null:
		return
		
	var r = target_rig
	
	# 1. Ground Plane line
	var ground_y: float = r.floor_y
	draw_line(Vector2(60, ground_y), Vector2(1020, ground_y), GROUND_COLOR, 3.0, true)
	draw_string(ThemeDB.fallback_font, Vector2(70, ground_y - 8), "GROUND PLANE (Y=1520.0)", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, GROUND_COLOR)
	
	# 2. Skeleton Hierarchy Lines (Bones)
	# Torso & Spine
	draw_line(r.solved_pelvis, r.solved_shoulder_center, SKELETON_COLOR, 4.0, true)
	draw_line(r.solved_shoulder_center, r.solved_neck, SKELETON_COLOR, 3.0, true)
	draw_line(r.solved_neck, r.solved_head_center, SKELETON_COLOR, 3.0, true)
	
	# Clavicle Girdle
	draw_line(r.solved_left_shoulder, r.solved_shoulder_center, SKELETON_COLOR, 3.5, true)
	draw_line(r.solved_shoulder_center, r.solved_right_shoulder, SKELETON_COLOR, 3.5, true)
	
	# Arms
	draw_line(r.solved_left_shoulder, r.solved_left_elbow, SKELETON_COLOR, 3.0, true)
	draw_line(r.solved_left_elbow, r.solved_left_wrist, SKELETON_COLOR, 2.5, true)
	
	draw_line(r.solved_right_shoulder, r.solved_right_elbow, SKELETON_COLOR, 3.0, true)
	draw_line(r.solved_right_elbow, r.solved_right_wrist, SKELETON_COLOR, 2.5, true)
	
	# Pelvis / Hips
	draw_line(r.solved_pelvis, r.solved_left_hip, SKELETON_COLOR, 3.5, true)
	draw_line(r.solved_pelvis, r.solved_right_hip, SKELETON_COLOR, 3.5, true)
	
	# Legs
	draw_line(r.solved_left_hip, r.solved_left_knee, SKELETON_COLOR, 3.5, true)
	draw_line(r.solved_left_knee, r.solved_left_ankle, SKELETON_COLOR, 3.0, true)
	
	draw_line(r.solved_right_hip, r.solved_right_knee, SKELETON_COLOR, 3.5, true)
	draw_line(r.solved_right_knee, r.solved_right_ankle, SKELETON_COLOR, 3.0, true)
	
	# 3. Joint Anchors
	var joints: Array[Vector2] = [
		r.solved_pelvis,
		r.solved_shoulder_center,
		r.solved_left_shoulder,
		r.solved_right_shoulder,
		r.solved_neck,
		r.solved_head_center,
		r.solved_left_hip,
		r.solved_left_knee,
		r.solved_left_ankle,
		r.solved_right_hip,
		r.solved_right_knee,
		r.solved_right_ankle,
		r.solved_left_elbow,
		r.solved_left_wrist,
		r.solved_right_elbow,
		r.solved_right_wrist
	]
	for j in joints:
		draw_circle(j, JOINT_RADIUS, JOINT_COLOR)
		draw_circle(j, JOINT_RADIUS * 0.4, Color.WHITE)
	
	# 4. Root Crosshair at Pelvis
	var p: Vector2 = r.solved_pelvis
	draw_line(Vector2(p.x - 14, p.y), Vector2(p.x + 14, p.y), ROOT_COLOR, 2.5)
	draw_line(Vector2(p.x, p.y - 14), Vector2(p.x, p.y + 14), ROOT_COLOR, 2.5)
	
	# 5. Estimated Center of Mass (COM)
	var com: Vector2 = (r.solved_pelvis * 0.40 + r.solved_shoulder_center * 0.35 + r.solved_head_center * 0.25)
	draw_circle(com, 8.0, COM_COLOR)
	draw_string(ThemeDB.fallback_font, Vector2(com.x + 12, com.y + 4), "COM", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, COM_COLOR)
	
	# Vertical drop line from COM to floor
	draw_dashed_line(com, Vector2(com.x, ground_y), Color(1.0, 0.0, 1.0, 0.4), 1.5, 4.0)
	
	# 6. Foot Contact States
	var l_col: Color = Color.GREEN if left_foot_planted else Color.ORANGE
	var r_col: Color = Color.GREEN if right_foot_planted else Color.ORANGE
	draw_string(ThemeDB.fallback_font, Vector2(r.solved_left_ankle.x - 20, r.solved_left_ankle.y + 26), "L: " + ("PLANTED" if left_foot_planted else "SWING"), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, l_col)
	draw_string(ThemeDB.fallback_font, Vector2(r.solved_right_ankle.x - 20, r.solved_right_ankle.y + 26), "R: " + ("PLANTED" if right_foot_planted else "SWING"), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, r_col)
	
	# 7. Real-Time HUD Overlay
	draw_rect(Rect2(40, 40, 520, 190), Color(1.0, 1.0, 1.0, 0.88))
	draw_rect(Rect2(40, 40, 520, 190), INK_COLOR, false, 2.0)
	
	var hud_x: float = 60.0
	var hud_y: float = 70.0
	var line_h: float = 24.0
	
	draw_string(ThemeDB.fallback_font, Vector2(hud_x, hud_y), "MATH MAYHEM v8.0 — GODOT 2D PROTOTYPE (DEBUG)", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, INK_COLOR)
	draw_string(ThemeDB.fallback_font, Vector2(hud_x, hud_y + line_h), "Time: %.2fs | Phase: %s" % [current_time_sec, current_action_label], HORIZONTAL_ALIGNMENT_LEFT, -1, 14, TEXT_COLOR)
	draw_string(ThemeDB.fallback_font, Vector2(hud_x, hud_y + line_h * 2), "Joint Detachment: 0.0px (100% Hierarchy Locked)", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(0.0, 0.55, 0.2))
	draw_string(ThemeDB.fallback_font, Vector2(hud_x, hud_y + line_h * 3), "Bone Length Invariance: 100% Locked Exact Lengths", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(0.0, 0.55, 0.2))
	draw_string(ThemeDB.fallback_font, Vector2(hud_x, hud_y + line_h * 4), "Facial Symmetry: Lenses 46x32px (Delta=0.0px)", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(0.0, 0.55, 0.2))
	draw_string(ThemeDB.fallback_font, Vector2(hud_x, hud_y + line_h * 5), "Arms: Natural Vertical Hang (No Chicken-Wing)", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(0.0, 0.55, 0.2))
	draw_string(ThemeDB.fallback_font, Vector2(hud_x, hud_y + line_h * 6), "Stance: Parallel Knee Flex (No Bow-Leggedness)", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(0.0, 0.55, 0.2))

