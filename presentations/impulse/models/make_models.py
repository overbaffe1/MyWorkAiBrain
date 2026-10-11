"""Procedural 3D mascot for the impulse-spending deck (Blender bpy -> GLB).

The glossy brown chestnut, little face, spiky green burr, arms and floating coin are
all modelled here. The animation is skinned (one armature / one loop), so PowerPoint
can play it as a real animated 3D model rather than as a video.
"""
from __future__ import annotations

import importlib.util
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "glb")
os.makedirs(OUT, exist_ok=True)
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SHARED_MODELS = os.path.join(REPO, "presentations", "schumpeter", "models", "make_models.py")
CANTILLON_MODELS = os.path.join(REPO, "presentations", "cantillon", "models")

# Use the shared modelling helpers and the repository's tested skinned-glTF exporter.
spec = importlib.util.spec_from_file_location("_shared_make_models", SHARED_MODELS)
shared = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = shared
spec.loader.exec_module(shared)

# rig.py imports `make_models`; point it at this module so it sees OUT/apply_all below.
sys.modules["make_models"] = sys.modules[__name__]
sys.path.insert(0, CANTILLON_MODELS)
from rig import Rig, export_rigged  # noqa: E402

# Methods expected by the shared Rig exporter when it imports this module as make_models.
apply_all = shared.apply_all
rot_all = shared.rot_all
_mats = shared._mats

def shift_all(dx=0.0, dy=0.0, dz=0.0):
    for obj in bpy.context.scene.objects:
        obj.location.x += dx
        obj.location.y += dy
        obj.location.z += dz
TAU = math.tau


def pbr(name, color, roughness=0.36, metallic=0.0, coat=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat
    return mat


def oval(name, loc, scale, mat, seg=24, rings=14):
    o = shared.sphere(name, 1.0, loc, mat, seg, rings)
    o.scale = scale
    return o


def chestnut_shell():
    """A custom, softly pointed nut mesh, fuller at the bottom like a real chestnut."""
    seg, levels = 40, 24
    verts = [(0.0, 0.0, 0.015)]
    rings = []
    for i in range(1, levels):
        u = i / levels
        z = 0.015 + 0.79 * u
        profile = max(0.0, math.sin(math.pi * u)) ** 0.66
        radius = 0.46 * profile * (0.88 + 0.18 * (1.0 - u))
        cx = 0.018 * math.sin(math.pi * u)
        ring = []
        for j in range(seg):
            a = TAU * j / seg
            ring.append(len(verts))
            verts.append((cx + radius * math.cos(a), radius * 0.72 * math.sin(a), z))
        rings.append(ring)
    top = len(verts)
    verts.append((0.0, 0.0, 0.805))
    faces = []
    first = rings[0]
    for j in range(seg):
        faces.append((0, first[(j + 1) % seg], first[j]))
    for lower, upper in zip(rings, rings[1:]):
        for j in range(seg):
            j1 = (j + 1) % seg
            faces.append((lower[j], lower[j1], upper[j1], upper[j]))
    last = rings[-1]
    for j in range(seg):
        faces.append((last[j], last[(j + 1) % seg], top))
    o = shared.mesh_obj("chestnut_shell", verts, faces)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(o.data)
    bm.free()
    o.data.materials.append(pbr("Chestnut lacquer", (0.25, 0.075, 0.026), 0.24, 0.0, 0.48))
    for poly in o.data.polygons:
        poly.use_smooth = True
    return o


def burr_spike(name, start, direction, length=0.18, radius=0.038):
    d = Vector(direction).normalized()
    bpy.ops.mesh.primitive_cone_add(vertices=9, radius1=radius, radius2=0.002, depth=length,
                                    location=Vector(start) + d * (length * 0.5))
    o = bpy.context.object
    o.name = name
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    o.data.materials.append(pbr("Burr green", (0.12, 0.30, 0.075), 0.56))
    for poly in o.data.polygons:
        poly.use_smooth = True
    return o


def coin():
    # Front of the coin faces the viewer (-Y); all surfaces are meshes before export.
    shared.cyl("floating_coin", 0.145, 0.036, (0.59, -0.16, 0.58), "gold", rot=(math.radians(90), 0, 0), seg=36, bevel=0.004)
    shared.torus("coin_rim", 0.119, 0.008, (0.59, -0.185, 0.58), "brass", rot=(math.radians(90), 0, 0), seg=36, mseg=8)
    shared.sphere("coin_stamp", 0.028, (0.59, -0.191, 0.58), "ivory", seg=16, rings=8)


def m_kashtan():
    rig = Rig()

    # Main nut and face — one bone, with the animation pivot close to the base.
    body = rig.mark()
    chestnut_shell()
    oval("soft underside", (0.015, -0.244, 0.15), (0.245, 0.075, 0.115),
         pbr("Chestnut hilum", (0.66, 0.42, 0.23), 0.55), 28, 14)

    # A green, prickly cupule peeks above and around the nut, as in the original photo.
    oval("green burr cup", (0.0, 0.055, 0.68), (0.39, 0.27, 0.17),
         pbr("Burr cup", (0.16, 0.34, 0.075), 0.56), 28, 16)
    for k in range(11):
        a = TAU * k / 11
        start = (0.30 * math.cos(a), 0.17 * math.sin(a) + 0.02, 0.68 + 0.035 * math.cos(a * 2))
        direction = (0.72 * math.cos(a), 0.72 * math.sin(a), 0.58 + 0.16 * math.sin(a * 3))
        burr_spike(f"burr spine {k + 1}", start, direction, 0.155 if k % 3 else 0.19, 0.032)

    # Friendly meme-face: big eyes, espresso pupils, tiny highlights, raised brows and a grin.
    eye_white = pbr("Warm eye white", (0.98, 0.91, 0.76), 0.22, 0.0, 0.15)
    pupil = pbr("Espresso pupils", (0.028, 0.014, 0.010), 0.16, 0.0, 0.3)
    glint = pbr("Eye sparkle", (1.0, 0.97, 0.84), 0.12)
    cheek = pbr("Cheek tint", (0.70, 0.16, 0.10), 0.50)
    smile = pbr("Smile", (0.12, 0.026, 0.012), 0.48)
    for side in (-1, 1):
        x = side * 0.135
        oval("eye", (x, -0.286, 0.47), (0.067, 0.052, 0.088), eye_white, 22, 12)
        oval("pupil", (x + 0.012, -0.333, 0.462), (0.027, 0.021, 0.041), pupil, 18, 10)
        oval("eye glint", (x + 0.004, -0.352, 0.483), (0.010, 0.008, 0.014), glint, 12, 6)
        oval("cheek", (side * 0.254, -0.258, 0.365), (0.052, 0.023, 0.028), cheek, 16, 8)
        shared.tube("eyebrow", [(x - 0.052, -0.302, 0.572), (x, -0.322, 0.588), (x + 0.052, -0.302, 0.572)],
                    0.014, "walnut", res=3, smooth_curve=True)
    grin_points = [(-0.104, -0.300, 0.346), (-0.058, -0.327, 0.322), (0.0, -0.334, 0.315),
                   (0.058, -0.327, 0.322), (0.104, -0.300, 0.346)]
    shared.tube("smile", grin_points, 0.012, smile, res=3, smooth_curve=True)
    rig.take(body, "body", head=(0.0, 0.0, 0.04))

    # Two expressive arms on separate bones. One waves; the other gestures to the coin.
    left = rig.mark()
    shared.tube("left arm", [(-0.335, -0.03, 0.43), (-0.47, -0.10, 0.40), (-0.54, -0.16, 0.49)],
                0.036, "walnut", res=4, smooth_curve=True)
    oval("left mitten", (-0.548, -0.17, 0.505), (0.072, 0.060, 0.078),
         pbr("Mittens", (0.79, 0.56, 0.32), 0.42), 18, 10)
    rig.take(left, "arm_left", head=(-0.335, -0.03, 0.43))

    right = rig.mark()
    shared.tube("right arm", [(0.335, -0.03, 0.43), (0.46, -0.10, 0.49), (0.52, -0.15, 0.60)],
                0.036, "walnut", res=4, smooth_curve=True)
    oval("right mitten", (0.532, -0.165, 0.612), (0.074, 0.060, 0.079),
         pbr("Mittens", (0.79, 0.56, 0.32), 0.42), 18, 10)
    rig.take(right, "arm_right", head=(0.335, -0.03, 0.43))

    # Little grounded legs and shoes (root bone, so the mascot keeps its footing while bobbing).
    shoe = pbr("Shoes", (0.11, 0.045, 0.025), 0.33, 0.0, 0.12)
    for side in (-1, 1):
        x = side * 0.145
        shared.tube("leg", [(x, -0.035, 0.08), (x, -0.085, -0.095)], 0.028, "walnut", res=3, smooth_curve=False)
        oval("shoe", (x + side * 0.035, -0.12, -0.115), (0.12, 0.13, 0.055), shoe, 18, 10)

    # A tiny coin: the joke is that Kashtan is auditing the receipt, not endorsing spending.
    money = rig.mark()
    coin()
    rig.take(money, "coin", head=(0.59, -0.16, 0.58))

    rig.shift(dz=-0.12)

    def anim(t):
        bob = 0.022 * (0.5 - 0.5 * math.cos(TAU * t))
        return {
            "body": {
                "loc": (0.0, 0.0, bob),
                "rot": [((0, 1, 0), 3.0 * math.sin(TAU * t)), ((1, 0, 0), 1.6 * math.sin(TAU * t + 0.6))],
            },
            "arm_left": {"rot": [((0, 1, 0), -24.0 + 18.0 * math.sin(TAU * t + 0.2))]},
            "arm_right": {"rot": [((0, 1, 0), 28.0 + 13.0 * math.sin(TAU * t - 0.2))]},
            "coin": {
                "loc": (0.0, 0.0, 0.032 * (0.5 + 0.5 * math.sin(TAU * t))),
                "rot": [((0, 1, 0), 16.0 * math.sin(TAU * t))],
            },
        }

    return rig, anim, 4.8


MODELS = {"kashtan": m_kashtan}

if __name__ == "__main__":
    want = [arg for arg in sys.argv[1:] if arg in MODELS] or list(MODELS)
    for key in want:
        shared.reset()
        _mats.clear()
        result = MODELS[key]()
        export_rigged(key, *result)
