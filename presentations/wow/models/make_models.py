# Brand-new animated exhibits for the WOW deck (Blender / bpy -> .glb for PowerPoint 3D).
# Three models that exist in no other collection:
#   lighthouse — stormy sea, rock island, striped tower, rotating twin light beams, gull
#   carousel   — spinning ride, three horses galloping in phase shift, glowing bulbs
#   tornado    — sheared rotating funnel, orbiting debris, dust ring, flashing lightning
#
#   python3 models/make_models.py                  -> models/glb/*.glb   (all models)
#   python3 models/make_models.py lighthouse       -> only selected models
#
# Convention: Blender Z up, the viewer looks from -Y.
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "schumpeter", "models"))
sys.path.append(os.path.join(HERE, "..", "..", "cantillon", "models"))  # rig.py (append: never shadow schumpeter)
import make_models as mm  # noqa: E402
from make_models import (bpy, bmesh, Vector, Matrix, TAU, M, finish, mesh_obj, lathe, box, cyl,  # noqa: E402
                         sphere, torus, tube)
from rig import Rig, export_rigged, clamp01, smooth, ease, pulse, back_out, hop, wave  # noqa: E402

mm.OUT = os.path.join(HERE, "glb")
os.makedirs(mm.OUT, exist_ok=True)


# ------------------------------------------------------------------ local helpers
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


def emit_alpha(name, base, alpha, emit, es):
    """Translucent glowing material (light beams, lightning): Principled + alpha + emission."""
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Roughness"].default_value = 0.6
    b.inputs["Alpha"].default_value = alpha
    b.inputs["Emission Color"].default_value = (*emit, 1)
    b.inputs["Emission Strength"].default_value = es
    m.surface_render_method = "BLENDED"
    m.use_backface_culling = False
    return m


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
    """Looping smoke / dust particle: rises, grows, fades out (scale 0 at both ends of its life)."""
    u = (t + k / n) % 1.0
    sc = max(0.001, math.sin(math.pi * u) * (0.5 + 0.8 * u) * size)
    return {"loc": (drift * math.sin(TAU * u + k), 0, rise * u), "scale": sc}


def sea_slab(rig, X0, X1, Y0, Y1, ZS, ZB, foam_n=18, seed=3):
    """Skirted water slab carried by 8 wave bones (travelling swell) + foam crests. Returns wxs."""
    nu, nv = 64, 20

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
    m = rig.mark()
    grid_surface("sea", nu, nv, sea, "water", 50)
    random.seed(seed)
    for k in range(foam_n):
        x = random.uniform(X0 + 0.08, X1 - 0.08); y = random.choice((-1, 1)) * random.uniform(0.28, 0.42)
        f = sphere("foam", 0.022, (x, y, ZS + 0.006), "paper", 10, 5)
        f.scale = (2.4, 0.9, 0.35)

    def sea_w(co):
        if co.z < ZB + 0.01:
            return {"root": 1.0}
        return {f"wave{k}": math.exp(-((co.x - x) / 0.26) ** 2) for k, x in enumerate(wxs)}
    rig.take_fn(m, "sea", sea_w)
    return wxs


# ------------------------------------------------------------------ 1. lighthouse
def m_lighthouse():
    """A lighthouse on a rock island in a stormy sea: twin beams sweep the horizon (2 turns
    per loop), waves run, the lamp breathes, a gull circles the tower."""
    rig = Rig()
    # sea + plinth + island rock
    X0, X1, Y0, Y1, ZS, ZB = -1.05, 1.05, -0.42, 0.42, 0.06, 0.0
    wxs = sea_slab(rig, X0, X1, Y0, Y1, ZS, ZB)
    m = rig.mark()
    box("plinth", (X1 - X0 + 0.12, Y1 - Y0 + 0.12, 0.09), ((X0 + X1) / 2, 0, ZB - 0.045), "walnut", 0.015)
    box("plate", (0.46, 0.008, 0.05), ((X0 + X1) / 2, Y0 - 0.064, ZB - 0.045), "brass", 0.003)
    lathe("island", [(0.44, 0.0), (0.40, 0.06), (0.34, 0.14), (0.30, 0.20), (0.28, 0.22), (0, 0.22)], "stone", 56, 40)
    for sx, sy, sr, sz in ((-0.68, 0.12, 0.10, 0.7), (0.72, -0.08, 0.085, 0.6), (0.34, 0.33, 0.06, 0.5)):
        s = sphere("skerry", sr, (sx, sy, ZS - 0.01), "stone", 14, 8)
        s.scale = (1, 0.8, sz)
    rig.take(m, "root")
    # striped tower: 5 tapering bands
    z0, bh = 0.22, 0.16
    r0, r1 = 0.150, 0.105
    bands = ["red", "whitestone", "red", "whitestone", "red"]
    for k in range(5):
        ra = r0 + (r1 - r0) * k / 5
        rb = r0 + (r1 - r0) * (k + 1) / 5
        lathe(f"band{k}", [(ra, z0 + bh * k), (rb, z0 + bh * (k + 1))], bands[k], 48, 50)
    zt = z0 + bh * 5  # 1.02 — tower top
    cyl("gallery", 0.170, 0.030, (0, 0, zt + 0.015), "iron", seg=48)
    for rz in (zt + 0.095, zt + 0.150):
        torus("rail", 0.150, 0.006, (0, 0, rz), "iron", seg=48, mseg=8)
    for k in range(8):
        a = TAU * k / 8
        cyl("post", 0.005, 0.150, (0.150 * math.cos(a), 0.150 * math.sin(a), zt + 0.105), "iron", seg=8)
    # door + lit windows on the front
    box("door", (0.095, 0.025, 0.170), (0, -0.138, z0 + 0.085), "walnut", 0.008)
    sphere("knob", 0.010, (0.028, -0.152, z0 + 0.085), "brass", 10, 6)
    for wz in (z0 + 0.33, z0 + 0.58):
        rw = r0 + (r1 - r0) * (wz - z0) / (bh * 5)
        box("win", (0.050, 0.020, 0.070), (0, -rw + 0.002, wz), "window", 0.005)
    # lamp room: glass, glowing lamp (own bone: it breathes), pedestal, cap roof
    lz = zt + 0.115
    cyl("lampglass", 0.075, 0.160, (0, 0, lz), "glass", seg=32)
    cyl("lampmast", 0.016, 0.160, (0, 0, lz), "brass_d", seg=12)
    lathe("lamproot", [(0.115, lz + 0.080), (0.10, lz + 0.095), (0.045, lz + 0.170), (0.012, lz + 0.195), (0, lz + 0.200)],
          "red", 48, 50)
    sphere("finial", 0.020, (0, 0, lz + 0.210), "brass", 12, 8)
    m = rig.mark()
    sphere("lamp", 0.036, (0, 0, lz), "flame", 20, 12)
    rig.take(m, "lamp", head=(0, 0, lz))
    # twin light beams: translucent glowing cones, rigid on one rotating bone
    beam_mat = emit_alpha("beam", (1.0, 0.95, 0.82), 0.22, (1.0, 0.88, 0.64), 3.0)
    core_mat = emit_alpha("beamcore", (1.0, 0.98, 0.92), 1.0, (1.0, 0.96, 0.86), 8.0)
    m = rig.mark()
    for bn, ry in (("beamA", 90), ("beamB", -90)):
        o = lathe(bn, [(0.028, 0), (0.125, 0.78), (0, 0.78)], beam_mat, 32, 80)
        o.rotation_euler = (0, math.radians(ry), 0)
        o.location = (0, 0, lz)
        c = lathe(bn + "core", [(0.020, 0.02), (0.052, 0.70), (0, 0.70)], core_mat, 20, 80)
        c.rotation_euler = (0, math.radians(ry), 0)
        c.location = (0, 0, lz)
    rig.take(m, "beam", head=(0, 0, lz))
    flyer(rig, "gull", (0.0, 0.0), 0.52, 1.52, 0.24, 0.10, 0.032, "paper", "paper", tip_mat="satin")
    rig.shift(dz=-0.72)
    LAM = 1.5

    def anim(t):
        p = {f"wave{k}": {"loc": (0, 0, 0.036 * wave(t, 1, -x / LAM))} for k, x in enumerate(wxs)}
        p["beam"] = {"rot": [((0, 0, 1), 720 * t)]}
        p["lamp"] = {"scale": 1 + 0.06 * wave(t, 2, 0.25)}
        p.update(flyer_pose("gull", t, turns=1, flaps=12, amp=34, bob=0.05, bob_k=2,
                             glide=(0.30, 0.38, 0.55, 0.62)))
        return p
    return rig, anim, 6.0


# ------------------------------------------------------------------ 2. carousel
def horse_parts(body_mat, blanket_mat):
    """A stylised galloping horse facing +X, centred near the origin (~0.36 long)."""
    sphere("body", 0.075, (0, 0, 0), body_mat, 20, 12).scale = (1.5, 0.85, 0.95)
    sphere("chest", 0.060, (0.090, 0, 0.010), body_mat, 16, 10)
    sphere("rump", 0.062, (-0.090, 0, 0.015), body_mat, 16, 10)
    cyl("neck", 0.035, 0.160, (0.130, 0, 0.090), body_mat, rot=(0, math.radians(30), 0), seg=16)
    box("head", (0.100, 0.055, 0.060), (0.185, 0, 0.155), body_mat, 0.020, rot=(0, math.radians(25), 0))
    for s in (-1, 1):
        sphere("ear", 0.014, (0.155, s * 0.025, 0.200), body_mat, 8, 6).scale = (1, 1, 1.8)
    box("mane", (0.100, 0.020, 0.090), (0.100, 0, 0.145), blanket_mat, 0.008, rot=(0, math.radians(30), 0))
    # gallop legs: front pair reaches forward, back pair pushes back
    for lx, ry in ((0.085, -18), (-0.085, 22)):
        for s in (-1, 1):
            c = (lx, s * 0.040, -0.100)
            cyl("leg", 0.016, 0.160, c, body_mat, rot=(0, math.radians(ry), 0), seg=10)
            ex = c[0] + 0.080 * -math.sin(math.radians(ry))
            ez = c[2] + 0.080 * -math.cos(math.radians(ry))
            cyl("hoof", 0.019, 0.028, (ex, c[1], ez), "satin", rot=(0, math.radians(ry), 0), seg=10)
    tube("tail", [(-0.150, 0, 0.030), (-0.200, 0, -0.050), (-0.210, 0, -0.130)], 0.014, blanket_mat, 4)
    box("blanket", (0.120, 0.130, 0.020), (-0.010, 0, 0.075), blanket_mat, 0.008)
    box("saddle", (0.070, 0.090, 0.030), (-0.010, 0, 0.095), "gold", 0.010)


def m_carousel():
    """A fairground carousel: the whole ride turns (1 revolution per loop) while three horses
    gallop up and down in phase shift under a bulb-lit canopy."""
    rig = Rig()
    # static stepped plinth
    lathe("plinth", [(0, 0), (0.75, 0), (0.78, 0.04), (0.72, 0.05), (0.72, 0.09), (0, 0.09)], "walnut", 64, 40)
    # everything on the ride turns with the "spin" bone
    rig.bone("spin", (0, 0, 0.09))
    m = rig.mark()
    cyl("platform", 0.620, 0.050, (0, 0, 0.115), "red", seg=64)
    torus("rim", 0.620, 0.015, (0, 0, 0.115), "gold", seg=64, mseg=10)
    cyl("column", 0.110, 0.620, (0, 0, 0.450), "ivory", seg=32)
    for bz in (0.250, 0.650):
        torus("band", 0.110, 0.012, (0, 0, bz), "gold", seg=32, mseg=8)
    lathe("canopy", [(0.660, 0.800), (0.600, 0.840), (0.300, 1.020), (0.080, 1.120), (0, 1.140)], "red", 48, 50)
    torus("canopyrim", 0.640, 0.018, (0, 0, 0.810), "gold", seg=64, mseg=10)
    for k in range(14):
        a = TAU * k / 14
        sphere("bulb", 0.022, (0.600 * math.cos(a), 0.600 * math.sin(a), 0.800), "glow", 12, 8)
    sphere("finial", 0.040, (0, 0, 1.160), "gold", 16, 10)
    cyl("spike", 0.008, 0.090, (0, 0, 1.205), "gold", seg=8)
    angs = [90, 210, 330]
    for a in angs:
        r = math.radians(a)
        cyl("pole", 0.014, 0.660, (0.38 * math.cos(r), 0.38 * math.sin(r), 0.470), "brass", seg=12)
    rig.take(m, "spin")
    # three horses, each on its own bobbing bone parented to the spin
    horse_mats = [("whitestone", "oxblood"), ("walnut", "gold"), ("satin", "red")]
    for k, a in enumerate(angs):
        r = math.radians(a)
        pos = (0.38 * math.cos(r), 0.38 * math.sin(r), 0.420)
        m = rig.mark()
        horse_parts(*horse_mats[k])
        M4 = Matrix.Translation(pos) @ Matrix.Rotation(math.radians(a + 90), 4, "Z")
        for o in bpy.context.scene.objects:
            if o not in m:
                o.matrix_world = M4 @ o.matrix_world
        rig.take(m, f"h{k}", head=pos, parent="spin")
    rig.shift(dz=-0.60)

    def anim(t):
        p = {"spin": {"rot": [((0, 0, 1), 360 * t)]}}
        for k, a in enumerate(angs):
            r = math.radians(a)
            p[f"h{k}"] = {"loc": (0, 0, 0.055 * math.sin(TAU * t + k * TAU / 3)),
                          "rot": [((math.cos(r), math.sin(r), 0), 5 * math.sin(TAU * t + k * TAU / 3 - 0.5))]}
        return p
    return rig, anim, 6.0


# ------------------------------------------------------------------ 3. tornado
def wobble_frustum(o, seed):
    """Break the surface-of-revolution symmetry so the spin is visible: angular ripple."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for v in bm.verts:
        a = math.atan2(v.co.y, v.co.x)
        s = 1 + 0.055 * math.sin(3 * a + seed) + 0.030 * math.sin(7 * a + seed * 2.3)
        v.co.x *= s
        v.co.y *= s
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()


def m_tornado():
    """A tornado touching down: six funnel segments shear past each other, debris orbits,
    dust rises at the base, storm cloud churns above and lightning flashes twice per loop."""
    rig = Rig()
    # ground + a leaning fence
    cyl("ground", 0.800, 0.070, (0, 0, 0.035), "brown", seg=64)
    m = rig.mark()
    for k, (fx, lean) in enumerate([(-0.55, 0), (-0.35, 0), (-0.15, 14)]):
        box("post", (0.030, 0.030, 0.170), (fx, -0.55, 0.155), "walnut", 0.005, rot=(0, math.radians(lean), 0))
    box("rail", (0.440, 0.020, 0.030), (-0.35, -0.55, 0.200), "walnut", 0.005)
    rig.take(m, "root")
    # funnel: 6 overlapping frustums, each spins at its own integer speed
    speeds = [2, 3, 4, 4, 3, 2]
    z0, z1 = 0.10, 1.30

    def fr(z):
        u = clamp01((z - z0) / (z1 - z0))
        return 0.090 + (0.400 - 0.090) * u ** 1.3
    for k in range(6):
        za = z0 + (z1 - z0) * k / 6 - 0.012
        zb = z0 + (z1 - z0) * (k + 1) / 6 + 0.012
        zm = (za + zb) / 2
        m = rig.mark()
        o = lathe(f"fun{k}", [(fr(za), za), (fr(zm) * 1.02, zm), (fr(zb), zb)], "concrete", 36, 60)
        wobble_frustum(o, 1.7 * k + 0.4)
        rig.take(m, f"f{k}", head=(0, 0, zm))
    # churning storm cloud (asymmetric, so its spin reads)
    m = rig.mark()
    random.seed(11)
    for k in range(7):
        a = TAU * k / 7 + random.uniform(-0.2, 0.2)
        rr = 0.26 if k else 0.0
        s = sphere("cloud", random.uniform(0.13, 0.20), (rr * math.cos(a), rr * math.sin(a), 1.32 + random.uniform(-0.03, 0.05)),
                   "navy", 14, 10)
        s.scale = (1, 0.9, 0.55)
    rig.take(m, "cloud", head=(0, 0, 1.32))
    # orbiting debris on three rings
    rig.bone("o0", (0, 0, 0.35))
    rig.bone("o1", (0, 0, 0.65))
    rig.bone("o2", (0, 0, 0.95))
    debris = [
        ("o0", [("plank", (0.42, 0.35), (0.140, 0.030, 0.020), "walnut", 12),
                ("plank", (0.42, 0.35), (0.120, 0.026, 0.018), "brown", 150),
                ("barrel", (0.50, 0.35), None, None, 270)]),
        ("o1", [("tree", (0.45, 0.65), None, None, 30),
                ("plank", (0.48, 0.65), (0.150, 0.030, 0.020), "walnut", 200)]),
        ("o2", [("crate", (0.44, 0.95), (0.075, 0.075, 0.075), "brown", 90),
                ("barrel", (0.50, 0.95), None, None, 210),
                ("plank", (0.46, 0.95), (0.130, 0.028, 0.020), "walnut", 330)]),
    ]
    for bn, items in debris:
        m = rig.mark()
        for kind, (rr, zz), size, mat, adeg in items:
            a = math.radians(adeg)
            x, y = rr * math.cos(a), rr * math.sin(a)
            if kind == "plank":
                box("debris", size, (x, y, zz), mat, 0.004, rot=(math.radians(12), 0, math.radians(adeg + 40)))
            elif kind == "crate":
                box("debris", size, (x, y, zz), mat, 0.006, rot=(math.radians(-8), math.radians(15), math.radians(adeg)))
            elif kind == "barrel":
                lathe("debris", [(0.001, 0), (0.034, 0.0), (0.040, 0.04), (0.034, 0.08), (0.001, 0.08)], "brown", 20, 40,
                      loc=(x, y, zz - 0.04))
                torus("band", 0.036, 0.005, (x, y, zz + 0.025), "iron", seg=20, mseg=6)
            elif kind == "tree":
                cyl("trunk", 0.012, 0.090, (x, y, zz - 0.045), "walnut", seg=8)
                lathe("crown", [(0.055, 0), (0.030, 0.07), (0.0, 0.12)], "leaf", 16, 40, loc=(x, y, zz))
        rig.take(m, bn)
    # dust devils rising around the funnel base
    for k in range(3):
        a = TAU * k / 3
        dz = 0.10
        rig.bone(f"d{k}", (0.30 * math.cos(a), 0.30 * math.sin(a), dz))
        m = rig.mark()
        sphere("dust", 0.070, (0.30 * math.cos(a), 0.30 * math.sin(a), dz + 0.02), "sand", 14, 10).scale = (1, 1, 0.8)
        rig.take(m, f"d{k}")
    # lightning: jagged emissive bolt, flashed twice per loop
    bolt_mat = emit_alpha("bolt", (0.85, 0.92, 1.0), 0.9, (0.75, 0.88, 1.0), 8.0)
    m = rig.mark()
    tube("bolt", [(0.30, 0.05, 1.25), (0.22, 0.10, 1.02), (0.28, 0.02, 0.80), (0.16, 0.08, 0.55),
                  (0.22, -0.02, 0.30), (0.18, -0.05, 0.08)], 0.012, bolt_mat, 4, False)
    rig.take(m, "bolt", head=(0.25, 0.0, 0.80))
    rig.shift(dz=-0.70)

    def anim(t):
        p = {f"f{k}": {"rot": [((0, 0, 1), 360 * s * t)]} for k, s in enumerate(speeds)}
        p["cloud"] = {"rot": [((0, 0, 1), 360 * t)]}
        osp = [2, 3, 4]
        for k in range(3):
            p[f"o{k}"] = {"rot": [((0, 0, 1), 360 * osp[k] * t)],
                          "loc": (0, 0, 0.030 * wave(t, 2, 0.13 * k))}
        for k in range(3):
            p[f"d{k}"] = puff_pose(t, k, 3, 0.35, 0.06, 1.2)
        flash = pulse(t, 0.10, 0.115, 0.16, 0.175) + pulse(t, 0.60, 0.615, 0.66, 0.675)
        p["bolt"] = {"scale": 1.0 if flash > 0.5 else 0.001}
        return p
    return rig, anim, 5.0


MODELS = {
    "lighthouse": m_lighthouse, "carousel": m_carousel, "tornado": m_tornado,
}


if __name__ == "__main__":
    keys = sys.argv[1:] or list(MODELS)
    for key in keys:
        mm.reset()
        mm._mats.clear()
        res = MODELS[key]()
        if isinstance(res, tuple):
            export_rigged(key, *res)
        else:
            mm.export(key)