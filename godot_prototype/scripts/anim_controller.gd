class_name AnimationController
extends Node

## Master Animation Controller for Math Mayhem Godot 2D Prototype (v9.0)
## Drives the CharacterRig2D properties through authored performance keyframes.
## Implements Milestone 3 (Walk Cycle), Milestone 4 (Reach & Recovery),
## Milestone 5 (Acting: Curiosity/Surprise/Recovery), and Milestone 8 (Combined 8.0s Proof of Concept).

@export var rig: Node2D
@export var debug_overlay: Node2D

var current_time: float = 0.0
var active_clip: String = "full_poc"
var clip_duration: float = 8.0

# Base standing heights (for character_scale = 1.70, floor_y = 1620.0)
const STANDING_Y: float = 1293.6
const TARGET_OBJ_POS: Vector2 = Vector2(740.0, 1220.0)

const PoseLibrary = preload("res://scripts/pose_library.gd")
const AnimationBuilder = preload("res://scripts/animation_builder.gd")
const PoseLibraryV12 = preload("res://scripts/pose_library_v12.gd")
const AnimationBuilderV12 = preload("res://scripts/animation_builder_v12.gd")

var anim_player: AnimationPlayer = null

const CLIP_DURATIONS: Dictionary = {
	"v12_six_poses": 6.0,
	"v12_stepped_blocking": 11.5,
	"mysterious_button": 10.0,
	"mysterious_button_stepped": 10.0,
	"six_poses": 6.0,
	"intensity_study": 9.0,
	"test_c_curiosity": 3.0,
	"test_d_surprise": 3.0,
	"test_e_confusion_satisfaction": 4.5,
	"combined_acting": 11.0,
	# Backward compatible clips:
	"test_a_walk": 2.5,
	"test_b_reach": 2.5,
	"test_c_acting": 2.5,
	"full_poc": 8.0
}

func _ready() -> void:
	if active_clip == "":
		set_clip("mysterious_button")
	_setup_animation_player()

func _setup_animation_player() -> void:
	if anim_player != null:
		return
	anim_player = AnimationPlayer.new()
	anim_player.name = "RigAnimationPlayer"
	anim_player.root_node = NodePath("../..")
	add_child(anim_player)
	
	var lib = AnimationLibrary.new()
	var master_anim = AnimationBuilder.create_mysterious_button_animation(false)
	var stepped_anim = AnimationBuilder.create_mysterious_button_animation(true)
	var v12_stepped = AnimationBuilderV12.create_v12_animation(true)
	
	lib.add_animation("mysterious_button", master_anim)
	lib.add_animation("mysterious_button_stepped", stepped_anim)
	lib.add_animation("v12_stepped_blocking", v12_stepped)
	anim_player.add_animation_library("", lib)
	
	# Save reusable resources to disk (Milestone 7 & v12)
	ResourceSaver.save(master_anim, "res://animations/mysterious_button_master.res")
	ResourceSaver.save(stepped_anim, "res://animations/mysterious_button_stepped.res")
	ResourceSaver.save(v12_stepped, "res://animations/mysterious_button_v12_stepped.res")

func set_clip(clip_name: String) -> void:
	active_clip = clip_name
	clip_duration = CLIP_DURATIONS.get(clip_name, 10.0)
	current_time = 0.0

func evaluate_at(t: float) -> void:
	if rig == null:
		return
		
	if active_clip == "v12_six_poses":
		_evaluate_v12_six_poses(t)
	elif active_clip == "v12_stepped_blocking":
		_evaluate_v12_stepped_blocking(t)
	elif active_clip == "mysterious_button":
		_evaluate_mysterious_button(t, false)
	elif active_clip == "mysterious_button_stepped":
		_evaluate_mysterious_button(t, true)
	elif active_clip == "six_poses":
		_evaluate_six_poses(t)
	elif active_clip == "intensity_study":
		_evaluate_intensity_study(t)
	elif active_clip == "test_c_curiosity":
		_evaluate_test_c_curiosity(t)
	elif active_clip == "test_d_surprise":
		_evaluate_test_d_surprise(t)
	elif active_clip == "test_e_confusion_satisfaction":
		_evaluate_test_e_confusion_satisfaction(t)
	elif active_clip == "combined_acting":
		_evaluate_combined_acting(t)
	elif active_clip == "test_a_walk":
		_evaluate_test_a_walk(t)
	elif active_clip == "test_b_reach":
		_evaluate_test_b_reach(t)
	elif active_clip == "test_c_acting":
		_evaluate_test_c_acting(t)
	else:
		_evaluate_full_poc(t)
		
	if debug_overlay != null:
		debug_overlay.set("current_time_sec", t)

func _evaluate_mysterious_button(t: float, is_stepped: bool) -> void:
	_setup_animation_player()
	var anim_name: String = "mysterious_button_stepped" if is_stepped else "mysterious_button"
	anim_player.play(anim_name)
	anim_player.seek(t, true)
	
	# Action labels and foot planting telemetry for debug overlay
	var label: String
	if t < 1.5:
		label = "Beat 1: Discovery & Curious Notice"
	elif t < 3.5:
		label = "Beat 2: Weight-Balanced Approach"
	elif t < 5.0:
		label = "Beat 3: Hand Pauses (Hesitation & Doubt)"
	elif t < 6.5:
		label = "Beat 4: Decisive Contact & Button Depress (-8px)"
	elif t < 7.6:
		label = "Beat 5/6: Consequence Flash & Explosive Recoil Hold"
	else:
		label = "Beat 7: Glasses Slide-Up & Intrigued Smirk"
		
	if debug_overlay != null:
		debug_overlay.set("current_action_label", label)
		var left_plant: bool = true
		var right_plant: bool = true
		if t >= 1.5 and t < 3.3:
			var walk_t = t - 1.5
			if walk_t < 0.9:
				right_plant = (walk_t < 0.2 or walk_t > 0.7)
			else:
				left_plant = (walk_t < 1.1 or walk_t > 1.6)
		debug_overlay.set("left_foot_planted", left_plant)
		debug_overlay.set("right_foot_planted", right_plant)

# ===========================================================================
# 0. v12.1 Canonical 6 Reference Poses & Stepped Blocking
# ===========================================================================
func _evaluate_v12_six_poses(t: float) -> void:
	var poses = PoseLibraryV12.get_all_six_poses()
	var pose_idx: int = clampi(int(floor(t)), 0, poses.size() - 1)
	var p_data: Dictionary = poses[pose_idx]
	PoseLibraryV12.apply_pose_to_rig(rig, p_data)
	_set_action(p_data["label"], true, true)

func _evaluate_v12_stepped_blocking(t: float) -> void:
	_setup_animation_player()
	anim_player.play("v12_stepped_blocking")
	anim_player.seek(t, true)
	
	var label: String
	if t < 1.5:
		label = "Beat 1: Discovery (Notice, head turn, lean)"
	elif t < 3.0:
		label = "Beat 2: Approach (Balanced steps to button)"
	elif t < 4.0:
		label = "Beat 3: Hesitation (Hand hovers above button, doubt)"
	elif t < 5.0:
		label = "Beat 4: Press (Commit & press, button -8px)"
	elif t < 5.5:
		label = "Beat 5: Activation (Energy burst flash)"
	elif t < 7.0:
		label = "Beat 6: Surprise (Recoil back, rear weight, wide arms gasp)"
	elif t < 9.0:
		label = "Beat 7: Recovery (Settle balance, push glasses up)"
	else:
		label = "Beat 8: Payoff (Amused smirk, appealing finish)"
		
	if debug_overlay != null:
		debug_overlay.set("current_action_label", label)
		var left_plant: bool = true
		var right_plant: bool = true
		if t >= 1.5 and t < 2.7:
			var step_t = t - 1.5
			if step_t < 0.6:
				right_plant = false
			elif step_t < 1.0:
				left_plant = false
		debug_overlay.set("left_foot_planted", left_plant)
		debug_overlay.set("right_foot_planted", right_plant)

# ===========================================================================
# 0. v10 Expressive Acting Clips & Authored Pose Evaluations
# ===========================================================================
func _evaluate_six_poses(t: float) -> void:
	rig.set("show_target_object", false)
	var pose_idx: int = clampi(int(floor(t)), 0, 5)
	var pose_names: Array = ["neutral", "curiosity", "concentration", "surprise", "confusion", "satisfaction"]
	var p_data: Dictionary = PoseLibrary.get_pose(pose_names[pose_idx], 2)
	PoseLibrary.apply_pose_to_rig(rig, p_data)
	_set_action("Pose %d: %s" % [pose_idx + 1, p_data["name"]], true, true)

func _evaluate_intensity_study(t: float) -> void:
	rig.set("show_target_object", false)
	var sec: int = clampi(int(floor(t)), 0, 8)
	var emotion: String
	var level: int = (sec % 3) + 1
	if sec < 3:
		emotion = "curiosity"
	elif sec < 6:
		emotion = "surprise"
	else:
		emotion = "satisfaction"
	var p_data: Dictionary = PoseLibrary.get_pose(emotion, level)
	PoseLibrary.apply_pose_to_rig(rig, p_data)
	var lvl_names = ["Subtle", "Readable", "Exaggerated"]
	_set_action("%s — Level %d (%s)" % [p_data["name"], level, lvl_names[level - 1]], true, true)

func _evaluate_test_c_curiosity(t: float) -> void:
	rig.set("show_target_object", false)
	var p_neut = PoseLibrary.get_pose("neutral", 2)
	var p_cur = PoseLibrary.get_pose("curiosity", 2)
	
	if t < 0.5:
		# 0.0 - 0.5s: Neutral start
		_set_action("Curiosity Test — Neutral Baseline", true, true)
		PoseLibrary.apply_pose_to_rig(rig, p_neut)
	elif t < 1.3:
		# 0.5 - 1.3s: Notice attention shift & lean in
		_set_action("Curiosity Test — Notice & Lean In", true, true)
		var p: float = _ease_in_out((t - 0.5) / 0.8)
		var blended = PoseLibrary.blend_poses(p_neut, p_cur, p)
		PoseLibrary.apply_pose_to_rig(rig, blended)
	elif t < 2.2:
		# 1.3 - 2.2s: Comedic curiosity hold
		_set_action("Curiosity Test — Comedic Hold & Study", true, true)
		PoseLibrary.apply_pose_to_rig(rig, p_cur)
	else:
		# 2.2 - 3.0s: Organic recovery back to neutral
		_set_action("Curiosity Test — Organic Recovery", true, true)
		var p: float = _ease_in_out((t - 2.2) / 0.8)
		var blended = PoseLibrary.blend_poses(p_cur, p_neut, p)
		PoseLibrary.apply_pose_to_rig(rig, blended)

func _evaluate_test_d_surprise(t: float) -> void:
	rig.set("show_target_object", false)
	var p_neut = PoseLibrary.get_pose("neutral", 2)
	var p_sur = PoseLibrary.get_pose("surprise", 3) # Exaggerated surprise
	
	if t < 0.6:
		# 0.0 - 0.6s: Neutral with subtle forward anticipation
		_set_action("Surprise Test — Neutral Anticipation", true, true)
		var p_sub = PoseLibrary.blend_poses(p_neut, PoseLibrary.get_pose("curiosity", 1), t / 0.6)
		PoseLibrary.apply_pose_to_rig(rig, p_sub)
	elif t < 1.1:
		# 0.6 - 1.1s: Sudden explosive startle recoil
		_set_action("Surprise Test — Explosive Recoil & Gasp", false, true)
		var snap: float = _elastic_out((t - 0.6) / 0.45)
		var blended = PoseLibrary.blend_poses(p_neut, p_sur, snap)
		PoseLibrary.apply_pose_to_rig(rig, blended)
	elif t < 2.0:
		# 1.1 - 2.0s: Comedic shocked freeze hold
		_set_action("Surprise Test — Shock Freeze Hold", false, true)
		PoseLibrary.apply_pose_to_rig(rig, p_sur)
	else:
		# 2.0 - 3.0s: Staggered organic recovery
		_set_action("Surprise Test — Staggered Recovery", true, true)
		var p_rec: float = _ease_in_out((t - 2.0) / 1.0)
		var blended = PoseLibrary.blend_poses(p_sur, p_neut, p_rec)
		# Secondary detail: glasses slide back onto bridge smoothly
		blended["glasses_slip_px"] = lerpf(5.5, 0.0, p_rec)
		PoseLibrary.apply_pose_to_rig(rig, blended)

func _evaluate_test_e_confusion_satisfaction(t: float) -> void:
	rig.set("show_target_object", false)
	var p_neut = PoseLibrary.get_pose("neutral", 2)
	var p_conf = PoseLibrary.get_pose("confusion", 2)
	var p_sat = PoseLibrary.get_pose("satisfaction", 2)
	
	if t < 0.4:
		# 0.0 - 0.4s: Neutral baseline
		_set_action("Confusion -> Satisfaction — Baseline", true, true)
		PoseLibrary.apply_pose_to_rig(rig, p_neut)
	elif t < 1.4:
		# 0.4 - 1.4s: Transition into confusion
		_set_action("Confusion -> Satisfaction — Puzzled Shrug", true, true)
		var p: float = _ease_in_out((t - 0.4) / 1.0)
		var blended = PoseLibrary.blend_poses(p_neut, p_conf, p)
		PoseLibrary.apply_pose_to_rig(rig, blended)
	elif t < 2.3:
		# 1.4 - 2.3s: Comedic confusion hold
		_set_action("Confusion -> Satisfaction — Confused Hold", true, true)
		PoseLibrary.apply_pose_to_rig(rig, p_conf)
	elif t < 2.9:
		# 2.3 - 2.9s: "Aha!" realization pop
		_set_action("Confusion -> Satisfaction — Aha! Realization", true, true)
		var p: float = _elastic_out((t - 2.3) / 0.6)
		var blended = PoseLibrary.blend_poses(p_conf, p_sat, p)
		PoseLibrary.apply_pose_to_rig(rig, blended)
	elif t < 3.8:
		# 2.9 - 3.8s: Triumphant satisfaction pose hold
		_set_action("Confusion -> Satisfaction — Triumphant Hold", true, true)
		PoseLibrary.apply_pose_to_rig(rig, p_sat)
	else:
		# 3.8 - 4.5s: Follow-through and settle into comfortable stance
		_set_action("Confusion -> Satisfaction — Confident Settle", true, true)
		var p: float = _ease_in_out((t - 3.8) / 0.7)
		var blended = PoseLibrary.blend_poses(p_sat, p_neut, p)
		blended["mouth_state"] = "smirk"
		PoseLibrary.apply_pose_to_rig(rig, blended)

func _evaluate_combined_acting(t: float) -> void:
	rig.set("show_target_object", false)
	var p_neut = PoseLibrary.get_pose("neutral", 2)
	var p_cur = PoseLibrary.get_pose("curiosity", 2)
	var p_conc = PoseLibrary.get_pose("concentration", 2)
	var p_sur = PoseLibrary.get_pose("surprise", 3)
	var p_conf = PoseLibrary.get_pose("confusion", 2)
	var p_sat = PoseLibrary.get_pose("satisfaction", 2)
	
	# -----------------------------------------------------------------------
	# 0.0s - 2.0s: Neutral & Curiosity (Section 17.1)
	# -----------------------------------------------------------------------
	if t < 0.7:
		_set_action("Phase 1: Neutral Standing", true, true)
		PoseLibrary.apply_pose_to_rig(rig, p_neut)
	elif t < 2.0:
		_set_action("Phase 1: Notice & Curious Lean", true, true)
		var p: float = _ease_in_out((t - 0.7) / 1.1)
		var blended = PoseLibrary.blend_poses(p_neut, p_cur, p)
		PoseLibrary.apply_pose_to_rig(rig, blended)
		
	# -----------------------------------------------------------------------
	# 2.0s - 4.0s: Investigation & Deep Concentration (Section 17.2)
	# -----------------------------------------------------------------------
	elif t < 2.9:
		_set_action("Phase 2: Hand-to-Chin Concentration", true, true)
		var p: float = _ease_in_out((t - 2.0) / 0.9)
		var blended = PoseLibrary.blend_poses(p_cur, p_conc, p)
		PoseLibrary.apply_pose_to_rig(rig, blended)
	elif t < 4.0:
		_set_action("Phase 2: Deep Analytical Hold", true, true)
		PoseLibrary.apply_pose_to_rig(rig, p_conc)
		
	# -----------------------------------------------------------------------
	# 4.0s - 6.0s: Sudden Surprise & Recoil (Section 17.3)
	# -----------------------------------------------------------------------
	elif t < 4.5:
		_set_action("Phase 3: Explosive Recoil & Gasp", false, true)
		var snap: float = _elastic_out((t - 4.0) / 0.45)
		var blended = PoseLibrary.blend_poses(p_conc, p_sur, snap)
		PoseLibrary.apply_pose_to_rig(rig, blended)
	elif t < 5.5:
		_set_action("Phase 3: Comedic Shock Freeze Hold", false, true)
		PoseLibrary.apply_pose_to_rig(rig, p_sur)
	elif t < 6.0:
		_set_action("Phase 3: Shock Dissipation", true, true)
		var p: float = _ease_in_out((t - 5.5) / 0.5)
		var blended = PoseLibrary.blend_poses(p_sur, p_conf, p * 0.4)
		PoseLibrary.apply_pose_to_rig(rig, blended)
		
	# -----------------------------------------------------------------------
	# 6.0s - 8.0s: Confusion & Head Scratch (Section 17.4)
	# -----------------------------------------------------------------------
	elif t < 6.8:
		_set_action("Phase 4: Asymmetrical Confusion Shrug", true, true)
		var p: float = _ease_in_out((t - 6.0) / 0.8)
		var blended = PoseLibrary.blend_poses(p_sur, p_conf, p)
		blended["glasses_slip_px"] = lerpf(5.5, 0.0, p)
		PoseLibrary.apply_pose_to_rig(rig, blended)
	elif t < 8.0:
		_set_action("Phase 4: Puzzled Investigation Hold", true, true)
		PoseLibrary.apply_pose_to_rig(rig, p_conf)
		
	# -----------------------------------------------------------------------
	# 8.0s - 9.5s: "Aha!" Realization (Section 17.5)
	# -----------------------------------------------------------------------
	elif t < 8.7:
		_set_action("Phase 5: Aha! Sudden Realization", true, true)
		var p: float = _elastic_out((t - 8.0) / 0.6)
		var blended = PoseLibrary.blend_poses(p_conf, p_sat, p)
		PoseLibrary.apply_pose_to_rig(rig, blended)
	elif t < 9.5:
		_set_action("Phase 5: Confident Chest Expansion", true, true)
		PoseLibrary.apply_pose_to_rig(rig, p_sat)
		
	# -----------------------------------------------------------------------
	# 9.5s - 11.0s: Triumphant Satisfaction & Settle (Section 17.6)
	# -----------------------------------------------------------------------
	elif t < 10.3:
		_set_action("Phase 6: Triumphant Fist Pump", true, true)
		var p_sat_ex = PoseLibrary.get_pose("satisfaction", 3)
		var p: float = _ease_in_out((t - 9.5) / 0.6)
		var blended = PoseLibrary.blend_poses(p_sat, p_sat_ex, p)
		PoseLibrary.apply_pose_to_rig(rig, blended)
	else:
		_set_action("Phase 6: Confident Smirk Settle", true, true)
		var p: float = _ease_in_out((t - 10.3) / 0.7)
		var blended = PoseLibrary.blend_poses(p_sat, p_neut, p * 0.7)
		blended["mouth_state"] = "smirk"
		blended["right_brow_raise_px"] = 3.0
		PoseLibrary.apply_pose_to_rig(rig, blended)
# Returns a dictionary of leg angles and pelvis vertical offset for a single step cycle [0.0, 1.0]
# Leading leg strikes first, trailing leg follows
func _sample_walk_cycle(cycle_t: float, is_right_leading: bool) -> Dictionary:
	# Clamped cycle [0.0, 1.0]:
	# 0.00: Contact (Heel strike)
	# 0.25: Down / Recoil (Knee compression, weight absorb)
	# 0.50: Passing (Body rides over stance leg, swing leg clears ground)
	# 0.75: Up / Push-off (Stance leg extends, heel raises, swing leg reaches)
	# 1.00: Opposite Contact
	var lead_thigh: float
	var lead_shin: float
	var lead_foot: float
	var trail_thigh: float
	var trail_shin: float
	var trail_foot: float
	var pelvis_dy: float
	var torso_lean: float
	var arm_swing: float
	
	if cycle_t < 0.25:
		# Contact -> Down
		var p: float = cycle_t / 0.25
		lead_thigh = lerpf(22.0, 16.0, p)
		lead_shin = lerpf(-10.0, -32.0, p) # Knee flexes to absorb weight
		lead_foot = lerpf(12.0, 0.0, p)    # Heel strike rolls to flat foot
		
		trail_thigh = lerpf(-18.0, -12.0, p)
		trail_shin = lerpf(-12.0, -38.0, p) # Knee lifts as foot leaves ground
		trail_foot = lerpf(-16.0, -8.0, p)
		
		pelvis_dy = lerpf(0.0, 12.0, p)     # Pelvis drops to lowest recoil
		torso_lean = lerpf(4.0, 5.0, p)
		arm_swing = lerpf(20.0, 10.0, p)
		
	elif cycle_t < 0.50:
		# Down -> Passing
		var p: float = (cycle_t - 0.25) / 0.25
		lead_thigh = lerpf(16.0, 4.0, p)
		lead_shin = lerpf(-32.0, -16.0, p) # Stance leg straightens
		lead_foot = 0.0                    # Flat planted foot
		
		trail_thigh = lerpf(-12.0, 14.0, p) # Swing leg swings forward
		trail_shin = lerpf(-38.0, -64.0, p) # Deep knee bend to clear ground
		trail_foot = lerpf(-8.0, 4.0, p)
		
		pelvis_dy = lerpf(12.0, -4.0, p)    # Pelvis rises over stance foot
		torso_lean = lerpf(5.0, 3.5, p)
		arm_swing = lerpf(10.0, 0.0, p)
		
	elif cycle_t < 0.75:
		# Passing -> Up
		var p: float = (cycle_t - 0.50) / 0.25
		lead_thigh = lerpf(4.0, -10.0, p)
		lead_shin = lerpf(-16.0, -6.0, p)  # Push-off extension
		lead_foot = lerpf(0.0, -14.0, p)   # Heel lifts, weight on ball of foot
		
		trail_thigh = lerpf(14.0, 22.0, p) # Swing leg extends forward
		trail_shin = lerpf(-64.0, -12.0, p)
		trail_foot = lerpf(4.0, 10.0, p)
		
		pelvis_dy = lerpf(-4.0, -14.0, p)  # Pelvis reaches highest peak
		torso_lean = lerpf(3.5, 4.2, p)
		arm_swing = lerpf(0.0, -14.0, p)
		
	else:
		# Up -> Opposite Contact
		var p: float = (cycle_t - 0.75) / 0.25
		lead_thigh = lerpf(-10.0, -18.0, p)
		lead_shin = lerpf(-6.0, -12.0, p)
		lead_foot = lerpf(-14.0, -16.0, p)
		
		trail_thigh = lerpf(22.0, 24.0, p)
		trail_shin = lerpf(-12.0, -10.0, p)
		trail_foot = lerpf(10.0, 12.0, p)   # Heel strike contact
		
		pelvis_dy = lerpf(-14.0, 0.0, p)
		torso_lean = lerpf(4.2, 4.0, p)
		arm_swing = lerpf(-14.0, -20.0, p)

	if is_right_leading:
		return {
			"r_thigh": lead_thigh, "r_shin": lead_shin, "r_foot": lead_foot,
			"l_thigh": trail_thigh, "l_shin": trail_shin, "l_foot": trail_foot,
			"pelvis_dy": pelvis_dy, "torso_lean": torso_lean, "arm_swing": arm_swing,
			"r_planted": cycle_t < 0.65, "l_planted": cycle_t >= 0.85 or cycle_t < 0.10
		}
	else:
		return {
			"l_thigh": lead_thigh, "l_shin": lead_shin, "l_foot": lead_foot,
			"r_thigh": trail_thigh, "r_shin": trail_shin, "r_foot": trail_foot,
			"pelvis_dy": pelvis_dy, "torso_lean": torso_lean, "arm_swing": -arm_swing,
			"l_planted": cycle_t < 0.65, "r_planted": cycle_t >= 0.85 or cycle_t < 0.10
		}

# ===========================================================================
# 2. Master 8.0s Combined Proof of Concept Sequence (Milestone 8)
# ===========================================================================
func _evaluate_full_poc(t: float) -> void:
	rig.set("show_target_object", true)
	rig.set("target_object_pos", TARGET_OBJ_POS)
	
	# -----------------------------------------------------------------------
	# 0.0s - 1.0s: Neutral Standing & Subtle Organic Idle
	# -----------------------------------------------------------------------
	if t <= 1.0:
		_set_action("Neutral Standing (Subtle Idle)", true, true)
		var cycle: float = sin(t * TAU * 1.0)
		rig.set("root_pos", Vector2(330.0, STANDING_Y - cycle * 1.5))
		rig.set("torso_lean_deg", 2.0 + cycle * 0.4)
		rig.set("spine_arch_deg", 4.5 + cycle * 0.3)
		rig.set("head_tilt_deg", 1.5 + cycle * 0.2)
		rig.set("head_nod_px", 0.0)
		rig.set("yaw_factor", 0.22)
		rig.set("glasses_slip_px", 0.0)
		rig.set("hair_lag_deg", 0.0)
		rig.set("left_brow_raise_px", 0.0)
		rig.set("right_brow_raise_px", 0.0)
		rig.set("brow_slant_deg", 0.0)
		rig.set("mouth_state", "neutral")
		rig.set("target_object_pulse", 0.0)
		
		# Parallel upright stance directly under hips
		rig.set("left_thigh_deg", 14.0)
		rig.set("left_shin_deg", -28.0)
		rig.set("left_foot_deg", 14.0)
		rig.set("right_thigh_deg", 14.0)
		rig.set("right_shin_deg", -28.0)
		rig.set("right_foot_deg", 14.0)
		
		# Natural vertical arm drape along flanks
		rig.set("left_shoulder_deg", 4.0 + cycle * 0.5)
		rig.set("left_elbow_deg", 12.0)
		rig.set("left_wrist_deg", 5.0)
		rig.set("left_hand_pose", "relaxed")
		
		rig.set("right_shoulder_deg", 6.0 + cycle * 0.5)
		rig.set("right_elbow_deg", 12.0)
		rig.set("right_wrist_deg", 5.0)
		rig.set("right_hand_pose", "relaxed")
		rig.set("right_shoulder_protract_px", 0.0)

	# -----------------------------------------------------------------------
	# 1.0s - 2.2s: Curiosity & Focus Toward Target Object
	# -----------------------------------------------------------------------
	elif t <= 2.2:
		var p: float = (t - 1.0) / 1.2
		var smooth_p: float = _ease_in_out(p)
		_set_action("Curiosity Focus & Head Turn", true, true)
		
		rig.set("root_pos", Vector2(330.0 + smooth_p * 15.0, STANDING_Y))
		rig.set("torso_lean_deg", lerpf(2.0, 5.0, smooth_p))
		rig.set("spine_arch_deg", lerpf(4.5, 5.5, smooth_p))
		rig.set("head_tilt_deg", lerpf(1.5, -4.5, smooth_p))
		rig.set("head_nod_px", lerpf(0.0, -3.0, smooth_p))
		rig.set("yaw_factor", lerpf(0.22, 0.30, smooth_p))
		rig.set("left_brow_raise_px", lerpf(0.0, 1.5, smooth_p))
		rig.set("right_brow_raise_px", lerpf(0.0, 4.0, smooth_p)) # Quizzical arch
		rig.set("brow_slant_deg", lerpf(0.0, 2.5, smooth_p))
		rig.set("mouth_state", "curious_o" if p >= 0.3 else "neutral")
		rig.set("target_object_pulse", 0.0)
		
		rig.set("left_shoulder_deg", lerpf(4.0, 6.0, smooth_p))
		rig.set("left_elbow_deg", 12.0)
		rig.set("right_shoulder_deg", lerpf(6.0, 16.0, smooth_p))
		rig.set("right_elbow_deg", lerpf(12.0, 24.0, smooth_p))
		rig.set("right_hand_pose", "reach_open" if p >= 0.4 else "relaxed")

	# -----------------------------------------------------------------------
	# 2.2s - 4.2s: Three-Step Walk Cycle Toward Target (+190px Root Advancement)
	# -----------------------------------------------------------------------
	elif t <= 4.2:
		var walk_t: float = (t - 2.2) / 2.0 # 2.0s duration for 3 deliberate steps
		_set_action("Authored Walk Cycle (Three Steps)", true, true)
		
		# Root displacement: advances smoothly from 345px to 535px (+190px displacement)
		var start_x: float = 345.0
		var total_disp: float = 190.0
		var current_x: float = start_x + _smooth_step(walk_t) * total_disp
		
		# 3 steps = 3 half-cycles of walk cycle:
		# Step 1 [0.00 - 0.33]: Right leg leads
		# Step 2 [0.33 - 0.67]: Left leg leads
		# Step 3 [0.67 - 1.00]: Right leg leads into planted stop
		var step_prog: float = walk_t * 3.0
		var step_idx: int = int(floor(step_prog))
		var sub_t: float = step_prog - float(step_idx)
		sub_t = clampf(sub_t, 0.0, 1.0)
		
		var sample: Dictionary
		if step_idx == 0:
			sample = _sample_walk_cycle(sub_t, true)
		elif step_idx == 1:
			sample = _sample_walk_cycle(sub_t, false)
		else:
			sample = _sample_walk_cycle(sub_t, true)
			
		# Apply sampled walk parameters
		rig.set("root_pos", Vector2(current_x, STANDING_Y + sample["pelvis_dy"]))
		rig.set("torso_lean_deg", sample["torso_lean"])
		rig.set("spine_arch_deg", 5.0)
		rig.set("head_tilt_deg", -2.0)
		rig.set("head_nod_px", 0.0)
		rig.set("mouth_state", "neutral")
		rig.set("target_object_pulse", 0.0)
		
		# Legs
		rig.set("right_thigh_deg", sample["r_thigh"])
		rig.set("right_shin_deg", sample["r_shin"])
		rig.set("right_foot_deg", sample["r_foot"])
		rig.set("left_thigh_deg", sample["l_thigh"])
		rig.set("left_shin_deg", sample["l_shin"])
		rig.set("left_foot_deg", sample["l_foot"])
		
		# Arm swing in walking opposition
		rig.set("left_shoulder_deg", 6.0 + sample["arm_swing"])
		rig.set("left_elbow_deg", 12.0 + absf(sample["arm_swing"]) * 0.4)
		rig.set("right_shoulder_deg", 6.0 - sample["arm_swing"])
		rig.set("right_elbow_deg", 12.0 + absf(sample["arm_swing"]) * 0.4)
		rig.set("left_hand_pose", "relaxed")
		rig.set("right_hand_pose", "relaxed")
		
		if debug_overlay != null:
			debug_overlay.set("left_foot_planted", sample["l_planted"])
			debug_overlay.set("right_foot_planted", sample["r_planted"])

	# -----------------------------------------------------------------------
	# 4.2s - 5.6s: Coordinated Whole-Body Reach & Target Contact
	# -----------------------------------------------------------------------
	elif t <= 5.6:
		var reach_t: float = (t - 4.2) / 1.4
		_set_action("Coordinated Whole-Body Reach & Contact", true, true)
		
		# Reaching progression:
		# 0.0 - 0.65: Weight shifts, torso leans forward, arm unfolds toward target
		# 0.65 - 0.85: Visible physical contact at (740, 1220), brief hold
		# 0.85 - 1.00: Contact triggers target orb pulse
		var p_reach: float = _ease_in_out(minf(1.0, reach_t / 0.65))
		
		rig.set("root_pos", Vector2(535.0, STANDING_Y))
		rig.set("torso_lean_deg", lerpf(4.0, 9.5, p_reach))
		rig.set("spine_arch_deg", lerpf(5.0, 7.0, p_reach))
		rig.set("head_tilt_deg", lerpf(-2.0, -3.5, p_reach))
		rig.set("head_nod_px", lerpf(0.0, -2.5, p_reach))
		
		# Right shoulder protracts forward into the reach
		rig.set("right_shoulder_protract_px", lerpf(0.0, 10.0, p_reach))
		
		# Right arm extension reaching exactly toward TARGET_OBJ_POS
		rig.set("right_shoulder_deg", lerpf(6.0, 68.0, p_reach))
		rig.set("right_elbow_deg", lerpf(12.0, 8.0, p_reach))
		rig.set("right_wrist_deg", lerpf(5.0, -5.0, p_reach))
		rig.set("right_hand_pose", "point")
		
		# Free left arm hangs comfortably in relaxed counterbalance
		rig.set("left_shoulder_deg", lerpf(6.0, 2.0, p_reach))
		rig.set("left_elbow_deg", lerpf(12.0, 10.0, p_reach))
		rig.set("left_hand_pose", "relaxed")
		
		# Planted forward stance
		rig.set("left_thigh_deg", 10.0)
		rig.set("left_shin_deg", -22.0)
		rig.set("left_foot_deg", 12.0)
		rig.set("right_thigh_deg", 18.0)
		rig.set("right_shin_deg", -32.0)
		rig.set("right_foot_deg", 14.0)
		
		rig.set("left_brow_raise_px", 1.5)
		rig.set("right_brow_raise_px", 3.0)
		rig.set("mouth_state", "curious_o")
		
		# Trigger orb pulse right at contact (reach_t >= 0.70)
		var pulse: float = 0.0
		if reach_t >= 0.70:
			pulse = (reach_t - 0.70) / 0.30
		rig.set("target_object_pulse", pulse)

	# -----------------------------------------------------------------------
	# 5.6s - 6.8s: Expressive Comedic Surprise (Explosive Recoil & Gasp)
	# -----------------------------------------------------------------------
	elif t <= 6.8:
		var gasp_t: float = (t - 5.6) / 1.2
		_set_action("Expressive Surprise (Startle Recoil & Gasp)", true, true)
		
		# Sudden explosive startle recoil
		var snap: float = _elastic_out(clampf(gasp_t / 0.35, 0.0, 1.0))
		
		# Whole-body recoil backward: pelvis drops, torso arches in shock
		rig.set("root_pos", Vector2(535.0 - snap * 28.0, STANDING_Y - snap * 8.0))
		rig.set("torso_lean_deg", lerpf(9.5, -8.0, snap))
		rig.set("spine_arch_deg", lerpf(7.0, -5.5, snap))
		rig.set("shoulder_shrug_px", snap * 14.0)
		rig.set("right_shoulder_protract_px", 0.0)
		
		# Head jerks up, hair whips back, glasses slip down nose
		rig.set("head_tilt_deg", lerpf(-3.5, 8.5, snap))
		rig.set("head_nod_px", lerpf(-2.5, -6.0, snap))
		rig.set("hair_lag_deg", -snap * 18.0)
		rig.set("glasses_slip_px", snap * 5.0)
		
		# Symmetrical startled eyebrows & open gasp
		rig.set("left_brow_raise_px", snap * 12.0)
		rig.set("right_brow_raise_px", snap * 12.0)
		rig.set("brow_slant_deg", 0.0)
		rig.set("mouth_state", "open_gasp")
		
		# Hands fling up defensively
		rig.set("right_shoulder_deg", lerpf(68.0, 44.0, snap))
		rig.set("right_elbow_deg", lerpf(8.0, 58.0, snap))
		rig.set("right_wrist_deg", -25.0)
		rig.set("right_hand_pose", "reach_open")
		
		rig.set("left_shoulder_deg", lerpf(2.0, 40.0, snap))
		rig.set("left_elbow_deg", lerpf(10.0, 54.0, snap))
		rig.set("left_wrist_deg", -20.0)
		rig.set("left_hand_pose", "reach_open")
		
		# Target orb pulse decays
		rig.set("target_object_pulse", maxf(0.0, 1.0 - gasp_t * 1.5))

	# -----------------------------------------------------------------------
	# 6.8s - 8.0s: Smooth Recovery & Smirk Settle into Approved Neutral Stance
	# -----------------------------------------------------------------------
	else:
		var rec_t: float = (t - 6.8) / 1.2
		var p_rec: float = _ease_in_out(rec_t)
		_set_action("Smooth Recovery & Confident Smirk Settle", true, true)
		
		# Torso and pelvis return smoothly to neutral upright balance
		rig.set("root_pos", Vector2(lerpf(507.0, 516.0, p_rec), STANDING_Y))
		rig.set("torso_lean_deg", lerpf(-8.0, 2.0, p_rec))
		rig.set("spine_arch_deg", lerpf(-5.5, 4.5, p_rec))
		rig.set("shoulder_shrug_px", lerpf(14.0, 0.0, p_rec))
		
		# Glasses slide back into position, hair settles
		rig.set("glasses_slip_px", lerpf(5.0, 0.0, p_rec))
		rig.set("hair_lag_deg", lerpf(-18.0, 0.0, p_rec))
		rig.set("head_tilt_deg", lerpf(8.5, -3.0, p_rec))
		rig.set("head_nod_px", lerpf(-6.0, -1.0, p_rec))
		
		# Eyebrows and mouth resolve into confident smirk
		rig.set("left_brow_raise_px", lerpf(12.0, 1.0, p_rec))
		rig.set("right_brow_raise_px", lerpf(12.0, 3.5, p_rec))
		rig.set("brow_slant_deg", lerpf(0.0, 2.0, p_rec))
		rig.set("mouth_state", "smirk" if rec_t >= 0.25 else "neutral")
		rig.set("target_object_pulse", 0.0)
		
		# Arms settle gracefully back to natural flank hang
		rig.set("right_shoulder_deg", lerpf(44.0, 6.0, p_rec))
		rig.set("right_elbow_deg", lerpf(58.0, 12.0, p_rec))
		rig.set("right_wrist_deg", lerpf(-25.0, 5.0, p_rec))
		rig.set("right_hand_pose", "relaxed")
		
		rig.set("left_shoulder_deg", lerpf(40.0, 4.0, p_rec))
		rig.set("left_elbow_deg", lerpf(54.0, 12.0, p_rec))
		rig.set("left_wrist_deg", lerpf(-20.0, 5.0, p_rec))
		rig.set("left_hand_pose", "relaxed")
		
		# Parallel grounded legs
		rig.set("left_thigh_deg", 14.0)
		rig.set("left_shin_deg", -28.0)
		rig.set("left_foot_deg", 14.0)
		rig.set("right_thigh_deg", 14.0)
		rig.set("right_shin_deg", -28.0)
		rig.set("right_foot_deg", 14.0)

# ===========================================================================
# 3. Isolated Milestone Tests (Section 13)
# ===========================================================================
func _evaluate_test_a_walk(t: float) -> void:
	rig.set("show_target_object", false)
	_set_action("Test A — Three-Step Walk Cycle", true, true)
	var norm_t: float = t / 2.5 # 2.5s duration
	var current_x: float = 380.0 + _smooth_step(norm_t) * 160.0
	var step_prog: float = norm_t * 3.0
	var step_idx: int = int(floor(step_prog))
	var sub_t: float = clampf(step_prog - float(step_idx), 0.0, 1.0)
	
	var sample: Dictionary = _sample_walk_cycle(sub_t, step_idx % 2 == 0)
	rig.set("root_pos", Vector2(current_x, STANDING_Y + sample["pelvis_dy"]))
	rig.set("torso_lean_deg", sample["torso_lean"])
	rig.set("right_thigh_deg", sample["r_thigh"])
	rig.set("right_shin_deg", sample["r_shin"])
	rig.set("right_foot_deg", sample["r_foot"])
	rig.set("left_thigh_deg", sample["l_thigh"])
	rig.set("left_shin_deg", sample["l_shin"])
	rig.set("left_foot_deg", sample["l_foot"])
	rig.set("left_shoulder_deg", 6.0 + sample["arm_swing"])
	rig.set("right_shoulder_deg", 6.0 - sample["arm_swing"])
	rig.set("mouth_state", "neutral")
	
	if debug_overlay != null:
		debug_overlay.set("left_foot_planted", sample["l_planted"])
		debug_overlay.set("right_foot_planted", sample["r_planted"])

func _evaluate_test_b_reach(t: float) -> void:
	rig.set("show_target_object", true)
	rig.set("target_object_pos", TARGET_OBJ_POS)
	_set_action("Test B — Coordinated Reach & Recovery", true, true)
	var p: float = _ease_in_out(minf(1.0, t / 1.4))
	rig.set("root_pos", Vector2(535.0, STANDING_Y))
	rig.set("torso_lean_deg", lerpf(2.0, 9.5, p))
	rig.set("right_shoulder_protract_px", lerpf(0.0, 10.0, p))
	rig.set("right_shoulder_deg", lerpf(6.0, 68.0, p))
	rig.set("right_elbow_deg", lerpf(12.0, 8.0, p))
	rig.set("right_hand_pose", "point")
	rig.set("mouth_state", "curious_o")
	var pulse: float = maxf(0.0, (t - 1.2) / 0.5) if t >= 1.2 else 0.0
	rig.set("target_object_pulse", pulse)

func _evaluate_test_c_acting(t: float) -> void:
	rig.set("show_target_object", false)
	_set_action("Test C — Silent Emotional Acting", true, true)
	if t < 0.8:
		var p: float = t / 0.8
		rig.set("head_tilt_deg", lerpf(1.5, -4.5, p))
		rig.set("right_brow_raise_px", lerpf(0.0, 4.0, p))
		rig.set("mouth_state", "curious_o")
	elif t < 1.6:
		var snap: float = _elastic_out((t - 0.8) / 0.35)
		rig.set("torso_lean_deg", lerpf(2.0, -8.0, snap))
		rig.set("glasses_slip_px", snap * 5.0)
		rig.set("left_brow_raise_px", snap * 12.0)
		rig.set("right_brow_raise_px", snap * 12.0)
		rig.set("mouth_state", "open_gasp")
	else:
		var p: float = (t - 1.6) / 0.9
		rig.set("torso_lean_deg", lerpf(-8.0, 2.0, p))
		rig.set("glasses_slip_px", lerpf(5.0, 0.0, p))
		rig.set("right_brow_raise_px", lerpf(12.0, 3.5, p))
		rig.set("mouth_state", "smirk")

# ===========================================================================
# Math Helpers
# ===========================================================================
func _ease_in_out(x: float) -> float:
	return 0.5 * (1.0 - cos(clampf(x, 0.0, 1.0) * PI))

func _smooth_step(x: float) -> float:
	var c = clampf(x, 0.0, 1.0)
	return c * c * (3.0 - 2.0 * c)

func _elastic_out(x: float) -> float:
	if x <= 0.0: return 0.0
	if x >= 1.0: return 1.0
	return sin(-13.0 * (x + 1.0) * (PI * 0.5)) * pow(2.0, -10.0 * x) + 1.0

func _set_action(label: String, left_plant: bool, right_plant: bool) -> void:
	if debug_overlay != null:
		debug_overlay.set("current_action_label", label)
		debug_overlay.set("left_foot_planted", left_plant)
		debug_overlay.set("right_foot_planted", right_plant)
