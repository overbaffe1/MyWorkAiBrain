# Procedural 3D exhibits for the Cantillon deck (Blender / bpy -> .glb for PowerPoint 3D).
# Re-uses the modelling helpers and the shared material palette of the Schumpeter deck.
#
#   python3 models/make_models.py              -> models/glb/*.glb   (all models)
#   python3 models/make_models.py ship candle  -> only selected models
#
# Convention (same as the Schumpeter models): Blender Z up, the viewer looks from -Y.
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "schumpeter", "models"))
import make_models as mm  # noqa: E402
from make_models import (bpy, bmesh, Vector, Matrix, TAU, M, finish, mesh_obj, lathe, box, cyl, sphere,  # noqa: E402
                         torus, tube, to_mesh, profile2d, rot_all, coin, book)
from rig import Rig, export_rigged, clamp01, smooth, ease, pulse, back_out, hop, wave  # noqa: E402

mm.OUT = os.path.join(HERE, "glb")
os.makedirs(mm.OUT, exist_ok=True)


# ------------------------------------------------------------------ extra helpers
def text_mesh(name, body, size, depth, mat, loc=(0, 0, 0), rot=(0, 0, 0), res=3, bevel=0.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = depth
    cu.bevel_depth = bevel
    cu.bevel_resolution = 1
    cu.resolution_u = res
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    o = mm.link(bpy.data.objects.new(name, cu))
    o.location = loc
    o.rotation_euler = rot
    return to_mesh(o, mat, 30)


def grid_surface(name, nu, nv, fn, mat, smooth=60):
    """Parametric surface: fn(u, v) -> (x, y, z), u, v in [0, 1]."""
    verts = [fn(i / nu, j / nv) for j in range(nv + 1) for i in range(nu + 1)]
    faces = []
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1))
    o = mesh_obj(name, verts, faces)
    return finish(o, mat, smooth)


def extrude_profile(name, prof, x0, x1, mat, smooth=40):
    """Closed (y, z) profile extruded along X with caps."""
    n = len(prof)
    verts = [(x0, y, z) for y, z in prof] + [(x1, y, z) for y, z in prof]
    faces = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    faces.append(tuple(reversed(range(n))))
    faces.append(tuple(range(n, 2 * n)))
    o = mesh_obj(name, verts, faces)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data); bm.free()
    return finish(o, mat, smooth)


def xform(objs, T):
    for o in objs:
        o.matrix_world = T @ o.matrix_world


def shift_all(dx=0, dy=0, dz=0):
    for o in bpy.context.scene.objects:
        o.location.x += dx
        o.location.y += dy
        o.location.z += dz


def sail(name, corners, billow, mat="canvas", nu=10, nv=8, normal=(0, -1, 0)):
    """Bilinear quad sail between 4 corners (tl, tr, br, bl) that bellies out along `normal`."""
    tl, tr, br, bl = [Vector(c) for c in corners]
    n = Vector(normal).normalized()

    def f(u, v):
        top = tl.lerp(tr, u)
        bot = bl.lerp(br, u)
        p = top.lerp(bot, v)
        p = p + n * billow * math.sin(math.pi * u) * (0.35 + 0.65 * math.sin(math.pi * min(1, v * 0.9 + 0.1)))
        return tuple(p)
    return grid_surface(name, nu, nv, f, mat, 70)


# ------------------------------------------------------------------ models
def m_louis():
    """Gold louis d'or with '1720' — the token that rolls along the progress track."""
    r, h = 0.5, 0.035
    lathe("coin", [(0, -h), (r * 0.94, -h), (r, -h + 0.012), (r, h - 0.012), (r * 0.94, h), (r * 0.88, h),
                   (r * 0.86, h - 0.012), (0, h - 0.012)], "gold_satin", 72, 30)
    torus("rim", r * 0.91, 0.013, (0, 0, h - 0.004), "gold", seg=72, mseg=8)
    for k in range(28):
        a = TAU * k / 28
        s = sphere("bead", 0.012, (r * 0.80 * math.cos(a), r * 0.80 * math.sin(a), h - 0.012), "gold", 10, 6)
        s.scale.z = 0.6
    text_mesh("year", "1720", 0.30, 0.012, "gold", loc=(0, -0.04, h - 0.012), res=4)
    text_mesh("rc", "R · C", 0.12, 0.010, "gold", loc=(0, 0.20, h - 0.012), res=3)
    lathe("back", [(0, -h + 0.01), (r * 0.86, -h + 0.01)], "gold", 48)
    rot_all(rx=90)


def m_rook():
    """Black rook = the Bastille that John Law threatened him with."""
    prof = [(0, 0), (0.34, 0), (0.35, 0.012), (0.35, 0.06), (0.32, 0.08), (0.33, 0.10), (0.29, 0.14), (0.24, 0.16),
            (0.22, 0.20), (0.23, 0.22), (0.19, 0.25), (0.165, 0.45), (0.16, 0.68), (0.17, 0.72), (0.23, 0.76),
            (0.25, 0.80), (0.25, 0.94), (0.20, 0.94), (0.20, 0.86), (0, 0.86)]
    lathe("rook", prof, "black", 96, 40)
    n = 6
    for k in range(n):
        a = TAU * (k + 0.5) / n
        o = box("merlon", (0.11, 0.075, 0.11), (0.225 * math.cos(a), 0.225 * math.sin(a), 0.99), "black", 0.012, rot=(0, 0, a))
    torus("band1", 0.252, 0.012, (0, 0, 0.80), "gold", seg=72, mseg=8)
    torus("band2", 0.226, 0.010, (0, 0, 0.21), "gold", seg=72, mseg=8)
    torus("band3", 0.343, 0.010, (0, 0, 0.065), "gold", seg=72, mseg=8)
    # arrow-slit windows and a gate facing the viewer
    for z in (0.40, 0.58):
        box("slit", (0.03, 0.03, 0.09), (0, -0.168, z), "window", 0.006)
    # a broken chain lying next to it
    for i in range(7):
        a = i * 0.9
        torus("link", 0.04, 0.009, (0.42 + i * 0.055, -0.16 + 0.02 * math.sin(i), 0.012), "steel",
              rot=(math.radians(90) if i % 2 else 0, 0, math.radians(20)), seg=20, mseg=6)
    shift_all(dz=-0.5)


def m_bread():
    """A baker's loaf: Cantillon's textbook entrepreneur buys flour at a known price."""
    random.seed(11)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=72, ring_count=40, radius=0.42)
    o = bpy.context.active_object
    o.name = "loaf"
    me = o.data
    for v in me.vertices:
        x, y, z = v.co
        z = z * 0.70 if z > 0 else z * 0.22
        r = math.hypot(x, y)
        # two crossing score lines on the crown
        g = min(abs(x * 0.92 - y * 0.39), abs(x * 0.39 + y * 0.92))
        if z > 0.10 and g < 0.018:
            z -= 0.03 * (1 - g / 0.018)
        n = 1 + 0.02 * math.sin(7 * x + 3 * y) + 0.015 * math.sin(11 * y - 5 * z)
        v.co = (x * n, y * n, z * n)
    finish(o, "crust", 0)
    o.data.materials.append(M("flour"))
    for p in me.polygons:
        x, y, z = p.center
        g = min(abs(x * 0.92 - y * 0.39), abs(x * 0.39 + y * 0.92))
        if z > 0.08 and g < 0.014:
            p.material_index = 1
        p.use_smooth = True
    o.location.z = 0.10
    # cutting board + a small roll + a scattering of flour-coloured grains
    lathe("board", [(0, 0), (0.62, 0), (0.64, 0.015), (0.64, 0.045), (0.62, 0.06), (0, 0.06)], "walnut", 72, 40, loc=(0.05, 0, -0.06))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, radius=0.15, location=(0.44, -0.25, 0.04))
    roll = bpy.context.active_object
    roll.scale = (1.35, 0.9, 0.62)
    finish(roll, "crust", 80)
    for i in range(14):
        a = random.uniform(0, TAU)
        rr = random.uniform(0.45, 0.58)
        s = sphere("grain", 0.012, (0.05 + rr * math.cos(a), rr * math.sin(a), 0.006), "flour", 8, 4)
        s.scale = (1.8, 1, 0.6)
    shift_all(dz=-0.2)


def m_globe_c():
    """Cantillon's banking map: Kerry -> Paris hub -> London, Amsterdam, Brussels, Vienna, Cadiz, Louisiana."""
    cities = {"kerry": (52.2, -9.6), "paris": (48.86, 2.35), "london": (51.5, -0.13), "amsterdam": (52.37, 4.9),
              "brussels": (50.85, 4.35), "vienna": (48.2, 16.4), "cadiz": (36.5, -6.3), "louisiana": (30.0, -90.1)}
    edges = [("kerry", "paris"), ("paris", "london"), ("paris", "amsterdam"), ("paris", "brussels"), ("paris", "vienna"),
             ("paris", "cadiz"), ("paris", "louisiana")]
    mm.m_globe(cities, edges, arc_mat="ember", pin_mat="ivory", spin=-62, arc_r=0.013, pin_r=0.026)



# ------------------------------------------------------------------ living details (v3.1)
def flyer(rig, name, center, radius, z, span, chord, body_r, body_mat, wing_mat, tip_mat=None, moth=False):
    """A bird / moth that orbits `center` (bone `name`) and flaps two wings (bones nameL / nameR).
    Built at orbit angle 0, i.e. at center + (radius, 0, 0), flying towards +Y."""
    cx, cy = center[0] + radius, center[1]
    rig.bone(name, (center[0], center[1], z))
    m = rig.mark()
    b = sphere(name + "_body", body_r, (cx, cy, z), body_mat, 16, 10)
    b.scale = (0.7, 2.2 if not moth else 1.8, 0.7)
    sphere(name + "_head", body_r * 0.75, (cx, cy + body_r * 2.0, z + body_r * 0.25), body_mat, 12, 8)
    if not moth:
        tube(name + "_beak", [(cx, cy + body_r * 2.6, z + body_r * 0.2), (cx, cy + body_r * 3.4, z + body_r * 0.05)], body_r * 0.18, "gold", 2, False)
        tube(name + "_tail", [(cx, cy - body_r * 1.4, z), (cx, cy - body_r * 2.8, z + body_r * 0.2)], body_r * 0.35, wing_mat, 2, False)
    rig.take(m, name)
    for side, bn in ((-1, name + "L"), (1, name + "R")):
        sh = (cx + side * body_r * 0.5, cy, z)
        rig.bone(bn, sh, name)
        m = rig.mark()

        def wing(u, v, side=side):
            c = chord * ((1 - 0.25 * u) if moth else (1 - 0.75 * u ** 1.4))
            sweep = (-0.25 if not moth else -0.05) * chord * u
            x = sh[0] + side * span * u
            y = cy + sweep + c * (0.5 - v) + (0.25 * chord * u if not moth else 0.0)
            zz = z + (0.18 * span * math.sin(math.pi * u * 0.8) if not moth else 0.04 * span * u)
            return (x, y, zz)
        grid_surface(bn, 8, 3, wing, wing_mat, 60)
        if tip_mat:
            grid_surface(bn + "_tip", 3, 2, lambda u, v, side=side: (
                sh[0] + side * span * (0.78 + 0.22 * u), cy - 0.25 * chord * (0.78 + 0.22 * u) + 0.25 * chord * (0.78 + 0.22 * u)
                + chord * (1 - 0.75 * (0.78 + 0.22 * u) ** 1.4) * (0.5 - v),
                z + 0.18 * span * math.sin(math.pi * (0.78 + 0.22 * u) * 0.8) + 0.002), tip_mat, 60)
        rig.take(m, bn)
    return name


def flyer_pose(name, t, turns=1, flaps=8, amp=32, bob=0.03, bob_k=2, glide=None):
    a = amp * math.sin(TAU * flaps * t)
    if glide:  # wings held still for part of the loop (gliding)
        a *= 1 - pulse(t, *glide) * 0.85
    return {name: {"rot": [((0, 0, 1), 360 * turns * t)], "loc": (0, 0, bob * math.sin(TAU * bob_k * t))},
            name + "L": {"rot": [((0, 1, 0), a)]},
            name + "R": {"rot": [((0, 1, 0), -a)]}}


def puff_pose(t, k, n, rise, drift, size=1.0):
    """Looping smoke / note particle: rises, grows, fades out (scale 0 at both ends of its life)."""
    u = (t + k / n) % 1.0
    sc = max(0.001, math.sin(math.pi * u) * (0.5 + 0.8 * u) * size)
    return {"loc": (drift * math.sin(TAU * u + k), 0, rise * u), "scale": sc}


# ------------------------------------------------------------------ animated exhibits (v3)
# Every exhibit below returns (rig, anim, seconds): the parts move by themselves inside PowerPoint
# (embedded glTF skin animation, looped until the end of the slide) — not a turntable spin.

def m_ship():
    """Merchant ship riding live waves: hull pitches and rolls, sails breathe, pennant flutters."""
    rig = Rig()
    NX, NS = 44, 18
    t0, t1 = -0.92, 1.0
    rows, verts = [], []
    m_hull = rig.mark()
    for i in range(NX + 1):
        t = t0 + (t1 - t0) * i / NX
        x = t * 1.0
        if t >= 0:
            w = 0.26 * max(0.0, 1 - (t / 1.0) ** 2) ** 0.55
        else:
            w = 0.26 * max(0.0, 1 - (abs(t) / 1.02) ** 5) ** 0.5
        w = max(w, 0.004)
        ztop = 0.30 + 0.07 * t * t + (0.10 if t < -0.55 else 0.10 * max(0, (-t - 0.40) / 0.15) if t < -0.40 else 0)
        zbot = 0.02 + 0.10 * max(0, t - 0.55) ** 1.5 * 4 + 0.04 * max(0, -t - 0.7)
        row = []
        for j in range(NS + 1):
            th = math.pi * j / NS
            c, s = math.cos(th), math.sin(th)
            y = w * (abs(c) ** 0.7) * (1 if c >= 0 else -1)
            z = ztop - (ztop - zbot) * (s ** 1.6)
            row.append(len(verts))
            verts.append((x, y, z))
        rows.append(row)
    faces = []
    for A, B in zip(rows, rows[1:]):
        for j in range(NS):
            faces.append((A[j], B[j], B[j + 1], A[j + 1]))
    hull = mesh_obj("hull", verts, faces)
    bm = bmesh.new(); bm.from_mesh(hull.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(hull.data); bm.free()
    for mname in ("brass_d", "black", "walnut"):
        hull.data.materials.append(M(mname))
    for p in hull.data.polygons:
        z = p.center.z
        p.material_index = 0 if z < 0.11 else (1 if z < 0.21 else 2)
        p.use_smooth = True
    hull.data.set_sharp_from_angle(angle=math.radians(50))
    dverts = []
    for row in rows:
        dverts.append(verts[row[0]])
        dverts.append(verts[row[-1]])
    dfaces = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(len(rows) - 1)]
    finish(mesh_obj("deck", [(x, y, z - 0.012) for x, y, z in dverts], dfaces), "brown", 40)
    tr = [verts[k] for k in rows[0]]
    finish(mesh_obj("transom", tr, [tuple(range(len(tr)))]), "walnut", 0)
    for side in (1, -1):
        pts = []
        for i in range(0, NX + 1, 2):
            idx = int(round(NS * 0.18)) if side > 0 else NS - int(round(NS * 0.18))
            px, py, pz = verts[rows[i][idx]]
            pts.append((px, py + 0.004 * side, pz))
        tube("stripe", pts, 0.006, "gold", 2)
        for k in range(7):
            x = -0.55 + k * 0.17
            i = int(round((x - t0) / (t1 - t0) * NX))
            idx = int(round(NS * 0.30)) if side > 0 else NS - int(round(NS * 0.30))
            px, py, pz = verts[rows[i][idx]]
            box("port", (0.05, 0.02, 0.04), (px, py + 0.006 * side, pz), "satin", 0.004)
    for k in range(3):
        box("sternwin", (0.012, 0.05, 0.04), (t0 - 0.004, -0.08 + k * 0.08, 0.36), "window", 0.003)
    lathe("lantern", [(0, 0), (0.025, 0), (0.03, 0.03), (0.025, 0.06), (0.01, 0.075), (0, 0.08)], "ember", 16, 40, loc=(-0.95, 0, 0.46))
    rig.take(m_hull, "hull", head=(0.0, 0, 0.12))
    masts = [(0.45, 1.25), (0.0, 1.45), (-0.48, 1.05)]
    brace = math.radians(28)
    ax = Vector((-math.sin(brace), math.cos(brace), 0))
    nrm = Vector((math.cos(brace), math.sin(brace), 0)) * -1
    si = 0
    for mx, mh in masts:
        m0 = rig.mark()
        cyl("mast", 0.02, mh, (mx, 0, 0.30 + mh / 2), "walnut", seg=16)
        cyl("top", 0.05, 0.015, (mx, 0, 0.30 + mh * 0.62), "walnut", seg=16)
        levels = [(0.30 + mh * 0.58, 0.30 + mh * 0.16, 0.30 if mx != -0.48 else 0.22),
                  (0.30 + mh * 0.95, 0.30 + mh * 0.63, 0.22 if mx != -0.48 else 0.16)]
        for ztop_, zbot_, half in levels:
            c_top = Vector((mx, 0, ztop_))
            tube("yard", [tuple(c_top - ax * (half + 0.04)), tuple(c_top + ax * (half + 0.04))], 0.009, "walnut", 2, False)
        rig.take(m0, "hull")
        for ztop_, zbot_, half in levels:
            c_top = Vector((mx, 0, ztop_))
            c_bot = Vector((mx, 0, zbot_))
            hb = half * 1.18
            m1 = rig.mark()
            sail("sail", [c_top - ax * half, c_top + ax * half, c_bot + ax * hb, c_bot - ax * hb], 0.09,
                 normal=(nrm.x, nrm.y - 0.6, 0))
            rig.take(m1, f"sail{si}", head=tuple(c_top), parent="hull")
            si += 1
    m2 = rig.mark()
    tube("bowsprit", [(0.95, 0, 0.38), (1.42, 0, 0.62)], 0.014, "walnut", 2, False)
    for (ax_, ah), (bx_, bh) in zip(masts, masts[1:]):
        tube("stay", [(ax_, 0, 0.30 + ah * 0.98), (bx_, 0, 0.30 + bh * 0.62)], 0.0028, "satin", 2, False)
    tube("forestay", [(0.45, 0, 0.30 + 1.25 * 0.98), (1.40, 0, 0.61)], 0.0028, "satin", 2, False)
    tube("backstay", [(-0.48, 0, 0.30 + 1.05 * 0.98), (-0.90, 0, 0.42)], 0.0028, "satin", 2, False)
    rig.take(m2, "hull")
    m3 = rig.mark()
    jib = mesh_obj("jib", [(1.38, 0, 0.60), (0.47, 0, 1.40), (0.62, 0, 0.42)], [(0, 1, 2)])
    finish(jib, "canvas", 0)
    rig.take(m3, "jib", head=(0.92, 0, 1.0), parent="hull")
    # pennant: three-bone chain, smoothly skinned along its length
    rig.bone("pen0", (0.0, 0, 1.78), "hull")
    rig.bone("pen1", (-0.11, 0, 1.78), "pen0")
    rig.bone("pen2", (-0.21, 0, 1.78), "pen1")
    m4 = rig.mark()
    grid_surface("pennant", 16, 2, lambda u, v: (-0.32 * u, 0.02 * math.sin(u * 5), 1.78 + 0.04 * (1 - u) * (v - 0.5) * 2), "oxblood", 60)

    def pen_w(co):
        s = clamp01(-co.x / 0.32)
        return {"pen0": clamp01(1 - s * 3), "pen1": clamp01(1 - abs(s - 0.34) * 3), "pen2": clamp01((s - 0.34) * 3)}
    rig.take_fn(m4, "pennant", pen_w)
    # live sea: a skirted water slab whose surface is carried by 8 wave bones (travelling swell)
    X0, X1, Y0, Y1, ZS, ZB = -1.32, 1.66, -0.46, 0.46, 0.128, 0.06
    nu, nv = 84, 26

    def sea(u, v):
        iu, iv = round(u * nu), round(v * nv)
        edge = iu in (0, nu) or iv in (0, nv)
        fu = clamp01((iu - 1) / (nu - 2)); fv = clamp01((iv - 1) / (nv - 2))
        x = X0 + (X1 - X0) * fu; y = Y0 + (Y1 - Y0) * fv
        if edge:
            return (x, y, ZB)
        z = ZS + 0.008 * math.sin(11 * x + 3 * y) + 0.005 * math.sin(23 * x - 9 * y + 1.3)
        return (x, y, z)
    wxs = [X0 + 0.1 + k * (X1 - X0 - 0.2) / 7 for k in range(8)]
    for k, x in enumerate(wxs):
        rig.bone(f"wave{k}", (x, 0, ZS))
    m5 = rig.mark()
    grid_surface("sea", nu, nv, sea, "water", 50)
    # foam crests along the swell
    random.seed(3)
    for k in range(26):
        x = random.uniform(X0 + 0.08, X1 - 0.08); y = random.choice((-1, 1)) * random.uniform(0.28, 0.42)
        f = sphere("foam", 0.022, (x, y, ZS + 0.006), "paper", 10, 5)
        f.scale = (2.4, 0.9, 0.35)

    def sea_w(co):
        if co.z < ZB + 0.01:
            return {"root": 1.0}
        w = {f"wave{k}": math.exp(-((co.x - x) / 0.26) ** 2) for k, x in enumerate(wxs)}
        return w
    rig.take_fn(m5, "sea", sea_w)
    m6 = rig.mark()
    box("plinth", (X1 - X0 + 0.12, Y1 - Y0 + 0.12, 0.09), ((X0 + X1) / 2, 0, ZB - 0.045), "walnut", 0.015)
    box("plate", (0.46, 0.008, 0.05), ((X0 + X1) / 2, Y0 - 0.064, ZB - 0.045), "brass", 0.003)
    rig.take(m6, "root")
    flyer(rig, "gull", (0.15, 0.0), 0.44, 1.46, 0.30, 0.12, 0.04, "paper", "paper", tip_mat="satin")
    rig.shift(dz=-0.55)
    LAM = 1.5

    def anim(t):
        p = {f"wave{k}": {"loc": (0, 0, 0.036 * wave(t, 1, -x / LAM))} for k, x in enumerate(wxs)}
        p["hull"] = {"rot": [((0, 1, 0), 3.2 * math.cos(TAU * t)), ((1, 0, 0), 3.6 * wave(t, 1, 0.18))],
                     "loc": (0, 0, 0.022 * wave(t, 1, 0))}
        for i in range(si):
            p[f"sail{i}"] = {"rot": [(tuple(ax), 4.0 * wave(t, 1, 0.07 * i) + 1.6 * wave(t, 3, 0.11 * i))]}
        p["jib"] = {"rot": [((0.73, 0, -0.68), 5 * wave(t, 2, 0.2))]}
        p["pen0"] = {"rot": [((0, 0, 1), 14 * wave(t, 3, 0.0))]}
        p["pen1"] = {"rot": [((0, 0, 1), 20 * wave(t, 3, -0.16))]}
        p["pen2"] = {"rot": [((0, 0, 1), 26 * wave(t, 3, -0.32))]}
        p.update(flyer_pose("gull", t, turns=1, flaps=10, amp=34, bob=0.05, bob_k=2, glide=(0.30, 0.38, 0.55, 0.62)))
        return p
    return rig, anim, 4.0


def m_harp():
    """Irish harp — a glissando runs across the strings; each string really vibrates and decays."""
    rig = Rig()
    S0, S1 = Vector((-0.02, 0, 0.06)), Vector((-0.42, 0, 1.06))
    axis = (S1 - S0).normalized()
    side = Vector((axis.z, 0, -axis.x))
    N = 12
    verts, faces = [], []
    for i in range(N + 1):
        t = i / N
        c = S0.lerp(S1, t)
        hw = 0.13 * (1 - t) + 0.05 * t
        hd = 0.12 * (1 - t) + 0.05 * t
        for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            p = c + side * (hw * sx)
            verts.append((p.x, hd * sy, p.z))
    for i in range(N):
        a = i * 4
        for k in range(4):
            faces.append((a + k, a + (k + 1) % 4, a + 4 + (k + 1) % 4, a + 4 + k))
    faces.append((3, 2, 1, 0))
    b = N * 4
    faces.append((b, b + 1, b + 2, b + 3))
    sb = mesh_obj("soundbox", verts, faces)
    bm = bmesh.new(); bm.from_mesh(sb.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(sb.data); bm.free()
    finish(sb, "walnut", 30, 0.025, 3)
    tube("inlay", [tuple(S0.lerp(S1, 0.05) + Vector((0, -0.125, 0))), tuple(S0.lerp(S1, 0.95) + Vector((0, -0.055, 0)))], 0.006, "gold", 2, False)
    neck = [(-0.44, 0, 1.08), (-0.34, 0, 1.20), (-0.18, 0, 1.20), (-0.02, 0, 1.10), (0.14, 0, 1.08), (0.30, 0, 1.22), (0.40, 0, 1.30)]
    tube("neck", neck, 0.045, "walnut", 5)
    pillar = [(0.40, 0, 1.30), (0.52, 0, 1.0), (0.56, 0, 0.6), (0.50, 0, 0.25), (0.40, 0, 0.04)]
    tube("pillar", pillar, 0.042, "walnut", 5)
    for z in (0.35, 0.75, 1.1):
        torus("pring", 0.047, 0.008, (0.53 if 0.3 < z < 1.0 else 0.47, 0, z), "brass", rot=(0, math.radians(90 - 12), 0), seg=24, mseg=6)
    box("foot", (0.56, 0.20, 0.05), (0.19, 0, 0.025), "walnut", 0.015)
    torus("medal", 0.05, 0.008, tuple(S0.lerp(S1, 0.55) + Vector((0, -0.095, 0))), "gold", rot=(math.radians(90), 0, 0), seg=32, mseg=6)
    # carved shamrock on the fore-pillar
    for k in range(3):
        a = math.radians(90 + 120 * k)
        sphere("leaf", 0.03, (0.56 + 0.028 * math.cos(a) * 0.3, -0.045, 0.62 + 0.03 * math.sin(a)), "gold", 16, 8).scale = (0.6, 0.35, 1.0)
    import numpy as np
    nx = np.array([p[0] for p in neck]); nz = np.array([p[2] for p in neck])
    strings = []
    for k in range(13):
        t = 0.10 + 0.80 * k / 12
        c = S0.lerp(S1, t) + side * (0.13 * (1 - t) + 0.05 * t) * 0.9
        x = c.x
        if x > 0.42:
            continue
        ztop = float(np.interp(x, nx, nz)) - 0.03
        h = ztop - c.z
        if h < 0.08:
            continue
        sphere("peg", 0.012, (x, -0.05, ztop + 0.01), "brass", 10, 6)
        strings.append((x, c.z, ztop))
    strings.sort()
    for i, (x, zb, zt) in enumerate(strings):
        bn = rig.bone(f"str{i}", (x, 0, zt))
        m = rig.mark()
        cyl("string", 0.0045, zt - zb, (x, 0, (zb + zt) / 2), "gold", seg=8)
        o = [ob for ob in bpy.context.scene.objects if ob not in m][0]
        # more rings along the string so it can bow smoothly
        bm = bmesh.new(); bm.from_mesh(o.data)
        edges = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.01]
        bmesh.ops.subdivide_edges(bm, edges=edges, cuts=14, use_grid_fill=True)
        bm.to_mesh(o.data); bm.free()

        def sw(co, zb=zb, zt=zt, bn=bn):
            u = clamp01((zt - co.z) / (zt - zb))
            w = math.sin(math.pi * u) ** 1.3
            return {bn: w, "root": 1 - w}
        rig.take_fn(m, f"s{i}", sw)
    # golden notes drifting up out of the strings
    for k, (nx0, nz0) in enumerate([(-0.12, 0.36), (0.02, 0.28), (-0.22, 0.50)]):
        head = (nx0, -0.10, nz0)
        rig.bone(f"note{k}", head)
        m = rig.mark()
        hd = sphere("notehead", 0.026, head, "gold", 16, 10)
        hd.scale = (1.35, 0.55, 1.0)
        hd.rotation_euler = (0, math.radians(-25), 0)
        cyl("notestem", 0.0055, 0.13, (nx0 + 0.03, -0.10, nz0 + 0.065), "gold", seg=8)
        if k != 1:
            tube("noteflag", [(nx0 + 0.03, -0.10, nz0 + 0.13), (nx0 + 0.07, -0.10, nz0 + 0.09), (nx0 + 0.065, -0.10, nz0 + 0.05)], 0.006, "gold", 2)
        else:  # a pair of quavers
            cyl("notestem2", 0.0055, 0.13, (nx0 + 0.11, -0.10, nz0 + 0.075), "gold", seg=8)
            sphere("notehead2", 0.026, (nx0 + 0.08, -0.10, nz0 + 0.01), "gold", 16, 10).scale = (1.35, 0.55, 1.0)
            box("notebeam", (0.09, 0.008, 0.016), (nx0 + 0.07, -0.10, nz0 + 0.135), "gold", 0.002)
        S = 1.9  # readable size on a slide
        xform([o for o in bpy.context.scene.objects if o not in m],
              Matrix.Translation(head) @ Matrix.Scale(S, 4) @ Matrix.Translation(Vector(head) * -1))
        rig.take(m, f"note{k}")
    rig.shift(dz=-0.65, dx=-0.05)
    ns = len(strings)

    def anim(t):
        p = {}
        for i in range(ns):
            # glissando up (t 0.05 .. 0.45) then down (0.55 .. 0.95)
            starts = [0.05 + 0.40 * i / max(1, ns - 1), 0.55 + 0.40 * (ns - 1 - i) / max(1, ns - 1)]
            ang = 0.0
            for s0 in starts:
                d = t - s0
                if d < 0:
                    continue
                ang += 11.0 * math.exp(-d / 0.10) * math.sin(TAU * 22 * d)
            # fade the tail so the loop closes cleanly
            ang *= 1 - ease(t, 0.97, 1.0)
            p[f"str{i}"] = {"rot": [((1, 0, 0), ang)]}
        for k in range(3):
            q = puff_pose(t, k, 3, 0.42, 0.06, 1.0)
            q["loc"] = (q["loc"][0] + 0.10 * ((t + k / 3) % 1.0), 0, q["loc"][2])
            q["rot"] = [((0, 1, 0), 18 * math.sin(TAU * ((t + k / 3) % 1.0) * 1.5))]
            q["scale"] = min(1.0, q["scale"] * 1.25)
            p[f"note{k}"] = q
        return p
    return rig, anim, 4.0


def m_chest():
    """Iron-bound strongbox: the key turns, the lid swings open, his papers rise, coins flip."""
    rig = Rig()
    W, D, H = 1.0, 0.58, 0.46
    R = D / 2
    # body as an open box (walls) so the inside is visible when the lid opens
    th = 0.04
    box("floor", (W, D, th), (0, 0, th / 2), "walnut", 0.008)
    box("wallF", (W, th, H), (0, -D / 2 + th / 2, H / 2), "walnut", 0.008)
    box("wallB", (W, th, H), (0, D / 2 - th / 2, H / 2), "walnut", 0.008)
    for sx in (-1, 1):
        box("wallS", (th, D, H), (sx * (W / 2 - th / 2), 0, H / 2), "walnut", 0.008)
    box("lining", (W - 2 * th, D - 2 * th, 0.004), (0, 0, th + 0.002), "wine", 0.0)
    for x in (-0.34, 0.34):
        box("bandF", (0.06, 0.012, H), (x, -D / 2 - 0.006, H / 2), "iron", 0.004)
        box("bandB", (0.06, 0.012, H), (x, D / 2 + 0.006, H / 2), "iron", 0.004)
        box("bandBot", (0.06, D + 0.024, 0.012), (x, 0, 0.006), "iron", 0.004)
        for z in (0.08, 0.23, 0.38):
            sphere("stud", 0.013, (x, -D / 2 - 0.013, z), "brass", 12, 6)
    for sx in (-1, 1):
        for sy in (-1, 1):
            box("corner", (0.08, 0.08, 0.08), (sx * (W / 2 - 0.03), sy * (D / 2 - 0.03), 0.04), "iron", 0.008)
        torus("handle", 0.07, 0.012, (sx * (W / 2 + 0.025), 0, H * 0.62), "iron", rot=(0, math.radians(90), 0), seg=32, mseg=8)
    box("lockplate", (0.18, 0.016, 0.20), (0, -D / 2 - 0.01, H - 0.06), "gold", 0.006)
    # contents sit on a raised inner tray, so they show above the front wall when the lid is open
    th0 = th
    th = th0 + 0.15
    box("tray", (W - 2 * th0 - 0.01, D - 2 * th0 - 0.01, 0.15), (0, 0, th0 + 0.075), "walnut", 0.004)
    box("trayfelt", (W - 2 * th0 - 0.03, D - 2 * th0 - 0.03, 0.004), (0, 0, th + 0.002), "wine", 0.0)
    random.seed(4)
    for i in range(5):
        box("letters", (0.30, 0.20, 0.03), (-0.22 + random.uniform(-0.01, 0.01), 0.03, th + 0.02 + i * 0.032), "paper", 0.004,
            rot=(0, 0, random.uniform(-0.08, 0.08)))
    box("tie", (0.03, 0.205, 0.165), (-0.22, 0.03, th + 0.085), "wine", 0.002)
    for j, (cx, cy, n) in enumerate([(0.30, -0.08, 6), (0.34, 0.08, 4), (0.12, 0.12, 5)]):
        for i in range(n):
            coin("c", (cx + random.uniform(-0.006, 0.006), cy, th + 0.015 + i * 0.026), (0, 0, random.uniform(0, 6)), r=0.075, t=0.026)
    # three coins that jump and flip when the lid is open
    for j, (cx, cy, z0) in enumerate([(0.30, -0.08, th + 0.015 + 6 * 0.026), (0.34, 0.08, th + 0.015 + 4 * 0.026),
                                      (0.12, 0.12, th + 0.015 + 5 * 0.026)]):
        m = rig.mark()
        coin("flip", (cx, cy, z0), (0, 0, j), r=0.075, t=0.026)
        rig.take(m, f"coin{j}", head=(cx, cy, z0))
    # the scroll with a red seal that rises out of the chest
    m = rig.mark()
    cyl("scroll", 0.045, 0.40, (0.0, -0.17, th + 0.05), "paper", rot=(0, math.radians(90), 0), seg=28)
    for sx in (-1, 1):
        cyl("scrollend", 0.052, 0.022, (sx * 0.20, -0.17, th + 0.05), "brass", rot=(0, math.radians(90), 0), seg=28)
    cyl("sealS", 0.035, 0.012, (0.0, -0.218, th + 0.05), "wine", rot=(math.radians(90), 0, 0), seg=24)
    rig.take(m, "scroll", head=(0.0, -0.17, th + 0.05))
    # lid (hinged at the back top edge) with its bands and hasp
    m = rig.mark()
    prof = [(R * math.cos(math.pi * i / 24), H + R * 0.62 * math.sin(math.pi * i / 24)) for i in range(25)]
    extrude_profile("lid", prof, -W / 2, W / 2, "walnut")
    box("lidlining", (W - 0.06, D - 0.06, 0.004), (0, 0, H + 0.004), "wine", 0.0)
    for x in (-0.34, 0.34):
        bp = [((R + 0.012) * math.cos(math.pi * i / 24), H + (R * 0.62 + 0.012) * math.sin(math.pi * i / 24)) for i in range(25)]
        bp = bp + [(p[0] * 0.92, H + (p[1] - H) * 0.92 - 0.004) for p in reversed(bp)]
        extrude_profile("bandLid", bp, x - 0.03, x + 0.03, "iron")
    box("hasp", (0.07, 0.02, 0.16), (0, -D / 2 - 0.02, H + 0.02), "brass_d", 0.006)
    rig.take(m, "lid", head=(0, D / 2, H))
    # key in the lock: turns before the lid opens
    m = rig.mark()
    cyl("keyhole", 0.016, 0.03, (0, -D / 2 - 0.02, H - 0.09), "satin", rot=(math.radians(90), 0, 0), seg=16)
    tube("keyshaft", [(0, -D / 2 - 0.03, H - 0.09), (0, -D / 2 - 0.20, H - 0.09)], 0.011, "brass", 3, False)
    torus("keybow", 0.045, 0.011, (0, -D / 2 - 0.245, H - 0.09), "brass", rot=(math.radians(90), 0, 0), seg=32, mseg=8)
    rig.take(m, "key", head=(0, -D / 2 - 0.02, H - 0.09))
    rig.shift(dz=-0.38)

    def anim(t):
        key = 90 * ease(t, 0.03, 0.12) * (1 - ease(t, 0.92, 0.99))
        lid = -98 * back_out((t - 0.14) / 0.20, 1.2) * (1 - ease(t, 0.78, 0.91)) if t > 0.14 else 0.0
        rise = pulse(t, 0.30, 0.44, 0.66, 0.78)
        p = {"key": {"rot": [((0, 1, 0), key)]},
             "lid": {"rot": [((1, 0, 0), lid)]},
             "scroll": {"loc": (0, -0.02 * rise, 0.30 * rise), "rot": [((0, 0, 1), 18 * rise), ((1, 0, 0), -14 * rise)]}}
        for j in range(3):
            s = 0.42 + 0.06 * j
            q = clamp01((t - s) / 0.13)
            p[f"coin{j}"] = {"loc": (0, 0, 0.17 * hop(q)), "rot": [((1, 0, 0) if j != 1 else (0, 1, 0), 360 * smooth(q))]}
        return p
    return rig, anim, 5.0


def m_bubble():
    """Mississippi bubble: it inflates and wobbles, bursts — shares fly up — and regrows."""
    rig = Rig()
    random.seed(7)
    sheets = []
    for i in range(9):
        m = rig.mark()
        box("share", (0.62, 0.42, 0.007), (random.uniform(-0.02, 0.02), random.uniform(-0.02, 0.02), 0.004 + i * 0.009),
            "paper", 0.002, rot=(0, 0, random.uniform(-0.12, 0.12)))
        if i >= 6:
            rig.take(m, f"sheet{i}", head=(0.0, 0.0, 0.004 + i * 0.009))
            sheets.append(i)
    m = rig.mark()
    lathe("seal", [(0, 0.10), (0.05, 0.10), (0.055, 0.092), (0.055, 0.084), (0, 0.084)], "wine", 32, loc=(0.16, -0.10, 0.0))
    box("ribbon", (0.05, 0.44, 0.004), (0.16, 0, 0.088), "wine", 0.001)
    rig.take(m, "sheet8")
    t = 0.04
    for i in range(6):
        coin("c", (-0.42 + random.uniform(-0.01, 0.01), -0.12, 0.02 + i * t), (0, 0, random.uniform(0, 6)), r=0.10, t=t)
    for i in range(3):
        coin("c2", (-0.30, 0.10, 0.02 + i * t), (0, 0, random.uniform(0, 6)), r=0.10, t=t)
    m = rig.mark()
    sphere("bubble", 0.40, (0.02, 0, 0.50), "bubble", 64, 32)
    rig.take(m, "bubble", head=(0.02, 0, 0.50))
    m = rig.mark()
    cyl("scroll", 0.035, 0.34, (0.02, 0, 0.50), "paper", rot=(0, math.radians(90), 0), seg=24)
    for sx in (-1, 1):
        cyl("scrollend", 0.042, 0.02, (0.02 + sx * 0.16, 0, 0.50), "brass", rot=(0, math.radians(90), 0), seg=24)
    text_mesh("rue", "1720", 0.035, 0.002, "wine", loc=(0.02, -0.036, 0.50), rot=(math.radians(90), 0, 0), res=2)
    rig.take(m, "scroll", head=(0.02, 0, 0.50))
    box("base", (0.95, 0.62, 0.04), (0, 0, -0.025), "walnut", 0.01)
    box("plate", (0.30, 0.006, 0.026), (0, -0.313, -0.025), "brass", 0.002)
    rig.shift(dz=-0.5)

    def anim(t):
        grow = 1.0 + 0.10 * ease(t, 0.0, 0.58)
        wob = 0.035 * math.sin(TAU * 7 * t) * (1 - ease(t, 0.55, 0.62))
        pop = 1 - ease(t, 0.60, 0.63)
        regrow = back_out((t - 0.74) / 0.24, 1.4) if t > 0.74 else 0.0
        s = grow * pop + (1 - pop) * (0.02 + 0.98 * regrow)
        if t > 0.74:
            s = 0.02 + 0.98 * regrow
        sx = s * (1 + wob); sz = s * (1 - wob)
        p = {"bubble": {"scale": (sx, sx, sz)}}
        fall = ease(t, 0.62, 0.70) * (1 - ease(t, 0.80, 0.97))
        p["scroll"] = {"rot": [((0, 0, 1), 360 * t), ((1, 0, 0), 8 * math.sin(TAU * 2 * t) * (1 - fall))],
                       "loc": (0, 0, 0.012 * math.sin(TAU * 2 * t) - 0.38 * fall)}
        for k, i in enumerate(sheets):
            q = clamp01((t - 0.615 - 0.02 * k) / 0.22)
            p[f"sheet{i}"] = {"loc": (0.04 * (k - 1) * hop(q), 0, (0.22 + 0.06 * k) * hop(q)),
                              "rot": [((0, 1, 0), (16 + 9 * k) * math.sin(math.pi * q) * (1 if k % 2 else -1)),
                                      ((1, 0, 0), 10 * math.sin(TAU * q))]}
        return p
    return rig, anim, 5.0


def m_quill():
    """'Essai' lies open: pages turn by themselves; the quill dips into the inkpot."""
    rig = Rig()
    W, D, T = 0.50, 0.72, 0.075  # half-width of the open book, depth, block thickness
    cov = 0.016
    # covers + page blocks (static), spine in the middle (x = 0)
    for sx in (-1, 1):
        box("cover", (W + 0.03, D + 0.04, cov), (sx * (W / 2 + 0.008), 0, cov / 2), "leather", 0.006)
        box("block", (W - 0.01, D - 0.01, T - cov), (sx * (W / 2 + 0.002), 0, cov + (T - cov) / 2), "paper", 0.006)
        for k in range(14):
            yy = D / 2 - 0.09 - k * 0.04
            if sx < 0 and k < 3:
                continue
            ln = (W - 0.14) * (0.55 if k % 5 == 4 else 1.0)
            box("line", (ln, 0.008, 0.0015), (sx * (0.06 + ln / 2), yy, T + 0.0008), "ink", 0.0)
    text_mesh("ttl", "ESSAI", 0.06, 0.0015, "ink", loc=(-W / 2, D / 2 - 0.08, T + 0.001), res=2)
    text_mesh("ttl2", "sur la nature du commerce", 0.024, 0.0012, "ink", loc=(-W / 2, D / 2 - 0.13, T + 0.001), res=2)
    cyl("spine", 0.022, D + 0.04, (0, 0, cov * 0.4), "leather", rot=(math.radians(90), 0, 0), seg=20)
    for y in (-D / 2 + 0.03, D / 2 - 0.03):
        box("headband", (0.03, 0.012, T * 0.8), (0, y, T * 0.45), "wine", 0.002)
    box("ribbon", (0.012, D * 0.6, 0.002), (0.02, -D * 0.35, cov * 0.5), "wine", 0.0)
    # three turning pages, each hinged at the spine with a second bone for the curl
    npg = 3
    for i in range(npg):
        z = T + 0.003 + 0.0025 * i
        ha = rig.bone(f"pg{i}a", (0.0, 0, z))
        hb = rig.bone(f"pg{i}b", (W * 0.45, 0, z), ha)
        m = rig.mark()
        grid_surface("page", 14, 2, lambda u, v, z=z: (0.004 + (W - 0.02) * u, -D / 2 + 0.01 + (D - 0.02) * v, z + 0.012 * math.sin(math.pi * u) * 0.0), "paper", 60)
        for side in (1, -1):
            for k in range(14):
                yy = D / 2 - 0.09 - k * 0.04
                ln = (W - 0.14) * (0.55 if (k + i) % 5 == 4 else 1.0)
                box("pl", (ln, 0.008, 0.0012), (0.06 + ln / 2, yy, z + side * 0.0011), "ink", 0.0)

        def pw(co, ha=ha, hb=hb):
            u = clamp01((co.x - 0.0) / (W * 0.9))
            wb = smooth(clamp01((u - 0.30) / 0.6))
            return {ha: 1 - wb, hb: wb}
        rig.take_fn(m, f"page{i}", pw)
    # inkpot + quill
    ip = (W + 0.24, -0.10, 0.0)
    lathe("inkpot", [(0, 0), (0.13, 0), (0.15, 0.02), (0.15, 0.10), (0.12, 0.15), (0.06, 0.17), (0.06, 0.20), (0.075, 0.21),
                     (0.075, 0.23), (0.05, 0.23), (0.05, 0.19), (0, 0.19)], "ink", 64, 40, loc=ip)
    torus("collar", 0.07, 0.01, (ip[0], ip[1], 0.215), "brass", seg=32, mseg=6)
    torus("potring", 0.15, 0.009, (ip[0], ip[1], 0.06), "brass", seg=48, mseg=6)
    m = rig.mark()
    base = Vector((ip[0], ip[1], 0.16))
    tip_dir = Vector((-0.30, 0.30, 1.0)).normalized()
    Lq = 0.85
    pts = [tuple(base + tip_dir * (Lq * i / 8) + Vector((-0.06, 0.0, 0)) * ((i / 8) ** 2)) for i in range(9)]
    tube("shaft", pts, 0.007, "ivory", 3)
    sd = tip_dir.cross(Vector((0, -1, 0))).normalized()
    for sgn, wmax in ((1, 0.075), (-1, 0.05)):
        def vane(u, v, sgn=sgn, wmax=wmax):
            uu = 0.22 + 0.78 * u
            p = base + tip_dir * (Lq * uu) + Vector((-0.06, 0.0, 0)) * (uu ** 2)
            prof = math.sin(math.pi * min(1, (u ** 0.8))) ** 0.6 * (1 - 0.25 * u)
            notch = 0.82 if 0.38 < u < 0.42 or 0.66 < u < 0.69 else 1.0
            w = wmax * prof * notch * v
            q = p + sd * (w * sgn) + Vector((0, -1, 0)) * (0.03 * v * v) - tip_dir * (0.05 * v)
            return tuple(q)
        grid_surface("vane", 24, 3, vane, "feather", 70)
    rig.take(m, "quill", head=(ip[0], ip[1], 0.21))
    rig.shift(dx=-0.12, dz=-0.30)
    turn = [(0.06, 0.26), (0.24, 0.44), (0.42, 0.62)]

    def anim(t):
        p = {}
        back = ease(t, 0.80, 0.95)
        for i, (a, b) in enumerate(turn):
            q = ease(t, a, b)
            ang = -(178 - 2.5 * i) * q * (1 - back)
            curl = -38 * math.sin(math.pi * clamp01((t - a) / (b - a))) * (1 - back) + 30 * math.sin(math.pi * back) * (q > 0.5)
            p[f"pg{i}a"] = {"rot": [((0, 1, 0), ang)]}
            p[f"pg{i}b"] = {"rot": [((0, 1, 0), curl)]}
        dip = hop(clamp01((t - 0.10) / 0.22)) + hop(clamp01((t - 0.55) / 0.22))
        p["quill"] = {"loc": (0, 0, 0.07 * dip), "rot": [((1, 0, 0), 4 * wave(t, 1, 0.1)), ((0, 1, 0), -5 * wave(t, 2, 0.0))]}
        return p
    return rig, anim, 6.0


def die(name, size, loc, rot):
    o = box(name, (size, size, size), (0, 0, 0), "ivory", size * 0.14, seg=4)
    parts = [o]
    h = size / 2
    q = size * 0.26
    r = size * 0.085
    faces = {
        (0, 0, 1): [(0, 0)],
        (0, 0, -1): [(-q, -q), (-q, 0), (-q, q), (q, -q), (q, 0), (q, q)],
        (0, -1, 0): [(-q, -q), (q, q)],
        (0, 1, 0): [(-q, -q), (-q, q), (q, -q), (q, q), (0, 0)],
        (1, 0, 0): [(-q, -q), (0, 0), (q, q)],
        (-1, 0, 0): [(-q, -q), (-q, q), (q, -q), (q, q)],
    }
    for n, pips in faces.items():
        nv = Vector(n)
        a = Vector((1, 0, 0)) if abs(nv.x) < 0.5 else Vector((0, 1, 0))
        bb = nv.cross(a)
        for (u, v) in pips:
            c = nv * (h - r * 0.35) + a * u + bb * v
            parts.append(sphere("pip", r, tuple(c), "satin" if len(pips) != 1 else "oxblood", 16, 8))
    T = Matrix.Translation(loc) @ Matrix.Rotation(rot[2], 4, "Z") @ Matrix.Rotation(rot[1], 4, "Y") @ Matrix.Rotation(rot[0], 4, "X")
    xform(parts, T)
    return parts


def m_dice():
    """Two dice keep tumbling on a felt tray — income 'at an uncertain price'."""
    rig = Rig()
    s = 0.36
    m = rig.mark()
    die("d1", s, (-0.24, 0.06, s / 2 + 0.06), (0, 0, math.radians(18)))
    rig.take(m, "d1", head=(-0.24, 0.06, s / 2 + 0.06))
    m = rig.mark()
    die("d2", s, (0.26, -0.10, s / 2 + 0.06), (0, 0, math.radians(-28)))
    rig.take(m, "d2", head=(0.26, -0.10, s / 2 + 0.06))
    # felt tray + stake coins
    box("tray", (1.30, 0.86, 0.06), (0, 0, 0.03), "walnut", 0.02)
    box("felt", (1.18, 0.74, 0.012), (0, 0, 0.061), "green", 0.004)
    random.seed(9)
    for i in range(4):
        coin("stake", (0.42, 0.22, 0.08 + i * 0.026), (0, 0, random.uniform(0, 6)), r=0.075, t=0.026)
    coin("stake", (0.30, 0.28, 0.08), (math.radians(4), 0, 1), r=0.075, t=0.026)
    m = rig.mark()
    coin("spinner", (-0.40, -0.24, 0.067 + 0.078), (math.radians(90), 0, 0), r=0.078, t=0.024)
    rig.take(m, "spin", head=(-0.40, -0.24, 0.067))
    rig.shift(dz=-0.25)
    a1 = Vector((math.cos(math.radians(18)), math.sin(math.radians(18)), 0))
    a2 = Vector((-math.sin(math.radians(-28)), math.cos(math.radians(-28)), 0))

    def roll(t, ph, nh=4):
        u = (t * nh + ph) % nh
        k, f = int(u), u - int(u)
        q = clamp01(f / 0.62)  # airborne 62% of each hop, then rests
        return 90 * (k + smooth(q)), 0.20 * hop(q)

    def anim(t):
        r1, z1 = roll(t, 0.0)
        r2, z2 = roll(t, 0.5)
        return {"d1": {"loc": (0, 0, z1), "rot": [(tuple(a1), -r1)]},
                "d2": {"loc": (0, 0, z2), "rot": [(tuple(a2), r2)]},
                "spin": {"rot": [((1, 0, 0), 7 * math.sin(TAU * 3 * t)), ((0, 0, 1), 360 * 4 * t)]}}
    return rig, anim, 4.0


def m_scales():
    """Balance: certain coins against a floating die; the beam searches for equilibrium."""
    rig = Rig()
    lathe("base", [(0, 0), (0.36, 0), (0.37, 0.02), (0.34, 0.06), (0.22, 0.09), (0.12, 0.11), (0, 0.11)], "walnut", 72)
    lathe("pillar", [(0, 0.10), (0.06, 0.10), (0.05, 0.16), (0.035, 0.22), (0.03, 0.95), (0.045, 0.98), (0.03, 1.02), (0, 1.02)],
          "brass", 40)
    sphere("finial", 0.045, (0, 0, 1.12), "brass", 24, 12)
    L = 0.62
    piv = Vector((0, 0, 1.02))
    m = rig.mark()
    endL, endR = piv - Vector((L, 0, 0)), piv + Vector((L, 0, 0))
    tube("beam", [tuple(endL), tuple(piv + Vector((0, 0, 0.03))), tuple(endR)], 0.018, "gold", 4)
    sphere("pivot", 0.04, tuple(piv), "brass", 24, 12)
    for e in (endL, endR):
        sphere("end", 0.025, tuple(e), "brass", 16, 8)
    # pointer needle
    tube("pointer", [tuple(piv), tuple(piv + Vector((0, -0.005, 0.20)))], 0.007, "oxblood", 2, False)
    rig.take(m, "beam", head=tuple(piv))
    box("dialplate", (0.16, 0.012, 0.05), (0, -0.03, 1.27), "brass_d", 0.004)
    for e, name in ((endL, "L"), (endR, "R")):
        pan_c = e - Vector((0, 0, 0.52))
        m = rig.mark()
        lathe("pan" + name, [(0, 0.0), (0.12, 0.0), (0.20, 0.035), (0.22, 0.06), (0.215, 0.065), (0.19, 0.04), (0.11, 0.008), (0, 0.008)],
              "brass", 64, 40, loc=tuple(pan_c))
        for k in range(3):
            a = TAU * k / 3 + 0.5
            tube("chain", [tuple(e), tuple(pan_c + Vector((0.21 * math.cos(a), 0.21 * math.sin(a), 0.06)))], 0.0035, "steel", 2, False)
        if name == "L":
            for i in range(5):
                coin("coin", tuple(pan_c + Vector((0.0, 0.0, 0.03 + i * 0.03))), (0, 0, i * 1.3), r=0.09, t=0.03)
        rig.take(m, "pan" + name, head=tuple(e), parent="beam")
        if name == "R":
            m = rig.mark()
            die("pd", 0.15, tuple(pan_c + Vector((0, 0, 0.17))), (0, 0, 0))
            rig.take(m, "pdie", head=tuple(pan_c + Vector((0, 0, 0.17))), parent="panR")
    rig.shift(dz=-0.55)

    def beam_angle(t):
        return 7.0 * wave(t, 1, 0) + 1.6 * wave(t, 3, 0.2)

    def anim(t):
        b = beam_angle(t)
        lag = 2.2 * wave(t, 1, -0.12)
        return {"beam": {"rot": [((0, 1, 0), b)]},
                "panL": {"rot": [((0, 1, 0), -b + lag)]},
                "panR": {"rot": [((0, 1, 0), -b + lag)]},
                "pdie": {"rot": [((1, 0, 0), 360 * t), ((0, 0, 1), 360 * t)], "loc": (0, 0, 0.03 * wave(t, 2, 0))}}
    return rig, anim, 4.0


def m_ripple():
    """A coin drops into water — splash crown and rings run outwards: the Cantillon effect."""
    rig = Rig()
    R = 0.62
    lathe("bowl", [(0, -0.10), (R * 0.85, -0.10), (R, -0.06), (R + 0.04, 0.03), (R + 0.06, 0.05), (R + 0.04, 0.065), (R, 0.04),
                   (R * 0.86, -0.06), (0, -0.07)], "brass", 96, 40)
    NR, NA = 40, 96
    verts, faces = [(0, 0, 0.010)], []
    for i in range(1, NR + 1):
        r = R * 0.985 * i / NR
        for j in range(NA):
            a = TAU * j / NA
            z = 0.006 * math.cos(r * 30) * math.exp(-r * 3.0) + 0.006
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for j in range(NA):
        faces.append((0, 1 + j, 1 + (j + 1) % NA))
    for i in range(NR - 1):
        for j in range(NA):
            a = 1 + i * NA + j
            b = 1 + i * NA + (j + 1) % NA
            faces.append((a, a + NA, b + NA, b))
    finish(mesh_obj("water", verts, faces), "water", 80)
    # expanding rings (bones scale them out; they flatten away near the rim)
    for k in range(4):
        m = rig.mark()
        torus("ring", 0.10, 0.0036, (0, 0, 0.014), "paper", seg=72, mseg=6)
        rig.take(m, f"ring{k}", head=(0, 0, 0.014))
    # splash crown
    m = rig.mark()
    for k in range(12):
        a = TAU * k / 12
        s = sphere("drop", 0.016, (0.06 * math.cos(a), 0.06 * math.sin(a), 0.05 + 0.02 * (k % 3)), "chrome", 12, 6)
        s.scale = (1, 1, 1.6)
    lathe("column", [(0, 0.0), (0.03, 0.0), (0.018, 0.06), (0.012, 0.10), (0, 0.13)], "chrome", 24, 60)
    rig.take(m, "splash", head=(0, 0, 0.01))
    m = rig.mark()
    coin("coin", (0.0, 0.0, 0.42), (math.radians(70), 0, 0), r=0.12, t=0.024)
    rig.take(m, "coin", head=(0, 0, 0.42))
    rig.shift(dz=-0.12)
    HIT = 0.22

    def anim(t):
        p = {}
        if t < HIT:
            q = t / HIT
            z = -0.40 * q * q
            sc = ease(t, 0.0, 0.035)
        else:
            q = clamp01((t - HIT) / 0.12)
            z = -0.40 - 0.10 * smooth(q)
            sc = 1 - ease(t, 0.36, 0.42)
        p["coin"] = {"loc": (0, 0, z), "rot": [((1, 0, 0), 520 * min(t, HIT) / HIT)], "scale": max(sc, 0.001)}
        sq = clamp01((t - HIT) / 0.16)
        p["splash"] = {"scale": (1 + 0.6 * sq, 1 + 0.6 * sq, max(0.001, math.sin(math.pi * sq) * 1.4)), "loc": (0, 0, 0)}
        for k in range(4):
            s0 = HIT + 0.02 + 0.11 * k
            q = (t - s0) / 0.55
            if q <= 0 or q >= 1:
                p[f"ring{k}"] = {"scale": 0.001}
            else:
                r = 0.4 + 5.3 * (1 - (1 - q) ** 1.6)
                p[f"ring{k}"] = {"scale": (r, r, max(0.001, 1.0 - q ** 2))}
        return p
    # start the loop mid-way (rings already running): frame 0 is also PowerPoint's poster / fallback image
    return rig, (lambda t: anim((t + 0.42) % 1.0)), 4.0


def m_compass():
    """Pocket compass: a jolt — the needle swings, overshoots and settles on north."""
    rig = Rig()
    Rr, h = 0.5, 0.10
    m = rig.mark()
    lathe("case", [(0, -h), (Rr - 0.02, -h), (Rr, -h + 0.02), (Rr + 0.01, 0), (Rr, h - 0.01), (Rr - 0.03, h), (Rr - 0.05, h - 0.005),
                   (Rr - 0.05, 0.02), (0, 0.02)], "brass", 96, 40)
    lathe("dial", [(0, 0.021), (Rr - 0.05, 0.021)], "ivory", 72)
    for k in range(32):
        a = TAU * k / 32
        long = k % 8 == 0
        Ln = 0.07 if long else (0.045 if k % 4 == 0 else 0.03)
        rr = Rr - 0.09 - Ln / 2
        box("tick", (Ln, 0.008 if not long else 0.014, 0.003), (rr * math.cos(a), rr * math.sin(a), 0.024), "satin", 0, rot=(0, 0, a))
    torus("dialring", Rr - 0.16, 0.004, (0, 0, 0.024), "brass_d", seg=72, mseg=4)
    for txt, a in (("N", 90), ("E", 0), ("S", -90), ("W", 180)):
        rr = Rr - 0.22
        text_mesh("lt" + txt, txt, 0.07, 0.003, "ember" if txt == "N" else "satin",
                  loc=(rr * math.cos(math.radians(a)), rr * math.sin(math.radians(a)), 0.025), rot=(0, 0, math.radians(a - 90)), res=3)
    # compass rose star
    for k in range(8):
        a = TAU * k / 8 + math.pi / 2
        Lr = 0.15 if k % 2 == 0 else 0.09
        d = Vector((math.cos(a), math.sin(a), 0)); pp = Vector((-d.y, d.x, 0))
        o = mesh_obj("rose", [(0, 0, 0.0235), tuple(pp * 0.022 + Vector((0, 0, 0.0235))), tuple(d * Lr + Vector((0, 0, 0.0235))),
                              tuple(-pp * 0.022 + Vector((0, 0, 0.0235)))], [(0, 1, 2), (0, 2, 3)])
        finish(o, "brass_d" if k % 2 else "gold", 0)
    lathe("glass", [(0, 0.075), (Rr - 0.04, 0.07)], "glass", 72)
    cyl("crown", 0.04, 0.08, (0, Rr + 0.04, 0), "brass", rot=(math.radians(90), 0, 0), seg=24)
    torus("bow", 0.09, 0.016, (0, Rr + 0.15, 0), "brass", rot=(0, math.radians(90), 0), seg=32, mseg=8)
    rig.take(m, "body", head=(0, 0, 0))
    m = rig.mark()
    an = math.radians(90)
    dn = Vector((math.cos(an), math.sin(an), 0)); pn = Vector((-dn.y, dn.x, 0))
    for sgn, mat in ((1, "oxblood"), (-1, "steel")):
        tip = dn * (0.30 * sgn)
        verts = [(0, 0, 0.044), tuple(pn * 0.03 + Vector((0, 0, 0.038))), tuple(tip + Vector((0, 0, 0.036))), tuple(-pn * 0.03 + Vector((0, 0, 0.038))),
                 (0, 0, 0.032)]
        finish(mesh_obj("needle", verts, [(0, 1, 2), (0, 2, 3), (4, 2, 1), (4, 3, 2)]), mat, 0)
    cyl("pin", 0.018, 0.03, (0, 0, 0.045), "brass", seg=16)
    rig.take(m, "needle", head=(0, 0, 0.04), parent="body")
    rig.rotate(rx=62)

    def anim(t):
        jolt = 5.0 * math.sin(TAU * 10 * t) * math.exp(-t / 0.035) * (t < 0.15)
        off = 75 * (1 - math.exp(-t / 0.015)) * math.exp(-t / 0.20) * math.cos(TAU * 3.2 * t)
        off *= 1 - ease(t, 0.93, 1.0)
        return {"body": {"rot": [((0, 1, 0), jolt), ((1, 0, 0), 0.6 * jolt)]},
                "needle": {"rot": [((0, 0, 1), off)]}}
    return rig, anim, 4.0


def m_candle():
    """Chamberstick: the flame flickers and sways, a wax drop crawls down — the night of 14 May 1734."""
    rig = Rig()
    lathe("pan", [(0, 0), (0.30, 0), (0.33, 0.015), (0.34, 0.045), (0.32, 0.05), (0.29, 0.025), (0.06, 0.02), (0, 0.02)], "brass", 80)
    lathe("socket", [(0, 0.02), (0.07, 0.02), (0.09, 0.05), (0.075, 0.08), (0.085, 0.16), (0.11, 0.18), (0.10, 0.20), (0.075, 0.19), (0, 0.19)],
          "brass", 64)
    torus("handle", 0.075, 0.016, (0.40, 0, 0.11), "brass", rot=(math.radians(90), 0, 0), seg=40, mseg=8)
    box("handlebar", (0.10, 0.03, 0.012), (0.32, 0, 0.04), "brass", 0.004)
    hc = 0.62
    prof = [(0, 0.18), (0.068, 0.18)]
    for i in range(1, 12):
        prof.append((0.068 - 0.002 * math.sin(i), 0.18 + hc * i / 11))
    prof += [(0.062, 0.18 + hc + 0.01), (0.04, 0.18 + hc - 0.01), (0, 0.18 + hc - 0.015)]
    lathe("candle", prof, "wax", 48, 50)
    random.seed(5)
    for k in range(5):
        a = random.uniform(0, TAU)
        ln = random.uniform(0.08, 0.22)
        s = sphere("drip", 0.016, (0.067 * math.cos(a), 0.067 * math.sin(a), 0.18 + hc - 0.01 - ln / 2), "wax", 16, 10)
        s.scale = (1, 1, ln / 0.032)
    tube("wick", [(0, 0, 0.18 + hc - 0.02), (0.004, 0, 0.18 + hc + 0.04), (0.012, 0, 0.18 + hc + 0.07)], 0.004, "satin", 2)
    fz = 0.18 + hc + 0.035
    m = rig.mark()
    lathe("flame", [(0, fz), (0.024, fz + 0.02), (0.033, fz + 0.06), (0.026, fz + 0.11), (0.013, fz + 0.16), (0, fz + 0.21)], "flame", 32, 80)
    rig.take(m, "flame", head=(0, 0, fz))
    m = rig.mark()
    lathe("core", [(0, fz + 0.005), (0.012, fz + 0.02), (0.016, fz + 0.045), (0.010, fz + 0.075), (0, fz + 0.10)], "glow", 24, 80)
    rig.take(m, "core", head=(0, 0, fz), parent="flame")
    # a fresh wax drop that crawls down the candle
    a = math.radians(-70)
    m = rig.mark()
    s = sphere("newdrip", 0.017, (0.069 * math.cos(a), 0.069 * math.sin(a), 0.18 + hc - 0.02), "wax", 16, 10)
    s.scale = (1, 1, 1.5)
    rig.take(m, "drop", head=(0.069 * math.cos(a), 0.069 * math.sin(a), 0.18 + hc - 0.02))
    for k in range(3):
        sz = fz + 0.235
        rig.bone(f"smoke{k}", (0, 0, sz))
        m = rig.mark()
        sphere("smoke", 0.046, (0, 0, sz + 0.02), "concrete", 16, 10).scale = (1, 1, 1.3)
        rig.take(m, f"smoke{k}")
    flyer(rig, "moth", (0.0, 0.0), 0.20, fz + 0.09, 0.09, 0.075, 0.019, "brown", "sand", moth=True)
    rig.shift(dz=-0.5)

    def noise(t, seeds):
        return sum(A * math.sin(TAU * (k * t + ph)) for A, k, ph in seeds)

    def anim(t):
        n1 = noise(t, [(0.5, 3, 0.1), (0.3, 7, 0.6), (0.2, 13, 0.3)])
        n2 = noise(t, [(0.5, 5, 0.4), (0.35, 11, 0.2), (0.15, 17, 0.8)])
        sway = noise(t, [(4.0, 2, 0.0), (2.5, 5, 0.3)])
        d = clamp01(t / 0.85)
        return {"flame": {"scale": (1 + 0.07 * n1, 1 + 0.07 * n1, 1 + 0.16 * n2),
                          "rot": [((1, 0, 0), sway), ((0, 1, 0), 0.7 * noise(t, [(4.0, 3, 0.5), (2.0, 7, 0.1)]))]},
                "core": {"scale": (1, 1, 1 + 0.12 * noise(t, [(0.6, 9, 0.2), (0.4, 15, 0.7)]))},
                "drop": {"loc": (0, 0, -0.30 * smooth(d)), "scale": (1, 1, 1 + 0.8 * math.sin(math.pi * d)) if t < 0.92 else 0.001},
                **{f"smoke{k}": puff_pose(t, k, 3, 0.20, 0.025, 0.9) for k in range(3)},
                **flyer_pose("moth", t, turns=2, flaps=24, amp=40, bob=0.035, bob_k=3)}
    return rig, anim, 4.0


MODELS = {
    "louis": m_louis, "ship": m_ship, "harp": m_harp, "chest": m_chest, "bubble": m_bubble, "rook": m_rook,
    "quill": m_quill, "dice": m_dice, "scales": m_scales, "bread": m_bread, "ripple": m_ripple, "compass": m_compass,
    "candle": m_candle, "globe_c": m_globe_c,
}

if __name__ == "__main__":
    want = [a for a in sys.argv[1:] if a in MODELS] or list(MODELS)
    for key in want:
        mm.reset()
        mm._mats.clear()
        res = MODELS[key]()
        if res:
            export_rigged(key, *res)
        else:
            mm.export(key)
