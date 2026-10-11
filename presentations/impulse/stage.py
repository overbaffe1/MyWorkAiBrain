# Handmade graph-paper collage assets for the meme-forward impulse-spending deck.
# Generated locally; the original presentation's cutout/meme style is carried by its own images.
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)
rng = np.random.default_rng(20261012)

# Warm notebook paper with faint blue rules, one red margin, soft paper grain and a torn bottom.
W, H = 2400, 1350
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
base = np.zeros((H, W, 3), np.float32)
base[:] = (250, 247, 236)
shade = np.clip(((x / W - .5) ** 2 + (y / H - .5) ** 2) * 13, 0, 5)
base -= shade[..., None]
base += rng.normal(0, 1.45, (H, W, 1))
img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
d = ImageDraw.Draw(img, "RGBA")
# Original deck used graph/ruled-paper textures. Keep these intentionally subtle under text.
for yy in range(36, H, 72):
    d.line((0, yy, W, yy), fill=(53, 127, 190, 25), width=2)
for xx in range(32, W, 72):
    d.line((xx, 0, xx, H), fill=(53, 127, 190, 13), width=1)
d.line((150, 0, 150, H), fill=(227, 64, 70, 82), width=4)
# Soft, irregular torn-paper edge at the bottom, echoed by a faint shadow.
pts = [(0, H)]
for xx in range(0, W + 60, 60):
    pts.append((xx, H - 15 + int(rng.integers(-8, 9))))
pts.append((W, H))
d.polygon(pts, fill=(255, 253, 246, 120))
img.save(os.path.join(ASSETS, "stage-bg.jpg"), quality=94, subsampling=0)

# Comic-book yellow burst behind each 3D exhibit, with a hand-drawn red outline.
S = 1100
burst = Image.new("RGBA", (S, S), (0, 0, 0, 0))
bd = ImageDraw.Draw(burst, "RGBA")
cx = cy = S / 2
points = []
for i in range(64):
    a = math.tau * i / 64 - math.pi / 2
    r = S * (0.49 if i % 2 == 0 else 0.365)
    points.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
bd.polygon(points, fill=(255, 221, 74, 202), outline=(220, 45, 54, 238), width=11)
# A few fine rays add a marker-drawn, pasted-sticker feel without overpowering the model.
for i in range(0, 64, 8):
    a = math.tau * i / 64 - math.pi / 2
    p1 = (cx + math.cos(a) * S * .41, cy + math.sin(a) * S * .41)
    p2 = (cx + math.cos(a) * S * .47, cy + math.sin(a) * S * .47)
    bd.line((p1, p2), fill=(255, 250, 226, 190), width=5)
burst.save(os.path.join(ASSETS, "glow.png"))

# Contact shadow for transparent 3D cutouts on paper.
SW, SH = 1100, 270
shadow = Image.new("L", (SW, SH), 0)
ImageDraw.Draw(shadow).ellipse([SW * .12, SH * .23, SW * .88, SH * .76], fill=94)
shadow = shadow.filter(ImageFilter.GaussianBlur(34))
out = Image.new("RGBA", (SW, SH), (20, 23, 29, 0))
out.putalpha(shadow)
out.save(os.path.join(ASSETS, "shadow.png"))
Image.new("RGBA", (1, 1), (0, 0, 0, 0)).save(os.path.join(ASSETS, "clear.png"))
print("meme-collage stage assets ready")
