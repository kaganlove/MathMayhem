extends Node2D

## Math Mayhem v13.2 — Validation Demonstration Test B: Contact-Driven Object Pickup
## Implements: Notice -> Prepare -> Reach -> Contact -> Grasp -> Lift -> Inspect -> Settle
## Uses InteractivePickupObject with 7 discrete states and 0.0px attachment continuity.

const CharacterRig2D = preload("res://scripts/character_rig_2d.gd")
const InteractivePickupObject = preload("res://scripts/interactive_pickup_object.gd")
const DebugOverlay = preload("res://scripts/debug_overlay.gd")

var rig: Node2D
var pickup_obj: Node2D
var debug_layer: Node2D

var is_debug_mode: bool = false
var fps: int = 30
var duration: float = 7.0
var output_dir: String = "res://temp_test_b_clean"

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

	# 1. Pickup Object
	pickup_obj = InteractivePickupObject.new()
	pickup_obj.name = "InteractivePickupObject"
	pickup_obj.object_type = "yellow_gadget"
	pickup_obj.ground_pos = Vector2(660.0, 1575.0)
	pickup_obj.size_px = Vector2(32.0, 36.0)
	pickup_obj.grip_offset = Vector2(0.0, -12.0)
	add_child(pickup_obj)

	# 2. Character Rig
	rig = CharacterRig2D.new()
	rig.name = "CharacterRig"
	rig.show_floor_item = true
	rig.pickup_object = pickup_obj
	add_child(rig)

	# 3. Debug Overlay
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
	var item_grip_target = pickup_obj.get_grip_world_pos()

	# Foot ground-anchors (strictly 0.0px drift throughout whole sequence)
	var left_lock = Vector2(510.0 - 13.0 * s, 1592.8)
	var right_lock = Vector2(510.0 + 13.0 * s, 1592.8)
	rig.lock_foot("left", left_lock)
	rig.lock_foot("right", right_lock)

	# -----------------------------------------------------------------------
	# Phase A: Notice (0.0s - 1.2s, Frames 0-36)
	# -----------------------------------------------------------------------
	if t < 1.2:
		debug_layer.current_action_label = "Test B: 1. NOTICE (Grounded object, inquisitive gaze)"
		rig.root_pos = Vector2(510.0, 1285.8)
		rig.release_hand_ik()
		pickup_obj.reset_to_ground()
		var p_look = clampf(t / 1.0, 0.0, 1.0)
		rig.look_at_target(item_grip_target)
		rig.set_expression("curious", p_look)
		rig.torso_lean_deg = lerpf(0.0, 6.0, ease(p_look, 0.5))

	# -----------------------------------------------------------------------
	# Phase B: Prepare (1.2s - 1.8s, Frames 36-54)
	# -----------------------------------------------------------------------
	elif t < 1.8:
		debug_layer.current_action_label = "Test B: 2. PREPARE (Weight shifts, knees begin flexion)"
		var p_prep = (t - 1.2) / 0.6
		rig.root_pos = Vector2(510.0, lerpf(1285.8, 1320.0, p_prep))
		rig.torso_lean_deg = lerpf(6.0, 12.0, p_prep)
		rig.look_at_target(item_grip_target)
		rig.set_expression("curious", 1.0)
		rig.right_hand_pose = "reach_open"

	# -----------------------------------------------------------------------
	# Phase C: Reach (1.8s - 3.2s, Frames 54-96)
	# -----------------------------------------------------------------------
	elif t < 3.2:
		debug_layer.current_action_label = "Test B: 3. REACH (Deep squat with hip counterbalance, hand reaches down)"
		pickup_obj.notify_reaching()
		var p_reach = (t - 1.8) / 1.4
		var ease_reach = ease(p_reach, 0.4)
		# Pelvis sits back to 485px, drops to 1475px
		rig.root_pos = Vector2(lerpf(510.0, 485.0, ease_reach), lerpf(1320.0, 1475.0, ease_reach))
		rig.torso_lean_deg = lerpf(12.0, 54.0, ease_reach)
		rig.look_at_target(item_grip_target)
		# 2-bone IK directly reaches the stationary item grip point with palm alignment
		rig.reach_hand_to(item_grip_target, true, true)
		rig.right_hand_pose = "reach_open"
		rig.left_shoulder_deg = lerpf(6.0, 24.0, ease_reach)
		rig.left_elbow_deg = lerpf(14.0, 50.0, ease_reach)

	# -----------------------------------------------------------------------
	# Phase D: Contact (3.2s - 3.5s, Frames 96-105)
	# -----------------------------------------------------------------------
	elif t < 3.5:
		debug_layer.current_action_label = "Test B: 4. CONTACT (Hand arrives at grip point, cups object boundary)"
		rig.root_pos = Vector2(485.0, 1475.0)
		rig.torso_lean_deg = 54.0
		rig.reach_hand_to(item_grip_target, true, true)
		rig.right_hand_pose = "grasp_contact"
		pickup_obj.establish_contact(rig.get_right_grip_pos())
		rig.look_at_target(item_grip_target)

	# -----------------------------------------------------------------------
	# Phase E: Grasp (3.5s - 3.9s, Frames 105-117)
	# -----------------------------------------------------------------------
	elif t < 3.9:
		debug_layer.current_action_label = "Test B: 5. GRASP (Hand closes into firm grip, 0.0px attachment continuity)"
		rig.root_pos = Vector2(485.0, 1475.0)
		rig.torso_lean_deg = 54.0
		rig.reach_hand_to(item_grip_target, true, true)
		rig.right_hand_pose = "grip_closed"
		pickup_obj.begin_grasp()
		if not pickup_obj.is_grasped:
			var success = pickup_obj.grasp(rig.get_right_grip_pos(), rig.get_right_hand_rot_deg())
			if not success:
				printerr("Test B Grasp Failed: Hand grip distance %.2f px" % [rig.get_right_grip_pos().distance_to(pickup_obj.get_grip_world_pos())])
		var p_e = (t - 3.5) / 0.4
		rig.set_expression_blend("curious", "confident", p_e)
		rig.look_at_target(item_grip_target)

	# -----------------------------------------------------------------------
	# Phase F: Lift (3.9s - 4.7s, Frames 117-141)
	# -----------------------------------------------------------------------
	elif t < 4.7:
		debug_layer.current_action_label = "Test B: 6. LIFT (Body rises, object follows hand with 0.0px drift)"
		var p_lift = (t - 3.9) / 0.8
		var ease_lift = ease(p_lift, 0.45)
		rig.root_pos = Vector2(lerpf(485.0, 500.0, ease_lift), lerpf(1475.0, 1340.0, ease_lift))
		rig.torso_lean_deg = lerpf(54.0, 22.0, ease_lift)
		# Hand drives object upward
		var lift_target = item_grip_target.lerp(Vector2(610.0, 1300.0), ease_lift)
		rig.reach_hand_to(lift_target, true, true)
		rig.right_hand_pose = "grip_closed"
		pickup_obj.start_lifting(rig.get_right_grip_pos(), rig.get_right_hand_rot_deg())
		rig.look_at_target(pickup_obj.world_pos)
		rig.set_expression_blend("confident", "thoughtful", p_lift)

	# -----------------------------------------------------------------------
	# Phase G: Rise & Inspect (4.7s - 5.8s, Frames 141-174)
	# -----------------------------------------------------------------------
	elif t < 5.8:
		debug_layer.current_action_label = "Test B: 7. INSPECT (Standing upright, object held at chest level)"
		var p_stand = (t - 4.7) / 1.1
		var ease_stand = ease(p_stand, 0.5)
		rig.root_pos = Vector2(lerpf(500.0, 510.0, ease_stand), lerpf(1340.0, 1285.8, ease_stand))
		rig.torso_lean_deg = lerpf(22.0, 4.0, ease_stand)
		var chest_pos = Vector2(575.0, 1140.0)
		var cur_hand = Vector2(610.0, 1300.0).lerp(chest_pos, ease_stand)
		rig.reach_hand_to(cur_hand, true, true)
		rig.right_hand_pose = "carry_grip"
		pickup_obj.update_carried_transform(rig.get_right_grip_pos(), rig.get_right_hand_rot_deg())
		rig.look_at_target(pickup_obj.world_pos)
		rig.set_expression("thoughtful", 1.0)
		rig.left_shoulder_deg = lerpf(24.0, 8.0, ease_stand)
		rig.left_elbow_deg = lerpf(50.0, 20.0, ease_stand)

	# -----------------------------------------------------------------------
	# Phase H: Settle & Smirk (5.8s - 7.0s, Frames 174-210)
	# -----------------------------------------------------------------------
	else:
		debug_layer.current_action_label = "Test B: 8. SETTLE & SMIRK (Comedic satisfaction, secure carry grip)"
		rig.root_pos = Vector2(510.0, 1285.8)
		rig.torso_lean_deg = 4.0
		var float_y = sin((t - 5.8) * PI * 2.0) * 3.0
		var hold_pos = Vector2(575.0, 1140.0 + float_y)
		rig.reach_hand_to(hold_pos, true, true)
		rig.right_hand_pose = "carry_grip"
		pickup_obj.update_carried_transform(rig.get_right_grip_pos(), rig.get_right_hand_rot_deg())
		rig.look_at_target(pickup_obj.world_pos)
		var p_smirk = clampf((t - 5.8) / 0.5, 0.0, 1.0)
		rig.set_expression_blend("thoughtful", "satisfied", p_smirk)
		rig.left_shoulder_deg = 12.0
		rig.left_elbow_deg = 65.0
