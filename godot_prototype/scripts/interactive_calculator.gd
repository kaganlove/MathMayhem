@tool
class_name InteractiveCalculator
extends Node2D

## Deterministic Interactive 4x4 Pedestal Calculator for Math Mayhem Episode 001.
## Authoritative geometry, physical hit zones, depression states, and LCD display.

signal button_pressed(key_label: String)
signal button_released(key_label: String)
signal expression_evaluated(expr: String, result: String, is_error: bool)

@export var floor_y: float = 1620.0
@export var calc_pos: Vector2 = Vector2(670.0, 860.0):
	set(val):
		calc_pos = val
		_build_buttons()
		queue_redraw()

@export var calc_width: float = 240.0
@export var calc_height: float = 420.0

# Pedestal dimensions
@export var pedestal_width: float = 46.0
@export var base_width: float = 180.0
@export var base_height: float = 24.0

# LCD Display state
@export var expr_text: String = "READY"
@export var result_text: String = "0"
@export var is_error_mode: bool = false
@export var error_glow_pulse: float = 0.0

# Button definitions
# 4x4 grid:
# [ 7 ] [ 8 ] [ 9 ] [ ÷ ]
# [ 4 ] [ 5 ] [ 6 ] [ × ]
# [ 1 ] [ 2 ] [ 3 ] [ − ]
# [ C ] [ 0 ] [ + ] [ = ]
const GRID_ROWS = [
	["7", "8", "9", "÷"],
	["4", "5", "6", "×"],
	["1", "2", "3", "−"],
	["C", "0", "+", "="],
]

const BTN_WIDTH = 44.0
const BTN_HEIGHT = 44.0
const GAP_X = 10.0
const GAP_Y = 10.0
const PAD_X = 18.0
const GRID_TOP = 136.0

# Button states
var buttons: Dictionary = {}
# Active pressed button
var active_pressed_key: String = ""

# Contact & input logging for QA validation
var contact_log: Array = []

func _init() -> void:
	_build_buttons()

func _ready() -> void:
	_build_buttons()

func _build_buttons() -> void:
	buttons.clear()
	for r_idx in range(GRID_ROWS.size()):
		var row = GRID_ROWS[r_idx]
		for c_idx in range(row.size()):
			var label = row[c_idx]
			var local_x = PAD_X + c_idx * (BTN_WIDTH + GAP_X) + BTN_WIDTH * 0.5
			var local_y = GRID_TOP + r_idx * (BTN_HEIGHT + GAP_Y) + BTN_HEIGHT * 0.5
			
			buttons[label] = {
				"label": label,
				"row": r_idx,
				"col": c_idx,
				"local_center": Vector2(local_x, local_y),
				"world_center": calc_pos + Vector2(local_x, local_y),
				"width": BTN_WIDTH,
				"height": BTN_HEIGHT,
				"hit_radius": 24.0,
				"is_pressed": false,
				"depression_offset": 0.0,
			}

func get_button_world_pos(label: String) -> Vector2:
	if buttons.has(label):
		return calc_pos + buttons[label]["local_center"]
	return calc_pos + Vector2(calc_width * 0.5, calc_height * 0.5)

func press_button(label: String, hand_pos: Vector2 = Vector2.ZERO) -> bool:
	if not buttons.has(label):
		return false
	
	var btn = buttons[label]
	btn["is_pressed"] = true
	btn["depression_offset"] = 4.0
	active_pressed_key = label
	
	var dist = 0.0
	if hand_pos != Vector2.ZERO:
		dist = hand_pos.distance_to(btn["world_center"])
	
	contact_log.append({
		"action": "press",
		"key": label,
		"world_target": btn["world_center"],
		"hand_pos": hand_pos,
		"distance": dist,
		"time": Time.get_ticks_msec(),
	})
	
	button_pressed.emit(label)
	queue_redraw()
	return true

func release_button(label: String, hand_pos: Vector2 = Vector2.ZERO) -> bool:
	if not buttons.has(label):
		return false
	
	var btn = buttons[label]
	btn["is_pressed"] = false
	btn["depression_offset"] = 0.0
	if active_pressed_key == label:
		active_pressed_key = ""
	
	var dist = 0.0
	if hand_pos != Vector2.ZERO:
		dist = hand_pos.distance_to(btn["world_center"])
		
	contact_log.append({
		"action": "release",
		"key": label,
		"world_target": btn["world_center"],
		"hand_pos": hand_pos,
		"distance": dist,
		"time": Time.get_ticks_msec(),
	})
	
	button_released.emit(label)
	queue_redraw()
	return true

func set_display(expr: String, result: String, is_err: bool = false) -> void:
	expr_text = expr
	result_text = result
	is_error_mode = is_err
	expression_evaluated.emit(expr, result, is_err)
	queue_redraw()

func _draw() -> void:
	var body_x = calc_pos.x
	var body_y = calc_pos.y
	var body_w = calc_width
	var body_h = calc_height
	var body_bottom = body_y + body_h
	
	# 1. Pedestal Stand & Base
	var stand_cx = body_x + body_w * 0.5
	var stand_left = stand_cx - pedestal_width * 0.5
	var stand_h = floor_y - body_bottom
	
	# Stand column
	draw_rect(Rect2(stand_left, body_bottom, pedestal_width, stand_h), Color(0.85, 0.87, 0.90))
	draw_rect(Rect2(stand_left, body_bottom, pedestal_width, stand_h), Color(0.15, 0.18, 0.22), false, 4.0)
	
	# Base plate
	var base_left = stand_cx - base_width * 0.5
	draw_rect(Rect2(base_left, floor_y - base_height, base_width, base_height), Color(0.80, 0.82, 0.86))
	draw_rect(Rect2(base_left, floor_y - base_height, base_width, base_height), Color(0.15, 0.18, 0.22), false, 4.0)
	
	# 2. Main Calculator Body
	# Drop shadow
	draw_rect(Rect2(body_x + 6, body_y + 8, body_w, body_h), Color(0.0, 0.0, 0.0, 0.12))
	# Body chassis
	var body_bg = Color(0.94, 0.95, 0.96)
	draw_rect(Rect2(body_x, body_y, body_w, body_h), body_bg)
	# Chassis outline
	var outline_col = Color(0.12, 0.15, 0.18)
	if is_error_mode:
		outline_col = Color(0.85, 0.12, 0.12).lerp(Color(0.2, 0.05, 0.05), error_glow_pulse * 0.5)
	draw_rect(Rect2(body_x, body_y, body_w, body_h), outline_col, false, 5.0)
	
	# Top accent bar
	var bar_col = Color(0.25, 0.35, 0.45) if not is_error_mode else Color(0.85, 0.15, 0.15)
	draw_rect(Rect2(body_x + 4, body_y + 4, body_w - 8, 8), bar_col)
	
	# 3. LCD Screen
	var lcd_x = body_x + 16.0
	var lcd_y = body_y + 20.0
	var lcd_w = body_w - 32.0
	var lcd_h = 96.0
	
	var lcd_bg = Color(0.86, 0.90, 0.85)
	var lcd_border = Color(0.25, 0.30, 0.26)
	if is_error_mode:
		lcd_bg = Color(0.96, 0.88, 0.88)
		lcd_border = Color(0.85, 0.15, 0.15)
		
	draw_rect(Rect2(lcd_x, lcd_y, lcd_w, lcd_h), lcd_bg)
	draw_rect(Rect2(lcd_x, lcd_y, lcd_w, lcd_h), lcd_border, false, 3.0)
	
	# Expression text (top-right of LCD)
	var expr_color = Color(0.20, 0.25, 0.22) if not is_error_mode else Color(0.60, 0.15, 0.15)
	draw_string(ThemeDB.fallback_font, Vector2(lcd_x + 12, lcd_y + 28), expr_text, HORIZONTAL_ALIGNMENT_LEFT, lcd_w - 24, 18, expr_color)
	
	# Result text (prominent, bottom of LCD)
	var result_color = Color(0.10, 0.14, 0.12)
	var font_sz = 30
	if is_error_mode:
		result_color = Color(0.90, 0.05, 0.05)
		font_sz = 26
	draw_string(ThemeDB.fallback_font, Vector2(lcd_x + 12, lcd_y + 72), result_text, HORIZONTAL_ALIGNMENT_RIGHT, lcd_w - 24, font_sz, result_color)
	
	# 4. Keypad Buttons
	for label in buttons.keys():
		var btn = buttons[label]
		var c = btn["world_center"]
		var dep = btn["depression_offset"]
		var is_pressed = btn["is_pressed"]
		
		var bx = c.x - BTN_WIDTH * 0.5
		var by = c.y - BTN_HEIGHT * 0.5 + dep
		var bw = BTN_WIDTH
		var bh = BTN_HEIGHT
		
		# Button base colors
		var btn_bg = Color(0.98, 0.98, 1.0)
		var text_col = Color(0.15, 0.18, 0.22)
		var border_col = Color(0.20, 0.24, 0.30)
		
		# Color coding by button category
		if label in ["÷", "×", "−", "+", "="]:
			btn_bg = Color(0.88, 0.92, 0.98)
			text_col = Color(0.08, 0.22, 0.45)
		elif label == "C":
			btn_bg = Color(0.98, 0.88, 0.88)
			text_col = Color(0.65, 0.12, 0.12)
			
		if is_pressed:
			btn_bg = btn_bg.lerp(Color(0.6, 0.8, 1.0), 0.6)
			border_col = Color(0.0, 0.45, 0.85)
			
		# Drop shadow when unpressed
		if not is_pressed:
			draw_rect(Rect2(bx + 2, by + 3, bw, bh), Color(0.0, 0.0, 0.0, 0.15))
			
		# Button face
		draw_rect(Rect2(bx, by, bw, bh), btn_bg)
		draw_rect(Rect2(bx, by, bw, bh), border_col, false, 2.5 if not is_pressed else 3.5)
		
		# Button label
		var text_offset_y = 30.0
		var btn_font_size = 22
		if label in ["÷", "×", "−", "+", "="]:
			btn_font_size = 24
			text_offset_y = 31.0
			
		draw_string(ThemeDB.fallback_font, Vector2(bx, by + text_offset_y), label, HORIZONTAL_ALIGNMENT_CENTER, bw, btn_font_size, text_col)
