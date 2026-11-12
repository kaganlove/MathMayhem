class_name CharacterStateMachine
extends Node

## Math Mayhem v13 — Reusable 14-State Animation & Interaction State Machine
## Implements Phase 9 Directive Architecture:
## IDLE, NOTICE_TARGET, LOOK_AT_TARGET, CONSIDER, ANTICIPATE, REACH,
## CONTACT, PRESS, HOLD, RELEASE, WITHDRAW, WAIT, REACT, RECOVER.
##
## Decouples high-level acting intent from low-level joint kinematics.
## Emits frame-accurate events for audio/sound synchronization and camera direction.

signal state_entered(state_name: String)
signal state_exited(state_name: String)
signal contact_event(event_name: String, position: Vector2)
signal interaction_completed()

enum State {
	IDLE,
	NOTICE_TARGET,
	LOOK_AT_TARGET,
	CONSIDER,
	ANTICIPATE,
	REACH,
	CONTACT,
	PRESS,
	HOLD,
	RELEASE,
	WITHDRAW,
	WAIT,
	REACT,
	RECOVER
}

const STATE_NAMES: Dictionary = {
	State.IDLE: "IDLE",
	State.NOTICE_TARGET: "NOTICE_TARGET",
	State.LOOK_AT_TARGET: "LOOK_AT_TARGET",
	State.CONSIDER: "CONSIDER",
	State.ANTICIPATE: "ANTICIPATE",
	State.REACH: "REACH",
	State.CONTACT: "CONTACT",
	State.PRESS: "PRESS",
	State.HOLD: "HOLD",
	State.RELEASE: "RELEASE",
	State.WITHDRAW: "WITHDRAW",
	State.WAIT: "WAIT",
	State.REACT: "REACT",
	State.RECOVER: "RECOVER"
}

@export var rig: Node2D
@export var interactive_target: Node2D

var current_state: State = State.IDLE
var state_time: float = 0.0
var state_duration: float = 1.0

# Base standing landmarks
const STANDING_Y: float = 1285.8

func _ready() -> void:
	transition_to(State.IDLE)

func transition_to(new_state: State) -> void:
	var old_state = current_state
	var old_name = STATE_NAMES.get(old_state, "UNKNOWN")
	var new_name = STATE_NAMES.get(new_state, "UNKNOWN")
	
	_on_state_exit(old_state)
	state_exited.emit(old_name)
	
	current_state = new_state
	state_time = 0.0
	_on_state_enter(new_state)
	state_entered.emit(new_name)

func _on_state_exit(old_state: State) -> void:
	if rig == null:
		return
	match old_state:
		State.REACH, State.CONTACT:
			# If transitioning anywhere other than PRESS/CONTACT, release hand IK
			if current_state != State.CONTACT and current_state != State.PRESS:
				rig.release_hand_ik()
		State.PRESS, State.HOLD:
			# Ensure hand detachment and proper mechanical release
			rig.detach_hand_from_button()
			if is_instance_valid(interactive_target):
				interactive_target.set_depression(0.0)

func _on_state_enter(state: State) -> void:
	if rig == null:
		return

	match state:
		State.IDLE:
			state_duration = 1.0
			rig.set_expression("neutral")
			rig.clear_gaze_target()
			rig.release_hand_ik()
			# Stand tall, lock feet to baseline
			rig.root_pos = Vector2(380.0, STANDING_Y)
			rig.torso_lean_deg = 0.0
			rig.shoulder_shrug_px = 0.0
			rig.hair_lag_deg = 0.0
			rig.glasses_slip_px = 0.0
			rig.lock_foot("left", Vector2(380.0 - 13.0 * rig.character_scale, 1592.8))
			rig.lock_foot("right", Vector2(380.0 + 13.0 * rig.character_scale, 1592.8))

		State.NOTICE_TARGET:
			state_duration = 0.8
			rig.set_expression("curious", 0.8)
			if is_instance_valid(interactive_target):
				rig.look_at_target(interactive_target.get_contact_pos())
			rig.torso_lean_deg = 8.0 # Small lean toward object

		State.LOOK_AT_TARGET:
			state_duration = 0.6
			rig.set_expression("curious", 1.0)
			rig.torso_lean_deg = 14.0

		State.CONSIDER:
			state_duration = 1.2
			rig.set_expression("hesitant", 1.0)
			# Hand hovers at pre-contact position
			if is_instance_valid(interactive_target):
				rig.reach_hand_to(interactive_target.get_pre_contact_pos(), true)
			rig.left_shoulder_deg = 14.0
			rig.left_elbow_deg = 72.0 # Left hand on hip contrapposto
			rig.right_hand_pose = "hesitant"

		State.ANTICIPATE:
			state_duration = 0.35
			rig.set_expression("confident", 0.7)
			rig.torso_lean_deg = 2.0 # Subtle pull-back before drive
			rig.right_shoulder_protract_px = -2.0

		State.REACH:
			state_duration = 0.4
			rig.set_expression("confident", 1.0)
			rig.torso_lean_deg = 10.0 # Forward commitment
			rig.right_shoulder_protract_px = 10.0
			rig.right_hand_pose = "press"
			if is_instance_valid(interactive_target):
				rig.reach_hand_to(interactive_target.get_contact_pos(), true)

		State.CONTACT:
			state_duration = 0.15
			rig.right_hand_pose = "press"
			if is_instance_valid(interactive_target):
				var c_pos = interactive_target.get_contact_pos()
				rig.reach_hand_to(c_pos, true)
				contact_event.emit("button_contact", c_pos)

		State.PRESS:
			state_duration = 0.35
			rig.attach_hand_to_button()
			if is_instance_valid(interactive_target):
				interactive_target.set_depression(8.0)
				contact_event.emit("button_depressed", interactive_target.get_depressed_pos())

		State.HOLD:
			state_duration = 0.45
			rig.attach_hand_to_button()

		State.RELEASE:
			state_duration = 0.3
			rig.detach_hand_from_button()
			if is_instance_valid(interactive_target):
				interactive_target.set_depression(0.0)
				rig.reach_hand_to(interactive_target.get_release_pos(), true)
				contact_event.emit("button_released", interactive_target.get_contact_pos())

		State.WITHDRAW:
			state_duration = 0.5
			rig.release_hand_ik()
			rig.set_expression("thoughtful", 0.8)

		State.WAIT:
			state_duration = 0.6
			rig.set_expression("thoughtful", 1.0)

		State.REACT:
			state_duration = 1.4
			rig.set_expression("surprised", 1.0)
			# Explosive recoil snap
			rig.torso_lean_deg = -18.0
			rig.shoulder_shrug_px = 26.0
			rig.hair_lag_deg = -30.0
			rig.glasses_slip_px = 7.0
			rig.right_hand_pose = "recoil"
			rig.left_hand_pose = "recoil"
			contact_event.emit("shock_recoil", rig.solved_head_center)

		State.RECOVER:
			state_duration = 2.0
			rig.set_expression("satisfied", 1.0)
			rig.torso_lean_deg = -2.0
			rig.shoulder_shrug_px = 0.0
			rig.hair_lag_deg = 0.0
			rig.glasses_slip_px = 0.0
			rig.right_hand_pose = "amused"
			rig.left_hand_pose = "relaxed"

func _process(delta: float) -> void:
	state_time += delta
	# Update active procedural constraints
	if current_state == State.PRESS or current_state == State.HOLD:
		if interactive_target != null:
			rig.button_depress_px = interactive_target.current_depression
	elif current_state == State.REACH:
		if interactive_target != null:
			rig.reach_hand_to(interactive_target.get_contact_pos(), true)
