@tool
class_name CharacterRig2D
extends Node2D

## Canonical Option C Character Rig for Godot 2D
## Implements the approved minimalist cartoon protagonist with thicker limbs,
## messy hair, blank rectangular glasses, short contoured beard, and seamless joint articulation.

# Canonical proportions (scale 1.0 base, scaled by character_scale)
@export var character_scale: float = 1.70
@export var facing: int = 1 # +1 = right, -1 = left
@export var floor_y: float = 1620.0

# Target Object for Reaching & Interaction Evaluation
@export var show_target_object: bool = false
@export var target_object_pos: Vector2 = Vector2(740.0, 1220.0)
@export var target_object_pulse: float = 0.0

# Base anatomical segment lengths (in local pixels at scale=1.0)
const HEAD_RADIUS: float = 78.0
const NECK_LENGTH: float = 22.0
const TORSO_LENGTH: float = 158.0
const HIP_HALF_WIDTH: float = 13.0
const SHOULDER_HALF_WIDTH: float = 10.0
const UPPER_ARM_LENGTH: float = 72.0
const FOREARM_LENGTH: float = 68.0
const THIGH_LENGTH: float = 92.0
const SHIN_LENGTH: float = 90.0
const BOOT_LENGTH: float = 44.0
const BOOT_HEIGHT: float = 16.0

# Stroke widths (start, mid, end)
const SPINE_WIDTHS: Vector3 = Vector3(23.0, 18.5, 20.5)
const LEG_WIDTHS: Vector3 = Vector3(17.0, 13.5, 11.0)
const ARM_WIDTHS: Vector3 = Vector3(15.5, 12.2, 9.8)
const OUTLINE_WIDTH: float = 6.8

# Canonical facial dimensions (scale 1.0) for 100% symmetry
const LENS_WIDTH: float = 46.0
const LENS_HEIGHT: float = 32.0
const LENS_CORNER_RADIUS: float = 5.5
const GLASSES_BRIDGE_GAP: float = 8.5
const BROW_LENGTH: float = 38.0
const BROW_ARCH: float = 4.5
const BROW_BASELINE_Y: float = 10.5

# Palette
const INK_COLOR: Color = Color(0.06, 0.08, 0.12)
const HEAD_FILL: Color = Color(1.0, 1.0, 1.0)
const HAIR_FILL: Color = Color(0.10, 0.12, 0.17)
const BEARD_FILL: Color = Color(0.15, 0.18, 0.24)
const BODY_FILL: Color = Color(0.07, 0.09, 0.14)
const SHADOW_COLOR: Color = Color(0.89, 0.91, 0.94)

# Rig Control Properties (Animateable in AnimationPlayer)
@export_group("Root & Torso")
@export var root_pos: Vector2 = Vector2(540.0, 1285.8)
@export var torso_lean_deg: float = 2.0
@export var spine_arch_deg: float = 4.5
@export var shoulder_shrug_px: float = 0.0
@export var right_shoulder_protract_px: float = 0.0
@export var torso_squash: float = 1.0

@export_group("Head & Face")
@export var head_tilt_deg: float = 1.5
@export var head_nod_px: float = 0.0
@export var head_squash: float = 1.0
@export var yaw_factor: float = 0.22
@export var glasses_slip_px: float = 0.0
@export var hair_lag_deg: float = 0.0
@export var left_brow_raise_px: float = 0.0
@export var right_brow_raise_px: float = 0.0
@export var brow_slant_deg: float = 0.0
@export_enum("neutral", "curious_o", "open_gasp", "smirk", "firm", "concentrating", "confused", "satisfied") var mouth_state: String = "neutral"

@export_group("Interactive Button Pedestal")
@export var show_button_pedestal: bool = false
@export var button_pedestal_pos: Vector2 = Vector2(760.0, 1220.0)
@export var button_depress_px: float = 0.0
@export var button_glow_alpha: float = 0.0

@export_group("Interactive Floor Item")
@export var show_floor_item: bool = false
@export var floor_item_pos: Vector2 = Vector2(700.0, 1600.0)
@export var is_item_held: bool = false

@export_group("Left Leg (Back)")
@export var left_thigh_deg: float = 14.0
@export var left_shin_deg: float = -28.0
@export var left_foot_deg: float = 14.0

@export_group("Right Leg (Front)")
@export var right_thigh_deg: float = 14.0
@export var right_shin_deg: float = -28.0
@export var right_foot_deg: float = 14.0

@export_group("Left Arm (Back)")
@export var left_shoulder_deg: float = 4.0
@export var left_elbow_deg: float = 12.0
@export var left_wrist_deg: float = 5.0
@export_enum("relaxed", "reach_open", "point", "fist", "chin_touch", "shrug_open") var left_hand_pose: String = "relaxed"

@export_group("Right Arm (Front)")
@export var right_shoulder_deg: float = 6.0
@export var right_elbow_deg: float = 12.0
@export var right_wrist_deg: float = 5.0
@export_enum("relaxed", "reach_open", "point", "fist", "chin_touch", "shrug_open") var right_hand_pose: String = "relaxed"

@export_group("Kinematic Constraints & Inverse Kinematics")
@export var left_foot_locked: bool = false
@export var left_foot_lock_pos: Vector2 = Vector2.ZERO
@export var right_foot_locked: bool = false
@export var right_foot_lock_pos: Vector2 = Vector2.ZERO

@export var right_arm_ik_enabled: bool = false
@export var right_arm_ik_target: Vector2 = Vector2.ZERO
@export var right_arm_ik_elbow_down: bool = true

@export var left_arm_ik_enabled: bool = false
@export var left_arm_ik_target: Vector2 = Vector2.ZERO
@export var left_arm_ik_elbow_down: bool = true

@export var gaze_target_enabled: bool = false
@export var gaze_target_pos: Vector2 = Vector2.ZERO
@export var hand_contact_constrained: bool = false

# Solved joint landmarks (in screen space) for debugging and verification
var solved_pelvis: Vector2
var solved_shoulder_center: Vector2
var solved_left_shoulder: Vector2
var solved_right_shoulder: Vector2
var solved_neck: Vector2
var solved_head_center: Vector2
var solved_left_hip: Vector2
var solved_left_knee: Vector2
var solved_left_ankle: Vector2
var solved_right_hip: Vector2
var solved_right_knee: Vector2
var solved_right_ankle: Vector2
var solved_left_elbow: Vector2
var solved_left_wrist: Vector2
var solved_right_elbow: Vector2
var solved_right_wrist: Vector2
var solved_right_fingertip: Vector2
var solved_left_fingertip: Vector2

func _ready() -> void:
	queue_redraw()

func _process(_delta: float) -> void:
	queue_redraw()

func get_button_contact_pos() -> Vector2:
	var s: float = character_scale
	var depress: float = clampf(button_depress_px, 0.0, 10.0) * s
	return Vector2(button_pedestal_pos.x, button_pedestal_pos.y - 6.0 * s + depress)

func get_right_fingertip_pos() -> Vector2:
	return solved_right_fingertip

func get_fingertip_contact_distance() -> float:
	return solved_right_fingertip.distance_to(get_button_contact_pos())

# ===========================================================================
# Analytical 2-Bone Inverse Kinematics Solver
# ===========================================================================
static func solve_ik_2bone(origin: Vector2, target: Vector2, l1: float, l2: float, bend_positive: bool = true) -> Dictionary:
	var delta: Vector2 = target - origin
	var dist: float = delta.length()
	var min_reach: float = absf(l1 - l2) + 0.001
	var max_reach: float = l1 + l2 - 0.001
	var d: float = clampf(dist, min_reach, max_reach)
	
	# Angle from +Y (vertical down) with safe singularity handling
	var theta: float = atan2(delta.x, delta.y) if dist > 0.0001 else 0.0
	
	var cos_alpha: float = clampf((l1 * l1 + d * d - l2 * l2) / (2.0 * l1 * d), -1.0, 1.0)
	var alpha: float = acos(cos_alpha)
	
	var cos_beta: float = clampf((l1 * l1 + l2 * l2 - d * d) / (2.0 * l1 * l2), -1.0, 1.0)
	var beta: float = acos(cos_beta)
	
	var joint1_rad: float
	var joint2_rel_rad: float
	
	if bend_positive:
		joint1_rad = theta + alpha
		joint2_rel_rad = -(PI - beta)
	else:
		joint1_rad = theta - alpha
		joint2_rel_rad = (PI - beta)
		
	var joint1_pos: Vector2 = origin + Vector2(l1 * sin(joint1_rad), l1 * cos(joint1_rad))
	var joint2_pos: Vector2 = joint1_pos + Vector2(l2 * sin(joint1_rad + joint2_rel_rad), l2 * cos(joint1_rad + joint2_rel_rad))
	
	return {
		"joint1_rad": joint1_rad,
		"joint2_rel_rad": joint2_rel_rad,
		"joint1_deg": rad_to_deg(joint1_rad),
		"joint2_deg": rad_to_deg(joint2_rel_rad),
		"joint1_pos": joint1_pos,
		"joint2_pos": joint2_pos,
		"is_reachable": (dist >= min_reach and dist <= max_reach),
		"distance": dist,
		"clamped_distance": d
	}

func solve_kinematics() -> void:
	var s: float = character_scale
	var d: float = float(facing)
	
	# Hips & Shoulders width foreshortened by yaw
	var width_scale: float = maxf(0.25, 1.0 - absf(yaw_factor) * 1.1)
	var hip_dx: float = HIP_HALF_WIDTH * s * width_scale * d
	var sh_dx: float = SHOULDER_HALF_WIDTH * s * width_scale * d
	
	solved_pelvis = root_pos
	
	# Spine Lean & Arch
	var lean_rad: float = deg_to_rad(torso_lean_deg * d)
	var sq: float = clampf(torso_squash, 0.5, 1.8)
	var spine_len: float = TORSO_LENGTH * s * sq
	
	solved_shoulder_center = solved_pelvis + Vector2(
		spine_len * sin(lean_rad),
		-spine_len * cos(lean_rad) - shoulder_shrug_px * s
	)
	
	# Clavicle axis perpendicular to spine lean
	var cos_lean: float = cos(lean_rad)
	var sin_lean: float = sin(lean_rad)
	var protract_dx: float = clampf(right_shoulder_protract_px * 0.20, -3.0, 6.0) * s * d
	
	solved_left_shoulder = solved_shoulder_center + Vector2(-sh_dx * cos_lean, -sh_dx * sin_lean)
	solved_right_shoulder = solved_shoulder_center + Vector2((sh_dx + protract_dx) * cos_lean, (sh_dx + protract_dx) * sin_lean)
	
	# Neck & Head
	var neck_rad: float = lean_rad + deg_to_rad(spine_arch_deg * 0.25 * d)
	solved_neck = solved_shoulder_center + Vector2(
		(NECK_LENGTH * s) * sin(neck_rad),
		-(NECK_LENGTH * s) * cos(neck_rad)
	)
	
	# Optional Gaze Target Solver
	if gaze_target_enabled and gaze_target_pos != Vector2.ZERO:
		var gaze_delta: Vector2 = gaze_target_pos - solved_neck
		var gaze_angle: float = atan2(gaze_delta.y, gaze_delta.x * d)
		head_tilt_deg = clampf(rad_to_deg(gaze_angle) * 0.35, -25.0, 25.0)
		yaw_factor = clampf(gaze_delta.x / 450.0 * d, -0.38, 0.38)

	var head_r: float = HEAD_RADIUS * s
	var head_rad: float = lean_rad + deg_to_rad(head_tilt_deg)
	solved_head_center = solved_neck + Vector2(
		(head_r * 0.94) * sin(head_rad),
		-(head_r * 0.94) * cos(head_rad)
	)
	
	# Legs Kinematics (FK or Planted-Foot IK)
	var thigh_l: float = THIGH_LENGTH * s
	var shin_l: float = SHIN_LENGTH * s
	
	solved_left_hip = solved_pelvis + Vector2(-hip_dx, 0.0)
	solved_right_hip = solved_pelvis + Vector2(hip_dx, 0.0)
	
	# Left Leg
	if left_foot_locked and left_foot_lock_pos != Vector2.ZERO:
		var ik_left = solve_ik_2bone(solved_left_hip, left_foot_lock_pos, thigh_l, shin_l, true)
		left_thigh_deg = ik_left["joint1_deg"] * d
		left_shin_deg = ik_left["joint2_deg"] * d
		solved_left_knee = ik_left["joint1_pos"]
		solved_left_ankle = ik_left["joint2_pos"]
	else:
		var l_thigh_rad: float = deg_to_rad(left_thigh_deg * d)
		solved_left_knee = solved_left_hip + Vector2(thigh_l * sin(l_thigh_rad), thigh_l * cos(l_thigh_rad))
		var l_shin_rad: float = l_thigh_rad + deg_to_rad(left_shin_deg * d)
		solved_left_ankle = solved_left_knee + Vector2(shin_l * sin(l_shin_rad), shin_l * cos(l_shin_rad))
	
	# Right Leg
	if right_foot_locked and right_foot_lock_pos != Vector2.ZERO:
		var ik_right = solve_ik_2bone(solved_right_hip, right_foot_lock_pos, thigh_l, shin_l, true)
		right_thigh_deg = ik_right["joint1_deg"] * d
		right_shin_deg = ik_right["joint2_deg"] * d
		solved_right_knee = ik_right["joint1_pos"]
		solved_right_ankle = ik_right["joint2_pos"]
	else:
		var r_thigh_rad: float = deg_to_rad(right_thigh_deg * d)
		solved_right_knee = solved_right_hip + Vector2(thigh_l * sin(r_thigh_rad), thigh_l * cos(r_thigh_rad))
		var r_shin_rad: float = r_thigh_rad + deg_to_rad(right_shin_deg * d)
		solved_right_ankle = solved_right_knee + Vector2(shin_l * sin(r_shin_rad), shin_l * cos(r_shin_rad))
	
	# Arms Kinematics (FK or Target Reaching IK)
	var u_arm: float = UPPER_ARM_LENGTH * s
	var f_arm: float = FOREARM_LENGTH * s
	var r_hand_len: float = (17.5 if (right_hand_pose == "press" or right_hand_pose == "point") else 14.5) * s
	var l_hand_len: float = 14.5 * s
	
	# Left Arm (Back)
	if left_arm_ik_enabled and left_arm_ik_target != Vector2.ZERO:
		var l_delta: Vector2 = left_arm_ik_target - solved_left_shoulder
		var l_dist: float = l_delta.length()
		var l_reach_dir: Vector2 = (l_delta / l_dist) if l_dist > 0.001 else Vector2(0.0, 1.0)
		var l_wrist_target: Vector2 = left_arm_ik_target - l_reach_dir * l_hand_len
		var ik_l_arm = solve_ik_2bone(solved_left_shoulder, l_wrist_target, u_arm, f_arm, not left_arm_ik_elbow_down)
		left_shoulder_deg = ik_l_arm["joint1_deg"] * d
		left_elbow_deg = ik_l_arm["joint2_deg"] * d
		solved_left_elbow = ik_l_arm["joint1_pos"]
		solved_left_wrist = ik_l_arm["joint2_pos"]
		solved_left_fingertip = solved_left_wrist + l_reach_dir * l_hand_len
	else:
		var l_sh_rad: float = deg_to_rad(left_shoulder_deg * d)
		solved_left_elbow = solved_left_shoulder + Vector2(u_arm * sin(l_sh_rad), u_arm * cos(l_sh_rad))
		var l_el_rad: float = l_sh_rad + deg_to_rad(left_elbow_deg * d)
		solved_left_wrist = solved_left_elbow + Vector2(f_arm * sin(l_el_rad), f_arm * cos(l_el_rad))
		var l_hand_rad: float = deg_to_rad(left_shoulder_deg + left_elbow_deg + left_wrist_deg)
		solved_left_fingertip = solved_left_wrist + Vector2(l_hand_len * cos(l_hand_rad), l_hand_len * sin(l_hand_rad))
	
	# Hand Contact Coupling
	if hand_contact_constrained and show_button_pedestal:
		right_arm_ik_enabled = true
		right_arm_ik_target = get_button_contact_pos()
		right_hand_pose = "press"

	# Right Arm (Front)
	if right_arm_ik_enabled and right_arm_ik_target != Vector2.ZERO:
		var r_delta: Vector2 = right_arm_ik_target - solved_right_shoulder
		var r_dist: float = r_delta.length()
		var r_reach_dir: Vector2 = (r_delta / r_dist) if r_dist > 0.001 else Vector2(0.0, 1.0)
		var r_wrist_target: Vector2 = right_arm_ik_target - r_reach_dir * r_hand_len
		var ik_r_arm = solve_ik_2bone(solved_right_shoulder, r_wrist_target, u_arm, f_arm, not right_arm_ik_elbow_down)
		right_shoulder_deg = ik_r_arm["joint1_deg"] * d
		right_elbow_deg = ik_r_arm["joint2_deg"] * d
		solved_right_elbow = ik_r_arm["joint1_pos"]
		solved_right_wrist = ik_r_arm["joint2_pos"]
		solved_right_fingertip = solved_right_wrist + r_reach_dir * r_hand_len
	else:
		var r_sh_rad: float = deg_to_rad(right_shoulder_deg * d)
		solved_right_elbow = solved_right_shoulder + Vector2(u_arm * sin(r_sh_rad), u_arm * cos(r_sh_rad))
		var r_el_rad: float = r_sh_rad + deg_to_rad(right_elbow_deg * d)
		solved_right_wrist = solved_right_elbow + Vector2(f_arm * sin(r_el_rad), f_arm * cos(r_el_rad))
		var r_hand_rad: float = deg_to_rad(right_shoulder_deg + right_elbow_deg + right_wrist_deg)
		solved_right_fingertip = solved_right_wrist + Vector2(r_hand_len * cos(r_hand_rad), r_hand_len * sin(r_hand_rad))

func _draw() -> void:
	solve_kinematics()
	var s: float = character_scale
	var d: float = float(facing)
	
	var leg_w: Vector3 = LEG_WIDTHS * s
	var arm_w: Vector3 = ARM_WIDTHS * s
	var spine_w: Vector3 = SPINE_WIDTHS * s
	var outline_w: float = OUTLINE_WIDTH * s
	
	# 1. Ground Shadow
	var shadow_cx: float = 0.4 * solved_left_ankle.x + 0.4 * solved_right_ankle.x + 0.2 * solved_pelvis.x
	draw_set_transform(Vector2(shadow_cx, floor_y + 3.0 * s), 0.0, Vector2(96.0 * s, 13.0 * s))
	draw_circle(Vector2.ZERO, 1.0, SHADOW_COLOR)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	
	# 2. Back Leg & Boot
	_draw_articulated_limb(solved_left_hip, solved_left_knee, solved_left_ankle, leg_w.x, leg_w.y, leg_w.z, BODY_FILL)
	_draw_boot(solved_left_ankle, left_foot_deg, BOOT_LENGTH * s, BOOT_HEIGHT * s, d)
	
	# 3. Back Arm & Hand
	_draw_articulated_limb(solved_left_shoulder, solved_left_elbow, solved_left_wrist, arm_w.x, arm_w.y, arm_w.z, BODY_FILL)
	_draw_hand(solved_left_wrist, left_shoulder_deg + left_elbow_deg + left_wrist_deg, left_hand_pose, s, arm_w.z)
	
	# 4. Torso & Clavicle Girdle
	# Tapered spine curve
	var mid_spine: Vector2 = (solved_pelvis + solved_shoulder_center) * 0.5 + Vector2(
		(TORSO_LENGTH * s * 0.12 * sin(deg_to_rad(spine_arch_deg * d))) * cos(deg_to_rad(torso_lean_deg * d)),
		(TORSO_LENGTH * s * 0.12 * sin(deg_to_rad(spine_arch_deg * d))) * sin(deg_to_rad(torso_lean_deg * d))
	)
	_draw_tapered_limb(solved_shoulder_center, mid_spine, solved_pelvis, spine_w.x, spine_w.y, spine_w.z, BODY_FILL)
	# Neck
	_draw_tapered_limb(solved_shoulder_center, (solved_shoulder_center + solved_neck) * 0.5, solved_neck, leg_w.y, leg_w.y, leg_w.z, BODY_FILL)
	# Solid Clavicle Girdle locking left & right shoulders firmly to torso
	_draw_articulated_limb(solved_left_shoulder, solved_shoulder_center, solved_right_shoulder, arm_w.x, spine_w.x * 0.88, arm_w.x, BODY_FILL)
	
	# 5. Front Leg & Boot
	_draw_articulated_limb(solved_right_hip, solved_right_knee, solved_right_ankle, leg_w.x, leg_w.y, leg_w.z, BODY_FILL)
	_draw_boot(solved_right_ankle, right_foot_deg, BOOT_LENGTH * s, BOOT_HEIGHT * s, d)
	
	# 6. Head, Beard, Hair, Blank Rectangular Glasses & Eyebrows
	_draw_head_and_face(s, d, outline_w)
	
	# 7. Front Arm & Hand (rendered in foreground with clavicle socket bridge)
	# Foreground clavicle bridge locks right shoulder firmly to chest
	_draw_articulated_limb(solved_shoulder_center, (solved_shoulder_center + solved_right_shoulder) * 0.5, solved_right_shoulder, spine_w.x * 0.85, arm_w.x * 1.15, arm_w.x, BODY_FILL)
	_draw_articulated_limb(solved_right_shoulder, solved_right_elbow, solved_right_wrist, arm_w.x, arm_w.y, arm_w.z, BODY_FILL)
	_draw_hand(solved_right_wrist, right_shoulder_deg + right_elbow_deg + right_wrist_deg, right_hand_pose, s, arm_w.z)

	# 8. Interactive Target Object (Simple minimalist pedestal stand & glowing orb)
	if show_target_object:
		_draw_interactive_target(s)

	# 9. The Mysterious Button on Pedestal (v11)
	if show_button_pedestal:
		_draw_button_pedestal(s)

	# 10. Interactive Floor Item (Test B: Math Gadget / Prism)
	if show_floor_item:
		_draw_floor_item(s)

func _draw_floor_item(s: float) -> void:
	var item_pos: Vector2 = solved_right_fingertip if is_item_held else floor_item_pos
	# Draw glowing golden prism / octahedron
	var sz: float = 16.0 * s
	var pts: PackedVector2Array = [
		item_pos + Vector2(0.0, -sz),
		item_pos + Vector2(sz * 0.8, -sz * 0.2),
		item_pos + Vector2(0.0, sz * 0.6),
		item_pos + Vector2(-sz * 0.8, -sz * 0.2)
	]
	draw_colored_polygon(pts, Color(0.98, 0.75, 0.15, 0.95))
	draw_polyline(pts, INK_COLOR, 3.5 * s, true)
	# Inner facet highlights
	draw_line(item_pos + Vector2(0.0, -sz), item_pos + Vector2(0.0, sz * 0.6), INK_COLOR, 2.0 * s)
	draw_line(item_pos + Vector2(-sz * 0.8, -sz * 0.2), item_pos + Vector2(sz * 0.8, -sz * 0.2), INK_COLOR, 2.0 * s)

func _draw_button_pedestal(s: float) -> void:
	var bx: float = button_pedestal_pos.x
	var by: float = button_pedestal_pos.y
	
	# 1. Base Plate & Column Stand on floor
	var base_w: float = 64.0 * s
	draw_line(Vector2(bx - base_w, floor_y), Vector2(bx + base_w, floor_y), INK_COLOR, 6.0 * s, true)
	draw_line(Vector2(bx, floor_y), Vector2(bx, by + 18.0 * s), INK_COLOR, 5.0 * s, true)
	
	# 2. Sleek Pedestal Tabletop Console
	var table_w: float = 48.0 * s
	var table_h: float = 12.0 * s
	var table_rect = Rect2(bx - table_w, by + 8.0 * s, table_w * 2.0, table_h)
	draw_rect(table_rect, Color(0.16, 0.20, 0.28))
	draw_rect(table_rect, INK_COLOR, false, 3.0 * s)
	
	# 3. Metallic Button Housing / Bezel
	var bezel_w: float = 24.0 * s
	var bezel_h: float = 10.0 * s
	var bezel_rect = Rect2(bx - bezel_w, by - 2.0 * s, bezel_w * 2.0, bezel_h)
	draw_rect(bezel_rect, Color(0.25, 0.30, 0.40))
	draw_rect(bezel_rect, INK_COLOR, false, 2.5 * s)
	
	# 4. Physical Push Button Cap (Depresses by button_depress_px)
	var cap_w: float = 18.0 * s
	var cap_h: float = 10.0 * s
	var depress: float = clampf(button_depress_px, 0.0, 10.0) * s
	var cap_top_y: float = by - 8.0 * s + depress
	var cap_rect = Rect2(bx - cap_w, cap_top_y, cap_w * 2.0, cap_h)
	# Vibrant warning red button
	draw_rect(cap_rect, Color(0.92, 0.18, 0.22))
	# Highlight on top edge
	draw_line(Vector2(bx - cap_w + 2.0 * s, cap_top_y + 1.5 * s), Vector2(bx + cap_w - 2.0 * s, cap_top_y + 1.5 * s), Color(1.0, 0.55, 0.55), 2.0 * s)
	draw_rect(cap_rect, INK_COLOR, false, 2.5 * s)
	
	# 5. Energy Blast / Flash Burst on activation (Controlled non-obscuring pulse)
	var glow: float = clampf(button_glow_alpha, 0.0, 1.0)
	if glow > 0.01:
		# Illuminate button cap with internal warm energy glow
		var glow_cap_col: Color = Color(0.92, 0.18, 0.22).lerp(Color(1.0, 0.85, 0.3), glow * 0.75)
		draw_rect(cap_rect, glow_cap_col)
		draw_rect(cap_rect, INK_COLOR, false, 2.5 * s)
		# Expanding clean fine shockwave ring around button base
		var pulse_r: float = 24.0 * s + glow * 22.0 * s
		draw_arc(Vector2(bx, by), pulse_r, 0, TAU, 32, Color(1.0, 0.85, 0.2, glow * 0.85), 2.5 * s, true)
		# Clean radiant energy sparks radiating outward away from bezel
		for ang_deg in [25, 70, 115, 205, 250, 295]:
			var a_rad: float = deg_to_rad(float(ang_deg))
			var p_start: Vector2 = Vector2(bx, by) + Vector2(cos(a_rad), sin(a_rad)) * (bezel_w * 1.05)
			var p_end: Vector2 = Vector2(bx, by) + Vector2(cos(a_rad), sin(a_rad)) * (bezel_w * 1.05 + 16.0 * s * glow)
			draw_line(p_start, p_end, Color(1.0, 0.9, 0.3, glow * 0.9), 2.2 * s)

func _draw_interactive_target(s: float) -> void:
	var tx = target_object_pos.x
	var ty = target_object_pos.y
	# Pedestal Base & Pole
	draw_line(Vector2(tx - 24.0 * s, floor_y), Vector2(tx + 24.0 * s, floor_y), INK_COLOR, 5.0 * s, true)
	draw_line(Vector2(tx, floor_y), Vector2(tx, ty + 20.0 * s), INK_COLOR, 4.0 * s, true)
	draw_circle(Vector2(tx, ty + 20.0 * s), 8.0 * s, INK_COLOR)
	
	# Target Orb
	var orb_r: float = 16.0 * s
	var glow_alpha: float = clampf(target_object_pulse, 0.0, 1.0)
	if glow_alpha > 0.01:
		draw_circle(Vector2(tx, ty), orb_r * (1.0 + glow_alpha * 0.5), Color(0.0, 0.85, 1.0, glow_alpha * 0.35))
		draw_arc(Vector2(tx, ty), orb_r * (1.0 + glow_alpha * 0.7), 0, TAU, 32, Color(1.0, 0.85, 0.2, glow_alpha * 0.8), 2.5 * s, true)
	
	draw_circle(Vector2(tx, ty), orb_r, Color(0.12, 0.16, 0.24))
	draw_circle(Vector2(tx, ty), orb_r * 0.72, Color(0.0, 0.85, 1.0) if glow_alpha > 0.01 else Color(0.85, 0.90, 0.96))
	draw_arc(Vector2(tx, ty), orb_r, 0, TAU, 32, INK_COLOR, 3.8 * s, true)

func _draw_articulated_limb(p0: Vector2, p1: Vector2, p2: Vector2, w0: float, w1: float, w2: float, col: Color) -> void:
	# Segment 1 trapezoid (p0 -> p1)
	var d1: Vector2 = p1 - p0
	var len1: float = maxf(1e-4, d1.length())
	var n1: Vector2 = Vector2(-d1.y, d1.x) / len1
	var poly1: PackedVector2Array = [
		p0 + n1 * (w0 * 0.5),
		p1 + n1 * (w1 * 0.5),
		p1 - n1 * (w1 * 0.5),
		p0 - n1 * (w0 * 0.5)
	]
	draw_colored_polygon(poly1, col)
	
	# Segment 2 trapezoid (p1 -> p2)
	var d2: Vector2 = p2 - p1
	var len2: float = maxf(1e-4, d2.length())
	var n2: Vector2 = Vector2(-d2.y, d2.x) / len2
	var poly2: PackedVector2Array = [
		p1 + n2 * (w1 * 0.5),
		p2 + n2 * (w2 * 0.5),
		p2 - n2 * (w2 * 0.5),
		p1 - n2 * (w1 * 0.5)
	]
	draw_colored_polygon(poly2, col)
	
	# Joint sphere caps
	draw_circle(p0, w0 * 0.5, col)
	draw_circle(p1, w1 * 0.5, col)
	draw_circle(p2, w2 * 0.5, col)

func _draw_tapered_limb(p0: Vector2, p1: Vector2, p2: Vector2, w0: float, w1: float, w2: float, col: Color) -> void:
	var steps: int = 16
	var pts_left: PackedVector2Array = []
	var pts_right: PackedVector2Array = []
	
	var ctrl: Vector2 = 1.15 * p1 - 0.075 * (p0 + p2)
	for i in range(steps + 1):
		var t: float = float(i) / float(steps)
		var u: float = 1.0 - t
		var pt: Vector2 = u * u * p0 + 2.0 * u * t * ctrl + t * t * p2
		var tangent: Vector2 = 2.0 * u * (ctrl - p0) + 2.0 * t * (p2 - ctrl)
		var n: Vector2 = Vector2(-tangent.y, tangent.x).normalized()
		var hw: float = 0.5 * (lerpf(w0, w1, t * 2.0) if t < 0.5 else lerpf(w1, w2, (t - 0.5) * 2.0))
		pts_left.append(pt + n * hw)
		pts_right.append(pt - n * hw)
	
	var poly: PackedVector2Array = []
	for p in pts_left:
		poly.append(p)
	for idx in range(pts_right.size() - 1, -1, -1):
		poly.append(pts_right[idx])
	draw_colored_polygon(poly, col)
	draw_circle(p0, w0 * 0.5, col)
	draw_circle(p2, w2 * 0.5, col)

func _draw_boot(ankle: Vector2, angle_deg: float, length: float, height: float, d: float) -> void:
	draw_set_transform(ankle, deg_to_rad(angle_deg), Vector2.ONE)
	var heel_x: float = -d * (length * 0.25)
	var toe_x: float = d * (length * 0.85)
	var sole_y: float = height
	
	var boot_pts: PackedVector2Array = [
		Vector2(heel_x, 0.0),
		Vector2(heel_x, sole_y),
		Vector2(toe_x, sole_y),
		Vector2(toe_x + d * 6.0, sole_y * 0.5),
		Vector2(d * (length * 0.25), -height * 0.20),
		Vector2(0.0, 0.0)
	]
	draw_colored_polygon(boot_pts, BODY_FILL)
	draw_polyline(boot_pts, INK_COLOR, 4.2, true)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

func _draw_hand(wrist: Vector2, angle_deg: float, pose: String, s: float, wrist_width: float) -> void:
	draw_set_transform(wrist, deg_to_rad(angle_deg), Vector2.ONE)
	var r_base: float = (wrist_width * s) * 0.5
	var hand_len: float = 14.5 * s
	
	if pose == "press" or pose == "point":
		# 4. Index-finger press (clearly distinct fingertip contacting surface)
		hand_len = 17.5 * s
		draw_circle(Vector2.ZERO, r_base, BODY_FILL)
		var palm_pts: PackedVector2Array = [
			Vector2(0, -r_base * 0.8),
			Vector2(hand_len * 0.45, -r_base * 0.9),
			Vector2(hand_len * 0.55, r_base * 0.7),
			Vector2(0, r_base * 0.8)
		]
		draw_colored_polygon(palm_pts, BODY_FILL)
		# Tapered extended index finger pointing along action axis
		var finger_pts: PackedVector2Array = [
			Vector2(hand_len * 0.35, -r_base * 0.35),
			Vector2(hand_len, -r_base * 0.2),
			Vector2(hand_len, r_base * 0.2),
			Vector2(hand_len * 0.35, r_base * 0.35)
		]
		draw_colored_polygon(finger_pts, BODY_FILL)
		draw_circle(Vector2(hand_len, 0), r_base * 0.35, BODY_FILL)
	elif pose == "hesitant" or pose == "hesitant_reach":
		# 3. Hesitant hovering hand
		hand_len = 16.0 * s
		draw_circle(Vector2.ZERO, r_base, BODY_FILL)
		var pts: PackedVector2Array = [
			Vector2(0, -r_base * 0.8),
			Vector2(hand_len * 0.65, -r_base * 0.9),
			Vector2(hand_len, -r_base * 0.25),
			Vector2(hand_len * 0.8, r_base * 0.6),
			Vector2(0, r_base * 0.7)
		]
		draw_colored_polygon(pts, BODY_FILL)
		draw_circle(Vector2(hand_len, -r_base * 0.15), r_base * 0.4, BODY_FILL)
	elif pose == "curious" or pose == "curious_gesture":
		# 2. Curious inquiring hand (fingers curved gently upward)
		hand_len = 16.0 * s
		draw_circle(Vector2.ZERO, r_base, BODY_FILL)
		var pts: PackedVector2Array = [
			Vector2(0, -r_base * 0.8),
			Vector2(hand_len * 0.6, -r_base * 1.1),
			Vector2(hand_len, -r_base * 0.4),
			Vector2(hand_len * 0.8, r_base * 0.7),
			Vector2(0, r_base * 0.8)
		]
		draw_colored_polygon(pts, BODY_FILL)
		draw_circle(Vector2(hand_len, -r_base * 0.3), r_base * 0.45, BODY_FILL)
	elif pose == "recoil" or pose == "startled" or pose == "reach_open":
		# 5. Startled recoil hand (wide open splayed reflex)
		hand_len = 17.0 * s
		draw_circle(Vector2.ZERO, r_base, BODY_FILL)
		var pts: PackedVector2Array = [
			Vector2(0, -r_base * 1.1),
			Vector2(hand_len * 0.75, -r_base * 1.4),
			Vector2(hand_len, -r_base * 0.5),
			Vector2(hand_len * 0.95, r_base * 0.6),
			Vector2(hand_len * 0.7, r_base * 1.3),
			Vector2(0, r_base * 1.0)
		]
		draw_colored_polygon(pts, BODY_FILL)
		draw_circle(Vector2(hand_len, -r_base * 0.5), r_base * 0.4, BODY_FILL)
		draw_circle(Vector2(hand_len * 0.75, -r_base * 1.2), r_base * 0.35, BODY_FILL)
	elif pose == "amused":
		# 6. Amused gesture hand
		hand_len = 15.0 * s
		draw_circle(Vector2.ZERO, r_base, BODY_FILL)
		var pts: PackedVector2Array = [
			Vector2(0, -r_base * 0.8),
			Vector2(hand_len * 0.7, -r_base * 0.7),
			Vector2(hand_len, 0),
			Vector2(hand_len * 0.6, r_base * 0.8),
			Vector2(0, r_base * 0.8)
		]
		draw_colored_polygon(pts, BODY_FILL)
		draw_circle(Vector2(hand_len * 0.8, 0), r_base * 0.45, BODY_FILL)
	elif pose == "fist":
		hand_len = 12.0 * s
		draw_circle(Vector2.ZERO, r_base, BODY_FILL)
		var pts: PackedVector2Array = [
			Vector2(0, -r_base * 0.9),
			Vector2(hand_len * 0.7, -r_base * 0.9),
			Vector2(hand_len, -r_base * 0.3),
			Vector2(hand_len, r_base * 0.4),
			Vector2(hand_len * 0.6, r_base * 0.9),
			Vector2(0, r_base * 0.9)
		]
		draw_colored_polygon(pts, BODY_FILL)
		draw_circle(Vector2(hand_len * 0.5, 0), r_base * 0.75, BODY_FILL)
	elif pose == "chin_touch":
		hand_len = 16.0 * s
		draw_circle(Vector2.ZERO, r_base, BODY_FILL)
		var pts: PackedVector2Array = [
			Vector2(0, -r_base * 0.7),
			Vector2(hand_len, -r_base * 0.2),
			Vector2(hand_len, r_base * 0.1),
			Vector2(hand_len * 0.45, r_base * 0.9),
			Vector2(0, r_base * 0.8)
		]
		draw_colored_polygon(pts, BODY_FILL)
		draw_circle(Vector2(hand_len, 0), r_base * 0.4, BODY_FILL)
	elif pose == "shrug_open":
		hand_len = 16.0 * s
		draw_circle(Vector2.ZERO, r_base, BODY_FILL)
		var pts: PackedVector2Array = [
			Vector2(0, -r_base * 0.6),
			Vector2(hand_len * 0.8, -r_base * 1.2),
			Vector2(hand_len, -r_base * 0.5),
			Vector2(hand_len * 0.9, r_base * 0.8),
			Vector2(0, r_base * 0.8)
		]
		draw_colored_polygon(pts, BODY_FILL)
		draw_circle(Vector2(hand_len * 0.8, -r_base * 0.5), r_base * 0.5, BODY_FILL)
	else: # "relaxed"
		# 1. Relaxed hand
		draw_circle(Vector2.ZERO, r_base, BODY_FILL)
		var pts: PackedVector2Array = [
			Vector2(0, -r_base * 0.8),
			Vector2(hand_len - r_base * 0.5, -r_base * 0.8),
			Vector2(hand_len, 0),
			Vector2(hand_len - r_base * 0.5, r_base * 0.8),
			Vector2(0, r_base * 0.8)
		]
		draw_colored_polygon(pts, BODY_FILL)
		draw_circle(Vector2(hand_len - r_base * 0.4, 0), r_base * 0.8, BODY_FILL)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

func _draw_head_and_face(s: float, d: float, outline_w: float) -> void:
	var head_r: float = HEAD_RADIUS * s
	var hx: float = solved_head_center.x
	var hy: float = solved_head_center.y
	var yaw_px: float = head_r * yaw_factor * d
	var nod_y: float = head_nod_px * s
	
	var h_sq: float = clampf(head_squash, 0.7, 1.4)
	draw_set_transform(Vector2(hx, hy), deg_to_rad(head_tilt_deg), Vector2(1.02 * (1.0 / sqrt(h_sq)), 0.99 * h_sq))
	
	# Head Cranium
	draw_circle(Vector2.ZERO, head_r, HEAD_FILL)
	draw_arc(Vector2.ZERO, head_r, 0, TAU, 64, INK_COLOR, outline_w, true)
	
	# Contoured Beard (Lower 30% of face)
	var beard_pts: PackedVector2Array = [
		Vector2(-head_r * 0.88 + yaw_px * 0.10, head_r * 0.34),
		Vector2(-head_r * 0.40 + yaw_px * 0.20, head_r * 0.68),
		Vector2(head_r * 0.40 + yaw_px * 0.20, head_r * 0.68),
		Vector2(head_r * 0.90 + yaw_px * 0.08, head_r * 0.32),
		Vector2(head_r * 0.70 + yaw_px * 0.15, head_r * 0.92),
		Vector2(yaw_px * 0.18, head_r * 1.05),
		Vector2(-head_r * 0.70 + yaw_px * 0.10, head_r * 0.92)
	]
	draw_colored_polygon(beard_pts, BEARD_FILL)
	draw_polyline(beard_pts, INK_COLOR, outline_w * 0.88, true)
	
	# Expressive Mouth Shapes
	var mx: float = yaw_px * 0.38
	var my: float = head_r * 0.46 + nod_y * 0.45
	if mouth_state == "curious_o":
		draw_circle(Vector2(mx, my), 6.5 * s, INK_COLOR)
	elif mouth_state == "open_gasp":
		draw_circle(Vector2(mx, my), 10.5 * s, Color(0.18, 0.08, 0.12))
		draw_arc(Vector2(mx, my), 10.5 * s, 0, TAU, 32, INK_COLOR, outline_w * 0.55, true)
	elif mouth_state == "concentrating" or mouth_state == "firm":
		var conc_pts: PackedVector2Array = [
			Vector2(mx - head_r * 0.11, my + 2.0 * s),
			Vector2(mx, my + 0.5 * s),
			Vector2(mx + head_r * 0.11, my + 2.0 * s)
		]
		draw_polyline(conc_pts, INK_COLOR, outline_w * 0.80, true)
	elif mouth_state == "confused":
		var conf_pts: PackedVector2Array = [
			Vector2(mx - head_r * 0.14, my + 3.0 * s),
			Vector2(mx - head_r * 0.04, my - 1.5 * s),
			Vector2(mx + head_r * 0.06, my + 2.5 * s),
			Vector2(mx + head_r * 0.15, my - 0.5 * s)
		]
		draw_polyline(conf_pts, INK_COLOR, outline_w * 0.75, true)
	elif mouth_state == "smirk" or mouth_state == "satisfied":
		var smirk_pts: PackedVector2Array = [
			Vector2(mx - head_r * 0.12, my),
			Vector2(mx, my + 4.5 * s),
			Vector2(mx + head_r * 0.14, my + 1.5 * s),
			Vector2(mx + head_r * 0.20, my - 4.0 * s)
		]
		draw_polyline(smirk_pts, INK_COLOR, outline_w * 0.70, true)
	else: # "neutral"
		var neut_pts: PackedVector2Array = [
			Vector2(mx - head_r * 0.12, my + 1.0 * s),
			Vector2(mx + head_r * 0.12, my + 1.0 * s)
		]
		draw_polyline(neut_pts, INK_COLOR, outline_w * 0.70, true)
	
	# Messy Hair Cap with secondary motion lag
	var lag_px: float = sin(deg_to_rad(hair_lag_deg)) * 12.0 * s
	var hair_pts: PackedVector2Array = [
		Vector2(-head_r * 0.90, -head_r * 0.28),
		Vector2(-head_r * 1.05, -head_r * 0.65),
		Vector2(-head_r * 0.84 + lag_px, -head_r * 1.05),
		Vector2(-head_r * 0.58, -head_r * 0.88),
		Vector2(-head_r * 0.32 + lag_px, -head_r * 1.30),
		Vector2(-head_r * 0.05, -head_r * 0.98),
		Vector2(head_r * 0.38 + lag_px, -head_r * 1.32),
		Vector2(head_r * 0.40, -head_r * 0.96),
		Vector2(head_r * 0.88 + lag_px, -head_r * 1.02),
		Vector2(head_r * 0.92, -head_r * 0.45),
		Vector2(head_r * 0.42, -head_r * 0.58),
		Vector2(-head_r * 0.35, -head_r * 0.56)
	]
	draw_colored_polygon(hair_pts, HAIR_FILL)
	draw_polyline(hair_pts, INK_COLOR, outline_w * 0.90, true)
	
	# Blank Rectangular Glasses (100% Mathematically Symmetrical Geometry)
	var canonical_w: float = LENS_WIDTH * s
	var canonical_h: float = LENS_HEIGHT * s
	var bridge_gap: float = GLASSES_BRIDGE_GAP * s
	var lens_y: float = -head_r * 0.16 + nod_y * 0.55 + glasses_slip_px * s
	
	var lx: float = yaw_px * 0.60 - bridge_gap * 0.5 - canonical_w
	var rx: float = yaw_px * 0.60 + bridge_gap * 0.5
	
	# Temples
	draw_line(Vector2(-head_r * 0.96, lens_y + canonical_h * 0.4), Vector2(lx, lens_y + canonical_h * 0.4), INK_COLOR, outline_w * 0.75, true)
	draw_line(Vector2(lx + canonical_w, lens_y + canonical_h * 0.4), Vector2(rx, lens_y + canonical_h * 0.4), INK_COLOR, outline_w * 0.85, true)
	
	# Left & Right Lenses (Identical rounded rectangles)
	_draw_rounded_lens(Rect2(lx, lens_y, canonical_w, canonical_h), LENS_CORNER_RADIUS * s, outline_w * 0.85)
	_draw_rounded_lens(Rect2(rx, lens_y, canonical_w, canonical_h), LENS_CORNER_RADIUS * s, outline_w * 0.85)
	
	# Symmetrical Eyebrows (Anchored anatomically to forehead, independent of glasses slip)
	var forehead_y: float = -head_r * 0.16 + nod_y * 0.55
	var baseline_y: float = forehead_y - BROW_BASELINE_Y * s
	var slant_shift: float = sin(deg_to_rad(brow_slant_deg)) * 5.0 * s
	var brow_len: float = BROW_LENGTH * s
	
	# Left eyebrow
	var lb_cx: float = lx + canonical_w * 0.5
	var lb_y: float = baseline_y - left_brow_raise_px * s
	var lb_pts: PackedVector2Array = [
		Vector2(lb_cx - brow_len * 0.5, lb_y + slant_shift),
		Vector2(lb_cx, lb_y - BROW_ARCH * s),
		Vector2(lb_cx + brow_len * 0.5, lb_y - slant_shift)
	]
	draw_polyline(lb_pts, INK_COLOR, outline_w * 0.75, true)
	
	# Right eyebrow
	var rb_cx: float = rx + canonical_w * 0.5
	var rb_y: float = baseline_y - right_brow_raise_px * s
	var rb_pts: PackedVector2Array = [
		Vector2(rb_cx - brow_len * 0.5, rb_y - slant_shift),
		Vector2(rb_cx, rb_y - BROW_ARCH * s),
		Vector2(rb_cx + brow_len * 0.5, rb_y + slant_shift)
	]
	draw_polyline(rb_pts, INK_COLOR, outline_w * 0.75, true)
	
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

func _draw_rounded_lens(rect: Rect2, rc: float, stroke_w: float) -> void:
	var pts: PackedVector2Array = []
	var corner_steps: int = 4
	# Top-left corner
	for i in range(corner_steps + 1):
		var a: float = PI + float(i) / float(corner_steps) * (PI * 0.5)
		pts.append(Vector2(rect.position.x + rc + rc * cos(a), rect.position.y + rc + rc * sin(a)))
	# Top-right corner
	for i in range(corner_steps + 1):
		var a: float = PI * 1.5 + float(i) / float(corner_steps) * (PI * 0.5)
		pts.append(Vector2(rect.end.x - rc + rc * cos(a), rect.position.y + rc + rc * sin(a)))
	# Bottom-right corner
	for i in range(corner_steps + 1):
		var a: float = 0.0 + float(i) / float(corner_steps) * (PI * 0.5)
		pts.append(Vector2(rect.end.x - rc + rc * cos(a), rect.end.y - rc + rc * sin(a)))
	# Bottom-left corner
	for i in range(corner_steps + 1):
		var a: float = PI * 0.5 + float(i) / float(corner_steps) * (PI * 0.5)
		pts.append(Vector2(rect.position.x + rc + rc * cos(a), rect.end.y - rc + rc * sin(a)))
	
	draw_colored_polygon(pts, Color.WHITE)
	pts.append(pts[0]) # Close loop for outline
	draw_polyline(pts, INK_COLOR, stroke_w, true)

# ===========================================================================
# Kinematic Control & Acting API (Milestone 1, 2, 3)
# ===========================================================================

## Locks foot in world space. Pelvis motion automatically flexes knee with 0.0px drift.
func lock_foot(side: String, world_pos: Vector2 = Vector2.ZERO) -> void:
	if side.to_lower() == "left":
		left_foot_locked = true
		left_foot_lock_pos = world_pos if world_pos != Vector2.ZERO else solved_left_ankle
	elif side.to_lower() == "right":
		right_foot_locked = true
		right_foot_lock_pos = world_pos if world_pos != Vector2.ZERO else solved_right_ankle

func unlock_foot(side: String) -> void:
	if side.to_lower() == "left":
		left_foot_locked = false
	elif side.to_lower() == "right":
		right_foot_locked = false

## Directs right hand to target position via 2-bone analytical IK.
func reach_hand_to(world_pos: Vector2, elbow_down: bool = true) -> void:
	right_arm_ik_enabled = true
	right_arm_ik_target = world_pos
	right_arm_ik_elbow_down = elbow_down

func release_hand_ik() -> void:
	right_arm_ik_enabled = false
	hand_contact_constrained = false

## Couples right hand to moving button contact point.
func attach_hand_to_button() -> void:
	hand_contact_constrained = true
	right_arm_ik_enabled = true
	right_hand_pose = "press"

func detach_hand_from_button() -> void:
	hand_contact_constrained = false
	right_arm_ik_enabled = false

## Orients head and eyes toward target position.
func look_at_target(world_pos: Vector2) -> void:
	gaze_target_enabled = true
	gaze_target_pos = world_pos

func clear_gaze_target() -> void:
	gaze_target_enabled = false

## Reusable silent-acting expression library (Phase 6).
func set_expression(expr_name: String, intensity: float = 1.0) -> void:
	match expr_name.to_lower():
		"curious":
			head_tilt_deg = lerpf(0.0, 4.0, intensity)
			right_brow_raise_px = lerpf(0.0, 6.0, intensity)
			left_brow_raise_px = lerpf(0.0, -1.0, intensity)
			brow_slant_deg = lerpf(0.0, 1.5, intensity)
			mouth_state = "curious_o"
		"confused":
			head_tilt_deg = lerpf(0.0, 8.5, intensity)
			right_brow_raise_px = lerpf(0.0, 7.0, intensity)
			left_brow_raise_px = lerpf(0.0, -3.0, intensity)
			brow_slant_deg = lerpf(0.0, 3.0, intensity)
			mouth_state = "neutral"
		"suspicious":
			head_tilt_deg = lerpf(0.0, -3.0, intensity)
			right_brow_raise_px = lerpf(0.0, -3.5, intensity)
			left_brow_raise_px = lerpf(0.0, -3.5, intensity)
			brow_slant_deg = lerpf(0.0, 2.0, intensity)
			mouth_state = "firm"
		"confident":
			head_tilt_deg = lerpf(0.0, -2.0, intensity)
			right_brow_raise_px = lerpf(0.0, 3.5, intensity)
			left_brow_raise_px = lerpf(0.0, 1.0, intensity)
			brow_slant_deg = lerpf(0.0, 1.0, intensity)
			mouth_state = "smirk"
		"hesitant":
			head_tilt_deg = lerpf(0.0, 10.0, intensity)
			right_brow_raise_px = lerpf(0.0, 6.0, intensity)
			left_brow_raise_px = lerpf(0.0, -2.0, intensity)
			brow_slant_deg = lerpf(0.0, 3.5, intensity)
			mouth_state = "neutral"
		"surprised":
			head_tilt_deg = lerpf(0.0, 15.0, intensity)
			right_brow_raise_px = lerpf(0.0, 12.0, intensity)
			left_brow_raise_px = lerpf(0.0, 12.0, intensity)
			brow_slant_deg = 0.0
			glasses_slip_px = lerpf(0.0, 7.0, intensity)
			mouth_state = "open_gasp"
		"frustrated":
			head_tilt_deg = lerpf(0.0, -5.0, intensity)
			right_brow_raise_px = lerpf(0.0, -4.0, intensity)
			left_brow_raise_px = lerpf(0.0, -4.0, intensity)
			brow_slant_deg = lerpf(0.0, -3.5, intensity)
			mouth_state = "firm"
		"satisfied":
			head_tilt_deg = lerpf(0.0, -3.0, intensity)
			right_brow_raise_px = lerpf(0.0, 4.0, intensity)
			left_brow_raise_px = lerpf(0.0, 1.0, intensity)
			brow_slant_deg = lerpf(0.0, 2.0, intensity)
			mouth_state = "smirk"
		"embarrassed":
			head_tilt_deg = lerpf(0.0, -5.0, intensity)
			right_brow_raise_px = lerpf(0.0, 2.0, intensity)
			left_brow_raise_px = lerpf(0.0, 2.0, intensity)
			brow_slant_deg = lerpf(0.0, -2.0, intensity)
			glasses_slip_px = lerpf(0.0, 4.0, intensity)
			mouth_state = "neutral"
		"thoughtful":
			head_tilt_deg = lerpf(0.0, 6.0, intensity)
			right_brow_raise_px = lerpf(0.0, 3.0, intensity)
			left_brow_raise_px = lerpf(0.0, -1.0, intensity)
			brow_slant_deg = lerpf(0.0, 1.5, intensity)
			mouth_state = "concentrating"
		"disappointed":
			head_tilt_deg = lerpf(0.0, -8.0, intensity)
			right_brow_raise_px = lerpf(0.0, -2.0, intensity)
			left_brow_raise_px = lerpf(0.0, -2.0, intensity)
			brow_slant_deg = lerpf(0.0, -2.5, intensity)
			shoulder_shrug_px = lerpf(0.0, -6.0, intensity)
			mouth_state = "neutral"
		"neutral", _:
			head_tilt_deg = 0.0
			right_brow_raise_px = 0.0
			left_brow_raise_px = 0.0
			brow_slant_deg = 0.0
			glasses_slip_px = 0.0
			shoulder_shrug_px = 0.0
			mouth_state = "neutral"

## Robustness & Verification Metrics API
func get_ik_error(limb: String) -> Dictionary:
	solve_kinematics()
	var s: float = character_scale
	if limb.to_lower() == "right_arm":
		var u_arm: float = UPPER_ARM_LENGTH * s
		var f_arm: float = FOREARM_LENGTH * s
		var r_hand_len: float = (17.5 if (right_hand_pose == "press" or right_hand_pose == "point") else 14.5) * s
		var max_reach: float = u_arm + f_arm + r_hand_len
		var reach_dist: float = solved_right_shoulder.distance_to(right_arm_ik_target)
		var actual_err: float = solved_right_fingertip.distance_to(right_arm_ik_target) if right_arm_ik_enabled else 0.0
		var b1: float = solved_right_shoulder.distance_to(solved_right_elbow)
		var b2: float = solved_right_elbow.distance_to(solved_right_wrist)
		var h_len: float = solved_right_wrist.distance_to(solved_right_fingertip)
		return {
			"enabled": right_arm_ik_enabled,
			"target": right_arm_ik_target,
			"actual_end_effector": solved_right_fingertip,
			"error_distance": actual_err,
			"reach_distance": reach_dist,
			"max_reach": max_reach,
			"is_reachable": reach_dist <= max_reach,
			"bone1_length": b1,
			"bone2_length": b2,
			"hand_length": h_len,
			"bone1_preserved": absf(b1 - u_arm) < 0.05,
			"bone2_preserved": absf(b2 - f_arm) < 0.05,
			"hand_preserved": absf(h_len - r_hand_len) < 0.05
		}
	elif limb.to_lower() == "left_leg":
		var thigh_l: float = THIGH_LENGTH * s
		var shin_l: float = SHIN_LENGTH * s
		var err: float = solved_left_ankle.distance_to(left_foot_lock_pos) if left_foot_locked else 0.0
		var b1: float = solved_left_hip.distance_to(solved_left_knee)
		var b2: float = solved_left_knee.distance_to(solved_left_ankle)
		return {
			"locked": left_foot_locked,
			"lock_pos": left_foot_lock_pos,
			"actual_pos": solved_left_ankle,
			"drift": err,
			"bone1_preserved": absf(b1 - thigh_l) < 0.05,
			"bone2_preserved": absf(b2 - shin_l) < 0.05
		}
	elif limb.to_lower() == "right_leg":
		var thigh_l: float = THIGH_LENGTH * s
		var shin_l: float = SHIN_LENGTH * s
		var err: float = solved_right_ankle.distance_to(right_foot_lock_pos) if right_foot_locked else 0.0
		var b1: float = solved_right_hip.distance_to(solved_right_knee)
		var b2: float = solved_right_knee.distance_to(solved_right_ankle)
		return {
			"locked": right_foot_locked,
			"lock_pos": right_foot_lock_pos,
			"actual_pos": solved_right_ankle,
			"drift": err,
			"bone1_preserved": absf(b1 - thigh_l) < 0.05,
			"bone2_preserved": absf(b2 - shin_l) < 0.05
		}
	return {}

func get_foot_drift(side: String) -> float:
	solve_kinematics()
	if side.to_lower() == "left":
		return solved_left_ankle.distance_to(left_foot_lock_pos) if left_foot_locked else 0.0
	elif side.to_lower() == "right":
		return solved_right_ankle.distance_to(right_foot_lock_pos) if right_foot_locked else 0.0
	return 0.0

func check_joint_limits() -> Array:
	solve_kinematics()
	var violations: Array = []
	# Right elbow angle
	var r_el_bend: float = absf(right_elbow_deg)
	if r_el_bend > 165.0:
		violations.append("Right elbow hyperextended/overbent: %.1f deg" % r_el_bend)
	# Left elbow angle
	var l_el_bend: float = absf(left_elbow_deg)
	if l_el_bend > 165.0:
		violations.append("Left elbow hyperextended/overbent: %.1f deg" % l_el_bend)
	# Right knee bend (anatomical flex)
	var r_knee_bend: float = absf(right_shin_deg)
	if r_knee_bend > 155.0:
		violations.append("Right knee overflexed: %.1f deg" % r_knee_bend)
	# Left knee bend
	var l_knee_bend: float = absf(left_shin_deg)
	if l_knee_bend > 155.0:
		violations.append("Left knee overflexed: %.1f deg" % l_knee_bend)
	# Torso lean
	if absf(torso_lean_deg) > 45.0:
		violations.append("Torso lean excessive: %.1f deg" % torso_lean_deg)
	return violations

