# Procedural 3D exhibits for the impulse-spending research presentation.
# Blender (bpy) -> compact GLB with skinned loops that PowerPoint can play.
# The shared mesh/material helpers live in ../schumpeter; the bone rig is in ../cantillon.
import os
import sys
import math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SCH_MODELS = os.path.join(ROOT, "schumpeter", "models")
CANT_MODELS = os.path.join(ROOT, "cantillon", "models")
sys.path.insert(0, SCH_MODELS)
import make_models as mm  # noqa: E402
sys.path.insert(0, CANT_MODELS)
from rig import Rig, export_rigged, ease, wave  # noqa: E402
from make_models import box, cyl, sphere, torus, tube, lathe  # noqa: E402

mm.OUT = os.path.join(HERE, "glb")
os.makedirs(mm.OUT, exist_ok=True)
TAU = math.tau


def custom_mat(name, color, metallic=0.0, roughness=0.4, emission=None):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission[0], 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission[1]
    return m


def materials():
    # A restrained contemporary palette: ink, porcelain, warm brass, mint and coral.
    return {
        "ink": custom_mat("Impulse · ink", (0.022, 0.046, 0.080), 0.45, 0.28),
        "screen": custom_mat("Impulse · screen", (0.018, 0.075, 0.112), 0.12, 0.26),
        "porcelain": custom_mat("Impulse · porcelain", (0.82, 0.83, 0.77), 0.02, 0.38),
        "mint": custom_mat("Impulse · mint", (0.055, 0.61, 0.56), 0.24, 0.27, ((0.08, 0.65, 0.59), 0.75)),
        "coral": custom_mat("Impulse · coral", (0.92, 0.25, 0.22), 0.10, 0.32),
        "gold": custom_mat("Impulse · brass", (0.83, 0.51, 0.20), 0.82, 0.31),
        "paper": custom_mat("Impulse · paper", (0.91, 0.87, 0.77), 0.0, 0.72),
        "brain": custom_mat("Impulse · brain", (0.78, 0.34, 0.33), 0.03, 0.45),
        "fold": custom_mat("Impulse · neural folds", (0.44, 0.15, 0.18), 0.02, 0.5),
        "glass": custom_mat("Impulse · frosted glass", (0.20, 0.66, 0.70), 0.0, 0.24),
        "graphite": custom_mat("Impulse · graphite", (0.07, 0.09, 0.12), 0.68, 0.34),
    }


# bpy is re-exported by the shared helper module; keeping it here also makes the
# model script work from a clean system Blender Python install.
bpy = mm.bpy


def m_phone():
    """A native 3D phone: a shopping tile and notification gently pulse in a loop."""
    c = materials()
    rig = Rig()
    # rounded aluminium body and inset glass, front faces the viewer (-Y)
    box("phone_body", (0.88, 0.09, 1.62), (0, 0, 0), c["graphite"], 0.09, seg=4)
    box("glass_screen", (0.79, 0.014, 1.49), (0, -0.054, 0), c["screen"], 0.07, seg=5)
    box("speaker", (0.18, 0.012, 0.025), (0, -0.066, 0.655), c["graphite"], 0.012, seg=3)
    sphere("camera", 0.025, (0.17, -0.068, 0.655), c["mint"], 16, 8)
    # quiet interface: header, product card, product bag, price and checkout button
    box("header_line", (0.43, 0.012, 0.025), (0, -0.068, 0.53), c["porcelain"], 0.012)
    box("product_tile", (0.61, 0.018, 0.48), (0, -0.072, 0.115), c["ink"], 0.055, seg=3)
    box("mini_bag", (0.25, 0.035, 0.23), (0, -0.098, 0.10), c["gold"], 0.035, seg=3)
    torus("bag_handle", 0.072, 0.012, (0, -0.105, 0.245), c["porcelain"], rot=(math.radians(90), 0, 0), seg=36, mseg=8)
    box("tile_caption", (0.30, 0.012, 0.02), (0, -0.085, -0.085), c["mint"], 0.008)
    box("price_line", (0.18, 0.012, 0.018), (-0.16, -0.085, -0.14), c["porcelain"], 0.006)
    box("buy_button", (0.57, 0.026, 0.12), (0, -0.078, -0.47), c["coral"], 0.04, seg=4)
    box("button_mark", (0.25, 0.012, 0.025), (0, -0.096, -0.47), c["porcelain"], 0.012)
    box("home_bar", (0.20, 0.015, 0.018), (0, -0.067, -0.68), c["porcelain"], 0.009)
    for side in (-1, 1):
        box("side_key", (0.018, 0.07, 0.18), (side * 0.449, 0.0, 0.28), c["gold"], 0.008)
    # attention ping: a small coral badge with a brass halo, kept inside the rest-pose bounds
    mark = rig.mark()
    sphere("notification", 0.078, (0.325, -0.095, 0.555), c["coral"], 32, 16)
    torus("notification_rim", 0.086, 0.009, (0.325, -0.100, 0.555), c["gold"], rot=(math.radians(90), 0, 0), seg=40, mseg=8)
    rig.take(mark, "ping", head=(0.325, -0.095, 0.555))

    def anim(t):
        pulse = 0.055 * math.sin(TAU * 2 * t)
        return {"ping": {"scale": 1.0 + 0.50 * (0.5 + 0.5 * math.sin(TAU * 2 * t)),
                         "loc": (0, 0, pulse)}}
    return rig, anim, 4.0


def m_brain():
    """A stylised brain with a pulsing choice-signal; not a literal neural scan."""
    c = materials()
    rig = Rig()
    lathe("pedestal", [(0, 0), (0.34, 0), (0.36, 0.025), (0.33, 0.06), (0.19, 0.10), (0.10, 0.14), (0, 0.14)], c["graphite"], 64)
    cyl("stem", 0.10, 0.20, (0, 0, 0.22), c["gold"], seg=32)
    sphere("brain_core", 0.32, (0, 0, 0.58), c["brain"], 40, 24).scale = (1.20, 0.86, 0.90)
    # Paired lobes make the silhouette readable from the presentation camera.
    lobes = [(-0.20, 0.00, 0.56, (0.72, 0.86, 0.80)), (0.20, 0.00, 0.56, (0.72, 0.86, 0.80)),
             (-0.15, -0.02, 0.77, (0.76, 0.80, 0.66)), (0.15, -0.02, 0.77, (0.76, 0.80, 0.66)),
             (-0.29, 0.00, 0.62, (0.55, 0.77, 0.70)), (0.29, 0.00, 0.62, (0.55, 0.77, 0.70))]
    for i, (x, y, z, sc) in enumerate(lobes):
        sphere(f"lobe_{i}", 0.205, (x, y, z), c["brain"], 28, 16).scale = sc
    # Fine dark folds on the front face add a hand-built, sculptural feel.
    for side in (-1, 1):
        for k in range(3):
            z0 = 0.44 + 0.13 * k
            x0 = side * (0.06 + 0.035 * k)
            pts = [(x0, -0.278, z0 - 0.08), (x0 + side * 0.025, -0.306, z0 - 0.035),
                   (x0 - side * 0.018, -0.312, z0 + 0.015), (x0 + side * 0.02, -0.287, z0 + 0.07)]
            tube(f"fold_{side}_{k}", pts, 0.008, c["fold"], 3, False)
    sphere("node_a", 0.025, (-0.28, -0.20, 0.70), c["mint"], 14, 8)
    sphere("node_b", 0.025, (0.27, -0.21, 0.46), c["gold"], 14, 8)
    # A single visible pulse, animated as a skin so it plays in PowerPoint 365.
    mark = rig.mark()
    sphere("choice_signal", 0.075, (0, -0.405, 0.60), c["mint"], 28, 16)
    torus("choice_ring", 0.115, 0.009, (0, -0.407, 0.60), c["porcelain"], rot=(math.radians(90), 0, 0), seg=40, mseg=8)
    rig.take(mark, "signal", head=(0, -0.405, 0.60))

    def anim(t):
        beat = 0.75 + 0.55 * (0.5 + 0.5 * math.sin(TAU * 2 * t))
        return {"signal": {"scale": (beat, beat, beat),
                           "rot": [((0, 0, 1), 18.0 * math.sin(TAU * t))],
                           "loc": (0.025 * math.sin(TAU * t), 0, 0)}}
    return rig, anim, 4.0


def m_paylater():
    """Card and four visible instalment tokens; two coins make a restrained looping lift."""
    c = materials()
    rig = Rig()
    box("card", (1.20, 0.065, 0.76), (-0.10, 0, 0), c["ink"], 0.09, seg=4)
    box("card_band", (0.95, 0.012, 0.035), (-0.10, -0.038, -0.23), c["mint"], 0.015)
    box("chip", (0.20, 0.018, 0.15), (-0.48, -0.045, 0.16), c["gold"], 0.025, seg=3)
    box("chip_line_1", (0.15, 0.012, 0.009), (-0.48, -0.057, 0.16), c["graphite"], 0.003)
    box("chip_line_2", (0.009, 0.012, 0.11), (-0.48, -0.057, 0.16), c["graphite"], 0.003)
    # Four discrete markers make the split-payment idea legible without embedding tiny text.
    for i in range(4):
        x = -0.38 + i * 0.19
        sphere(f"installment_dot_{i}", 0.045, (x, -0.052, -0.015), c["porcelain"] if i == 0 else c["mint"], 18, 10)
    # Contactless motif.
    for i in range(3):
        pts = [(-0.02 + 0.09 * i, -0.051, 0.20), (0.02 + 0.09 * i, -0.055, 0.16), (0.03 + 0.09 * i, -0.051, 0.11)]
        tube(f"contactless_{i}", pts, 0.007, c["porcelain"], 2, False)
    # Coins to the right of the card; their faces point toward the viewer.
    coin_specs = [(0.72, 0.29, "coin_a"), (0.78, -0.12, "coin_b"), (0.70, -0.36, "coin_c")]
    for x, z, name in coin_specs:
        mark = rig.mark()
        cyl(name, 0.145, 0.045, (x, -0.07, z), c["gold"], rot=(math.radians(90), 0, 0), seg=48, bevel=0.007)
        torus(name + "_rim", 0.132, 0.008, (x, -0.098, z), c["porcelain"], rot=(math.radians(90), 0, 0), seg=40, mseg=8)
        sphere(name + "_emboss", 0.036, (x, -0.104, z), c["porcelain"], 20, 10)
        rig.take(mark, name, head=(x, -0.07, z))

    def anim(t):
        return {
            "coin_a": {"loc": (0, 0, 0.13 * math.sin(TAU * t)),
                       "rot": [((1, 0, 0), 30 * math.sin(TAU * t)), ((0, 0, 1), 12 * math.sin(TAU * t))]},
            "coin_b": {"loc": (0, 0, 0.10 * math.sin(TAU * t + math.pi)),
                       "rot": [((1, 0, 0), 24 * math.sin(TAU * t + math.pi))]},
            "coin_c": {"rot": [((1, 0, 0), 18 * math.sin(TAU * t + math.pi / 2))]},
        }
    return rig, anim, 4.0


def m_clipboard():
    """Survey board: checkboxes, a simple chart and a pen that nods as if taking notes."""
    c = materials()
    rig = Rig()
    box("board", (1.08, 0.09, 1.54), (0, 0, 0), c["graphite"], 0.06, seg=4)
    box("paper_sheet", (0.91, 0.014, 1.34), (0, -0.053, -0.015), c["paper"], 0.025, seg=3)
    box("clip", (0.35, 0.045, 0.14), (0, -0.078, 0.71), c["gold"], 0.025, seg=4)
    for i, z in enumerate((0.42, 0.19, -0.04, -0.27)):
        box(f"check_box_{i}", (0.095, 0.018, 0.095), (-0.31, -0.073, z), c["mint"] if i < 3 else c["coral"], 0.012)
        box(f"row_line_a_{i}", (0.42, 0.012, 0.020), (0.06, -0.069, z + 0.018), c["graphite"], 0.008)
        box(f"row_line_b_{i}", (0.27 if i % 2 else 0.34, 0.012, 0.012), (-0.005, -0.069, z - 0.026), c["gold"], 0.006)
    # small, legible chart bars at the bottom of the sheet
    for i, h in enumerate((0.18, 0.28, 0.40, 0.30)):
        x = -0.25 + i * 0.17
        box(f"bar_{i}", (0.085, 0.018, h), (x, -0.072, -0.53 + h / 2), c["mint"] if i != 2 else c["coral"], 0.012)
    box("chart_axis", (0.79, 0.012, 0.014), (0.07, -0.069, -0.54), c["graphite"], 0.005)
    # Mechanical pencil along the right margin.
    mark = rig.mark()
    cyl("pencil_barrel", 0.035, 0.78, (0.42, -0.115, -0.02), c["gold"], rot=(0, math.radians(-5), 0), seg=28)
    cyl("pencil_cap", 0.038, 0.10, (0.42, -0.115, 0.42), c["coral"], seg=24)
    sphere("pencil_tip", 0.034, (0.455, -0.115, -0.425), c["graphite"], 16, 8)
    rig.take(mark, "pen", head=(0.42, -0.115, 0.02))

    def anim(t):
        return {"pen": {"rot": [((0, 1, 0), 13.0 * math.sin(TAU * t)), ((1, 0, 0), 6.0 * math.sin(TAU * t))],
                         "loc": (0, 0, 0.035 * math.sin(TAU * t))}}
    return rig, anim, 4.0


def m_timer():
    """Hourglass with five skinned grains flowing visibly in front of the glass."""
    c = materials()
    rig = Rig()
    H = 0.61
    # Finials, rims and three slim uprights.
    for z in (-0.71, 0.71):
        cyl("end_cap", 0.34, 0.075, (0, 0, z), c["graphite"], seg=56, bevel=0.015)
        torus("end_rim", 0.31, 0.018, (0, 0, z + (0.045 if z > 0 else -0.045)), c["gold"], seg=56, mseg=8)
    for k in range(3):
        a = TAU * k / 3 + 0.35
        x, y = 0.255 * math.cos(a), 0.255 * math.sin(a)
        tube(f"upright_{k}", [(x, y, -0.66), (x * 0.94, y * 0.94, -0.30), (x * 0.94, y * 0.94, 0.30), (x, y, 0.66)], 0.021, c["gold"], 4, False)
    profile = [(0, -0.62), (0.20, -0.62), (0.235, -0.47), (0.19, -0.28), (0.08, -0.08), (0.055, 0),
               (0.08, 0.08), (0.19, 0.28), (0.235, 0.47), (0.20, 0.62), (0, 0.62)]
    lathe("glass_body", profile, c["glass"], 56, 40)
    # Sand piles and a fine central stream; the mound levels subtly cycle with the grains.
    mark = rig.mark()
    lathe("sand_top", [(0, 0.16), (0.13, 0.16), (0.18, 0.23), (0.12, 0.34), (0.05, 0.41), (0, 0.43)], c["gold"], 48, 40)
    rig.take(mark, "sandtop", head=(0, 0, 0.16))
    mark = rig.mark()
    lathe("sand_bottom", [(0, -0.46), (0.20, -0.46), (0.22, -0.39), (0.15, -0.31), (0.08, -0.25), (0, -0.23)], c["gold"], 48, 40)
    rig.take(mark, "sandbottom", head=(0, 0, -0.46))
    cyl("sand_stream", 0.009, 0.28, (0, -0.04, 0.01), c["gold"], seg=10)
    phases = (0.00, 0.20, 0.40, 0.60, 0.80)
    for i, phase in enumerate(phases):
        z0 = 0.30 - 0.60 * phase
        mark = rig.mark()
        sphere(f"grain_{i}", 0.031, (0, -0.285, z0), c["gold"], 18, 10)
        rig.take(mark, f"grain_{i}", head=(0, -0.285, z0))

    def anim(t):
        fill = 0.5 - 0.5 * math.cos(TAU * t)
        pose = {
            "sandtop": {"scale": (1.0, 1.0, 1.0 - 0.45 * fill)},
            "sandbottom": {"scale": (1.0, 1.0, 0.75 + 0.40 * fill)},
        }
        for i, phase in enumerate(phases):
            target = 0.30 - 0.60 * ((t + phase) % 1.0)
            z0 = 0.30 - 0.60 * phase
            pose[f"grain_{i}"] = {"loc": (0, 0, target - z0), "scale": 0.9 + 0.1 * math.sin(TAU * (t + phase))}
        return pose
    return rig, anim, 5.0


def m_bag():
    """A tactile shopping bag and receipt; the receipt rises clearly in a short loop."""
    c = materials()
    rig = Rig()
    # Structured paper bag with dark gussets and a contrasting front panel.
    box("bag_body", (0.96, 0.57, 0.90), (0, 0, -0.12), c["porcelain"], 0.035, seg=3)
    box("bag_front", (0.72, 0.022, 0.66), (0, -0.301, -0.14), c["mint"], 0.045, seg=4)
    box("bag_seal", (0.28, 0.018, 0.055), (0, -0.319, -0.17), c["coral"], 0.018)
    # Cord handles are deliberately oversized so they remain visible on a projector.
    tube("handle_left", [(-0.28, -0.18, 0.32), (-0.30, -0.20, 0.58), (-0.20, -0.20, 0.68), (-0.07, -0.20, 0.61), (-0.08, -0.20, 0.32)], 0.018, c["gold"], 4, False)
    tube("handle_right", [(0.08, -0.18, 0.32), (0.07, -0.20, 0.61), (0.20, -0.20, 0.68), (0.30, -0.20, 0.58), (0.28, -0.18, 0.32)], 0.018, c["gold"], 4, False)
    # Tissue paper peeking from the open top.
    box("tissue_left", (0.22, 0.025, 0.38), (-0.23, -0.12, 0.34), c["paper"], 0.015, rot=(0, math.radians(-16), 0))
    box("tissue_right", (0.22, 0.025, 0.38), (0.22, -0.10, 0.35), c["paper"], 0.015, rot=(0, math.radians(18), 0))
    # A small star-like medallion on the front.
    sphere("seal", 0.085, (0, -0.335, -0.14), c["gold"], 28, 14)
    sphere("seal_core", 0.042, (0, -0.381, -0.14), c["coral"], 20, 10)
    # Receipt, ruled in low relief, animated on a short, deliberately subtle bob.
    mark = rig.mark()
    box("receipt", (0.30, 0.022, 0.44), (0.10, -0.16, 0.51), c["paper"], 0.014, rot=(math.radians(-5), math.radians(11), math.radians(4)))
    for i, w in enumerate((0.18, 0.22, 0.15, 0.20)):
        box(f"receipt_line_{i}", (w, 0.009, 0.012), (0.10, -0.176, 0.64 - 0.075 * i), c["graphite"], 0.004)
    rig.take(mark, "receipt", head=(0.10, -0.16, 0.51))

    def anim(t):
        q = math.sin(TAU * t)
        return {"receipt": {"loc": (0.0, 0.0, 0.11 * q), "rot": [((0, 1, 0), 9.0 * q)]}}
    return rig, anim, 4.0


MODELS = {
    "phone": m_phone,
    "brain": m_brain,
    "paylater": m_paylater,
    "clipboard": m_clipboard,
    "timer": m_timer,
    "bag": m_bag,
}


if __name__ == "__main__":
    requested = [arg for arg in sys.argv[1:] if arg in MODELS] or list(MODELS)
    for key in requested:
        mm.reset()
        mm._mats.clear()
        rig_data = MODELS[key]()
        export_rigged(key, *rig_data)
