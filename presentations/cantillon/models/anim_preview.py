# QA for the embedded animations: re-imports the exported .glb (exactly what PowerPoint receives),
# poses the skin at N moments of the loop and renders them with Cycles into a strip + animated GIF.
#
#   LD_LIBRARY_PATH=/tmp/bstub python3 models/anim_preview.py chest ship    -> models/_anim/<key>.png / .gif
#   env: FRAMES=8 PX=320 SAMPLES=10 ROT="12,-30,0"
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "schumpeter", "models"))
os.environ.setdefault("GLB_DIR", os.path.join(HERE, "glb"))
import render  # noqa: E402
import bpy  # noqa: E402

OUT = os.path.join(HERE, "_anim")
os.makedirs(OUT, exist_ok=True)


def frames_for(key, n, px, samples, rot):
    sc = render.setup_scene(px, samples)
    root, r = render.load_model(key)
    render.camera(sc, r)
    render.add_lights(sc, 0)
    render.set_rot(root, *rot)
    acts = [o.animation_data.action for o in bpy.data.objects if o.animation_data and o.animation_data.action]
    f0, f1 = acts[0].frame_range if acts else (0, 0)
    paths = []
    for i in range(n):
        f = f0 + (f1 - f0) * i / n
        sc.frame_set(int(f), subframe=f - int(f))
        p = os.path.join(OUT, f"{key}_{i:02d}.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    return paths, (f1 - f0) / sc.render.fps


if __name__ == "__main__":
    from PIL import Image
    n = int(os.environ.get("FRAMES", "8"))
    px = int(os.environ.get("PX", "320"))
    samples = int(os.environ.get("SAMPLES", "10"))
    rot = tuple(float(v) for v in os.environ.get("ROT", "12,-30,0").split(","))
    for key in sys.argv[1:]:
        paths, secs = frames_for(key, n, px, samples, rot)
        ims = [Image.open(p).convert("RGBA") for p in paths]
        strip = Image.new("RGBA", (px * len(ims), px), (24, 26, 34, 255))
        gif = []
        for i, im in enumerate(ims):
            bg = Image.new("RGBA", im.size, (24, 26, 34, 255))
            bg.alpha_composite(im)
            strip.paste(bg, (i * px, 0))
            gif.append(bg.convert("RGB").convert("P", palette=Image.ADAPTIVE))
        strip.convert("RGB").save(os.path.join(OUT, f"{key}.png"))
        gif[0].save(os.path.join(OUT, f"{key}.gif"), save_all=True, append_images=gif[1:], loop=0,
                    duration=int(secs * 1000 / len(gif)))
        if not os.environ.get("KEEP"):
            for p in paths:
                os.remove(p)
        print(f"[anim] {key}: {len(ims)} frames over {secs:.2f}s", flush=True)
