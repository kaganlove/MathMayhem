class_name PoseLibraryV12
extends RefCounted

## Math Mayhem v12.1 — Canonical Authored Expressive Pose Library
## Implements the 6 primary reference poses from the v12.1 Animation Production Blueprint:
## 1. Neutral (Idle) — Relaxed, ready, balanced weight, soft knees, gentle arm hang
## 2. Curious (Interest) — Notices button, head leads, forward lean (12°), inquiring hand
## 3. Think / Hesitate (Uncertain) — Balanced near button, hovering hand (elbow 72°), head cocks in doubt, free hand at waist
## 4. Reach / Press (Action) — Commit and press, shoulder protracts, organic elbow flex (38°), button depresses -8px
## 5. Surprise (Reaction) — Sudden recoil (-16°), rear foot weight transfer, shoulders up (+24px), asymmetric wide arms, gasp
## 6. Satisfaction (Payoff) — Amused and intrigued, relaxed shoulders, subtle amused smirk, appealing finish

const STANDING_Y: float = 1285.8

static func get_pose(pose_name: String) -> Dictionary:
	match pose_name.to_lower():
		"neutral", "idle":
			return get_neutral_pose()
		"curious", "curiosity", "interest":
			return get_curious_pose()
		"think", "hesitate", "hesitation", "uncertain":
			return get_hesitation_pose()
		"reach", "press", "action":
			return get_press_pose()
		"surprise", "reaction":
			return get_surprise_pose()
		"satisfaction", "payoff", "smirk":
			return get_satisfaction_pose()
		_:
			return get_neutral_pose()

# ===========================================================================
# 1. Neutral (Idle) — Relaxed, Ready
# ===========================================================================
static func get_neutral_pose() -> Dictionary:
	return {
		"name": "Neutral",
		"label": "1. Neutral (Idle)",
		"description": "Relaxed approachable stance, soft knees, natural arm hang, zero tension",
		"root_pos": Vector2(380.0, STANDING_Y),
		"torso_lean_deg": 1.0,
		"spine_arch_deg": 2.5,
		"torso_squash": 1.0,
		"shoulder_shrug_px": 0.0,
		"right_shoulder_protract_px": 0.0,
		# Head & Face
		"head_tilt_deg": 0.5,
		"head_nod_px": 0.0,
		"head_squash": 1.0,
		"yaw_factor": 0.22,
		"glasses_slip_px": 0.0,
		"hair_lag_deg": 0.0,
		"left_brow_raise_px": 0.0,
		"right_brow_raise_px": 0.0,
		"brow_slant_deg": 0.0,
		"mouth_state": "neutral",
		# Arms (natural downward drape, gentle elbow flex, no chicken wings)
		"left_shoulder_deg": 8.0,
		"left_elbow_deg": 18.0,
		"left_wrist_deg": 5.0,
		"left_hand_pose": "relaxed",
		"right_shoulder_deg": 10.0,
		"right_elbow_deg": 20.0,
		"right_wrist_deg": 5.0,
		"right_hand_pose": "relaxed",
		# Legs (parallel soft knee flex, balanced center of mass)
		"left_thigh_deg": 14.0,
		"left_shin_deg": -28.0,
		"left_foot_deg": 14.0,
		"right_thigh_deg": 14.0,
		"right_shin_deg": -28.0,
		"right_foot_deg": 14.0,
		# Button pedestal
		"show_button_pedestal": true,
		"button_depress_px": 0.0,
		"button_glow_alpha": 0.0
	}

# ===========================================================================
# 2. Curious (Interest) — Notices Something
# ===========================================================================
static func get_curious_pose() -> Dictionary:
	var p = get_neutral_pose()
	p["name"] = "Curious"
	p["label"] = "2. Curious (Interest)"
	p["description"] = "Head leads attention shift, forward lean (12°), weight shifts forward, inquiring hand"
	p["root_pos"] = Vector2(390.0, STANDING_Y)
	p["torso_lean_deg"] = 12.0
	p["spine_arch_deg"] = 5.0
	p["shoulder_shrug_px"] = 2.0
	p["head_tilt_deg"] = -5.5
	p["head_nod_px"] = -2.0
	p["yaw_factor"] = 0.32
	p["left_brow_raise_px"] = 1.0
	p["right_brow_raise_px"] = 5.5
	p["brow_slant_deg"] = 3.0
	p["mouth_state"] = "curious_o"
	# Arms: front arm lifts inquiringly, back arm counterbalances
	p["left_shoulder_deg"] = -6.0
	p["left_elbow_deg"] = 16.0
	p["left_wrist_deg"] = 5.0
	p["left_hand_pose"] = "relaxed"
	p["right_shoulder_deg"] = 30.0
	p["right_elbow_deg"] = 42.0
	p["right_wrist_deg"] = -10.0
	p["right_hand_pose"] = "reach_open"
	# Legs: weight shifts forward onto front foot
	p["left_thigh_deg"] = 8.0
	p["left_shin_deg"] = -18.0
	p["left_foot_deg"] = 10.0
	p["right_thigh_deg"] = 22.0
	p["right_shin_deg"] = -36.0
	p["right_foot_deg"] = 14.0
	return p

# ===========================================================================
# 3. Think / Hesitate (Uncertain) — Considers the Risk
# ===========================================================================
static func get_hesitation_pose() -> Dictionary:
	var p = get_neutral_pose()
	p["name"] = "Think / Hesitate"
	p["label"] = "3. Think / Hesitate (Uncertain)"
	p["description"] = "Balanced near button, hovering hand (elbow 72°), head cocks in doubt, free hand at waist"
	p["root_pos"] = Vector2(540.0, STANDING_Y)
	p["torso_lean_deg"] = 6.0
	p["spine_arch_deg"] = 3.5
	p["shoulder_shrug_px"] = 4.0
	p["head_tilt_deg"] = 8.0
	p["head_nod_px"] = 1.5
	p["yaw_factor"] = 0.28
	p["left_brow_raise_px"] = -2.5
	p["right_brow_raise_px"] = 6.0
	p["brow_slant_deg"] = -4.0
	p["mouth_state"] = "confused"
	# Arms: Left arm resting at waist, Right arm hovering 25px above button
	p["left_shoulder_deg"] = 18.0
	p["left_elbow_deg"] = 62.0
	p["left_wrist_deg"] = 15.0
	p["left_hand_pose"] = "relaxed"
	p["right_shoulder_deg"] = 48.0
	p["right_elbow_deg"] = 46.0
	p["right_wrist_deg"] = -12.0
	p["right_hand_pose"] = "point"
	# Legs: Stable balanced stance
	p["left_thigh_deg"] = 12.0
	p["left_shin_deg"] = -24.0
	p["left_foot_deg"] = 12.0
	p["right_thigh_deg"] = 18.0
	p["right_shin_deg"] = -32.0
	p["right_foot_deg"] = 14.0
	return p

# ===========================================================================
# 4. Reach / Press (Action) — Commit and Press
# ===========================================================================
static func get_press_pose() -> Dictionary:
	var p = get_neutral_pose()
	p["name"] = "Reach / Press"
	p["label"] = "4. Reach / Press (Action)"
	p["description"] = "Committed forward drive, shoulder protracts, organic elbow flex (38°), button presses -8px"
	p["root_pos"] = Vector2(540.0, STANDING_Y)
	p["torso_lean_deg"] = 14.0
	p["spine_arch_deg"] = 5.5
	p["shoulder_shrug_px"] = 0.0
	p["right_shoulder_protract_px"] = 10.0
	p["head_tilt_deg"] = -3.5
	p["head_nod_px"] = -1.0
	p["yaw_factor"] = 0.25
	p["left_brow_raise_px"] = 1.0
	p["right_brow_raise_px"] = 3.5
	p["brow_slant_deg"] = 2.0
	p["mouth_state"] = "concentrating"
	# Arms: Left arm counterbalances back, Right arm presses button
	p["left_shoulder_deg"] = -14.0
	p["left_elbow_deg"] = 22.0
	p["left_wrist_deg"] = 8.0
	p["left_hand_pose"] = "relaxed"
	p["right_shoulder_deg"] = 64.0
	p["right_elbow_deg"] = 26.0
	p["right_wrist_deg"] = -4.0
	p["right_hand_pose"] = "point"
	# Legs: Committed wide forward stance
	p["left_thigh_deg"] = -2.0
	p["left_shin_deg"] = -10.0
	p["left_foot_deg"] = 12.0
	p["right_thigh_deg"] = 28.0
	p["right_shin_deg"] = -46.0
	p["right_foot_deg"] = 18.0
	# Physical button depression
	p["button_depress_px"] = 8.0
	p["button_glow_alpha"] = 0.0
	return p

# ===========================================================================
# 5. Surprise (Reaction) — Sudden Unexpected Result
# ===========================================================================
static func get_surprise_pose() -> Dictionary:
	var p = get_neutral_pose()
	p["name"] = "Surprise"
	p["label"] = "5. Surprise (Reaction)"
	p["description"] = "Explosive recoil (-16°), weight over rear foot, shoulders up (+24px), asymmetric arms, gasp"
	p["root_pos"] = Vector2(506.0, STANDING_Y - 10.0)
	p["torso_lean_deg"] = -16.0
	p["spine_arch_deg"] = -8.0
	p["torso_squash"] = 1.08
	p["shoulder_shrug_px"] = 24.0
	p["right_shoulder_protract_px"] = 0.0
	p["head_tilt_deg"] = 14.0
	p["head_nod_px"] = -4.0
	p["head_squash"] = 1.06
	p["yaw_factor"] = 0.24
	p["glasses_slip_px"] = 7.0
	p["hair_lag_deg"] = -28.0
	p["left_brow_raise_px"] = 16.0
	p["right_brow_raise_px"] = 16.0
	p["brow_slant_deg"] = 0.0
	p["mouth_state"] = "open_gasp"
	# Arms: Asymmetrical wide shock
	p["left_shoulder_deg"] = 60.0
	p["left_elbow_deg"] = 66.0
	p["left_wrist_deg"] = -24.0
	p["left_hand_pose"] = "reach_open"
	p["right_shoulder_deg"] = 72.0
	p["right_elbow_deg"] = 86.0
	p["right_wrist_deg"] = -30.0
	p["right_hand_pose"] = "reach_open"
	# Legs: Weight shifted onto rear foot (braced rear knee)
	p["left_thigh_deg"] = -16.0
	p["left_shin_deg"] = -34.0
	p["left_foot_deg"] = 14.0
	p["right_thigh_deg"] = 12.0
	p["right_shin_deg"] = -14.0
	p["right_foot_deg"] = 8.0
	# Button popped back up with residual activation glow
	p["button_depress_px"] = 0.0
	p["button_glow_alpha"] = 0.8
	return p

# ===========================================================================
# 6. Satisfaction (Payoff) — Amused and Intrigued
# ===========================================================================
static func get_satisfaction_pose() -> Dictionary:
	var p = get_neutral_pose()
	p["name"] = "Satisfaction"
	p["label"] = "6. Satisfaction (Payoff)"
	p["description"] = "Relaxed shoulders, subtle amused smirk, comfortable stable stance, gesture of intrigue"
	p["root_pos"] = Vector2(514.0, STANDING_Y)
	p["torso_lean_deg"] = -1.5
	p["spine_arch_deg"] = 3.0
	p["shoulder_shrug_px"] = 0.0
	p["right_shoulder_protract_px"] = 0.0
	p["head_tilt_deg"] = -2.0
	p["head_nod_px"] = 0.0
	p["yaw_factor"] = 0.26
	p["glasses_slip_px"] = 0.0
	p["hair_lag_deg"] = 0.0
	p["left_brow_raise_px"] = 1.0
	p["right_brow_raise_px"] = 4.0
	p["brow_slant_deg"] = 2.0
	p["mouth_state"] = "smirk"
	# Arms: Left arm relaxed at flank, Right arm gesturing or comfortable
	p["left_shoulder_deg"] = 8.0
	p["left_elbow_deg"] = 16.0
	p["left_wrist_deg"] = 5.0
	p["left_hand_pose"] = "relaxed"
	p["right_shoulder_deg"] = 18.0
	p["right_elbow_deg"] = 36.0
	p["right_wrist_deg"] = -6.0
	p["right_hand_pose"] = "relaxed"
	# Legs: Relaxed balanced stance
	p["left_thigh_deg"] = 12.0
	p["left_shin_deg"] = -26.0
	p["left_foot_deg"] = 14.0
	p["right_thigh_deg"] = 16.0
	p["right_shin_deg"] = -30.0
	p["right_foot_deg"] = 14.0
	p["button_depress_px"] = 0.0
	p["button_glow_alpha"] = 0.0
	return p

static func get_all_six_poses() -> Array[Dictionary]:
	return [
		get_neutral_pose(),
		get_curious_pose(),
		get_hesitation_pose(),
		get_press_pose(),
		get_surprise_pose(),
		get_satisfaction_pose()
	]

static func apply_pose_to_rig(rig: Node2D, pose: Dictionary) -> void:
	for prop in pose:
		if prop in ["name", "label", "description"]:
			continue
		if prop in rig:
			rig.set(prop, pose[prop])
