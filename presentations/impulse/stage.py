"""Generate a light notebook-paper stage that keeps the original collage/meme feel."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ASSETS = Path(__file__).resolve().parent / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(1234)
W, H = 2560, 1440
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
u, v = x / W, y / H

# Warm paper, a very subtle edge falloff and a fine notebook grid.
base = np.array([248, 245, 237], np.float32)
shade = 1 - 0.055 * np.clip(np.sqrt(((u - 0.5) * 1.18) ** 2 + ((v - 0.48) * 1.15) ** 2), 0, 1)
paper = base[None, None, :] * shade[..., None]
paper += rng.normal(0, 1.25, (H, W, 1))
img = Image.fromarray(np.clip(paper, 0, 255).astype(np.uint8), "RGB")
d = ImageDraw.Draw(img, "RGBA")
grid = (82, 139, 174, 24)
for xx in range(0, W, 56):
    d.line((xx, 0, xx, H), fill=grid, width=1)
for yy in range(0, H, 56):
    d.line((0, yy, W, yy), fill=grid, width=1)
# The red margin and two nearly invisible registration marks nod to the original notebook collage.
d.line((118, 0, 118, H), fill=(225, 77, 65, 38), width=2)
d.line((0, 128, W, 128), fill=(225, 77, 65, 20), width=1)
img.save(ASSETS / "stage-bg.jpg", quality=92, optimize=True)

# Soft warm halo behind the mascot; transparent so it works on the paper stage.
S = 768
yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
r = np.sqrt(((xx - S / 2) / (S / 2)) ** 2 + ((yy - S / 2) / (S / 2)) ** 2)
a = np.clip(1 - r, 0, 1) ** 2.2 * 0.28
halo = np.zeros((S, S, 4), np.uint8)
halo[..., 0] = 238
halo[..., 1] = 139
halo[..., 2] = 82
halo[..., 3] = (a * 255).astype(np.uint8)
Image.fromarray(halo, "RGBA").save(ASSETS / "glow.png", optimize=True)

# Soft contact shadow.
SW, SH = 900, 240
mask = Image.new("L", (SW, SH), 0)
ImageDraw.Draw(mask).ellipse((SW * 0.12, SH * 0.25, SW * 0.88, SH * 0.75), fill=122)
mask = mask.filter(ImageFilter.GaussianBlur(30))
shadow = Image.new("RGBA", (SW, SH), (44, 34, 29, 0))
shadow.putalpha(mask)
shadow.save(ASSETS / "shadow.png", optimize=True)
Image.new("RGBA", (1, 1), (0, 0, 0, 0)).save(ASSETS / "clear.png")
print("stage assets written to", ASSETS)
