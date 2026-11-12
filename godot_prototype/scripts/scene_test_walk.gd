extends Node2D

## Math Mayhem v13 — Validation Demonstration: Contact-Locked Natural Walk Cycle
## Implements: Anticipation -> 4 Natural Strides -> Deceleration -> Close Step -> Settle & Smirk
## Features:
## - 2-Bone analytical IK planted foot locking (strictly 0.0px foot drift during stance)
## - Dynamic pelvis harmonic bobbing (Contact -> Down Recoil -> Passing -> Push-off)
## - Richard Williams Animator's Survival Kit passing clearance arc
## - Counter-oscillating arm swing with secondary elbow flexion
## - Forward momentum spine lean and secondary hair lag
## - Seamless transition to expressive standing idle and confident smirk

const CharacterRig2D = preload("res://scripts/character_rig_2d.gd")
const DebugOverlay = preload("res://scripts/debug_overlay.gd")

var rig: Node2D
var debug_layer: Node2D

var is_debug_mode: bool = false
var fps: int = 30
var duration: float = 6.5
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
	rig.show_button_pedestal = false
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

	# Warm up rendering engine so initial frame buffer is populated
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

	# Target lookahead position for gaze tracking (eyes look ahead at eye height)
	rig.look_at_target(Vector2(1000.0, 1150.0))

	# -----------------------------------------------------------------------
	# Phase 1: Anticipation & Start (0.0s - 0.8s)
	# -----------------------------------------------------------------------
	if t < 0.8:
		debug_layer.current_action_label = "Walk: 1. ANTICIPATION (Weight shifts to stance foot, forward intent)"
		var p_start = t / 0.8
		var ease_start = _smoothstep(p_start)
		
		# Pelvis starts at 295px, leans slightly forward
		rig.root_pos = Vector2(lerpf(295.0, 310.0, ease_start), standing_y)
		rig.torso_lean_deg = lerpf(2.0, 4.5, ease_start)
		rig.spine_arch_deg = 4.5
		rig.hair_lag_deg = sin(p_start * PI) * 3.0
		
		# Both feet initially grounded
		rig.lock_foot("left", Vector2(280.0, floor_ankle_y))
		rig.lock_foot("right", Vector2(310.0, floor_ankle_y))
		
		rig.left_shoulder_deg = lerpf(6.0, -10.0, ease_start)
		rig.right_shoulder_deg = lerpf(6.0, 15.0, ease_start)
		rig.left_elbow_deg = 14.0
		rig.right_elbow_deg = 18.0
		rig.right_hand_pose = "relaxed"
		rig.left_hand_pose = "relaxed"
		rig.set_expression("neutral", 1.0)

	# -----------------------------------------------------------------------
	# Phase 2: Active Strides (0.8s - 4.0s, 4 Stride Steps @ 0.8s each)
	# -----------------------------------------------------------------------
	elif t < 4.0:
		var walk_t = t - 0.8
		var step_dur = 0.8
		var step_idx = int(floor(walk_t / step_dur))
		var sub_p = (walk_t - float(step_idx) * step_dur) / step_dur
		var ease_p = _smoothstep(sub_p)
		
		# Pelvis vertical bobbing (Harmonic 2-cycle oscillation per full stride)
		# Down at recoil (sub_p = 0.20), High at passing (sub_p = 0.60)
		var bob_dy = -sin(sub_p * TAU) * 6.5
		
		# Hair secondary motion lag
		rig.hair_lag_deg = -sin(sub_p * TAU) * 7.5
		rig.torso_lean_deg = 4.2 + sin(sub_p * PI) * 1.0
		rig.set_expression("curious", 0.5)

		match step_idx:
			0:
				# Step 1: Right Foot Swings (0.8s - 1.6s)
				debug_layer.current_action_label = "Walk: 2. STRIDE 1 (Right foot swings, left stance locked)"
				var p_root_x = lerpf(310.0, 395.0, ease_p)
				rig.root_pos = Vector2(p_root_x, standing_y + bob_dy)
				
				# Stance: Left foot firmly locked
				rig.lock_foot("left", Vector2(280.0, floor_ankle_y))
				
				# Swing: Right foot swings from 310 to 425
				var swing_x = lerpf(310.0, 425.0, ease_p)
				var clearance = sin(sub_p * PI) * 26.0
				rig.lock_foot("right", Vector2(swing_x, floor_ankle_y - clearance))
				rig.right_foot_deg = lerpf(-12.0, 16.0, sub_p) if sub_p < 0.85 else lerpf(16.0, 0.0, (sub_p - 0.85) / 0.15)
				
				# Arm swing: Left arm swings forward, Right swings back
				rig.left_shoulder_deg = lerpf(-10.0, 26.0, ease_p)
				rig.right_shoulder_deg = lerpf(15.0, -18.0, ease_p)
				rig.left_elbow_deg = lerpf(14.0, 28.0, sin(sub_p * PI))
				rig.right_elbow_deg = lerpf(18.0, 12.0, sin(sub_p * PI))

			1:
				# Step 2: Left Foot Swings (1.6s - 2.4s)
				debug_layer.current_action_label = "Walk: 3. STRIDE 2 (Left foot swings over right stance)"
				var p_root_x = lerpf(395.0, 495.0, ease_p)
				rig.root_pos = Vector2(p_root_x, standing_y + bob_dy)
				
				# Stance: Right foot firmly locked at planted location
				rig.lock_foot("right", Vector2(425.0, floor_ankle_y))
				
				# Swing: Left foot swings from 280 to 535
				var swing_x = lerpf(280.0, 535.0, ease_p)
				var clearance = sin(sub_p * PI) * 26.0
				rig.lock_foot("left", Vector2(swing_x, floor_ankle_y - clearance))
				rig.left_foot_deg = lerpf(-12.0, 16.0, sub_p) if sub_p < 0.85 else lerpf(16.0, 0.0, (sub_p - 0.85) / 0.15)
				
				# Arm swing: Right arm swings forward, Left swings back
				rig.right_shoulder_deg = lerpf(-18.0, 26.0, ease_p)
				rig.left_shoulder_deg = lerpf(26.0, -18.0, ease_p)
				rig.right_elbow_deg = lerpf(12.0, 28.0, sin(sub_p * PI))
				rig.left_elbow_deg = lerpf(28.0, 12.0, sin(sub_p * PI))

			2:
				# Step 3: Right Foot Swings (2.4s - 3.2s)
				debug_layer.current_action_label = "Walk: 4. STRIDE 3 (Right foot swings forward)"
				var p_root_x = lerpf(495.0, 595.0, ease_p)
				rig.root_pos = Vector2(p_root_x, standing_y + bob_dy)
				
				# Stance: Left foot firmly locked
				rig.lock_foot("left", Vector2(535.0, floor_ankle_y))
				
				# Swing: Right foot swings from 425 to 645
				var swing_x = lerpf(425.0, 645.0, ease_p)
				var clearance = sin(sub_p * PI) * 26.0
				rig.lock_foot("right", Vector2(swing_x, floor_ankle_y - clearance))
				rig.right_foot_deg = lerpf(-12.0, 16.0, sub_p) if sub_p < 0.85 else lerpf(16.0, 0.0, (sub_p - 0.85) / 0.15)
				
				# Arm swing: Left arm swings forward, Right swings back
				rig.left_shoulder_deg = lerpf(-18.0, 26.0, ease_p)
				rig.right_shoulder_deg = lerpf(26.0, -18.0, ease_p)
				rig.left_elbow_deg = lerpf(12.0, 28.0, sin(sub_p * PI))
				rig.right_elbow_deg = lerpf(28.0, 12.0, sin(sub_p * PI))

			3, _:
				# Step 4: Left Foot Swings (3.2s - 4.0s)
				debug_layer.current_action_label = "Walk: 5. STRIDE 4 (Left foot swings to forward plant)"
				var p_root_x = lerpf(595.0, 685.0, ease_p)
				rig.root_pos = Vector2(p_root_x, standing_y + bob_dy)
				
				# Stance: Right foot firmly locked
				rig.lock_foot("right", Vector2(645.0, floor_ankle_y))
				
				# Swing: Left foot swings from 535 to 735
				var swing_x = lerpf(535.0, 735.0, ease_p)
				var clearance = sin(sub_p * PI) * 26.0
				rig.lock_foot("left", Vector2(swing_x, floor_ankle_y - clearance))
				rig.left_foot_deg = lerpf(-12.0, 16.0, sub_p) if sub_p < 0.85 else lerpf(16.0, 0.0, (sub_p - 0.85) / 0.15)
				
				# Arm swing: Right arm swings forward, Left swings back
				rig.right_shoulder_deg = lerpf(-18.0, 22.0, ease_p)
				rig.left_shoulder_deg = lerpf(26.0, -12.0, ease_p)
				rig.right_elbow_deg = lerpf(12.0, 24.0, sin(sub_p * PI))
				rig.left_elbow_deg = lerpf(28.0, 14.0, sin(sub_p * PI))

	# -----------------------------------------------------------------------
	# Phase 3: Deceleration & Close Step (4.0s - 4.8s)
	# -----------------------------------------------------------------------
	elif t < 4.8:
		debug_layer.current_action_label = "Walk: 6. DECELERATE & CLOSE (Right foot matches stance, velocity dampens)"
		var p_dec = (t - 4.0) / 0.8
		var ease_dec = _smoothstep(p_dec)
		
		rig.root_pos = Vector2(lerpf(685.0, 745.0, ease_dec), standing_y - sin(p_dec * PI) * 3.0)
		rig.torso_lean_deg = lerpf(4.2, 2.5, ease_dec)
		rig.hair_lag_deg = sin(p_dec * PI * 2.0) * 3.0
		
		# Left foot firmly locked at final forward anchor
		rig.lock_foot("left", Vector2(735.0, floor_ankle_y))
		
		# Right foot closes step to comfortable standing width
		var swing_r = lerpf(645.0, 765.0, ease_dec)
		var clearance_r = sin(p_dec * PI) * 16.0
		rig.lock_foot("right", Vector2(swing_r, floor_ankle_y - clearance_r))
		rig.right_foot_deg = lerpf(12.0, 0.0, ease_dec)
		
		# Arms return to neutral rest angles
		rig.right_shoulder_deg = lerpf(22.0, 6.0, ease_dec)
		rig.left_shoulder_deg = lerpf(-12.0, 4.0, ease_dec)
		rig.right_elbow_deg = lerpf(24.0, 12.0, ease_dec)
		rig.left_elbow_deg = lerpf(14.0, 12.0, ease_dec)
		
		rig.set_expression_blend("curious", "confident", ease_dec)

	# -----------------------------------------------------------------------
	# Phase 4: Settle & Confident Smirk (4.8s - 6.5s)
	# -----------------------------------------------------------------------
	else:
		debug_layer.current_action_label = "Walk: 7. SETTLE & SMIRK (Balanced standing pose, satisfied finish)"
		var p_settle = (t - 4.8) / 1.7
		var ease_settle = _smoothstep(clampf(p_settle * 2.0, 0.0, 1.0))
		
		# Subtle organic breathing cycle (1.2 Hz)
		var breath = sin((t - 4.8) * TAU * 0.9) * 1.5
		rig.root_pos = Vector2(745.0, standing_y + breath)
		rig.torso_lean_deg = 2.5
		rig.hair_lag_deg = sin((t - 4.8) * TAU * 0.9) * 1.0
		
		# Both feet permanently locked in final stance
		rig.lock_foot("left", Vector2(735.0, floor_ankle_y))
		rig.lock_foot("right", Vector2(765.0, floor_ankle_y))
		rig.left_foot_deg = 0.0
		rig.right_foot_deg = 0.0
		
		rig.right_shoulder_deg = 6.0
		rig.left_shoulder_deg = 4.0
		rig.right_elbow_deg = 12.0
		rig.left_elbow_deg = 12.0
		
		# Smooth transition to satisfied smirk
		var p_smirk = clampf((t - 4.8) / 0.6, 0.0, 1.0)
		rig.set_expression_blend("confident", "satisfied", p_smirk)
