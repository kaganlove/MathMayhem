extends Node2D

## Math Mayhem v13 — Validation Demonstration Test C: Unexpected Surprise
## Demonstrates: Casual occupied task -> Sudden off-screen alert -> Explosive recoil ->
## Braced rear foot lock -> Glasses slip & catch -> Confused recovery & chin touch

const CharacterRig2D = preload("res://scripts/character_rig_2d.gd")
const DebugOverlay = preload("res://scripts/debug_overlay.gd")

var rig: Node2D
var debug_layer: Node2D

var is_debug_mode: bool = false
var fps: int = 30
var duration: float = 7.0
var output_dir: String = "res://temp_test_c_clean"

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
	add_child(rig)

	# Debug Overlay
	debug_layer = DebugOverlay.new()
	debug_layer.name = "DebugOverlay"
	debug_layer.target_rig = rig
	debug_layer.show_debug = is_debug_mode
	add_child(debug_layer)

func _render_sequence() -> void:
	var total_frames: int = int(round(duration * float(fps)))
	print("Starting Test C Render: total_frames=%d, debug=%s" % [total_frames, str(is_debug_mode)])

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
			print("Rendered Test C frame %d / %d (%.2fs / %.2fs)" % [i, total_frames, t, duration])

	print("Test C Render finished. Saved to: ", output_dir)
	get_tree().quit(0)

func _evaluate_state_at(t: float) -> void:
	debug_layer.current_time_sec = t
	var s: float = rig.character_scale

	# Beat 1: Casual occupied task (0.0s - 1.6s)
	if t < 1.6:
		debug_layer.current_action_label = "Test C: 1. CASUAL TASK (Relaxed breathing, idle rhythm)"
		rig.root_pos = Vector2(530.0, 1285.8)
		rig.lock_foot("left", Vector2(530.0 - 13.0 * s, 1592.8))
		rig.lock_foot("right", Vector2(530.0 + 13.0 * s, 1592.8))
		rig.release_hand_ik()
		rig.clear_gaze_target()
		rig.set_expression("neutral")
		rig.torso_lean_deg = 1.5 + sin(t * PI * 2.0) * 0.8
		rig.right_shoulder_deg = 8.0 + sin(t * PI * 2.0) * 3.0
		rig.right_elbow_deg = 24.0 + sin(t * PI * 2.0) * 4.0
		rig.left_shoulder_deg = 6.0
		rig.left_elbow_deg = 20.0
		rig.right_hand_pose = "relaxed"
		rig.left_hand_pose = "relaxed"

	# Beat 2: Sudden Off-Screen Alert (1.6s - 2.5s)
	elif t < 2.5:
		debug_layer.current_action_label = "Test C: 2. ALERT (Sudden off-screen disturbance, gaze snaps)"
		var p_alert = (t - 1.6) / 0.9
		rig.look_at_target(Vector2(950.0, 780.0))
		rig.torso_lean_deg = lerpf(1.5, 6.0, p_alert)
		rig.set_expression("curious", 1.0)
		rig.right_brow_raise_px = 6.0
		rig.left_brow_raise_px = 2.0

	# Beat 3: Anticipation Dip & Explosive Recoil (2.5s - 4.0s)
	elif t < 4.0:
		rig.clear_gaze_target()
		if t < 2.58:
			# 2-frame (0.08s) quick anticipation squash into the disturbance
			debug_layer.current_action_label = "Test C: 3. ANTICIPATION DIP (Torso squash, brief freeze before blast)"
			var p_dip = (t - 2.5) / 0.08
			rig.torso_squash = lerpf(1.0, 0.94, p_dip)
			rig.torso_lean_deg = lerpf(6.0, 8.5, p_dip)
			rig.set_expression("surprised", 0.7)
		else:
			debug_layer.current_action_label = "Test C: 3. SHOCK RECOIL (Full body recoil, glasses slip, braced rear foot)"
			var p_rec = clampf((t - 2.58) / 0.26, 0.0, 1.0)
			var ease_rec = ease(p_rec, 0.2)
			rig.torso_squash = lerpf(0.94, 1.02, ease_rec)
			# Pelvis snaps backward and sinks down into rear brace (zero float)
			rig.root_pos = Vector2(lerpf(530.0, 495.0, ease_rec), 1285.8 + ease_rec * 6.0)
			rig.torso_lean_deg = lerpf(8.5, -18.0, ease_rec)
			rig.shoulder_shrug_px = lerpf(0.0, 26.0, ease_rec)
			rig.glasses_slip_px = lerpf(0.0, 8.0, ease_rec)
			rig.hair_lag_deg = lerpf(0.0, -30.0, ease_rec)
			rig.set_expression("surprised", 1.0)
			rig.right_hand_pose = "recoil"
			rig.left_hand_pose = "recoil"
			rig.right_shoulder_deg = lerpf(8.0, -22.0, ease_rec)
			rig.right_elbow_deg = lerpf(24.0, 85.0, ease_rec)
			rig.left_shoulder_deg = lerpf(6.0, -18.0, ease_rec)
			rig.left_elbow_deg = lerpf(20.0, 78.0, ease_rec)

	# Beat 4: Hesitant Recovery & Glasses Push (4.0s - 5.5s)
	elif t < 5.5:
		debug_layer.current_action_label = "Test C: 4. RECOVERY (Cautious ease, glasses reset, confused scan)"
		var p_recov = (t - 4.0) / 1.5
		var ease_recov = ease(p_recov, 0.5)
		rig.root_pos = Vector2(lerpf(495.0, 520.0, ease_recov), 1285.8)
		rig.torso_lean_deg = lerpf(-18.0, -3.0, ease_recov)
		rig.shoulder_shrug_px = lerpf(26.0, 0.0, ease_recov)
		rig.hair_lag_deg = 0.0
		if t >= 4.7 and t <= 4.95:
			rig.glasses_slip_px = -1.5 # Reset bounce
		else:
			rig.glasses_slip_px = 0.0
		rig.set_expression("confused", 0.9)
		rig.right_hand_pose = "relaxed"
		rig.left_hand_pose = "chin_touch"

	# Beat 5: Bewildered Chin Scratch & Shrug (5.5s - 7.0s)
	else:
		debug_layer.current_action_label = "Test C: 5. BEWILDERMENT (Asymmetrical brows, chin scratch, skeptical pose)"
		rig.root_pos = Vector2(520.0, 1285.8)
		rig.torso_lean_deg = -3.0
		rig.set_expression("confused", 1.0)
		rig.left_hand_pose = "chin_touch"
		rig.right_hand_pose = "shrug_open"
		rig.left_shoulder_deg = -12.0
		rig.left_elbow_deg = 82.0
		rig.right_shoulder_deg = 18.0
		rig.right_elbow_deg = 48.0
