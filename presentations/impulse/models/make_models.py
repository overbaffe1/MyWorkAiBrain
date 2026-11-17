# Procedural 3D exhibits for the "Психология импульсивных трат" deck (Blender / bpy -> .glb for PowerPoint 3D).
# Re-uses the modelling helpers, the material palette and the rig/export machinery of the Schumpeter / Cantillon decks.
#
#   python3 models/make_models.py               -> models/glb/*.glb   (all exhibits)
#   python3 models/make_models.py phone lever   -> only selected ones
#
# Convention (same as the other decks): Blender Z up, the viewer looks from -Y.
# PowerPoint plays only *skinned* glTF animation, so every moving part is bound to a bone of one armature
# and the whole motion is a function of normalised time t in [0, 1] (t = 0 and t = 1 give the same pose).
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "schumpeter", "models"))
import make_models as mm  # noqa: E402
from make_models import (bpy, bmesh, Vector, Matrix, TAU, M, finish, mesh_obj, lathe, box, cyl, sphere,  # noqa: E402
                         torus, tube, to_mesh, profile2d, rot_all, coin, book)
from rig import Rig, export_rigged, clamp01, smooth, ease, pulse, back_out, hop, wave  # noqa: E402

mm.OUT = os.path.join(HERE, "glb")
os.makedirs(mm.OUT, exist_ok=True)


# ------------------------------------------------------------------ helpers
def text_mesh(name, body, size, depth, mat, loc=(0, 0, 0), rot=(0, 0, 0), res=3, bevel=0.0):
    """Volumetric text (FONT curve -> mesh), centred on loc."""
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


def grid_surface(name, nu, nv, fn, mat, smooth_=60):
    """Parametric surface: fn(u, v) -> (x, y, z), u, v in [0, 1]."""
    verts = [fn(i / nu, j / nv) for j in range(nv + 1) for i in range(nu + 1)]
    faces = []
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            faces.append((a, a + 1, a + nu + 2, a + nu + 1))
    return finish(mesh_obj(name, verts, faces), mat, smooth_)


def xform(objs, T):
    T = Matrix(T)
    for o in objs:
        o.matrix_world = T @ o.matrix_world


# extra palette: screens, plastic, money — the digital-economy props
EXTRA = {
    "screen":    ((0.010, 0.020, 0.052), 0.05, 0.12, {"emit": (0.09, 0.19, 0.55), "es": 1.2, "coat": 0.9}),
    "screen_l":  ((0.030, 0.055, 0.110), 0.00, 0.15, {"emit": (0.24, 0.46, 0.95), "es": 1.8, "coat": 0.8}),
    "ui":        ((0.300, 0.760, 0.960), 0.00, 0.35, {"emit": (0.34, 0.80, 1.00), "es": 2.4}),
    "ui_dim":    ((0.240, 0.300, 0.420), 0.00, 0.40, {"emit": (0.30, 0.42, 0.70), "es": 0.9}),
    "warn":      ((0.980, 0.330, 0.250), 0.00, 0.35, {"emit": (1.00, 0.32, 0.22), "es": 3.0}),
    "plastic":   ((0.050, 0.055, 0.070), 0.10, 0.30, {"coat": 0.9}),
    "plastic_w": ((0.760, 0.760, 0.790), 0.05, 0.34, {"coat": 0.5}),
    "money":     ((0.330, 0.470, 0.330), 0.00, 0.85, {}),
    "money2":    ((0.480, 0.560, 0.420), 0.00, 0.85, {}),
    "paper_w":   ((0.880, 0.860, 0.800), 0.00, 0.80, {}),
    "ink":       ((0.030, 0.030, 0.050), 0.00, 0.55, {}),
    "steel_s":   ((0.620, 0.640, 0.680), 1.00, 0.34, {}),
    "coral":     ((0.820, 0.290, 0.230), 0.10, 0.38, {"coat": 0.5}),
    "gold_r":    ((0.960, 0.700, 0.300), 1.00, 0.32, {}),
}
_em = {}


_base_M = mm.M


def MT(name):
    """Material lookup: the shared palette, plus the local screens/plastics/money additions."""
    if name not in EXTRA:
        return _base_M(name)
    if name in _em and _em[name].name in bpy.data.materials:
        return _em[name]
    col, met, rough, ex = EXTRA[name]
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Metallic"].default_value = met
    b.inputs["Roughness"].default_value = rough
    if "coat" in ex:
        b.inputs["Coat Weight"].default_value = ex["coat"]
    if "emit" in ex:
        b.inputs["Emission Color"].default_value = (*ex["emit"], 1)
        b.inputs["Emission Strength"].default_value = ex["es"]
    _em[name] = m
    return m


mm.M = MT          # the shared helpers (box/cyl/lathe/...) resolve materials through this hook


def dead(t, s, d=0.06):
    """1 while hidden, 0 while alive: a short cross-fade window for pop-in / pop-out parts."""
    return 1.0 - (ease(t, s, s + d) * (1 - ease(t, 1.0 - s - d, 1.0 - s)))


def pop(t, a, b, c, d):
    """Visible (1) between a..b, gone outside, with short fades: scale helper for appearing parts."""
    return pulse(t, a, a + (b - a) * 0.25, b - (b - a) * 0.25, b) * (1 - ease(t, c, d)) if d > c else \
        pulse(t, a, a + (b - a) * 0.25, b - (b - a) * 0.25, b)


def damped(t, t0, freq, amp, tau):
    """Decaying oscillation that is exactly 0 at t = 0 and t = 1 (envelope = pulse)."""
    return amp * math.sin(TAU * freq * (t - t0)) * pulse(t, max(0.0, t0), max(0.0, t0) + tau * 0.35,
                                                         min(0.98, t0 + tau), min(1.0, t0 + tau * 1.45))


# ================================================================== exhibits
def m_phone():
    """One tap = one purchase: a finger presses "buy" on the phone, a coin jumps out of the screen."""
    rig = Rig()
    W, D, H = 0.50, 0.062, 0.98
    FY = -D / 2 - 0.005
    rig.bone("phone", (0, 0.10, -H / 2))
    m0 = rig.mark()
    box("body", (W, D, H), (0, 0, 0), "plastic", 0.032, seg=3)
    box("sidebtn", (0.010, 0.026, 0.07), (-W / 2 - 0.003, 0, 0.22), "plastic_w", 0.003)
    box("sidebtn2", (0.010, 0.020, 0.04), (-W / 2 - 0.003, 0, 0.30), "plastic_w", 0.003)
    box("speaker", (0.10, 0.006, 0.012), (0, FY - 0.001, H / 2 - 0.035), "ink", 0.002)
    box("screen", (W - 0.042, 0.006, H - 0.072), (0, FY + 0.004, 0.0), "screen", 0.010)
    # app UI: header, three product cards, price bars, the big "buy" button, bottom tab bar
    box("hdr", (0.30, 0.004, 0.030), (0, FY - 0.004, 0.385), "ui_dim", 0.002)
    for i, z in enumerate((0.275, 0.135, -0.005)):
        box(f"pcard{i}", (0.42, 0.004, 0.105), (0, FY - 0.004, z), "ui_dim", 0.002)
        box(f"pphoto{i}", (0.085, 0.005, 0.085), (-0.16, FY - 0.006, z), "ui", 0.002)
        box(f"ptxt{i}", (0.16, 0.005, 0.014), (0.09, FY - 0.006, z + 0.022), "ui", 0.002)
        box(f"ptxt2{i}", (0.11, 0.005, 0.012), (0.065, FY - 0.006, z - 0.012), "ui_dim", 0.002)
    box("tabbar", (0.42, 0.004, 0.030), (0, FY - 0.004, -0.445), "ui_dim", 0.002)
    box("chin", (0.215, 0.135, 0.135), (0.195, 0.035, -0.470), "plastic", 0.030, seg=3)
    box("homebar", (0.20, 0.004, 0.008), (0.195, -0.032, -0.500), "ui_dim", 0.002)
    rig.take(m0, "phone")
    # the buy button (bone: it sinks when pressed)
    m = rig.mark()
    box("buy", (0.42, 0.014, 0.078), (0, FY - 0.010, -0.315), "warn", 0.006)
    text_mesh("buytxt", "КУПИТЬ", 0.036, 0.005, "paper_w", loc=(0, FY - 0.024, -0.315))
    rig.take(m, "btn", head=(0, FY - 0.010, -0.315))
    # the finger that taps it
    m = rig.mark()
    cyl("finger", 0.030, 0.17, (0.075, FY - 0.115, -0.315), "ivory", rot=(math.radians(90), 0, 0), seg=24)
    f = sphere("fingertip", 0.031, (0.075, FY - 0.03, -0.315), "ivory", 24, 12)
    f.scale = (1, 0.7, 1)
    cyl("sleve", 0.043, 0.06, (0.075, FY - 0.185, -0.315), "navy", rot=(math.radians(90), 0, 0), seg=24)
    rig.take(m, "finger", head=(0, FY - 0.02, -0.315))
    # the coin that flies out of the button
    m = rig.mark()
    coin("pop", (0.075, FY - 0.05, -0.315), (math.radians(90), 0, 0), r=0.062, t=0.018)
    rig.take(m, "pop", head=(0.075, FY - 0.05, -0.315))
    # the impact ring at the tap point
    m = rig.mark()
    torus("tapring", 0.075, 0.006, (0.075, FY - 0.02, -0.315), "warn", rot=(math.radians(90), 0, 0), seg=48, mseg=8)
    rig.take(m, "ring", head=(0.075, FY - 0.02, -0.315))
    # the cart badge with the counter that ticks up
    m = rig.mark()
    box("badge", (0.088, 0.016, 0.056), (0.185, FY - 0.014, 0.335), "warn", 0.012)
    box("badgetxt", (0.030, 0.006, 0.016), (0.185, FY - 0.026, 0.335), "paper_w", 0.002)
    rig.take(m, "badge", head=(0.185, FY - 0.014, 0.335))
    # the "order placed" toast that slides in
    m = rig.mark()
    box("toast", (0.34, 0.014, 0.086), (0, FY - 0.014, 0.195), "paper_w", 0.008)
    box("toastic", (0.036, 0.006, 0.036), (-0.135, FY - 0.024, 0.195), "ui", 0.004)
    text_mesh("toastt1", "ЗАКАЗ ОФОРМЛЕН", 0.026, 0.004, "ink", loc=(0.035, FY - 0.024, 0.212))
    box("toastt2", (0.10, 0.005, 0.011), (0.0, FY - 0.024, 0.180), "ink", 0.002)
    rig.take(m, "toast", head=(0, FY - 0.014, 0.195))
    rig.shift(dz=-0.01)

    def anim(t):
        appr = ease(t, 0.04, 0.16) * (1 - ease(t, 0.60, 0.74))
        press = pulse(t, 0.16, 0.20, 0.23, 0.29)
        fl = clamp01((t - 0.22) / 0.46)
        q = clamp01((t - 0.20) / 0.28)
        toast = pulse(t, 0.54, 0.70, 0.88, 0.97)
        return {
            "phone": {"rot": [((0, 1, 0), 0.7 * wave(t, 1)), ((1, 0, 0), 0.5 * wave(t, 2, 0.2))]},
            "btn": {"scale": (1, 1 - 0.16 * press, 1)},
            "finger": {"loc": (0, -0.115 * (1 - appr) + 0.016 * press, 0.055 * (1 - appr))},
            "pop": {"loc": (0.14 * fl, -0.26 * fl, 0.42 * math.sin(math.pi * fl * 0.8)),
                    "rot": [((1, 0, 0), 760 * fl), ((0, 0, 1), 120 * fl)],
                    "scale": max(0.001, math.sin(math.pi * min(1, fl * 1.05)) * (1 - ease(t, 0.62, 0.72)))},
            "ring": {"scale": (0.35 + 2.3 * q, 0.35 + 2.3 * q, max(0.001, 1 - q ** 2))},
            "badge": {"scale": (1 + 0.30 * pulse(t, 0.30, 0.36, 0.42, 0.52),
                                1 + 0.30 * pulse(t, 0.30, 0.36, 0.42, 0.52),
                                1 + 0.30 * pulse(t, 0.30, 0.36, 0.42, 0.52))},
            "toast": {"loc": (-0.46 * (1 - toast), 0, 0), "scale": max(0.001, toast)},
        }
    return rig, (lambda t: anim((t + 0.26) % 1.0)), 5.0


def m_card():
    """Pay-by-tap: the card taps the terminal, four "payment parts" stack up, the receipt slides out."""
    rig = Rig()
    FY = -0.132
    m0 = rig.mark()
    box("tower", (0.56, 0.26, 0.40), (-0.17, 0.0, -0.13), "plastic", 0.022, seg=3)
    box("screen", (0.30, 0.008, 0.17), (-0.17, -0.145, -0.055), "screen_l", 0.006)
    box("scr1", (0.20, 0.005, 0.016), (-0.20, -0.152, -0.020), "ui", 0.002)
    box("scr2", (0.14, 0.005, 0.014), (-0.23, -0.152, -0.058), "ui_dim", 0.002)
    for r in range(3):
        for c in range(3):
            box("key", (0.078, 0.010, 0.030), (-0.29 + 0.12 * c, -0.150 - 0.020 * r, -0.165 - 0.052 * r),
                "plastic_w", 0.004)
    box("slot", (0.20, 0.012, 0.012), (-0.17, -0.146, 0.012), "ink", 0.003)
    box("brand", (0.16, 0.006, 0.014), (-0.17, -0.150, 0.058), "gold_r", 0.002)
    rig.take(m0, "root")
    # the LED strip (blinks while the payment goes through)
    m = rig.mark()
    box("led", (0.028, 0.010, 0.028), (0.02, -0.150, 0.055), "ui", 0.006)
    rig.take(m, "led", head=(0.02, -0.150, 0.055))
    # the printed receipt sliding out of the slot
    m = rig.mark()
    box("strip", (0.16, 0.005, 0.30), (-0.17, -0.150, -0.14), "paper_w", 0.0)
    rig.take(m, "strip", head=(-0.17, -0.150, 0.01))
    # the bank card (bone: it hovers, taps the reader and lifts off again)
    m = rig.mark()
    cx, cy, cz = 0.30, -0.16, 0.06
    box("cbody", (0.46, 0.014, 0.29), (cx, cy, cz), "plastic", 0.018, seg=2)
    box("cchip", (0.060, 0.008, 0.048), (cx - 0.14, cy - 0.010, cz + 0.035), "gold_r", 0.004)
    box("cwave", (0.036, 0.006, 0.036), (cx + 0.02, cy - 0.010, cz + 0.045), "paper_w", 0.004)
    box("cstripe", (0.070, 0.006, 0.29), (cx + 0.17, cy - 0.009, cz), "coral", 0.002)
    box("cnum", (0.22, 0.006, 0.020), (cx - 0.06, cy - 0.010, cz - 0.075), "paper_w", 0.002)
    box("cnum2", (0.10, 0.006, 0.016), (cx - 0.12, cy - 0.010, cz - 0.110), "paper_w", 0.002)
    rig.take(m, "card", head=(cx, cy, cz))
    # three contactless waves around the card
    for i in range(3):
        m = rig.mark()
        torus("wave", 0.16 + 0.07 * i, 0.005, (cx - 0.16, cy, cz + 0.02), "ui", rot=(math.radians(90), 0, 0),
              seg=48, mseg=6)
        rig.take(m, f"wav{i}", head=(cx - 0.16, cy, cz + 0.02))
    # four "installment" coins that stack up as the payments are booked
    for i in range(4):
        m = rig.mark()
        coin("inst", (0.335, 0.055, -0.315 + i * 0.030), (0, 0, 0.3 * i), r=0.075, t=0.024)
        rig.take(m, f"inst{i}", head=(0.335, 0.055, -0.315 + i * 0.030))
    rig.shift(dz=0.02)

    def anim(t):
        tap = pulse(t, 0.14, 0.24, 0.34, 0.46)
        blink = 0.5 + 0.5 * math.sin(TAU * 3 * t)
        o = {
            "card": {"loc": (0.02 * tap, 0.05 * tap, 0.24 * (1 - tap)),
                     "rot": [((0, 1, 0), -16 * (1 - tap)), ((0, 0, 1), 6 * (1 - tap))]},
            "led": {"scale": (max(0.001, blink), max(0.001, blink), max(0.001, blink))},
            "strip": {"scale": (1, 1, 0.05 + 0.95 * pulse(t, 0.50, 0.66, 0.90, 0.99))},
        }
        for i in range(3):
            q = clamp01((t - 0.14 - 0.05 * i) / 0.24)
            o[f"wav{i}"] = {"scale": (0.3 + 2.6 * q, 0.3 + 2.6 * q, max(0.001, 1 - q ** 2))}
        for i in range(4):
            q = clamp01((t - 0.52 - 0.08 * i) / 0.10)
            o[f"inst{i}"] = {"loc": (0, 0, 0.16 * (1 - smooth(q))),
                             "rot": [((0, 1, 0), 190 * (1 - smooth(q)))],
                             "scale": max(0.001, 4 * q) if q < 1 else 1}
        return o
    return rig, anim, 5.0


def m_cart():
    """The basket that fills itself: parcel, bottle, book and cup drop in one after another."""
    rig = Rig()
    rig.bone("cart", (0, 0, 0))
    m0 = rig.mark()
    torus("ringbot", 0.245, 0.009, (0, 0, 0.005), "steel_s", seg=64, mseg=8).scale = (1, 0.74, 1)
    torus("ringtop", 0.365, 0.011, (0, 0, 0.40), "steel_s", seg=64, mseg=8).scale = (1, 0.74, 1)
    cyl("floor", 0.235, 0.014, (0, 0, 0.008), "steel_s", seg=48).scale = (1, 0.74, 1)
    for i in range(18):
        a = TAU * i / 18
        tube("wire", [(0.245 * math.cos(a), 0.181 * math.sin(a), 0.01),
                      (0.285 * math.cos(a), 0.211 * math.sin(a), 0.20),
                      (0.365 * math.cos(a), 0.270 * math.sin(a), 0.40)], 0.006, "steel_s", 3)
    tube("handle", [(-0.30, 0, 0.40), (-0.16, 0, 0.60), (0.16, 0, 0.60), (0.30, 0, 0.40)], 0.011, "steel_s", 4)
    for sx in (-1, 1):
        sphere("rivet", 0.014, (sx * 0.30, 0, 0.40), "gold_r", 16, 8)
    rig.take(m0, "cart")
    # items: they rest at the bottom, the animation drops them in
    m = rig.mark()
    box("parcel", (0.20, 0.19, 0.17), (-0.10, 0.0, 0.105), "paper", 0.010)
    box("rib1", (0.018, 0.196, 0.176), (-0.10, 0.0, 0.105), "coral", 0.004)
    box("rib2", (0.206, 0.018, 0.176), (-0.10, 0.0, 0.105), "coral", 0.004)
    rig.take(m, "it0", head=(-0.10, 0.0, 0.105))
    m = rig.mark()
    lathe("bottle", [(0, 0), (0.052, 0), (0.055, 0.10), (0.032, 0.13), (0.026, 0.19), (0.030, 0.21), (0, 0.21)],
          "green", 40, 40, loc=(0.10, -0.03, 0.02))
    cyl("capl", 0.030, 0.030, (0.10, -0.03, 0.225), "coral", seg=24)
    rig.take(m, "it1", head=(0.10, -0.03, 0.02))
    m = rig.mark()
    book("bk", 0.19, 0.13, 0.036, "navy", Vector((0.055, 0.10, 0.03)), rz=14, bands=1)
    rig.take(m, "it2", head=(0.055, 0.10, 0.03))
    m = rig.mark()
    lathe("cup", [(0, 0), (0.055, 0), (0.062, 0.02), (0.070, 0.14), (0.062, 0.15), (0.058, 0.13), (0.050, 0.02), (0, 0.02)],
          "paper_w", 40, 40, loc=(-0.02, 0.10, 0.10))
    torus("cuplid", 0.070, 0.008, (-0.02, 0.10, 0.245), "plastic", seg=40, mseg=8)
    rig.take(m, "it3", head=(-0.02, 0.10, 0.10))
    # price tag swinging on the handle
    m = rig.mark()
    tube("string", [(0.26, 0, 0.52), (0.28, 0, 0.44), (0.30, 0, 0.36)], 0.004, "sand", 2, False)
    box("tag", (0.15, 0.008, 0.10), (0.31, 0, 0.28), "paper_w", 0.006)
    box("tagbar", (0.09, 0.006, 0.014), (0.31, -0.008, 0.28), "coral", 0.002)
    rig.take(m, "tag", head=(0.28, 0, 0.44))
    rig.shift(dz=-0.30)

    def anim(t):
        o = {}
        for i in range(4):
            s = 0.06 + 0.17 * i
            q = clamp01((t - s) / 0.16)
            o[f"it{i}"] = {"loc": (0, 0, 0.30 * (1 - smooth(q))),
                           "rot": [((0, 0, 1), (18 + 6 * i) * (1 - smooth(q)))],
                           "scale": max(0.001, min(1, 5 * q)) * (1 - ease(t, 0.90, 0.99))}
        jig = 0.0
        for i in range(4):
            jig += damped(t, 0.06 + 0.17 * i + 0.16, 3.0, 3.6, 0.13)
        o["cart"] = {"rot": [((1, 0, 0), jig)]}
        o["tag"] = {"rot": [((0, 1, 0), 7 * wave(t, 2) + 3 * wave(t, 3, 0.3))]}
        return o
    return rig, anim, 5.5


def m_lever():
    """"Light dopamine": the one-armed machine — lever pulled, reels spinning, coins in the tray."""
    rig = Rig()
    m0 = rig.mark()
    # cabinet built as walls so the three reels really sit inside the window
    box("sideL", (0.030, 0.40, 0.80), (-0.295, 0.0, 0.0), "plastic", 0.010)
    box("sideR", (0.030, 0.40, 0.80), (0.295, 0.0, 0.0), "plastic", 0.010)
    box("floor", (0.62, 0.40, 0.030), (0, 0.0, -0.385), "plastic", 0.010)
    box("back", (0.62, 0.024, 0.80), (0, 0.188, 0.0), "plastic", 0.008)
    box("roof", (0.66, 0.42, 0.070), (0, 0.0, 0.435), "coral", 0.016)
    box("wbot", (0.62, 0.030, 0.150), (0, -0.195, -0.305), "plastic", 0.008)
    box("wtop", (0.62, 0.030, 0.075), (0, -0.195, 0.298), "plastic", 0.008)
    box("titleplate", (0.46, 0.020, 0.060), (0, -0.205, 0.370), "plastic", 0.008)
    for sx in (-1, 1):
        box("wpos", (0.070, 0.030, 0.44), (sx * 0.275, -0.195, 0.0), "plastic", 0.008)
        box("trim", (0.026, 0.024, 0.78), (sx * 0.310, -0.198, 0.0), "gold_r", 0.004)
    for sx in (-1, 1):
        box("wdiv", (0.024, 0.030, 0.44), (sx * 0.082, -0.195, 0.0), "gold_r", 0.004)
    box("payline", (0.52, 0.026, 0.012), (0, -0.207, 0.0), "gold_r", 0.003)
    box("tray", (0.36, 0.20, 0.050), (0, -0.190, -0.360), "plastic_w", 0.010)
    box("traymouth", (0.30, 0.16, 0.020), (0, -0.190, -0.330), "ink", 0.004)
    text_mesh("title", "ДОФАМИН", 0.050, 0.008, "ui", loc=(0, -0.222, 0.370))
    rig.take(m0, "root")
    # three reels seen through the window
    for i in range(3):
        x = -0.164 + 0.164 * i
        m = rig.mark()
        cyl("reel", 0.090, 0.150, (x, -0.120, 0.0), "plastic_w", rot=(0, math.radians(90), 0), seg=32)
        for k in range(4):
            a = math.radians(45 + 90 * k)
            box("sym", (0.140, 0.022, 0.050), (x, -0.120 + 0.090 * math.cos(a), 0.090 * math.sin(a)),
                "warn" if k % 2 == 0 else "ui", 0.004, rot=(a, 0, 0))
        rig.take(m, f"reel{i}", head=(x, -0.120, 0.0))
    # the lever on the right cheek
    m = rig.mark()
    box("hinge", (0.10, 0.12, 0.10), (0.34, 0.02, -0.230), "coral", 0.014)
    tube("arm", [(0.34, 0.02, -0.200), (0.40, 0.02, 0.030), (0.43, 0.02, 0.230)], 0.013, "steel_s", 4, False)
    sphere("knob", 0.052, (0.435, 0.02, 0.270), "coral", 24, 12)
    rig.take(m, "lever", head=(0.34, 0.02, -0.200))
    # payout coins in the tray
    for i in range(3):
        m = rig.mark()
        coin("pay", (-0.06 + 0.06 * i, -0.190, -0.300), (math.radians(90), 0, 0.4 * i), r=0.055, t=0.018)
        rig.take(m, f"pay{i}", head=(-0.06 + 0.06 * i, -0.190, -0.300))
    # the flash that pops on the winning line
    m = rig.mark()
    torus("flash", 0.115, 0.014, (0, -0.213, 0.0), "warn", rot=(math.radians(90), 0, 0), seg=48, mseg=8)
    rig.take(m, "flash", head=(0, -0.213, 0.0))
    rig.shift(dz=-0.02)

    def anim(t):
        pull = pulse(t, 0.04, 0.12, 0.20, 0.34)
        o = {"lever": {"rot": [((0, 1, 0), -40 * pull)]},
             "flash": {"scale": (max(0.001, 2.4 * pulse(t, 0.50, 0.545, 0.58, 0.68)),) * 3}}
        for i in range(3):
            stop = 0.50 + 0.065 * i
            q = smooth(clamp01((t - 0.20) / (stop - 0.20)))
            wob = damped(t, stop, 5.0, 7.0, 0.05) if t > stop else 0.0
            o[f"reel{i}"] = {"rot": [((1, 0, 0), 360 * (3 + i) * q + wob)]}
        for i in range(3):
            q = clamp01((t - 0.60 - 0.07 * i) / 0.12)
            o[f"pay{i}"] = {"loc": (0, 0, 0.13 * (1 - smooth(q))), "rot": [((0, 0, 1), 180 * (1 - smooth(q)))],
                            "scale": max(0.001, min(1, 5 * q))}
        return o
    return rig, anim, 6.0


def m_clock():
    """The discount timer: built face-up, then tilted towards the viewer — hands race, the bell rings."""
    rig = Rig()
    rig.bone("body", (0, 0, -0.08))
    m0 = rig.mark()
    lathe("case", [(0, 0), (0.42, 0), (0.45, 0.04), (0.47, 0.12), (0.45, 0.19), (0.40, 0.23), (0.31, 0.25), (0, 0.25)],
          "coral", 64, 40)
    lathe("bezel", [(0.35, 0.24), (0.42, 0.26), (0.43, 0.30), (0.40, 0.31), (0.34, 0.28), (0.33, 0.26)], "gold_r", 64, 40)
    lathe("face", [(0, 0.25), (0.35, 0.25), (0.35, 0.268), (0, 0.268)], "ivory", 64, 30)
    for i in range(12):
        a = TAU * i / 12
        box("tick", (0.030, 0.014, 0.008), (0.295 * math.cos(a), 0.295 * math.sin(a), 0.272), "ink", 0.002,
            rot=(0, 0, a))
    cyl("hub", 0.030, 0.024, (0, 0, 0.278), "gold_r", seg=32)
    for sx in (-1, 1):
        s = sphere("bell", 0.125, (sx * 0.255, 0, 0.285), "gold_r", 32, 16)
        s.scale = (1, 1, 1.05)
        cyl("bellpost", 0.030, 0.10, (sx * 0.255, 0, 0.235), "gold_r", seg=24)
        cyl("foot", 0.028, 0.13, (sx * 0.20, 0.055, -0.05), "gold_r", rot=(math.radians(-14), 0, 0), seg=20)
    rig.take(m0, "body")
    # the two hands: they race around (full turns only, so the loop is seamless)
    m = rig.mark()
    box("min", (0.235, 0.026, 0.010), (0.108, 0, 0.281), "ink", 0.003)
    box("mintail", (0.07, 0.030, 0.010), (-0.035, 0, 0.281), "ink", 0.003)
    rig.take(m, "min", head=(0, 0, 0.281), parent="body")
    m = rig.mark()
    box("sec", (0.30, 0.010, 0.008), (0.14, 0, 0.288), "warn", 0.003)
    torus("seckit", 0.034, 0.008, (0.10, 0, 0.288), "warn", seg=24, mseg=6)
    rig.take(m, "sec", head=(0, 0, 0.288), parent="body")
    # the striker between the bells + the bells themselves (bone per bell so they can jiggle)
    m = rig.mark()
    box("strike", (0.024, 0.20, 0.014), (0, 0.10, 0.375), "steel_s", 0.004)
    sphere("striketip", 0.020, (0, 0.20, 0.375), "steel_s", 16, 8)
    rig.take(m, "strike", head=(0, 0, 0.375), parent="body")
    for s_ in (-1, 1):
        m = rig.mark()
        s = sphere("bellx", 0.125, (s_ * 0.255, 0, 0.285), "gold_r", 32, 16)
        s.scale = (1, 1, 1.05)
        rig.take(m, f"bell{'L' if s_ < 0 else 'R'}", head=(s_ * 0.255, 0, 0.285), parent="body")
    # the discount tag hanging off the right bell (hangs "down" = -Y before the final tilt)
    m = rig.mark()
    tube("string", [(0.255, -0.10, 0.305), (0.285, -0.19, 0.235), (0.305, -0.275, 0.170)], 0.005, "sand", 3, False)
    box("tag", (0.30, 0.18, 0.010), (0.315, -0.360, 0.110), "paper_w", 0.010)
    text_mesh("t50", "-50%", 0.105, 0.012, "warn", loc=(0.315, -0.360, 0.117), res=3)
    rig.take(m, "tag", head=(0.28, -0.12, 0.25), parent="body")
    rig.rotate(rx=90)
    rig.shift(dz=-0.06)

    def anim(t):
        ring = pulse(t, 0.66, 0.73, 0.88, 0.97)
        return {
            "body": {"rot": [((1, 0, 0), 1.6 * wave(t, 3))], "loc": (0, 0, 0.012 * ring)},
            "min": {"rot": [((0, 0, 1), 360 * 2 * t)]},
            "sec": {"rot": [((0, 0, 1), 360 * 6 * t)]},
            "strike": {"rot": [((0, 0, 1), 32 * ring * math.sin(TAU * 11 * t))]},
            "bellL": {"rot": [((0, 1, 0), 6 * ring * math.sin(TAU * 11 * t))], "scale": 1 + 0.05 * ring},
            "bellR": {"rot": [((0, 1, 0), -6 * ring * math.sin(TAU * 11 * t))], "scale": 1 + 0.05 * ring},
            "tag": {"rot": [((0, 0, 1), 5 * wave(t, 2) + 18 * ring * wave(t, 9, 0.15))]},
        }
    return rig, (lambda t: anim((t + 0.15) % 1.0)), 5.0


def m_receipt():
    """Buy now, pay later: the receipt prints itself — four installments and a red total line."""
    rig = Rig()
    m0 = rig.mark()
    box("printer", (0.44, 0.26, 0.26), (0, 0, 0.36), "plastic", 0.020, seg=3)
    box("pscr", (0.22, 0.008, 0.10), (0, -0.135, 0.395), "screen_l", 0.005)
    box("pb1", (0.15, 0.005, 0.013), (-0.02, -0.142, 0.420), "ui", 0.002)
    box("pb2", (0.10, 0.005, 0.011), (-0.04, -0.142, 0.392), "ui_dim", 0.002)
    box("pslot", (0.30, 0.022, 0.014), (0, -0.03, 0.222), "ink", 0.004)
    box("pbrand", (0.13, 0.006, 0.014), (0, -0.138, 0.300), "gold_r", 0.002)
    box("plip", (0.30, 0.016, 0.020), (0, -0.14, 0.228), "plastic_w", 0.004)
    rig.take(m0, "root")
    # the paper: bone at the slot, scale on Z prints it downwards
    m = rig.mark()
    box("strip", (0.29, 0.006, 0.82), (0, -0.02, -0.20), "paper_w", 0.0)
    rig.take(m, "strip", head=(0, -0.02, 0.215))
    # printed rows (each appears when the paper reaches it)
    rows_z = [0.11, -0.04, -0.19, -0.34, -0.49]
    for i, z in enumerate(rows_z):
        m = rig.mark()
        last = i == len(rows_z) - 1
        box("rbar", (0.235 if last else 0.19, 0.005, 0.028 if last else 0.018),
            (-0.015 if last else -0.025, -0.027, z), "warn" if last else "ink", 0.002)
        box("rbox", (0.030, 0.005, 0.030), (0.115, -0.027, z), "gold_r" if last else "ui_dim", 0.002)
        box("rbox2", (0.014, 0.005, 0.014), (0.115, -0.030, z), "paper_w", 0.002)
        rig.take(m, f"row{i}", head=(0, -0.027, z))
    # the warning flag at the bottom of the receipt
    m = rig.mark()
    box("flag", (0.11, 0.005, 0.07), (0.09, -0.027, -0.585), "warn", 0.004, rot=(0, 0, math.radians(-8)))
    box("flagtxt", (0.06, 0.005, 0.012), (0.09, -0.031, -0.585), "paper_w", 0.002, rot=(0, 0, math.radians(-8)))
    rig.take(m, "flag", head=(0.09, -0.027, -0.585))
    # the coin that drops out of the slot
    m = rig.mark()
    coin("drop", (0, -0.055, 0.185), (math.radians(90), 0, 0), r=0.055, t=0.018)
    rig.take(m, "drop", head=(0, -0.055, 0.185))
    rig.shift(dz=0.06)

    def anim(t):
        pr = pulse(t, 0.06, 0.52, 0.86, 1.0)
        o = {"strip": {"scale": (1, 1, 0.03 + 0.97 * pr)}}
        for i, z in enumerate(rows_z):
            s = 0.10 + 0.075 * i
            o[f"row{i}"] = {"scale": max(0.001, ease(t, s, s + 0.06) * (1 - ease(t, 0.88, 0.96)))}
        q = clamp01((t - 0.52) / 0.26)
        o["drop"] = {"loc": (0, 0, -0.58 * smooth(q)),
                     "rot": [((0, 0, 1), 700 * smooth(q))],
                     "scale": max(0.001, smooth(q / 0.10) * (1 - smooth((q - 0.85) / 0.15)))}
        o["flag"] = {"scale": max(0.001, pulse(t, 0.76, 0.82, 0.90, 0.99))}
        return o
    return rig, (lambda t: anim((t + 0.42) % 1.0)), 6.0


def m_target():
    """The goal: a dart flies in, hits the bullseye, the board rings and the impact waves run out."""
    rig = Rig()
    rig.bone("board", (0, 0.03, 0.17))
    board = []
    for i, (r, mat) in enumerate([(0.46, "sand"), (0.38, "ink"), (0.30, "sand"), (0.22, "ink"), (0.14, "sand"),
                                  (0.065, "warn")]):
        board.append(lathe("bring", [(0, 0), (r, 0), (r, 0.016), (r * 0.93, 0.023), (0, 0.023)], mat, 60, 30,
                           loc=(0, 0, i * 0.011)))
    xform(board, Matrix.Translation((0, 0.03, 0.17)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    m = rig.mark()
    for o in board:
        pass
    rig.take_objs(board, "board")
    m0 = rig.mark()
    box("base", (0.80, 0.30, 0.035), (0, 0.08, -0.535), "walnut", 0.010)
    box("backleg", (0.055, 0.055, 0.62), (0, 0.235, -0.16), "walnut", 0.010, rot=(math.radians(16), 0, 0))
    for sx in (-1, 1):
        tube("leg", [(sx * 0.255, 0.055, -0.045), (sx * 0.30, 0.12, -0.30), (sx * 0.335, 0.155, -0.52)], 0.020,
             "walnut", 4, False)
    box("shelf", (0.34, 0.16, 0.030), (0, 0.135, -0.30), "walnut", 0.008)
    box("shelfbar", (0.30, 0.014, 0.030), (0, 0.055, -0.30), "gold_r", 0.004)
    rig.take(m0, "root")
    # impact waves on the board face
    for i in range(2):
        m = rig.mark()
        torus("tring", 0.075, 0.008, (0, -0.06, 0.17), "gold_r", rot=(math.radians(90), 0, 0), seg=48, mseg=8)
        rig.take(m, f"twav{i}", head=(0, -0.06, 0.17), parent="board")
    # the dart (tip in the bullseye, flights towards the viewer)
    m = rig.mark()
    cyl("shaft", 0.013, 0.26, (0, -0.13, 0.17), "steel_s", rot=(math.radians(90), 0, 0), seg=20)
    cyl("tip", 0.006, 0.07, (0, -0.035, 0.17), "steel_s", rot=(math.radians(90), 0, 0), seg=16, bevel=0.002)
    cyl("barrel", 0.019, 0.10, (0, -0.075, 0.17), "gold_r", rot=(math.radians(90), 0, 0), seg=20)
    for k in range(4):
        box("fin", (0.078, 0.105, 0.005), (0, -0.275, 0.17), "warn", 0.002, rot=(0, math.radians(45 + 90 * k), 0))
    cyl("nock", 0.011, 0.03, (0, -0.325, 0.17), "ink", rot=(math.radians(90), 0, 0), seg=16)
    rig.take(m, "dart", head=(0, -0.02, 0.17))
    rig.shift(dz=-0.02)

    def anim(t):
        stuck = pulse(t, 0.06, 0.20, 0.62, 0.80)
        env = ease(t, 0.20, 0.225) * (1 - ease(t, 0.58, 0.68))
        vib = 9.0 * env * math.sin(TAU * 11 * (t - 0.20))
        k = 1.0 - stuck
        o = {"dart": {"loc": (0.60 * k, -0.32 * k, -0.32 * k),
                      "rot": [((0, 0, 1), -38 * k + vib), ((1, 0, 0), 10 * k)]},
             "board": {"rot": [((1, 0, 0), 0.22 * vib)]}}
        for i in range(2):
            q = clamp01((t - 0.22 - 0.09 * i) / 0.34)
            o[f"twav{i}"] = {"scale": (0.30 + 3.1 * q, 0.30 + 3.1 * q, max(0.001, 1 - q ** 2))}
        return o
    return rig, anim, 5.0


def m_hourglass():
    """Time budget: the sand runs down, pauses, and runs back up — an endless loop of "ещё успею"."""
    rig = Rig()
    rig.bone("sway", (0, 0, 0.45))
    m0 = rig.mark()
    lathe("plate0", [(0, 0), (0.40, 0), (0.43, 0.02), (0.41, 0.05), (0, 0.05)], "walnut", 64, 30)
    lathe("plate1", [(0, 0), (0.40, 0), (0.43, 0.02), (0.41, 0.05), (0, 0.05)], "walnut", 64, 30,
          loc=(0, 0, 0.86))
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl("post", 0.020, 0.87, (sx * 0.285, sy * 0.285, 0.455), "gold_r", seg=20)
            sphere("finial", 0.030, (sx * 0.285, sy * 0.285, 0.905), "gold_r", 20, 10)
    lathe("glassT", [(0.036, 0), (0.10, 0.025), (0.20, 0.10), (0.255, 0.22), (0.255, 0.30), (0.225, 0.355)],
          "glass", 64, 60, loc=(0, 0, 0.47))
    lathe("glassB", [(0.036, 0), (0.10, -0.025), (0.20, -0.10), (0.255, -0.22), (0.255, -0.30), (0.225, -0.355)],
          "glass", 64, 60, loc=(0, 0, 0.47))
    cyl("neck", 0.036, 0.05, (0, 0, 0.47), "glass", seg=32)
    rig.take(m0, "sway")
    m = rig.mark()
    lathe("sandT", [(0.032, 0), (0.10, 0.02), (0.19, 0.10), (0.245, 0.21), (0.245, 0.28), (0.19, 0.30),
                    (0.10, 0.16), (0.032, 0.04)], "sand", 56, 40, loc=(0, 0, 0.47))
    rig.take(m, "sandT", head=(0, 0, 0.47), parent="sway")
    m = rig.mark()
    cyl("stream", 0.011, 0.35, (0, 0, 0.295), "sand", seg=14)
    rig.take(m, "stream", head=(0, 0, 0.47), parent="sway")
    m = rig.mark()
    lathe("sandB", [(0, 0), (0.20, 0), (0.17, 0.05), (0.10, 0.15), (0.035, 0.21), (0, 0.22)], "sand", 56, 40,
          loc=(0, 0, 0.10))
    rig.take(m, "sandB", head=(0, 0, 0.10), parent="sway")

    def anim(t):
        run = pulse(t, 0.05, 0.12, 0.48, 0.62)          # sand running down
        back = pulse(t, 0.66, 0.76, 0.92, 1.0)          # and pouring back up
        return {
            "sway": {"rot": [((0, 1, 0), 1.3 * wave(t, 1)), ((1, 0, 0), 0.8 * wave(t, 2, 0.25))],
                     "loc": (0, 0, 0.006 * wave(t, 3))},
            "sandT": {"scale": (1, 1, max(0.04, 1 - 0.96 * run + 0.96 * back))},
            "sandB": {"scale": (1, 1, max(0.04, 0.06 + 0.94 * run - 0.94 * back))},
            "stream": {"scale": (1, 1, max(0.001, run * (1 - ease(t, 0.52, 0.60))))},
        }
    return rig, anim, 6.0


def m_scales():
    """Weighing the hypotheses: the "want it now" pan against the budget pan — the beam never settles."""
    rig = Rig()
    lathe("base", [(0, 0), (0.34, 0), (0.36, 0.02), (0.33, 0.06), (0.20, 0.09), (0.10, 0.11), (0, 0.11)], "walnut", 72)
    lathe("pillar", [(0, 0.10), (0.055, 0.10), (0.045, 0.16), (0.032, 0.22), (0.028, 0.90), (0.042, 0.93),
                     (0.028, 0.97), (0, 0.97)], "brass", 40)
    sphere("finial", 0.040, (0, 0, 1.05), "brass", 24, 12)
    L = 0.60
    piv = Vector((0, 0, 0.97))
    m = rig.mark()
    endL, endR = piv - Vector((L, 0, 0)), piv + Vector((L, 0, 0))
    tube("beam", [tuple(endL), tuple(piv + Vector((0, 0, 0.03))), tuple(endR)], 0.017, "gold_r", 4)
    sphere("pivot", 0.038, tuple(piv), "brass", 24, 12)
    for e in (endL, endR):
        sphere("end", 0.024, tuple(e), "brass", 16, 8)
    tube("pointer", [tuple(piv), tuple(piv + Vector((0, -0.005, 0.19)))], 0.007, "warn", 2, False)
    rig.take(m, "beam", head=tuple(piv))
    box("dial", (0.15, 0.012, 0.045), (0, -0.030, 1.215), "brass_d", 0.004)
    for e, name in ((endL, "L"), (endR, "R")):
        pan_c = e - Vector((0, 0, 0.50))
        m = rig.mark()
        lathe("pan" + name, [(0, 0.0), (0.12, 0.0), (0.20, 0.035), (0.22, 0.06), (0.215, 0.065), (0.19, 0.04),
                             (0.11, 0.008), (0, 0.008)], "brass", 56, 40, loc=tuple(pan_c))
        for k in range(3):
            a = TAU * k / 3 + 0.5
            tube("chain", [tuple(e), tuple(pan_c + Vector((0.21 * math.cos(a), 0.21 * math.sin(a), 0.06)))],
                 0.0035, "steel_s", 2, False)
        if name == "L":
            box("want", (0.24, 0.20, 0.10), tuple(pan_c + Vector((-0.02, 0.0, 0.08))), "paper", 0.012)
            box("wantrib", (0.03, 0.205, 0.105), tuple(pan_c + Vector((-0.02, 0.0, 0.08))), "coral", 0.004)
            box("phone", (0.13, 0.02, 0.24), tuple(pan_c + Vector((0.10, -0.05, 0.16))), "plastic", 0.014,
                rot=(math.radians(-14), 0, math.radians(12)))
            box("scr", (0.10, 0.008, 0.20), tuple(pan_c + Vector((0.10, -0.062, 0.16))), "screen_l", 0.004,
                rot=(math.radians(-14), 0, math.radians(12)))
            for i in range(2):
                box("note", (0.20, 0.13, 0.006), tuple(pan_c + Vector((-0.16, 0.0, 0.135 + 0.008 * i))), "money",
                    0.002, rot=(0, 0, math.radians(9 - 12 * i)))
        else:
            for i in range(5):
                coin("c", tuple(pan_c + Vector((0.0, 0.0, 0.012 + i * 0.026))), (0, 0, i * 1.3), r=0.085, t=0.026)
        rig.take(m, "pan" + name, head=tuple(e), parent="beam")
    # three hypothesis cards leaning against the base
    for i, (x, lab) in enumerate(((-0.29, "H1"), (0.0, "H2"), (0.29, "H3"))):
        m = rig.mark()
        box("hcard", (0.22, 0.014, 0.15), (x, -0.400, -0.505), "paper_w", 0.008, rot=(math.radians(-15), 0, 0))
        text_mesh("hlab", lab, 0.085, 0.010, "ink", loc=(x, -0.412, -0.507), rot=(math.radians(-15), 0, 0))
        rig.take(m, f"hcard{i}", head=(x, -0.385, -0.575), parent="root")
    rig.shift(dz=-0.58)

    def beam_angle(t):
        return 6.5 * wave(t, 1) + 2.0 * wave(t, 3, -0.15)

    def anim(t):
        b = beam_angle(t)
        lag = 2.4 * wave(t, 1, -0.10)
        o = {"beam": {"rot": [((0, 1, 0), b)]},
             "panL": {"rot": [((0, 1, 0), -b + lag)], "loc": (0, 0, 0.010 * wave(t, 2))},
             "panR": {"rot": [((0, 1, 0), -b + lag)], "loc": (0, 0, 0.010 * wave(t, 2, 0.35))}}
        for i in range(3):
            o[f"hcard{i}"] = {"rot": [((1, 0, 0), 2.2 * wave(t, 2, 0.18 * i))]}
        return o
    return rig, anim, 5.0


def m_survey():
    """The questionnaire: the magnifier walks down the rows and the answers get ticked one by one."""
    rig = Rig()
    rig.bone("board", (0, 0, -0.47))
    m0 = rig.mark()
    box("board", (0.66, 0.045, 0.94), (0, 0, 0), "walnut", 0.018, seg=2)
    box("paper", (0.58, 0.006, 0.84), (0, -0.026, -0.02), "paper_w", 0.0)
    box("clip", (0.24, 0.055, 0.055), (0, -0.030, 0.425), "steel_s", 0.010)
    tube("cliphook", [(-0.10, -0.048, 0.44), (0, -0.070, 0.46), (0.10, -0.048, 0.44)], 0.010, "steel_s", 3)
    text_mesh("hdr", "АНКЕТА", 0.058, 0.006, "ink", loc=(0, -0.032, 0.345))
    box("hdrbar", (0.40, 0.004, 0.005), (0, -0.032, 0.305), "ink", 0.0)
    box("nplate", (0.28, 0.010, 0.080), (0.115, -0.032, -0.355), "gold_r", 0.006)
    text_mesh("ntext", "n = 50", 0.062, 0.008, "ink", loc=(0.115, -0.040, -0.355))
    rig.take(m0, "board")
    rows = [0.255 - 0.084 * i for i in range(6)]
    for i, z in enumerate(rows):
        m = rig.mark()
        box("qbar", (0.30 - 0.026 * (i % 2), 0.004, 0.024), (-0.135, -0.032, z), "ui_dim", 0.002)
        box("qbar2", (0.17, 0.004, 0.016), (-0.20, -0.032, z - 0.030), "ui_dim", 0.002)
        box("cb", (0.064, 0.006, 0.064), (0.238, -0.031, z), "ink", 0.002)
        box("cbin", (0.052, 0.006, 0.052), (0.238, -0.033, z), "paper_w", 0.002)
        rig.take(m, f"qb{i}", head=(-0.135, -0.032, z), parent="board")
    for i, z in enumerate(rows):
        m = rig.mark()
        box("t1", (0.030, 0.006, 0.010), (0.229, -0.038, z - 0.006), "warn", 0.002, rot=(0, math.radians(-48), 0))
        box("t2", (0.056, 0.006, 0.010), (0.255, -0.038, z + 0.005), "warn", 0.002, rot=(0, math.radians(42), 0))
        rig.take(m, f"tick{i}", head=(0.238, -0.038, z), parent="board")
    # the magnifier
    m = rig.mark()
    torus("lens", 0.115, 0.020, (-0.115, -0.078, 0.30), "steel_s", rot=(math.radians(90), 0, 0), seg=48, mseg=10)
    cyl("lensglass", 0.112, 0.008, (-0.115, -0.078, 0.30), "glass", rot=(math.radians(90), 0, 0), seg=48)
    cyl("lenshandle", 0.022, 0.20, (-0.115, -0.078, 0.135), "walnut", seg=20)
    rig.take(m, "mag", head=(-0.115, -0.078, 0.30), parent="board")

    def anim(t):
        down = pulse(t, 0.05, 0.90, 0.94, 0.995)
        o = {"mag": {"loc": (-0.02 * wave(t, 1), 0, -0.52 * down),
                     "rot": [((0, 1, 0), 6 * wave(t, 2)), ((0, 0, 1), 3 * wave(t, 3))]}}
        for i in range(6):
            s = 0.10 + 0.115 * i
            o[f"tick{i}"] = {"scale": max(0.001, pulse(t, s, s + 0.05, 0.90, 0.97) * 1.0)}
        o["board"] = {"rot": [((0, 1, 0), 0.7 * wave(t, 1, 0.3))]}
        return o
    return rig, (lambda t: anim((t + 0.12) % 1.0)), 6.0


def m_backpack():
    """The student's backpack: the flap opens, the phone rises — and the money quietly flies out of it."""
    rig = Rig()
    rig.bone("body", (0, 0, 0))
    m0 = rig.mark()
    box("shell", (0.52, 0.32, 0.66), (0, 0.010, 0.0), "navy", 0.075, seg=4)
    box("pocket", (0.40, 0.11, 0.26), (0, -0.195, -0.14), "navy", 0.045, seg=3)
    tube("zip", [(-0.185, -0.245, -0.015), (0, -0.256, 0.005), (0.185, -0.245, -0.015)], 0.008, "steel_s", 3)
    box("zipull", (0.020, 0.012, 0.055), (0.165, -0.252, -0.050), "gold_r", 0.004)
    tube("grip", [(-0.13, 0.135, 0.30), (0, 0.155, 0.395), (0.13, 0.135, 0.30)], 0.016, "leather", 4)
    for sx in (-1, 1):
        box("foot", (0.10, 0.30, 0.045), (sx * 0.16, 0.02, -0.340), "leather", 0.014)
    for sx in (-1, 1):
        box("strap", (0.055, 0.022, 0.40), (sx * 0.235, 0.125, 0.07), "leather", 0.012)
        box("buckle", (0.030, 0.030, 0.045), (sx * 0.235, 0.125, -0.13), "gold_r", 0.006)
    rig.take(m0, "body")
    # the flap: a curved sheet hinged at the back-top edge
    m = rig.mark()

    def flap(u, v):
        x = (-0.265 + 0.53 * u) * (1 - 0.05 * max(0.0, v - 0.6) / 0.4)
        if v < 0.6:
            a = math.pi * (v / 0.6)
            return (x, 0.150 * math.cos(a), 0.295 + 0.150 * math.sin(a))
        w = (v - 0.6) / 0.4
        return (x, -0.150 - 0.022 * w, 0.295 - 0.355 * w)

    grid_surface("flap", 12, 12, flap, "leather", 60)
    box("flapface", (0.26, 0.012, 0.12), (0, -0.156, 0.02), "navy", 0.010)
    rig.take(m, "flap", head=(0, 0.150, 0.295))
    # the phone that rises out of the open backpack
    m = rig.mark()
    box("phone", (0.15, 0.022, 0.26), (0.0, 0.02, 0.235), "plastic", 0.016)
    box("pscr", (0.115, 0.008, 0.215), (0.0, 0.006, 0.235), "screen_l", 0.004)
    rig.take(m, "phone", head=(0.0, 0.02, 0.235), parent="body")
    # coins that hop out and land in front of the backpack
    for i, (x0, y0, z0) in enumerate(((0.10, 0.03, 0.245), (-0.12, 0.03, 0.245))):
        m = rig.mark()
        coin("out", (x0, y0, z0), (math.radians(80), 0, 0.5 * i), r=0.058, t=0.018)
        rig.take(m, f"out{i}", head=(x0, y0, z0), parent="body")
    rig.shift(dz=-0.04)

    def anim(t):
        fl = pulse(t, 0.12, 0.34, 0.76, 0.92)
        rise = pulse(t, 0.34, 0.52, 0.66, 0.82)
        o = {"flap": {"rot": [((1, 0, 0), -86 * back_out(fl, 1.3))]},
             "phone": {"loc": (0, 0, 0.20 * rise), "rot": [((0, 0, 1), 14 * rise)]}}
        for i in range(2):
            s = 0.42 + 0.14 * i
            q = clamp01((t - s) / 0.34)
            o[f"out{i}"] = {"loc": ((-1) ** i * 0.06 * q, -0.34 * q, 0.16 * math.sin(math.pi * q * 0.9) - 0.30 * q),
                            "rot": [((0, 0, 1), 320 * q)],
                            "scale": max(0.001, smooth(q / 0.12) * (1 - smooth((q - 0.86) / 0.14)))}
        return o
    return rig, anim, 5.5


def m_memo():
    """The memo that is the project's output: a pencil ticks the four rules, the 24-h dial turns."""
    rig = Rig()
    rig.bone("card", (0, 0, -0.47))
    m0 = rig.mark()
    box("card", (0.60, 0.035, 0.92), (0, 0, 0), "ivory", 0.020, seg=2)
    box("frame", (0.62, 0.030, 0.024), (0, 0, 0.462), "gold_r", 0.006)
    box("frame2", (0.62, 0.030, 0.024), (0, 0, -0.462), "gold_r", 0.006)
    box("frame3", (0.024, 0.030, 0.94), (-0.30, 0, 0), "gold_r", 0.006)
    box("frame4", (0.024, 0.030, 0.94), (0.30, 0, 0), "gold_r", 0.006)
    text_mesh("hdr", "ПАМЯТКА", 0.062, 0.008, "ink", loc=(-0.130, -0.024, 0.390))
    box("hdrbar", (0.24, 0.005, 0.006), (-0.145, -0.024, 0.348), "gold_r", 0.002)
    rows = [0.195, 0.045, -0.105, -0.255]
    for i, z in enumerate(rows):
        box("cb", (0.090, 0.012, 0.090), (-0.195, -0.026, z), "ink", 0.004)
        box("cbin", (0.074, 0.008, 0.074), (-0.195, -0.030, z), "paper_w", 0.002)
        box("line", (0.30 - 0.028 * i, 0.005, 0.020), (0.055, -0.026, z + 0.014), "ui_dim", 0.002)
        box("line2", (0.21 - 0.02 * i, 0.005, 0.015), (0.010, -0.026, z - 0.018), "ui_dim", 0.002)
    # the 24-hour dial
    cyl("dial", 0.100, 0.028, (0.170, -0.028, 0.360), "gold_r", rot=(math.radians(90), 0, 0), seg=40)
    cyl("dialin", 0.081, 0.030, (0.170, -0.032, 0.360), "paper_w", rot=(math.radians(90), 0, 0), seg=40)
    text_mesh("dialtxt", "24", 0.050, 0.006, "ink", loc=(0.170, -0.048, 0.336))
    rig.take(m0, "card")
    # the dial's hand: one full turn per loop
    m = rig.mark()
    box("hand", (0.072, 0.008, 0.014), (0.170, -0.050, 0.360 + 0.034), "warn", 0.003)
    box("handtail", (0.020, 0.008, 0.014), (0.170, -0.050, 0.360 - 0.010), "warn", 0.003)
    rig.take(m, "hand", head=(0.170, -0.050, 0.360), parent="card")
    # the ticks
    for i, z in enumerate(rows):
        m = rig.mark()
        box("t1", (0.036, 0.008, 0.012), (-0.206, -0.036, z - 0.008), "warn", 0.002, rot=(0, math.radians(-48), 0))
        box("t2", (0.068, 0.008, 0.012), (-0.174, -0.036, z + 0.004), "warn", 0.002, rot=(0, math.radians(42), 0))
        rig.take(m, f"tick{i}", head=(-0.195, -0.036, z), parent="card")
    # the pencil that walks down the list
    m = rig.mark()
    cyl("pbody", 0.014, 0.24, (0.115, -0.070, 0.285), "sand", seg=20)
    cyl("pferrule", 0.016, 0.04, (0.115, -0.070, 0.402), "gold_r", seg=20)
    box("peraser", (0.026, 0.026, 0.022), (0.115, -0.070, 0.430), "coral", 0.006)
    lathe("ptip", [(0, 0), (0.003, 0.012), (0.014, 0.036)], "ink", 20, 40, loc=(0.115, -0.070, 0.135))
    rig.take(m, "pencil", head=(0.115, -0.070, 0.28), parent="card")
    rig.shift(dz=-0.02)

    def anim(t):
        down = pulse(t, 0.06, 0.86, 0.92, 0.995)
        o = {"card": {"rot": [((0, 1, 0), 0.8 * wave(t, 1, 0.1))]},
             "hand": {"rot": [((0, 1, 0), -360 * t)]},
             "pencil": {"loc": (0, 0, -0.40 * down), "rot": [((0, 1, 0), 3 * wave(t, 2))]}}
        for i in range(4):
            s = 0.14 + 0.19 * i
            o[f"tick{i}"] = {"scale": max(0.001, pulse(t, s, s + 0.06, 0.90, 0.98))}
        return o
    return rig, (lambda t: anim((t + 0.06) % 1.0)), 6.0


def m_wallet():
    """The last slide's exhibit: the coin goes in, the flap shuts, the padlock snaps — budget under lock."""
    rig = Rig()
    rig.bone("body", (0, 0, 0))
    m0 = rig.mark()
    box("shell", (0.50, 0.17, 0.34), (0, 0, 0), "leather", 0.030, seg=3)
    box("stitch", (0.512, 0.176, 0.020), (0, 0, -0.155), "gold_r", 0.004)
    box("band", (0.508, 0.178, 0.028), (0, 0, 0.010), "walnut", 0.004)
    for i, (mat, dz) in enumerate((("money", 0.0), ("money2", 0.010), ("money", -0.008))):
        box("note", (0.40, 0.010, 0.155), (0.012 * (i - 1), -0.022 + 0.012 * i, 0.195 + dz), mat, 0.002,
            rot=(0, 0, math.radians(2.5 * i - 2.5)))
    rig.take(m0, "body")
    # the flap with its snap ring
    m = rig.mark()
    box("flap", (0.50, 0.215, 0.048), (0, -0.028, 0.196), "leather", 0.016)
    box("flapedge", (0.50, 0.020, 0.050), (0, -0.130, 0.196), "walnut", 0.006)
    torus("ring", 0.048, 0.011, (0, -0.148, 0.176), "gold_r", rot=(math.radians(90), 0, 0), seg=32, mseg=8)
    rig.take(m, "flap", head=(0, 0.085, 0.200))
    # the padlock hanging from the ring
    m = rig.mark()
    lathe("lock", [(0, 0), (0.076, 0), (0.081, 0.020), (0.081, 0.086), (0.070, 0.102), (0.030, 0.107), (0, 0.107)],
          "brass", 40, 40, loc=(0, -0.148, 0.010))
    cyl("keyhole", 0.014, 0.020, (0, -0.226, 0.046), "ink", rot=(math.radians(90), 0, 0), seg=16)
    rig.take(m, "lock", head=(0, -0.148, 0.010))
    # the shackle: hinged on the right, snaps shut at the end
    m = rig.mark()
    tube("shackle", [(0.058, -0.148, 0.112), (0.060, -0.148, 0.162), (0, -0.148, 0.188), (-0.060, -0.148, 0.162),
                     (-0.058, -0.148, 0.112)], 0.017, "steel_s", 4)
    rig.take(m, "shackle", head=(0.058, -0.148, 0.112))
    # the coin that drops in
    m = rig.mark()
    coin("c", (0, -0.060, 0.205), (math.radians(80), 0, 0), r=0.062, t=0.020)
    rig.take(m, "coin", head=(0, -0.060, 0.205))
    # the guard ring that blooms over the lock
    m = rig.mark()
    torus("guard", 0.105, 0.009, (0, -0.150, 0.056), "gold_r", rot=(math.radians(90), 0, 0), seg=48, mseg=8)
    rig.take(m, "guard", head=(0, -0.150, 0.056))
    rig.shift(dz=-0.03)

    def anim(t):
        openl = pulse(t, 0.05, 0.15, 0.62, 0.74)
        fl = pulse(t, 0.12, 0.28, 0.50, 0.64)
        q = clamp01((t - 0.28) / 0.24)
        g = clamp01((t - 0.74) / 0.24)
        return {
            "body": {"rot": [((1, 0, 0), 0.5 * wave(t, 2))]},
            "flap": {"rot": [((1, 0, 0), -76 * back_out(fl, 1.25))]},
            "shackle": {"rot": [((1, 0, 0), -78 * openl)]},
            "coin": {"loc": (0, 0.012 * q, -0.30 * smooth(q)),
                     "rot": [((0, 0, 1), 540 * smooth(q))],
                     "scale": max(0.001, smooth(q / 0.12) * (1 - smooth((q - 0.86) / 0.14)))},
            "guard": {"scale": (0.25 + 3.0 * g, 0.25 + 3.0 * g, max(0.001, 1 - g ** 2))},
        }
    return rig, anim, 5.5


def m_token():
    """Progress token: the "one-click" coin that rolls along the progress track (static model)."""
    r = 0.5
    lathe("coin", [(0, -0.045), (r * 0.94, -0.045), (r, -0.030), (r, 0.030), (r * 0.94, 0.045), (0, 0.045)],
          "gold_r", 72, 30)
    torus("rim", r * 0.90, 0.014, (0, 0, 0.030), "gold", seg=72, mseg=8)
    lathe("face", [(0, 0.042), (r * 0.88, 0.042), (r * 0.855, 0.050), (0, 0.050)], "gold_satin", 64, 30)
    arrow = [(0.0, 0.0), (-0.035, -0.235), (0.058, -0.170), (0.112, -0.285), (0.175, -0.252), (0.120, -0.140),
             (0.215, -0.128), (0.115, 0.030)]
    o = profile2d("cursor", [arrow], 0.020, 0.005, "ink")
    xform([o], Matrix.Translation((0.03, 0.055, 0.052)))
    for i in range(3):
        a = math.radians(20 + 45 * i)
        box("ray", (0.075, 0.018, 0.014), (0.24 * math.cos(a) + 0.10, 0.24 * math.sin(a) - 0.16, 0.055), "ink", 0.003,
            rot=(0, 0, a))
    torus("click", 0.315, 0.012, (0.09, -0.13, 0.052), "ink", seg=64, mseg=8)
    rot_all(rx=90)


MODELS = {
    "token": m_token, "phone": m_phone, "card": m_card, "cart": m_cart, "lever": m_lever, "clock": m_clock, "receipt": m_receipt,
    "target": m_target, "hourglass": m_hourglass, "scales": m_scales, "survey": m_survey, "backpack": m_backpack,
    "memo": m_memo, "wallet": m_wallet,
}

if __name__ == "__main__":
    want = [a for a in sys.argv[1:] if a in MODELS] or list(MODELS)
    for key in want:
        mm.reset()
        mm._mats.clear()
        _em.clear()
        res = MODELS[key]()
        if res:
            export_rigged(key, *res)
        else:
            mm.export(key)
