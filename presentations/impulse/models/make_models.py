# Procedural, looping PowerPoint 3D exhibits for the impulse-spending deck.
# Built in Blender (bpy); all geometry and animation are local and reproducible.
#
#   LD_LIBRARY_PATH=/tmp/bstub python3 models/make_models.py
#   LD_LIBRARY_PATH=/tmp/bstub python3 models/make_models.py chestnut smartphone cart wallet
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCH_MODELS = os.path.join(HERE, "..", "..", "schumpeter", "models")
sys.path.insert(0, SCH_MODELS)
import make_models as mm  # noqa: E402
from make_models import bpy, Vector, box, cyl, sphere, torus, tube  # noqa: E402
CANT_MODELS = os.path.join(HERE, "..", "..", "cantillon", "models")
sys.path.insert(0, CANT_MODELS)
from rig import Rig, export_rigged  # noqa: E402

mm.OUT = os.path.join(HERE, "glb")
os.makedirs(mm.OUT, exist_ok=True)
TAU = math.tau


def material(name, rgb, roughness=0.4, metallic=0.0, coat=0.0, emit=None):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if coat:
        bsdf.inputs["Coat Weight"].default_value = coat
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit[0], 1)
        bsdf.inputs["Emission Strength"].default_value = emit[1]
    return m


def prepare():
    mm.reset()
    mm._mats.clear()
    return {
        "shell": material("chestnut_glaze", (0.34, 0.105, 0.028), 0.24, 0.04, 0.42),
        "shell_light": material("nut_highlight", (0.55, 0.24, 0.055), 0.31, 0.02, 0.32),
        "burr": material("burr_green", (0.15, 0.30, 0.045), 0.62, 0.0, 0.08),
        "cream": material("cream", (0.92, 0.72, 0.43), 0.7),
        "white": material("eye_white", (0.98, 0.91, 0.76), 0.3),
        "black": material("pupil", (0.018, 0.013, 0.012), 0.24),
        "pink": material("cheek", (0.76, 0.20, 0.13), 0.55),
        "screen": material("screen", (0.025, 0.055, 0.11), 0.25, 0.12, 0.25),
        "teal": material("teal", (0.03, 0.49, 0.46), 0.3, 0.2, 0.18),
        "mint": material("mint", (0.34, 0.82, 0.66), 0.34),
        "coral": material("coral", (0.96, 0.22, 0.17), 0.34, 0.05, 0.2),
        "gold": material("gold", (0.93, 0.56, 0.15), 0.3, 0.62, 0.2),
        "cream_paper": material("paper", (0.95, 0.84, 0.62), 0.82),
        "leather": material("wallet_leather", (0.19, 0.061, 0.028), 0.48, 0.0, 0.25),
        "leather_light": material("wallet_edge", (0.43, 0.17, 0.062), 0.52, 0.0, 0.16),
        "metal": material("cart_metal", (0.39, 0.48, 0.49), 0.3, 0.76),
        "rubber": material("wheel_rubber", (0.035, 0.044, 0.05), 0.82),
        "plum": material("plum", (0.45, 0.075, 0.25), 0.4, 0.04, 0.16),
        "blue": material("blue", (0.04, 0.25, 0.78), 0.34, 0.13, 0.16),
        "green": material("product_green", (0.18, 0.53, 0.18), 0.42),
    }


def mesh_sphere(name, loc, scale, mat, segments=48, rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    return mm.finish(o, mat, 80)


def cone_to(name, base, direction, radius, length, mat):
    d = Vector(direction).normalized()
    center = Vector(base) + d * (length * 0.5)
    bpy.ops.mesh.primitive_cone_add(vertices=9, radius1=radius, radius2=0.002,
                                    depth=length, location=center)
    o = bpy.context.object
    o.name = name
    o.rotation_euler = Vector((0, 0, 1)).rotation_difference(d).to_euler()
    return mm.finish(o, mat, 20)


def m_chestnut():
    """The recurring meme mascot: a glossy chestnut, green burr crown, face and a looping hello."""
    mats = prepare()
    rig = Rig()

    main = rig.mark()
    # An organically tapered conker, with a flattened lower tip and a warm shell.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=40, radius=1, location=(0, 0, 0))
    nut = bpy.context.object
    nut.name = "chestnut"
    for v in nut.data.vertices:
        x, y, z = v.co
        taper = 1.0 - 0.12 * z
        bottom = max(0.82, 1.0 + 0.17 * z)
        v.co = (x * 0.52 * taper * bottom, y * 0.39 * taper * bottom, 0.72 + z * 0.68)
    mm.finish(nut, mats["shell"], 80)
    # Soft warm highlight along the upper shell.
    mesh_sphere("shell_glint", (-0.16, -0.245, 1.08), (0.13, 0.025, 0.23), mats["shell_light"], 24, 16)
    # The pale hilum mark is the unmistakable chestnut detail.
    mesh_sphere("hilum", (0, -0.353, 0.37), (0.19, 0.045, 0.105), mats["cream"], 32, 20)
    mesh_sphere("hilum_edge", (0, -0.373, 0.37), (0.13, 0.018, 0.052), mats["shell_light"], 28, 16)

    # Friendly but slightly bewildered face, facing the PowerPoint viewer (-Y).
    for side in (-1, 1):
        x = side * 0.155
        mesh_sphere("eye_white", (x, -0.344, 0.92), (0.086, 0.055, 0.105), mats["white"], 24, 16)
        mesh_sphere("pupil", (x - side * 0.012, -0.392, 0.918), (0.041, 0.028, 0.057), mats["black"], 20, 12)
        mesh_sphere("eye_glint", (x - side * 0.026, -0.416, 0.944), (0.014, 0.011, 0.018), mats["white"], 12, 8)
        mesh_sphere("cheek", (side * 0.29, -0.314, 0.73), (0.053, 0.023, 0.035), mats["pink"], 18, 10)
    tube("smile", [(-0.105, -0.365, 0.70), (-0.066, -0.387, 0.665), (0, -0.394, 0.653),
                     (0.066, -0.387, 0.665), (0.105, -0.365, 0.70)], 0.012, mats["black"], 4, True)

    # A little green spiky husk sits behind the crown, like the source photo.
    mesh_sphere("green_burr", (0, 0.105, 1.31), (0.34, 0.20, 0.17), mats["burr"], 32, 18)
    for i in range(11):
        a = TAU * i / 11
        d = (0.72 * math.cos(a), 0.42 * math.sin(a), 0.18 + 0.28 * math.cos(a * 2))
        base = (0.24 * math.cos(a), 0.115 + 0.11 * math.sin(a), 1.30 + 0.045 * math.cos(a * 2))
        cone_to("burr_spike", base, d, 0.042, 0.17 if i % 2 else 0.21, mats["burr"])

    # Stubby legs and tiny shoes make the mascot feel like a character, not a walnut.
    for side in (-1, 1):
        x = side * 0.19
        tube("leg", [(x, 0.0, 0.15), (x + side * 0.015, -0.01, 0.075)], 0.038, mats["leather"], 4, False)
        mesh_sphere("shoe", (x + side * 0.055, -0.03, 0.055), (0.10, 0.075, 0.048), mats["leather"], 18, 10)
    rig.take(main, "body", head=(0, 0, 0.70))

    # Arms are separately skinned so Kash can do a little wave on each slide.
    for side, name in ((-1, "armL"), (1, "armR")):
        pivot = (side * 0.42, 0.015, 0.73)
        arm = rig.mark()
        tube("arm", [pivot, (side * 0.53, -0.01, 0.78), (side * 0.57, -0.03, 0.88)], 0.045, mats["shell_light"], 5, True)
        mesh_sphere("mitten", (side * 0.58, -0.04, 0.89), (0.085, 0.075, 0.072), mats["cream"], 18, 12)
        rig.take(arm, name, head=pivot, parent="body")

    def anim(t):
        w = math.sin(TAU * t)
        return {
            "body": {"loc": (0, 0, 0.032 * math.sin(TAU * t)), "rot": [((0, 1, 0), 2.5 * w)]},
            "armL": {"rot": [((0, 1, 0), 14 + 22 * math.sin(TAU * t))]},
            "armR": {"rot": [((0, 1, 0), -14 - 22 * math.sin(TAU * t))]},
        }
    export_rigged("chestnut", rig, anim, seconds=4.0)


def m_smartphone():
    """A slightly-too-convenient phone with an animated, irresistible pay button."""
    mats = prepare()
    rig = Rig()
    body = rig.mark()
    # rounded frame and deep screen, standing upright and facing the viewer
    box("phone_frame", (0.78, 0.16, 1.48), (0, 0, 0.79), mats["teal"], 0.075, seg=4)
    box("phone_screen", (0.67, 0.028, 1.30), (0, -0.092, 0.79), mats["screen"], 0.04, seg=4)
    box("speaker", (0.17, 0.018, 0.022), (0, -0.114, 1.395), mats["metal"], 0.01, seg=3)
    mesh_sphere("camera", (0.145, -0.118, 1.395), (0.023, 0.013, 0.023), mats["black"], 14, 8)

    # Interface elements: a sale tile, a product card, a cart and a big pay pill.
    box("deal_tile", (0.50, 0.018, 0.24), (0, -0.12, 1.18), mats["plum"], 0.035, seg=3)
    mesh_sphere("deal_dot", (-0.19, -0.135, 1.18), (0.046, 0.015, 0.046), mats["gold"], 16, 10)
    box("deal_text_1", (0.19, 0.015, 0.025), (0.045, -0.135, 1.21), mats["cream_paper"], 0.008, seg=2)
    box("deal_text_2", (0.13, 0.015, 0.018), (0.015, -0.135, 1.16), mats["mint"], 0.006, seg=2)
    box("product_card", (0.50, 0.018, 0.38), (0, -0.12, 0.84), mats["blue"], 0.03, seg=3)
    mesh_sphere("product", (0, -0.15, 0.91), (0.12, 0.045, 0.12), mats["gold"], 20, 12)
    box("product_line_1", (0.22, 0.015, 0.022), (0.10, -0.15, 0.77), mats["cream_paper"], 0.006, seg=2)
    box("product_line_2", (0.16, 0.015, 0.018), (0.07, -0.15, 0.72), mats["mint"], 0.006, seg=2)
    box("installment_chip", (0.42, 0.018, 0.10), (0, -0.12, 0.56), mats["gold"], 0.018, seg=3)
    for i in range(3):
        mesh_sphere("installment_dot", (-0.13 + i * 0.13, -0.137, 0.56), (0.022, 0.012, 0.022), mats["screen"], 12, 8)
    box("pay_button", (0.47, 0.04, 0.15), (0, -0.14, 0.32), mats["coral"], 0.06, seg=5)
    # a tiny outline shopping bag on the button
    tube("cart_handle", [(-0.08, -0.17, 0.34), (-0.06, -0.17, 0.39), (0.06, -0.17, 0.39), (0.08, -0.17, 0.34)], 0.009, mats["cream_paper"], 3, False)
    tube("cart_basket", [(-0.09, -0.17, 0.34), (-0.06, -0.17, 0.28), (0.06, -0.17, 0.28), (0.09, -0.17, 0.34)], 0.009, mats["cream_paper"], 3, False)
    for x in (-0.045, 0.045):
        mesh_sphere("cart_wheel", (x, -0.175, 0.25), (0.015, 0.012, 0.015), mats["cream_paper"], 10, 6)
    rig.take(body, "body", head=(0, 0, 0.72))

    badge = rig.mark()
    mesh_sphere("notification", (0.30, -0.13, 1.27), (0.075, 0.035, 0.075), mats["coral"], 20, 12)
    mesh_sphere("notification_dot", (0.30, -0.166, 1.27), (0.018, 0.012, 0.018), mats["cream_paper"], 12, 8)
    rig.take(badge, "badge", head=(0.30, -0.13, 1.27), parent="body")

    button = rig.mark()
    # A small gold sparkle rises above the pay button.
    mesh_sphere("sparkle", (0.22, -0.15, 0.36), (0.035, 0.025, 0.035), mats["gold"], 12, 8)
    rig.take(button, "spark", head=(0.22, -0.15, 0.36), parent="body")

    def anim(t):
        return {
            "body": {"rot": [((0, 0, 1), 2.0 * math.sin(TAU * t))]},
            "badge": {"rot": [((0, 0, 1), 10 * math.sin(TAU * t))], "scale": 1.0 + 0.08 * math.sin(TAU * t)},
            "spark": {"loc": (0, 0, 0.035 * math.sin(TAU * t + math.pi / 2)), "scale": 0.8 + 0.2 * (0.5 + 0.5 * math.sin(TAU * t))},
        }
    export_rigged("smartphone", rig, anim, seconds=4.0)


def m_cart():
    """An online-shopping basket on wheels: the products keep trying to jump in."""
    mats = prepare()
    rig = Rig()
    base = rig.mark()
    # trolley chassis
    box("basket_floor", (1.12, 0.72, 0.12), (0, 0.02, 0.44), mats["metal"], 0.045, seg=3)
    # top rim and side rails
    for y in (-0.33, 0.37):
        tube("rim", [(-0.58, y, 0.91), (0.58, y, 0.91)], 0.025, mats["metal"], 3, False)
        for i in range(9):
            x = -0.52 + i * 0.13
            tube("basket_rail", [(x, y, 0.48), (x, y, 0.91)], 0.012, mats["metal"], 2, False)
    for x in (-0.57, 0.57):
        tube("rim_side", [(x, -0.33, 0.91), (x, 0.37, 0.91)], 0.025, mats["metal"], 3, False)
        for i in range(5):
            y = -0.28 + i * 0.16
            tube("basket_cross", [(x, y, 0.48), (x, y, 0.91)], 0.012, mats["metal"], 2, False)
    for z in (0.61, 0.75):
        tube("basket_grid", [(-0.55, -0.33, z), (0.55, -0.33, z)], 0.012, mats["metal"], 2, False)
        tube("basket_grid_back", [(-0.55, 0.37, z), (0.55, 0.37, z)], 0.012, mats["metal"], 2, False)
        for x in (-0.57, 0.57):
            tube("basket_grid_side", [(x, -0.33, z), (x, 0.37, z)], 0.012, mats["metal"], 2, False)
    # handle and two axles
    tube("handle_stem", [(-0.48, 0.34, 0.87), (-0.66, 0.50, 1.12), (-0.76, 0.50, 1.18)], 0.035, mats["metal"], 4, False)
    tube("handle_grip", [(-0.78, 0.50, 1.18), (-0.48, 0.50, 1.18)], 0.045, mats["leather"], 4, False)
    for x in (-0.42, 0.42):
        for y in (-0.30, 0.30):
            cyl("wheel_axle", 0.035, 0.08, (x, y, 0.21), mats["metal"], rot=(math.pi / 2, 0, 0), seg=16)
            mesh_sphere("wheel", (x, y, 0.21), (0.10, 0.07, 0.10), mats["rubber"], 18, 10)
    rig.take(base, "frame", head=(0, 0, 0.45))

    # The cart contents are independently animated, but remain inside the basket silhouette.
    for name, x, y, z, size, mat in (
        ("snack", -0.26, -0.07, 0.78, (0.28, 0.25, 0.43), mats["plum"]),
        ("box", 0.08, 0.04, 0.76, (0.34, 0.26, 0.38), mats["blue"]),
    ):
        group = rig.mark()
        box(name + "_pack", size, (x, y, z), mat, 0.035, seg=3)
        box(name + "_label", (size[0] * 0.50, 0.018, size[2] * 0.22), (x, y - size[1] / 2 - 0.01, z), mats["cream_paper"], 0.012, seg=2)
        rig.take(group, name, head=(x, y, z), parent="frame")
    can = rig.mark()
    cyl("can", 0.14, 0.43, (0.36, -0.03, 0.77), mats["mint"], seg=40, bevel=0.018)
    cyl("can_top", 0.11, 0.018, (0.36, -0.03, 0.992), mats["metal"], seg=32)
    box("can_logo", (0.15, 0.014, 0.08), (0.36, -0.174, 0.78), mats["coral"], 0.025, seg=3)
    rig.take(can, "can", head=(0.36, -0.03, 0.77), parent="frame")

    fruit = rig.mark()
    mesh_sphere("fruit", (-0.01, -0.20, 0.94), (0.15, 0.15, 0.16), mats["gold"], 24, 16)
    mesh_sphere("fruit_leaf", (-0.01, -0.20, 1.10), (0.045, 0.025, 0.10), mats["green"], 14, 8)
    rig.take(fruit, "fruit", head=(-0.01, -0.20, 0.94), parent="frame")

    def anim(t):
        w = math.sin(TAU * t)
        return {
            "frame": {"rot": [((0, 0, 1), 1.5 * w)]},
            "snack": {"loc": (0, 0, 0.025 * w), "rot": [((0, 1, 0), 3 * w)]},
            "box": {"loc": (0, 0, -0.02 * w), "rot": [((1, 0, 0), -2 * w)]},
            "can": {"rot": [((0, 0, 1), 2 * w)]},
            "fruit": {"loc": (0, 0, 0.045 * math.sin(TAU * t + 0.4))},
        }
    export_rigged("cart", rig, anim, seconds=4.0)


def m_wallet():
    """A wallet that opens a little; the card and coin gently bounce back into view."""
    mats = prepare()
    rig = Rig()
    body = rig.mark()
    box("wallet_base", (1.18, 0.27, 0.78), (0, 0.04, 0.58), mats["leather"], 0.09, seg=4)
    box("wallet_front", (1.08, 0.055, 0.69), (0, -0.125, 0.55), mats["leather_light"], 0.075, seg=4)
    # Stitch lines frame the front cover.
    for side in (-1, 1):
        tube("stitch_side", [(side * 0.47, -0.162, 0.28), (side * 0.47, -0.162, 0.83)], 0.009, mats["cream"], 2, False)
    tube("stitch_bottom", [(-0.46, -0.162, 0.26), (0.46, -0.162, 0.26)], 0.009, mats["cream"], 2, False)
    box("clasp", (0.27, 0.08, 0.12), (0, -0.18, 0.52), mats["gold"], 0.035, seg=3)
    box("clasp_inlay", (0.13, 0.02, 0.035), (0, -0.228, 0.52), mats["leather"], 0.012, seg=2)
    rig.take(body, "body", head=(0, 0, 0.58))

    card = rig.mark()
    # teal card peeking from the top slot, chip toward the viewer
    box("bank_card", (0.50, 0.045, 0.32), (0.13, -0.065, 1.00), mats["teal"], 0.045, seg=4)
    box("card_chip", (0.11, 0.018, 0.09), (0.13, -0.093, 0.99), mats["gold"], 0.012, seg=2)
    tube("card_mark", [(0.25, -0.095, 0.91), (0.39, -0.095, 0.91)], 0.009, mats["cream_paper"], 2, False)
    rig.take(card, "card", head=(0.13, -0.065, 0.91), parent="body")

    coin = rig.mark()
    cyl("coin", 0.19, 0.045, (-0.38, -0.23, 0.34), mats["gold"], rot=(math.pi / 2, 0, 0), seg=40, bevel=0.012)
    torus("coin_rim", 0.15, 0.009, (-0.38, -0.258, 0.34), mats["cream"], rot=(math.pi / 2, 0, 0), seg=36, mseg=8)
    rig.take(coin, "coin", head=(-0.38, -0.23, 0.34), parent="body")

    def anim(t):
        w = math.sin(TAU * t)
        return {
            "body": {"rot": [((0, 0, 1), 1.5 * w)]},
            "card": {"loc": (0, 0, 0.04 * (0.5 + 0.5 * w)), "rot": [((0, 1, 0), 2.5 * w)]},
            "coin": {"rot": [((0, 0, 1), 7 * w)], "loc": (0, 0, 0.018 * (0.5 + 0.5 * w))},
        }
    export_rigged("wallet", rig, anim, seconds=4.0)


MODELS = {"chestnut": m_chestnut, "smartphone": m_smartphone, "cart": m_cart, "wallet": m_wallet}
if __name__ == "__main__":
    keys = sys.argv[1:] or list(MODELS)
    for key in keys:
        if key not in MODELS:
            raise SystemExit(f"unknown model {key!r}; choose from {', '.join(MODELS)}")
        MODELS[key]()
