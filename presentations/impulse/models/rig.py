# Bone rigs + looping keyframe animation for PowerPoint 3D models.
#
# PowerPoint plays only *skinned* glTF animations (no node-transform or morph-target animation),
# so every moving part of an exhibit is rigidly (or smoothly) weighted to a bone of one armature.
# The animation is authored as a function of normalised time t in [0, 1] and baked to keyframes;
# t = 0 and t = 1 give the same pose, so the scene loops seamlessly ("Repeat: until end of slide").
#
#   rig = Rig()
#   m = rig.mark(); ...build the lid...; rig.take(m, "lid", head=(0, 0.29, 0.46))
#   rig.xform(Matrix.Translation((0, 0, -0.38)))          # keep bones in sync with shift_all()/rot_all()
#   export_rigged("chest", rig, lambda t: {"lid": {"rot": [((1, 0, 0), -70 * ease(t))]}}, seconds=4)
#
# Axes, offsets and pivots are given in the model's own frame (Blender: Z up, viewer looks from -Y),
# before xform() rotations, so animation code does not care about a final tilt of the model.
import math, os
import bpy
from mathutils import Vector, Matrix, Quaternion
import make_models as mm

FPS = 24
TAU = math.tau


# ------------------------------------------------------------------ easing helpers (all periodic-safe)
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def smooth(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease(t, a, b):
    """0 before a, smooth 0->1 between a and b, 1 after b."""
    return smooth((t - a) / (b - a)) if b > a else float(t >= a)


def pulse(t, a, b, c, d):
    """0 -> 1 on [a, b], hold, 1 -> 0 on [c, d]."""
    return ease(t, a, b) * (1 - ease(t, c, d))


def back_out(x, s=1.7):
    x = clamp01(x) - 1
    return x * x * ((s + 1) * x + s) + 1


def hop(x):
    """Parabolic jump 0 -> 1 -> 0 on x in [0, 1]."""
    x = clamp01(x)
    return 4 * x * (1 - x)


def wave(t, k=1, ph=0.0):
    return math.sin(TAU * (k * t + ph))


class Rig:
    def __init__(self):
        self.bones = {"root": {"head": Vector((0, 0, 0)), "parent": None}}
        self.order = ["root"]
        self.fns = {}
        self.R = Matrix.Identity(3)

    def bone(self, name, head, parent="root"):
        assert parent in self.bones, parent
        self.bones[name] = {"head": Vector(head), "parent": parent}
        self.order.append(name)
        return name

    def mark(self):
        return set(bpy.context.scene.objects)

    def take(self, mark, bone, head=None, parent="root"):
        """Give every object created since `mark` to `bone` (created when `head` is given)."""
        if head is not None:
            self.bone(bone, head, parent)
        for o in bpy.context.scene.objects:
            if o not in mark:
                o["bone"] = bone
        return bone

    def take_objs(self, objs, bone):
        for o in objs:
            o["bone"] = bone

    def take_fn(self, mark, key, fn):
        """Smooth skinning: fn(co: Vector, model frame) -> {bone: weight}."""
        self.fns[key] = fn
        for o in bpy.context.scene.objects:
            if o not in mark:
                o["bone"] = "fn:" + key

    def xform(self, T):
        """Apply the same transform that shift_all()/rot_all() applied to the meshes."""
        T = Matrix(T)
        for b in self.bones.values():
            b["head"] = T @ b["head"]
        self.R = T.to_3x3().normalized() @ self.R
        Rinv = T.inverted()
        for key, fn in list(self.fns.items()):
            self.fns[key] = (lambda f, Ri: (lambda co: f(Ri @ co)))(fn, Rinv)

    def shift(self, dx=0, dy=0, dz=0):
        mm_shift_all(dx, dy, dz)
        self.xform(Matrix.Translation((dx, dy, dz)))

    def rotate(self, rx=0, ry=0, rz=0):
        mm.rot_all(rx, ry, rz)
        self.xform(Matrix.Rotation(math.radians(rz), 4, "Z") @ Matrix.Rotation(math.radians(ry), 4, "Y")
                   @ Matrix.Rotation(math.radians(rx), 4, "X"))


def mm_shift_all(dx, dy, dz):
    for o in bpy.context.scene.objects:
        o.location.x += dx
        o.location.y += dy
        o.location.z += dz


# ------------------------------------------------------------------ export
def _join(objs, name):
    if len(objs) == 1:
        objs[0].name = name
        return objs[0]
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    with bpy.context.temp_override(active_object=objs[0], selected_editable_objects=objs, selected_objects=objs):
        bpy.ops.object.join()
    objs[0].name = name
    return objs[0]


def _bake_geometry():
    for o in list(bpy.context.scene.objects):
        if o.type != "MESH":
            bpy.data.objects.remove(o)
    for o in bpy.context.scene.objects:
        bpy.context.view_layer.objects.active = o
        for md in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=md.name)
    mm.apply_all()


def export_rigged(key, rig, anim, seconds=4.0):
    _bake_geometry()
    # 1) one mesh per bone (fewer draw calls in PowerPoint)
    groups = {}
    for o in list(bpy.context.scene.objects):
        groups.setdefault(o.get("bone", "root"), []).append(o)
    meshes = {g: _join(objs, "m_" + g.replace(":", "_")) for g, objs in groups.items()}
    # 2) armature, every bone points +Z in rest pose (same rest orientation for all bones)
    arm_data = bpy.data.armatures.new("rig")
    arm = bpy.data.objects.new("rig", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    L = 0.08
    for name in rig.order:
        b = rig.bones[name]
        eb = arm_data.edit_bones.new(name)
        eb.head = b["head"]
        eb.tail = b["head"] + Vector((0, 0, L))
        eb.roll = 0
        if b["parent"]:
            eb.parent = arm_data.edit_bones[b["parent"]]
            eb.use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    # 3) skinning
    for g, o in meshes.items():
        if g.startswith("fn:"):
            fn = rig.fns[g[3:]]
            vgs = {}
            for v in o.data.vertices:
                w = fn(Vector(v.co))
                tot = sum(w.values()) or 1.0
                for bn, wt in w.items():
                    if wt <= 1e-4:
                        continue
                    if bn not in vgs:
                        vgs[bn] = o.vertex_groups.new(name=bn)
                    vgs[bn].add([v.index], wt / tot, "REPLACE")
        else:
            vg = o.vertex_groups.new(name=g)
            vg.add([v.index for v in o.data.vertices], 1.0, "REPLACE")
        md = o.modifiers.new("arm", "ARMATURE")
        md.object = arm
        o.parent = arm
        o.matrix_parent_inverse = Matrix.Identity(4)
    # 4) bake the animation
    sc = bpy.context.scene
    n = max(2, int(round(seconds * FPS)))
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 0, n
    Rr = arm_data.bones["root"].matrix_local.to_quaternion()  # identical rest rotation for all bones
    Rri = Rr.inverted()
    R = rig.R
    for f in range(n + 1):
        t = (f / n) % 1.0
        pose = anim(t)
        for name in rig.order:
            if name == "root":
                continue
            pb = arm.pose.bones[name]
            pb.rotation_mode = "QUATERNION"
            spec = pose.get(name, {})
            qw = Quaternion()
            for axis, deg in spec.get("rot", []):
                qw = Quaternion((R @ Vector(axis)).normalized(), math.radians(deg)) @ qw
            pb.rotation_quaternion = Rri @ qw @ Rr
            d = R @ Vector(spec.get("loc", (0, 0, 0)))
            pb.location = Rri @ d
            s = spec.get("scale", 1.0)
            if isinstance(s, (int, float)):
                pb.scale = (s, s, s)
            else:
                sx, sy, sz = s
                pb.scale = (sx, sz, sy)  # bone local axes: X = world X, Y = world Z, Z = world -Y
            for path in ("rotation_quaternion", "location", "scale"):
                pb.keyframe_insert(path, frame=f)
    # 5) export
    path = os.path.join(mm.OUT, f"{key}.glb")
    props = bpy.ops.export_scene.gltf.get_rna_type().properties.keys()
    opts = dict(filepath=path, export_format="GLB", export_apply=True, export_yup=True,
                export_draco_mesh_compression_enable=False, export_image_format="JPEG", export_image_quality=88,
                export_cameras=False, export_lights=False, export_extras=False, use_selection=False,
                export_animations=True, export_skins=True, export_force_sampling=True, export_frame_range=True,
                export_def_bones=False, export_anim_slide_to_zero=True, export_optimize_animation_size=False,
                export_animation_mode="ACTIVE_ACTIONS", export_bake_animation=False, export_reset_pose_bones=True,
                export_rest_position_armature=True, export_morph=False)
    bpy.ops.export_scene.gltf(**{k: v for k, v in opts.items() if k in props or k == "filepath"})
    tris = sum(len(p.vertices) - 2 for o in meshes.values() for p in o.data.polygons)
    print(f"[model] {key}: {os.path.getsize(path)/1024:.0f} KB, ~{tris} tris, {len(rig.order)} bones, {seconds:.1f}s loop")
