#!/usr/bin/env python3
"""Structural QA for the exported editable PowerPoint deck."""
import sys, zipfile
from xml.etree import ElementTree as ET

pptx=sys.argv[1] if len(sys.argv)>1 else "../../exports/ekonomika123-3d-presentation.pptx"
ns={
 "p":"http://schemas.openxmlformats.org/presentationml/2006/main",
 "r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships",
 "a":"http://schemas.openxmlformats.org/drawingml/2006/main",
}
with zipfile.ZipFile(pptx) as z:
    names=set(z.namelist())
    pres=ET.fromstring(z.read("ppt/presentation.xml"))
    slide_ids=pres.find("p:sldIdLst",ns)
    slides=sorted(n for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml") and "/_rels/" not in n)
    assert len(slide_ids)==10, f"expected 10 presentation slides, got {len(slide_ids)}"
    assert len(slides)==10, f"expected 10 slide parts, got {len(slides)}"
    models=animations=scene_effects=0
    notes_parts=[n for n in names if n.startswith("ppt/notesSlides/notesSlide") and n.endswith(".xml")]
    assert len(notes_parts)>=10, f"expected notes for all slides, got {len(notes_parts)}"
    for i in range(1,11):
        p=f"ppt/slides/slide{i}.xml"
        raw=z.read(p)
        root=ET.fromstring(raw)
        text=raw.decode("utf-8")
        nmodel=text.count("am3d:model3d")
        nanim=text.count("embedAnim")
        nscene=text.count('presetID="100"')
        assert nmodel>=1, f"slide {i} has no native 3D model"
        assert nanim>=1, f"slide {i} has no embedded GLB animation"
        assert nscene>=1, f"slide {i} has no repeating Scene effect"
        if i>1:
            assert "morph" in text and "p159" in text, f"slide {i} has no Morph transition"
        models+=nmodel; animations+=nanim; scene_effects+=nscene
    glbs=[n for n in names if n.startswith("ppt/media/model3d") and n.endswith(".glb")]
    assert len(glbs)>=9, f"expected at least 9 embedded exhibit models, got {len(glbs)}"
    assert "ppt/notesSlides/notesSlide1.xml" in names, "speaker notes are missing"
    # Parse every XML part to catch malformed XML early.
    xmls=[n for n in names if n.endswith(".xml") or n.endswith(".rels")]
    for n in xmls:
        ET.fromstring(z.read(n))
    print(f"OK: {len(slide_ids)} slides; {len(glbs)} GLBs; {models} 3D placements; {animations} embedded animations; {scene_effects} Scene effects; all XML parses")
try:
    from pptx import Presentation
    deck=Presentation(pptx)
    assert len(deck.slides)==10
    print("OK: python-pptx opens the deck")
except ImportError:
    print("NOTE: python-pptx not installed; Open XML structural checks passed")
