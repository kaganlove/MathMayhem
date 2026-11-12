class_name AnimationBuilder
extends RefCounted

## Math Mayhem v11.0 — Master Animation Builder & Track Authoring Engine
## Authors professional Godot Animation resources featuring:
## 1. Staggered keyframe timing (Overlapping Action)
## 2. Independent track curves (Cubic Bézier vs Stepped Blocking)
## 3. Physical button interaction and depression
## 4. Volume-preserving squash & stretch

const STANDING_Y: float = 1285.8

static func create_mysterious_button_animation(is_stepped: bool = false) -> Animation:
	var anim: Animation = Animation.new()
	anim.length = 10.0
	var interp_mode = Animation.INTERPOLATION_NEAREST if is_stepped else Animation.INTERPOLATION_CUBIC

	# Setup all property tracks
	var tracks: Dictionary = {}
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

	for prop in track_names:
		var idx = anim.add_track(Animation.TYPE_VALUE)
		anim.track_set_path(idx, prop)
		# String properties (mouth_state, hand_pose, bools) are always discrete nearest
		if "mouth_state" in prop or "hand_pose" in prop or "show_button" in prop:
			anim.track_set_interpolation_type(idx, Animation.INTERPOLATION_NEAREST)
		else:
			anim.track_set_interpolation_type(idx, interp_mode)
		tracks[prop] = idx

	# Always show the button pedestal throughout the scene
	_k(anim, tracks["CharacterRig:show_button_pedestal"], 0.0, true)

	# =======================================================================
	# Beat 1 — Discovery & Curious Notice (0.0s - 1.5s)
	# =======================================================================
	# Initial Neutral Idle
	_k(anim, tracks["CharacterRig:root_pos"], 0.0, Vector2(380.0, STANDING_Y))
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 0.0, 1.0)
	_k(anim, tracks["CharacterRig:spine_arch_deg"], 0.0, 3.0)
	_k(anim, tracks["CharacterRig:torso_squash"], 0.0, 1.0)
	_k(anim, tracks["CharacterRig:shoulder_shrug_px"], 0.0, 0.0)
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 0.0, 0.5)
	_k(anim, tracks["CharacterRig:head_nod_px"], 0.0, 0.0)
	_k(anim, tracks["CharacterRig:head_squash"], 0.0, 1.0)
	_k(anim, tracks["CharacterRig:yaw_factor"], 0.0, 0.20)
	_k(anim, tracks["CharacterRig:glasses_slip_px"], 0.0, 0.0)
	_k(anim, tracks["CharacterRig:hair_lag_deg"], 0.0, 0.0)
	_k(anim, tracks["CharacterRig:left_brow_raise_px"], 0.0, 0.0)
	_k(anim, tracks["CharacterRig:right_brow_raise_px"], 0.0, 0.0)
	_k(anim, tracks["CharacterRig:brow_slant_deg"], 0.0, 0.0)
	_k(anim, tracks["CharacterRig:mouth_state"], 0.0, "neutral")
	_k(anim, tracks["CharacterRig:left_shoulder_deg"], 0.0, 4.0)
	_k(anim, tracks["CharacterRig:left_elbow_deg"], 0.0, 12.0)
	_k(anim, tracks["CharacterRig:left_wrist_deg"], 0.0, 5.0)
	_k(anim, tracks["CharacterRig:left_hand_pose"], 0.0, "relaxed")
	_k(anim, tracks["CharacterRig:right_shoulder_deg"], 0.0, 6.0)
	_k(anim, tracks["CharacterRig:right_elbow_deg"], 0.0, 12.0)
	_k(anim, tracks["CharacterRig:right_wrist_deg"], 0.0, 5.0)
	_k(anim, tracks["CharacterRig:right_hand_pose"], 0.0, "relaxed")
	_k(anim, tracks["CharacterRig:left_thigh_deg"], 0.0, 14.0)
	_k(anim, tracks["CharacterRig:left_shin_deg"], 0.0, -28.0)
	_k(anim, tracks["CharacterRig:left_foot_deg"], 0.0, 14.0)
	_k(anim, tracks["CharacterRig:right_thigh_deg"], 0.0, 14.0)
	_k(anim, tracks["CharacterRig:right_shin_deg"], 0.0, -28.0)
	_k(anim, tracks["CharacterRig:right_foot_deg"], 0.0, 14.0)
	_k(anim, tracks["CharacterRig:button_depress_px"], 0.0, 0.0)
	_k(anim, tracks["CharacterRig:button_glow_alpha"], 0.0, 0.0)

	# 0.5s - 1.0s: Staggered Notice (Eye dart -> Head dip -> Head turn -> Brow arch)
	_k(anim, tracks["CharacterRig:yaw_factor"], 0.50, 0.20)
	_k(anim, tracks["CharacterRig:yaw_factor"], 0.75, 0.35) # Eye darts right
	_k(anim, tracks["CharacterRig:head_nod_px"], 0.60, 0.0)
	_k(anim, tracks["CharacterRig:head_nod_px"], 0.72, 3.5)  # Anticipation dip
	_k(anim, tracks["CharacterRig:head_squash"], 0.72, 0.94) # Anticipation squash
	_k(anim, tracks["CharacterRig:head_nod_px"], 0.95, -2.5) # Head lifts
	_k(anim, tracks["CharacterRig:head_squash"], 0.95, 1.03)
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 0.65, 0.5)
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 0.95, -4.5) # Head tilts toward button
	_k(anim, tracks["CharacterRig:right_brow_raise_px"], 0.70, 0.0)
	_k(anim, tracks["CharacterRig:right_brow_raise_px"], 0.95, 4.5) # Quizzical arch
	_k(anim, tracks["CharacterRig:brow_slant_deg"], 0.95, 3.0)
	_k(anim, tracks["CharacterRig:mouth_state"], 0.80, "curious_o")
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 0.75, 1.0)
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 1.10, 4.0) # Torso follows slightly
	
	# 1.1s - 1.5s: Hold curious discovery pose

	# =======================================================================
	# Beat 2 — Approach Toward Pedestal (1.5s - 3.5s)
	# =======================================================================
	# Two deliberate, weight-balanced steps from x=380 to x=540
	# Step 1 (1.5s - 2.4s): Right leg leads
	_k(anim, tracks["CharacterRig:root_pos"], 1.5, Vector2(380.0, STANDING_Y))
	_k(anim, tracks["CharacterRig:root_pos"], 1.7, Vector2(415.0, STANDING_Y + 18.0)) # Down / Recoil
	_k(anim, tracks["CharacterRig:torso_squash"], 1.7, 0.94)
	_k(anim, tracks["CharacterRig:root_pos"], 2.0, Vector2(455.0, STANDING_Y - 14.0)) # Up / Push-off
	_k(anim, tracks["CharacterRig:torso_squash"], 2.0, 1.04)
	_k(anim, tracks["CharacterRig:root_pos"], 2.4, Vector2(485.0, STANDING_Y))

	# Step 1 Leg rotations
	_k(anim, tracks["CharacterRig:right_thigh_deg"], 1.5, 14.0)
	_k(anim, tracks["CharacterRig:right_thigh_deg"], 1.7, 24.0)
	_k(anim, tracks["CharacterRig:right_shin_deg"], 1.7, -12.0)
	_k(anim, tracks["CharacterRig:right_thigh_deg"], 2.0, 8.0)
	_k(anim, tracks["CharacterRig:right_shin_deg"], 2.0, -38.0) # Passing foot clearance
	_k(anim, tracks["CharacterRig:right_thigh_deg"], 2.4, 26.0)
	_k(anim, tracks["CharacterRig:right_shin_deg"], 2.4, -20.0)

	# Step 2 (2.4s - 3.3s): Left leg leads into planted stop at x=540
	_k(anim, tracks["CharacterRig:root_pos"], 2.6, Vector2(510.0, STANDING_Y + 16.0))
	_k(anim, tracks["CharacterRig:root_pos"], 2.9, Vector2(530.0, STANDING_Y - 10.0))
	_k(anim, tracks["CharacterRig:root_pos"], 3.3, Vector2(540.0, STANDING_Y))
	_k(anim, tracks["CharacterRig:torso_squash"], 3.3, 1.0)

	# Planted forward stance at x=540
	_k(anim, tracks["CharacterRig:left_thigh_deg"], 3.3, 12.0)
	_k(anim, tracks["CharacterRig:left_shin_deg"], 3.3, -24.0)
	_k(anim, tracks["CharacterRig:right_thigh_deg"], 3.3, 20.0)
	_k(anim, tracks["CharacterRig:right_shin_deg"], 3.3, -34.0)

	# Arm begins reaching toward button
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 3.0, 4.0)
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 3.5, 7.5) # Leans in toward button
	_k(anim, tracks["CharacterRig:right_shoulder_deg"], 2.8, 8.0)
	_k(anim, tracks["CharacterRig:right_shoulder_deg"], 3.5, 48.0) # Arm extends forward
	_k(anim, tracks["CharacterRig:right_elbow_deg"], 3.5, 22.0)
	_k(anim, tracks["CharacterRig:right_wrist_deg"], 3.5, -6.0)
	_k(anim, tracks["CharacterRig:right_hand_pose"], 3.2, "point")

	# =======================================================================
	# Beat 3 — Hesitation & Uncertainty (3.5s - 5.0s)
	# =======================================================================
	# Reaching hand halts 30px before button cap
	_k(anim, tracks["CharacterRig:right_shoulder_deg"], 3.7, 52.0)
	_k(anim, tracks["CharacterRig:right_shoulder_deg"], 3.9, 49.0) # Slight hesitation pull-back
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 3.9, 5.5)

	# Head cocks sideways in doubt ("Should I really press this?")
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 3.7, -4.5)
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 4.2, 7.0) # Sideways confusion cock
	_k(anim, tracks["CharacterRig:left_brow_raise_px"], 4.0, -2.0) # Inner furrow
	_k(anim, tracks["CharacterRig:right_brow_raise_px"], 4.0, 5.5)  # Raised arch
	_k(anim, tracks["CharacterRig:brow_slant_deg"], 4.0, -4.0)
	_k(anim, tracks["CharacterRig:mouth_state"], 3.9, "confused")

	# 4.2s - 4.8s: Comedic Hesitation Hold (hand hovers, character ponders)
	_k(anim, tracks["CharacterRig:right_wrist_deg"], 4.2, -6.0)
	_k(anim, tracks["CharacterRig:right_wrist_deg"], 4.5, -4.0) # Subtle trembling hover
	_k(anim, tracks["CharacterRig:right_wrist_deg"], 4.8, -6.0)

	# =======================================================================
	# Beat 4 — Decision & Physical Contact (5.0s - 6.5s)
	# =======================================================================
	# 5.0s - 5.3s: Decisive commitment: posture straightens, confident brow
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 5.0, 7.0)
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 5.3, -2.5) # Head snaps into focus
	_k(anim, tracks["CharacterRig:left_brow_raise_px"], 5.3, 1.0)
	_k(anim, tracks["CharacterRig:right_brow_raise_px"], 5.3, 3.0)
	_k(anim, tracks["CharacterRig:brow_slant_deg"], 5.3, 1.5)
	_k(anim, tracks["CharacterRig:mouth_state"], 5.2, "smirk")

	# Torso recoil anticipation before press
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 5.1, 5.5)
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 5.3, 3.0) # Subtle pull-back
	_k(anim, tracks["CharacterRig:right_shoulder_deg"], 5.3, 44.0)

	# 5.3s - 5.6s: Thrust forward into contact!
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 5.6, 9.5)
	_k(anim, tracks["CharacterRig:right_shoulder_protract_px"], 5.3, 0.0)
	_k(anim, tracks["CharacterRig:right_shoulder_protract_px"], 5.6, 10.0) # Protracts into contact
	_k(anim, tracks["CharacterRig:right_shoulder_deg"], 5.6, 68.0)
	_k(anim, tracks["CharacterRig:right_elbow_deg"], 5.6, 10.0)
	_k(anim, tracks["CharacterRig:right_wrist_deg"], 5.6, -2.0)

	# 5.6s - 6.4s: PHYSICAL BUTTON DEPRESSION!
	_k(anim, tracks["CharacterRig:button_depress_px"], 5.55, 0.0)
	_k(anim, tracks["CharacterRig:button_depress_px"], 5.70, 8.0) # Button presses down 8px
	_k(anim, tracks["CharacterRig:button_depress_px"], 6.40, 8.0) # Held firmly down

	# =======================================================================
	# Beat 5 & 6 — Consequence & Explosive Recoil (6.5s - 8.2s)
	# =======================================================================
	# 6.50s: Button Activation Flash Burst!
	_k(anim, tracks["CharacterRig:button_glow_alpha"], 6.45, 0.0)
	_k(anim, tracks["CharacterRig:button_glow_alpha"], 6.52, 1.0) # Peak brilliant flash
	_k(anim, tracks["CharacterRig:button_glow_alpha"], 6.75, 0.6)
	_k(anim, tracks["CharacterRig:button_glow_alpha"], 7.30, 0.0)

	# 6.52s - 6.80s: Sudden Explosive Shock Recoil!
	_k(anim, tracks["CharacterRig:mouth_state"], 6.52, "open_gasp")
	_k(anim, tracks["CharacterRig:left_brow_raise_px"], 6.52, 1.0)
	_k(anim, tracks["CharacterRig:left_brow_raise_px"], 6.65, 16.0) # Brows shoot up
	_k(anim, tracks["CharacterRig:right_brow_raise_px"], 6.65, 16.0)

	# Whole-body recoil backward
	_k(anim, tracks["CharacterRig:root_pos"], 6.50, Vector2(540.0, STANDING_Y))
	_k(anim, tracks["CharacterRig:root_pos"], 6.72, Vector2(508.0, STANDING_Y - 10.0))
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 6.50, 9.5)
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 6.70, -12.5) # Snaps backward
	_k(anim, tracks["CharacterRig:spine_arch_deg"], 6.70, -7.0)
	_k(anim, tracks["CharacterRig:torso_squash"], 6.70, 1.08) # Stretch in shock
	_k(anim, tracks["CharacterRig:shoulder_shrug_px"], 6.50, 0.0)
	_k(anim, tracks["CharacterRig:shoulder_shrug_px"], 6.70, 22.0) # Shrugs up 22px
	_k(anim, tracks["CharacterRig:right_shoulder_protract_px"], 6.70, 0.0)

	# Head snap & secondary dynamics
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 6.50, -2.5)
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 6.70, 12.0)
	_k(anim, tracks["CharacterRig:hair_lag_deg"], 6.50, 0.0)
	_k(anim, tracks["CharacterRig:hair_lag_deg"], 6.72, -26.0) # Hair whips back
	_k(anim, tracks["CharacterRig:glasses_slip_px"], 6.50, 0.0)
	_k(anim, tracks["CharacterRig:glasses_slip_px"], 6.75, 6.5) # Glasses slip down nose

	# Arms flung wide in terror
	_k(anim, tracks["CharacterRig:right_shoulder_deg"], 6.50, 68.0)
	_k(anim, tracks["CharacterRig:right_shoulder_deg"], 6.72, 58.0)
	_k(anim, tracks["CharacterRig:right_elbow_deg"], 6.72, 82.0)
	_k(anim, tracks["CharacterRig:right_wrist_deg"], 6.72, -32.0)
	_k(anim, tracks["CharacterRig:right_hand_pose"], 6.55, "reach_open")
	_k(anim, tracks["CharacterRig:left_shoulder_deg"], 6.72, 52.0)
	_k(anim, tracks["CharacterRig:left_elbow_deg"], 6.72, 74.0)
	_k(anim, tracks["CharacterRig:left_wrist_deg"], 6.72, -26.0)
	_k(anim, tracks["CharacterRig:left_hand_pose"], 6.55, "reach_open")

	# Button pops back up after release
	_k(anim, tracks["CharacterRig:button_depress_px"], 6.55, 8.0)
	_k(anim, tracks["CharacterRig:button_depress_px"], 6.70, 0.0)

	# 6.75s - 7.60s: COMEDIC FROZEN SHOCK HOLD (0.85s motionless terrified hold)
	_k(anim, tracks["CharacterRig:hair_lag_deg"], 7.40, -18.0)

	# =======================================================================
	# Beat 7 — Staggered Recovery & Intrigued Smirk (7.6s - 10.0s)
	# =======================================================================
	# 7.6s - 8.3s: Shoulders drop, torso eases forward
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 7.6, -12.5)
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 8.3, -2.0)
	_k(anim, tracks["CharacterRig:spine_arch_deg"], 8.3, 3.0)
	_k(anim, tracks["CharacterRig:torso_squash"], 8.3, 1.0)
	_k(anim, tracks["CharacterRig:shoulder_shrug_px"], 7.6, 22.0)
	_k(anim, tracks["CharacterRig:shoulder_shrug_px"], 8.3, 4.0)
	_k(anim, tracks["CharacterRig:left_brow_raise_px"], 8.3, 3.0)
	_k(anim, tracks["CharacterRig:right_brow_raise_px"], 8.3, 4.0)
	_k(anim, tracks["CharacterRig:mouth_state"], 8.0, "curious_o")

	# 8.3s - 9.1s: Right hand reaches up and pushes glasses back up bridge
	_k(anim, tracks["CharacterRig:right_shoulder_deg"], 8.3, 28.0)
	_k(anim, tracks["CharacterRig:right_shoulder_deg"], 8.7, 34.0)
	_k(anim, tracks["CharacterRig:right_elbow_deg"], 8.7, -125.0) # Reaches up to glasses
	_k(anim, tracks["CharacterRig:right_wrist_deg"], 8.7, 30.0)
	_k(anim, tracks["CharacterRig:right_hand_pose"], 8.5, "chin_touch")
	_k(anim, tracks["CharacterRig:glasses_slip_px"], 8.7, 6.5)
	_k(anim, tracks["CharacterRig:glasses_slip_px"], 9.1, 0.0) # Pushes glasses back into place!

	# Left arm relaxes to flank
	_k(anim, tracks["CharacterRig:left_shoulder_deg"], 8.3, 30.0)
	_k(anim, tracks["CharacterRig:left_shoulder_deg"], 8.8, 6.0)
	_k(anim, tracks["CharacterRig:left_elbow_deg"], 8.8, 12.0)
	_k(anim, tracks["CharacterRig:left_hand_pose"], 8.5, "relaxed")

	# 9.1s - 10.0s: Final amused intrigued smirk & comfortable stance
	_k(anim, tracks["CharacterRig:right_shoulder_deg"], 9.1, 34.0)
	_k(anim, tracks["CharacterRig:right_shoulder_deg"], 9.6, 8.0) # Hand settles to flank
	_k(anim, tracks["CharacterRig:right_elbow_deg"], 9.6, 14.0)
	_k(anim, tracks["CharacterRig:right_wrist_deg"], 9.6, 5.0)
	_k(anim, tracks["CharacterRig:right_hand_pose"], 9.4, "relaxed")
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 8.7, 8.0)
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 9.5, -2.5) # Head cocks with amused smirk
	_k(anim, tracks["CharacterRig:hair_lag_deg"], 9.2, 0.0)
	_k(anim, tracks["CharacterRig:mouth_state"], 8.8, "smirk")
	_k(anim, tracks["CharacterRig:left_brow_raise_px"], 9.4, 1.0)
	_k(anim, tracks["CharacterRig:right_brow_raise_px"], 9.4, 3.5)
	_k(anim, tracks["CharacterRig:brow_slant_deg"], 9.4, 2.0)
	_k(anim, tracks["CharacterRig:shoulder_shrug_px"], 9.5, 0.0)

	# End hold at 10.0s
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 10.0, -1.0)
	_k(anim, tracks["CharacterRig:root_pos"], 10.0, Vector2(512.0, STANDING_Y))

	return anim

# Helper function to insert keyframe
static func _k(anim: Animation, track_idx: int, time: float, value: Variant) -> void:
	anim.track_insert_key(track_idx, time, value)
