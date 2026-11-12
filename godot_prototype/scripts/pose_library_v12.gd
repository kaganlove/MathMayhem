class_name PoseLibraryV12
extends RefCounted

## Math Mayhem v12.2 — Canonical Authored Expressive Pose Library & Movement Breakdowns
## Implements the revised 6 master emotional reference poses and functional movement breakdowns:
## 1. Neutral (Idle) — Tall, relaxed, upright balance, minimal knee flex, natural arm hang
## 2. Curious (Interest) — Forward C-curve lean (14°), weight forward, inquiring hand, trailing arm
## 3. Think / Hesitate (Uncertain) — Asymmetric S-curve, hand on hip, hovering hand (28px above button, elbow 44°), head cocked in doubt (+10°)
## 4. Reach / Press (Action) — Committed athletic stance, clavicle protracts, organic elbow flex (41°), index fingertip physically contacts button cap (0.1px precision), button depresses -8px
## 5. Surprise (Reaction) — Explosive backward recoil (-18°), rear-foot weight catch, shoulders up (+26px), asymmetric wide recoil hands, gasp
## 6. Satisfaction (Payoff) — Relaxed cocky ease (-2° lean), amused head cock (-3°), raised brow (+5px), subtle smirk, intentional button gesture

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
# 1. Neutral (Idle) — Relaxed, Ready, Balanced
# ===========================================================================
static func get_neutral_pose() -> Dictionary:
	return {
		"name": "Neutral",
		"label": "1. Neutral (Idle)",
		"subtitle": "Relaxed, ready",
		"description": "Tall relaxed upright balance, soft knees (3°), natural arm drape (6°), calm level head",
		"root_pos": Vector2(380.0, STANDING_Y),
		"torso_lean_deg": 0.5,
		"spine_arch_deg": 1.5,
		"torso_squash": 1.0,
		"shoulder_shrug_px": 0.0,
		"right_shoulder_protract_px": 0.0,
		# Head & Face
		"head_tilt_deg": 0.0,
		"head_nod_px": 0.0,
		"head_squash": 1.0,
		"yaw_factor": 0.22,
		"glasses_slip_px": 0.0,
		"hair_lag_deg": 0.0,
		"left_brow_raise_px": 0.0,
		"right_brow_raise_px": 0.0,
		"brow_slant_deg": 0.0,
		"mouth_state": "neutral",
		# Arms (natural downward drape, soft elbow flex, no chicken wings)
		"left_shoulder_deg": 6.0,
		"left_elbow_deg": 14.0,
		"left_wrist_deg": 4.0,
		"left_hand_pose": "relaxed",
		"right_shoulder_deg": 6.0,
		"right_elbow_deg": 14.0,
		"right_wrist_deg": 4.0,
		"right_hand_pose": "relaxed",
		# Legs (tall, minimal knee flexion, genuine relaxed standing)
		"left_thigh_deg": 3.0,
		"left_shin_deg": -5.0,
		"left_foot_deg": 2.0,
		"right_thigh_deg": 3.0,
		"right_shin_deg": -5.0,
		"right_foot_deg": 2.0,
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
	p["subtitle"] = "Notices something"
	p["description"] = "Strong forward C-curve (14°), weight forward onto front stance foot, front hand lifted in inquiry, trailing back arm"
	p["root_pos"] = Vector2(390.0, STANDING_Y)
	p["torso_lean_deg"] = 14.0
	p["spine_arch_deg"] = 5.5
	p["shoulder_shrug_px"] = 2.0
	p["head_tilt_deg"] = -6.5
	p["head_nod_px"] = -2.5
	p["yaw_factor"] = 0.35
	p["left_brow_raise_px"] = 1.0
	p["right_brow_raise_px"] = 6.0
	p["brow_slant_deg"] = 3.5
	p["mouth_state"] = "curious_o"
	# Arms: front inquiring hand lifted, rear arm counterbalances
	p["left_shoulder_deg"] = -18.0
	p["left_elbow_deg"] = 16.0
	p["left_wrist_deg"] = 6.0
	p["left_hand_pose"] = "relaxed"
	p["right_shoulder_deg"] = 38.0
	p["right_elbow_deg"] = 50.0
	p["right_wrist_deg"] = -12.0
	p["right_hand_pose"] = "curious"
	# Legs: weight driven forward onto front right foot
	p["left_thigh_deg"] = 4.0
	p["left_shin_deg"] = -10.0
	p["left_foot_deg"] = 6.0
	p["right_thigh_deg"] = 24.0
	p["right_shin_deg"] = -38.0
	p["right_foot_deg"] = 14.0
	return p

# ===========================================================================
# 3. Think / Hesitate (Uncertain) — Considers the Risk
# ===========================================================================
static func get_hesitation_pose() -> Dictionary:
	var p = get_neutral_pose()
	p["name"] = "Think / Hesitate"
	p["label"] = "3. Think / Hesitate (Uncertain)"
	p["subtitle"] = "Considers the risk"
	p["description"] = "Asymmetric S-curve, left hand on hip, right hand hovering 28px directly above button (elbow 44°), head cocked (+10°)"
	p["root_pos"] = Vector2(540.0, STANDING_Y)
	p["torso_lean_deg"] = 4.0
	p["spine_arch_deg"] = 2.5
	p["shoulder_shrug_px"] = 3.0
	p["head_tilt_deg"] = 10.0
	p["head_nod_px"] = 1.0
	p["yaw_factor"] = 0.30
	p["left_brow_raise_px"] = -3.0
	p["right_brow_raise_px"] = 7.0
	p["brow_slant_deg"] = -5.0
	p["mouth_state"] = "confused"
	# Arms: Left hand firmly on hip/waist, Right hand hovering 28px directly above button cap
	p["left_shoulder_deg"] = 24.0
	p["left_elbow_deg"] = 72.0
	p["left_wrist_deg"] = 16.0
	p["left_hand_pose"] = "relaxed"
	# Right hand hovering: x=760.15, y=1178.33 (28px directly above button top at x=760, y=1206.4)
	p["right_shoulder_deg"] = 30.0
	p["right_elbow_deg"] = 44.0
	p["right_wrist_deg"] = -21.0
	p["right_hand_pose"] = "hesitant"
	# Legs: Stable balanced stance
	p["left_thigh_deg"] = 6.0
	p["left_shin_deg"] = -12.0
	p["left_foot_deg"] = 6.0
	p["right_thigh_deg"] = 14.0
	p["right_shin_deg"] = -24.0
	p["right_foot_deg"] = 10.0
	return p

# ===========================================================================
# 4. Reach / Press (Action) — Commit and Press
# ===========================================================================
static func get_press_pose() -> Dictionary:
	var p = get_neutral_pose()
	p["name"] = "Reach / Press"
	p["label"] = "4. Reach / Press (Action)"
	p["subtitle"] = "Commit and press"
	p["description"] = "Committed diagonal drive (10°), right clavicle protracts, index fingertip physically on button (0.1px), button depresses -8px"
	p["root_pos"] = Vector2(540.0, STANDING_Y)
	p["torso_lean_deg"] = 10.0
	p["spine_arch_deg"] = 4.5
	p["shoulder_shrug_px"] = 0.0
	p["right_shoulder_protract_px"] = 10.0
	p["head_tilt_deg"] = -3.0
	p["head_nod_px"] = -1.0
	p["yaw_factor"] = 0.25
	p["left_brow_raise_px"] = 1.0
	p["right_brow_raise_px"] = 4.0
	p["brow_slant_deg"] = 2.0
	p["mouth_state"] = "concentrating"
	# Arms: Left arm counterbalances back (-18°), Right arm presses button
	# Kinematic exact contact: root_x=540, lean=10, sh=21, el=41, wr=5 -> tip=(760.10, 1220.01) [Target: 760.0, 1220.0]
	p["left_shoulder_deg"] = -18.0
	p["left_elbow_deg"] = 20.0
	p["left_wrist_deg"] = 8.0
	p["left_hand_pose"] = "relaxed"
	p["right_shoulder_deg"] = 21.0
	p["right_elbow_deg"] = 41.0
	p["right_wrist_deg"] = 5.0
	p["right_hand_pose"] = "press"
	# Legs: Stance foot bearing downward load
	p["left_thigh_deg"] = 0.0
	p["left_shin_deg"] = -6.0
	p["left_foot_deg"] = 6.0
	p["right_thigh_deg"] = 22.0
	p["right_shin_deg"] = -36.0
	p["right_foot_deg"] = 14.0
	# Button fully depressed by 8px
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
	p["subtitle"] = "Sudden unexpected result"
	p["description"] = "Explosive backward recoil (-18°), weight caught on braced rear foot, shoulders hiked (+26px), wide asymmetric shock hands, gasp"
	p["root_pos"] = Vector2(495.0, STANDING_Y - 8.0)
	p["torso_lean_deg"] = -18.0
	p["spine_arch_deg"] = -9.0
	p["torso_squash"] = 1.08
	p["shoulder_shrug_px"] = 26.0
	p["right_shoulder_protract_px"] = 0.0
	p["head_tilt_deg"] = 15.0
	p["head_nod_px"] = -4.0
	p["head_squash"] = 1.06
	p["yaw_factor"] = 0.24
	p["glasses_slip_px"] = 7.0
	p["hair_lag_deg"] = -30.0
	p["left_brow_raise_px"] = 16.0
	p["right_brow_raise_px"] = 16.0
	p["brow_slant_deg"] = 0.0
	p["mouth_state"] = "open_gasp"
	# Arms: Asymmetrical wide shock (Right arm high defensive, Left arm wide)
	p["left_shoulder_deg"] = 48.0
	p["left_elbow_deg"] = 56.0
	p["left_wrist_deg"] = -20.0
	p["left_hand_pose"] = "recoil"
	p["right_shoulder_deg"] = 76.0
	p["right_elbow_deg"] = 92.0
	p["right_wrist_deg"] = -30.0
	p["right_hand_pose"] = "recoil"
	# Legs: Kinetic weight caught on braced rear foot (deep knee flex -32°), front leg extended
	p["left_thigh_deg"] = -18.0
	p["left_shin_deg"] = -32.0
	p["left_foot_deg"] = 14.0
	p["right_thigh_deg"] = 16.0
	p["right_shin_deg"] = -8.0
	p["right_foot_deg"] = 22.0
	p["button_depress_px"] = 0.0
	p["button_glow_alpha"] = 0.0
	return p

# ===========================================================================
# 6. Satisfaction (Payoff) — Amused and Intrigued
# ===========================================================================
static func get_satisfaction_pose() -> Dictionary:
	var p = get_neutral_pose()
	p["name"] = "Satisfaction"
	p["label"] = "6. Satisfaction (Payoff)"
	p["subtitle"] = "Amused and intrigued"
	p["description"] = "Relaxed confident ease (-2° lean), shoulders settled, amused smirk, raised brow (+5px), subtle intentional button gesture"
	p["root_pos"] = Vector2(520.0, STANDING_Y)
	p["torso_lean_deg"] = -2.0
	p["spine_arch_deg"] = 3.0
	p["shoulder_shrug_px"] = 0.0
	p["right_shoulder_protract_px"] = 0.0
	p["head_tilt_deg"] = -3.0
	p["head_nod_px"] = 0.0
	p["yaw_factor"] = 0.28
	p["glasses_slip_px"] = 0.0
	p["hair_lag_deg"] = 0.0
	p["left_brow_raise_px"] = 1.0
	p["right_brow_raise_px"] = 5.0
	p["brow_slant_deg"] = 2.5
	p["mouth_state"] = "smirk"
	# Arms: Left arm casual at flank, Right arm gesturing toward button
	p["left_shoulder_deg"] = 8.0
	p["left_elbow_deg"] = 16.0
	p["left_wrist_deg"] = 5.0
	p["left_hand_pose"] = "relaxed"
	p["right_shoulder_deg"] = 22.0
	p["right_elbow_deg"] = 38.0
	p["right_wrist_deg"] = -8.0
	p["right_hand_pose"] = "amused"
	# Legs: Relaxed, comfortable, appealing stance
	p["left_thigh_deg"] = 8.0
	p["left_shin_deg"] = -16.0
	p["left_foot_deg"] = 8.0
	p["right_thigh_deg"] = 10.0
	p["right_shin_deg"] = -18.0
	p["right_foot_deg"] = 8.0
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

# ===========================================================================
# PART 4: FUNCTIONAL MOVEMENT BREAKDOWNS
# ===========================================================================

# 1. Walking Breakdowns (Contact, Down, Passing, Up, Final Plant, Settled Stop)
static func get_walking_breakdowns() -> Array[Dictionary]:
	var p_contact = get_neutral_pose()
	p_contact["name"] = "Walk 1: Contact"
	p_contact["root_pos"] = Vector2(410.0, STANDING_Y)
	p_contact["torso_lean_deg"] = 6.0
	p_contact["right_thigh_deg"] = 28.0
	p_contact["right_shin_deg"] = -14.0
	p_contact["right_foot_deg"] = 18.0
	p_contact["left_thigh_deg"] = -16.0
	p_contact["left_shin_deg"] = -8.0
	p_contact["left_foot_deg"] = 6.0

	var p_down = get_neutral_pose()
	p_down["name"] = "Walk 2: Down"
	p_down["root_pos"] = Vector2(435.0, STANDING_Y + 14.0)
	p_down["torso_lean_deg"] = 5.0
	p_down["right_thigh_deg"] = 22.0
	p_down["right_shin_deg"] = -32.0
	p_down["right_foot_deg"] = 10.0
	p_down["left_thigh_deg"] = -8.0
	p_down["left_shin_deg"] = -20.0

	var p_passing = get_neutral_pose()
	p_passing["name"] = "Walk 3: Passing"
	p_passing["root_pos"] = Vector2(470.0, STANDING_Y - 12.0)
	p_passing["torso_lean_deg"] = 4.0
	p_passing["right_thigh_deg"] = 8.0
	p_passing["right_shin_deg"] = -12.0
	p_passing["left_thigh_deg"] = 26.0
	p_passing["left_shin_deg"] = -42.0

	var p_up = get_neutral_pose()
	p_up["name"] = "Walk 4: Up"
	p_up["root_pos"] = Vector2(505.0, STANDING_Y - 6.0)
	p_up["torso_lean_deg"] = 5.0
	p_up["right_thigh_deg"] = -14.0
	p_up["right_shin_deg"] = -6.0
	p_up["left_thigh_deg"] = 24.0
	p_up["left_shin_deg"] = -16.0

	var p_plant = get_neutral_pose()
	p_plant["name"] = "Walk 5: Plant"
	p_plant["root_pos"] = Vector2(535.0, STANDING_Y + 8.0)
	p_plant["torso_lean_deg"] = 4.0
	p_plant["left_thigh_deg"] = 18.0
	p_plant["left_shin_deg"] = -28.0
	p_plant["right_thigh_deg"] = 6.0
	p_plant["right_shin_deg"] = -12.0

	var p_settled = get_neutral_pose()
	p_settled["name"] = "Walk 6: Settled Stop"
	p_settled["root_pos"] = Vector2(540.0, STANDING_Y)
	p_settled["torso_lean_deg"] = 2.0
	p_settled["left_thigh_deg"] = 6.0
	p_settled["left_shin_deg"] = -10.0
	p_settled["right_thigh_deg"] = 8.0
	p_settled["right_shin_deg"] = -14.0

	return [p_contact, p_down, p_passing, p_up, p_plant, p_settled]

# 2. Reaching Breakdowns (Anticipation, Mid-Reach, Pre-Contact, Contact, Fully Depressed, Release)
static func get_reaching_breakdowns() -> Array[Dictionary]:
	var p_antic = get_neutral_pose()
	p_antic["name"] = "Reach 1: Anticipation"
	p_antic["root_pos"] = Vector2(540.0, STANDING_Y)
	p_antic["torso_lean_deg"] = 1.0
	p_antic["right_shoulder_deg"] = 12.0
	p_antic["right_elbow_deg"] = 22.0
	p_antic["head_tilt_deg"] = -1.0

	var p_mid = get_neutral_pose()
	p_mid["name"] = "Reach 2: Mid-Reach Arc"
	p_mid["root_pos"] = Vector2(540.0, STANDING_Y)
	p_mid["torso_lean_deg"] = 5.0
	p_mid["right_shoulder_deg"] = 28.0
	p_mid["right_elbow_deg"] = 55.0
	p_mid["right_wrist_deg"] = -14.0
	p_mid["right_hand_pose"] = "curious"

	var p_pre = get_neutral_pose()
	p_pre["name"] = "Reach 3: Pre-Contact"
	p_pre["root_pos"] = Vector2(540.0, STANDING_Y)
	p_pre["torso_lean_deg"] = 6.0
	p_pre["right_shoulder_deg"] = 24.0
	p_pre["right_elbow_deg"] = 46.0
	p_pre["right_wrist_deg"] = -16.0
	p_pre["right_hand_pose"] = "press"

	# Fingertip Contact (0px depression) -> matches exact button top at 759.85, 1206.45
	var p_contact = get_neutral_pose()
	p_contact["name"] = "Reach 4: Fingertip Contact"
	p_contact["root_pos"] = Vector2(540.0, STANDING_Y)
	p_contact["torso_lean_deg"] = 8.0
	p_contact["right_shoulder_protract_px"] = 10.0
	p_contact["right_shoulder_deg"] = 21.0
	p_contact["right_elbow_deg"] = 46.0
	p_contact["right_wrist_deg"] = -10.0
	p_contact["right_hand_pose"] = "press"
	p_contact["button_depress_px"] = 0.0

	# Fully Depressed Button (-8px depression) -> matches exact button down at 760.10, 1220.01
	var p_depressed = get_press_pose()
	p_depressed["name"] = "Reach 5: Depressed -8px"

	var p_release = get_neutral_pose()
	p_release["name"] = "Reach 6: Release"
	p_release["root_pos"] = Vector2(535.0, STANDING_Y)
	p_release["torso_lean_deg"] = 5.0
	p_release["right_shoulder_deg"] = 26.0
	p_release["right_elbow_deg"] = 38.0
	p_release["right_wrist_deg"] = -6.0
	p_release["right_hand_pose"] = "press"
	p_release["button_depress_px"] = 0.0

	return [p_antic, p_mid, p_pre, p_contact, p_depressed, p_release]

# 3. Surprise Breakdowns (Initial Startle, Torso Recoil, Rear Catch, Peak Surprise, First Recovery)
static func get_surprise_breakdowns() -> Array[Dictionary]:
	var p_startle = get_press_pose()
	p_startle["name"] = "Surprise 1: Startle"
	p_startle["torso_lean_deg"] = 2.0
	p_startle["shoulder_shrug_px"] = 12.0
	p_startle["head_tilt_deg"] = 4.0
	p_startle["right_shoulder_deg"] = 38.0
	p_startle["right_elbow_deg"] = 55.0
	p_startle["right_hand_pose"] = "recoil"
	p_startle["mouth_state"] = "open_gasp"

	var p_snap = get_surprise_pose()
	p_snap["name"] = "Surprise 2: Torso Recoil"
	p_snap["torso_lean_deg"] = -12.0
	p_snap["shoulder_shrug_px"] = 20.0
	p_snap["root_pos"] = Vector2(515.0, STANDING_Y)

	var p_catch = get_surprise_pose()
	p_catch["name"] = "Surprise 3: Rear Catch"
	p_catch["root_pos"] = Vector2(500.0, STANDING_Y - 4.0)
	p_catch["torso_lean_deg"] = -16.0
	p_catch["left_thigh_deg"] = -16.0
	p_catch["left_shin_deg"] = -30.0

	var p_peak = get_surprise_pose()
	p_peak["name"] = "Surprise 4: Peak Hold"

	var p_settle = get_surprise_pose()
	p_settle["name"] = "Surprise 5: First Recovery"
	p_settle["torso_lean_deg"] = -10.0
	p_settle["shoulder_shrug_px"] = 14.0
	p_settle["mouth_state"] = "curious_o"

	return [p_startle, p_snap, p_catch, p_peak, p_settle]

# 4. Recovery Breakdowns (Weight Redistribution, Shoulder Settle, Arm Lowering, Glasses Adjust, Final Amused)
static func get_recovery_breakdowns() -> Array[Dictionary]:
	var p_weight = get_neutral_pose()
	p_weight["name"] = "Recovery 1: Weight Shift"
	p_weight["root_pos"] = Vector2(515.0, STANDING_Y)
	p_weight["torso_lean_deg"] = -4.0
	p_weight["shoulder_shrug_px"] = 8.0
	p_weight["mouth_state"] = "curious_o"

	var p_sh_settle = get_neutral_pose()
	p_sh_settle["name"] = "Recovery 2: Shoulder Settle"
	p_sh_settle["root_pos"] = Vector2(520.0, STANDING_Y)
	p_sh_settle["torso_lean_deg"] = -2.0
	p_sh_settle["shoulder_shrug_px"] = 2.0
	p_sh_settle["mouth_state"] = "curious_o"

	var p_arm = get_neutral_pose()
	p_arm["name"] = "Recovery 3: Arm Lowering"
	p_arm["root_pos"] = Vector2(520.0, STANDING_Y)
	p_arm["left_shoulder_deg"] = 8.0
	p_arm["left_elbow_deg"] = 16.0
	p_arm["right_shoulder_deg"] = 26.0
	p_arm["right_elbow_deg"] = -80.0
	p_arm["right_hand_pose"] = "chin_touch"

	var p_glasses = get_neutral_pose()
	p_glasses["name"] = "Recovery 4: Glasses Adjust"
	p_glasses["root_pos"] = Vector2(520.0, STANDING_Y)
	p_glasses["head_tilt_deg"] = 4.0
	p_glasses["right_shoulder_deg"] = 32.0
	p_glasses["right_elbow_deg"] = -125.0
	p_glasses["right_wrist_deg"] = 28.0
	p_glasses["right_hand_pose"] = "chin_touch"
	p_glasses["mouth_state"] = "smirk"

	var p_final = get_satisfaction_pose()
	p_final["name"] = "Recovery 5: Final Amused Pose"

	return [p_weight, p_sh_settle, p_arm, p_glasses, p_final]

static func apply_pose_to_rig(rig: Node2D, pose: Dictionary) -> void:
	for prop in pose:
		if prop in ["name", "label", "subtitle", "description"]:
			continue
		if prop in rig:
			rig.set(prop, pose[prop])
