# Renders transparent PNG rasters of the .glb models with Blender Cycles.
# The camera reproduces PowerPoint's own 3D-model framing (am3d:model3d):
#   * model centred and normalised so that its largest bbox side = 1
#   * perspective camera, fov 45°, distance = |half extents| / sin(22.5°)
#   * square viewport; rotation = am3d:rot (ax, ay, az) applied in glTF space
# These PNGs are written into the pptx as the model's cached raster / fallback
# picture, and used by the HTML preview.
#
#   python3 models/render.py jobs.json          (jobs: [{id,key,rot:[ax,ay,az],px,out}])
#   python3 models/render.py --sheet key1 key2  (quick look renders into models/_look/)
import bpy, math, os, sys, json
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.environ.get("GLB_DIR") or os.path.join(HERE, "glb")
HDRI = os.path.join(bpy.utils.system_resource("DATAFILES"), "studiolights", "world", "studio.exr")


def setup_scene(px, samples):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.cycles.transparent_max_bounces = 16
    sc.render.film_transparent = True
    sc.cycles.film_transparent_glass = True
    sc.render.resolution_x = sc.render.resolution_y = px
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Punchy"
    sc.view_settings.exposure = 0.45
    # environment: studio HDRI for reflections (invisible: film is transparent)
    w = bpy.data.worlds.new("w")
    sc.world = w
    nt = w.node_tree
    bg = nt.nodes["Background"]
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(HDRI)
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.55
    return sc


def add_lights(sc, d):
    # key (warm, upper-left-front), rim (cool, behind-right), fill (soft, low-front)
    def area(name, loc, energy, color, size):
        L = bpy.data.lights.new(name, "AREA")
        L.energy = energy
        L.color = color
        L.size = size
        o = bpy.data.objects.new(name, L)
        sc.collection.objects.link(o)
        o.location = loc
        direction = -Vector(loc)
        o.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    area("key", (-1.6, -2.0, 2.2), 260, (1.0, 0.88, 0.74), 1.6)
    area("rim", (2.0, 1.8, 1.6), 300, (0.62, 0.80, 1.0), 1.0)
    area("fill", (1.4, -2.4, -0.3), 60, (0.85, 0.9, 1.0), 2.5)


def load_model(key):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(GLB, key + ".glb"))
    objs = [o for o in bpy.data.objects if o not in before]
    for o in objs:  # importer helpers (bone-shape icosphere) must neither render nor count for framing
        if any(c.name.startswith("glTF_not_exported") for c in o.users_collection):
            o.hide_render = True
    objs = [o for o in objs if not o.hide_render]
    meshes = [o for o in objs if o.type == "MESH"]
    bpy.context.view_layer.update()
    mn = Vector((1e9, 1e9, 1e9)); mx = Vector((-1e9, -1e9, -1e9))
    for o in meshes:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
    center = (mn + mx) / 2
    ext = mx - mn
    acts = [o.animation_data.action for o in objs if o.animation_data and o.animation_data.action]
    if acts:  # animated model: raster = first frame of the loop (PowerPoint's poster frame)
        bpy.context.scene.frame_set(int(acts[0].frame_range[0]))
    maxe = max(ext)
    norm = bpy.data.objects.new("norm", None)
    bpy.context.scene.collection.objects.link(norm)
    rot = bpy.data.objects.new("rot", None)
    bpy.context.scene.collection.objects.link(rot)
    norm.parent = rot
    norm.matrix_basis = Matrix.Scale(1 / maxe, 4) @ Matrix.Translation(-center)
    for o in objs:
        if o.parent is None:
            mw = o.matrix_world.copy()
            o.parent = norm
            o.matrix_parent_inverse = Matrix.Identity(4)
            o.matrix_basis = mw
    # radius as in PowerPoint: |half extents| of the normalised box
    r = (ext / maxe / 2).length
    return rot, r


def set_rot(rot, ax, ay, az):
    # glTF axes -> Blender axes: X->X, Y->Z, Z->-Y.  R = Rx(ax)·Ry(ay)·Rz(az) in glTF space
    R = (Matrix.Rotation(math.radians(ax), 4, "X") @ Matrix.Rotation(math.radians(ay), 4, "Z")
         @ Matrix.Rotation(math.radians(-az), 4, "Y"))
    rot.matrix_basis = R


def camera(sc, r):
    d = r / math.sin(math.radians(22.5))
    cam = bpy.data.cameras.new("cam")
    cam.angle = math.radians(45)
    cam.clip_start = 0.01
    o = bpy.data.objects.new("cam", cam)
    sc.collection.objects.link(o)
    o.location = (0, -d, 0)
    o.rotation_euler = (math.radians(90), 0, 0)
    sc.camera = o
    return d


def render_jobs(jobs, samples=64):
    by_key = {}
    for j in jobs:
        by_key.setdefault((j["key"], j.get("px", 900)), []).append(j)
    for (key, px), js in by_key.items():
        sc = setup_scene(px, samples)
        rot, r = load_model(key)
        d = camera(sc, r)
        add_lights(sc, d)
        for j in js:
            set_rot(rot, *j["rot"])
            sc.render.filepath = j["out"]
            bpy.ops.render.render(write_still=True)
            print("[render]", j["out"], flush=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--sheet":
        LOOK = os.environ.get("LOOK_DIR") or os.path.join(HERE, "_look")
        os.makedirs(LOOK, exist_ok=True)
        jobs = []
        for k in args[1:]:
            for i, rot in enumerate([(12, -30, 0), (8, 40, 0)]):
                jobs.append({"key": k, "rot": rot, "px": 420, "out": os.path.join(LOOK, f"{k}-{i}.png")})
        render_jobs(jobs, samples=24)
    else:
        render_jobs(json.load(open(args[0])), samples=int(os.environ.get("SAMPLES", "64")))
