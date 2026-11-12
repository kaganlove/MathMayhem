extends Node2D

## Math Mayhem v13 — State Machine Animated Scene Runner
## Orchestrates the full target-driven, foot-anchored, expressive interaction sequence.

const CharacterRig2D = preload("res://scripts/character_rig_2d.gd")
const InteractiveButton = preload("res://scripts/interactive_button.gd")
const CharacterStateMachine = preload("res://scripts/character_state_machine.gd")
const DebugOverlay = preload("res://scripts/debug_overlay.gd")

var rig: Node2D
var button_prop: Node2D
var sm: Node
var debug_layer: Node2D

var is_debug_mode: bool = false
var fps: int = 30
var duration: float = 11.0
var output_dir: String = "res://temp_v13_clean"

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

	# 1. Button Prop
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

	# 3. State Machine
	sm = CharacterStateMachine.new()
	sm.name = "CharacterStateMachine"
	sm.rig = rig
	sm.interactive_target = button_prop
	add_child(sm)

	# 4. Debug Overlay
	debug_layer = DebugOverlay.new()
	debug_layer.name = "DebugOverlay"
	debug_layer.target_rig = rig
	debug_layer.show_debug = is_debug_mode
	add_child(debug_layer)

func _render_sequence() -> void:
	var total_frames: int = int(round(duration * float(fps)))
	print("Starting v13 State Machine Render: total_frames=%d, debug=%s" % [total_frames, str(is_debug_mode)])

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
			print("Rendered v13 frame %d / %d (%.2fs / %.2fs)" % [i, total_frames, t, duration])

	print("v13 Render finished. Saved to: ", output_dir)
	get_tree().quit(0)

func _evaluate_state_at(t: float) -> void:
	debug_layer.current_time_sec = t
	var s: float = rig.character_scale

	# Synchronize rig button pedestal state to button prop
	rig.button_depress_px = button_prop.current_depression
	rig.button_glow_alpha = button_prop.glow_alpha

	# -----------------------------------------------------------------------
	# 14-State Narrative Progression with Foot Locking & IK
	# -----------------------------------------------------------------------
	if t < 0.45:
		# IDLE (0.0s - 0.45s)
		sm.transition_to(CharacterStateMachine.State.IDLE)
		debug_layer.current_action_label = "1. IDLE (Living breath, tall stance)"
		rig.root_pos = Vector2(380.0, 1285.8)
		rig.lock_foot("left", Vector2(380.0 - 13.0 * s, 1592.8))
		rig.lock_foot("right", Vector2(380.0 + 13.0 * s, 1592.8))
		rig.torso_squash = 1.0 + sin(t * PI * 2.0) * 0.006

	elif t < 1.20:
		# NOTICE & LOOK (0.45s - 1.2s)
		sm.transition_to(CharacterStateMachine.State.NOTICE_TARGET)
		debug_layer.current_action_label = "2. NOTICE_TARGET (Eyes & head aim at button, C-curve lean)"
		rig.look_at_target(button_prop.get_contact_pos())
		var p_notice = (t - 0.45) / 0.75
		rig.torso_lean_deg = lerpf(0.0, 14.0, ease(p_notice, 0.5))

	elif t < 2.60:
		# APPROACH WALK (1.2s - 2.6s)
		debug_layer.current_action_label = "3. APPROACH (Grounded stride to button pedestal)"
		rig.unlock_foot("left")
		rig.unlock_foot("right")
		rig.clear_gaze_target()
		rig.head_tilt_deg = -3.0
		var p_walk = (t - 1.2) / 1.4
		var cur_x = lerpf(380.0, 540.0, ease(p_walk, 0.4))
		rig.root_pos = Vector2(cur_x, 1285.8 + sin(p_walk * PI * 4.0) * 8.0)
		rig.left_thigh_deg = sin(p_walk * PI * 4.0) * 18.0
		rig.left_shin_deg = -absf(cos(p_walk * PI * 4.0)) * 24.0
		rig.right_thigh_deg = -sin(p_walk * PI * 4.0) * 18.0
		rig.right_shin_deg = -absf(sin(p_walk * PI * 4.0)) * 24.0
		rig.left_shoulder_deg = -sin(p_walk * PI * 4.0) * 14.0
		rig.right_shoulder_deg = sin(p_walk * PI * 4.0) * 14.0

	elif t < 4.00:
		# CONSIDER & HESITATE (2.6s - 4.0s)
		sm.transition_to(CharacterStateMachine.State.CONSIDER)
		debug_layer.current_action_label = "4. CONSIDER (Hand hovers 28px over button, hip contrapposto)"
		rig.root_pos = Vector2(540.0, 1285.8)
		# Stance Foot Locks
		rig.lock_foot("left", Vector2(540.0 - 13.0 * s, 1592.8))
		rig.lock_foot("right", Vector2(540.0 + 13.0 * s, 1592.8))
		rig.look_at_target(button_prop.get_contact_pos())
		# Target-driven hovering hand
		rig.reach_hand_to(button_prop.get_pre_contact_pos(), true)

	elif t < 4.40:
		# ANTICIPATE & REACH (4.0s - 4.4s)
		sm.transition_to(CharacterStateMachine.State.REACH)
		debug_layer.current_action_label = "5. REACH (Clavicle leads, 2-bone IK reaches contact point)"
		var p_reach = (t - 4.0) / 0.4
		var reach_pos = button_prop.get_pre_contact_pos().lerp(button_prop.get_contact_pos(), p_reach)
		rig.reach_hand_to(reach_pos, true)
		rig.torso_lean_deg = lerpf(4.0, 10.0, p_reach)
		rig.right_shoulder_protract_px = lerpf(0.0, 10.0, p_reach)

	elif t < 4.80:
		# CONTACT & PRESS HOLD (4.4s - 4.8s)
		sm.transition_to(CharacterStateMachine.State.PRESS)
		debug_layer.current_action_label = "6. PRESS & HOLD (Coupled hand locked to -8px depressing cap)"
		var p_press = clampf((t - 4.4) / 0.1, 0.0, 1.0)
		button_prop.set_depression(lerpf(0.0, 8.0, p_press))
		rig.attach_hand_to_button()
		rig.torso_squash = 0.98

	elif t < 5.20:
		# ACTIVATION & RELEASE (4.8s - 5.2s)
		sm.transition_to(CharacterStateMachine.State.RELEASE)
		debug_layer.current_action_label = "7. RELEASE (Energy pulse, shockwave radiates, hand lifts)"
		button_prop.activate()
		var p_rel = (t - 4.8) / 0.4
		button_prop.set_depression(lerpf(8.0, 0.0, p_rel))
		var lift_pos = button_prop.get_contact_pos().lerp(button_prop.get_release_pos(), p_rel)
		rig.reach_hand_to(lift_pos, true)

	elif t < 6.80:
		# REACT (5.2s - 6.8s)
		sm.transition_to(CharacterStateMachine.State.REACT)
		debug_layer.current_action_label = "8. REACT (Shock recoil snap, hair drag, braced rear catch, freeze)"
		button_prop.glow_alpha = 0.0
		rig.release_hand_ik()
		rig.clear_gaze_target()
		var p_recoil = clampf((t - 5.2) / 0.25, 0.0, 1.0)
		rig.root_pos = Vector2(lerpf(540.0, 495.0, p_recoil), 1285.8 - p_recoil * 8.0)
		# Rear foot remains locked
		rig.lock_foot("left", Vector2(495.0 - 13.0 * s, 1592.8))

	elif t < 9.00:
		# RECOVER (6.8s - 9.0s)
		sm.transition_to(CharacterStateMachine.State.RECOVER)
		debug_layer.current_action_label = "9. RECOVER (Torso eases, hand sweeps to bridge, glasses push bounce)"
		var p_rec = (t - 6.8) / 2.2
		rig.root_pos = Vector2(lerpf(495.0, 520.0, p_rec), 1285.8)
		rig.lock_foot("left", Vector2(520.0 - 13.0 * s, 1592.8))
		rig.lock_foot("right", Vector2(520.0 + 13.0 * s, 1592.8))
		if t >= 8.1 and t <= 8.35:
			rig.glasses_slip_px = -1.5 # Bounce!
		else:
			rig.glasses_slip_px = 0.0

	else:
		# AMUSED PAYOFF (9.0s - 11.0s)
		debug_layer.current_action_label = "10. AMUSED PAYOFF (Cocky ease, button gesture, final comedic hold)"
		rig.root_pos = Vector2(520.0, 1285.8)
		rig.set_expression("satisfied", 1.0)
		rig.right_hand_pose = "amused"
		rig.left_hand_pose = "relaxed"
