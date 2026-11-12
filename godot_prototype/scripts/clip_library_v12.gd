class_name ClipLibraryV12
extends RefCounted

## Math Mayhem v12 — Reusable Production Animation Clip Library
## Serializes modular, production-ready animation clips for the CharacterRig2D:
## 1. `idle_neutral` (2.0s loop, tall breathing)
## 2. `curiosity_notice` (1.2s, eyebrow/head lead, C-curve lean, living hold)
## 3. `walk_cycle` (1.6s 2-stride loop, grounded kinematics, vertical bobbing)
## 4. `hesitate_doubt` (1.5s, hovering hand, hip contrapposto, doubt hold)
## 5. `button_press` (1.2s, anticipation, clavicle drive, contact & -8px depress hold)
## 6. `surprise_recoil` (1.8s, explosive -20° snap, hair lag -34°, rear foot catch)
## 7. `recovery_glasses_push` (2.0s, shoulder settle, glasses push-up bounce, smirk)
## 8. `amused_smirk` (2.0s loop, cocky ease, button gesture, amused hold)

const PoseLibraryV12 = preload("res://scripts/pose_library_v12.gd")
const STANDING_Y: float = 1285.8

static func get_track_names() -> Array[String]:
	return [
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

static func _create_base_anim(duration: float, is_loop: bool = false) -> Array:
	var anim: Animation = Animation.new()
	anim.length = duration
	anim.loop_mode = Animation.LOOP_LINEAR if is_loop else Animation.LOOP_NONE

	var tracks: Dictionary = {}
	for prop in get_track_names():
		var idx = anim.add_track(Animation.TYPE_VALUE)
		anim.track_set_path(idx, prop)
		if "mouth_state" in prop or "hand_pose" in prop or "show_button" in prop:
			anim.track_set_interpolation_type(idx, Animation.INTERPOLATION_NEAREST)
		else:
			anim.track_set_interpolation_type(idx, Animation.INTERPOLATION_CUBIC)
		tracks[prop] = idx
	return [anim, tracks]

static func _k(anim: Animation, track_idx: int, time: float, value: Variant) -> void:
	anim.track_insert_key(track_idx, time, value)

static func _apply_pose(anim: Animation, tracks: Dictionary, time: float, pose: Dictionary) -> void:
	for prop in pose:
		var track_key = "CharacterRig:" + prop
		if track_key in tracks:
			_k(anim, tracks[track_key], time, pose[prop])

# ===========================================================================
# 1. Idle Neutral (2.0s Loop)
# ===========================================================================
static func create_idle_clip() -> Animation:
	var pair = _create_base_anim(2.0, true)
	var anim: Animation = pair[0]
	var tracks: Dictionary = pair[1]

	_apply_pose(anim, tracks, 0.0, PoseLibraryV12.get_neutral_pose())
	# Subtle living breath at 1.0s
	_k(anim, tracks["CharacterRig:torso_squash"], 1.0, 1.008)
	_k(anim, tracks["CharacterRig:head_nod_px"], 1.0, -0.6)
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 1.0, 1.0)
	_apply_pose(anim, tracks, 2.0, PoseLibraryV12.get_neutral_pose())
	return anim

# ===========================================================================
# 2. Curiosity Notice (1.2s)
# ===========================================================================
static func create_curiosity_clip() -> Animation:
	var pair = _create_base_anim(1.2, false)
	var anim: Animation = pair[0]
	var tracks: Dictionary = pair[1]

	_apply_pose(anim, tracks, 0.0, PoseLibraryV12.get_neutral_pose())
	# Stagger 1: Eyebrows dart (t=0.2s)
	_k(anim, tracks["CharacterRig:left_brow_raise_px"], 0.2, 3.5)
	_k(anim, tracks["CharacterRig:right_brow_raise_px"], 0.2, 5.5)
	_k(anim, tracks["CharacterRig:brow_slant_deg"], 0.2, 1.0)
	# Stagger 2: Head leads (t=0.35s)
	_k(anim, tracks["CharacterRig:yaw_factor"], 0.35, 0.20)
	_k(anim, tracks["CharacterRig:head_nod_px"], 0.35, 1.5)
	# Stagger 3: Torso follows (t=0.5s)
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 0.5, 6.0)
	# Stagger 4: Arm lifts (t=0.65s)
	_k(anim, tracks["CharacterRig:right_shoulder_deg"], 0.65, 16.0)
	_k(anim, tracks["CharacterRig:right_elbow_deg"], 0.65, 28.0)
	_k(anim, tracks["CharacterRig:right_hand_pose"], 0.65, "curious")
	# Overshoot at 0.8s
	_k(anim, tracks["CharacterRig:yaw_factor"], 0.8, 0.32)
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 0.8, -6.5)
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 0.8, 14.5)
	_k(anim, tracks["CharacterRig:mouth_state"], 0.75, "curious_o")
	# Living hold settled at 0.9s - 1.2s
	_apply_pose(anim, tracks, 0.9, PoseLibraryV12.get_curious_pose())
	_apply_pose(anim, tracks, 1.2, PoseLibraryV12.get_curious_pose())
	return anim

# ===========================================================================
# 3. Walk Cycle (1.6s 2-Stride Loop)
# ===========================================================================
static func create_walk_clip() -> Animation:
	var pair = _create_base_anim(1.6, true)
	var anim: Animation = pair[0]
	var tracks: Dictionary = pair[1]

	var w = PoseLibraryV12.get_walking_breakdowns()
	# Step 1: Right lead (0.0s - 0.8s)
	_apply_pose(anim, tracks, 0.0, w[0]) # Contact
	_apply_pose(anim, tracks, 0.2, w[1]) # Down
	_k(anim, tracks["CharacterRig:torso_squash"], 0.2, 0.96)
	_apply_pose(anim, tracks, 0.4, w[2]) # Passing
	_apply_pose(anim, tracks, 0.6, w[3]) # Up
	_k(anim, tracks["CharacterRig:torso_squash"], 0.6, 1.04)

	# Step 2: Left lead (0.8s - 1.6s) - Mirrored stride
	var w_mirrored = _mirror_walk_pose(w[0])
	_apply_pose(anim, tracks, 0.8, w_mirrored)
	_apply_pose(anim, tracks, 1.0, _mirror_walk_pose(w[1]))
	_k(anim, tracks["CharacterRig:torso_squash"], 1.0, 0.96)
	_apply_pose(anim, tracks, 1.2, _mirror_walk_pose(w[2]))
	_apply_pose(anim, tracks, 1.4, _mirror_walk_pose(w[3]))
	_k(anim, tracks["CharacterRig:torso_squash"], 1.4, 1.04)
	_apply_pose(anim, tracks, 1.6, w[0])
	return anim

static func _mirror_walk_pose(p: Dictionary) -> Dictionary:
	var m = p.duplicate()
	m["left_thigh_deg"] = p.get("right_thigh_deg", 0.0)
	m["left_shin_deg"] = p.get("right_shin_deg", 0.0)
	m["left_foot_deg"] = p.get("right_foot_deg", 0.0)
	m["right_thigh_deg"] = p.get("left_thigh_deg", 0.0)
	m["right_shin_deg"] = p.get("left_shin_deg", 0.0)
	m["right_foot_deg"] = p.get("left_foot_deg", 0.0)
	m["left_shoulder_deg"] = p.get("right_shoulder_deg", 0.0)
	m["right_shoulder_deg"] = p.get("left_shoulder_deg", 0.0)
	return m

# ===========================================================================
# 4. Hesitate & Doubt (1.5s)
# ===========================================================================
static func create_hesitate_clip() -> Animation:
	var pair = _create_base_anim(1.5, false)
	var anim: Animation = pair[0]
	var tracks: Dictionary = pair[1]

	_apply_pose(anim, tracks, 0.0, PoseLibraryV12.get_neutral_pose())
	_apply_pose(anim, tracks, 0.3, PoseLibraryV12.get_hesitation_pose())
	# Doubt micro-twitch at 0.8s
	_k(anim, tracks["CharacterRig:right_wrist_deg"], 0.8, -18.0)
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 0.8, 11.5)
	_k(anim, tracks["CharacterRig:right_brow_raise_px"], 0.8, 7.0)
	_apply_pose(anim, tracks, 1.5, PoseLibraryV12.get_hesitation_pose())
	return anim

# ===========================================================================
# 5. Button Press (1.2s)
# ===========================================================================
static func create_press_clip() -> Animation:
	var pair = _create_base_anim(1.2, false)
	var anim: Animation = pair[0]
	var tracks: Dictionary = pair[1]

	var reaches = PoseLibraryV12.get_reaching_breakdowns()
	_apply_pose(anim, tracks, 0.0, reaches[0]) # Anticipation
	_apply_pose(anim, tracks, 0.15, reaches[1]) # Mid-Reach Arc
	_apply_pose(anim, tracks, 0.30, reaches[2]) # Pre-contact
	_apply_pose(anim, tracks, 0.40, reaches[3]) # Contact touch (0px depress)
	_k(anim, tracks["CharacterRig:button_depress_px"], 0.40, 0.0)
	_k(anim, tracks["CharacterRig:torso_squash"], 0.48, 0.98)
	# Depress hold (-8px depression, held 0.5s - 0.8s)
	_apply_pose(anim, tracks, 0.50, reaches[4])
	_k(anim, tracks["CharacterRig:button_depress_px"], 0.50, 8.0)
	_apply_pose(anim, tracks, 0.80, reaches[4])
	_k(anim, tracks["CharacterRig:button_depress_px"], 0.80, 8.0)
	# Release and lift
	_apply_pose(anim, tracks, 1.00, reaches[5])
	_k(anim, tracks["CharacterRig:button_depress_px"], 1.00, 2.0)
	_apply_pose(anim, tracks, 1.20, reaches[0])
	_k(anim, tracks["CharacterRig:button_depress_px"], 1.20, 0.0)
	return anim

# ===========================================================================
# 6. Surprise Recoil (1.8s)
# ===========================================================================
static func create_surprise_clip() -> Animation:
	var pair = _create_base_anim(1.8, false)
	var anim: Animation = pair[0]
	var tracks: Dictionary = pair[1]

	var s = PoseLibraryV12.get_surprise_breakdowns()
	_apply_pose(anim, tracks, 0.0, PoseLibraryV12.get_press_pose())
	# Anticipation (t=0.1s): brows & gasp
	_k(anim, tracks["CharacterRig:left_brow_raise_px"], 0.1, 12.0)
	_k(anim, tracks["CharacterRig:right_brow_raise_px"], 0.1, 12.0)
	_k(anim, tracks["CharacterRig:mouth_state"], 0.1, "open_gasp")
	# Startle & stretch (t=0.2s)
	_apply_pose(anim, tracks, 0.2, s[0])
	_k(anim, tracks["CharacterRig:torso_squash"], 0.26, 1.08)
	_k(anim, tracks["CharacterRig:hair_lag_deg"], 0.26, -32.0)
	# Recoil snap with overshoot (t=0.35s)
	_apply_pose(anim, tracks, 0.35, s[1])
	_k(anim, tracks["CharacterRig:torso_lean_deg"], 0.35, -20.0)
	_k(anim, tracks["CharacterRig:shoulder_shrug_px"], 0.35, 28.0)
	_k(anim, tracks["CharacterRig:glasses_slip_px"], 0.35, 8.5)
	_k(anim, tracks["CharacterRig:hair_lag_deg"], 0.35, -34.0)
	# Rear catch impact (t=0.5s)
	_apply_pose(anim, tracks, 0.50, s[2])
	_k(anim, tracks["CharacterRig:torso_squash"], 0.50, 0.94)
	# Comedic freeze hold (t=0.65s - 1.8s)
	_apply_pose(anim, tracks, 0.65, s[3])
	_apply_pose(anim, tracks, 1.80, s[3])
	return anim

# ===========================================================================
# 7. Recovery & Glasses Push (2.0s)
# ===========================================================================
static func create_recovery_clip() -> Animation:
	var pair = _create_base_anim(2.0, false)
	var anim: Animation = pair[0]
	var tracks: Dictionary = pair[1]

	var r = PoseLibraryV12.get_recovery_breakdowns()
	_apply_pose(anim, tracks, 0.0, r[0]) # Weight shift
	_apply_pose(anim, tracks, 0.4, r[1]) # Shoulder settle
	_k(anim, tracks["CharacterRig:mouth_state"], 0.4, "curious_o")
	_apply_pose(anim, tracks, 0.8, r[2]) # Arm sweep to face
	_apply_pose(anim, tracks, 1.3, r[3]) # Glasses push
	# Bounce overshoot at 1.35s
	_k(anim, tracks["CharacterRig:glasses_slip_px"], 1.35, -1.5)
	_k(anim, tracks["CharacterRig:glasses_slip_px"], 1.55, 0.0)
	_k(anim, tracks["CharacterRig:mouth_state"], 1.55, "smirk")
	_k(anim, tracks["CharacterRig:right_brow_raise_px"], 1.55, 4.0)
	# Settle to smirk stance at 2.0s
	_apply_pose(anim, tracks, 2.0, PoseLibraryV12.get_satisfaction_pose())
	return anim

# ===========================================================================
# 8. Amused Smirk (2.0s Loop)
# ===========================================================================
static func create_amused_clip() -> Animation:
	var pair = _create_base_anim(2.0, true)
	var anim: Animation = pair[0]
	var tracks: Dictionary = pair[1]

	_apply_pose(anim, tracks, 0.0, PoseLibraryV12.get_satisfaction_pose())
	# Subtle living smirk sway
	_k(anim, tracks["CharacterRig:head_tilt_deg"], 1.0, -4.0)
	_k(anim, tracks["CharacterRig:torso_squash"], 1.0, 1.006)
	_apply_pose(anim, tracks, 2.0, PoseLibraryV12.get_satisfaction_pose())
	return anim

# ===========================================================================
# Master Exporter
# ===========================================================================
static func build_and_save_all_clips(out_dir: String = "res://animations/clips") -> Dictionary:
	var dir = DirAccess.open("res://")
	if not dir.dir_exists(out_dir):
		dir.make_dir_recursive(out_dir)

	var clips: Dictionary = {
		"idle_neutral": create_idle_clip(),
		"curiosity_notice": create_curiosity_clip(),
		"walk_cycle": create_walk_clip(),
		"hesitate_doubt": create_hesitate_clip(),
		"button_press": create_press_clip(),
		"surprise_recoil": create_surprise_clip(),
		"recovery_glasses_push": create_recovery_clip(),
		"amused_smirk": create_amused_clip()
	}

	for clip_name in clips:
		var path = "%s/%s.res" % [out_dir, clip_name]
		var err = ResourceSaver.save(clips[clip_name], path)
		if err != OK:
			printerr("Failed to save clip: ", path)
		else:
			print("Saved clip: ", path)

	return clips
