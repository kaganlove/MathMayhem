class_name InteractiveButton
extends Node2D

## Math Mayhem v13 — Interactive Button Prop & Physical Target Provider
## Encapsulates physical button geometry, interaction landmarks, and state events.
## Replaces hardcoded screen coordinates with an object-relative target system:
## - Approach Position
## - Pre-Contact Hover Position
## - Contact Surface Point
## - Fully Depressed Surface Point
## - Release Retraction Position

signal contact_established(hand_pos: Vector2)
signal button_depressed(depth: float)
signal button_activated()
signal button_released()

@export var pedestal_pos: Vector2 = Vector2(760.0, 1220.0)
@export var button_radius: float = 38.0
@export var button_height: float = 14.0
@export var max_depress_px: float = 8.0

var current_depression: float = 0.0
var is_active: bool = false
var glow_alpha: float = 0.0

func get_approach_pos() -> Vector2:
	return Vector2(pedestal_pos.x - 220.0, pedestal_pos.y + 65.8)

func get_pre_contact_pos() -> Vector2:
	return Vector2(pedestal_pos.x, pedestal_pos.y - 42.0)

func get_contact_pos() -> Vector2:
	return Vector2(pedestal_pos.x, pedestal_pos.y - button_height + current_depression)

func get_depressed_pos() -> Vector2:
	return Vector2(pedestal_pos.x, pedestal_pos.y - button_height + max_depress_px)

func get_release_pos() -> Vector2:
	return Vector2(pedestal_pos.x - 20.0, pedestal_pos.y - button_height - 25.0)

func set_depression(depress_px: float) -> void:
	var prev = current_depression
	current_depression = clampf(depress_px, 0.0, max_depress_px)
	button_depressed.emit(current_depression)
	if current_depression >= max_depress_px and not is_active:
		activate()
	elif current_depression < prev and prev >= max_depress_px:
		button_released.emit()

## Physical contact validation: only depresses if hand end-effector is within contact threshold
func attempt_press(hand_pos: Vector2, depress_px: float, tolerance: float = 12.0) -> bool:
	var c_pos = get_contact_pos()
	var dist = hand_pos.distance_to(c_pos)
	if dist <= tolerance:
		set_depression(depress_px)
		contact_established.emit(hand_pos)
		return true
	return false

func activate() -> void:
	is_active = true
	glow_alpha = 1.0
	button_activated.emit()

func reset() -> void:
	current_depression = 0.0
	is_active = false
	glow_alpha = 0.0
