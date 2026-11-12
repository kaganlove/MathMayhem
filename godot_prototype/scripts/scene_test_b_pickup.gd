extends Node2D

## Math Mayhem v13 — Validation Demonstration Test B: Object Pickup
## Demonstrates: Notice floor object -> Bend down with knee flex & foot locking ->
## Hand IK pickup -> Return upright -> Gaze inspection -> Comedic satisfaction

const CharacterRig2D = preload("res://scripts/character_rig_2d.gd")
const DebugOverlay = preload("res://scripts/debug_overlay.gd")

var rig: Node2D
var debug_layer: Node2D

var is_debug_mode: bool = false
var fps: int = 30
var duration: float = 7.0
var output_dir: String = "res://temp_test_b_clean"
var floor_item_target: Vector2 = Vector2(670.0, 1590.0)

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

	# Character Rig
	rig = CharacterRig2D.new()
	rig.name = "CharacterRig"
	rig.show_floor_item = true
	rig.floor_item_pos = floor_item_target
	rig.is_item_held = false
	add_child(rig)

	# Debug Overlay
	debug_layer = DebugOverlay.new()
	debug_layer.name = "DebugOverlay"
	debug_layer.target_rig = rig
	debug_layer.show_debug = is_debug_mode
	add_child(debug_layer)

func _render_sequence() -> void:
	var total_frames: int = int(round(duration * float(fps)))
	print("Starting Test B Render: total_frames=%d, debug=%s" % [total_frames, str(is_debug_mode)])

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
			print("Rendered Test B frame %d / %d (%.2fs / %.2fs)" % [i, total_frames, t, duration])

	print("Test B Render finished. Saved to: ", output_dir)
	get_tree().quit(0)

func _evaluate_state_at(t: float) -> void:
	debug_layer.current_time_sec = t
	var s: float = rig.character_scale

	# Planted foot anchors (strictly 0.0px drift throughout whole squat and stand)
	var left_lock = Vector2(510.0 - 13.0 * s, 1592.8)
	var right_lock = Vector2(510.0 + 13.0 * s, 1592.8)
	rig.lock_foot("left", left_lock)
	rig.lock_foot("right", right_lock)

	# Beat 1: Idle & Discovery (0.0s - 1.2s)
	if t < 1.2:
		debug_layer.current_action_label = "Test B: 1. DISCOVERY (Standing upright, spots shiny floor object)"
		rig.root_pos = Vector2(510.0, 1285.8)
		rig.release_hand_ik()
		rig.is_item_held = false
		var p_look = clampf(t / 1.0, 0.0, 1.0)
		rig.look_at_target(floor_item_target)
		rig.set_expression("curious", p_look)
		rig.torso_lean_deg = lerpf(0.0, 8.0, ease(p_look, 0.5))

	# Beat 2: Crouch & Reach (1.2s - 3.0s)
	elif t < 3.0:
		debug_layer.current_action_label = "Test B: 2. SQUAT & REACH (Pelvis lowers, knee IK flexes, hand reaches floor item)"
		var p_crouch = (t - 1.2) / 1.8
		var ease_crouch = ease(p_crouch, 0.4)
		rig.root_pos = Vector2(510.0, lerpf(1285.8, 1375.0, ease_crouch))
		rig.torso_lean_deg = lerpf(8.0, 32.0, ease_crouch)
		rig.look_at_target(floor_item_target)
		# 2-bone IK reaches down to item
		rig.reach_hand_to(floor_item_target, true)
		rig.right_hand_pose = "reach_open" if p_crouch < 0.85 else "point"
		rig.left_shoulder_deg = lerpf(4.0, 22.0, ease_crouch)
		rig.left_elbow_deg = lerpf(12.0, 45.0, ease_crouch) # Balance counter-pose

	# Beat 3: Grasp Item (3.0s - 3.8s)
	elif t < 3.8:
		debug_layer.current_action_label = "Test B: 3. GRASP (Hand establishes contact, item attaches)"
		rig.root_pos = Vector2(510.0, 1375.0)
		rig.torso_lean_deg = 32.0
		rig.reach_hand_to(floor_item_target, true)
		rig.right_hand_pose = "point"
		rig.is_item_held = true
		rig.set_expression("confident", 0.8)

	# Beat 4: Rise Upright with Item (3.8s - 5.2s)
	elif t < 5.2:
		debug_layer.current_action_label = "Test B: 4. RISE UPRIGHT (Pelvis returns to baseline, lifts item to chest)"
		var p_rise = (t - 3.8) / 1.4
		var ease_rise = ease(p_rise, 0.5)
		rig.root_pos = Vector2(510.0, lerpf(1375.0, 1285.8, ease_rise))
		rig.torso_lean_deg = lerpf(32.0, 4.0, ease_rise)
		# Hand brings item up to chest height
		var chest_hold_pos = Vector2(575.0, 1140.0)
		var cur_hand = floor_item_target.lerp(chest_hold_pos, ease_rise)
		rig.reach_hand_to(cur_hand, true)
		rig.look_at_target(cur_hand)
		rig.set_expression("thoughtful", 1.0)
		rig.left_shoulder_deg = lerpf(22.0, 6.0, ease_rise)
		rig.left_elbow_deg = lerpf(45.0, 14.0, ease_rise)

	# Beat 5: Inspect & Smirk (5.2s - 7.0s)
	else:
		debug_layer.current_action_label = "Test B: 5. INSPECTION (Gaze inspects gadget, delighted smirk)"
		rig.root_pos = Vector2(510.0, 1285.8)
		rig.torso_lean_deg = 4.0
		var inspect_pos = Vector2(575.0, 1135.0 + sin((t - 5.2) * PI * 2.0) * 4.0)
		rig.reach_hand_to(inspect_pos, true)
		rig.look_at_target(inspect_pos)
		rig.set_expression("satisfied", 1.0)
		rig.left_shoulder_deg = 12.0
		rig.left_elbow_deg = 65.0 # Delighted contrapposto
