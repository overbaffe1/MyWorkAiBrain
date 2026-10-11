# Generates a calm dark-blue behavioral-lab stage (no AI or stock imagery):
#   assets/stage-bg.jpg  ink-blue gradient, vignette and subtle grain
#   assets/glow.png      muted amber pool behind the 3D exhibit
#   assets/shadow.png    soft contact shadow
import os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")
os.makedirs(A, exist_ok=True)
rng = np.random.default_rng(2026)

W, H = 2560, 1440
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
u, v = x / W, y / H
# Restrained midnight palette with a cool upper-right wash.
top = np.array([18, 30, 49], np.float32)
bot = np.array([8, 14, 26], np.float32)
img = top[None, None] * (1 - v[..., None]) + bot[None, None] * v[..., None]
d1 = np.sqrt(((u - 0.80) * 1.5) ** 2 + (v - 0.24) ** 2)
img += np.array([12, 23, 35], np.float32)[None, None] * np.clip(1 - d1 / 0.9, 0, 1)[..., None] ** 2
d2 = np.sqrt(((u - 0.12) * 1.6) ** 2 + (v - 0.88) ** 2)
img += np.array([17, 10, 3], np.float32)[None, None] * np.clip(1 - d2 / 0.8, 0, 1)[..., None] ** 2
dv = np.sqrt(((u - 0.5) * 1.22) ** 2 + ((v - 0.5) * 1.08) ** 2)
img *= (1 - 0.47 * np.clip(dv - 0.28, 0, 1) ** 1.55)[..., None]
img += rng.normal(0, 1.35, (H, W, 1))
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(os.path.join(A, "stage-bg.jpg"), quality=93)

S = 768
yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
r = np.sqrt((xx - S / 2) ** 2 + (yy - S / 2) ** 2) / (S / 2)
a = np.clip(1 - r, 0, 1) ** 2.0 * 0.36
g = np.zeros((S, S, 4), np.float32)
g[..., 0], g[..., 1], g[..., 2] = 236, 177, 104
g[..., 3] = a * 255
Image.fromarray(g.astype(np.uint8)).save(os.path.join(A, "glow.png"))

SW, SH = 1024, 256
sh = Image.new("L", (SW, SH), 0)
ImageDraw.Draw(sh).ellipse([SW * 0.12, SH * 0.29, SW * 0.88, SH * 0.71], fill=185)
sh = sh.filter(ImageFilter.GaussianBlur(30))
out = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
out.putalpha(sh)
out.save(os.path.join(A, "shadow.png"))
Image.new("RGBA", (1, 1), (0, 0, 0, 0)).save(os.path.join(A, "clear.png"))
print("behavioral-lab stage assets generated")
