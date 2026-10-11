# Quick animation check: renders 6 frames across the loop -> GIF. Blender Z up, viewer from -Y.
#   GLB_DIR=... LOOK_DIR=... python3 gifcheck.py key [key2 ...]
import os, sys
FUN = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(FUN, "..", "..", "schumpeter", "models"))
import render as R
from PIL import Image

LOOK = os.environ.get("LOOK_DIR") or "/tmp/gif"
os.makedirs(LOOK, exist_ok=True)
PX, SAMPLES, NFR = 300, 12, 6
for key in sys.argv[1:]:
    sc = R.setup_scene(PX, SAMPLES)
    rot, r = R.load_model(key)
    d = R.camera(sc, r)
    R.add_lights(sc, d)
    R.set_rot(rot, 12, -30, 0)
    acts = [o.animation_data.action for o in __import__("bpy").data.objects
            if o.animation_data and o.animation_data.action]
    f0, f1 = (int(acts[0].frame_range[0]), int(acts[0].frame_range[1])) if acts else (1, 1)
    print(f"[gif] {key}: frames {f0}..{f1}", flush=True)
    paths = []
    for i in range(NFR):
        fr = f0 + round((f1 - f0) * i / max(NFR - 1, 1))
        __import__("bpy").context.scene.frame_set(fr)
        p = os.path.join(LOOK, f"{key}-{i}.png")
        sc.render.filepath = p
        __import__("bpy").ops.render.render(write_still=True)
        paths.append(p)
    imgs = [Image.open(p).convert("RGBA") for p in paths]
    imgs[0].save(os.path.join(LOOK, f"{key}.gif"), save_all=True, append_images=imgs[1:],
                 duration=250, loop=0, disposal=2)
    print(f"[gif] {key}.gif ok", flush=True)
