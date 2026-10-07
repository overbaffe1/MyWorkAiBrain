# Procedural 3D models for the Schumpeter deck, built in Blender (bpy) and
# exported as self-contained .glb files that PowerPoint can embed as native 3D models.
#
#   python3 models/make_models.py            -> models/glb/*.glb   (all models)
#   python3 models/make_models.py gear globe -> only selected models
#
# Every model is modelled "front towards the viewer": in glTF terms +Y is up and
# the camera looks from +Z (Blender: Z up, front faces -Y).
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "glb")
os.makedirs(OUT, exist_ok=True)
TAU = math.tau


# ------------------------------------------------------------------ helpers
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


_mats = {}


def M(name):
    """Shared material palette — one coherent 'brass / ivory / navy' language."""
    if name in _mats and _mats[name].name in bpy.data.materials:
        return _mats[name]
    P = {
        # name: (base rgb, metallic, roughness, extra)
        "brass":    ((0.80, 0.56, 0.26), 0.85, 0.30, {}),
        "brass_d":  ((0.50, 0.32, 0.14), 0.85, 0.38, {}),
        "gold":     ((1.00, 0.74, 0.32), 1.00, 0.22, {}),
        "steel":    ((0.62, 0.64, 0.68), 1.00, 0.16, {}),
        "chrome":   ((0.85, 0.86, 0.88), 1.00, 0.06, {}),
        "black":    ((0.018, 0.020, 0.026), 0.20, 0.22, {"coat": 0.8}),
        "satin":    ((0.006, 0.006, 0.008), 0.05, 0.30, {"coat": 0.3}),
        "ivory":    ((0.72, 0.64, 0.50), 0.00, 0.38, {"coat": 0.4}),
        "paper":    ((0.70, 0.64, 0.52), 0.00, 0.80, {}),
        "navy":     ((0.012, 0.025, 0.075), 0.05, 0.45, {}),
        "oxblood":  ((0.180, 0.016, 0.016), 0.05, 0.42, {}),
        "green":    ((0.012, 0.070, 0.045), 0.05, 0.45, {}),
        "brown":    ((0.090, 0.036, 0.016), 0.05, 0.45, {}),
        "walnut":   ((0.110, 0.050, 0.022), 0.00, 0.40, {"coat": 0.5}),
        "teal":     ((0.015, 0.160, 0.200), 0.30, 0.30, {}),
        "red":      ((0.300, 0.025, 0.020), 0.20, 0.32, {"coat": 0.6}),
        "thread":   ((0.190, 0.010, 0.010), 0.00, 0.55, {}),
        "sand":     ((0.700, 0.460, 0.200), 0.00, 0.90, {}),
        "glass":    ((0.880, 0.930, 1.000), 0.00, 0.02, {"alpha": 0.12}),
        "glow":     ((1.000, 0.620, 0.260), 0.00, 0.50, {"emit": (1.0, 0.55, 0.18), "es": 6.0}),
        "cyan":     ((0.380, 0.830, 0.940), 0.00, 0.30, {"emit": (0.38, 0.83, 0.94), "es": 3.0}),
        "window":   ((1.000, 0.700, 0.350), 0.00, 0.30, {"emit": (1.0, 0.62, 0.28), "es": 2.5}),
        "rubber":   ((0.030, 0.030, 0.030), 0.00, 0.80, {}),
        # used by the Cantillon deck
        "canvas":   ((0.760, 0.700, 0.580), 0.00, 0.85, {"sheen": 0.3}),
        "wax":      ((0.800, 0.740, 0.610), 0.00, 0.42, {"coat": 0.3}),
        "flame":    ((1.000, 0.780, 0.400), 0.00, 0.50, {"emit": (1.0, 0.62, 0.22), "es": 14.0}),
        "crust":    ((0.250, 0.090, 0.020), 0.00, 0.55, {}),
        "flour":    ((0.780, 0.700, 0.560), 0.00, 0.90, {}),
        "water":    ((0.006, 0.030, 0.045), 0.00, 0.04, {"coat": 1.0}),
        "iron":     ((0.070, 0.068, 0.070), 0.90, 0.42, {}),
        "ember":    ((0.880, 0.420, 0.300), 0.00, 0.40, {"emit": (0.95, 0.42, 0.26), "es": 2.5}),
        "wine":     ((0.190, 0.012, 0.030), 0.05, 0.35, {"coat": 0.6}),
        "leather":  ((0.120, 0.040, 0.020), 0.00, 0.55, {"coat": 0.2}),
        "feather":  ((0.860, 0.830, 0.770), 0.00, 0.55, {"sheen": 0.6}),
        "ink":      ((0.004, 0.004, 0.010), 0.00, 0.08, {"coat": 1.0}),
        "copper":   ((0.700, 0.300, 0.150), 0.95, 0.35, {}),
        "stone":    ((0.300, 0.270, 0.240), 0.00, 0.75, {}),
        # used by the Lvov deck
        "brick":    ((0.300, 0.040, 0.028), 0.00, 0.70, {}),
        "whitestone": ((0.760, 0.730, 0.660), 0.00, 0.60, {}),
        "malachite": ((0.010, 0.150, 0.085), 0.10, 0.22, {"coat": 0.8}),
        "concrete": ((0.420, 0.405, 0.385), 0.00, 0.92, {}),
        "leaf":     ((0.050, 0.230, 0.035), 0.00, 0.45, {"sheen": 0.4, "coat": 0.3}),
        "clay":     ((0.360, 0.120, 0.050), 0.00, 0.70, {}),
        "star":     ((1.000, 0.120, 0.060), 0.10, 0.30, {"emit": (1.0, 0.10, 0.05), "es": 3.0}),
        "pcb":      ((0.008, 0.085, 0.045), 0.10, 0.30, {"coat": 0.7}),
        "silicon":  ((0.040, 0.050, 0.080), 0.60, 0.18, {}),
        "drum":     ((0.020, 0.060, 0.160), 0.55, 0.32, {"coat": 0.5}),
        "verdigris": ((0.180, 0.420, 0.330), 0.40, 0.45, {}),
        "silver":   ((0.800, 0.810, 0.830), 1.00, 0.40, {}),
        "satin_steel": ((0.780, 0.790, 0.810), 1.00, 0.30, {}),
        "gold_satin": ((1.00, 0.72, 0.30), 1.00, 0.46, {}),
        "bubble":   ((0.950, 0.970, 1.000), 0.00, 0.00, {"alpha": 0.7, "film": 380, "trans": 1.0}),
    }
    col, met, rough, ex = P[name]
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Metallic"].default_value = met
    b.inputs["Roughness"].default_value = rough
    if "coat" in ex:
        b.inputs["Coat Weight"].default_value = ex["coat"]
    if "sheen" in ex:
        b.inputs["Sheen Weight"].default_value = ex["sheen"]
    if "alpha" in ex:
        b.inputs["Alpha"].default_value = ex["alpha"]
        m.surface_render_method = "BLENDED"
        m.use_backface_culling = False
    if "trans" in ex:
        b.inputs["Transmission Weight"].default_value = ex["trans"]
        b.inputs["IOR"].default_value = 1.5
    if "film" in ex:
        try:
            b.inputs["Thin Film Thickness"].default_value = ex["film"]
            b.inputs["Thin Film IOR"].default_value = 1.33
        except KeyError:
            pass
    if "emit" in ex:
        b.inputs["Emission Color"].default_value = (*ex["emit"], 1)
        b.inputs["Emission Strength"].default_value = ex["es"]
    _mats[name] = m
    return m


def link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def finish(obj, mat=None, smooth=30, bevel=0.0, seg=2):
    if mat is not None:
        obj.data.materials.clear()
        obj.data.materials.append(M(mat) if isinstance(mat, str) else mat)
    if bevel:
        md = obj.modifiers.new("bevel", "BEVEL")
        md.width = bevel
        md.segments = seg
        md.limit_method = "ANGLE"
        md.angle_limit = math.radians(40)
        md.harden_normals = False
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
        if bevel:
            md = obj.modifiers.new("smooth", "NODES") if False else None
        obj.data.set_sharp_from_angle(angle=math.radians(smooth))
    return obj


def mesh_obj(name, verts, faces):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    return link(bpy.data.objects.new(name, me))


def lathe(name, prof, mat, seg=72, smooth=35, loc=(0, 0, 0)):
    """Revolve a (r, z) profile around the Z axis."""
    verts, faces, rings = [], [], []
    for r, z in prof:
        if r < 1e-6:
            rings.append([len(verts)])
            verts.append((0, 0, z))
        else:
            ring = []
            for i in range(seg):
                a = TAU * i / seg
                ring.append(len(verts))
                verts.append((r * math.cos(a), r * math.sin(a), z))
            rings.append(ring)
    for A, B in zip(rings, rings[1:]):
        if len(A) == 1 and len(B) == 1:
            continue
        if len(A) == 1:
            for i in range(seg):
                faces.append((A[0], B[i], B[(i + 1) % seg]))
        elif len(B) == 1:
            for i in range(seg):
                faces.append((A[i], B[0], A[(i + 1) % seg]))
        else:
            for i in range(seg):
                faces.append((A[i], B[i], B[(i + 1) % seg], A[(i + 1) % seg]))
    o = mesh_obj(name, verts, faces)
    # make normals point outwards
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free()
    o.location = loc
    return finish(o, mat, smooth)


def box(name, size, loc, mat, bevel=0.01, rot=(0, 0, 0), seg=2):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, mat, 30, bevel, seg)


def cyl(name, r, h, loc, mat, rot=(0, 0, 0), seg=48, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    return finish(o, mat, 35, bevel)


def sphere(name, r, loc, mat, seg=48, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=r, location=loc)
    o = bpy.context.active_object
    o.name = name
    return finish(o, mat, 80)


def torus(name, R, r, loc, mat, rot=(0, 0, 0), seg=72, mseg=16):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=seg, minor_segments=mseg,
                                     location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    return finish(o, mat, 80)


def tube(name, pts, r, mat, res=6, smooth_curve=True):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = res
    cu.use_fill_caps = True
    if smooth_curve:
        sp = cu.splines.new("NURBS")
        sp.points.add(len(pts) - 1)
        for p, c in zip(sp.points, pts):
            p.co = (*c, 1)
        sp.use_endpoint_u = True
        sp.order_u = min(4, len(pts))
        sp.resolution_u = max(2, min(12, 48 // len(pts)))
    else:
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for p, c in zip(sp.points, pts):
            p.co = (*c, 1)
    o = link(bpy.data.objects.new(name, cu))
    return to_mesh(o, mat)


def to_mesh(o, mat=None, smooth=40):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.convert(target="MESH")
    o = bpy.context.active_object
    return finish(o, mat, smooth)


def profile2d(name, loops, depth, bevel, mat, bevel_res=3):
    """Extrude closed 2D polygons (XY plane, holes allowed) along Z with rounded edges."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "2D"
    cu.fill_mode = "BOTH"
    cu.extrude = depth
    cu.bevel_depth = bevel
    cu.bevel_resolution = bevel_res
    for loop in loops:
        sp = cu.splines.new("POLY")
        sp.points.add(len(loop) - 1)
        for p, (x, y) in zip(sp.points, loop):
            p.co = (x, y, 0, 1)
        sp.use_cyclic_u = True
    o = link(bpy.data.objects.new(name, cu))
    return to_mesh(o, mat, 35)


def apply_all():
    for o in bpy.context.scene.objects:
        o.select_set(o.type == "MESH")
    bpy.context.view_layer.objects.active = next(o for o in bpy.context.scene.objects if o.type == "MESH")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def export(key):
    # bake modifiers, drop non-mesh helpers, then write a compact GLB (no Draco: PowerPoint can't read it)
    for o in list(bpy.context.scene.objects):
        if o.type != "MESH":
            bpy.data.objects.remove(o)
    for o in bpy.context.scene.objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = bpy.context.scene.objects[0]
    for o in bpy.context.scene.objects:
        bpy.context.view_layer.objects.active = o
        for md in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=md.name)
    apply_all()
    path = os.path.join(OUT, f"{key}.glb")
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", export_apply=True, export_yup=True,
        export_draco_mesh_compression_enable=False, export_image_format="JPEG", export_image_quality=88,
        export_cameras=False, export_lights=False, export_extras=False, use_selection=False,
    )
    tris = sum(len(p.vertices) - 2 for o in bpy.context.scene.objects for p in o.data.polygons)
    print(f"[model] {key}: {os.path.getsize(path)/1024:.0f} KB, ~{tris} tris")


def rot_all(rx=0, ry=0, rz=0):
    """Rotate the whole assembled model around the origin (Blender axes, degrees)."""
    R = (Matrix.Rotation(math.radians(rz), 4, "Z") @ Matrix.Rotation(math.radians(ry), 4, "Y")
         @ Matrix.Rotation(math.radians(rx), 4, "X"))
    for o in bpy.context.scene.objects:
        o.matrix_world = R @ o.matrix_world


# ------------------------------------------------------------------ models
def gear_outline(n, r_tip, r_root):
    pts = []
    p = TAU / n
    for i in range(n):
        a0 = i * p
        for f, r in [(0.00, r_root), (0.12, r_root), (0.25, r_tip), (0.33, r_tip * 1.004),
                     (0.42, r_tip), (0.55, r_root), (0.70, r_root), (0.85, r_root)]:
            a = a0 + f * p
            pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def spoke_holes(nsp, r_in, r_out, sw):
    holes = []
    for k in range(nsp):
        a0 = TAU * k / nsp + math.asin(sw / r_out)
        a1 = TAU * (k + 1) / nsp - math.asin(sw / r_out)
        b0 = TAU * k / nsp + math.asin(min(0.99, sw / r_in))
        b1 = TAU * (k + 1) / nsp - math.asin(min(0.99, sw / r_in))
        loop = []
        for i in range(17):
            a = a0 + (a1 - a0) * i / 16
            loop.append((r_out * math.cos(a), r_out * math.sin(a)))
        for i in range(9):
            a = b1 + (b0 - b1) * i / 8
            loop.append((r_in * math.cos(a), r_in * math.sin(a)))
        holes.append(loop)
    return holes


def build_gear(teeth=20, r_tip=1.0, depth=0.075, nsp=5, mat="brass", hub_mat="brass_d", y=0.0, rivets=True):
    outer = gear_outline(teeth, r_tip, r_tip * 0.87)
    holes = spoke_holes(nsp, r_tip * 0.30, r_tip * 0.68, r_tip * 0.07)
    g = profile2d("gear", [outer] + holes, depth, 0.018 * r_tip, mat)
    parts = [g]
    hub = lathe("hub", [(0, depth + 0.13), (0.10 * r_tip, depth + 0.13), (0.16 * r_tip, depth + 0.11),
                        (0.20 * r_tip, depth + 0.06), (0.21 * r_tip, 0), (0.20 * r_tip, -depth - 0.06),
                        (0.16 * r_tip, -depth - 0.11), (0.10 * r_tip, -depth - 0.13), (0, -depth - 0.13)], hub_mat, 64)
    parts.append(hub)
    axle = lathe("axle", [(0, depth + 0.16), (0.055 * r_tip, depth + 0.16), (0.065 * r_tip, depth + 0.14),
                          (0.065 * r_tip, -depth - 0.14), (0.055 * r_tip, -depth - 0.16), (0, -depth - 0.16)], "steel", 40)
    parts.append(axle)
    rim = torus("rimring", r_tip * 0.775, 0.012 * r_tip, (0, 0, depth + 0.012), hub_mat, mseg=10)
    parts.append(rim)
    if rivets:
        for k in range(nsp * 2):
            a = TAU * (k + 0.5) / (nsp * 2)
            s = sphere("rivet", 0.028 * r_tip, (r_tip * 0.775 * math.cos(a), r_tip * 0.775 * math.sin(a), depth + 0.02),
                       "brass_d", 16, 8)
            s.scale.z = 0.55
            parts.append(s)
    for o in parts:
        o.location.z += 0
    return parts


def m_gear_s():
    # light version for the small gear that rolls along the progress track
    outer = gear_outline(20, 1.0, 0.87)
    holes = spoke_holes(5, 0.30, 0.68, 0.07)
    profile2d("gear", [outer] + holes, 0.075, 0.018, "brass", bevel_res=1)
    lathe("hub", [(0, 0.2), (0.16, 0.2), (0.21, 0.12), (0.21, -0.12), (0.16, -0.2), (0, -0.2)], "brass_d", 32)
    rot_all(rx=90)


def m_gear():
    build_gear()
    # face the viewer: gear plane XY -> XZ (front = -Y)
    rot_all(rx=90)


def m_spool():
    # turned wooden spool with deep-red wool thread (father's cloth factory)
    lathe("flange_bottom", [(0, -0.50), (0.40, -0.50), (0.45, -0.485), (0.47, -0.45), (0.47, -0.42), (0.45, -0.40),
                            (0.33, -0.385), (0.27, -0.37), (0.27, -0.33), (0.08, -0.33), (0.08, -0.52), (0, -0.52)], "walnut", 80)
    lathe("flange_top", [(0, 0.52), (0.08, 0.52), (0.08, 0.33), (0.27, 0.33), (0.27, 0.37), (0.33, 0.385), (0.45, 0.40),
                         (0.47, 0.42), (0.47, 0.45), (0.45, 0.485), (0.40, 0.50), (0, 0.50)], "walnut", 80)
    lathe("core", [(0.08, -0.4), (0.23, -0.4), (0.23, 0.4), (0.08, 0.4)], "walnut", 48)
    prof = []
    N = 90
    for i in range(N + 1):
        z = -0.375 + 0.75 * i / N
        prof.append((0.355 + 0.0045 * math.cos(i * math.pi) - 0.02 * (abs(z) / 0.375) ** 6, z))
    prof = [(0.24, -0.375)] + prof + [(0.24, 0.375)]
    lathe("thread", prof, "thread", 64, 60)
    # loose end of the thread falling down
    pts = [(0.0, -0.36, 0.20), (0.08, -0.43, 0.10), (0.20, -0.50, -0.15), (0.34, -0.55, -0.42), (0.52, -0.56, -0.55),
           (0.78, -0.48, -0.58), (0.98, -0.30, -0.57)]
    tube("strand", pts, 0.011, "thread", 4)
    # brass maker's ring on the top flange
    torus("ring", 0.37, 0.012, (0, 0, 0.505), "brass", mseg=10)
    rot_all(rz=-20)


def book(name, w, d, t, cover, loc, rz=0, bands=2, band_mat="gold"):
    """Hardcover book lying flat. w = spine length (X), d = page depth (Y), t = thickness."""
    objs = []
    bt = 0.022
    objs.append(box(name + "_pages", (w - 0.035, d - 0.03, t - 2 * bt), (0, 0.012, 0), "paper", 0.004))
    objs.append(box(name + "_top", (w, d, bt), (0, 0, t / 2 - bt / 2), cover, 0.008))
    objs.append(box(name + "_bot", (w, d, bt), (0, 0, -t / 2 + bt / 2), cover, 0.008))
    sp = cyl(name + "_spine", t / 2, w, (0, -d / 2 + 0.004, 0), cover, rot=(0, math.radians(90), 0), seg=32)
    sp.scale = (1, 0.55, 1)
    objs.append(sp)
    for k in range(bands):
        x = -w / 2 + w * (k + 1) / (bands + 1)
        b = torus(name + "_band", t / 2 + 0.002, 0.007, (x, -d / 2 + 0.004, 0), band_mat,
                  rot=(0, math.radians(90), 0), seg=32, mseg=6)
        b.scale = (1, 0.56, 1)
        objs.append(b)
    for o in objs:
        o.matrix_world = Matrix.Translation(loc) @ Matrix.Rotation(math.radians(rz), 4, "Z") @ o.matrix_world
    return objs


def m_books():
    # the four key works (1911/12 · 1939 · 1942 · 1954) — the last one is the fat posthumous History
    z = 0
    specs = [(1.30, 0.92, 0.30, "brown", 4, 3), (1.12, 0.80, 0.17, "navy", -3, 2),
             (1.05, 0.76, 0.15, "oxblood", 6, 2), (0.98, 0.70, 0.13, "green", -7, 2)]
    for i, (w, d, t, c, rz, bands) in enumerate(specs):
        book(f"b{i}", w, d, t, c, Vector((0.02 * i, 0.01 * i, z + t / 2)), rz, bands)
        z += t
    # ribbon bookmark hanging out of the top book
    tube("ribbon", [(0.20, -0.30, z - 0.06), (0.24, -0.38, z - 0.10), (0.27, -0.42, z - 0.22), (0.28, -0.42, z - 0.34)],
         0.012, "oxblood", 2)
    for o in bpy.context.scene.objects:
        o.location.z -= z / 2
    rot_all(rz=-8)


def m_edu():
    book("e0", 1.15, 0.82, 0.20, "oxblood", Vector((0, 0, 0.10)), 0, 2)
    book("e1", 1.00, 0.74, 0.16, "navy", Vector((0.03, 0.02, 0.28)), 9, 2)
    zc = 0.36
    lathe("cap", [(0, zc), (0.27, zc), (0.29, zc + 0.01), (0.30, zc + 0.12), (0.285, zc + 0.20), (0, zc + 0.205)], "satin", 64)
    board = box("board", (0.86, 0.86, 0.026), (0, 0, zc + 0.215), "satin", 0.006, rot=(0, 0, math.radians(38)))
    sphere("button", 0.035, (0, 0, zc + 0.235), "gold", 24, 12).scale.z = 0.5
    # tassel cord over the edge
    a = math.radians(38 + 45)
    edge = (0.86 / 2 * math.sqrt(2)) * 0.98
    ex, ey = edge * math.cos(a), edge * math.sin(a)
    tube("cord", [(0, 0, zc + 0.24), (ex * 0.5, ey * 0.5, zc + 0.245), (ex * 0.92, ey * 0.92, zc + 0.24),
                  (ex * 1.0, ey * 1.0, zc + 0.20), (ex * 1.02, ey * 1.02, zc + 0.05)], 0.008, "gold", 4)
    lathe("tassel", [(0, zc + 0.06), (0.025, zc + 0.055), (0.03, zc + 0.02), (0.05, zc - 0.12), (0, zc - 0.125)], "gold", 24,
          loc=(ex * 1.02, ey * 1.02, 0))
    for o in bpy.context.scene.objects:
        o.location.z -= 0.30
    rot_all(rz=-15)


def m_tophat():
    prof = [(0, 0.80), (0.33, 0.80), (0.355, 0.79), (0.37, 0.77), (0.375, 0.74), (0.36, 0.40), (0.35, 0.10),
            (0.36, 0.06), (0.52, 0.045), (0.60, 0.07), (0.62, 0.095), (0.63, 0.085), (0.62, 0.05), (0.56, 0.02),
            (0.40, 0.012), (0.33, 0.02), (0.30, 0.03), (0.30, 0.76), (0, 0.76)]
    # build crown + brim as one turned silk shell
    lathe("hat", [(0, 0.80), (0.33, 0.80), (0.355, 0.792), (0.372, 0.772), (0.378, 0.745), (0.362, 0.40),
                  (0.352, 0.10), (0.36, 0.062), (0.50, 0.050), (0.585, 0.068), (0.615, 0.096), (0.632, 0.090),
                  (0.625, 0.058), (0.565, 0.026), (0.42, 0.014), (0.34, 0.03), (0.32, 0.05), (0.32, 0.74), (0, 0.74)],
          "satin", 96, 40)
    lathe("band", [(0.352, 0.10), (0.3585, 0.10), (0.3595, 0.105), (0.3575, 0.235), (0.356, 0.24), (0.350, 0.24)],
          "oxblood", 96, 50)
    box("buckle", (0.06, 0.02, 0.09), (0.20, -0.30, 0.17), "brass", 0.006, rot=(0, 0, math.radians(-34)))
    for o in bpy.context.scene.objects:
        o.location.z -= 0.45
    rot_all(rx=0, rz=0)


def wheel(name, r, x, y, z, mat="red", spokes=12, w=0.06):
    objs = []
    objs.append(torus(name + "_tyre", r - 0.015, 0.02, (0, 0, 0), "steel", seg=40, mseg=8))
    objs.append(torus(name + "_rim", r - 0.045, 0.018, (0, 0, 0), mat, seg=40, mseg=8))
    for k in range(spokes):
        a = TAU * k / spokes
        objs.append(box(name + "_sp", (r - 0.07, 0.022, 0.026), ((r - 0.05) / 2 * math.cos(a), (r - 0.05) / 2 * math.sin(a), 0.0),
                        mat, 0, rot=(0, 0, a)))
    objs.append(cyl(name + "_hub", r * 0.22, w + 0.03, (0, 0, 0), "brass", seg=32, bevel=0.006))
    objs.append(cyl(name + "_pin", 0.022, w + 0.07, (r * 0.5, 0, 0), "steel", seg=16))
    side = 1 if y > 0 else -1
    T = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(90 * side), 4, "X")
    for o in objs:
        o.matrix_world = T @ o.matrix_world
    return objs


def m_locomotive():
    # stylised 19th-century steam locomotive — "add mail-coaches, you'll never get a railway"
    zb = 0.80
    box("frame", (2.10, 0.46, 0.10), (0.05, 0, 0.42), "red", 0.012)
    box("footplate", (2.0, 0.78, 0.035), (0.10, 0, 0.53), "black", 0.006)
    cyl("boiler", 0.31, 1.25, (0.30, 0, zb), "black", rot=(0, math.radians(90), 0), seg=72)
    for x in (-0.20, 0.25, 0.70):
        torus("band", 0.312, 0.012, (x, 0, zb), "brass", rot=(0, math.radians(90), 0), seg=72, mseg=8)
    cyl("smokebox", 0.33, 0.24, (1.03, 0, zb), "black", rot=(0, math.radians(90), 0), seg=72, bevel=0.01)
    cyl("door", 0.27, 0.04, (1.165, 0, zb), "black", rot=(0, math.radians(90), 0), seg=64, bevel=0.012)
    torus("doorring", 0.27, 0.014, (1.185, 0, zb), "brass", rot=(0, math.radians(90), 0), seg=64, mseg=8)
    sphere("doorknob", 0.035, (1.20, 0, zb), "brass", 24, 12)
    lathe("chimney", [(0, 1.0), (0.085, 1.0), (0.085, 1.30), (0.10, 1.36), (0.135, 1.45), (0.14, 1.49), (0.125, 1.50),
                      (0.10, 1.47), (0.0, 1.47)], "black", 48, loc=(1.03, 0, 0))
    torus("chimring", 0.137, 0.012, (1.03, 0, 1.485), "brass", seg=48, mseg=8)
    lathe("dome", [(0, zb + 0.24), (0.12, zb + 0.24), (0.12, zb + 0.36), (0.11, zb + 0.42), (0.07, zb + 0.46),
                   (0, zb + 0.47)], "brass", 48, loc=(0.40, 0, 0))
    lathe("whistle", [(0, zb + 0.28), (0.03, zb + 0.28), (0.03, zb + 0.40), (0.04, zb + 0.42), (0.04, zb + 0.46), (0, zb + 0.47)],
          "brass", 24, loc=(-0.12, 0, 0))
    # cab with warm light inside
    box("cab", (0.62, 0.72, 0.80), (-0.62, 0, 0.94), "red", 0.02)
    box("roof", (0.76, 0.86, 0.05), (-0.62, 0, 1.37), "black", 0.02)
    for y in (-0.362, 0.362):
        box("win", (0.26, 0.012, 0.22), (-0.60, y, 1.12), "window", 0.004)
        box("winframe", (0.30, 0.008, 0.26), (-0.60, y * 1.005, 1.12), "brass", 0.004)
    box("frontwin", (0.012, 0.18, 0.16), (-0.305, 0.20, 1.14), "window", 0.003)
    box("frontwin2", (0.012, 0.18, 0.16), (-0.305, -0.20, 1.14), "window", 0.003)
    box("cabstripe", (0.63, 0.73, 0.03), (-0.62, 0, 0.62), "brass", 0.004)
    # drive wheels
    for x in (-0.55, -0.05, 0.45):
        for y in (-0.30, 0.30):
            wheel("dw", 0.30, x, y, 0.30)
    for x in (0.98,):
        for y in (-0.27, 0.27):
            wheel("lw", 0.16, x, y, 0.16, spokes=8, w=0.05)
    for y in (-0.36, 0.36):
        box("rod", (1.06, 0.02, 0.045), (-0.05 + 0.15, y * 1.02, 0.30), "steel", 0.006)
        cyl("piston", 0.10, 0.36, (0.80, y * 0.95, 0.42), "black", rot=(0, math.radians(90), 0), seg=32, bevel=0.01)
        torus("pistring", 0.1, 0.01, (0.98, y * 0.95, 0.42), "brass", rot=(0, math.radians(90), 0), seg=32, mseg=6)
    # cow-catcher
    v = [(1.15, -0.40, 0.48), (1.15, 0.40, 0.48), (1.15, -0.40, 0.44), (1.15, 0.40, 0.44),
         (1.45, -0.05, 0.06), (1.45, 0.05, 0.06), (1.15, -0.40, 0.06), (1.15, 0.40, 0.06)]
    for k in range(7):
        yy = -0.36 + k * 0.12
        tube("slat", [(1.17, yy, 0.47), (1.43 - abs(yy) * 0.55, yy * 0.25, 0.06)], 0.014, "red", 3, False)
    box("buffer", (0.08, 0.86, 0.12), (1.17, 0, 0.47), "red", 0.012)
    for y in (-0.30, 0.30):
        bh = lathe("bufferhead", [(0, 0), (0.05, 0), (0.05, 0.02), (0.035, 0.03), (0.03, 0.08), (0, 0.08)], "steel", 24)
        bh.matrix_world = Matrix.Translation((1.29, y, 0.47)) @ Matrix.Rotation(math.radians(-90), 4, "Y")
    # headlamp
    box("lamp", (0.14, 0.14, 0.15), (1.06, 0, zb + 0.40), "black", 0.015)
    cyl("lens", 0.05, 0.02, (1.135, 0, zb + 0.40), "glow", rot=(0, math.radians(90), 0), seg=32)
    for o in bpy.context.scene.objects:
        o.location.x -= 0.25
        o.location.z -= 0.75
    rot_all(rz=0)


def m_cube():
    # 3x3x3 combination puzzle with the top layer caught mid-turn: "new combinations"
    random.seed(7)
    pal = ["brass", "ivory", "navy", "brass", "oxblood", "ivory", "teal", "navy"]
    s, g = 0.30, 0.018
    for i in range(3):
        for j in range(3):
            for k in range(3):
                c = box("cubie", (s, s, s), ((i - 1) * (s + g), (j - 1) * (s + g), (k - 1) * (s + g)),
                        random.choice(pal), 0.035, seg=3)
                if k == 2:
                    c.matrix_world = Matrix.Rotation(math.radians(24), 4, "Z") @ c.matrix_world
    rot_all(rz=0)


def m_king():
    prof = [(0, 0), (0.30, 0), (0.31, 0.01), (0.31, 0.05), (0.29, 0.07), (0.30, 0.09), (0.27, 0.12), (0.22, 0.14),
            (0.20, 0.17), (0.21, 0.19), (0.17, 0.22), (0.13, 0.40), (0.105, 0.62), (0.10, 0.70), (0.14, 0.72),
            (0.17, 0.74), (0.15, 0.76), (0.12, 0.78), (0.15, 0.82), (0.19, 0.96), (0.20, 0.98), (0.16, 1.00),
            (0.10, 1.02), (0.06, 1.04), (0, 1.045)]
    lathe("king", prof, "black", 96, 40)
    torus("collar", 0.152, 0.018, (0, 0, 0.74), "gold", seg=64, mseg=10)
    torus("baser", 0.205, 0.014, (0, 0, 0.185), "gold", seg=64, mseg=10)
    box("cross_v", (0.05, 0.05, 0.22), (0, 0, 1.15), "gold", 0.012)
    box("cross_h", (0.16, 0.05, 0.05), (0, 0, 1.18), "gold", 0.012)
    sphere("orb", 0.05, (0, 0, 1.05), "gold", 32, 16)
    # a fallen ivory pawn: the old order knocked over
    pawn = [(0, 0), (0.17, 0), (0.175, 0.03), (0.16, 0.05), (0.12, 0.07), (0.10, 0.10), (0.08, 0.25), (0.11, 0.27),
            (0.08, 0.29), (0.0, 0.29)]
    p = lathe("pawn", pawn, "ivory", 64, 40)
    h = sphere("pawnhead", 0.085, (0, 0, 0.35), "ivory", 32, 16)
    T = Matrix.Translation((0.48, -0.22, 0.09)) @ Matrix.Rotation(math.radians(-88), 4, "Y") @ Matrix.Rotation(math.radians(25), 4, "X")
    for o in (p, h):
        o.matrix_world = T @ o.matrix_world
    for o in bpy.context.scene.objects:
        o.location.z -= 0.6
    rot_all(rz=0)


def coin(name, loc, rot=(0, 0, 0), r=0.32, t=0.05):
    h = t / 2
    prof = [(0, -h + 0.008), (r * 0.80, -h + 0.008), (r * 0.82, -h), (r * 0.97, -h), (r, -h + 0.008), (r, h - 0.008),
            (r * 0.97, h), (r * 0.82, h), (r * 0.80, h - 0.008), (r * 0.62, h - 0.008), (r * 0.60, h - 0.004),
            (r * 0.40, h - 0.004), (r * 0.38, h - 0.008), (0, h - 0.002)]
    o = lathe(name, prof, "gold", 56, 30)
    o.matrix_world = Matrix.Translation(loc) @ Matrix.Rotation(rot[2], 4, "Z") @ Matrix.Rotation(rot[1], 4, "Y") @ Matrix.Rotation(rot[0], 4, "X")
    return o


def m_coins():
    random.seed(3)
    t = 0.052
    for i in range(8):
        coin("c", (random.uniform(-0.03, 0.03), random.uniform(-0.03, 0.03), t / 2 + i * t), (0, 0, random.uniform(0, 6)), t=t)
    for i in range(4):
        coin("c2", (0.55 + random.uniform(-0.03, 0.03), 0.15 + random.uniform(-0.03, 0.03), t / 2 + i * t), (0, 0, random.uniform(0, 6)), t=t)
    coin("lean", (-0.42, -0.10, 0.31), (math.radians(90), math.radians(-14), math.radians(-25)), t=t)
    coin("flat", (0.30, -0.45, t / 2), (0, 0, 1.0), t=t)
    for o in bpy.context.scene.objects:
        o.location.x -= 0.1
        o.location.z -= 0.25
    rot_all(rz=0)


def m_hourglass():
    H = 0.60
    for z, s in ((-H - 0.06, 1), (H + 0.06, -1)):
        lathe("plate", [(0, z - 0.05 * s), (0.42, z - 0.05 * s), (0.44, z - 0.03 * s), (0.44, z + 0.03 * s), (0.42, z + 0.05 * s), (0, z + 0.05 * s)],
              "walnut", 72)
        torus("platering", 0.44, 0.012, (0, 0, z), "brass", seg=72, mseg=8)
    for k in range(3):
        a = TAU * k / 3 + 0.4
        prof = [(0.03, -H), (0.045, -H + 0.04), (0.03, -H + 0.10), (0.035, -0.2), (0.05, 0), (0.035, 0.2), (0.03, H - 0.10),
                (0.045, H - 0.04), (0.03, H)]
        prof = [(0, -H)] + prof + [(0, H)]
        lathe("post", prof, "brass", 24, 40, loc=(0.36 * math.cos(a), 0.36 * math.sin(a), 0))
    # glass
    gp = []
    N = 48
    for i in range(N + 1):
        z = -H + 2 * H * i / N
        u = abs(z) / H
        r = 0.035 + 0.26 * math.sin(min(1, u) * math.pi * 0.62) ** 1.3
        if u > 0.93:
            r = 0.24 + (1 - u) * 0.3
        gp.append((r, z))
    lathe("glass", gp, "glass", 64, 60)
    # sand: the top chamber empties, the bottom one fills
    lathe("sand_top", [(0, 0.06), (0.05, 0.08), (0.16, 0.22), (0.19, 0.28), (0, 0.28)], "sand", 48, 60)
    lathe("sand_bottom", [(0, -H + 0.02), (0.235, -H + 0.02), (0.245, -0.40), (0.15, -0.33), (0.04, -0.27), (0, -0.26)], "sand", 48, 60)
    cyl("stream", 0.008, 0.36, (0, 0, -0.10), "sand", seg=8)
    rot_all(rz=0)


def m_cradle():
    # Newton's cradle — the rhythm of booms and busts
    box("base", (1.55, 0.70, 0.08), (0, 0, 0.04), "black", 0.02)
    box("baseplate", (1.45, 0.60, 0.012), (0, 0, 0.085), "brass_d", 0.004)
    top = 0.95
    for y in (-0.27, 0.27):
        tube("frame", [(-0.65, y, 0.09), (-0.65, y, top - 0.08), (-0.62, y, top - 0.02), (-0.55, y, top),
                       (0.55, y, top), (0.62, y, top - 0.02), (0.65, y, top - 0.08), (0.65, y, 0.09)], 0.022, "brass", 6, False)
    r = 0.105
    zb = 0.30
    for i in range(5):
        x = (i - 2) * 2 * r * 1.005
        ang = math.radians(38) if i == 0 else 0
        piv = Vector((x, 0, top))
        L = top - zb
        c = Vector((x - L * math.sin(ang), 0, top - L * math.cos(ang)))
        sphere("ball", r, c, "chrome", 48, 24)
        hook = c + Vector((r * 0.9 * math.sin(ang), 0, r * 0.9 * math.cos(ang)))
        for y in (-0.265, 0.265):
            tube("string", [tuple(hook), (x, y, top)], 0.0035, "steel", 2, False)
        torus("hookring", 0.016, 0.004, tuple(hook), "steel", rot=(math.radians(90), 0, 0), seg=16, mseg=6)
    for o in bpy.context.scene.objects:
        o.location.z -= 0.48
    rot_all(rz=0)


def m_bulb():
    prof = []
    N = 50
    for i in range(N + 1):
        t = i / N
        z = -0.10 + 1.0 * t
        if t < 0.15:
            r = 0.16 + (t / 0.15) * 0.04
        else:
            u = (t - 0.15) / 0.85
            r = 0.20 + 0.20 * math.sin(u * math.pi) ** 0.9 * (1 - 0.15 * u) + 0.05 * u
            if u > 0.75:
                r *= math.sqrt(max(0, 1 - ((u - 0.75) / 0.25) ** 2)) * 0.97 + 0.03 * (1 - u) * 4
        prof.append((max(r, 0.0), z))
    prof[-1] = (0, prof[-1][1])
    lathe("bulb", prof, "glass", 72, 60)
    # screw base
    sp = [(0, -0.45), (0.06, -0.45), (0.09, -0.43)]
    for i in range(41):
        z = -0.41 + 0.30 * i / 40
        sp.append((0.155 + 0.012 * math.sin(i * math.pi / 2.5), z))
    sp += [(0.17, -0.10), (0.16, -0.08)]
    lathe("base", sp, "brass", 72, 50)
    lathe("insulator", [(0, -0.47), (0.065, -0.47), (0.07, -0.445), (0, -0.44)], "black", 32)
    # glass stem + filament
    lathe("stem", [(0.0, -0.08), (0.07, -0.08), (0.045, 0.05), (0.03, 0.30), (0, 0.31)], "glass", 32)
    for x in (-0.10, 0.10):
        tube("lead", [(x * 0.3, 0, 0.0), (x * 0.7, 0, 0.25), (x, 0, 0.48)], 0.005, "steel", 2)
    pts = []
    for i in range(41):
        t = i / 40
        x = -0.10 + 0.20 * t
        pts.append((x, 0.025 * math.sin(t * math.pi * 10), 0.48 + 0.06 * math.sin(t * math.pi)))
    tube("filament", pts, 0.008, "glow", 2)
    for o in bpy.context.scene.objects:
        o.location.z -= 0.2
    rot_all(rz=0)


def m_globe(cities=None, edges=None, arc_mat="cyan", pin_mat="ivory", spin=-80, arc_r=0.009, pin_r=0.022):
    import numpy as np
    from global_land_mask import globe as gl
    # equirectangular texture: navy ocean, brass continents, fine graticule
    W, Hh = 1024, 512
    lats = np.linspace(89.9, -89.9, Hh)
    lons = np.linspace(-180, 179.9, W)
    LON, LAT = np.meshgrid(lons, lats)
    land = gl.is_land(LAT, LON)
    img = np.zeros((Hh, W, 4), dtype=np.float32)
    ocean = np.array([0.035, 0.065, 0.14, 1])
    landc = np.array([0.72, 0.52, 0.25, 1])
    img[:] = ocean
    img[land] = landc
    grid = (np.abs(((LAT + 90) % 15) - 7.5) > 7.32) | (np.abs(((LON + 180) % 15) - 7.5) > 7.38)
    img[grid & ~land] = ocean * 0.4 + np.array([0.72, 0.52, 0.25, 1]) * 0.35
    img[..., 3] = 1
    im = bpy.data.images.new("earth", W, Hh, alpha=False)
    im.pixels = img[::-1].ravel().tolist()
    im.filepath_raw = os.path.join(OUT, "_earth.png")
    im.file_format = "PNG"
    im.save()
    m = bpy.data.materials.new("earth")
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = im
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = 0.35
    b.inputs["Roughness"].default_value = 0.38
    R = 0.5
    bpy.ops.mesh.primitive_uv_sphere_add(segments=72, ring_count=36, radius=R)
    s = bpy.context.active_object
    s.name = "earth"
    finish(s, m, 80)

    def ll(lat, lon, rr=R):
        # Blender UV sphere: u=0 at +X going counter-clockwise; texture u=0 is lon -180
        la, lo = math.radians(lat), math.radians(lon + 180)
        return Vector((rr * math.cos(la) * math.cos(lo), rr * math.cos(la) * math.sin(lo), rr * math.sin(la)))

    if cities is None:
        cities = {"vienna": (48.2, 16.4), "cairo": (30.0, 31.2), "czernowitz": (48.3, 25.9),
                  "bonn": (50.7, 7.1), "cambridge": (42.4, -71.1)}
        route = ["vienna", "cairo", "czernowitz", "bonn", "cambridge"]
        edges = list(zip(route, route[1:]))
    for k, (la, lo) in cities.items():
        p = ll(la, lo, R * 1.01)
        sphere("pin_" + k, pin_r, tuple(p), pin_mat, 16, 8)
    for a, b2 in edges:
        A, B = ll(*cities[a]), ll(*cities[b2])
        pts = []
        ang = A.angle(B)
        for i in range(25):
            t = i / 24
            P = A.slerp(B, t) if hasattr(A, "slerp") else (A * (1 - t) + B * t)
            P = P.normalized() * (R * (1.012 + 0.10 * math.sin(math.pi * t) * min(1.0, ang * 1.4)))
            pts.append(tuple(P))
        tube("arc", pts, arc_r, arc_mat, 3)
    # spin so Europe/Atlantic face the viewer (-Y), then tilt the axis
    for o in bpy.context.scene.objects:
        o.matrix_world = Matrix.Rotation(math.radians(spin), 4, "Z") @ o.matrix_world
    for o in bpy.context.scene.objects:
        o.matrix_world = Matrix.Rotation(math.radians(-18), 4, "X") @ o.matrix_world
        o.matrix_world = Matrix.Rotation(math.radians(23.4), 4, "Y") @ o.matrix_world
        o.matrix_world = Matrix.Translation((0, 0, 0.72)) @ o.matrix_world
    # meridian half ring + stand
    ax = Matrix.Translation((0, 0, 0.72)) @ Matrix.Rotation(math.radians(23.4), 4, "Y")
    ring = []
    for i in range(49):
        a = math.radians(-100 + 200 * i / 48)
        ring.append(tuple(ax @ Vector((0.56 * math.sin(a) * 0 + 0.56 * math.cos(math.radians(90)) , 0, 0)) ) if False else None)
    pts = []
    for i in range(61):
        a = math.radians(-95 + 190 * i / 60)
        pts.append(tuple(ax @ Vector((-0.56 * math.cos(a), 0, 0.56 * math.sin(a)))))
    tube("meridian", pts, 0.016, "brass", 6)
    for zz in (0.585, -0.585):
        cyl("pivot", 0.02, 0.06, tuple(ax @ Vector((0, 0, zz))), "brass", seg=16)
    lathe("stand", [(0, 0.0), (0.30, 0.0), (0.31, 0.02), (0.29, 0.05), (0.18, 0.08), (0.10, 0.10), (0.06, 0.14),
                    (0.045, 0.20), (0.04, 0.16 + 0.0), (0.0, 0.16)], "walnut", 72)
    tube("post", [(0, 0, 0.12), (0, 0, 0.17), tuple(ax @ Vector((0, 0, -0.56)))], 0.03, "brass", 6, False)
    torus("standring", 0.295, 0.01, (0, 0, 0.022), "brass", seg=64, mseg=8)
    for o in bpy.context.scene.objects:
        o.location.z -= 0.62


MODELS = {
    "gear": m_gear, "gear_s": m_gear_s, "spool": m_spool, "edu": m_edu, "globe": m_globe, "tophat": m_tophat, "books": m_books,
    "locomotive": m_locomotive, "cube": m_cube, "king": m_king, "coins": m_coins, "hourglass": m_hourglass,
    "cradle": m_cradle, "bulb": m_bulb,
}

if __name__ == "__main__":
    want = [a for a in sys.argv[1:] if a in MODELS] or list(MODELS)
    for key in want:
        reset()
        _mats.clear()
        MODELS[key]()
        export(key)
