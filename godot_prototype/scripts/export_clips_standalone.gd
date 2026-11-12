extends SceneTree

const ClipLibraryV12 = preload("res://scripts/clip_library_v12.gd")

func _init() -> void:
	print("--- Building and serializing all v12 modular animation clips ---")
	var clips = ClipLibraryV12.build_and_save_all_clips("res://animations/clips")
	print("Successfully serialized %d animation clips!" % clips.size())
	quit(0)
