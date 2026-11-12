extends Node2D

## Math Mayhem v13.4 — Natural Locomotion & Walk-to-Interaction Transition
## Implements: Neutral Idle -> Initiation -> Authored 5-Pose Gait -> Deceleration -> Notice -> Approach & Reach
## Features:
## - 5 Authored Gait Poses: Contact (A), Down (B), Passing (C), Up (D), Opposite Contact (E)
## - Zero-slip stance foot locking via 2-bone analytical IK (strictly 0.0px drift)
## - Natural swing clearance arc (18-22px floor clearance, heel-to-toe roll)
## - Harmonic pelvis bobbing (down recoil absorption +5px, passing vault -5.5px)
## - Restrained, shoulder-driven arm swing with secondary elbow follow-through
## - Upright stabilized head during walking (no exaggerated persistent tilt)
## - Seamless Walk -> Stop -> Notice -> Reach transition for Episode 001

const CharacterRig2D = preload("res://scripts/character_rig_2d.gd")
const DebugOverlay = preload("res://scripts/debug_overlay.gd")

var rig: Node2D
var debug_layer: Node2D

var is_debug_mode: bool = false
var fps: int = 30
var duration: float = 7.0
var output_dir: String = "res://temp_test_walk_clean"

func _ready() -> void:
	var args: PackedStringArray = OS.get_cmdline_user_args()
	for arg in args:
		if arg == "--debug":
			is_debug_mode = true
		elif arg.begins_with("--out="):
			output_dir = arg.substr(6)
	
	_setup_stage()
	_render_sequence()

func _setup_stage() -> void:
	RenderingServer.set_default_clear_color(Color(0.96, 0.97, 0.98))

	# 1. Character Rig
	rig = CharacterRig2D.new()
	rig.name = "CharacterRig"
	rig.show_floor_item = false
	rig.show_button_pedestal = true
	rig.button_pedestal_pos = Vector2(800.0, 1220.0)
	add_child(rig)

	# 2. Debug Overlay
	debug_layer = DebugOverlay.new()
	debug_layer.name = "DebugOverlay"
	debug_layer.target_rig = rig
	debug_layer.show_debug = is_debug_mode
	add_child(debug_layer)

func _render_sequence() -> void:
	var total_frames: int = int(round(duration * float(fps)))
	print("Starting Walk Demonstration Render: total_frames=%d, debug=%s" % [total_frames, str(is_debug_mode)])

	var dir = DirAccess.open("res://")
	if not dir.dir_exists(output_dir):
		dir.make_dir_recursive(output_dir)

	# Warm up rendering engine
	_evaluate_state_at(0.0)
	RenderingServer.force_draw()
	await get_tree().process_frame
	await get_tree().process_frame

	for i in range(total_frames):
		var t: float = float(i) / float(fps)
		_evaluate_state_at(t)

		RenderingServer.force_draw()
		await get_tree().process_frame

		var img: Image = get_viewport().get_texture().get_image()
		var frame_path: String = "%s/frame_%04d.png" % [output_dir, i]
		var err = img.save_png(frame_path)
		if err != OK:
			printerr("Failed saving frame: ", frame_path)

		if i % 30 == 0:
			print("Rendered Walk frame %d / %d (%.2fs / %.2fs)" % [i, total_frames, t, duration])

	print("Walk Render finished. Saved to: ", output_dir)
	get_tree().quit(0)

func _smoothstep(p: float) -> float:
	var c = clampf(p, 0.0, 1.0)
	return c * c * (3.0 - 2.0 * c)

func _evaluate_state_at(t: float) -> void:
	debug_layer.current_time_sec = t
	var s: float = rig.character_scale
	var floor_ankle_y: float = 1592.8
	var standing_y: float = 1285.8

	# -----------------------------------------------------------------------
	# Phase 1: Neutral Standing Idle (0.0s - 0.7s, Frames 0-21)
	# -----------------------------------------------------------------------
	if t < 0.7:
		debug_layer.current_action_label = "Locomotion: 1. NEUTRAL IDLE (Upright head, relaxed posture)"
		rig.root_pos = Vector2(250.0, standing_y)
		rig.torso_lean_deg = 1.5
		rig.spine_arch_deg = 3.5
		rig.head_tilt_deg = 0.0 # Stabilized upright head!
		rig.expression_tilt_offset_deg = 0.0
		rig.clear_gaze_target()
		
		# Both feet planted at initial standing position
		rig.lock_foot("left", Vector2(232.0, floor_ankle_y))
		rig.lock_foot("right", Vector2(268.0, floor_ankle_y))
		rig.left_foot_deg = 0.0
		rig.right_foot_deg = 0.0
		
		# Relaxed arms at sides
		rig.left_shoulder_deg = 4.0
		rig.right_shoulder_deg = 6.0
		rig.left_elbow_deg = 12.0
		rig.right_elbow_deg = 14.0
		rig.right_hand_pose = "relaxed"
		rig.left_hand_pose = "relaxed"
		rig.set_expression("neutral", 1.0)

	# -----------------------------------------------------------------------
	# Phase 2: Walk Initiation & Weight Shift (0.7s - 1.2s, Frames 21-36)
	# -----------------------------------------------------------------------
	elif t < 1.2:
		debug_layer.current_action_label = "Locomotion: 2. INITIATION (Weight shifts forward, heel unloads)"
		var p_init = (t - 0.7) / 0.5
		var ease_init = _smoothstep(p_init)
		
		# Pelvis translates forward smoothly
		rig.root_pos = Vector2(lerpf(250.0, 275.0, ease_init), standing_y)
		rig.torso_lean_deg = lerpf(1.5, 3.8, ease_init)
		rig.head_tilt_deg = 0.0 # Head remains upright
		
		# Left foot is stance foot (firmly locked)
		rig.lock_foot("left", Vector2(232.0, floor_ankle_y))
		
		# Right foot unloads heel, prepares to step
		var r_lift = ease_init * 6.0
		rig.lock_foot("right", Vector2(lerpf(268.0, 276.0, ease_init), floor_ankle_y - r_lift))
		rig.right_foot_deg = lerpf(0.0, -8.0, ease_init)
		
		# Gentle counter-balance arm shift
		rig.left_shoulder_deg = lerpf(4.0, -8.0, ease_init)
		rig.right_shoulder_deg = lerpf(6.0, 12.0, ease_init)
		rig.left_elbow_deg = 14.0
		rig.right_elbow_deg = 16.0

	# -----------------------------------------------------------------------
	# Phase 3: Authored 5-Pose Gait Strides (1.2s - 4.2s, Frames 36-126)
	# 4 Stride Steps @ 0.75s each:
	# Stride 1: Right Swing (1.2s - 1.95s)
	# Stride 2: Left Swing (1.95s - 2.70s)
	# Stride 3: Right Swing (2.70s - 3.45s)
	# Stride 4: Left Swing (3.45s - 4.20s)
	# -----------------------------------------------------------------------
	elif t < 4.2:
		var walk_t = t - 1.2
		var step_dur = 0.75
		var step_idx = int(floor(walk_t / step_dur))
		var phi = (walk_t - float(step_idx) * step_dur) / step_dur
		var ease_phi = _smoothstep(phi)
		
		# Pelvis vertical bobbing (Authored 5-pose displacement):
		# phi=0.0 (Contact): dy = 0.0
		# phi=0.20 (Down/Recoil): dy = +5.0 (cushions weight)
		# phi=0.50 (Passing): dy = -5.5 (vaults over straight stance leg)
		# phi=0.75 (Up/Push-off): dy = -2.0
		var bob_dy: float = 0.0
		if phi < 0.20:
			bob_dy = lerpf(0.0, 5.0, phi / 0.20)
		elif phi < 0.50:
			bob_dy = lerpf(5.0, -5.5, (phi - 0.20) / 0.30)
		elif phi < 0.75:
			bob_dy = lerpf(-5.5, -2.0, (phi - 0.50) / 0.25)
		else:
			bob_dy = lerpf(-2.0, 0.0, (phi - 0.75) / 0.25)

		# Stabilized upright head with subtle organic nodding
		rig.head_tilt_deg = sin(phi * TAU) * 0.8
		rig.torso_lean_deg = 3.5 + sin(phi * PI) * 0.5
		rig.hair_lag_deg = -sin(phi * TAU) * 4.5
		rig.set_expression("neutral", 1.0)

		# Swing foot ground clearance arc (18-22px lift at passing, heel-to-toe roll)
		var swing_lift = sin(phi * PI) * 20.0
		var foot_rot: float = 0.0
		if phi < 0.25:
			# Push-off / toe drag
			foot_rot = lerpf(-8.0, 0.0, phi / 0.25)
		elif phi < 0.65:
			# Level passing clearance
			foot_rot = 3.5
		elif phi < 0.90:
			# Heel strike reach
			foot_rot = lerpf(3.5, 14.0, (phi - 0.65) / 0.25)
		else:
			# Roll flat to ground
			foot_rot = lerpf(14.0, 0.0, (phi - 0.90) / 0.10)

		# Arm swing opposition with subtle elbow flexion
		var arm_lead = sin((phi - 0.5) * PI) # Smooth sine curve

		match step_idx:
			0:
				# Stride 1: Right Foot Swings (1.20s - 1.95s)
				debug_layer.current_action_label = "Locomotion: 3. STRIDE 1 (Right swing, left stance locked)"
				var root_x = lerpf(275.0, 370.0, ease_phi)
				rig.root_pos = Vector2(root_x, standing_y + bob_dy)
				
				# Stance: Left foot strictly locked with 0.0px drift
				rig.lock_foot("left", Vector2(232.0, floor_ankle_y))
				rig.left_foot_deg = 0.0
				
				# Swing: Right foot swings from 276 to 415
				var swing_x = lerpf(276.0, 415.0, ease_phi)
				rig.lock_foot("right", Vector2(swing_x, floor_ankle_y - swing_lift))
				rig.right_foot_deg = foot_rot
				
				# Arm swing: Left arm forward (+18 deg), Right arm back (-14 deg)
				rig.left_shoulder_deg = lerpf(-8.0, 18.0, ease_phi)
				rig.right_shoulder_deg = lerpf(12.0, -14.0, ease_phi)
				rig.left_elbow_deg = lerpf(14.0, 24.0, sin(phi * PI))
				rig.right_elbow_deg = lerpf(16.0, 10.0, sin(phi * PI))

			1:
				# Stride 2: Left Foot Swings (1.95s - 2.70s)
				debug_layer.current_action_label = "Locomotion: 4. STRIDE 2 (Left swing over right stance)"
				var root_x = lerpf(370.0, 475.0, ease_phi)
				rig.root_pos = Vector2(root_x, standing_y + bob_dy)
				
				# Stance: Right foot strictly locked at 415.0
				rig.lock_foot("right", Vector2(415.0, floor_ankle_y))
				rig.right_foot_deg = 0.0
				
				# Swing: Left foot swings from 232 to 525
				var swing_x = lerpf(232.0, 525.0, ease_phi)
				rig.lock_foot("left", Vector2(swing_x, floor_ankle_y - swing_lift))
				rig.left_foot_deg = foot_rot
				
				# Arm swing: Right arm forward (+18 deg), Left arm back (-14 deg)
				rig.right_shoulder_deg = lerpf(-14.0, 18.0, ease_phi)
				rig.left_shoulder_deg = lerpf(18.0, -14.0, ease_phi)
				rig.right_elbow_deg = lerpf(10.0, 24.0, sin(phi * PI))
				rig.left_elbow_deg = lerpf(24.0, 10.0, sin(phi * PI))

			2:
				# Stride 3: Right Foot Swings (2.70s - 3.45s)
				debug_layer.current_action_label = "Locomotion: 5. STRIDE 3 (Right swing over left stance)"
				var root_x = lerpf(475.0, 575.0, ease_phi)
				rig.root_pos = Vector2(root_x, standing_y + bob_dy)
				
				# Stance: Left foot strictly locked at 525.0
				rig.lock_foot("left", Vector2(525.0, floor_ankle_y))
				rig.left_foot_deg = 0.0
				
				# Swing: Right foot swings from 415 to 630
				var swing_x = lerpf(415.0, 630.0, ease_phi)
				rig.lock_foot("right", Vector2(swing_x, floor_ankle_y - swing_lift))
				rig.right_foot_deg = foot_rot
				
				# Arm swing: Left arm forward, Right arm back
				rig.left_shoulder_deg = lerpf(-14.0, 18.0, ease_phi)
				rig.right_shoulder_deg = lerpf(18.0, -14.0, ease_phi)
				rig.left_elbow_deg = lerpf(10.0, 24.0, sin(phi * PI))
				rig.right_elbow_deg = lerpf(24.0, 10.0, sin(phi * PI))

			3, _:
				# Stride 4: Left Foot Swings (3.45s - 4.20s)
				debug_layer.current_action_label = "Locomotion: 6. STRIDE 4 (Left swing to forward plant)"
				var root_x = lerpf(575.0, 650.0, ease_phi)
				rig.root_pos = Vector2(root_x, standing_y + bob_dy)
				
				# Stance: Right foot strictly locked at 630.0
				rig.lock_foot("right", Vector2(630.0, floor_ankle_y))
				rig.right_foot_deg = 0.0
				
				# Swing: Left foot swings from 525 to 700
				var swing_x = lerpf(525.0, 700.0, ease_phi)
				rig.lock_foot("left", Vector2(swing_x, floor_ankle_y - swing_lift))
				rig.left_foot_deg = foot_rot
				
				# Arm swing: Right arm forward, Left arm back
				rig.right_shoulder_deg = lerpf(-14.0, 14.0, ease_phi)
				rig.left_shoulder_deg = lerpf(18.0, -8.0, ease_phi)
				rig.right_elbow_deg = lerpf(10.0, 20.0, sin(phi * PI))
				rig.left_elbow_deg = lerpf(24.0, 12.0, sin(phi * PI))

	# -----------------------------------------------------------------------
	# Phase 4: Deceleration & Stance Close (4.2s - 4.9s, Frames 126-147)
	# -----------------------------------------------------------------------
	elif t < 4.9:
		debug_layer.current_action_label = "Locomotion: 7. DECELERATION & CLOSE (Natural stop, feet plant)"
		var p_dec = (t - 4.2) / 0.7
		var ease_dec = _smoothstep(p_dec)
		
		# Pelvis decelerates smoothly to 680px
		rig.root_pos = Vector2(lerpf(650.0, 680.0, ease_dec), standing_y)
		rig.torso_lean_deg = lerpf(3.5, 1.8, ease_dec)
		rig.head_tilt_deg = 0.0
		rig.hair_lag_deg = sin(p_dec * PI) * 2.0
		
		# Left foot firmly locked at final plant
		rig.lock_foot("left", Vector2(700.0, floor_ankle_y))
		rig.left_foot_deg = 0.0
		
		# Right foot closes step to comfortable standing width at 735px
		var close_x = lerpf(630.0, 735.0, ease_dec)
		var close_lift = sin(p_dec * PI) * 12.0
		rig.lock_foot("right", Vector2(close_x, floor_ankle_y - close_lift))
		rig.right_foot_deg = lerpf(8.0, 0.0, ease_dec)
		
		# Arms return to neutral rest angles
		rig.right_shoulder_deg = lerpf(14.0, 6.0, ease_dec)
		rig.left_shoulder_deg = lerpf(-8.0, 4.0, ease_dec)
		rig.right_elbow_deg = lerpf(20.0, 12.0, ease_dec)
		rig.left_elbow_deg = lerpf(12.0, 12.0, ease_dec)

	# -----------------------------------------------------------------------
	# Phase 5: Notice Pedestal & Head Turn (4.9s - 5.8s, Frames 147-174)
	# -----------------------------------------------------------------------
	elif t < 5.8:
		debug_layer.current_action_label = "Locomotion: 8. NOTICE PEDESTAL (Head & gaze aim toward console)"
		var p_notice = (t - 4.9) / 0.9
		var ease_notice = _smoothstep(p_notice)
		
		rig.root_pos = Vector2(680.0, standing_y)
		rig.torso_lean_deg = lerpf(1.8, 3.5, ease_notice)
		
		# Both feet permanently locked in balanced stance
		rig.lock_foot("left", Vector2(700.0, floor_ankle_y))
		rig.lock_foot("right", Vector2(735.0, floor_ankle_y))
		rig.left_foot_deg = 0.0
		rig.right_foot_deg = 0.0
		
		# Notice target: Button pedestal at (800, 1220)
		var button_pos = rig.get_button_contact_pos()
		rig.look_at_target(button_pos)
		
		# Expression blends smoothly to curious
		rig.set_expression_blend("neutral", "curious", ease_notice)
		
		# Right hand prepares to reach
		rig.right_shoulder_deg = lerpf(6.0, 22.0, ease_notice)
		rig.right_elbow_deg = lerpf(12.0, 35.0, ease_notice)
		rig.right_hand_pose = "reach_open"

	# -----------------------------------------------------------------------
	# Phase 6: Approach & Controlled Reach (5.8s - 7.0s, Frames 174-210)
	# -----------------------------------------------------------------------
	else:
		debug_layer.current_action_label = "Locomotion: 9. APPROACH & REACH (2-Bone IK reach toward button)"
		var p_reach = (t - 5.8) / 1.2
		var ease_reach = _smoothstep(p_reach)
		
		# Controlled subtle weight lean toward pedestal
		rig.root_pos = Vector2(lerpf(680.0, 695.0, ease_reach), standing_y)
		rig.torso_lean_deg = lerpf(3.5, 6.0, ease_reach)
		
		rig.lock_foot("left", Vector2(700.0, floor_ankle_y))
		rig.lock_foot("right", Vector2(735.0, floor_ankle_y))
		
		var button_pos = rig.get_button_contact_pos()
		rig.look_at_target(button_pos)
		
		# 2-bone IK reaches toward button contact point!
		var hover_target = button_pos + Vector2(-15.0, -18.0).lerp(Vector2(-4.0, -4.0), ease_reach)
		rig.reach_hand_to(hover_target, true, false)
		rig.right_hand_pose = "point"
		
		rig.left_shoulder_deg = lerpf(4.0, -4.0, ease_reach)
		rig.left_elbow_deg = 14.0
		
		rig.set_expression_blend("curious", "thoughtful", ease_reach)
