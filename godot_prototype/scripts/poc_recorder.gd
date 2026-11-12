extends Node2D

## Headless / Batch Frame Renderer for Godot 2D Prototype
## Renders frame-accurate clean or debug image sequences and coordinates video compilation.

const CharacterRig2D = preload("res://scripts/character_rig_2d.gd")
const DebugOverlay = preload("res://scripts/debug_overlay.gd")
const AnimationController = preload("res://scripts/anim_controller.gd")

var rig: Node2D
var debug_layer: Node2D
var anim: Node

var is_debug_mode: bool = false
var fps: int = 30
var duration: float = 6.0
var output_dir: String = "res://temp_frames"

func _ready() -> void:
	var target_clip: String = "full_poc"
	# Parse command line args
	var args: PackedStringArray = OS.get_cmdline_user_args()
	for arg in args:
		if arg == "--debug":
			is_debug_mode = true
		elif arg.begins_with("--clip="):
			target_clip = arg.substr(7)
		elif arg.begins_with("--out="):
			output_dir = arg.substr(6)
	
	_setup_scene(target_clip)
	_render_sequence()

func _setup_scene(target_clip: String) -> void:
	RenderingServer.set_default_clear_color(Color(0.96, 0.97, 0.98))
	
	rig = CharacterRig2D.new()
	rig.name = "CharacterRig"
	add_child(rig)
	
	debug_layer = DebugOverlay.new()
	debug_layer.name = "DebugOverlay"
	debug_layer.target_rig = rig
	debug_layer.show_debug = is_debug_mode
	add_child(debug_layer)
	
	anim = AnimationController.new()
	anim.name = "AnimationController"
	anim.rig = rig
	anim.debug_overlay = debug_layer
	anim.set_clip(target_clip)
	duration = anim.clip_duration
	add_child(anim)

func _render_sequence() -> void:
	var total_frames: int = int(round(duration * float(fps)))
	print("Starting Godot batch render: clip=%s, total_frames=%d, fps=%d, debug=%s" % [anim.active_clip, total_frames, fps, str(is_debug_mode)])
	
	var dir = DirAccess.open("res://")
	if not dir.dir_exists(output_dir):
		dir.make_dir_recursive(output_dir)
		
	# Render loop
	for i in range(total_frames):
		var t: float = float(i) / float(fps)
		anim.evaluate_at(t)
		
		# Force synchronous draw
		RenderingServer.force_draw()
		await get_tree().process_frame
		
		var img: Image = get_viewport().get_texture().get_image()
		var frame_path: String = "%s/frame_%04d.png" % [output_dir, i]
		var err = img.save_png(frame_path)
		if err != OK:
			printerr("Failed saving frame: ", frame_path)
			
		if i % 30 == 0:
			print("Rendered frame %d / %d (%.2fs / %.2fs)" % [i, total_frames, t, duration])
			
	print("Batch render finished successfully. Frames saved to: ", output_dir)
	get_tree().quit(0)
