"""Validate the final deck package and the animated, skinned chestnut GLB."""
from __future__ import annotations

import json
import struct
import zipfile
from pathlib import Path
from lxml import etree
from pptx import Presentation

ROOT = Path(__file__).resolve().parents[2]
PPTX = ROOT / "ekonomika123.pptx"
GLB = ROOT / "presentations" / "impulse" / "models" / "glb" / "kashtan.glb"

assert PPTX.exists(), f"missing {PPTX}"
assert GLB.exists(), f"missing {GLB}"

with zipfile.ZipFile(PPTX) as z:
    names = z.namelist()
    slides = sorted((n for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml")),
                    key=lambda n: int(n.rsplit("slide", 1)[1][:-4]))
    assert len(slides) == 10, f"expected 10 slides, got {len(slides)}"
    for i, slide in enumerate(slides, 1):
        raw = z.read(slide)
        etree.fromstring(raw)
        xml = raw.decode("utf-8")
        assert "am3d:model3d" in xml, f"slide {i}: native 3D model missing"
        assert "!!m-kashtan" in xml, f"slide {i}: named mascot missing"
        assert "embedAnim" in xml, f"slide {i}: embedded animation missing"
        assert 'presetID="100"' in xml, f"slide {i}: looping Scene timing missing"
        if i > 1:
            assert "morph" in xml.lower(), f"slide {i}: Morph transition missing"
    assert any(n.startswith("ppt/notesSlides/notesSlide") and n.endswith(".xml") for n in names), "speaker notes missing"
    model_files = [n for n in names if n.startswith("ppt/media/model3d") and n.endswith(".glb")]
    assert len(model_files) == 10, f"expected 10 embedded model instances, got {len(model_files)}"
    for name in model_files:
        payload = z.read(name)
        assert payload[:4] == b"glTF", f"invalid GLB header: {name}"

buf = GLB.read_bytes()
assert buf[:4] == b"glTF", "not a GLB binary"
json_len = struct.unpack_from("<I", buf, 12)[0]
gltf = json.loads(buf[20:20 + json_len])
assert len(gltf.get("animations", [])) == 1, "GLB must have exactly one animation"
assert len(gltf.get("skins", [])) == 1, "GLB must have exactly one skin"
assert gltf.get("animations", [{}])[0].get("channels"), "GLB animation has no channels"
assert not any("draco" in ext.lower() for ext in gltf.get("extensionsUsed", [])), "Draco compression unsupported by PowerPoint"
prs = Presentation(PPTX)
assert len(prs.slides) == 10
print(f"[ok] {PPTX.name}: 10 valid slides, 10 native 3D models, looping animation, Morph, speaker notes")
print(f"[ok] kashtan.glb: {len(gltf['skins'][0]['joints'])} joints, {len(gltf['animations'][0]['channels'])} channels")
print(f"[ok] PPTX size {PPTX.stat().st_size / 1e6:.2f} MB")
