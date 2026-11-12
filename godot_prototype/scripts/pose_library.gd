class_name PoseLibrary
extends RefCounted

## Math Mayhem v10.0 — Canonical Authored Expressive Pose Library
## Implements the 6 primary emotional poses with 3 discrete intensity levels
## (1 = Subtle, 2 = Readable, 3 = Exaggerated).

const STANDING_Y: float = 1285.8

static func get_pose(pose_name: String, intensity: int = 2) -> Dictionary:
	match pose_name:
		"neutral":
			return _get_neutral_pose()
		"curiosity":
			return _get_curiosity_pose(intensity)
		"concentration":
			return _get_concentration_pose(intensity)
		"surprise":
			return _get_surprise_pose(intensity)
		"confusion":
			return _get_confusion_pose(intensity)
		"satisfaction":
			return _get_satisfaction_pose(intensity)
		_:
			return _get_neutral_pose()

# ===========================================================================
# 1. Neutral Standing
# ===========================================================================
static func _get_neutral_pose() -> Dictionary:
	return {
		"name": "Neutral",
		"description": "Relaxed approachable stance, soft knees, natural arm hang",
		"root_pos": Vector2(540.0, STANDING_Y),
		"torso_lean_deg": 1.0,
		"spine_arch_deg": 3.0,
		"shoulder_shrug_px": 0.0,
		"right_shoulder_protract_px": 0.0,
		# Head & Face
		"head_tilt_deg": 0.5,
		"head_nod_px": 0.0,
		"yaw_factor": 0.20,
		"glasses_slip_px": 0.0,
		"hair_lag_deg": 0.0,
		"left_brow_raise_px": 0.0,
		"right_brow_raise_px": 0.0,
		"brow_slant_deg": 0.0,
		"mouth_state": "neutral",
		# Arms (natural downward drape, no chicken wing)
		"left_shoulder_deg": 4.0,
		"left_elbow_deg": 12.0,
		"left_wrist_deg": 5.0,
		"left_hand_pose": "relaxed",
		"right_shoulder_deg": 6.0,
		"right_elbow_deg": 12.0,
		"right_wrist_deg": 5.0,
		"right_hand_pose": "relaxed",
		# Legs (parallel soft knee flex)
		"left_thigh_deg": 14.0,
		"left_shin_deg": -28.0,
		"left_foot_deg": 14.0,
		"right_thigh_deg": 14.0,
		"right_shin_deg": -28.0,
		"right_foot_deg": 14.0,
	}

# ===========================================================================
# 2. Curiosity (Notice, forward diagonal lean, hovering inquiring hand)
# ===========================================================================
static func _get_curiosity_pose(intensity: int) -> Dictionary:
	var p = _get_neutral_pose()
	p["name"] = "Curiosity"
	p["description"] = "Inquiring forward lean, quizzical brow arch, reaching interest"
	
	if intensity == 1: # Subtle
		p["torso_lean_deg"] = 3.5
		p["spine_arch_deg"] = 4.5
		p["head_tilt_deg"] = -3.0
		p["yaw_factor"] = 0.25
		p["right_brow_raise_px"] = 2.5
		p["left_brow_raise_px"] = 0.5
		p["brow_slant_deg"] = 2.0
		p["mouth_state"] = "curious_o"
		p["right_shoulder_deg"] = 16.0
		p["right_elbow_deg"] = 22.0
		p["right_hand_pose"] = "reach_open"
	elif intensity == 3: # Exaggerated
		p["root_pos"] = Vector2(560.0, STANDING_Y)
		p["torso_lean_deg"] = 8.5
		p["spine_arch_deg"] = 6.5
		p["head_tilt_deg"] = -7.0
		p["head_nod_px"] = -4.0
		p["yaw_factor"] = 0.36
		p["right_brow_raise_px"] = 7.0
		p["left_brow_raise_px"] = 1.5
		p["brow_slant_deg"] = 5.0
		p["mouth_state"] = "curious_o"
		p["right_shoulder_deg"] = 42.0
		p["right_elbow_deg"] = 48.0
		p["right_wrist_deg"] = -10.0
		p["right_hand_pose"] = "reach_open"
		p["right_thigh_deg"] = 18.0
		p["right_shin_deg"] = -34.0
	else: # Readable (Standard)
		p["root_pos"] = Vector2(550.0, STANDING_Y)
		p["torso_lean_deg"] = 5.8
		p["spine_arch_deg"] = 5.5
		p["head_tilt_deg"] = -5.0
		p["head_nod_px"] = -2.5
		p["yaw_factor"] = 0.30
		p["right_brow_raise_px"] = 4.5
		p["left_brow_raise_px"] = 1.0
		p["brow_slant_deg"] = 3.5
		p["mouth_state"] = "curious_o"
		p["right_shoulder_deg"] = 28.0
		p["right_elbow_deg"] = 36.0
		p["right_wrist_deg"] = -5.0
		p["right_hand_pose"] = "reach_open"
		p["left_shoulder_deg"] = 2.0
		p["left_elbow_deg"] = 10.0
	return p

# ===========================================================================
# 3. Concentration (Hand-to-chin, folded arms, narrowed focused brows)
# ===========================================================================
static func _get_concentration_pose(intensity: int) -> Dictionary:
	var p = _get_neutral_pose()
	p["name"] = "Concentration"
	p["description"] = "Thoughtful chin hold, folded arms, downward analytical focus"
	
	p["mouth_state"] = "concentrating"
	p["left_hand_pose"] = "relaxed"
	p["right_hand_pose"] = "chin_touch"
	
	if intensity == 1: # Subtle
		p["torso_lean_deg"] = 2.5
		p["head_tilt_deg"] = -2.0
		p["left_brow_raise_px"] = -1.5
		p["right_brow_raise_px"] = -1.5
		p["brow_slant_deg"] = -2.0
		p["right_shoulder_deg"] = 24.0
		p["right_elbow_deg"] = -110.0
		p["right_wrist_deg"] = 25.0
		p["left_shoulder_deg"] = 14.0
		p["left_elbow_deg"] = -60.0
	elif intensity == 3: # Exaggerated
		p["torso_lean_deg"] = 6.0
		p["spine_arch_deg"] = 6.0
		p["head_tilt_deg"] = -6.5
		p["head_nod_px"] = -4.0
		p["shoulder_shrug_px"] = -3.0
		p["left_brow_raise_px"] = -4.5
		p["right_brow_raise_px"] = -4.5
		p["brow_slant_deg"] = -5.5
		p["right_shoulder_deg"] = 36.0
		p["right_elbow_deg"] = -135.0
		p["right_wrist_deg"] = 42.0
		p["left_shoulder_deg"] = 28.0
		p["left_elbow_deg"] = -95.0
		p["left_wrist_deg"] = 20.0
	else: # Readable (Standard)
		p["torso_lean_deg"] = 4.0
		p["spine_arch_deg"] = 4.5
		p["head_tilt_deg"] = -4.0
		p["head_nod_px"] = -2.0
		p["left_brow_raise_px"] = -3.0
		p["right_brow_raise_px"] = -3.0
		p["brow_slant_deg"] = -3.5
		p["right_shoulder_deg"] = 30.0
		p["right_elbow_deg"] = -125.0
		p["right_wrist_deg"] = 35.0
		p["left_shoulder_deg"] = 20.0
		p["left_elbow_deg"] = -80.0
		p["left_wrist_deg"] = 15.0
	return p

# ===========================================================================
# 4. Surprise (Explosive recoil, arched back, flared elbows, gasp)
# ===========================================================================
static func _get_surprise_pose(intensity: int) -> Dictionary:
	var p = _get_neutral_pose()
	p["name"] = "Surprise"
	p["description"] = "Explosive whole-body recoil, shrugged shoulders, flared arms, wide gasp"
	p["mouth_state"] = "open_gasp"
	p["left_hand_pose"] = "reach_open"
	p["right_hand_pose"] = "reach_open"
	
	if intensity == 1: # Subtle
		p["root_pos"] = Vector2(530.0, STANDING_Y - 4.0)
		p["torso_lean_deg"] = -4.0
		p["shoulder_shrug_px"] = 8.0
		p["head_tilt_deg"] = 4.5
		p["glasses_slip_px"] = 2.5
		p["left_brow_raise_px"] = 6.0
		p["right_brow_raise_px"] = 6.0
		p["right_shoulder_deg"] = 32.0
		p["right_elbow_deg"] = 42.0
		p["left_shoulder_deg"] = 28.0
		p["left_elbow_deg"] = 38.0
	elif intensity == 3: # Exaggerated
		p["root_pos"] = Vector2(505.0, STANDING_Y - 14.0)
		p["torso_lean_deg"] = -13.5
		p["spine_arch_deg"] = -8.0
		p["shoulder_shrug_px"] = 22.0
		p["head_tilt_deg"] = 13.5
		p["head_nod_px"] = -9.0
		p["hair_lag_deg"] = -28.0
		p["glasses_slip_px"] = 7.5
		p["left_brow_raise_px"] = 18.0
		p["right_brow_raise_px"] = 18.0
		p["right_shoulder_deg"] = 62.0
		p["right_elbow_deg"] = 85.0
		p["right_wrist_deg"] = -38.0
		p["left_shoulder_deg"] = 55.0
		p["left_elbow_deg"] = 78.0
		p["left_wrist_deg"] = -32.0
		p["left_thigh_deg"] = 26.0
		p["left_shin_deg"] = -48.0
		p["right_thigh_deg"] = -12.0
		p["right_shin_deg"] = 12.0
	else: # Readable (Standard)
		p["root_pos"] = Vector2(515.0, STANDING_Y - 8.0)
		p["torso_lean_deg"] = -9.5
		p["spine_arch_deg"] = -6.0
		p["shoulder_shrug_px"] = 16.0
		p["head_tilt_deg"] = 9.5
		p["head_nod_px"] = -6.0
		p["hair_lag_deg"] = -20.0
		p["glasses_slip_px"] = 5.5
		p["left_brow_raise_px"] = 14.0
		p["right_brow_raise_px"] = 14.0
		p["right_shoulder_deg"] = 50.0
		p["right_elbow_deg"] = 68.0
		p["right_wrist_deg"] = -28.0
		p["left_shoulder_deg"] = 44.0
		p["left_elbow_deg"] = 60.0
		p["left_wrist_deg"] = -24.0
		p["left_thigh_deg"] = 22.0
		p["left_shin_deg"] = -42.0
		p["right_thigh_deg"] = -6.0
		p["right_shin_deg"] = 8.0
	return p

# ===========================================================================
# 5. Confusion (Asymmetrical head cock, one-arm shrug, wavy mouth, puzzled brow)
# ===========================================================================
static func _get_confusion_pose(intensity: int) -> Dictionary:
	var p = _get_neutral_pose()
	p["name"] = "Confusion"
	p["description"] = "Asymmetrical head tilt, one-arm open shrug, puzzled uneven brows"
	p["mouth_state"] = "confused"
	p["left_hand_pose"] = "relaxed"
	p["right_hand_pose"] = "shrug_open"
	
	if intensity == 1: # Subtle
		p["torso_lean_deg"] = -1.5
		p["head_tilt_deg"] = 4.0
		p["shoulder_shrug_px"] = 3.0
		p["left_brow_raise_px"] = -1.0
		p["right_brow_raise_px"] = 3.5
		p["brow_slant_deg"] = -2.5
		p["right_shoulder_deg"] = 32.0
		p["right_elbow_deg"] = 30.0
		p["left_shoulder_deg"] = 12.0
		p["left_elbow_deg"] = -40.0
	elif intensity == 3: # Exaggerated
		p["root_pos"] = Vector2(532.0, STANDING_Y)
		p["torso_lean_deg"] = -4.5
		p["shoulder_shrug_px"] = 9.0
		p["head_tilt_deg"] = 11.0
		p["yaw_factor"] = 0.12
		p["left_brow_raise_px"] = -3.0
		p["right_brow_raise_px"] = 9.0
		p["brow_slant_deg"] = -6.0
		p["right_shoulder_deg"] = 58.0
		p["right_elbow_deg"] = 52.0
		p["right_wrist_deg"] = 28.0
		p["left_shoulder_deg"] = 24.0
		p["left_elbow_deg"] = -75.0
		p["left_wrist_deg"] = 15.0
	else: # Readable (Standard)
		p["torso_lean_deg"] = -3.0
		p["head_tilt_deg"] = 7.5
		p["shoulder_shrug_px"] = 6.0
		p["yaw_factor"] = 0.15
		p["left_brow_raise_px"] = -2.0
		p["right_brow_raise_px"] = 6.5
		p["brow_slant_deg"] = -4.5
		p["right_shoulder_deg"] = 46.0
		p["right_elbow_deg"] = 42.0
		p["right_wrist_deg"] = 20.0
		p["left_shoulder_deg"] = 18.0
		p["left_elbow_deg"] = -58.0
		p["left_wrist_deg"] = 10.0
	return p

# ===========================================================================
# 6. Satisfaction (Confident chest, triumphant chest fist, smirk)
# ===========================================================================
static func _get_satisfaction_pose(intensity: int) -> Dictionary:
	var p = _get_neutral_pose()
	p["name"] = "Satisfaction"
	p["description"] = "Proud posture, chest expanded, triumphant fist gesture, confident smirk"
	p["mouth_state"] = "smirk"
	p["left_hand_pose"] = "relaxed"
	p["right_hand_pose"] = "fist"
	
	if intensity == 1: # Subtle
		p["torso_lean_deg"] = -1.0
		p["spine_arch_deg"] = 3.5
		p["head_tilt_deg"] = 2.0
		p["right_brow_raise_px"] = 2.0
		p["left_brow_raise_px"] = 0.5
		p["right_shoulder_deg"] = 18.0
		p["right_elbow_deg"] = -85.0
		p["right_wrist_deg"] = 15.0
	elif intensity == 3: # Exaggerated
		p["root_pos"] = Vector2(545.0, STANDING_Y)
		p["torso_lean_deg"] = -3.5
		p["spine_arch_deg"] = 6.0
		p["head_tilt_deg"] = 6.0
		p["head_nod_px"] = 4.0
		p["right_brow_raise_px"] = 5.0
		p["left_brow_raise_px"] = 2.0
		p["brow_slant_deg"] = 3.0
		p["right_shoulder_deg"] = 36.0
		p["right_elbow_deg"] = -135.0
		p["right_wrist_deg"] = 30.0
		p["left_shoulder_deg"] = 10.0
		p["left_elbow_deg"] = 20.0
	else: # Readable (Standard)
		p["torso_lean_deg"] = -2.0
		p["spine_arch_deg"] = 4.5
		p["head_tilt_deg"] = 3.8
		p["head_nod_px"] = 2.5
		p["right_brow_raise_px"] = 3.5
		p["left_brow_raise_px"] = 1.0
		p["brow_slant_deg"] = 2.0
		p["right_shoulder_deg"] = 26.0
		p["right_elbow_deg"] = -112.0
		p["right_wrist_deg"] = 22.0
		p["left_shoulder_deg"] = 6.0
		p["left_elbow_deg"] = 14.0
	return p

# Utility to apply a pose dictionary to a character rig
static func apply_pose_to_rig(rig: Node2D, pose: Dictionary) -> void:
	for key in pose:
		if key in ["name", "description"]:
			continue
		rig.set(key, pose[key])

# Utility to blend between two pose dictionaries by alpha t in [0.0, 1.0]
static func blend_poses(pose_a: Dictionary, pose_b: Dictionary, t: float) -> Dictionary:
	var blended: Dictionary = {}
	var alpha: float = clampf(t, 0.0, 1.0)
	
	for k in pose_a:
		if k in ["name", "description"]:
			blended[k] = pose_b.get(k, pose_a[k]) if alpha >= 0.5 else pose_a[k]
			continue
			
		var val_a = pose_a[k]
		var val_b = pose_b.get(k, val_a)
		
		if val_a is float and val_b is float:
			blended[k] = lerpf(val_a, val_b, alpha)
		elif val_a is Vector2 and val_b is Vector2:
			blended[k] = val_a.lerp(val_b, alpha)
		elif val_a is String:
			blended[k] = val_b if alpha >= 0.5 else val_a
		else:
			blended[k] = val_b if alpha >= 0.5 else val_a
			
	return blended
