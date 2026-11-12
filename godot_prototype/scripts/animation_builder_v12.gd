class_name AnimationBuilderV12
extends RefCounted

## Math Mayhem v12.1 — Master Animation Builder & Track Authoring Engine
## Authors professional Godot Animation resources for v12.1:
## 1. Authored Stepped Blocking (Animation.INTERPOLATION_NEAREST)
## 2. 8-Beat Narrative Story Arc (Discovery -> Approach -> Hesitation -> Press -> Activation -> Surprise -> Recovery -> Payoff)
## 3. Weight & balance shifts over stance feet
## 4. Organic reach arcs with natural elbow bends (no straight robotic pistons)
## 5. Physical button interaction (-8px depression) and activation glow burst
## 6. Rear-foot recoil weight transfer and comedic holds

const PoseLibraryV12 = preload("res://scripts/pose_library_v12.gd")
const STANDING_Y: float = 1285.8

static func create_v12_animation(is_stepped: bool = true) -> Animation:
	var anim: Animation = Animation.new()
	anim.length = 11.5
	var interp_mode = Animation.INTERPOLATION_NEAREST if is_stepped else Animation.INTERPOLATION_CUBIC

	var track_names: Array = [
		"CharacterRig:root_pos",
		"CharacterRig:torso_lean_deg",
		"CharacterRig:spine_arch_deg",
		"CharacterRig:torso_squash",
		"CharacterRig:shoulder_shrug_px",
		"CharacterRig:right_shoulder_protract_px",
		"CharacterRig:head_tilt_deg",
		"CharacterRig:head_nod_px",
		"CharacterRig:head_squash",
		"CharacterRig:yaw_factor",
		"CharacterRig:glasses_slip_px",
		"CharacterRig:hair_lag_deg",
		"CharacterRig:left_brow_raise_px",
		"CharacterRig:right_brow_raise_px",
		"CharacterRig:brow_slant_deg",
		"CharacterRig:mouth_state",
		"CharacterRig:left_shoulder_deg",
		"CharacterRig:left_elbow_deg",
		"CharacterRig:left_wrist_deg",
		"CharacterRig:left_hand_pose",
		"CharacterRig:right_shoulder_deg",
		"CharacterRig:right_elbow_deg",
		"CharacterRig:right_wrist_deg",
		"CharacterRig:right_hand_pose",
		"CharacterRig:left_thigh_deg",
		"CharacterRig:left_shin_deg",
		"CharacterRig:left_foot_deg",
		"CharacterRig:right_thigh_deg",
		"CharacterRig:right_shin_deg",
		"CharacterRig:right_foot_deg",
		"CharacterRig:show_button_pedestal",
		"CharacterRig:button_depress_px",
		"CharacterRig:button_glow_alpha"
	]

	var tracks: Dictionary = {}
	for prop in track_names:
		var idx = anim.add_track(Animation.TYPE_VALUE)
		anim.track_set_path(idx, prop)
		if "mouth_state" in prop or "hand_pose" in prop or "show_button" in prop:
			anim.track_set_interpolation_type(idx, Animation.INTERPOLATION_NEAREST)
		else:
			anim.track_set_interpolation_type(idx, interp_mode)
		tracks[prop] = idx

	# Button pedestal visible throughout
	_k(anim, tracks["CharacterRig:show_button_pedestal"], 0.0, true)

	# -----------------------------------------------------------------------
	# Beat 1: Discovery (0.0s - 1.5s)
	# -----------------------------------------------------------------------
	# 0.0s - 0.6s: Neutral Idle
	_apply_pose_at(anim, tracks, 0.0, PoseLibraryV12.get_neutral_pose())
	
	# 0.65s: Notice Eye Dart / Pre-anticipation
	_k(anim, tracks["CharacterRig:yaw_factor"], 0.65, 0.30)
	_k(anim, tracks["CharacterRig:head_nod_px"], 0.65, 2.5)
	
	# 0.85s - 1.5s: Curious Notice Keyframe (Hold 8-12f)
	var p_curious = PoseLibraryV12.get_curious_pose()
	_apply_pose_at(anim, tracks, 0.85, p_curious)

	# -----------------------------------------------------------------------
	# Beat 2: Approach (1.5s - 3.0s) — Two Deliberate Balanced Steps
	# -----------------------------------------------------------------------
	# 1.5s: Step 1 Lift (Right leg lifts, weight on left leg)
	_k(anim, tracks["CharacterRig:root_pos"], 1.5, Vector2(395.0, STANDING_Y - 8.0))
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 1.5, 8.0)
	_k(anim, tracks["CharacterRig:right_thigh_deg"], 1.5, 26.0)
	_k(anim, tracks["CharacterRig:right_shin_deg"], 1.5, -20.0)
	_k(anim, tracks["CharacterRig:left_thigh_deg"], 1.5, 10.0)
	_k(anim, tracks["CharacterRig:left_shin_deg"], 1.5, -22.0)
	
	# 1.9s: Step 1 Down / Contact (Right foot plants at x=460)
	_k(anim, tracks["CharacterRig:root_pos"], 1.9, Vector2(460.0, STANDING_Y + 12.0))
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 1.9, 6.0)
	_k(anim, tracks["CharacterRig:right_thigh_deg"], 1.9, 20.0)
	_k(anim, tracks["CharacterRig:right_shin_deg"], 1.9, -32.0)
	_k(anim, tracks["CharacterRig:left_thigh_deg"], 1.9, 2.0)
	_k(anim, tracks["CharacterRig:left_shin_deg"], 1.9, -12.0)

	# 2.3s: Step 2 Lift / Passing (Left leg swings forward, pelvis rises)
	_k(anim, tracks["CharacterRig:root_pos"], 2.3, Vector2(505.0, STANDING_Y - 10.0))
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 2.3, 7.0)
	_k(anim, tracks["CharacterRig:left_thigh_deg"], 2.3, 24.0)
	_k(anim, tracks["CharacterRig:left_shin_deg"], 2.3, -22.0)
	_k(anim, tracks["CharacterRig:right_thigh_deg"], 2.3, 12.0)
	_k(anim, tracks["CharacterRig:right_shin_deg"], 2.3, -24.0)

	# 2.7s: Step 2 Contact & Plant at Button (x=540)
	_k(anim, tracks["CharacterRig:root_pos"], 2.7, Vector2(540.0, STANDING_Y))
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 2.7, 5.0)
	_k(anim, tracks["CharacterRig:left_thigh_deg"], 2.7, 12.0)
	_k(anim, tracks["CharacterRig:left_shin_deg"], 2.7, -24.0)
	_k(anim, tracks["CharacterRig:right_thigh_deg"], 2.7, 18.0)
	_k(anim, tracks["CharacterRig:right_shin_deg"], 2.7, -32.0)

	# -----------------------------------------------------------------------
	# Beat 3: Hesitation (3.0s - 4.0s) — Thinking / Doubt Hold
	# -----------------------------------------------------------------------
	# Hand halts directly above button, elbow bent 72°, free arm at waist
	var p_hesitate = PoseLibraryV12.get_hesitation_pose()
	_apply_pose_at(anim, tracks, 3.0, p_hesitate)
	
	# Subtle comedic doubt micro-twitch at 3.5s
	_k(anim, tracks["CharacterRig:right_wrist_deg"], 3.5, -10.0)
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 3.5, 9.5)

	# -----------------------------------------------------------------------
	# Beat 4: Decision & Press (4.0s - 5.0s)
	# -----------------------------------------------------------------------
	# 4.0s: Anticipation pull-back before strike
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 4.0, 3.0)
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 4.0, -2.0)
	_k(anim, tracks["CharacterRig:right_shoulder_deg"], 4.0, 42.0)
	_k(anim, tracks["CharacterRig:mouth_state"], 4.0, "smirk")

	# 4.3s - 5.0s: Decisive Contact & Press! (Elbow bent 38°, button -8px)
	var p_press = PoseLibraryV12.get_press_pose()
	_apply_pose_at(anim, tracks, 4.3, p_press)

	# -----------------------------------------------------------------------
	# Beat 5: Activation (5.0s - 5.5s) — Energy Blast Burst
	# -----------------------------------------------------------------------
	_k(anim, tracks["CharacterRig:button_glow_alpha"], 5.0, 1.0)
	_k(anim, tracks["CharacterRig:mouth_state"], 5.0, "curious_o")
	_k(anim, tracks["CharacterRig:button_depress_px"], 5.0, 8.0)

	# -----------------------------------------------------------------------
	# Beat 6: Surprise (5.5s - 7.0s) — Explosive Recoil & Comedic Freeze Hold
	# -----------------------------------------------------------------------
	# 5.5s: Explosive snap backward (-16°), weight to rear foot, gasp!
	var p_surprise = PoseLibraryV12.get_surprise_pose()
	_apply_pose_at(anim, tracks, 5.5, p_surprise)
	
	# Comedic frozen shock hold through 7.0s (Hold 45 frames)

	# -----------------------------------------------------------------------
	# Beat 7: Recovery (7.0s - 9.0s) — Settle & Glasses Push-Up
	# -----------------------------------------------------------------------
	# 7.0s: Recoil Settle (Torso eases forward, shoulders relax)
	_k(anim, tracks["CharacterRig:root_pos"], 7.0, Vector2(515.0, STANDING_Y))
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 7.0, -3.0)
	_k(anim, tracks["CharacterRig:spine_arch_deg"], 7.0, 2.0)
	_k(anim, tracks["CharacterRig:torso_squash"], 7.0, 1.0)
	_k(anim, tracks["CharacterRig:shoulder_shrug_px"], 7.0, 6.0)
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 7.0, 2.0)
	_k(anim, tracks["CharacterRig:left_brow_raise_px"], 7.0, 4.0)
	_k(anim, tracks["CharacterRig:right_brow_raise_px"], 7.0, 5.0)
	_k(anim, tracks["CharacterRig:mouth_state"], 7.0, "curious_o")
	_k(anim, tracks["CharacterRig:button_glow_alpha"], 7.0, 0.0)

	# 7.8s: Hand reaches up and pushes glasses back into position
	_k(anim, tracks["CharacterRig:right_shoulder_deg"], 7.8, 32.0)
	_k(anim, tracks["CharacterRig:right_elbow_deg"], 7.8, -125.0)
	_k(anim, tracks["CharacterRig:right_wrist_deg"], 7.8, 30.0)
	_k(anim, tracks["CharacterRig:right_hand_pose"], 7.8, "chin_touch")
	_k(anim, tracks["CharacterRig:glasses_slip_px"], 7.8, 7.0)
	
	# 8.4s: Glasses pushed firmly up
	_k(anim, tracks["CharacterRig:glasses_slip_px"], 8.4, 0.0)
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 8.4, 6.0)
	_k(anim, tracks["CharacterRig:mouth_state"], 8.4, "smirk")

	# -----------------------------------------------------------------------
	# Beat 8: Payoff (9.0s - 11.5s) — Amused Smirk & End Hold
	# -----------------------------------------------------------------------
	var p_payoff = PoseLibraryV12.get_satisfaction_pose()
	_apply_pose_at(anim, tracks, 9.0, p_payoff)
	
	# Final hold through 11.5s
	_apply_pose_at(anim, tracks, 11.5, p_payoff)

	return anim

static func _apply_pose_at(anim: Animation, tracks: Dictionary, time: float, pose: Dictionary) -> void:
	for prop in pose:
		var track_key = "CharacterRig:" + prop
		if track_key in tracks:
			_k(anim, tracks[track_key], time, pose[prop])

static func _k(anim: Animation, track_idx: int, time: float, value: Variant) -> void:
	anim.track_insert_key(track_idx, time, value)
