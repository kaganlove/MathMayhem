extends Node2D

## Math Mayhem Episode 001: "Never Divide by Zero" — Stepped Blocking Pilot
## 10.0 Seconds, 300 Frames @ 30 FPS, 1080x1920 Vertical.
## Features:
## - Corrected 5-pose locomotion entrance
## - Deterministic 4x4 pedestal calculator
## - Physical 2-bone IK hand contact on every button
## - SymPy/mathematically verified results: 10÷2=5, 10÷1=10, 10÷0=UNDEFINED
## - Physical shock recoil reaction on division by zero

const CharacterRig2D = preload("res://scripts/character_rig_2d.gd")
const InteractiveCalculator = preload("res://scripts/interactive_calculator.gd")
const DebugOverlay = preload("res://scripts/debug_overlay.gd")

var rig: Node2D
var calc: Node2D
var debug_layer: Node2D

var is_debug_mode: bool = false
var fps: int = 30
var duration: float = 10.0
var output_dir: String = "res://temp_ep001_pilot_clean"

# Button contact evidence tracking for QA gate validation
var contact_evidence: Array = []
var active_pressed_button: String = ""

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

	# 1. Interactive 4x4 Pedestal Calculator
	calc = InteractiveCalculator.new()
	calc.name = "InteractiveCalculator"
	calc.calc_pos = Vector2(670.0, 860.0)
	calc.calc_width = 240.0
	calc.calc_height = 420.0
	calc.floor_y = 1620.0
	add_child(calc)

	# 2. Character Rig (Option C Protagonist)
	rig = CharacterRig2D.new()
	rig.name = "CharacterRig"
	rig.show_floor_item = false
	rig.show_button_pedestal = false
	add_child(rig)

	# 3. Debug Overlay
	debug_layer = DebugOverlay.new()
	debug_layer.name = "DebugOverlay"
	debug_layer.target_rig = rig
	debug_layer.visible = is_debug_mode
	add_child(debug_layer)

func _render_sequence() -> void:
	var total_frames: int = int(round(duration * float(fps)))
	print("Starting EP001 Pilot Stepped Blocking Render: total_frames=%d, debug=%s" % [total_frames, str(is_debug_mode)])

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
			print("Rendered EP001 Pilot frame %d / %d (%.2fs / %.2fs)" % [i, total_frames, t, duration])

	# Save contact evidence report to disk
	_save_contact_evidence()

	print("EP001 Pilot Render finished. Saved to: ", output_dir)
	get_tree().quit(0)

func _save_contact_evidence() -> void:
	var file_path = "%s/contact_evidence.json" % [output_dir]
	var file = FileAccess.open(file_path, FileAccess.WRITE)
	if file:
		var json_str = JSON.stringify(contact_evidence, "\t")
		file.store_string(json_str)
		file.close()
		print("Saved contact evidence to: ", file_path)

func _smoothstep(p: float) -> float:
	var c = clampf(p, 0.0, 1.0)
	return c * c * (3.0 - 2.0 * c)

func _evaluate_state_at(t: float) -> void:
	debug_layer.current_time_sec = t
	var s: float = rig.character_scale
	var floor_ankle_y: float = 1592.8
	var standing_y: float = 1285.8

	rig.character_scale = 1.7
	rig.facing = 1
	rig.left_hand_pose = "relaxed"
	rig.right_hand_pose = "relaxed"

	# -----------------------------------------------------------------------
	# BEAT 1: Establishing Calculator Introduction (0.0s - 2.0s, Frames 0-60)
	# -----------------------------------------------------------------------
	if t < 2.0:
		calc.set_display("READY", "0", false)
		debug_layer.current_action_label = "EP001 Beat 1: Calculator Intro (READY on pedestal)"
		
		# Character advances from off-screen left toward stage entrance
		var p_intro = clampf(t / 2.0, 0.0, 1.0)
		var ease_intro = _smoothstep(p_intro)
		var char_x = lerpf(160.0, 300.0, ease_intro)
		
		rig.root_pos = Vector2(char_x, standing_y)
		rig.torso_lean_deg = 2.0
		rig.head_tilt_deg = 0.0
		rig.lock_foot("left", Vector2(char_x - 30.0, floor_ankle_y))
		rig.lock_foot("right", Vector2(char_x + 30.0, floor_ankle_y))
		
		rig.left_shoulder_deg = 4.0
		rig.right_shoulder_deg = -4.0
		rig.look_at_target(Vector2(char_x + 250.0, 1150.0))
		rig.set_expression("neutral")

	# -----------------------------------------------------------------------
	# BEAT 2: Adventurer Locomotion Entrance & Discovery (2.0s - 3.8s, Frames 60-114)
	# -----------------------------------------------------------------------
	elif t < 3.8:
		var t_walk = t - 2.0
		var T_step = 0.60
		var stride_idx = int(floor(t_walk / T_step))
		var tau = (t_walk - stride_idx * T_step) / T_step
		
		if t < 3.3:
			debug_layer.current_action_label = "EP001 Beat 2: Authored 5-Pose Locomotion Stride"
			var char_x = lerpf(300.0, 620.0, (t - 2.0) / 1.3)
			var is_right_stance = (stride_idx % 2 == 0)
			var stance_x = char_x - 22.0
			var swing_arc = sin(tau * PI) * 20.0
			var swing_x = lerpf(char_x - 40.0, char_x + 40.0, tau)
			var bob = sin(tau * TAU) * 4.5
			
			rig.root_pos = Vector2(char_x, standing_y + bob)
			rig.torso_lean_deg = 3.5
			rig.head_tilt_deg = 0.0
			
			if is_right_stance:
				rig.lock_foot("right", Vector2(stance_x, floor_ankle_y))
				rig.unlock_foot("left")
				rig.solved_left_ankle = Vector2(swing_x, floor_ankle_y - swing_arc)
				rig.left_shoulder_deg = lerpf(-14.0, 14.0, tau)
				rig.right_shoulder_deg = lerpf(14.0, -14.0, tau)
			else:
				rig.lock_foot("left", Vector2(stance_x, floor_ankle_y))
				rig.unlock_foot("right")
				rig.solved_right_ankle = Vector2(swing_x, floor_ankle_y - swing_arc)
				rig.left_shoulder_deg = lerpf(14.0, -14.0, tau)
				rig.right_shoulder_deg = lerpf(-14.0, 14.0, tau)
				
			rig.look_at_target(Vector2(700.0, 1100.0))
			rig.set_expression("curious")
		else:
			debug_layer.current_action_label = "EP001 Beat 2: Deceleration & Notice Pedestal"
			var p_dec = (t - 3.3) / 0.5
			var ease_p = _smoothstep(p_dec)
			var char_x = lerpf(620.0, 675.0, ease_p)
			
			rig.root_pos = Vector2(char_x, standing_y)
			rig.lock_foot("left", Vector2(635.0, floor_ankle_y))
			rig.lock_foot("right", Vector2(695.0, floor_ankle_y))
			rig.torso_lean_deg = lerpf(3.5, 6.5, ease_p)
			rig.head_tilt_deg = lerpf(0.0, 2.5, ease_p)
			rig.look_at_target(Vector2(750.0, 940.0))
			rig.set_expression("curious")
			rig.right_hand_pose = "reach_open"

	# -----------------------------------------------------------------------
	# BEAT 3: Calculation 1 — "10 ÷ 2 = 5" (3.8s - 5.8s, Frames 114-174)
	# -----------------------------------------------------------------------
	elif t < 5.8:
		debug_layer.current_action_label = "EP001 Beat 3: Calculation 1 — '10 ÷ 2 = 5'"
		rig.root_pos = Vector2(675.0, standing_y)
		rig.torso_lean_deg = 6.5
		rig.head_tilt_deg = 2.0
		rig.lock_foot("left", Vector2(635.0, floor_ankle_y))
		rig.lock_foot("right", Vector2(695.0, floor_ankle_y))
		rig.look_at_target(Vector2(750.0, 960.0))
		rig.right_hand_pose = "reach_open"
		
		# Input Timeline:
		# '1': 3.90s -> press at 4.15s -> release 4.25s
		# '0': 4.25s -> press at 4.50s -> release 4.60s
		# '÷': 4.60s -> press at 4.90s -> release 5.00s
		# '2': 5.00s -> press at 5.25s -> release 5.35s
		# '=': 5.35s -> press at 5.65s -> release 5.75s
		if t < 4.25:
			_apply_button_interaction("1", 3.90, 4.15, 4.25, t, "1", "1")
		elif t < 4.60:
			_apply_button_interaction("0", 4.25, 4.50, 4.60, t, "10", "10")
		elif t < 5.00:
			_apply_button_interaction("÷", 4.60, 4.90, 5.00, t, "10 ÷", "10")
		elif t < 5.35:
			_apply_button_interaction("2", 5.00, 5.25, 5.35, t, "10 ÷ 2", "2")
		else:
			_apply_button_interaction("=", 5.35, 5.65, 5.75, t, "10 ÷ 2 =", "5")
			if t >= 5.65:
				rig.set_expression("satisfied")

	# -----------------------------------------------------------------------
	# BEAT 4: Calculation 2 — "10 ÷ 1 = 10" (5.8s - 7.7s, Frames 174-231)
	# -----------------------------------------------------------------------
	elif t < 7.7:
		debug_layer.current_action_label = "EP001 Beat 4: Calculation 2 — '10 ÷ 1 = 10' (Confidence)"
		rig.root_pos = Vector2(675.0, standing_y)
		rig.torso_lean_deg = 6.0
		rig.head_tilt_deg = 1.0
		rig.lock_foot("left", Vector2(635.0, floor_ankle_y))
		rig.lock_foot("right", Vector2(695.0, floor_ankle_y))
		rig.look_at_target(Vector2(750.0, 960.0))
		rig.right_hand_pose = "reach_open"
		
		# Input Timeline:
		# 'C': 5.80s -> press at 5.95s -> release 6.05s
		# '1': 6.05s -> press at 6.25s -> release 6.35s
		# '0': 6.35s -> press at 6.55s -> release 6.65s
		# '÷': 6.65s -> press at 6.90s -> release 7.00s
		# '1': 7.00s -> press at 7.20s -> release 7.30s
		# '=': 7.30s -> press at 7.55s -> release 7.65s
		if t < 6.05:
			_apply_button_interaction("C", 5.80, 5.95, 6.05, t, "", "0")
		elif t < 6.35:
			_apply_button_interaction("1", 6.05, 6.25, 6.35, t, "1", "1")
		elif t < 6.65:
			_apply_button_interaction("0", 6.35, 6.55, 6.65, t, "10", "10")
		elif t < 7.00:
			_apply_button_interaction("÷", 6.65, 6.90, 7.00, t, "10 ÷", "10")
		elif t < 7.30:
			_apply_button_interaction("1", 7.00, 7.20, 7.30, t, "10 ÷ 1", "1")
		else:
			_apply_button_interaction("=", 7.30, 7.55, 7.65, t, "10 ÷ 1 =", "10")
			if t >= 7.55:
				rig.set_expression("confident")

	# -----------------------------------------------------------------------
	# BEAT 5: Forbidden Calculation — "10 ÷ 0 = UNDEFINED" (7.7s - 10.0s, Frames 231-300)
	# -----------------------------------------------------------------------
	else:
		rig.lock_foot("left", Vector2(635.0, floor_ankle_y))
		rig.lock_foot("right", Vector2(695.0, floor_ankle_y))
		
		if t < 9.35:
			debug_layer.current_action_label = "EP001 Beat 5: Forbidden Calculation — '10 ÷ 0 = ?'"
			rig.root_pos = Vector2(675.0, standing_y)
			rig.torso_lean_deg = 6.8
			rig.head_tilt_deg = 3.5
			rig.look_at_target(Vector2(750.0, 960.0))
			rig.set_expression("thoughtful")
			rig.right_hand_pose = "reach_open"
			
			# Input Timeline:
			# 'C': 7.70s -> press at 7.85s -> release 7.95s
			# '1': 7.95s -> press at 8.15s -> release 8.25s
			# '0': 8.25s -> press at 8.45s -> release 8.55s
			# '÷': 8.55s -> press at 8.80s -> release 8.90s
			# '0': 8.90s -> press at 9.05s -> release 9.15s
			# '=': 9.15s -> press at 9.30s -> release 9.35s
			if t < 7.95:
				_apply_button_interaction("C", 7.70, 7.85, 7.95, t, "", "0")
			elif t < 8.25:
				_apply_button_interaction("1", 7.95, 8.15, 8.25, t, "1", "1")
			elif t < 8.55:
				_apply_button_interaction("0", 8.25, 8.45, 8.55, t, "10", "10")
			elif t < 8.90:
				_apply_button_interaction("÷", 8.55, 8.80, 8.90, t, "10 ÷", "10")
			elif t < 9.15:
				_apply_button_interaction("0", 8.90, 9.05, 9.15, t, "10 ÷ 0", "0")
			else:
				_apply_button_interaction("=", 9.15, 9.30, 9.35, t, "10 ÷ 0 =", "UNDEFINED", true)
		else:
			debug_layer.current_action_label = "EP001 Beat 5: 'UNDEFINED' ERROR VOID RECOIL (Shock Freeze)"
			var p_recoil = clampf((t - 9.35) / 0.25, 0.0, 1.0)
			var ease_recoil = _smoothstep(p_recoil)
			
			# Calculator flashes UNDEFINED error
			calc.set_display("10 ÷ 0 =", "UNDEFINED", true)
			calc.error_glow_pulse = sin((t - 9.35) * 16.0)
			
			# Character recoils back, torso leans backward, eyes wide shocked
			rig.root_pos = Vector2(lerpf(665.0, 640.0, ease_recoil), standing_y - 6.0 * ease_recoil)
			rig.torso_lean_deg = lerpf(6.0, -9.0, ease_recoil)
			rig.head_tilt_deg = lerpf(3.5, -6.5, ease_recoil)
			
			# Hand snaps back to chest
			var shock_hand = Vector2(615.0, 1175.0)
			rig.reach_hand_to(shock_hand, true, false)
			rig.right_hand_pose = "fist"
			rig.left_shoulder_deg = lerpf(4.0, 26.0, ease_recoil)
			
			rig.set_expression("surprised", 1.0)
			rig.look_at_target(calc.calc_pos + Vector2(120.0, 60.0))

func _apply_button_interaction(key: String, t_start: float, t_press: float, t_end: float, t_curr: float, expr_after: String, res_after: String, is_err: bool = false) -> void:
	var btn_pos = calc.get_button_world_pos(key)
	var hover_pos = btn_pos + Vector2(-18.0, -20.0)
	
	if t_curr < t_press:
		var p = (t_curr - t_start) / maxf(0.01, t_press - t_start)
		var hand_target = hover_pos.lerp(btn_pos, _smoothstep(p))
		rig.reach_hand_to(hand_target, true, false)
		if active_pressed_button == key:
			calc.release_button(key, hand_target)
			active_pressed_button = ""
	elif t_curr <= (t_press + 0.06):
		# EXACT PHYSICAL CONTACT: hand reaches button center
		rig.reach_hand_to(btn_pos, true, false)
		calc.press_button(key, btn_pos)
		calc.set_display(expr_after, res_after, is_err)
		active_pressed_button = key
		
		# Record evidence of physical contact
		var dist = rig.solved_right_fingertip.distance_to(btn_pos)
		contact_evidence.append({
			"key": key,
			"time": t_curr,
			"target_btn_pos": [btn_pos.x, btn_pos.y],
			"hand_solved_pos": [rig.solved_right_fingertip.x, rig.solved_right_fingertip.y],
			"contact_distance_px": dist,
			"contact_valid": (dist < 4.0),
			"lcd_expression": expr_after,
			"lcd_result": res_after,
			"is_error": is_err,
		})
	else:
		var p = (t_curr - (t_press + 0.06)) / maxf(0.01, t_end - (t_press + 0.06))
		var hand_target = btn_pos.lerp(hover_pos, _smoothstep(p))
		rig.reach_hand_to(hand_target, true, false)
		if active_pressed_button == key:
			calc.release_button(key, hand_target)
			active_pressed_button = ""
		calc.set_display(expr_after, res_after, is_err)
