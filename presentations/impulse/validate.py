"""QA checks for the exported impulse-spending 3D deck."""
import json
import os
import re
import struct
import sys
import zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
PPTX = os.path.join(ROOT, "exports", "impulse-buying-3d-presentation.pptx")
GLB_DIR = os.path.join(os.path.dirname(__file__), "models", "glb")
AM3D = "http://schemas.microsoft.com/office/drawing/2017/model3d"
A3D = "http://schemas.microsoft.com/office/drawing/2018/animation/model3d"
ANIMATED = {"phone", "brain", "paylater", "clipboard", "timer", "bag", "scales"}

def gltf_json(path):
    data = open(path, "rb").read()
    assert data[:4] == b"glTF", f"not a GLB: {path}"
    length = struct.unpack("<I", data[12:16])[0]
    return json.loads(data[20:20 + length].decode("utf-8"))

with zipfile.ZipFile(PPTX) as z:
    names = z.namelist()
    slides = sorted((n for n in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)), key=lambda p: int(re.search(r"slide(\d+)", p).group(1)))
    assert len(slides) == 10, f"expected 10 slides, found {len(slides)}"
    all_models = 0
    all_embedded = 0
    for i, name in enumerate(slides, 1):
        root = ET.fromstring(z.read(name))
        models = root.findall(f".//{{{AM3D}}}model3d")
        assert models, f"slide {i} has no native model3d"
        all_models += len(models)
        embedded = root.findall(f".//{{{A3D}}}embedAnim")
        all_embedded += len(embedded)
        if i < 10:
            assert embedded, f"slide {i} should carry a looping skinned model"
            assert any(el.attrib.get("presetID") == "100" for el in root.iter()), f"slide {i} has no auto-play Scene timing"
        ET.fromstring(z.read(f"ppt/slides/_rels/slide{i}.xml.rels"))
    assert "glb" in z.read("[Content_Types].xml").decode("utf-8").lower()
    print(f"PPTX: {len(slides)} slides, {all_models} native 3D placements (incl. Morph ghosts), {all_embedded} embedded model animations")
    for name in names:
        if name.endswith(".xml") or name.endswith(".rels"):
            ET.fromstring(z.read(name))

for key in sorted(ANIMATED):
    gltf = gltf_json(os.path.join(GLB_DIR, key + ".glb"))
    assert len(gltf.get("animations", [])) == 1, f"{key}: expected exactly one glTF animation"
    assert len(gltf.get("skins", [])) == 1, f"{key}: expected exactly one skin"
    assert not any("KHR_draco" in x for x in gltf.get("extensionsUsed", [])), f"{key}: Draco is not PowerPoint-safe"
    print(f"GLB {key}: one skinned animation, {len(gltf['skins'][0]['joints'])} joints, {os.path.getsize(os.path.join(GLB_DIR, key + '.glb')) // 1024} KB")

try:
    from pptx import Presentation
    prs = Presentation(PPTX)
    assert len(prs.slides) == 10
    print("python-pptx: opened successfully")
except ImportError:
    print("python-pptx unavailable; XML/ZIP validation completed")
