extends Node2D

## Math Mayhem v13 — Validation Demonstration Test A: Button Interaction
## Demonstrates: Notice -> Hesitate -> Press -> Hold -> Pulse -> Recoil -> Recover

const CharacterRig2D = preload("res://scripts/character_rig_2d.gd")
const InteractiveButton = preload("res://scripts/interactive_button.gd")
const DebugOverlay = preload("res://scripts/debug_overlay.gd")

var rig: Node2D
var button_prop: Node2D
var debug_layer: Node2D

var is_debug_mode: bool = false
var fps: int = 30
var duration: float = 7.0
var output_dir: String = "res://temp_test_a_clean"

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

	# 1. Button Prop at standard reachable location
	button_prop = InteractiveButton.new()
	button_prop.name = "InteractiveButton"
	button_prop.pedestal_pos = Vector2(760.0, 1220.0)
	add_child(button_prop)

	# 2. Character Rig
	rig = CharacterRig2D.new()
	rig.name = "CharacterRig"
	rig.show_button_pedestal = true
	rig.button_pedestal_pos = button_prop.pedestal_pos
	add_child(rig)

	# 3. Debug Overlay
	debug_layer = DebugOverlay.new()
	debug_layer.name = "DebugOverlay"
	debug_layer.target_rig = rig
	debug_layer.show_debug = is_debug_mode
	add_child(debug_layer)

func _render_sequence() -> void:
	var total_frames: int = int(round(duration * float(fps)))
	print("Starting Test A Render: total_frames=%d, debug=%s" % [total_frames, str(is_debug_mode)])

	var dir = DirAccess.open("res://")
	if not dir.dir_exists(output_dir):
		dir.make_dir_recursive(output_dir)

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
			print("Rendered Test A frame %d / %d (%.2fs / %.2fs)" % [i, total_frames, t, duration])

	print("Test A Render finished. Saved to: ", output_dir)
	get_tree().quit(0)

func _evaluate_state_at(t: float) -> void:
	debug_layer.current_time_sec = t
	var s: float = rig.character_scale

	# Sync visual button state
	rig.button_depress_px = button_prop.current_depression
	rig.button_glow_alpha = button_prop.glow_alpha

	# Beat 1: Idle & Notice (0.0s - 1.2s)
	if t < 1.2:
		debug_layer.current_action_label = "Test A: 1. NOTICE (Standing tall, gaze tracks button)"
		rig.root_pos = Vector2(540.0, 1285.8)
		rig.lock_foot("left", Vector2(540.0 - 13.0 * s, 1592.8))
		rig.lock_foot("right", Vector2(540.0 + 13.0 * s, 1592.8))
		rig.release_hand_ik()
		var p_notice = clampf(t / 1.0, 0.0, 1.0)
		rig.set_expression("curious", p_notice)
		rig.look_at_target(button_prop.get_contact_pos())
		rig.torso_lean_deg = lerpf(0.0, 6.0, ease(p_notice, 0.5))

	# Beat 2: Consider & Hesitate (1.2s - 2.4s)
	elif t < 2.4:
		debug_layer.current_action_label = "Test A: 2. HESITATE (2-bone IK pre-contact hover, hip contrapposto)"
		var p_hes = (t - 1.2) / 1.2
		rig.set_expression("hesitant", 1.0)
		rig.look_at_target(button_prop.get_contact_pos())
		var hover_target = button_prop.get_pre_contact_pos()
		rig.reach_hand_to(hover_target, true)
		rig.torso_lean_deg = lerpf(6.0, 10.0, p_hes)
		rig.right_hand_pose = "hesitant"
		rig.left_shoulder_deg = 14.0
		rig.left_elbow_deg = 72.0

	# Beat 3: Anticipate & Press (2.4s - 3.2s)
	elif t < 3.2:
		debug_layer.current_action_label = "Test A: 3. PRESS (Exact geometric contact, hand drives plunger)"
		var p_press = (t - 2.4) / 0.8
		rig.set_expression("confident", 1.0)
		rig.right_hand_pose = "press"
		if p_press < 0.35:
			# Reaching to contact point
			var reach_p = p_press / 0.35
			var c_pos = button_prop.get_pre_contact_pos().lerp(button_prop.get_contact_pos(), reach_p)
			rig.reach_hand_to(c_pos, true)
		else:
			# Hand contact coupled to button depression
			var depress_p = (p_press - 0.35) / 0.65
			button_prop.set_depression(lerpf(0.0, 8.0, depress_p))
			rig.attach_hand_to_button()

	# Beat 4: Hold & Wait (3.2s - 4.2s)
	elif t < 4.2:
		debug_layer.current_action_label = "Test A: 4. HOLD & WAIT (Coupled hand locked, expression shifts)"
		button_prop.set_depression(8.0)
		rig.attach_hand_to_button()
		rig.set_expression("thoughtful", 1.0)

	# Beat 5: Sudden Shock & Recoil (4.2s - 5.4s)
	elif t < 5.4:
		debug_layer.current_action_label = "Test A: 5. RECOIL (Shock snap, braced rear foot 0.0px drift)"
		button_prop.activate()
		button_prop.set_depression(0.0)
		rig.detach_hand_from_button()
		rig.clear_gaze_target()
		var p_recoil = clampf((t - 4.2) / 0.3, 0.0, 1.0)
		rig.root_pos = Vector2(lerpf(540.0, 505.0, p_recoil), 1285.8 + p_recoil * 6.0)
		rig.torso_lean_deg = lerpf(10.0, -18.0, p_recoil)
		rig.shoulder_shrug_px = lerpf(0.0, 24.0, p_recoil)
		rig.glasses_slip_px = lerpf(0.0, 7.0, p_recoil)
		rig.hair_lag_deg = lerpf(0.0, -28.0, p_recoil)
		rig.set_expression("surprised", 1.0)
		rig.right_hand_pose = "recoil"
		rig.left_hand_pose = "recoil"

	# Beat 6: Recover & Amused Payoff (5.4s - 7.0s)
	else:
		debug_layer.current_action_label = "Test A: 6. RECOVER (Glasses reset, satisfied comedic smirk)"
		var p_rec = (t - 5.4) / 1.6
		rig.root_pos = Vector2(lerpf(505.0, 530.0, p_rec), 1285.8)
		rig.torso_lean_deg = lerpf(-18.0, -2.0, p_rec)
		rig.shoulder_shrug_px = lerpf(24.0, 0.0, p_rec)
		rig.hair_lag_deg = 0.0
		if t >= 6.1 and t <= 6.35:
			rig.glasses_slip_px = -1.5 # Bounce back onto nose
		else:
			rig.glasses_slip_px = 0.0
		rig.set_expression("satisfied", 1.0)
		rig.right_hand_pose = "amused"
		rig.left_hand_pose = "relaxed"
