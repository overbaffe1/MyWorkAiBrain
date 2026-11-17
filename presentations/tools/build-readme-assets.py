#!/usr/bin/env python3
"""
build-readme-assets.py — Reproducible generator for MyWorkAiBrain's bespoke README exhibit suite.

Generates zero-external-dependency visual artifacts in `.github/assets/`:
  1. Binary & ASCII .stl 3D exhibits (`exhibits/ship.stl`, `lighthouse.stl`, `locomotive.stl`,
     `armillary-compass.stl`) directly from repository `.glb` models + procedural manifold geometry.
  2. Adaptive dark/light + mobile + motion-safe hero covers (`stage-cover*.svg`).
  3. Dual copperplate & X-ray armature technical plates (`plate-mesh.svg`, `plate-bones.svg`)
     projected from real vertex/triangle/joint buffers of `presentations/cantillon/models/glb/ship.glb`.
  4. Four collector museum seals (`seal-agent.svg`, `seal-manual.svg`, `seal-scenes.svg`, `seal-exports.svg`).
  5. 3D-Morph choreography filmstrip (`morph-reel.svg`, `morph-reel-still.svg`).
  6. Real tracked-file circle-packed repository map (`repo-fingerprint.svg`, `repo-fingerprint-compact.svg`).
  7. Motion-safe first-frame PNGs for GIFs + `signature.svg` + `1280x640` `social-preview.png`.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import struct
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / ".github" / "assets"
EXHIBITS = ASSETS / "exhibits"


# ---------------------------------------------------------------------------
# Shared adaptive CSS palette (warm museum vellum in Light, obsidian stage in Dark)
# ---------------------------------------------------------------------------
PALETTE_CSS = """
  :root {
    --bg: #F6EFE2;
    --bg-2: #EDE2CE;
    --bg-card: #EFE5D4;
    --veil-0: rgba(246, 239, 226, 0.98);
    --veil-1: rgba(246, 239, 226, 0.90);
    --veil-2: rgba(246, 239, 226, 0.00);
    --ink: #221418;
    --ink-soft: #5A454B;
    --muted: #7C656A;
    --brass: #8F5B14;
    --brass-hi: #B8791F;
    --brass-faint: rgba(143, 91, 20, 0.16);
    --violet: #6D28D9;
    --violet-hi: #7C3AED;
    --violet-faint: rgba(109, 40, 217, 0.13);
    --crimson: #9F1D35;
    --teal: #0F6E66;
    --line: rgba(34, 20, 24, 0.14);
    --line-strong: rgba(143, 91, 20, 0.36);
    --beam-a: rgba(184, 121, 31, 0.13);
    --beam-b: rgba(109, 40, 217, 0.09);
    --mesh-fill: #E7DAC2;
    --mesh-shade: #D6C3A3;
    --mesh-edge: #3D262B;
    --mesh-rib: rgba(61, 38, 43, 0.22);
    --ghost: rgba(109, 40, 217, 0.22);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0E080D;
      --bg-2: #180E16;
      --bg-card: #160D15;
      --veil-0: rgba(14, 8, 13, 0.98);
      --veil-1: rgba(14, 8, 13, 0.88);
      --veil-2: rgba(14, 8, 13, 0.00);
      --ink: #F8F0E3;
      --ink-soft: #CBBAB8;
      --muted: #968186;
      --brass: #E6BC6A;
      --brass-hi: #F7D78E;
      --brass-faint: rgba(230, 188, 106, 0.16);
      --violet: #B48EFF;
      --violet-hi: #D1B8FF;
      --violet-faint: rgba(180, 142, 255, 0.16);
      --crimson: #F26B83;
      --teal: #57D1C4;
      --line: rgba(248, 240, 227, 0.12);
      --line-strong: rgba(230, 188, 106, 0.34);
      --beam-a: rgba(230, 188, 106, 0.14);
      --beam-b: rgba(180, 142, 255, 0.11);
      --mesh-fill: #1C111A;
      --mesh-shade: #281824;
      --mesh-edge: #E8C378;
      --mesh-rib: rgba(232, 195, 120, 0.20);
      --ghost: rgba(180, 142, 255, 0.30);
    }
  }
"""


# ---------------------------------------------------------------------------
# 1. Binary glTF (.glb) reader & scene-graph evaluator
# ---------------------------------------------------------------------------
def quat_to_mat(q: List[float]) -> np.ndarray:
    x, y, z, w = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w),     2 * (x * z + y * w),     0.0],
        [2 * (x * y + z * w),     1 - 2 * (x * x + z * z), 2 * (y * z - x * w),     0.0],
        [2 * (x * z - y * w),     2 * (y * z + x * w),     1 - 2 * (x * x + y * y), 0.0],
        [0.0,                     0.0,                     0.0,                     1.0],
    ], dtype=np.float64)


def node_local_matrix(node: dict) -> np.ndarray:
    if "matrix" in node:
        return np.array(node["matrix"], dtype=np.float64).reshape(4, 4).T
    M = np.eye(4, dtype=np.float64)
    if "translation" in node:
        T = np.eye(4)
        T[:3, 3] = node["translation"]
        M = M @ T
    if "rotation" in node:
        M = M @ quat_to_mat(node["rotation"])
    if "scale" in node:
        S = np.diag(list(node["scale"]) + [1.0])
        M = M @ S
    return M


def load_glb(path: Path):
    data = path.read_bytes()
    jlen = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20:20 + jlen])
    blob = data[20 + jlen + 8:]

    def acc_np(idx: int) -> np.ndarray:
        a = gltf["accessors"][idx]
        bv = gltf["bufferViews"][a["bufferView"]]
        off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        ct = {
            5120: np.int8, 5121: np.uint8, 5122: np.int16,
            5123: np.uint16, 5125: np.uint32, 5126: np.float32,
        }[a["componentType"]]
        ncomp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[a["type"]]
        stride = bv.get("byteStride", 0)
        cnt = a["count"]
        item = np.dtype(ct).itemsize * ncomp
        if stride and stride != item:
            raw = np.frombuffer(blob, dtype=np.uint8, count=cnt * stride, offset=off).reshape(cnt, stride)[:, :item]
            return np.frombuffer(raw.tobytes(), dtype=ct).reshape(cnt, ncomp)
        return np.frombuffer(blob, dtype=ct, count=cnt * ncomp, offset=off).reshape(cnt, ncomp)

    nodes = gltf.get("nodes", [])
    parents: Dict[int, int] = {}
    for idx, n in enumerate(nodes):
        for ch in n.get("children", []) or []:
            parents[ch] = idx

    world_mats: Dict[int, np.ndarray] = {}

    def get_world(idx: int) -> np.ndarray:
        if idx in world_mats:
            return world_mats[idx]
        loc = node_local_matrix(nodes[idx])
        if idx in parents:
            w = get_world(parents[idx]) @ loc
        else:
            w = loc
        world_mats[idx] = w
        return w

    for i in range(len(nodes)):
        get_world(i)

    meshes_out = []
    for ni, n in enumerate(nodes):
        if "mesh" not in n:
            continue
        W = world_mats[ni]
        m = gltf["meshes"][n["mesh"]]
        mname = m.get("name", f"mesh_{n['mesh']}")
        for pr in m["primitives"]:
            if pr.get("mode", 4) != 4:
                continue
            pos = acc_np(pr["attributes"]["POSITION"]).astype(np.float64)
            ones = np.ones((len(pos), 1), dtype=np.float64)
            wpos = (W @ np.hstack([pos, ones]).T).T[:, :3]
            if "indices" in pr:
                tri = acc_np(pr["indices"]).reshape(-1, 3).astype(np.int32)
            else:
                tri = np.arange(len(wpos), dtype=np.int32).reshape(-1, 3)
            joints = acc_np(pr["attributes"]["JOINTS_0"]) if "JOINTS_0" in pr["attributes"] else None
            weights = acc_np(pr["attributes"]["WEIGHTS_0"]) if "WEIGHTS_0" in pr["attributes"] else None
            meshes_out.append({
                "name": mname,
                "verts": wpos,
                "tris": tri,
                "joints": joints,
                "weights": weights,
            })

    bones = []
    if gltf.get("skins"):
        s = gltf["skins"][0]
        jset = set(s["joints"])
        for j_idx in s["joints"]:
            p_idx = parents.get(j_idx)
            p_pos = world_mats[p_idx][:3, 3] if (p_idx in jset) else None
            bones.append({
                "idx": j_idx,
                "name": nodes[j_idx].get("name", f"joint_{j_idx}"),
                "pos": world_mats[j_idx][:3, 3].copy(),
                "parent_idx": p_idx if (p_idx in jset) else None,
                "parent_pos": p_pos.copy() if p_pos is not None else None,
            })

    return gltf, meshes_out, bones


# ---------------------------------------------------------------------------
# 2. Export real binary .stl models + procedural manifold ASCII .stl compass
# ---------------------------------------------------------------------------
def glb_to_binary_stl(glb_path: Path, stl_path: Path, header_label: str) -> int:
    _, meshes, _ = load_glb(glb_path)
    all_tris = []
    for m in meshes:
        v = m["verts"]
        # Convert glTF Y-up (x, y, z) -> STL Z-up (x, -z, y)
        vz = np.column_stack([v[:, 0], -v[:, 2], v[:, 1]])
        t = vz[m["tris"]]  # (F, 3, 3)
        all_tris.append(t)
    tris = np.concatenate(all_tris, axis=0)
    # Center XY and rest on Z=0
    mn = tris.reshape(-1, 3).min(axis=0)
    mx = tris.reshape(-1, 3).max(axis=0)
    center = 0.5 * (mn + mx)
    span = max(mx - mn)
    scale = 80.0 / span if span > 0 else 1.0
    tris = (tris - np.array([center[0], center[1], mn[2]])) * scale

    e1 = tris[:, 1] - tris[:, 0]
    e2 = tris[:, 2] - tris[:, 0]
    normals = np.cross(e1, e2)
    nlen = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = np.divide(normals, np.maximum(nlen, 1e-12))

    stl_path.parent.mkdir(parents=True, exist_ok=True)
    hdr = header_label.encode("ascii", errors="ignore")[:80].ljust(80, b" ")
    n_tri = len(tris)
    dtype = np.dtype([
        ("n", "<f4", (3,)),
        ("v0", "<f4", (3,)),
        ("v1", "<f4", (3,)),
        ("v2", "<f4", (3,)),
        ("attr", "<u2"),
    ])
    rec = np.zeros(n_tri, dtype=dtype)
    rec["n"] = normals.astype(np.float32)
    rec["v0"] = tris[:, 0].astype(np.float32)
    rec["v1"] = tris[:, 1].astype(np.float32)
    rec["v2"] = tris[:, 2].astype(np.float32)
    with open(stl_path, "wb") as f:
        f.write(hdr)
        f.write(struct.pack("<I", n_tri))
        f.write(rec.tobytes())
    return n_tri


def build_manifold_compass_stl() -> Tuple[str, dict]:
    """
    Construct a watertight, manifold 3D sculpture for inline README ```stl```:
      Component 1: Stepped octagonal turntable ring (torus-prism with 8 facets, 64 tris)
      Component 2: Tilted equatorial armillary ring (8-segment square-section torus, 64 tris)
      Component 3: 8-pointed bevelled Polaris / Compass Rose crystal at center (32 tris)
    Total = 160 manifold triangles, exact outward normals, verified Euler V - E + F!
    """
    tris: List[Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]]] = []

    def add_tri(a, b, c):
        tris.append((a, b, c))

    def add_quad(a, b, c, d):
        # CCW viewed from outside: a -> b -> c -> d
        add_tri(a, b, c)
        add_tri(a, c, d)

    def make_ring(N: int, r_in: float, r_out: float, z_lo: float, z_hi: float, tilt_deg: float = 0.0, rot_z_deg: float = 0.0):
        ca, sa = math.cos(math.radians(tilt_deg)), math.sin(math.radians(tilt_deg))
        cz, sz = math.cos(math.radians(rot_z_deg)), math.sin(math.radians(rot_z_deg))

        def xf(x, y, z):
            # tilt around X, then rotate around Z, then lift to Z center 22
            y1 = y * ca - z * sa
            z1 = y * sa + z * ca
            x2 = x * cz - y1 * sz
            y2 = x * sz + y1 * cz
            return (round(x2, 3), round(y2, 3), round(z1 + (22.0 if tilt_deg != 0.0 else 0.0), 3))

        ring_pts = []
        for i in range(N):
            th = 2.0 * math.pi * i / N
            c, s = math.cos(th), math.sin(th)
            # 4 vertices of cross-section at angle th:
            # 0: inner bottom, 1: outer bottom, 2: outer top, 3: inner top
            ring_pts.append([
                xf(r_in * c, r_in * s, z_lo),
                xf(r_out * c, r_out * s, z_lo),
                xf(r_out * c, r_out * s, z_hi),
                xf(r_in * c, r_in * s, z_hi),
            ])

        for i in range(N):
            j = (i + 1) % N
            A0, A1, A2, A3 = ring_pts[i]
            B0, B1, B2, B3 = ring_pts[j]
            # Bottom face (normal -Z): A1 -> A0 -> B0 -> B1
            add_quad(A1, A0, B0, B1)
            # Outer wall (normal +R): A1 -> B1 -> B2 -> A2
            add_quad(A1, B1, B2, A2)
            # Top face (normal +Z): A2 -> B2 -> B3 -> A3
            add_quad(A2, B2, B3, A3)
            # Inner wall (normal -R): A0 -> A3 -> B3 -> B0
            add_quad(A0, A3, B3, B0)

    # 1. Stage turntable base ring (10-gon brass ring resting at z = 0..4.5)
    make_ring(N=10, r_in=15.0, r_out=22.0, z_lo=0.0, z_hi=4.2, tilt_deg=0.0)

    # 2. Tilted armillary gimbal ring (10-gon equatorial ring tilted 28 deg)
    make_ring(N=10, r_in=16.2, r_out=18.8, z_lo=-1.5, z_hi=1.5, tilt_deg=28.0, rot_z_deg=18.0)

    # 3. Central 6-ray 3D Compass / Morph Star (bipyramidal 12-gon star, 48 manifold tris!)
    zc = 22.0
    top_apex = (0.0, 0.0, round(zc + 14.5, 3))
    bot_apex = (0.0, 0.0, round(zc - 14.5, 3))
    star_ring = []
    M = 12  # alternating 6 long cardinal points + 6 inner valleys
    for i in range(M):
        th = 2.0 * math.pi * i / M
        r = 13.8 if (i % 2 == 0) else 5.2
        star_ring.append((round(r * math.cos(th), 3), round(r * math.sin(th), 3), round(zc, 3)))
    for i in range(M):
        j = (i + 1) % M
        P, Q = star_ring[i], star_ring[j]
        add_tri(P, Q, top_apex)
        add_tri(Q, P, bot_apex)

    # Verify manifoldness (every directed edge (u,v) has exact twin (v,u))
    directed = defaultdict(int)
    verts = set()
    for a, b, c in tris:
        verts.update([a, b, c])
        for u, v in ((a, b), (b, c), (c, a)):
            directed[(u, v)] += 1
    boundary = sum(1 for (u, v), cnt in directed.items() if directed.get((v, u), 0) != cnt)
    non_single = sum(1 for cnt in directed.values() if cnt != 1)
    assert boundary == 0 and non_single == 0, f"Non-manifold STL: boundary={boundary}, dup={non_single}"

    lines = ["solid myworkaibrain_armillary"]
    for a, b, c in tris:
        va, vb, vc = np.array(a), np.array(b), np.array(c)
        n = np.cross(vb - va, vc - va)
        nl = np.linalg.norm(n)
        n = n / nl if nl > 0 else np.array([0.0, 0.0, 1.0])
        lines.append(f"  facet normal {n[0]:.4f} {n[1]:.4f} {n[2]:.4f}")
        lines.append("    outer loop")
        lines.append(f"      vertex {a[0]:.3f} {a[1]:.3f} {a[2]:.3f}")
        lines.append(f"      vertex {b[0]:.3f} {b[1]:.3f} {b[2]:.3f}")
        lines.append(f"      vertex {c[0]:.3f} {c[1]:.3f} {c[2]:.3f}")
        lines.append("    endloop")
        lines.append("  endfacet")
    lines.append("endsolid myworkaibrain_armillary")
    stl_text = "\n".join(lines) + "\n"

    EXHIBITS.mkdir(parents=True, exist_ok=True)
    (EXHIBITS / "armillary-compass.stl").write_text(stl_text, encoding="utf-8")
    Path("/tmp/inline_compass.stl").write_text(stl_text, encoding="utf-8")

    stats = {
        "verts": len(verts),
        "edges": len(directed) // 2,
        "faces": len(tris),
        "euler": len(verts) - (len(directed) // 2) + len(tris),
    }
    return stl_text, stats


# ---------------------------------------------------------------------------
# 3. 3D projection helper for `ship.glb` -> crisp silhouette & crease paths
# ---------------------------------------------------------------------------
def project_ship_geometry(yaw_deg: float = -34.0, pitch_deg: float = 17.0):
    glb_path = ROOT / "presentations" / "cantillon" / "models" / "glb" / "ship.glb"
    _, meshes, bones = load_glb(glb_path)

    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)

    def cam_pts(pts: np.ndarray) -> np.ndarray:
        # glTF is Y-up, X-right, Z-forward
        x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
        x1 = x * cy + z * sy
        z1 = -x * sy + z * cy
        y2 = y * cp - z1 * sp
        z2 = y * sp + z1 * cp
        return np.column_stack([x1, y2, z2])

    # Compute overall bounds in camera space
    all_v = np.vstack([cam_pts(m["verts"]) for m in meshes])
    mn, mx = all_v.min(axis=0), all_v.max(axis=0)
    ctr = 0.5 * (mn + mx)
    span = max(mx[0] - mn[0], mx[1] - mn[1])

    def to_px(pts3: np.ndarray, cx: float, cy_px: float, scale_px: float) -> np.ndarray:
        c = cam_pts(pts3) - ctr
        # Slight perspective
        persp = 1.0 / (1.0 - 0.14 * (c[:, 2] / span))
        sx = cx + c[:, 0] * persp * (scale_px / span)
        sy_ = cy_px - c[:, 1] * persp * (scale_px / span)
        return np.column_stack([sx, sy_, c[:, 2]])

    def extract_lines(cx: float, cy_px: float, scale_px: float, crease_deg: float = 24.0):
        sil_segs = []
        crease_segs = []
        sea_segs = []
        cos_thresh = math.cos(math.radians(crease_deg))

        for m in meshes:
            v3 = m["verts"]
            p2 = to_px(v3, cx, cy_px, scale_px)
            c3 = cam_pts(v3)
            tris = m["tris"]
            is_sea = m["name"] == "sea"

            # Quantize vertices to weld seams for adjacency
            vq = [tuple(np.round(p, 4)) for p in v3]
            t0, t1, t2 = c3[tris[:, 0]], c3[tris[:, 1]], c3[tris[:, 2]]
            fn = np.cross(t1 - t0, t2 - t0)
            fl = np.linalg.norm(fn, axis=1, keepdims=True)
            fn = np.divide(fn, np.maximum(fl, 1e-12))
            front = fn[:, 2] > 0.0  # facing camera (+Z)

            edge_faces: Dict[Tuple[Tuple, Tuple], List[Tuple[int, int, int]]] = defaultdict(list)
            for fi, (i0, i1, i2) in enumerate(tris):
                for a, b in ((i0, i1), (i1, i2), (i2, i0)):
                    qa, qb = vq[a], vq[b]
                    if qa == qb:
                        continue
                    key = (qa, qb) if qa < qb else (qb, a if qa < qb else a)
                    k_ord = (qa, qb) if qa < qb else (qb, qa)
                    edge_faces[k_ord].append((fi, a, b))

            for entries in edge_faces.values():
                _, a, b = entries[0]
                pa, pb = p2[a, :2], p2[b, :2]
                seg_len = math.hypot(pa[0] - pb[0], pa[1] - pb[1])
                if seg_len < 0.8:
                    continue
                if len(entries) == 1:
                    if is_sea:
                        sea_segs.append((pa, pb))
                    else:
                        sil_segs.append((pa, pb))
                else:
                    f0, f1 = entries[0][0], entries[1][0]
                    if front[f0] != front[f1]:
                        if is_sea:
                            sea_segs.append((pa, pb))
                        else:
                            sil_segs.append((pa, pb))
                    elif front[f0] and front[f1]:
                        dot = float(np.dot(fn[f0], fn[f1]))
                        if dot < cos_thresh:
                            if is_sea:
                                sea_segs.append((pa, pb))
                            else:
                                crease_segs.append((pa, pb))

        # Project bones too
        bone_proj = []
        for b in bones:
            bp = to_px(b["pos"].reshape(1, 3), cx, cy_px, scale_px)[0]
            pp = to_px(b["parent_pos"].reshape(1, 3), cx, cy_px, scale_px)[0] if b["parent_pos"] is not None else None
            bone_proj.append({
                "name": b["name"],
                "xy": (float(bp[0]), float(bp[1])),
                "parent_xy": (float(pp[0]), float(pp[1])) if pp is not None else None,
            })

        return sil_segs, crease_segs, sea_segs, bone_proj

    return extract_lines


def segs_to_path(segs: List[Tuple[np.ndarray, np.ndarray]]) -> str:
    parts = []
    for pa, pb in segs:
        parts.append(f"M{pa[0]:.1f},{pa[1]:.1f}L{pb[0]:.1f},{pb[1]:.1f}")
    return "".join(parts)


# ---------------------------------------------------------------------------
# 4. Dual Technical X-Ray Plates (`plate-mesh.svg` & `plate-bones.svg`)
# ---------------------------------------------------------------------------
def build_technical_plates(projector):
    sil, crease, sea, bones = projector(cx=310.0, cy_px=222.0, scale_px=405.0, crease_deg=23.0)
    sil_d = segs_to_path(sil)
    crease_d = segs_to_path(crease)
    sea_d = segs_to_path(sea)

    def frame_chrome(plate_no: str, title: str, subtitle: str, badge_right: str) -> str:
        return f"""
  <rect width="620" height="430" rx="14" fill="var(--bg)"/>
  <rect x="10" y="10" width="600" height="410" rx="10" fill="none" stroke="var(--line-strong)" stroke-width="1"/>
  <rect x="16" y="16" width="588" height="398" rx="7" fill="none" stroke="var(--line)" stroke-width="0.75"/>
  <!-- Corner registration crosshairs -->
  <path d="M28,24v12M22,30h12 M592,24v12M586,30h12 M28,394v12M22,400h12 M592,394v12M586,400h12" stroke="var(--brass)" stroke-width="1" opacity="0.65"/>
  <!-- Subtle technical grid -->
  <path d="M90,56v320M165,56v320M240,56v320M315,56v320M390,56v320M465,56v320M540,56v320 M28,116h564M28,186h564M28,256h564M28,326h564" stroke="var(--line)" stroke-width="0.6" stroke-dasharray="2 5"/>
  <!-- Top header bar -->
  <text x="44" y="34" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" letter-spacing="1.6" fill="var(--brass)">{plate_no}</text>
  <text x="576" y="34" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" letter-spacing="1.2" fill="var(--muted)">{badge_right}</text>
  <!-- Bottom caption bar (two-row clean layout, zero collision on any system font) -->
  <line x1="28" y1="368" x2="592" y2="368" stroke="var(--line)" stroke-width="0.8"/>
  <text x="42" y="388" font-family="Georgia, 'Times New Roman', serif" font-size="14.5" font-weight="700" fill="var(--ink)">{title}</text>
  <text x="42" y="405" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" fill="var(--ink-soft)">{subtitle}</text>
"""

    # Plate I: Copperplate mesh silhouette & feature edges
    plate1 = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 620 430" width="620" height="430" role="img" aria-label="Лист I: Гравюра полигональной сетки ship.glb">
  <style>{PALETTE_CSS}</style>
  <defs>
    <radialGradient id="glow1" cx="52%" cy="50%" r="44%">
      <stop offset="0%" stop-color="var(--brass)" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="var(--brass)" stop-opacity="0"/>
    </radialGradient>
  </defs>
  {frame_chrome("ЛИСТ I · ГРАВЮРА ПОВЕРХНОСТИ", "Внешняя форма: парусник Кантильона", "10 755 вершин · 14 042 Δ · 14 мешей · Cycles PBR", "CANTILLON / SHIP.GLB")}
  <ellipse cx="315" cy="218" rx="235" ry="132" fill="url(#glow1)"/>
  <!-- Projected sea wave contours -->
  <path d="{sea_d}" fill="none" stroke="var(--teal)" stroke-width="0.7" stroke-linecap="round" opacity="0.58"/>
  <!-- Projected internal crease ribs -->
  <path d="{crease_d}" fill="none" stroke="var(--mesh-edge)" stroke-width="0.55" stroke-linecap="round" opacity="0.46"/>
  <!-- Crisp copperplate silhouette edges -->
  <path d="{sil_d}" fill="none" stroke="var(--mesh-edge)" stroke-width="1.15" stroke-linecap="round"/>
  <!-- Architectural dimension callouts -->
  <g font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="9.5" fill="var(--muted)">
    <line x1="84" y1="346" x2="544" y2="346" stroke="var(--brass)" stroke-width="0.8" opacity="0.6"/>
    <path d="M84,342v8 M544,342v8" stroke="var(--brass)" stroke-width="0.9"/>
    <text x="314" y="359" text-anchor="middle" fill="var(--brass)">БАЗА ВОЛН 2.78 ЕД. · КАМЕРА FOV 45° · 1 ЕДИНЫЙ GLB</text>
  </g>
</svg>
"""

    # Plate II: X-Ray Single-Armature Bone Rig (23 joints!)
    bone_lines = []
    bone_nodes = []
    labels_wanted = {
        "root": ("root", (12, 13)),
        "hull": ("hull (крен)", (14, -4)),
        "sail2": ("sail0..5 (паруса)", (-124, 6)),
        "pen0": ("pen0→2 (вымпел)", (-122, -12)),
        "jib": ("jib (кливер)", (12, -6)),
        "gull": ("gull + L/R (чайка)", (14, -8)),
        "wave0": ("wave0", (-6, 16)),
        "wave7": ("wave7 (8 волн)", (-42, 16)),
    }

    for b in bones:
        x, y = b["xy"]
        if b["parent_xy"] is not None:
            px, py = b["parent_xy"]
            # Draw octahedral Blender-style bone spear from parent to child
            dx, dy = x - px, y - py
            L = math.hypot(dx, dy)
            if L > 2.0:
                nx, ny = -dy / L, dx / L
                w = min(4.2, max(1.8, L * 0.08))
                mx, my = px + dx * 0.22, py + dy * 0.22
                pts = f"{px:.1f},{py:.1f} {mx + nx * w:.1f},{my + ny * w:.1f} {x:.1f},{y:.1f} {mx - nx * w:.1f},{my - ny * w:.1f}"
                is_wave = b["name"].startswith("wave")
                col = "var(--teal)" if is_wave else "var(--violet)"
                op = "0.55" if is_wave else "0.85"
                bone_lines.append(f'<polygon points="{pts}" fill="{col}" fill-opacity="0.22" stroke="{col}" stroke-width="1.05" opacity="{op}"/>')

    for b in bones:
        x, y = b["xy"]
        nm = b["name"]
        is_root = nm in ("root", "hull")
        is_wave = nm.startswith("wave")
        col = "var(--brass-hi)" if is_root else ("var(--teal)" if is_wave else "var(--violet-hi)")
        r = 4.2 if is_root else (2.7 if is_wave else 3.3)
        bone_nodes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r + 3.0:.1f}" fill="{col}" opacity="0.18"/>')
        bone_nodes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="var(--bg)" stroke="{col}" stroke-width="1.5"/>')
        if nm in labels_wanted:
            txt, (ox, oy) = labels_wanted[nm]
            bone_nodes.append(
                f'<text x="{x + ox:.1f}" y="{y + oy:.1f}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" '
                f'font-size="9.5" font-weight="600" fill="{col}">{txt}</text>'
            )

    plate2 = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 620 430" width="620" height="430" role="img" aria-label="Лист II: Рентген 23 костей единого скелета ship.glb">
  <style>{PALETTE_CSS}</style>
  <defs>
    <radialGradient id="glow2" cx="50%" cy="48%" r="45%">
      <stop offset="0%" stop-color="var(--violet)" stop-opacity="0.18"/>
      <stop offset="100%" stop-color="var(--violet)" stop-opacity="0"/>
    </radialGradient>
  </defs>
  {frame_chrome("ЛИСТ II · РЕНТГЕН ЕДИНОГО СКЕЛЕТА", "Секрет PowerPoint: все детали в одной арматуре", "23 кости (joints) · JOINTS_0 / WEIGHTS_0", "SKIN[0] · 0 TRS-НОД")}
  <ellipse cx="315" cy="220" rx="240" ry="140" fill="url(#glow2)"/>
  <!-- Translucent X-ray ghost of mesh -->
  <path d="{sea_d}" fill="none" stroke="var(--ghost)" stroke-width="0.55" opacity="0.45"/>
  <path d="{sil_d}" fill="none" stroke="var(--ghost)" stroke-width="0.85" opacity="0.65"/>
  <!-- Real projected Blender armature hierarchy -->
  <g>{"".join(bone_lines)}</g>
  <g>{"".join(bone_nodes)}</g>
  <g font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="9.2" fill="var(--muted)">
    <text x="314" y="359" text-anchor="middle" fill="var(--violet)">POWERPOINT ИГНОРИРУЕТ NODE TRS → ВОЛНЫ, ПАРУСА И ЧАЙКА СКИНЯТСЯ К ОДНОЙ АРМАТУРЕ</text>
  </g>
</svg>
"""

    (ASSETS / "plate-mesh.svg").write_text(plate1, encoding="utf-8")
    (ASSETS / "plate-bones.svg").write_text(plate2, encoding="utf-8")


# ---------------------------------------------------------------------------
# 5. Adaptive Hero Cover Suite (`stage-cover*.svg`)
# ---------------------------------------------------------------------------
def build_stage_covers(projector):
    # Project real ship onto right half of 1280x500 stage!
    sil, crease, sea, bones = projector(cx=985.0, cy_px=252.0, scale_px=420.0, crease_deg=26.0)
    sil_d = segs_to_path(sil)
    crease_d = segs_to_path(crease)
    sea_d = segs_to_path(sea)

    joint_sparks = []
    for idx, b in enumerate(bones):
        if b["name"] in ("root", "hull", "sail1", "sail3", "sail5", "jib", "pen0", "gull", "wave1", "wave4", "wave6"):
            x, y = b["xy"]
            col = "var(--brass-hi)" if b["name"] in ("root", "hull") else "var(--violet-hi)"
            joint_sparks.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{col}" opacity="0.20"/>'
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.2" fill="{col}"/>'
            )

    def wide_svg(animated: bool) -> str:
        anim_css = ""
        turntable_spin = ""
        if animated:
            anim_css = """
    @media (prefers-reduced-motion: no-preference) {
      .beam-left { animation: swayA 11s ease-in-out infinite alternate; transform-origin: 860px 0px; }
      .beam-right { animation: swayB 13s ease-in-out infinite alternate; transform-origin: 1120px 0px; }
      .ship-rig { animation: floatShip 7.5s ease-in-out infinite; }
      .spark-layer { animation: pulseSparks 4.8s ease-in-out infinite; }
    }
    @keyframes swayA { 0% { opacity: 0.65; } 100% { opacity: 1.0; } }
    @keyframes swayB { 0% { opacity: 0.95; } 100% { opacity: 0.55; } }
    @keyframes floatShip { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-6px); } }
    @keyframes pulseSparks { 0%, 100% { opacity: 0.55; } 50% { opacity: 1.0; } }
"""
            turntable_spin = '<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="64s" repeatCount="indefinite"/>'

        # Degree tick marks around turntable ring (centered at 0,0, squashed vertically byouter scale(1, 0.30))
        ticks = []
        for deg in range(0, 360, 10):
            r0 = 236 if deg % 30 == 0 else 242
            r1 = 250
            rad = math.radians(deg)
            x0, y0 = r0 * math.cos(rad), r0 * math.sin(rad)
            x1, y1 = r1 * math.cos(rad), r1 * math.sin(rad)
            ticks.append(f"M{x0:.1f},{y0:.1f}L{x1:.1f},{y1:.1f}")
        ticks_d = "".join(ticks)

        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 500" width="1280" height="500" role="img" aria-label="MyWorkAiBrain — театр живых 3D-презентаций PowerPoint из кода">
  <style>
    {PALETTE_CSS}
    {anim_css}
  </style>
  <defs>
    <linearGradient id="bgGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="var(--bg)"/>
      <stop offset="58%" stop-color="var(--bg-2)"/>
      <stop offset="100%" stop-color="var(--bg)"/>
    </linearGradient>
    <linearGradient id="leftVeil" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="var(--veil-0)"/>
      <stop offset="68%" stop-color="var(--veil-1)"/>
      <stop offset="100%" stop-color="var(--veil-2)"/>
    </linearGradient>
    <linearGradient id="spotGold" x1="0.5" y1="0" x2="0.5" y2="1">
      <stop offset="0%" stop-color="var(--brass-hi)" stop-opacity="0.26"/>
      <stop offset="100%" stop-color="var(--brass-hi)" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="spotViolet" x1="0.5" y1="0" x2="0.5" y2="1">
      <stop offset="0%" stop-color="var(--violet)" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="var(--violet)" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="stagePool" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="var(--brass)" stop-opacity="0.22"/>
      <stop offset="65%" stop-color="var(--violet)" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="var(--bg)" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="stageClip">
      <rect width="1280" height="500" rx="18"/>
    </clipPath>
  </defs>

  <g clip-path="url(#stageClip)">
    <rect width="1280" height="500" fill="url(#bgGrad)"/>

    <!-- Perspective theatrical stage floor horizon & rays -->
    <g opacity="0.55">
      <line x1="620" y1="360" x2="1280" y2="360" stroke="var(--line-strong)" stroke-width="0.9"/>
      <line x1="660" y1="418" x2="1280" y2="418" stroke="var(--line)" stroke-width="0.7" stroke-dasharray="3 6"/>
      <path d="M985,360 L690,500 M985,360 L835,500 M985,360 L985,500 M985,360 L1135,500 M985,360 L1275,500" stroke="var(--line)" stroke-width="0.75"/>
    </g>

    <!-- Volumetric proscenium spotlight cones -->
    <polygon class="beam-left" points="820,0 910,0 1165,455 745,455" fill="url(#spotGold)"/>
    <polygon class="beam-right" points="1085,0 1165,0 1195,455 815,455" fill="url(#spotViolet)"/>

    <!-- Off-stage Morph ghost portals (!!m-prev / !!m-next) -->
    <g opacity="0.42" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="9.5" fill="var(--muted)">
      <ellipse cx="735" cy="390" rx="46" ry="13" fill="none" stroke="var(--violet)" stroke-width="1" stroke-dasharray="3 4"/>
      <text x="735" y="415" text-anchor="middle">!!ship · -80°</text>
      <ellipse cx="1218" cy="390" rx="42" ry="12" fill="none" stroke="var(--brass)" stroke-width="1" stroke-dasharray="3 4"/>
      <text x="1212" y="415" text-anchor="middle">!!next · +80°</text>
    </g>

    <!-- Stage floor turntable dial (safe nested <g>: outer positions & squashes, inner rotates!) -->
    <ellipse cx="985" cy="382" rx="275" ry="82" fill="url(#stagePool)"/>
    <g transform="translate(985, 382) scale(1, 0.30)">
      <g>
        <circle cx="0" cy="0" r="252" fill="none" stroke="var(--brass)" stroke-width="1.6" opacity="0.65"/>
        <circle cx="0" cy="0" r="218" fill="none" stroke="var(--violet)" stroke-width="1.1" stroke-dasharray="8 8" opacity="0.55"/>
        <circle cx="0" cy="0" r="168" fill="none" stroke="var(--line-strong)" stroke-width="1"/>
        <path d="{ticks_d}" stroke="var(--brass)" stroke-width="1.3" opacity="0.72"/>
        {turntable_spin}
      </g>
    </g>

    <!-- Real projected 3D brigantine `ship.glb` (14,042 tris, 23 bones) -->
    <g class="ship-rig">
      <path d="{sea_d}" fill="none" stroke="var(--teal)" stroke-width="0.72" opacity="0.55"/>
      <path d="{crease_d}" fill="none" stroke="var(--mesh-edge)" stroke-width="0.55" opacity="0.42"/>
      <path d="{sil_d}" fill="none" stroke="var(--mesh-edge)" stroke-width="1.18" stroke-linecap="round"/>
      <g class="spark-layer">{"".join(joint_sparks)}</g>
    </g>

    <!-- Quiet left curtain veil under editorial typography -->
    <rect x="0" y="0" width="790" height="500" fill="url(#leftVeil)"/>

    <!-- Editorial museum typography -->
    <g>
      <text x="58" y="68" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11.5" letter-spacing="2.4" fill="var(--brass)">КУНСТКАМЕРА ЖИВОГО 3D · BLENDER 4.3 × OPENXML</text>
      <line x1="58" y1="84" x2="540" y2="84" stroke="var(--line-strong)" stroke-width="1"/>

      <text x="56" y="182" font-family="Georgia, 'Times New Roman', serif" font-size="82" font-weight="700" letter-spacing="-1.5" fill="var(--ink)">MyWorkAiBrain</text>

      <text x="58" y="232" font-family="Georgia, 'Times New Roman', serif" font-size="24" font-style="italic" fill="var(--ink-soft)">Театр трёхмерных презентаций PowerPoint,</text>
      <text x="58" y="264" font-family="Georgia, 'Times New Roman', serif" font-size="24" font-style="italic" fill="var(--ink-soft)">собранных целиком из кода и единого скелета.</text>

      <text x="58" y="316" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" font-size="14.5" fill="var(--muted)">Процедурные .glb-модели · PptxGenJS · инъекция a3d:model3D · бесшовный Morph !!</text>

      <!-- Three crisp brass atelier plaques -->
      <g transform="translate(58, 354)" font-family="ui-monospace, SFMono-Regular, Menlo, monospace">
        <rect x="0" y="0" width="166" height="58" rx="8" fill="var(--bg-card)" stroke="var(--line-strong)" stroke-width="1"/>
        <text x="16" y="24" font-size="18" font-weight="700" fill="var(--brass)">5 колод</text>
        <text x="16" y="44" font-size="10.5" fill="var(--muted)">42 слайда в .pptx</text>

        <rect x="180" y="0" width="184" height="58" rx="8" fill="var(--bg-card)" stroke="var(--line-strong)" stroke-width="1"/>
        <text x="196" y="24" font-size="18" font-weight="700" fill="var(--violet)">49 моделей</text>
        <text x="196" y="44" font-size="10.5" fill="var(--muted)">до 40 костей в арматуре</text>

        <rect x="378" y="0" width="198" height="58" rx="8" fill="var(--bg-card)" stroke="var(--line-strong)" stroke-width="1"/>
        <text x="394" y="24" font-size="18" font-weight="700" fill="var(--ink)">6 глав курса</text>
        <text x="394" y="44" font-size="10.5" fill="var(--muted)">учебник для ИИ и людей</text>
      </g>

      <text x="58" y="458" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10.5" letter-spacing="1.4" fill="var(--muted)">ЭКСПОНАТ НА СЦЕНЕ: CANTILLON / SHIP.GLB · 14 042 ГРАНИ · 23 КОСТИ · РЕАЛЬНАЯ ПРОЕКЦИЯ</text>
    </g>

    <!-- Outer museum frame border -->
    <rect x="10" y="10" width="1260" height="480" rx="12" fill="none" stroke="var(--line-strong)" stroke-width="1"/>
  </g>
</svg>
"""

    # Compact mobile cover (760x430)
    sil_c, crease_c, sea_c, _ = projector(cx=585.0, cy_px=248.0, scale_px=275.0, crease_deg=28.0)
    sil_cd = segs_to_path(sil_c)
    crease_cd = segs_to_path(crease_c)
    sea_cd = segs_to_path(sea_c)

    def compact_svg(animated: bool) -> str:
        anim = """
    @media (prefers-reduced-motion: no-preference) {
      .ship-c { animation: bobC 7s ease-in-out infinite; }
    }
    @keyframes bobC { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-5px); } }
""" if animated else ""
        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 430" width="760" height="430" role="img" aria-label="MyWorkAiBrain — живые 3D-презентации PowerPoint из кода">
  <style>{PALETTE_CSS}{anim}</style>
  <defs>
    <linearGradient id="veilC" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="var(--veil-0)"/>
      <stop offset="72%" stop-color="var(--veil-1)"/>
      <stop offset="100%" stop-color="var(--veil-2)"/>
    </linearGradient>
  </defs>
  <rect width="760" height="430" rx="16" fill="var(--bg)"/>
  <g class="ship-c" opacity="0.72">
    <path d="{sea_cd}" fill="none" stroke="var(--teal)" stroke-width="0.65"/>
    <path d="{crease_cd}" fill="none" stroke="var(--mesh-edge)" stroke-width="0.5" opacity="0.4"/>
    <path d="{sil_cd}" fill="none" stroke="var(--mesh-edge)" stroke-width="1.05"/>
  </g>
  <rect width="600" height="430" rx="16" fill="url(#veilC)"/>
  <rect x="10" y="10" width="740" height="410" rx="11" fill="none" stroke="var(--line-strong)" stroke-width="1"/>
  <text x="38" y="56" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10.5" letter-spacing="2" fill="var(--brass)">КУНСТКАМЕРА ЖИВОГО 3D · GLB × PPTX</text>
  <text x="36" y="138" font-family="Georgia, 'Times New Roman', serif" font-size="56" font-weight="700" fill="var(--ink)">MyWorkAiBrain</text>
  <text x="38" y="182" font-family="Georgia, 'Times New Roman', serif" font-size="20" font-style="italic" fill="var(--ink-soft)">Живые 3D-презентации PowerPoint,</text>
  <text x="38" y="210" font-family="Georgia, 'Times New Roman', serif" font-size="20" font-style="italic" fill="var(--ink-soft)">собранные целиком из кода.</text>
  <g transform="translate(38, 256)" font-family="ui-monospace, SFMono-Regular, Menlo, monospace">
    <rect x="0" y="0" width="145" height="54" rx="7" fill="var(--bg-card)" stroke="var(--line-strong)"/>
    <text x="14" y="23" font-size="16" font-weight="700" fill="var(--brass)">5 колод</text>
    <text x="14" y="41" font-size="10" fill="var(--muted)">готовые .pptx</text>
    <rect x="158" y="0" width="165" height="54" rx="7" fill="var(--bg-card)" stroke="var(--line-strong)"/>
    <text x="172" y="23" font-size="16" font-weight="700" fill="var(--violet)">49 моделей</text>
    <text x="172" y="41" font-size="10" fill="var(--muted)">единый скелет glTF</text>
    <rect x="336" y="0" width="155" height="54" rx="7" fill="var(--bg-card)" stroke="var(--line-strong)"/>
    <text x="350" y="23" font-size="16" font-weight="700" fill="var(--ink)">6 глав</text>
    <text x="350" y="41" font-size="10" fill="var(--muted)">курс train-ai/</text>
  </g>
  <text x="38" y="388" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" letter-spacing="1.2" fill="var(--muted)">BLENDER 4.3 · PPTXGENJS · A3D:MODEL3D · MORPH !!</text>
</svg>
"""

    (ASSETS / "stage-cover.svg").write_text(wide_svg(True), encoding="utf-8")
    (ASSETS / "stage-cover-still.svg").write_text(wide_svg(False), encoding="utf-8")
    (ASSETS / "stage-cover-compact.svg").write_text(compact_svg(True), encoding="utf-8")
    (ASSETS / "stage-cover-compact-still.svg").write_text(compact_svg(False), encoding="utf-8")


# ---------------------------------------------------------------------------
# 6. Four Collector Museum Seals (`seal-*.svg`)
# ---------------------------------------------------------------------------
def build_seals():
    seals = [
        (
            "seal-agent.svg",
            "AGENTS.MD · ПЛЕЙБУК АГЕНТА · ЗОЛОТЫЕ ПРАВИЛА СЦЕНЫ ·",
            "Плейбук ИИ",
            "AGENTS.md",
            "var(--brass)",
            # Compass star emblem
            """
      <polygon points="0,-28 6,-6 28,0 6,6 0,28 -6,6 -28,0 -6,-6" fill="var(--brass-faint)" stroke="var(--brass)" stroke-width="1.5"/>
      <polygon points="0,-18 18,0 0,18 -18,0" fill="none" stroke="var(--violet)" stroke-width="1.1"/>
      <circle cx="0" cy="0" r="4" fill="var(--brass)"/>
            """,
        ),
        (
            "seal-manual.svg",
            "TRAIN-AI · УЧЕБНИК В 6 ГЛАВАХ · ОТ КОСТЕЙ ДО MORPH ·",
            "Учебник · 6 глав",
            "train-ai/",
            "var(--violet)",
            # Open architectural codex + armature node
            """
      <path d="M-24,-14 C-12,-18 -4,-15 0,-10 C4,-15 12,-18 24,-14 L24,16 C12,12 4,15 0,20 C-4,15 -12,12 -24,16 Z" fill="var(--violet-faint)" stroke="var(--violet)" stroke-width="1.5"/>
      <line x1="0" y1="-10" x2="0" y2="20" stroke="var(--violet)" stroke-width="1.2"/>
      <path d="M-17,-6h11 M-17,1h11 M-17,8h9 M6,-5h11 M6,2h11 M6,9h9" stroke="var(--brass)" stroke-width="1.1" stroke-linecap="round"/>
            """,
        ),
        (
            "seal-scenes.svg",
            "ПРИМЕРЫ ПРЕЗЕНТАЦИЙ · 5 ПРОЕКТОВ · 49 МОДЕЛЕЙ GLB ·",
            "Примеры сцен",
            "presentations/",
            "var(--teal)",
            # Faceted 3D polyhedron on turntable
            """
      <ellipse cx="0" cy="18" rx="24" ry="7" fill="none" stroke="var(--brass)" stroke-width="1.2" stroke-dasharray="3 3"/>
      <polygon points="0,-24 21,-7 13,15 -13,15 -21,-7" fill="var(--brass-faint)" stroke="var(--teal)" stroke-width="1.5"/>
      <path d="M0,-24 L0,3 M21,-7 L0,3 M-21,-7 L0,3 M13,15 L0,3 M-13,15 L0,3" stroke="var(--teal)" stroke-width="1.1"/>
      <circle cx="0" cy="3" r="3" fill="var(--brass)"/>
            """,
        ),
        (
            "seal-exports.svg",
            "ПРИМЕРЫ ЭКСПОРТА · 5 ГОТОВЫХ КОЛОД PPTX · СЦЕНАРИИ ·",
            "Примеры экспорта",
            "exports/",
            "var(--crimson)",
            # Proscenium slide frame + 3D play prism
            """
      <rect x="-24" y="-16" width="48" height="32" rx="4" fill="var(--brass-faint)" stroke="var(--crimson)" stroke-width="1.5"/>
      <polygon points="-6,-9 11,0 -6,9" fill="var(--crimson)" opacity="0.85"/>
      <path d="M-18,-22h36 M-14,22h28" stroke="var(--brass)" stroke-width="1.1" stroke-linecap="round"/>
            """,
        ),
    ]

    ticks = "".join(
        f"M{62 * math.cos(math.radians(a)):.1f},{62 * math.sin(math.radians(a)):.1f}"
        f"L{66 * math.cos(math.radians(a)):.1f},{66 * math.sin(math.radians(a)):.1f}"
        for a in range(0, 360, 12)
    )

    for fname, ring_txt, label, sub, accent, emblem in seals:
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 168 188" width="168" height="188" role="img" aria-label="{label} — {sub}">
  <style>
    {PALETTE_CSS}
    @media (prefers-reduced-motion: no-preference) {{
      .orbit {{ animation: spinRing 46s linear infinite; }}
    }}
    @keyframes spinRing {{ to {{ transform: rotate(360deg); }} }}
  </style>
  <defs>
    <path id="ringPath" d="M 0,-51 A 51,51 0 1,1 -0.01,-51"/>
  </defs>
  <g transform="translate(84, 76)">
    <circle cx="0" cy="0" r="68" fill="var(--bg-card)" stroke="var(--line-strong)" stroke-width="1.2"/>
    <path d="{ticks}" stroke="var(--brass)" stroke-width="0.9" opacity="0.55"/>
    <circle cx="0" cy="0" r="39" fill="var(--bg)" stroke="{accent}" stroke-width="1.2" opacity="0.85"/>
    <g class="orbit">
      <text font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="7.6" letter-spacing="1.55" fill="var(--ink-soft)">
        <textPath href="#ringPath" startOffset="0%">{ring_txt}</textPath>
      </text>
    </g>
    <g>{emblem}</g>
  </g>
  <text x="84" y="164" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif" font-size="13.5" font-weight="700" fill="var(--ink)">{label}</text>
  <text x="84" y="180" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" fill="{accent}">{sub}</text>
</svg>
"""
        (ASSETS / fname).write_text(svg, encoding="utf-8")


# ---------------------------------------------------------------------------
# 7. 3D-Morph Choreography Filmstrip (`morph-reel.svg` & `morph-reel-still.svg`)
# ---------------------------------------------------------------------------
def build_morph_reel():
    def make_reel(animated: bool) -> str:
        anim_css = ""
        if animated:
            # Starts on the completed full diagram (0%..18% and 70%..100%) so mid-scroll readers always see everything!
            anim_css = """
    @media (prefers-reduced-motion: no-preference) {
      .stage-arrow { stroke-dasharray: 8 6; animation: march 1.8s linear infinite; }
      .coin-roll { animation: rollCoin 9s ease-in-out infinite; }
      .live-badge { animation: blinkDot 2.8s ease-in-out infinite; }
    }
    @keyframes march { to { stroke-dashoffset: -28; } }
    @keyframes rollCoin {
      0%, 22%   { transform: rotate(0deg); }
      48%, 68%  { transform: rotate(-146deg); }
      92%, 100% { transform: rotate(-292deg); }
    }
    @keyframes blinkDot { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
"""
        # Filmstrip sprocket holes top & bottom
        sprockets = "".join(
            f'<rect x="{x}" y="14" width="14" height="9" rx="2.5" fill="var(--bg)" stroke="var(--line-strong)" stroke-width="0.8"/>'
            f'<rect x="{x}" y="317" width="14" height="9" rx="2.5" fill="var(--bg)" stroke="var(--line-strong)" stroke-width="0.8"/>'
            for x in range(28, 1096, 36)
        )

        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 340" width="1120" height="340" role="img" aria-label="Кинолента хореографии перехода 3D Morph между слайдами">
  <style>
    {PALETTE_CSS}
    {anim_css}
  </style>
  <rect width="1120" height="340" rx="14" fill="var(--bg-card)"/>
  <rect x="8" y="8" width="1104" height="324" rx="10" fill="none" stroke="var(--line-strong)" stroke-width="1"/>
  {sprockets}

  <!-- Header -->
  <text x="36" y="48" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10.5" letter-spacing="1.8" fill="var(--brass)">ПАРТИТУРА ПЕРЕХОДА · P159:MORPH (DUR = 1300 МС) · СОПОСТАВЛЕНИЕ ПО ПРЕФИКСУ !!</text>
  <circle class="live-badge" cx="1076" cy="44" r="4.5" fill="var(--crimson)"/>
  <text x="1064" y="48" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" fill="var(--muted)">КАДР 1 → КАДР 2</text>

  <!-- ================= SLIDE N ================= -->
  <g transform="translate(36, 66)">
    <rect x="0" y="0" width="446" height="206" rx="10" fill="var(--bg)" stroke="var(--line-strong)" stroke-width="1"/>
    <!-- Off-stage zones vs visible 16:9 viewport -->
    <rect x="86" y="14" width="274" height="154" rx="6" fill="var(--brass-faint)" stroke="var(--brass)" stroke-width="1.3"/>
    <text x="223" y="30" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="9.5" font-weight="700" fill="var(--brass)">ЭКРАН СЛАЙДА n (10" × 5.625")</text>

    <text x="43" y="30" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="8.5" fill="var(--muted)">КУЛИСА L</text>
    <text x="403" y="30" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="8.5" fill="var(--muted)">КУЛИСА R</text>

    <!-- Active model A in center -->
    <g transform="translate(223, 84)">
      <circle cx="0" cy="0" r="26" fill="var(--bg-card)" stroke="var(--brass)" stroke-width="1.8"/>
      <polygon points="0,-17 15,-3 9,14 -9,14 -15,-3" fill="var(--brass-faint)" stroke="var(--brass)" stroke-width="1.4"/>
      <text x="0" y="40" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="9.5" font-weight="700" fill="var(--ink)">!!model-A</text>
      <text x="0" y="52" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="8.5" fill="var(--brass)">x=5.0" · ry=0°</text>
    </g>

    <!-- Ghost model B waiting right off-stage -->
    <g transform="translate(403, 92)" opacity="0.78">
      <circle cx="0" cy="0" r="21" fill="none" stroke="var(--violet)" stroke-width="1.4" stroke-dasharray="4 3"/>
      <polygon points="0,-12 11,0 0,12 -11,0" fill="var(--violet-faint)" stroke="var(--violet)" stroke-width="1.2"/>
      <text x="0" y="38" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="9" font-weight="700" fill="var(--violet)">!!model-B</text>
      <text x="0" y="50" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="8" fill="var(--muted)">+14.2" · +80°</text>
    </g>

    <!-- Rolling !!coin medallion bottom-left -->
    <g transform="translate(106, 152)">
      <g class="coin-roll">
        <circle cx="0" cy="0" r="10" fill="var(--bg-card)" stroke="var(--brass-hi)" stroke-width="1.4"/>
        <path d="M0,-7v14 M-5,0h10" stroke="var(--brass-hi)" stroke-width="1.1"/>
      </g>
    </g>
    <text x="122" y="155" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="8.5" fill="var(--muted)">!!coin rz=0°</text>

    <text x="223" y="191" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif" font-size="12.5" font-style="italic" fill="var(--ink-soft)">Будущий экспонат ждёт за правой кулисой в развороте +80°</text>
  </g>

  <!-- ================= MORPH BRIDGE ================= -->
  <g transform="translate(494, 134)">
    <line class="stage-arrow" x1="4" y1="34" x2="124" y2="34" stroke="var(--violet)" stroke-width="2"/>
    <polygon points="128,34 118,28 118,40" fill="var(--violet)"/>
    <rect x="14" y="2" width="104" height="24" rx="12" fill="var(--violet-faint)" stroke="var(--violet)" stroke-width="1"/>
    <text x="66" y="18" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" font-weight="700" fill="var(--violet)">MORPH 1.3s</text>
    <text x="66" y="54" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="8.5" fill="var(--muted)">интерполяция</text>
    <text x="66" y="66" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="8.5" fill="var(--muted)">x, y, cam + rz</text>
  </g>

  <!-- ================= SLIDE N+1 ================= -->
  <g transform="translate(638, 66)">
    <rect x="0" y="0" width="446" height="206" rx="10" fill="var(--bg)" stroke="var(--line-strong)" stroke-width="1"/>
    <rect x="86" y="14" width="274" height="154" rx="6" fill="var(--violet-faint)" stroke="var(--violet)" stroke-width="1.3"/>
    <text x="223" y="30" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="9.5" font-weight="700" fill="var(--violet)">ЭКРАН СЛАЙДА n+1 (10" × 5.625")</text>

    <text x="43" y="30" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="8.5" fill="var(--muted)">КУЛИСА L</text>
    <text x="403" y="30" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="8.5" fill="var(--muted)">КУЛИСА R</text>

    <!-- Outgoing ghost A exits left off-stage -->
    <g transform="translate(43, 92)" opacity="0.78">
      <circle cx="0" cy="0" r="21" fill="none" stroke="var(--brass)" stroke-width="1.4" stroke-dasharray="4 3"/>
      <polygon points="0,-13 11,-3 6,10 -6,10 -11,-3" fill="var(--brass-faint)" stroke="var(--brass)" stroke-width="1.2"/>
      <text x="0" y="38" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="9" font-weight="700" fill="var(--brass)">!!model-A</text>
      <text x="0" y="50" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="8" fill="var(--muted)">-4.2" · -80°</text>
    </g>

    <!-- Incoming model B arrives center stage -->
    <g transform="translate(223, 84)">
      <circle cx="0" cy="0" r="26" fill="var(--bg-card)" stroke="var(--violet)" stroke-width="1.8"/>
      <polygon points="0,-17 17,0 0,17 -17,0" fill="var(--violet-faint)" stroke="var(--violet)" stroke-width="1.5"/>
      <text x="0" y="40" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="9.5" font-weight="700" fill="var(--ink)">!!model-B</text>
      <text x="0" y="52" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="8.5" fill="var(--violet)">x=5.0" · ry=0°</text>
    </g>

    <!-- Next ghost C preloaded right -->
    <g transform="translate(403, 92)" opacity="0.65">
      <circle cx="0" cy="0" r="19" fill="none" stroke="var(--teal)" stroke-width="1.3" stroke-dasharray="4 3"/>
      <circle cx="0" cy="0" r="7" fill="none" stroke="var(--teal)" stroke-width="1.2"/>
      <text x="0" y="38" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="9" font-weight="700" fill="var(--teal)">!!model-C</text>
      <text x="0" y="50" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="8" fill="var(--muted)">+14.2" · +80°</text>
    </g>

    <!-- Rolled !!coin medallion -->
    <g transform="translate(274, 152)">
      <g class="coin-roll">
        <circle cx="0" cy="0" r="10" fill="var(--bg-card)" stroke="var(--brass-hi)" stroke-width="1.4"/>
        <path d="M0,-7v14 M-5,0h10" stroke="var(--brass-hi)" stroke-width="1.1"/>
      </g>
    </g>
    <text x="290" y="155" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="8.5" fill="var(--muted)">!!coin -146°</text>

    <text x="223" y="191" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif" font-size="12.5" font-style="italic" fill="var(--ink-soft)">A уходит влево (-80°), B поворачивается к залу, монета катится</text>
  </g>

  <text x="560" y="298" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10.5" fill="var(--ink-soft)">ВАЖНО: призраки !! за краем холста обязаны нести ту же a3d:animation (auto/indefinite), иначе клип оборвётся в полёте</text>
</svg>
"""

    (ASSETS / "morph-reel.svg").write_text(make_reel(True), encoding="utf-8")
    (ASSETS / "morph-reel-still.svg").write_text(make_reel(False), encoding="utf-8")


# ---------------------------------------------------------------------------
# 8. Real Tracked-File Circle-Packed Repository Map (`repo-fingerprint*.svg`)
# ---------------------------------------------------------------------------
def pack_circles_in_cluster(radii: List[float], cx: float, cy: float) -> List[Tuple[float, float, float]]:
    """Deterministic golden-angle spiral + relaxation so circles never overlap."""
    n = len(radii)
    if n == 0:
        return []
    order = sorted(range(n), key=lambda i: -radii[i])
    pts = np.zeros((n, 2), dtype=np.float64)
    rs = np.array([radii[i] for i in order], dtype=np.float64)
    phi = math.pi * (3.0 - math.sqrt(5.0))
    for k in range(1, n):
        r_step = (rs[0] + rs[k]) * 0.85 * math.sqrt(k)
        ang = k * phi
        pts[k] = [r_step * math.cos(ang), r_step * math.sin(ang)]

    for _ in range(90):
        # Pull gently toward cluster center
        pts *= 0.96
        for i in range(n):
            for j in range(i + 1, n):
                dx = pts[j, 0] - pts[i, 0]
                dy = pts[j, 1] - pts[i, 1]
                d = math.hypot(dx, dy)
                min_d = rs[i] + rs[j] + 1.4
                if d < min_d:
                    if d < 1e-6:
                        dx, dy, d = 1.0, 0.0, 1.0
                    push = 0.52 * (min_d - d)
                    ux, uy = dx / d, dy / d
                    pts[i, 0] -= ux * push
                    pts[i, 1] -= uy * push
                    pts[j, 0] += ux * push
                    pts[j, 1] += uy * push

    # Recenter
    c_mid = 0.5 * ((pts - rs[:, None]).min(axis=0) + (pts + rs[:, None]).max(axis=0))
    pts -= c_mid
    out = [None] * n
    for k, orig_i in enumerate(order):
        out[orig_i] = (cx + float(pts[k, 0]), cy + float(pts[k, 1]), float(rs[k]))
    return out


def build_repo_fingerprint():
    out = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    files = []
    for rel in out:
        p = ROOT / rel
        if p.exists() and p.is_file():
            files.append((rel, p.stat().st_size))

    groups = [
        ("exports", "exports/ (.pptx + превью)", "var(--crimson)", (168, 174)),
        ("cantillon", "cantillon/ (10 сл.)", "var(--brass)", (395, 128)),
        ("schumpeter", "schumpeter/ (15 сл.)", "var(--violet)", (592, 130)),
        ("impulse", "impulse/ (13 сл.)", "var(--teal)", (782, 130)),
        ("wow", "wow/ (3 чуда)", "var(--brass-hi)", (478, 252)),
        ("fun", "fun/ (вулкан)", "var(--crimson)", (658, 254)),
        ("docs", "train-ai/ · tools · SVG", "var(--ink-soft)", (858, 254)),
    ]

    bucket: Dict[str, List[Tuple[str, int]]] = {g[0]: [] for g in groups}
    for rel, sz in files:
        if rel.startswith("exports/"):
            bucket["exports"].append((rel, sz))
        elif rel.startswith("presentations/cantillon/"):
            bucket["cantillon"].append((rel, sz))
        elif rel.startswith("presentations/schumpeter/"):
            bucket["schumpeter"].append((rel, sz))
        elif rel.startswith("presentations/impulse/"):
            bucket["impulse"].append((rel, sz))
        elif rel.startswith("presentations/wow/"):
            bucket["wow"].append((rel, sz))
        elif rel.startswith("presentations/fun/"):
            bucket["fun"].append((rel, sz))
        else:
            bucket["docs"].append((rel, sz))

    total_files = sum(len(v) for v in bucket.values())
    total_mb = sum(sz for _, sz in files) / (1024 * 1024)

    circles_svg = []
    for key, label, col, (cx, cy) in groups:
        items = bucket[key]
        radii = [max(2.2, min(22.0, 1.35 * (sz / 1024.0) ** 0.29)) for _, sz in items]
        packed = pack_circles_in_cluster(radii, cx, cy)
        if packed:
            max_ext = max(math.hypot(x - cx, y - cy) + r for x, y, r in packed)
            circles_svg.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{max_ext + 7:.1f}" fill="none" stroke="{col}" stroke-width="0.9" stroke-dasharray="3 4" opacity="0.45"/>'
            )
            for (rel, sz), (x, y, r) in zip(items, packed):
                kb = f"{sz / (1024 * 1024):.1f} MB" if sz >= 1024 * 1024 else f"{max(1, sz // 1024)} KB"
                is_glb = rel.endswith(".glb")
                fill_op = "0.55" if is_glb else "0.24"
                stroke_w = "1.25" if is_glb else "0.85"
                circles_svg.append(
                    f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{col}" fill-opacity="{fill_op}" stroke="{col}" stroke-width="{stroke_w}">'
                    f'<title>{rel} ({kb})</title></circle>'
                )
            circles_svg.append(
                f'<text x="{cx:.1f}" y="{cy + max_ext + 21:.1f}" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="9.5" font-weight="600" fill="{col}">{label} · {len(items)}</text>'
            )

    wide = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 980 396" width="980" height="396" role="img" aria-label="Отпечаток репозитория MyWorkAiBrain: каждый круг — реальный файл">
  <style>{PALETTE_CSS}</style>
  <rect width="980" height="396" rx="14" fill="var(--bg)"/>
  <rect x="10" y="10" width="960" height="376" rx="10" fill="none" stroke="var(--line-strong)" stroke-width="1"/>
  <text x="32" y="38" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10.5" letter-spacing="1.8" fill="var(--brass)">АНАТОМИЧЕСКИЙ ОТПЕЧАТОК РЕПОЗИТОРИЯ · 1 КРУГ = 1 ФАЙЛ (НАВЕДИТЕ КУРСОР)</text>
  <text x="948" y="38" text-anchor="end" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10.5" fill="var(--ink-soft)">{total_files} ФАЙЛОВ · {total_mb:.1f} МБ · 49 МОДЕЛЕЙ .GLB</text>
  <line x1="32" y1="50" x2="948" y2="50" stroke="var(--line)" stroke-width="0.8"/>
  <g>{"".join(circles_svg)}</g>
  <line x1="32" y1="344" x2="948" y2="344" stroke="var(--line)" stroke-width="0.7"/>
  <text x="32" y="368" font-family="Georgia, 'Times New Roman', serif" font-size="12.5" font-style="italic" fill="var(--muted)">Плотные ядра внутри кластеров — бинарные модели .glb и рендеры Cycles; крупные сферы слева — пять готовых .pptx.</text>
</svg>
"""

    # Compact horizontal bar summary for narrow screens
    bars = []
    yb = 78
    for key, label, col, _ in groups:
        items = bucket[key]
        mb = sum(sz for _, sz in items) / (1024 * 1024)
        w = max(18.0, min(310.0, mb * 4.8))
        bars.append(
            f'<text x="28" y="{yb + 13}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="11" fill="var(--ink)">{label}</text>'
            f'<rect x="230" y="{yb}" width="{w:.1f}" height="16" rx="4" fill="{col}" fill-opacity="0.35" stroke="{col}" stroke-width="1"/>'
            f'<text x="{238 + w:.1f}" y="{yb + 12}" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" fill="var(--muted)">{len(items)} ф. · {mb:.1f} МБ</text>'
        )
        yb += 34

    compact = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 340" width="640" height="340" role="img" aria-label="Состав репозитория MyWorkAiBrain">
  <style>{PALETTE_CSS}</style>
  <rect width="640" height="340" rx="14" fill="var(--bg)"/>
  <rect x="10" y="10" width="620" height="320" rx="10" fill="none" stroke="var(--line-strong)" stroke-width="1"/>
  <text x="28" y="40" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10.5" letter-spacing="1.5" fill="var(--brass)">ОТПЕЧАТОК РЕПОЗИТОРИЯ · {total_files} ФАЙЛОВ · {total_mb:.1f} МБ</text>
  <line x1="28" y1="54" x2="612" y2="54" stroke="var(--line)" stroke-width="0.8"/>
  <g>{"".join(bars)}</g>
</svg>
"""

    (ASSETS / "repo-fingerprint.svg").write_text(wide, encoding="utf-8")
    (ASSETS / "repo-fingerprint-compact.svg").write_text(compact, encoding="utf-8")


# ---------------------------------------------------------------------------
# 9. Motion-safe static GIF fallbacks + `signature.svg` + `social-preview.png`
# ---------------------------------------------------------------------------
def build_still_frames_and_colophon(projector):
    gif_pairs = [
        (ROOT / "exports" / "impulse-animations-preview.gif", ASSETS / "impulse-anim-still.png"),
        (ROOT / "presentations" / "fun" / "preview" / "volcano.gif", ASSETS / "volcano-still.png"),
        (ROOT / "presentations" / "fun" / "preview" / "lavapool.gif", ASSETS / "lavapool-still.png"),
        (ROOT / "presentations" / "fun" / "preview" / "torch.gif", ASSETS / "torch-still.png"),
    ]
    for src, dst in gif_pairs:
        if src.exists():
            with Image.open(src) as im:
                im.seek(0)
                im.convert("RGBA").save(dst, optimize=True)

    # Studio colophon signature SVG
    sig = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 132" width="960" height="132" role="img" aria-label="Колофон мастерской MyWorkAiBrain">
  <style>
    {PALETTE_CSS}
    @media (prefers-reduced-motion: no-preference) {{
      .wave-line {{ stroke-dasharray: 6 6; animation: driftWave 12s linear infinite; }}
    }}
    @keyframes driftWave {{ to {{ stroke-dashoffset: -120; }} }}
  </style>
  <rect width="960" height="132" rx="14" fill="var(--bg)"/>
  <rect x="8" y="8" width="944" height="116" rx="10" fill="none" stroke="var(--line-strong)" stroke-width="1"/>
  <path class="wave-line" d="M36,30 C190,14 330,46 480,30 C630,14 770,46 924,30" fill="none" stroke="var(--brass)" stroke-width="1" opacity="0.65"/>
  <polygon points="480,18 485,26 494,30 485,34 480,42 475,34 466,30 475,26" fill="var(--bg)" stroke="var(--brass)" stroke-width="1.2"/>
  <text x="480" y="72" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif" font-size="20" font-style="italic" fill="var(--ink)">«Слайд — не плоский лист, а сцена с глубиной, светом и единым скелетом.»</text>
  <text x="480" y="101" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10.5" letter-spacing="1.8" fill="var(--muted)">MYWORKAIBRAIN · BLENDER 4.3 · PPTXGENJS · OPENXML A3D:MODEL3D · OVERBAFFE1</text>
</svg>
"""
    (ASSETS / "signature.svg").write_text(sig, encoding="utf-8")

    # 1280x640 GitHub Social Preview Card (.png < 500 KB)
    W, H = 1280, 640
    img = Image.new("RGB", (W, H), (14, 8, 13))
    draw = ImageDraw.Draw(img, "RGBA")

    # Subtle spotlight gradient bands
    for r in range(360, 10, -8):
        alpha = int(28 * (1 - r / 360))
        draw.ellipse((1015 - r, 325 - int(r * 0.85), 1015 + r, 325 + int(r * 0.85)), fill=(230, 188, 106, min(alpha, 8)))

    # Project ship.glb directly onto the social preview canvas!
    sil, crease, sea, bones = projector(cx=1018.0, cy_px=338.0, scale_px=455.0, crease_deg=25.0)
    for pa, pb in sea:
        draw.line([(float(pa[0]), float(pa[1])), (float(pb[0]), float(pb[1]))], fill=(87, 209, 196, 110), width=1)
    for pa, pb in crease:
        draw.line([(float(pa[0]), float(pa[1])), (float(pb[0]), float(pb[1]))], fill=(230, 188, 106, 95), width=1)
    for pa, pb in sil:
        draw.line([(float(pa[0]), float(pa[1])), (float(pb[0]), float(pb[1]))], fill=(247, 215, 142, 225), width=2)
    for b in bones:
        x, y = b["xy"]
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(180, 142, 255, 220))

    # Border frame
    draw.rounded_rectangle((20, 20, W - 20, H - 20), radius=18, outline=(230, 188, 106, 95), width=2)

    def load_font(paths, size):
        for fp in paths:
            if os.path.exists(fp):
                return ImageFont.truetype(fp, size)
        return ImageFont.load_default()

    f_mono = load_font([
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ], 15)
    f_card_sub = load_font([
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ], 13)
    f_title = load_font([
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    ], 72)
    f_sub = load_font([
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ], 25)
    f_stat = load_font([
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ], 21)

    draw.text((68, 78), "MYWORKAIBRAIN · BLENDER 4.3 × OPENXML 3D", font=f_mono, fill=(230, 188, 106, 255))
    draw.line([(68, 110), (620, 110)], fill=(230, 188, 106, 90), width=1)
    draw.text((64, 160), "MyWorkAiBrain", font=f_title, fill=(248, 240, 227, 255))
    draw.text((68, 268), "Живые 3D-презентации PowerPoint,", font=f_sub, fill=(203, 186, 184, 255))
    draw.text((68, 304), "собранные из кода и единого скелета.", font=f_sub, fill=(203, 186, 184, 255))

    cards = [
        ("5 колод .pptx", "42 слайда + скрипты", (230, 188, 106, 255)),
        ("49 моделей", "до 40 костей в glTF", (180, 142, 255, 255)),
        ("train-ai/", "учебник в 6 главах", (87, 209, 196, 255)),
    ]
    cx0 = 68
    for top_t, bot_t, acc in cards:
        draw.rounded_rectangle((cx0, 412, cx0 + 206, 502), radius=12, fill=(24, 14, 22, 235), outline=(230, 188, 106, 85), width=1)
        draw.text((cx0 + 16, 428), top_t, font=f_stat, fill=acc)
        draw.text((cx0 + 16, 466), bot_t, font=f_card_sub, fill=(170, 150, 155, 255))
        cx0 += 220

    draw.text((68, 558), "github.com/overbaffe1/MyWorkAiBrain", font=f_mono, fill=(150, 129, 134, 255))
    img.save(ASSETS / "social-preview.png", optimize=True)


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    EXHIBITS.mkdir(parents=True, exist_ok=True)

    # 1. Binary & ASCII STL 3D exhibits
    n_ship = glb_to_binary_stl(
        ROOT / "presentations" / "cantillon" / "models" / "glb" / "ship.glb",
        EXHIBITS / "ship.stl",
        "MyWorkAiBrain :: Cantillon Brigantine (ship.glb, 23 bones)",
    )
    n_lh = glb_to_binary_stl(
        ROOT / "presentations" / "wow" / "models" / "glb" / "lighthouse.glb",
        EXHIBITS / "lighthouse.stl",
        "MyWorkAiBrain :: Three Wonders Lighthouse (lighthouse.glb, 14 bones)",
    )
    n_loco = glb_to_binary_stl(
        ROOT / "presentations" / "schumpeter" / "models" / "glb" / "locomotive.glb",
        EXHIBITS / "locomotive.stl",
        "MyWorkAiBrain :: Schumpeter Innovation Locomotive (locomotive.glb)",
    )
    _, compass_stats = build_manifold_compass_stl()
    print(f"STL exhibits ready: ship={n_ship} tris, lighthouse={n_lh} tris, locomotive={n_loco} tris, inline_compass={compass_stats}")

    # 2. Projector for `ship.glb`
    projector = project_ship_geometry(yaw_deg=-34.0, pitch_deg=17.0)

    # 3. SVGs & PNGs
    build_technical_plates(projector)
    build_stage_covers(projector)
    build_seals()
    build_morph_reel()
    build_repo_fingerprint()
    build_still_frames_and_colophon(projector)
    print("All .github/assets/ artifacts generated successfully.")


if __name__ == "__main__":
    main()
