# Brand-new animated exhibits for the FUN one-slide deck (Blender / bpy -> .glb).
#   volcano  — erupting island diorama: lava fountain, smoke, dragon breathing fire, dancing 3D title
#   torch    — standing torch with flickering flame, smoke and embers (slide edges)
#   lavapool — bubbling lava pool (slide corners)
#
#   python3 models/make_models.py              -> models/glb/*.glb   (all models)
#   python3 models/make_models.py volcano      -> only selected models
#
# Convention: Blender Z up, the viewer looks from -Y.
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "schumpeter", "models"))
sys.path.append(os.path.join(HERE, "..", "..", "cantillon", "models"))  # rig.py (append: never shadow schumpeter)
import make_models as mm  # noqa: E402
from make_models import (bpy, bmesh, Vector, Matrix, TAU, M, finish, mesh_obj, lathe, box, cyl,  # noqa: E402
                         sphere, torus, tube, to_mesh)
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
    """Translucent glowing material (beams, fire, lava): Principled + alpha + emission."""
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


def puff_pose(t, k, n, rise, drift, size=1.0):
    """Looping particle: rises, grows, fades out (scale 0 at both ends of its life)."""
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
        x = random.uniform(X0 + 0.08, X1 - 0.08); y = random.choice((-1, 1)) * random.uniform(0.30, 0.44)
        f = sphere("foam", 0.022, (x, y, ZS + 0.006), "paper", 10, 5)
        f.scale = (2.4, 0.9, 0.35)

    def sea_w(co):
        if co.z < ZB + 0.01:
            return {"root": 1.0}
        return {f"wave{k}": math.exp(-((co.x - x) / 0.26) ** 2) for k, x in enumerate(wxs)}
    rig.take_fn(m, "sea", sea_w)
    return wxs


# ------------------------------------------------------------------ 1. volcano
def m_volcano():
    """Erupting volcanic island: lava fountain + smoke + embers, glowing flows and steam,
    swaying palms, a hut, a dragon circling the crater and breathing fire, and a dancing
    golden 3D title floating above it all."""
    rig = Rig()
    lava = emit_alpha("lava", (0.80, 0.20, 0.02), 1.0, (1.0, 0.28, 0.03), 1.35)
    lavabright = emit_alpha("lavabright", (0.90, 0.34, 0.05), 1.0, (1.0, 0.42, 0.06), 1.60)
    # sea + plinth
    X0, X1, Y0, Y1, ZS, ZB = -1.15, 1.15, -0.50, 0.50, 0.06, 0.0
    wxs = sea_slab(rig, X0, X1, Y0, Y1, ZS, ZB, foam_n=20, seed=7)
    m = rig.mark()
    box("plinth", (X1 - X0 + 0.12, Y1 - Y0 + 0.12, 0.09), ((X0 + X1) / 2, 0, ZB - 0.045), "walnut", 0.015)
    box("plate", (0.46, 0.008, 0.05), ((X0 + X1) / 2, Y0 - 0.064, ZB - 0.045), "brass", 0.003)
    # island cone with a crater bowl + sand beach ring
    lathe("island", [(0.62, 0), (0.58, 0.08), (0.50, 0.20), (0.40, 0.35), (0.31, 0.50), (0.24, 0.62),
                     (0.215, 0.68), (0.21, 0.72), (0.17, 0.72), (0.165, 0.66), (0, 0.66)], "stone", 56, 40)
    t = torus("beach", 0.640, 0.050, (0, 0, 0.050), "sand", seg=56, mseg=10)
    t.scale = (1, 1, 0.4)
    rig.take(m, "root")

    def cone_r(z):
        prof = [(0, 0.62), (0.08, 0.58), (0.20, 0.50), (0.35, 0.40), (0.50, 0.31), (0.62, 0.24), (0.70, 0.215)]
        for (z0, r0), (z1, r1) in zip(prof, prof[1:]):
            if z0 <= z <= z1:
                f = (z - z0) / (z1 - z0)
                return r0 + (r1 - r0) * f
        return 0.215
    # lava pool in the crater (breathes)
    m = rig.mark()
    cyl("pool", 0.155, 0.025, (0, 0, 0.665), lava, seg=40)
    rig.take(m, "pool", head=(0, 0, 0.66))
    # lava fountain: blobs + big bombs
    for k in range(6):
        rig.bone(f"f{k}", (0, 0, 0.70))
        m = rig.mark()
        sphere("fount", 0.041, (0, 0, 0.72), lavabright, 12, 8)
        rig.take(m, f"f{k}")
    for k in range(2):
        rig.bone(f"b{k}", (0, 0, 0.70))
        m = rig.mark()
        sphere("bomb", 0.058, (0, 0, 0.72), lava, 14, 10)
        rig.take(m, f"b{k}")
    # smoke column + high embers
    for k in range(3):
        rig.bone(f"s{k}", (0, 0, 1.02))
        m = rig.mark()
        sphere("smoke", 0.075, (0, 0, 1.04), "satin", 14, 10).scale = (1, 1, 1.2)
        rig.take(m, f"s{k}")
    for k in range(2):
        rig.bone(f"e{k}", (0.05 if k else -0.05, 0, 0.95))
        m = rig.mark()
        sphere("ember", 0.018, (0.05 if k else -0.05, 0, 0.97), lavabright, 10, 6)
        rig.take(m, f"e{k}")
    # glowing lava flows down the slopes (static) + steam where they meet the sea
    m = rig.mark()
    for adeg in (215, 250, 305):
        a = math.radians(adeg)
        c, s = math.cos(a), math.sin(a)
        pts = []
        for z in (0.70, 0.60, 0.48, 0.36, 0.24, 0.12, 0.065):
            r = cone_r(min(z, 0.70)) + 0.012
            pts.append((r * c, r * s, z))
        tube("flow", pts, 0.020, lava, 5)
    rig.take(m, "root")
    for k, adeg in enumerate((250, 305)):
        a = math.radians(adeg)
        px, py = 0.62 * math.cos(a), 0.62 * math.sin(a)
        rig.bone(f"st{k}", (px, py, 0.08))
        m = rig.mark()
        sphere("steam", 0.050, (px, py, 0.10), "paper", 12, 8)
        rig.take(m, f"st{k}")
    # swaying palms on the slopes
    for k, adeg in enumerate((140, 70, 20)):
        a = math.radians(adeg)
        bx, by = 0.44 * math.cos(a), 0.44 * math.sin(a)
        bz = 0.30
        m = rig.mark()
        tx, ty, tz = bx, by, bz
        lean = 0.10 + 0.03 * k
        for j in range(3):
            cyl("trunk", 0.022 - j * 0.003, 0.120, (tx, ty, tz + 0.060), "walnut", seg=10)
            tx += lean * 0.06 * math.cos(a + 1.2)
            ty += lean * 0.06 * math.sin(a + 1.2)
            tz += 0.115
        top = (tx, ty, tz)
        for j in range(7):
            ph = TAU * j / 7 + 0.3 * k

            def frond(u, v, ph=ph, top=top):
                dx, dy = math.cos(ph), math.sin(ph)
                px = top[0] + dx * 0.30 * u
                py = top[1] + dy * 0.30 * u
                pz = top[2] + 0.06 * math.sin(math.pi * u) - 0.16 * u * u
                w = (v - 0.5) * 0.090 * (1 - u * 0.7)
                return (px - dy * w, py + dx * w, pz)
            grid_surface("frond", 6, 2, frond, "leaf", 60)
        sphere("coco", 0.025, (top[0] + 0.03, top[1], top[2] - 0.03), "brown", 10, 6)
        sphere("coco", 0.025, (top[0] - 0.03, top[1] + 0.01, top[2] - 0.035), "brown", 10, 6)
        rig.take(m, f"palm{k}", head=(bx, by, bz))
    # a tiny hut on the beach (someone lives dangerously)
    m = rig.mark()
    ha = math.radians(190)
    hx, hy = 0.66 * math.cos(ha), 0.66 * math.sin(ha)
    box("hut", (0.170, 0.150, 0.110), (hx, hy, 0.115), "walnut", 0.008)
    box("roofL", (0.200, 0.100, 0.020), (hx, hy - 0.038, 0.200), "brown", 0.006, rot=(math.radians(35), 0, 0))
    box("roofR", (0.200, 0.100, 0.020), (hx, hy + 0.038, 0.200), "brown", 0.006, rot=(math.radians(-35), 0, 0))
    box("hutwin", (0.050, 0.012, 0.050), (hx - 0.040, hy - 0.078, 0.120), "window", 0.004)
    box("hutdoor", (0.045, 0.012, 0.085), (hx + 0.045, hy - 0.078, 0.103), "satin", 0.004)
    rig.take(m, "root")
    # THE DRAGON circling the crater
    DC = (0.0, 0.0)
    DR, DZ = 0.78, 1.62
    cx, cy, cz = DC[0] + DR, DC[1], DZ
    rig.bone("drag", (DC[0], DC[1], DZ))
    m = rig.mark()
    sphere("dbody", 0.055, (cx, cy, cz), "oxblood", 18, 12).scale = (0.85, 2.3, 0.85)
    cyl("dneck", 0.030, 0.140, (cx, cy + 0.100, cz + 0.070), "oxblood", rot=(math.radians(-35), 0, 0), seg=12)
    box("dhead", (0.075, 0.100, 0.060), (cx, cy + 0.170, cz + 0.130), "oxblood", 0.020)
    box("dsnout", (0.050, 0.070, 0.040), (cx, cy + 0.230, cz + 0.115), "oxblood", 0.015)
    for s in (-1, 1):
        lathe("dhorn", [(0.012, 0), (0.008, 0.030), (0, 0.055)], "ivory", 10, 30, loc=(cx + s * 0.030, cy + 0.140, cz + 0.160))
        sphere("deye", 0.011, (cx + s * 0.032, cy + 0.200, cz + 0.135), lavabright, 8, 6)
    for j, (oy, oz) in enumerate(((0.02, 0.045), (-0.03, 0.048), (-0.08, 0.042))):
        lathe("dspike", [(0.014, 0), (0, 0.040)], "satin", 8, 30, loc=(cx, cy + oy, cz + oz))
    rig.take(m, "drag")
    for side, bn in ((-1, "dragL"), (1, "dragR")):
        sh = (cx + side * 0.045, cy, cz + 0.020)
        rig.bone(bn, sh, "drag")
        m = rig.mark()

        def wing(u, v, side=side, sh=sh):
            x = sh[0] + side * 0.46 * u
            y = cy - 0.10 * u + 0.30 * (0.5 - v) * (1 - 0.55 * u)
            z = cz + 0.020 + 0.10 * 0.46 * math.sin(math.pi * min(u * 1.15, 1)) - 0.05 * v * max(0.0, math.sin(u * math.pi * 3.5)) ** 2
            return (x, y, z)
        grid_surface(bn, 10, 4, wing, "oxblood", 60)
        rig.take(m, bn)
    rig.bone("dragT", (cx, cy - 0.110, cz), "drag")
    m = rig.mark()
    cyl("dtail1", 0.028, 0.100, (cx, cy - 0.160, cz), "oxblood", rot=(math.radians(90), 0, 0), seg=12)
    cyl("dtail2", 0.020, 0.100, (cx, cy - 0.250, cz + 0.010), "oxblood", rot=(math.radians(90), 0, 0), seg=10)
    sp = lathe("dspade", [(0.035, 0), (0.028, 0.040), (0, 0.090)], "oxblood", 12, 40)
    sp.rotation_euler = (math.radians(-90), 0, 0)
    sp.location = (cx, cy - 0.300, cz + 0.010)
    sp.scale = (0.4, 1, 1)
    rig.take(m, "dragT")
    # dragon fire breath (flashes once per loop while gliding)
    fire_out = emit_alpha("fireout", (0.95, 0.45, 0.10), 0.25, (1.0, 0.42, 0.08), 1.60)
    fire_in = emit_alpha("firein", (1.0, 0.72, 0.25), 1.0, (1.0, 0.62, 0.15), 2.20)
    rig.bone("dragF", (cx, cy + 0.270, cz + 0.110), "drag")
    m = rig.mark()
    for fn, prof, mat, seg in (("fout", [(0.030, 0), (0.075, 0.22), (0, 0.22)], fire_out, 20),
                               ("fin", [(0.016, 0), (0.034, 0.16), (0, 0.16)], fire_in, 14)):
        o = lathe(fn, prof, mat, seg, 80)
        o.rotation_euler = (math.radians(-90), 0, 0)
        o.location = (cx, cy + 0.265, cz + 0.110)
    rig.take(m, "dragF")
    # dancing golden 3D title floating above the volcano
    word = "INFERNO"
    widths = {"I": 0.36, "N": 0.78, "F": 0.65, "E": 0.68, "R": 0.72, "O": 0.80}
    adv = [(widths[ch] + 0.18) * 0.30 for ch in word]
    total = sum(adv) - 0.18 * 0.30
    lx = -total / 2
    for k, ch in enumerate(word):
        w = widths[ch] * 0.30
        px = lx + w / 2
        lx += adv[k]
        m = rig.mark()
        text_mesh(f"L{k}", ch, 0.30, 0.06, "gold", loc=(px, 0.10, 2.02), rot=(math.radians(90), 0, 0), bevel=0.004)
        rig.take(m, f"L{k}", head=(px, 0.10, 2.02))
    rig.shift(dz=-1.00)
    LAM = 1.5

    def anim(t):
        p = {f"wave{k}": {"loc": (0, 0, 0.036 * wave(t, 1, -x / LAM))} for k, x in enumerate(wxs)}
        ps = 1 + 0.045 * wave(t, 2, 0.0)
        p["pool"] = {"scale": (ps, ps, 1)}
        for k in range(6):
            p[f"f{k}"] = puff_pose(t, k, 6, 0.55, 0.09, 1.0)
        for k in range(2):
            p[f"b{k}"] = puff_pose(t, k, 2, 0.80, 0.16, 1.5)
        for k in range(3):
            p[f"s{k}"] = puff_pose(t, k, 3, 0.55, 0.05, 1.9)
        for k in range(2):
            p[f"e{k}"] = puff_pose(t, k, 2, 0.85, 0.12, 0.6)
        for k in range(2):
            p[f"st{k}"] = puff_pose(t, k, 2, 0.22, 0.03, 0.9)
        for k in range(3):
            p[f"palm{k}"] = {"rot": [((1, 0, 0), 4.0 * wave(t, 1, 0.13 * k)), ((0, 1, 0), 3.0 * wave(t, 2, 0.21 * k))]}
        # dragon: one turn per loop, glides while breathing fire
        gl = 1 - pulse(t, 0.33, 0.38, 0.50, 0.55) * 0.85
        a = 40 * math.sin(TAU * 6 * t) * gl
        p["drag"] = {"rot": [((0, 0, 1), 360 * t)], "loc": (0, 0, 0.06 * wave(t, 2, 0.0))}
        p["dragL"] = {"rot": [((0, 1, 0), a)]}
        p["dragR"] = {"rot": [((0, 1, 0), -a)]}
        p["dragT"] = {"rot": [((0, 0, 1), 18 * wave(t, 3, 0.1))]}
        p["dragF"] = {"scale": 1.0 if pulse(t, 0.35, 0.38, 0.47, 0.50) > 0.5 else 0.001}
        for k in range(7):
            p[f"L{k}"] = {"loc": (0, 0, 0.045 * math.sin(TAU * 2 * t + k * 0.85))}
        return p
    return rig, anim, 6.0


# ------------------------------------------------------------------ 2. torch
def m_torch():
    """A standing torch: the flame flickers and sways, smoke and embers rise. Lives on slide edges."""
    rig = Rig()
    lathe("foot", [(0, 0), (0.120, 0), (0.130, 0.020), (0.100, 0.035), (0, 0.035)], "stone", 32, 40)
    cyl("pole", 0.025, 0.620, (0, 0, 0.370), "iron", seg=16)
    torus("collar", 0.028, 0.010, (0, 0, 0.560), "brass_d", seg=16, mseg=8)
    lathe("bowl", [(0.020, 0.680), (0.090, 0.680), (0.110, 0.730), (0.100, 0.750), (0.070, 0.730), (0, 0.730)],
          "brass_d", 32, 40)
    for k, (ox, oy) in enumerate(((0.035, 0.010), (-0.030, 0.025), (0.005, -0.035))):
        sphere("coal", 0.022, (ox, oy, 0.735), "ember", 10, 6)
    m = rig.mark()
    lathe("flame", [(0, 0.750), (0.030, 0.780), (0.038, 0.830), (0.028, 0.890), (0.012, 0.950), (0, 1.000)],
          "flame", 24, 80)
    rig.take(m, "flame", head=(0, 0, 0.750))
    m = rig.mark()
    lathe("core", [(0, 0.755), (0.014, 0.775), (0.017, 0.810), (0.010, 0.850), (0, 0.880)], "glow", 16, 80)
    rig.take(m, "core", head=(0, 0, 0.755), parent="flame")
    for k in range(2):
        rig.bone(f"s{k}", (0, 0, 1.020))
        m = rig.mark()
        sphere("smoke", 0.045, (0, 0, 1.040), "concrete", 12, 8).scale = (1, 1, 1.25)
        rig.take(m, f"s{k}")
    for k in range(2):
        rig.bone(f"e{k}", (0, 0, 0.950))
        m = rig.mark()
        sphere("ember", 0.014, (0, 0, 0.970), "ember", 8, 6)
        rig.take(m, f"e{k}")
    rig.shift(dz=-0.500)

    def noise(t, seeds):
        return sum(A * math.sin(TAU * (k * t + ph)) for A, k, ph in seeds)

    def anim(t):
        n1 = noise(t, [(0.5, 3, 0.1), (0.3, 7, 0.6), (0.2, 13, 0.3)])
        n2 = noise(t, [(0.5, 5, 0.4), (0.35, 11, 0.2), (0.15, 17, 0.8)])
        sway = noise(t, [(4.0, 2, 0.0), (2.5, 5, 0.3)])
        return {"flame": {"scale": (1 + 0.07 * n1, 1 + 0.07 * n1, 1 + 0.16 * n2),
                          "rot": [((1, 0, 0), sway), ((0, 1, 0), 0.7 * sway)]},
                "core": {"scale": (1, 1, 1 + 0.12 * noise(t, [(0.6, 9, 0.2), (0.4, 15, 0.7)]))},
                **{f"s{k}": puff_pose(t, k, 2, 0.30, 0.020, 1.0) for k in range(2)},
                **{f"e{k}": puff_pose(t, k, 2, 0.45, 0.030, 0.5) for k in range(2)}}
    return rig, anim, 4.0


# ------------------------------------------------------------------ 3. lavapool
def m_lavapool():
    """A bubbling lava pool in a rock rim: the surface breathes, blobs grow and pop."""
    rig = Rig()
    lava = emit_alpha("lava2", (0.85, 0.22, 0.03), 1.0, (1.0, 0.30, 0.04), 1.35)
    lathe("rim", [(0.300, 0), (0.320, 0.040), (0.300, 0.080), (0.240, 0.080), (0.240, 0.050), (0, 0.050)],
          "stone", 40, 40)
    m = rig.mark()
    cyl("surface", 0.230, 0.020, (0, 0, 0.060), lava, seg=40)
    rig.take(m, "lava", head=(0, 0, 0.060))
    for k in range(3):
        a = TAU * k / 3 + 0.5
        px, py = 0.120 * math.cos(a), 0.120 * math.sin(a)
        rig.bone(f"bb{k}", (px, py, 0.070))
        m = rig.mark()
        sphere("blob", 0.045, (px, py, 0.075), lava, 12, 8)
        rig.take(m, f"bb{k}")

    def anim(t):
        ps = 1 + 0.03 * wave(t, 2, 0.0)
        p = {"lava": {"scale": (ps, ps, 1)}}
        for k in range(3):
            u = (t + k / 3) % 1.0
            sc = max(0.15, math.sin(math.pi * min(u * 1.15, 1.0)))
            p[f"bb{k}"] = {"scale": (sc, sc, sc), "loc": (0, 0, 0.030 * sc)}
        return p
    return rig, anim, 4.0


MODELS = {
    "volcano": m_volcano, "torch": m_torch, "lavapool": m_lavapool,
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