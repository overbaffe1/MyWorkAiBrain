# Small transparent comic-glow/fallback assets for the collaged 3D stickers.
# The actual slide texture and paper/meme assets come from the original PPTX.
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)

S = 768
y, x = np.mgrid[0:S, 0:S].astype(np.float32)
r = np.sqrt(((x-S/2)/(S/2))**2 + ((y-S/2)/(S/2))**2)
a = np.clip(1-r, 0, 1)**2.1 * 0.33
rgba = np.zeros((S,S,4), dtype=np.uint8)
rgba[...,0], rgba[...,1], rgba[...,2] = 255, 184, 61
rgba[...,3] = np.clip(a*255,0,255).astype(np.uint8)
Image.fromarray(rgba,"RGBA").save(os.path.join(ASSETS,"glow.png"))
Image.new("RGBA",(1,1),(0,0,0,0)).save(os.path.join(ASSETS,"clear.png"))
print("comic-stage assets generated")
