class_name AnimationBuilderV12
extends RefCounted

## Math Mayhem v12.2 — Master Animation Builder & Track Authoring Engine
## Authors professional Godot Animation resources for v12.2:
## 1. Stepped Blocking (Animation.INTERPOLATION_NEAREST) with Authored Functional Breakdowns
## 2. Paced 11.0s Story Arc (Notice -> Walk Breakdown -> Hesitate -> Reach & Contact -> Activation -> Recoil Catch -> Recovery -> Amused Payoff)
## 3. Planted support-foot locking (drift <= 0.1% character height)
## 4. Shared button contact target with mathematical fingertip alignment (0.1px precision)
## 5. Controlled non-obscuring activation energy pulse
## 6. Rear-foot recoil weight transfer and comedic timing

const PoseLibraryV12 = preload("res://scripts/pose_library_v12.gd")
const STANDING_Y: float = 1285.8

static func create_v12_animation(is_stepped: bool = true) -> Animation:
	var anim: Animation = Animation.new()
	anim.length = 11.0
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
	# Beat 1: Establish & Notice (0.0s - 1.2s)
	# -----------------------------------------------------------------------
	# 0.0s - 0.5s: Calm neutral stance, attention slightly forward
	_apply_pose_at(anim, tracks, 0.0, PoseLibraryV12.get_neutral_pose())
	
	# 0.5s: Attention shift starts (head leads, eye dart)
	_k(anim, tracks["CharacterRig:yaw_factor"], 0.5, 0.28)
	_k(anim, tracks["CharacterRig:head_nod_px"], 0.5, 2.0)
	
	# 0.75s - 1.2s: Curious Notice Keyframe (Hold 14 frames)
	_apply_pose_at(anim, tracks, 0.75, PoseLibraryV12.get_curious_pose())

	# -----------------------------------------------------------------------
	# Beat 2: Approach & Stop (1.2s - 2.8s) — Full Walking Breakdown Sequence
	# -----------------------------------------------------------------------
	var walks = PoseLibraryV12.get_walking_breakdowns()
	# 1.20s: Walk 1 - Contact (Right heel strikes at x=410)
	_apply_pose_at(anim, tracks, 1.20, walks[0])
	# 1.45s: Walk 2 - Down (Shock absorption, pelvis drops at x=435)
	_apply_pose_at(anim, tracks, 1.45, walks[1])
	# 1.75s: Walk 3 - Passing (Left leg swings past stance leg at x=470)
	_apply_pose_at(anim, tracks, 1.75, walks[2])
	# 2.05s: Walk 4 - Up (Right push-off onto left swing foot at x=505)
	_apply_pose_at(anim, tracks, 2.05, walks[3])
	# 2.35s: Walk 5 - Plant (Left foot plants at x=535)
	_apply_pose_at(anim, tracks, 2.35, walks[4])
	# 2.60s - 2.80s: Walk 6 - Settled Stop (Firm bilateral ground lock at x=540)
	_apply_pose_at(anim, tracks, 2.60, walks[5])

	# -----------------------------------------------------------------------
	# Beat 3: Investigate & Hesitate (2.8s - 4.0s) — Comedic Doubt Hold
	# -----------------------------------------------------------------------
	# Hand hovers 28px directly above button (elbow 44°), left hand on hip, head cocked (+10°)
	_apply_pose_at(anim, tracks, 2.80, PoseLibraryV12.get_hesitation_pose())
	
	# Subtle comedic doubt micro-twitch at 3.4s (held through 4.0s)
	_k(anim, tracks["CharacterRig:right_wrist_deg"], 3.4, -18.0)
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 3.4, 11.5)

	# -----------------------------------------------------------------------
	# Beat 4: Decision & Press (4.0s - 4.8s) — Full Reaching & Contact Breakdowns
	# -----------------------------------------------------------------------
	var reaches = PoseLibraryV12.get_reaching_breakdowns()
	# 4.00s: Reach 1 - Shoulder Anticipation (Gathers decisive focus)
	_apply_pose_at(anim, tracks, 4.00, reaches[0])
	# 4.15s: Reach 2 - Mid-Reach Arc (Shoulder drives forward, hand rises in arc)
	_apply_pose_at(anim, tracks, 4.15, reaches[1])
	# 4.30s: Reach 3 - Pre-Contact (Fingertip hovers 6px above button cap)
	_apply_pose_at(anim, tracks, 4.30, reaches[2])
	# 4.40s: Reach 4 - Initial Fingertip Contact (Touch at y=1206.4, 0px depression)
	_apply_pose_at(anim, tracks, 4.40, reaches[3])
	# 4.50s - 4.80s: Reach 5 - Fully Depressed Button (-8px depression, held 9 frames)
	_apply_pose_at(anim, tracks, 4.50, reaches[4])

	# -----------------------------------------------------------------------
	# Beat 5: Activation (4.8s - 5.2s) — Controlled Non-Obscuring Pulse
	# -----------------------------------------------------------------------
	# 4.80s: Button cap lights up with energy pulse, small sparks radiate away from bezel
	_k(anim, tracks["CharacterRig:button_glow_alpha"], 4.80, 1.0)
	_k(anim, tracks["CharacterRig:button_depress_px"], 4.80, 8.0)
	# 5.00s: Hand release moment begins (finger begins lifting off button)
	_apply_pose_at(anim, tracks, 5.00, reaches[5])
	_k(anim, tracks["CharacterRig:button_glow_alpha"], 5.00, 0.6)

	# -----------------------------------------------------------------------
	# Beat 6: Surprise & Peak Hold (5.2s - 6.8s) — Startle, Recoil & Rear Catch
	# -----------------------------------------------------------------------
	var surprises = PoseLibraryV12.get_surprise_breakdowns()
	# 5.20s: Surprise 1 - Initial Startle (Head jerks back, hand retracts)
	_apply_pose_at(anim, tracks, 5.20, surprises[0])
	# 5.35s: Surprise 2 - Torso Recoil Snap (-12° backward lean)
	_apply_pose_at(anim, tracks, 5.35, surprises[1])
	# 5.50s: Surprise 3 - Rear Foot Catch (Left knee flexes -32° catching weight)
	_apply_pose_at(anim, tracks, 5.50, surprises[2])
	# 5.65s - 6.80s: Surprise 4 - Peak Comedic Freeze Hold (-18° recoil, held 35 frames)
	_apply_pose_at(anim, tracks, 5.65, surprises[3])
	_k(anim, tracks["CharacterRig:button_glow_alpha"], 5.65, 0.0)

	# -----------------------------------------------------------------------
	# Beat 7: Recovery & Reconsideration (6.8s - 9.0s) — Staggered Settle
	# -----------------------------------------------------------------------
	var recoveries = PoseLibraryV12.get_recovery_breakdowns()
	# 6.80s: Recovery 1 - Weight Redistribution (Torso eases forward to -4°)
	_apply_pose_at(anim, tracks, 6.80, recoveries[0])
	# 7.20s: Recovery 2 - Shoulder Settle (Shoulders drop to neutral baseline)
	_apply_pose_at(anim, tracks, 7.20, recoveries[1])
	# 7.60s: Recovery 3 - Arm Lowering & Hand Lifts toward face
	_apply_pose_at(anim, tracks, 7.60, recoveries[2])
	# 8.10s: Recovery 4 - Glasses Adjust (Pushes glasses back up bridge, smirk begins)
	_apply_pose_at(anim, tracks, 8.10, recoveries[3])
	# 8.60s: Hand settles away from glasses, head turns back to inspect button
	_k(anim, tracks["CharacterRig:glasses_slip_px"], 8.60, 0.0)
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 8.60, -2.0)
	_k(anim, tracks["CharacterRig:mouth_state"], 8.60, "smirk")

	# -----------------------------------------------------------------------
	# Beat 8: Amused Payoff (9.0s - 11.0s) — Comedic Punctuation Mark
	# -----------------------------------------------------------------------
	# Final cocky amused finish: hand gesturing toward button ("Should I press it again?")
	_apply_pose_at(anim, tracks, 9.00, PoseLibraryV12.get_satisfaction_pose())
	# Final hold through 11.0s
	_apply_pose_at(anim, tracks, 11.00, PoseLibraryV12.get_satisfaction_pose())

	return anim

static func _apply_pose_at(anim: Animation, tracks: Dictionary, time: float, pose: Dictionary) -> void:
	for prop in pose:
		var track_key = "CharacterRig:" + prop
		if track_key in tracks:
			_k(anim, tracks[track_key], time, pose[prop])

static func _k(anim: Animation, track_idx: int, time: float, value: Variant) -> void:
	anim.track_insert_key(track_idx, time, value)
