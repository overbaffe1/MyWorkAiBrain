# Cantillon deck variant of ../schumpeter/stage.py (warm candle-lit palette).
# Generates the neutral "stage" assets (no AI imagery):
#   assets/stage-bg.jpg  deep wine-black gradient + vignette + fine film grain
#   assets/glow.png      warm radial light pool that sits behind the 3D models
#   assets/shadow.png    soft contact shadow placed under the 3D models
import numpy as np
from PIL import Image, ImageFilter
import os
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(A, exist_ok=True)
rng = np.random.default_rng(1734)

W, H = 2560, 1440
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
u, v = x / W, y / H
top = np.array([24, 13, 17], np.float32)
bot = np.array([10, 6, 8], np.float32)
img = top[None, None] * (1 - v[..., None]) + bot[None, None] * v[..., None]
# faint cool light from upper right, warm from lower left
d1 = np.sqrt(((u - 0.78) * 1.6) ** 2 + (v - 0.18) ** 2)
img += np.array([26, 14, 12])[None, None] * np.clip(1 - d1 / 0.9, 0, 1)[..., None] ** 2
d2 = np.sqrt(((u - 0.1) * 1.6) ** 2 + (v - 1.0) ** 2)
img += np.array([10, 6, 10])[None, None] * np.clip(1 - d2 / 0.8, 0, 1)[..., None] ** 2
# vignette
dv = np.sqrt(((u - 0.5) * 1.25) ** 2 + ((v - 0.5) * 1.1) ** 2)
img *= (1 - 0.55 * np.clip(dv - 0.25, 0, 1) ** 1.5)[..., None]
img += rng.normal(0, 2.2, (H, W, 1))
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(os.path.join(A, "stage-bg.jpg"), quality=92)

S = 768
yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
r = np.sqrt((xx - S / 2) ** 2 + (yy - S / 2) ** 2) / (S / 2)
a = np.clip(1 - r, 0, 1) ** 2.2 * 0.55
g = np.zeros((S, S, 4), np.float32)
g[..., 0], g[..., 1], g[..., 2] = 236, 160, 80
g[..., 3] = a * 255
Image.fromarray(g.astype(np.uint8)).save(os.path.join(A, "glow.png"))

SW, SH = 1024, 256
sh = Image.new("L", (SW, SH), 0)
from PIL import ImageDraw
ImageDraw.Draw(sh).ellipse([SW * 0.12, SH * 0.30, SW * 0.88, SH * 0.70], fill=200)
sh = sh.filter(ImageFilter.GaussianBlur(28))
out = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
out.putalpha(sh)
out.save(os.path.join(A, "shadow.png"))
# 1x1 transparent raster for off-slide (morph "ghost") model copies
Image.new("RGBA", (1, 1), (0, 0, 0, 0)).save(os.path.join(A, "clear.png"))
print("stage assets ok")
