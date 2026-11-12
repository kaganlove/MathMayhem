class_name AnimationController
extends Node

## Master Animation Controller for Math Mayhem Godot 2D Prototype
## Drives the CharacterRig2D properties through authored performance keyframes.
## Implements Milestone 3 (Neutral), Milestone 4 (Walk), Milestone 5 (Reach),
## Milestone 6 (Acting), and Milestone 7 (Combined 6.0s Proof of Concept).

@export var rig: Node2D
@export var debug_overlay: Node2D

var current_time: float = 0.0
var playback_speed: float = 1.0
var is_playing: bool = true
var active_clip: String = "full_poc"
var clip_duration: float = 6.0

# Clip boundaries for isolated tests
const CLIP_DURATIONS: Dictionary = {
	"neutral_idle": 2.0,
	"walk_three_steps": 2.5,
	"reach": 2.0,
	"acting": 2.5,
	"full_poc": 6.0
}

func _ready() -> void:
	set_clip("full_poc")

func set_clip(clip_name: String) -> void:
	active_clip = clip_name
	clip_duration = CLIP_DURATIONS.get(clip_name, 6.0)
	current_time = 0.0

func evaluate_at(t: float) -> void:
	if rig == null:
		return
		
	if active_clip == "neutral_idle":
		_evaluate_idle(t)
	elif active_clip == "walk_three_steps":
		_evaluate_walk(t)
	elif active_clip == "reach":
		_evaluate_reach(t)
	elif active_clip == "acting":
		_evaluate_acting(t)
	else:
		_evaluate_full_poc(t)
		
	if debug_overlay != null:
		debug_overlay.current_time_sec = t

# ---------------------------------------------------------------------------
# Master 6.0s Combined Proof of Concept Sequence
# ---------------------------------------------------------------------------
func _evaluate_full_poc(t: float) -> void:
	# 0.0s - 1.0s: Neutral Breathing Idle
	if t <= 1.0:
		_set_action("Neutral Breathing Idle", true, true)
		var cycle: float = sin(t * TAU * 1.0)
		rig.root_pos = Vector2(400.0, 1285.8 - cycle * 1.5)
		rig.torso_lean_deg = 2.0 + cycle * 0.4
		rig.spine_arch_deg = 4.5 + cycle * 0.3
		rig.head_tilt_deg = 1.5 + cycle * 0.2
		rig.head_nod_px = 0.0
		rig.yaw_factor = 0.22
		rig.glasses_slip_px = 0.0
		rig.hair_lag_deg = 0.0
		rig.left_brow_raise_px = 0.0
		rig.right_brow_raise_px = 0.0
		rig.brow_slant_deg = 0.0
		rig.mouth_state = "neutral"
		
		# Parallel stance directly beneath hips
		rig.left_thigh_deg = 14.0
		rig.left_shin_deg = -28.0
		rig.left_foot_deg = 14.0
		rig.right_thigh_deg = 14.0
		rig.right_shin_deg = -28.0
		rig.right_foot_deg = 14.0
		
		# Relaxed vertical arm hang along torso flanks
		rig.left_shoulder_deg = 4.0 + cycle * 0.5
		rig.left_elbow_deg = 12.0
		rig.left_wrist_deg = 5.0
		rig.left_hand_pose = "relaxed"
		rig.right_shoulder_deg = 6.0 + cycle * 0.5
		rig.right_elbow_deg = 12.0
		rig.right_wrist_deg = 5.0
		rig.right_hand_pose = "relaxed"
		rig.right_shoulder_protract_px = 0.0

	# 1.0s - 2.0s: Curiosity & Inquisitive Focus
	elif t <= 2.0:
		var p: float = (t - 1.0) / 1.0
		var smooth_p: float = _ease_in_out(p)
		_set_action("Curiosity & Head Turn", true, true)
		
		rig.root_pos = Vector2(400.0 + smooth_p * 12.0, 1285.8)
		rig.torso_lean_deg = lerpf(2.0, 5.0, smooth_p)
		rig.spine_arch_deg = lerpf(4.5, 5.5, smooth_p)
		rig.head_tilt_deg = lerpf(1.5, -4.0, smooth_p)
		rig.head_nod_px = lerpf(0.0, -2.5, smooth_p) # Look up/forward
		rig.yaw_factor = lerpf(0.22, 0.28, smooth_p)
		rig.left_brow_raise_px = lerpf(0.0, 1.5, smooth_p)
		rig.right_brow_raise_px = lerpf(0.0, 3.5, smooth_p) # Subtle brow arch
		rig.brow_slant_deg = lerpf(0.0, 2.5, smooth_p)
		rig.mouth_state = "curious_o" if p >= 0.4 else "neutral"
		
		# Legs stay grounded
		rig.left_thigh_deg = 14.0
		rig.left_shin_deg = -28.0
		rig.left_foot_deg = 14.0
		rig.right_thigh_deg = 14.0
		rig.right_shin_deg = -28.0
		rig.right_foot_deg = 14.0
		
		# Arms adjust slightly with curiosity
		rig.left_shoulder_deg = lerpf(4.0, 5.0, smooth_p)
		rig.left_elbow_deg = lerpf(12.0, 14.0, smooth_p)
		rig.right_shoulder_deg = lerpf(6.0, 12.0, smooth_p)
		rig.right_elbow_deg = lerpf(12.0, 22.0, smooth_p)
		rig.right_hand_pose = "reach_open" if p >= 0.5 else "relaxed"

	# 2.0s - 3.2s: Three Believable Steps Across Screen (Measurable Displacement)
	elif t <= 3.2:
		var walk_t: float = (t - 2.0) / 1.2 # 1.2s total walk duration
		_set_action("Three-Step Walk Cycle", true, true)
		
		# Total root displacement = 120 pixels across screen
		var root_start_x: float = 412.0
		var total_stride: float = 120.0
		rig.root_pos.x = root_start_x + walk_t * total_stride
		
		# Pelvis vertical bounce (double cycle per stride)
		var bob: float = absf(sin(walk_t * PI * 3.0)) * 6.0
		rig.root_pos.y = 1285.8 - bob
		rig.torso_lean_deg = 5.5 + sin(walk_t * PI * 3.0) * 1.5
		rig.spine_arch_deg = 5.0
		rig.head_tilt_deg = -2.0 + sin(walk_t * PI * 3.0) * 1.0
		
		# Walk gait cycle: 3 steps -> 1.5 full walk periods
		var gait_phase: float = walk_t * PI * 3.0
		var r_swing: float = sin(gait_phase)
		var l_swing: float = -r_swing
		
		# Leg angles with contact, passing, and toe push-off
		rig.right_thigh_deg = 14.0 + r_swing * 22.0
		rig.right_shin_deg = -28.0 + (maxf(0.0, -r_swing) * 28.0) - (maxf(0.0, r_swing) * 8.0)
		rig.right_foot_deg = 14.0 - r_swing * 12.0
		
		rig.left_thigh_deg = 14.0 + l_swing * 22.0
		rig.left_shin_deg = -28.0 + (maxf(0.0, -l_swing) * 28.0) - (maxf(0.0, l_swing) * 8.0)
		rig.left_foot_deg = 14.0 - l_swing * 12.0
		
		# Natural arm swing in walking opposition (left arm swings with right leg)
		rig.left_shoulder_deg = 6.0 + r_swing * 18.0
		rig.left_elbow_deg = 12.0 + absf(r_swing) * 10.0
		rig.right_shoulder_deg = 6.0 - r_swing * 18.0
		rig.right_elbow_deg = 12.0 + absf(r_swing) * 10.0
		
		rig.mouth_state = "neutral"
		if debug_overlay != null:
			debug_overlay.left_foot_planted = l_swing <= 0.2
			debug_overlay.right_foot_planted = r_swing <= 0.2

	# 3.2s - 4.2s: Coordinated Whole-Body Reach
	elif t <= 4.2:
		var reach_t: float = (t - 3.2) / 1.0
		_set_action("Whole-Body Reach & Extension", true, true)
		
		# Decelerated settle into forward planted stance
		var p_reach: float = _ease_in_out(minf(1.0, reach_t / 0.65))
		rig.root_pos = Vector2(532.0, 1285.8)
		rig.torso_lean_deg = lerpf(4.0, 8.5, p_reach)
		rig.spine_arch_deg = lerpf(5.0, 6.5, p_reach)
		rig.head_tilt_deg = lerpf(-1.0, -3.0, p_reach)
		rig.head_nod_px = lerpf(0.0, -2.0, p_reach)
		
		# Right shoulder protracts forward into the reach
		rig.right_shoulder_protract_px = lerpf(0.0, 8.0, p_reach)
		
		# Right arm extends forward with pointing finger
		rig.right_shoulder_deg = lerpf(6.0, 65.0, p_reach)
		rig.right_elbow_deg = lerpf(12.0, 10.0, p_reach)
		rig.right_wrist_deg = lerpf(5.0, 0.0, p_reach)
		rig.right_hand_pose = "point"
		
		# Free left arm hangs comfortably in relaxed counterbalance
		rig.left_shoulder_deg = lerpf(6.0, 2.0, p_reach)
		rig.left_elbow_deg = lerpf(12.0, 10.0, p_reach)
		rig.left_hand_pose = "relaxed"
		
		# Stable planted feet
		rig.left_thigh_deg = 10.0
		rig.left_shin_deg = -22.0
		rig.left_foot_deg = 12.0
		rig.right_thigh_deg = 18.0
		rig.right_shin_deg = -32.0
		rig.right_foot_deg = 14.0
		
		rig.left_brow_raise_px = 1.0
		rig.right_brow_raise_px = 2.5
		rig.mouth_state = "curious_o"

	# 4.2s - 5.0s: Expressive Comedic Surprise (Startle Recoil & Gasp)
	elif t <= 5.0:
		var gasp_t: float = (t - 4.2) / 0.8
		_set_action("Expressive Surprise & Recoil", true, true)
		
		var snap: float = _elastic_out(clampf(gasp_t / 0.35, 0.0, 1.0))
		# Whole-body recoil backward: pelvis drops, torso arches in shock
		rig.root_pos = Vector2(532.0 - snap * 22.0, 1285.8 - snap * 6.0)
		rig.torso_lean_deg = lerpf(8.5, -6.5, snap)
		rig.spine_arch_deg = lerpf(6.5, -4.5, snap)
		rig.shoulder_shrug_px = snap * 12.0
		rig.right_shoulder_protract_px = 0.0
		
		# Head jerks up, hair whips back, glasses slip down nose
		rig.head_tilt_deg = lerpf(-3.0, 7.5, snap)
		rig.head_nod_px = lerpf(-2.0, -5.5, snap)
		rig.hair_lag_deg = -snap * 15.0
		rig.glasses_slip_px = snap * 4.5
		
		# Symmetrical startled eyebrows & open gasp
		rig.left_brow_raise_px = snap * 10.0
		rig.right_brow_raise_px = snap * 10.0
		rig.brow_slant_deg = 0.0
		rig.mouth_state = "open_gasp"
		
		# Hands fling up defensively
		rig.right_shoulder_deg = lerpf(65.0, 42.0, snap)
		rig.right_elbow_deg = lerpf(10.0, 55.0, snap)
		rig.right_wrist_deg = -25.0
		rig.right_hand_pose = "reach_open"
		
		rig.left_shoulder_deg = lerpf(2.0, 38.0, snap)
		rig.left_elbow_deg = lerpf(10.0, 52.0, snap)
		rig.left_wrist_deg = -20.0
		rig.left_hand_pose = "reach_open"

	# 5.0s - 6.0s: Smooth Recovery & Settle into Approved Neutral Stance
	else:
		var rec_t: float = (t - 5.0) / 1.0
		var p_rec: float = _ease_in_out(rec_t)
		_set_action("Smooth Recovery & Smirk Settle", true, true)
		
		# Torso and pelvis return smoothly to neutral balance
		rig.root_pos = Vector2(lerpf(510.0, 516.0, p_rec), 1285.8)
		rig.torso_lean_deg = lerpf(-6.5, 2.5, p_rec)
		rig.spine_arch_deg = lerpf(-4.5, 4.5, p_rec)
		rig.shoulder_shrug_px = lerpf(12.0, 0.0, p_rec)
		
		# Glasses slide back into position, hair settles
		rig.glasses_slip_px = lerpf(4.5, 0.0, p_rec)
		rig.hair_lag_deg = lerpf(-15.0, 0.0, p_rec)
		rig.head_tilt_deg = lerpf(7.5, -3.0, p_rec)
		rig.head_nod_px = lerpf(-5.5, -1.0, p_rec)
		
		# Eyebrows and mouth resolve into confident smirk
		rig.left_brow_raise_px = lerpf(10.0, 1.0, p_rec)
		rig.right_brow_raise_px = lerpf(10.0, 3.0, p_rec)
		rig.brow_slant_deg = lerpf(0.0, 2.0, p_rec)
		rig.mouth_state = "smirk" if rec_t >= 0.3 else "neutral"
		
		# Arms settle gracefully back to natural flank hang
		rig.right_shoulder_deg = lerpf(42.0, 6.0, p_rec)
		rig.right_elbow_deg = lerpf(55.0, 12.0, p_rec)
		rig.right_wrist_deg = lerpf(-25.0, 5.0, p_rec)
		rig.right_hand_pose = "relaxed"
		
		rig.left_shoulder_deg = lerpf(38.0, 4.0, p_rec)
		rig.left_elbow_deg = lerpf(52.0, 12.0, p_rec)
		rig.left_wrist_deg = lerpf(-20.0, 5.0, p_rec)
		rig.left_hand_pose = "relaxed"
		
		# Parallel grounded legs
		rig.left_thigh_deg = 14.0
		rig.left_shin_deg = -28.0
		rig.left_foot_deg = 14.0
		rig.right_thigh_deg = 14.0
		rig.right_shin_deg = -28.0
		rig.right_foot_deg = 14.0

# ---------------------------------------------------------------------------
# Isolated Milestone Clips
# ---------------------------------------------------------------------------
func _evaluate_idle(t: float) -> void:
	_set_action("Milestone 3 — Neutral Idle", true, true)
	var cycle: float = sin(t * TAU * 1.0)
	rig.root_pos = Vector2(540.0, 1285.8 - cycle * 1.5)
	rig.torso_lean_deg = 2.0 + cycle * 0.4
	rig.left_shoulder_deg = 4.0 + cycle * 0.5
	rig.left_elbow_deg = 12.0
	rig.right_shoulder_deg = 6.0 + cycle * 0.5
	rig.right_elbow_deg = 12.0
	rig.mouth_state = "neutral"

func _evaluate_walk(t: float) -> void:
	_set_action("Milestone 4 — Walk Cycle (3 Steps)", true, true)
	var norm_t: float = t / 2.5
	rig.root_pos.x = 420.0 + norm_t * 140.0
	var bob: float = absf(sin(norm_t * PI * 3.0)) * 6.0
	rig.root_pos.y = 1285.8 - bob
	var r_swing: float = sin(norm_t * PI * 3.0)
	var l_swing: float = -r_swing
	rig.right_thigh_deg = 14.0 + r_swing * 22.0
	rig.right_shin_deg = -28.0 + (maxf(0.0, -r_swing) * 28.0)
	rig.left_thigh_deg = 14.0 + l_swing * 22.0
	rig.left_shin_deg = -28.0 + (maxf(0.0, -l_swing) * 28.0)
	rig.left_shoulder_deg = 6.0 + r_swing * 18.0
	rig.right_shoulder_deg = 6.0 - r_swing * 18.0

func _evaluate_reach(t: float) -> void:
	_set_action("Milestone 5 — Coordinated Reach", true, true)
	var p: float = _ease_in_out(minf(1.0, t / 1.4))
	rig.root_pos = Vector2(540.0, 1285.8)
	rig.torso_lean_deg = lerpf(2.0, 8.5, p)
	rig.right_shoulder_protract_px = lerpf(0.0, 8.0, p)
	rig.right_shoulder_deg = lerpf(6.0, 65.0, p)
	rig.right_elbow_deg = lerpf(12.0, 10.0, p)
	rig.right_hand_pose = "point"

func _evaluate_acting(t: float) -> void:
	_set_action("Milestone 6 — Expressive Acting Test", true, true)
	if t < 0.8:
		# Curiosity
		var p: float = t / 0.8
		rig.head_tilt_deg = lerpf(1.5, -4.0, p)
		rig.right_brow_raise_px = lerpf(0.0, 3.5, p)
		rig.mouth_state = "curious_o"
	elif t < 1.6:
		# Surprise
		var snap: float = _elastic_out((t - 0.8) / 0.4)
		rig.torso_lean_deg = lerpf(2.0, -6.5, snap)
		rig.glasses_slip_px = snap * 4.5
		rig.left_brow_raise_px = snap * 10.0
		rig.right_brow_raise_px = snap * 10.0
		rig.mouth_state = "open_gasp"
	else:
		# Recovery
		var p: float = (t - 1.6) / 0.9
		rig.torso_lean_deg = lerpf(-6.5, 2.5, p)
		rig.glasses_slip_px = lerpf(4.5, 0.0, p)
		rig.right_brow_raise_px = lerpf(10.0, 3.0, p)
		rig.mouth_state = "smirk"

# ---------------------------------------------------------------------------
# Easing & Interpolation Math
# ---------------------------------------------------------------------------
func _ease_in_out(x: float) -> float:
	return 0.5 * (1.0 - cos(x * PI))

func _elastic_out(x: float) -> float:
	if x <= 0.0: return 0.0
	if x >= 1.0: return 1.0
	return sin(-13.0 * (x + 1.0) * (PI * 0.5)) * pow(2.0, -10.0 * x) + 1.0

func _set_action(label: String, left_plant: bool, right_plant: bool) -> void:
	if debug_overlay != null:
		debug_overlay.current_action_label = label
		debug_overlay.left_foot_planted = left_plant
		debug_overlay.right_foot_planted = right_plant
