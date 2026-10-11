"""Render the exported GLB back through Blender and make a loop GIF for QA."""
from pathlib import Path
import os
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCH_MODELS = REPO / "presentations" / "schumpeter" / "models"
os.environ.setdefault("GLB_DIR", str(HERE / "glb"))
sys.path.insert(0, str(SCH_MODELS))
import bpy  # noqa: E402
import render  # noqa: E402
from PIL import Image  # noqa: E402

OUT = HERE.parent / "preview"
OUT.mkdir(parents=True, exist_ok=True)


def make_preview(key="kashtan", frames=10, px=300, samples=10, rot=(10, -18, 0)):
    scene = render.setup_scene(px, samples)
    root, radius = render.load_model(key)
    render.camera(scene, radius)
    render.add_lights(scene, 0)
    render.set_rot(root, *rot)
    actions = [o.animation_data.action for o in bpy.data.objects if o.animation_data and o.animation_data.action]
    start, end = actions[0].frame_range if actions else (0, 0)
    temp = OUT / ".animation-frames"
    temp.mkdir(exist_ok=True)
    rendered = []
    for i in range(frames):
        frame = start + (end - start) * i / frames
        scene.frame_set(int(frame), subframe=frame - int(frame))
        scene.render.filepath = str(temp / f"{key}-{i:02d}.png")
        bpy.ops.render.render(write_still=True)
        rendered.append(Path(scene.render.filepath))
    frames_rgb = []
    for file in rendered:
        rgba = Image.open(file).convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (248, 245, 237, 255))
        bg.alpha_composite(rgba)
        frames_rgb.append(bg.convert("RGB"))
    path = OUT / f"{key}-animation.gif"
    frames_rgb[0].save(path, save_all=True, append_images=frames_rgb[1:], loop=0,
                       duration=max(80, int((end - start) / scene.render.fps * 1000 / frames)),
                       optimize=True, disposal=2)
    strip = Image.new("RGB", (px * frames, px), (248, 245, 237))
    for i, frame in enumerate(frames_rgb):
        strip.paste(frame, (i * px, 0))
    strip.save(OUT / f"{key}-animation-strip.jpg", quality=88, optimize=True)
    for file in rendered:
        file.unlink(missing_ok=True)
    temp.rmdir()
    print(f"[anim] {key}: {frames} frames over {(end-start)/scene.render.fps:.2f}s -> {path}", flush=True)


if __name__ == "__main__":
    make_preview(
        frames=int(os.environ.get("FRAMES", "10")),
        px=int(os.environ.get("PX", "300")),
        samples=int(os.environ.get("SAMPLES", "10")),
        rot=tuple(float(value) for value in os.environ.get("ROT", "10,-18,0").split(",")),
    )
