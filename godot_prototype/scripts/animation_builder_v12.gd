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
	if not is_stepped:
		return create_v12_master_animation()
	return create_v12_stepped_animation()

static func create_v12_stepped_animation() -> Animation:
	var anim: Animation = Animation.new()
	anim.length = 11.0
	var interp_mode = Animation.INTERPOLATION_NEAREST

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

# ===========================================================================
# Math Mayhem v12 — Master Spline Animation with Cascading Delays & Secondary Physics
# ===========================================================================
static func create_v12_master_animation() -> Animation:
	var anim: Animation = Animation.new()
	anim.length = 11.0

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
			anim.track_set_interpolation_type(idx, Animation.INTERPOLATION_CUBIC)
		tracks[prop] = idx

	# Button pedestal visible throughout
	_k(anim, tracks["CharacterRig:show_button_pedestal"], 0.0, true)

	# -----------------------------------------------------------------------
	# Beat 1: Establish & Notice (0.0s - 1.2s)
	# -----------------------------------------------------------------------
	# 0.0s - 0.45s: Calm tall neutral stance with subtle living breathing
	_apply_pose_at(anim, tracks, 0.00, PoseLibraryV12.get_neutral_pose())
	_k(anim, tracks["CharacterRig:torso_squash"], 0.25, 1.006)
	_k(anim, tracks["CharacterRig:head_nod_px"], 0.25, -0.5)
	_apply_pose_at(anim, tracks, 0.45, PoseLibraryV12.get_neutral_pose())

	# 0.48s: Stagger 1 — Eye dart & eyebrows anticipate notice (2 frames before head)
	_k(anim, tracks["CharacterRig:left_brow_raise_px"], 0.48, 3.5)
	_k(anim, tracks["CharacterRig:right_brow_raise_px"], 0.48, 5.5)
	_k(anim, tracks["CharacterRig:brow_slant_deg"], 0.48, 1.0)

	# 0.52s: Stagger 2 — Head leads attention turn
	_k(anim, tracks["CharacterRig:yaw_factor"], 0.52, 0.18)
	_k(anim, tracks["CharacterRig:head_nod_px"], 0.52, 1.5)

	# 0.60s: Stagger 3 — Torso leans in following head
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 0.60, 5.0)
	_k(anim, tracks["CharacterRig:spine_arch_deg"], 0.60, 2.5)

	# 0.68s: Stagger 4 — Arm lifts into curious gesture
	_k(anim, tracks["CharacterRig:right_shoulder_deg"], 0.68, 16.0)
	_k(anim, tracks["CharacterRig:right_elbow_deg"], 0.68, 28.0)
	_k(anim, tracks["CharacterRig:right_hand_pose"], 0.68, "curious")

	# 0.78s: Overshoot moment (Head & body ease past target)
	_k(anim, tracks["CharacterRig:yaw_factor"], 0.78, 0.32)
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 0.78, -6.5)
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 0.78, 14.5)
	_k(anim, tracks["CharacterRig:mouth_state"], 0.75, "curious_o")

	# 0.85s - 1.10s: Living Curious Hold (Audience absorbs comedic interest)
	_apply_pose_at(anim, tracks, 0.85, PoseLibraryV12.get_curious_pose())
	_apply_pose_at(anim, tracks, 1.10, PoseLibraryV12.get_curious_pose())

	# 1.15s: Anticipation Dip before stride (pelvis lowers slightly)
	_k(anim, tracks["CharacterRig:root_pos"], 1.15, Vector2(380.0, STANDING_Y + 3.0))
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 1.15, 8.0)

	# -----------------------------------------------------------------------
	# Beat 2: Approach & Stop (1.2s - 2.8s) — Splined 6-Phase Walk
	# -----------------------------------------------------------------------
	var walks = PoseLibraryV12.get_walking_breakdowns()
	# 1.20s: Walk 1 - Contact (Right heel strikes at x=410)
	_apply_pose_at(anim, tracks, 1.20, walks[0])
	# 1.45s: Walk 2 - Down (Shock absorption squash, pelvis drops at x=435)
	_apply_pose_at(anim, tracks, 1.45, walks[1])
	_k(anim, tracks["CharacterRig:torso_squash"], 1.45, 0.96)
	_k(anim, tracks["CharacterRig:head_squash"], 1.45, 0.98)
	# 1.75s: Walk 3 - Passing (Left leg swings past stance leg at x=470)
	_apply_pose_at(anim, tracks, 1.75, walks[2])
	_k(anim, tracks["CharacterRig:torso_squash"], 1.75, 1.01)
	# 2.05s: Walk 4 - Up (Push-off extension stretch at x=505)
	_apply_pose_at(anim, tracks, 2.05, walks[3])
	_k(anim, tracks["CharacterRig:torso_squash"], 2.05, 1.04)
	_k(anim, tracks["CharacterRig:head_squash"], 2.05, 1.02)
	# 2.35s: Walk 5 - Plant (Left foot plants firmly at x=535)
	_apply_pose_at(anim, tracks, 2.35, walks[4])
	# 2.60s: Walk 6 - Settled Stop (Bilateral foot lock at x=540)
	_apply_pose_at(anim, tracks, 2.60, walks[5])
	_k(anim, tracks["CharacterRig:torso_squash"], 2.60, 1.00)
	_k(anim, tracks["CharacterRig:head_squash"], 2.60, 1.00)

	# -----------------------------------------------------------------------
	# Beat 3: Investigate & Hesitate (2.8s - 4.0s) — Sustained Comedic Hold
	# -----------------------------------------------------------------------
	# 2.80s: Transition into Hesitation pose (Hand hovers 28px directly above button, elbow 44°)
	_apply_pose_at(anim, tracks, 2.80, PoseLibraryV12.get_hesitation_pose())
	
	# 3.40s: Subtle doubt micro-twitch (head cocks +11.5°, brow twitches)
	_k(anim, tracks["CharacterRig:right_wrist_deg"], 3.40, -18.0)
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 3.40, 11.5)
	_k(anim, tracks["CharacterRig:right_brow_raise_px"], 3.40, 7.0)

	# 3.85s: Hold sustained firmly through 3.85s
	_apply_pose_at(anim, tracks, 3.85, PoseLibraryV12.get_hesitation_pose())

	# 3.95s: Anticipation Pull-back (Gathers energy to press)
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 3.95, 2.0)
	_k(anim, tracks["CharacterRig:right_shoulder_deg"], 3.95, 26.0)
	_k(anim, tracks["CharacterRig:right_elbow_deg"], 3.95, 48.0)
	_k(anim, tracks["CharacterRig:right_wrist_deg"], 3.95, -15.0)

	# -----------------------------------------------------------------------
	# Beat 4: Decision & Press (4.0s - 4.8s) — Exact Kinematic Contact & Depression
	# -----------------------------------------------------------------------
	var reaches = PoseLibraryV12.get_reaching_breakdowns()
	# 4.00s: Reach 1 - Shoulder Anticipation
	_apply_pose_at(anim, tracks, 4.00, reaches[0])
	# 4.15s: Reach 2 - Mid-Reach Arc (Torso leans forward, shoulder protracts)
	_apply_pose_at(anim, tracks, 4.15, reaches[1])
	# 4.30s: Reach 3 - Pre-Contact (Hovering 6px above button cap)
	_apply_pose_at(anim, tracks, 4.30, reaches[2])

	# 4.40s: Reach 4 - Initial Fingertip Touch (Fingertip on button at y=1206.45, diff 0.16px, 0px depress)
	_apply_pose_at(anim, tracks, 4.40, reaches[3])
	_k(anim, tracks["CharacterRig:button_depress_px"], 4.40, 0.0)

	# 4.48s: Impact compression (torso squash 0.98 as button compresses -8px)
	_k(anim, tracks["CharacterRig:torso_squash"], 4.48, 0.98)

	# 4.50s - 4.80s: Reach 5 - Solid Depressed Button Hold (-8px depression, diff 0.10px)
	_apply_pose_at(anim, tracks, 4.50, reaches[4])
	_k(anim, tracks["CharacterRig:button_depress_px"], 4.50, 8.0)
	_apply_pose_at(anim, tracks, 4.80, reaches[4])
	_k(anim, tracks["CharacterRig:button_depress_px"], 4.80, 8.0)

	# -----------------------------------------------------------------------
	# Beat 5: Activation (4.8s - 5.2s) — Controlled Non-Obscuring Pulse
	# -----------------------------------------------------------------------
	# 4.80s: Activation flash burst triggers (cap glow = 1.0)
	_k(anim, tracks["CharacterRig:button_glow_alpha"], 4.80, 1.0)
	_k(anim, tracks["CharacterRig:button_depress_px"], 4.80, 8.0)

	# 5.00s: Hand release moment (finger begins lifting off button)
	_apply_pose_at(anim, tracks, 5.00, reaches[5])
	_k(anim, tracks["CharacterRig:button_glow_alpha"], 5.00, 0.6)
	_k(anim, tracks["CharacterRig:button_depress_px"], 5.00, 4.0)

	# 5.15s: Facial Anticipation of Shock (brows shoot up, mouth gasps 1 frame before body snaps)
	_k(anim, tracks["CharacterRig:left_brow_raise_px"], 5.15, 12.0)
	_k(anim, tracks["CharacterRig:right_brow_raise_px"], 5.15, 12.0)
	_k(anim, tracks["CharacterRig:mouth_state"], 5.15, "open_gasp")
	_k(anim, tracks["CharacterRig:button_depress_px"], 5.15, 0.0)

	# -----------------------------------------------------------------------
	# Beat 6: Surprise & Peak Hold (5.2s - 6.8s) — Recoil, Drag & Rear Catch
	# -----------------------------------------------------------------------
	var surprises = PoseLibraryV12.get_surprise_breakdowns()
	# 5.20s: Surprise 1 - Initial Startle (Head jerks back, hand retracts)
	_apply_pose_at(anim, tracks, 5.20, surprises[0])
	# 5.26s: Stretch & Drag (Torso stretch 1.08, hair lag -32°)
	_k(anim, tracks["CharacterRig:torso_squash"], 5.26, 1.08)
	_k(anim, tracks["CharacterRig:head_squash"], 5.26, 1.06)
	_k(anim, tracks["CharacterRig:hair_lag_deg"], 5.26, -32.0)

	# 5.35s: Surprise 2 - Torso Recoil Snap with Overshoot (-20° lean, +28px shrug, +8.5px glasses slip)
	_apply_pose_at(anim, tracks, 5.35, surprises[1])
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 5.35, -20.0)
	_k(anim, tracks["CharacterRig:shoulder_shrug_px"], 5.35, 28.0)
	_k(anim, tracks["CharacterRig:glasses_slip_px"], 5.35, 8.5)
	_k(anim, tracks["CharacterRig:hair_lag_deg"], 5.35, -34.0)

	# 5.50s: Surprise 3 - Rear Foot Catch (Left knee absorbs shock, torso squash 0.94)
	_apply_pose_at(anim, tracks, 5.50, surprises[2])
	_k(anim, tracks["CharacterRig:torso_squash"], 5.50, 0.94)
	_k(anim, tracks["CharacterRig:head_squash"], 5.50, 0.96)

	# 5.65s - 6.80s: Surprise 4 - Peak Comedic Freeze Hold (-18° recoil, held 35 frames)
	_apply_pose_at(anim, tracks, 5.65, surprises[3])
	_k(anim, tracks["CharacterRig:torso_squash"], 5.65, 1.00)
	_k(anim, tracks["CharacterRig:head_squash"], 5.65, 1.00)
	_k(anim, tracks["CharacterRig:button_glow_alpha"], 5.65, 0.0)
	_apply_pose_at(anim, tracks, 6.80, surprises[3])

	# -----------------------------------------------------------------------
	# Beat 7: Recovery & Reconsideration (6.8s - 9.0s) — Staggered Settle & Glasses Push
	# -----------------------------------------------------------------------
	var recoveries = PoseLibraryV12.get_recovery_breakdowns()
	# 6.80s: Recovery 1 - Weight Redistribution (Torso eases forward to -4°)
	_apply_pose_at(anim, tracks, 6.80, recoveries[0])

	# 7.20s: Recovery 2 - Shoulder Settle (Shoulders drop to +2px)
	_apply_pose_at(anim, tracks, 7.20, recoveries[1])
	_k(anim, tracks["CharacterRig:mouth_state"], 7.20, "curious_o")

	# 7.60s: Recovery 3 - Arm Lowering & Hand sweeps toward face
	_apply_pose_at(anim, tracks, 7.60, recoveries[2])

	# 8.10s: Recovery 4 - Glasses Adjust
	_apply_pose_at(anim, tracks, 8.10, recoveries[3])

	# 8.15s: Glasses Secondary Bounce (Finger pushes glasses past bridge to -1.5px)
	_k(anim, tracks["CharacterRig:glasses_slip_px"], 8.15, -1.5)

	# 8.35s: Glasses settle cleanly to 0.0px, smirk begins
	_k(anim, tracks["CharacterRig:glasses_slip_px"], 8.35, 0.0)
	_k(anim, tracks["CharacterRig:mouth_state"], 8.35, "smirk")
	_k(anim, tracks["CharacterRig:right_brow_raise_px"], 8.35, 4.0)

	# 8.60s: Hand settles away from face, head turns back toward button
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 8.60, -2.5)
	_k(anim, tracks["CharacterRig:yaw_factor"], 8.60, 0.22)

	# -----------------------------------------------------------------------
	# Beat 8: Amused Payoff (9.0s - 11.0s) — Comedic Punctuation Mark Hold
	# -----------------------------------------------------------------------
	_apply_pose_at(anim, tracks, 9.00, PoseLibraryV12.get_satisfaction_pose())
	# Final hold through 11.0s (60 frames)
	_apply_pose_at(anim, tracks, 11.00, PoseLibraryV12.get_satisfaction_pose())

	return anim

static func _apply_pose_at(anim: Animation, tracks: Dictionary, time: float, pose: Dictionary) -> void:
	for prop in pose:
		var track_key = "CharacterRig:" + prop
		if track_key in tracks:
			_k(anim, tracks[track_key], time, pose[prop])

static func _k(anim: Animation, track_idx: int, time: float, value: Variant) -> void:
	anim.track_insert_key(track_idx, time, value)
