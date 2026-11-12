class_name InteractivePickupObject
extends Node2D

## Math Mayhem v13.3 — Reusable Contact-Driven Pickup & Grasp Object
## Implements the authoritative 8-state physical acquisition state machine:
## GROUNDED -> REACHING -> CONTACT -> GRASPING -> ATTACHED -> LIFTING -> CARRIED -> RELEASED
## Guarantees strictly 0.0px teleportation jump and physical contact validation.

signal state_changed(old_state: int, new_state: int)
signal contact_established(hand_pos: Vector2)
signal grasped(grip_pos: Vector2)
signal lifted(start_pos: Vector2)
signal released(world_pos: Vector2)

enum ObjectState {
	GROUNDED,
	REACHING,
	CONTACT,
	GRASPING,
	ATTACHED,
	LIFTING,
	CARRIED,
	RELEASED
}

const STATE_NAMES: Dictionary = {
	ObjectState.GROUNDED: "GROUNDED",
	ObjectState.REACHING: "REACHING",
	ObjectState.CONTACT: "CONTACT",
	ObjectState.GRASPING: "GRASPING",
	ObjectState.ATTACHED: "ATTACHED",
	ObjectState.LIFTING: "LIFTING",
	ObjectState.CARRIED: "CARRIED",
	ObjectState.RELEASED: "RELEASED"
}

@export var object_type: String = "yellow_gadget" # "yellow_gadget", "math_tablet", "chalk_stylus"
@export var ground_pos: Vector2 = Vector2(660.0, 1575.0)
@export var current_state: ObjectState = ObjectState.GROUNDED

# Object Dimensions (at scale 1.0, scaled by character_scale)
@export var size_px: Vector2 = Vector2(32.0, 36.0)
@export var grip_offset: Vector2 = Vector2(0.0, -12.0) # Relative to object center
@export var contact_tolerance_px: float = 24.0 # Generous tolerance encompassing palm-to-fingertip span

var world_pos: Vector2 = Vector2.ZERO
var world_rot_deg: float = 0.0
var attachment_hand_offset: Vector2 = Vector2.ZERO
var attachment_hand_rot_offset: float = 0.0
var is_grasped: bool = false

func _ready() -> void:
	reset_to_ground()

func reset_to_ground() -> void:
	current_state = ObjectState.GROUNDED
	world_pos = ground_pos
	world_rot_deg = 0.0
	is_grasped = false
	attachment_hand_offset = Vector2.ZERO
	attachment_hand_rot_offset = 0.0

func get_grip_world_pos() -> Vector2:
	if current_state == ObjectState.GROUNDED or current_state == ObjectState.REACHING or current_state == ObjectState.CONTACT or current_state == ObjectState.GRASPING:
		return ground_pos + grip_offset
	return world_pos + grip_offset.rotated(deg_to_rad(world_rot_deg))

func check_contact(hand_pos: Vector2) -> bool:
	var grip_pos = get_grip_world_pos()
	var dist = hand_pos.distance_to(grip_pos)
	return dist <= contact_tolerance_px

func notify_reaching() -> void:
	if current_state == ObjectState.GROUNDED:
		_transition_to(ObjectState.REACHING)

func establish_contact(hand_pos: Vector2) -> bool:
	if not check_contact(hand_pos):
		return false
	if current_state == ObjectState.REACHING or current_state == ObjectState.GROUNDED:
		_transition_to(ObjectState.CONTACT)
		contact_established.emit(hand_pos)
	return true

func begin_grasp() -> void:
	if current_state == ObjectState.CONTACT:
		_transition_to(ObjectState.GRASPING)

## Binds object to hand, recording attachment offset to guarantee 0.0px jump
func grasp(hand_grip_pos: Vector2, hand_rot_deg: float) -> bool:
	if not check_contact(hand_grip_pos):
		# Rejected: hand is not within contact tolerance!
		push_warning("PickupObject.grasp rejected: hand distance %.2f exceeds tolerance %.2f" % [hand_grip_pos.distance_to(get_grip_world_pos()), contact_tolerance_px])
		return false
	
	# Compute hand-local offset at the exact instant of attachment
	# so world_pos before attachment == world_pos after attachment
	var delta = world_pos - hand_grip_pos
	attachment_hand_offset = delta.rotated(-deg_to_rad(hand_rot_deg))
	attachment_hand_rot_offset = world_rot_deg - hand_rot_deg
	
	is_grasped = true
	_transition_to(ObjectState.ATTACHED)
	grasped.emit(hand_grip_pos)
	return true

func start_lifting(hand_grip_pos: Vector2, hand_rot_deg: float) -> void:
	if is_grasped and (current_state == ObjectState.ATTACHED or current_state == ObjectState.GRASPING):
		_transition_to(ObjectState.LIFTING)
		lifted.emit(world_pos)
	update_carried_transform(hand_grip_pos, hand_rot_deg)

func update_carried_transform(hand_grip_pos: Vector2, hand_rot_deg: float) -> void:
	if not is_grasped:
		return
	# Authoritative global transform derived strictly from hand
	world_rot_deg = hand_rot_deg + attachment_hand_rot_offset
	world_pos = hand_grip_pos + attachment_hand_offset.rotated(deg_to_rad(hand_rot_deg))
	
	if current_state == ObjectState.LIFTING and world_pos.y < ground_pos.y - 80.0:
		_transition_to(ObjectState.CARRIED)

func release(drop_velocity: Vector2 = Vector2.ZERO) -> void:
	is_grasped = false
	_transition_to(ObjectState.RELEASED)
	released.emit(world_pos)

func _transition_to(new_state: ObjectState) -> void:
	var old_state = current_state
	current_state = new_state
	state_changed.emit(old_state, new_state)

func draw_object(canvas: CanvasItem, s: float) -> void:
	var draw_pos = world_pos if (current_state == ObjectState.ATTACHED or current_state == ObjectState.LIFTING or current_state == ObjectState.CARRIED or current_state == ObjectState.RELEASED) else ground_pos
	var ink = Color(0.06, 0.08, 0.12)
	
	match object_type:
		"math_tablet":
			# Flat sleek rectangular math slate
			var w = size_px.x * s
			var h = size_px.y * s
			var rect = Rect2(draw_pos.x - w * 0.5, draw_pos.y - h * 0.5, w, h)
			canvas.draw_rect(rect, Color(0.22, 0.28, 0.38))
			canvas.draw_rect(rect, ink, false, 3.0 * s)
			# Screen surface with glowing formula
			var scr_rect = Rect2(draw_pos.x - w * 0.42, draw_pos.y - h * 0.42, w * 0.84, h * 0.84)
			canvas.draw_rect(scr_rect, Color(0.10, 0.14, 0.20))
			canvas.draw_line(Vector2(draw_pos.x - w * 0.25, draw_pos.y), Vector2(draw_pos.x + w * 0.25, draw_pos.y), Color(0.0, 0.85, 1.0), 2.0 * s)
			
		"chalk_stylus":
			# Narrow cylinder/stylus
			var len_px = size_px.y * s
			var rad_px = size_px.x * 0.5 * s
			var pts: PackedVector2Array = [
				draw_pos + Vector2(-rad_px, -len_px * 0.5),
				draw_pos + Vector2(rad_px, -len_px * 0.5),
				draw_pos + Vector2(rad_px, len_px * 0.5),
				draw_pos + Vector2(-rad_px, len_px * 0.5)
			]
			canvas.draw_colored_polygon(pts, Color(0.95, 0.95, 0.92))
			canvas.draw_polyline(pts, ink, 2.5 * s, true)
			
		"yellow_gadget", _:
			# Canonical golden prism / octahedron
			var sz = size_px.x * 0.5 * s
			var pts: PackedVector2Array = [
				draw_pos + Vector2(0.0, -sz * 1.3),
				draw_pos + Vector2(sz * 0.85, -sz * 0.25),
				draw_pos + Vector2(0.0, sz * 0.75),
				draw_pos + Vector2(-sz * 0.85, -sz * 0.25)
			]
			canvas.draw_colored_polygon(pts, Color(0.98, 0.75, 0.15, 0.95))
			canvas.draw_polyline(pts, ink, 3.5 * s, true)
			# Facet highlights
			canvas.draw_line(draw_pos + Vector2(0.0, -sz * 1.3), draw_pos + Vector2(0.0, sz * 0.75), ink, 2.0 * s)
			canvas.draw_line(draw_pos + Vector2(-sz * 0.85, -sz * 0.25), draw_pos + Vector2(sz * 0.85, -sz * 0.25), ink, 2.0 * s)
