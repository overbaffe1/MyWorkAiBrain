#!/usr/bin/env python3
"""Universal structural validator for 3D PowerPoint (.pptx) decks built in this repo.

Checks:
  1. Every .xml and .rels file in the archive parses cleanly.
  2. [Content_Types].xml declares model/gltf.binary (.glb).
  3. Slide count in ppt/presentation.xml matches ppt/slides/slide*.xml.
  4. Every slide contains at least one native PowerPoint 3D model (am3d:model3d)
     with a matching PNG fallback inside mc:AlternateContent.
  5. No duplicate 3D-model names or IDs on the same slide (PowerPoint silently drops
     duplicate model3d names).
  6. Embedded .glb binaries are valid glTF 2.0 without Draco compression; if animated
     (default), every slide has a3danim:embedAnim + looping Scene timing (presetID="100"),
     and animated .glb files use skinned animation (skins >= 1, animations == 1).
  7. Slides 2..N have Morph transitions (unless --no-morph).
  8. Speaker notes exist for all slides (unless --no-notes).

Usage:
  python3 presentations/tools/validate-pptx.py exports/cantillon-3d-presentation.pptx
  python3 presentations/tools/validate-pptx.py exports/schumpeter-3d-presentation.pptx --allow-static
"""
import argparse
import json
import struct
import sys
import zipfile
from xml.etree import ElementTree as ET

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "am3d": "http://schemas.microsoft.com/office/drawing/2017/model3d",
}


def check_glb(name: str, data: bytes) -> tuple[bool, int, int]:
    if len(data) < 20 or data[:4] != b"glTF":
        raise AssertionError(f"{name}: invalid GLB magic header")
    version = struct.unpack("<I", data[4:8])[0]
    if version != 2:
        raise AssertionError(f"{name}: expected glTF v2, got v{version}")
    json_len = struct.unpack("<I", data[12:16])[0]
    gltf = json.loads(data[20 : 20 + json_len].decode("utf-8"))
    exts_req = set(gltf.get("extensionsRequired") or [])
    exts_used = set(gltf.get("extensionsUsed") or [])
    if "KHR_draco_mesh_compression" in (exts_req | exts_used):
        raise AssertionError(f"{name}: uses Draco compression (unsupported by PowerPoint)")
    n_anims = len(gltf.get("animations") or [])
    n_skins = len(gltf.get("skins") or [])
    if n_anims > 0 and n_skins == 0:
        raise AssertionError(
            f"{name}: has {n_anims} animation(s) but 0 skins — PowerPoint ignores node TRS / morph animations!"
        )
    if n_anims > 1:
        raise AssertionError(
            f"{name}: has {n_anims} separate glTF animations — combine into 1 armature + 1 action for PowerPoint"
        )
    return (n_anims == 1 and n_skins >= 1), n_skins, n_anims


def validate(path: str, expect_slides: int | None, allow_static: bool, require_morph: bool, require_notes: bool) -> None:
    with zipfile.ZipFile(path, "r") as z:
        names = set(z.namelist())

        # 1. Parse all XML / .rels files
        for item in sorted(names):
            if item.endswith(".xml") or item.endswith(".rels"):
                try:
                    ET.fromstring(z.read(item))
                except ET.ParseError as exc:
                    raise AssertionError(f"{item}: malformed XML ({exc})") from exc

        # 2. Content_Types check for .glb
        ct_raw = z.read("[Content_Types].xml").decode("utf-8")
        if 'Extension="glb"' not in ct_raw or "model/gltf.binary" not in ct_raw:
            raise AssertionError("[Content_Types].xml is missing Extension=\"glb\" ContentType=\"model/gltf.binary\"")

        # 3. Slide count
        pres = ET.fromstring(z.read("ppt/presentation.xml"))
        sld_ids = pres.find("p:sldIdLst", NS)
        n_pres_slides = len(sld_ids) if sld_ids is not None else 0
        slide_files = sorted(
            n for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml") and "/_rels/" not in n
        )
        if n_pres_slides != len(slide_files) or n_pres_slides == 0:
            raise AssertionError(f"slide count mismatch: presentation.xml={n_pres_slides}, files={len(slide_files)}")
        if expect_slides is not None and n_pres_slides != expect_slides:
            raise AssertionError(f"expected {expect_slides} slides, got {n_pres_slides}")

        # 4. Validate all embedded .glb files
        glb_files = sorted(n for n in names if n.startswith("ppt/media/") and n.endswith(".glb"))
        if not glb_files:
            raise AssertionError("no .glb files found in ppt/media/")
        animated_glbs = 0
        for gf in glb_files:
            is_anim, _, _ = check_glb(gf, z.read(gf))
            if is_anim:
                animated_glbs += 1

        if not allow_static and animated_glbs == 0:
            raise AssertionError("no animated (skinned) .glb models found (pass --allow-static for static 3D decks)")

        # 5. Per-slide checks
        total_models = 0
        total_embeds = 0
        total_scenes = 0
        for idx in range(1, n_pres_slides + 1):
            sp = f"ppt/slides/slide{idx}.xml"
            raw = z.read(sp)
            text = raw.decode("utf-8")
            root = ET.fromstring(raw)

            # Check Choice vs Fallback and unique model3d names
            model_names: list[str] = []
            model_ids: list[str] = []
            for ac in root.findall(".//mc:AlternateContent", NS):
                choice = ac.find("mc:Choice", NS)
                fallback = ac.find("mc:Fallback", NS)
                if choice is None or choice.find(".//am3d:model3d", NS) is None:
                    continue
                if fallback is None or fallback.find(".//p:pic", NS) is None:
                    raise AssertionError(f"slide {idx}: am3d:model3d missing PNG p:pic fallback in mc:Fallback")
                cnv = choice.find(".//p:cNvPr", NS)
                if cnv is not None:
                    model_names.append(cnv.attrib.get("name", ""))
                    model_ids.append(cnv.attrib.get("id", ""))

            if not model_names:
                raise AssertionError(f"slide {idx}: no native am3d:model3d found")
            if len(set(model_names)) != len(model_names):
                raise AssertionError(f"slide {idx}: duplicate 3D model names on slide: {model_names}")
            if len(set(model_ids)) != len(model_ids):
                raise AssertionError(f"slide {idx}: duplicate 3D model shape IDs on slide: {model_ids}")

            n_embed = text.count("embedAnim")
            n_scene = text.count('presetID="100"')
            if not allow_static:
                if n_embed < 1:
                    raise AssertionError(f"slide {idx}: missing a3danim:embedAnim")
                if n_scene < 1:
                    raise AssertionError(f"slide {idx}: missing auto-playing Scene timing (presetID=\"100\")")

            if require_morph and idx > 1:
                if "morph" not in text or "p159" not in text:
                    raise AssertionError(f"slide {idx}: missing Morph transition (p159:morph)")

            total_models += len(model_names)
            total_embeds += n_embed
            total_scenes += n_scene

        # 6. Speaker notes check
        notes_files = sorted(n for n in names if n.startswith("ppt/notesSlides/notesSlide") and n.endswith(".xml"))
        if require_notes and len(notes_files) < n_pres_slides:
            raise AssertionError(f"expected speaker notes for all {n_pres_slides} slides, found {len(notes_files)}")

    try:
        from pptx import Presentation  # type: ignore

        prs = Presentation(path)
        if len(prs.slides) != n_pres_slides:
            raise AssertionError(f"python-pptx read {len(prs.slides)} slides, expected {n_pres_slides}")
        pptx_tag = "python-pptx OK"
    except ImportError:
        pptx_tag = "python-pptx not installed (OpenXML checks OK)"

    print(
        f"VALIDATED {path}: {n_pres_slides} slides | {len(glb_files)} GLBs ({animated_glbs} rigged) | "
        f"{total_models} 3D placements | {total_embeds} embedAnim | {total_scenes} Scene loops | "
        f"{len(notes_files)} notes | {pptx_tag}"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate a 3D PowerPoint (.pptx) deck.")
    ap.add_argument("pptx", help="Path to the .pptx file")
    ap.add_argument("--expect-slides", type=int, default=None, help="Expected number of slides")
    ap.add_argument("--allow-static", action="store_true", help="Allow static 3D models without skinned animation")
    ap.add_argument("--no-morph", action="store_true", help="Skip Morph transition check on slides 2..N")
    ap.add_argument("--no-notes", action="store_true", help="Skip speaker notes check")
    args = ap.parse_args()
    try:
        validate(
            args.pptx,
            expect_slides=args.expect_slides,
            allow_static=args.allow_static,
            require_morph=not args.no_morph,
            require_notes=not args.no_notes,
        )
    except Exception as exc:
        print(f"VALIDATION FAILED ({args.pptx}): {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
