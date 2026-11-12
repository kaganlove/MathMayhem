class_name CharacterStateMachine
extends Node

## Math Mayhem v12 — Production Character Animation State Machine
## Orchestrates modular animation states, smooth transitions, and event triggers:
## - Manages states: IDLE, CURIOSITY, WALK, HESITATE, PRESS, SURPRISE, RECOVERY, AMUSED.
## - Supports seamless cross-fades via Godot's AnimationPlayer blending.
## - Emits frame-accurate signals for audio/SFX synchronization.
## - Executes scripted episodic beat sequences.

signal state_changed(old_state: String, new_state: String)
signal contact_event(event_name: String, landmark_pos: Vector2)
signal sequence_completed()

enum State {
	IDLE,
	CURIOSITY,
	WALK,
	HESITATE,
	PRESS,
	SURPRISE,
	RECOVERY,
	AMUSED
}

const STATE_NAMES: Dictionary = {
	State.IDLE: "idle_neutral",
	State.CURIOSITY: "curiosity_notice",
	State.WALK: "walk_cycle",
	State.HESITATE: "hesitate_doubt",
	State.PRESS: "button_press",
	State.SURPRISE: "surprise_recoil",
	State.RECOVERY: "recovery_glasses_push",
	State.AMUSED: "amused_smirk"
}

@export var rig: Node2D
@export var anim_player: AnimationPlayer

var current_state: State = State.IDLE
var is_playing_sequence: bool = false
var sequence_queue: Array[Dictionary] = []
var sequence_step_timer: float = 0.0
var sequence_step_duration: float = 0.0

const ClipLibraryV12 = preload("res://scripts/clip_library_v12.gd")

func _ready() -> void:
	_setup_anim_player()
	play_state(State.IDLE)

func _setup_anim_player() -> void:
	if anim_player == null:
		anim_player = AnimationPlayer.new()
		anim_player.name = "StateMachinePlayer"
		anim_player.root_node = NodePath("../..")
		add_child(anim_player)

	var lib = AnimationLibrary.new()
	var clips = ClipLibraryV12.build_and_save_all_clips("res://animations/clips")
	for clip_name in clips:
		lib.add_animation(clip_name, clips[clip_name])
	
	if anim_player.has_animation_library(""):
		anim_player.remove_animation_library("")
	anim_player.add_animation_library("", lib)

	# Set up default blend transitions for smooth crossfades
	anim_player.set_blend_time("idle_neutral", "walk_cycle", 0.25)
	anim_player.set_blend_time("walk_cycle", "hesitate_doubt", 0.3)
	anim_player.set_blend_time("hesitate_doubt", "button_press", 0.2)
	anim_player.set_blend_time("button_press", "surprise_recoil", 0.05) # Snappy explosive shock!
	anim_player.set_blend_time("surprise_recoil", "recovery_glasses_push", 0.35)
	anim_player.set_blend_time("recovery_glasses_push", "amused_smirk", 0.3)
	anim_player.set_blend_time("amused_smirk", "idle_neutral", 0.3)

func play_state(new_state: State, custom_blend: float = -1.0) -> void:
	var old_state_name = STATE_NAMES.get(current_state, "unknown")
	var new_state_name = STATE_NAMES.get(new_state, "idle_neutral")
	current_state = new_state

	if anim_player != null and anim_player.has_animation(new_state_name):
		anim_player.play(new_state_name, custom_blend)

	state_changed.emit(old_state_name, new_state_name)

func play_state_by_name(state_name: String, custom_blend: float = -1.0) -> void:
	for s in STATE_NAMES:
		if STATE_NAMES[s] == state_name.to_lower():
			play_state(s, custom_blend)
			return
	printerr("Unknown state name: ", state_name)

func play_sequence(steps: Array) -> void:
	sequence_queue.clear()
	for s in steps:
		sequence_queue.append(s)
	is_playing_sequence = true
	_advance_sequence()

func _advance_sequence() -> void:
	if sequence_queue.is_empty():
		is_playing_sequence = false
		sequence_completed.emit()
		return

	var step = sequence_queue.pop_front()
	var state_str: String = step.get("state", "idle_neutral")
	sequence_step_duration = step.get("duration", 1.5)
	sequence_step_timer = 0.0
	var blend: float = step.get("blend", -1.0)

	play_state_by_name(state_str, blend)

func _process(delta: float) -> void:
	if is_playing_sequence:
		sequence_step_timer += delta
		if sequence_step_timer >= sequence_step_duration:
			_advance_sequence()
