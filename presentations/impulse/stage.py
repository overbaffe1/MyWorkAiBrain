# Backdrop assets for the "impulse buying" deck (no AI imagery, pure numpy gradients):
#   assets/stage-bg.jpg  deep digital-dusk gradient (indigo-black) + glow pools + vignette + grain
#   assets/glow.png      cool-warm light pool that sits behind the 3D models
#   assets/shadow.png    soft contact shadow under the models
#   assets/clear.png     1x1 transparent raster used by the off-slide "ghost" copies (Morph)
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
import os
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(A, exist_ok=True)
rng = np.random.default_rng(2026)

W, H = 2560, 1440
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
u, v = x / W, y / H
top = np.array([19, 18, 30], np.float32)
bot = np.array([8, 7, 13], np.float32)
img = top[None, None] * (1 - v[..., None]) + bot[None, None] * v[..., None]
# cool light from the upper right (screens), warm money-gold from the lower left
d1 = np.sqrt(((u - 0.80) * 1.6) ** 2 + (v - 0.16) ** 2)
img += np.array([20, 26, 40])[None, None] * np.clip(1 - d1 / 0.95, 0, 1)[..., None] ** 2
d2 = np.sqrt(((u - 0.08) * 1.6) ** 2 + (v - 1.02) ** 2)
img += np.array([26, 16, 8])[None, None] * np.clip(1 - d2 / 0.85, 0, 1)[..., None] ** 2
# a faint vertical "screen" band on the right third, so the composition leans to the model side
band = np.clip(1 - np.abs(u - 0.78) / 0.22, 0, 1) ** 3 * np.clip(1 - v, 0, 1) ** 2
img += np.array([10, 14, 26])[None, None] * band[..., None]
# vignette
dv = np.sqrt(((u - 0.5) * 1.22) ** 2 + ((v - 0.5) * 1.08) ** 2)
img *= (1 - 0.58 * np.clip(dv - 0.26, 0, 1) ** 1.4)[..., None]
img += rng.normal(0, 2.0, (H, W, 1))
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(os.path.join(A, "stage-bg.jpg"), quality=92)

S = 768
yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
r = np.sqrt((xx - S / 2) ** 2 + (yy - S / 2) ** 2) / (S / 2)
a = np.clip(1 - r, 0, 1) ** 2.2 * 0.52
g = np.zeros((S, S, 4), np.float32)
# warm gold core with a cool rim: reads as "screen light on a desk"
g[..., 0] = 232 + 22 * (1 - r)
g[..., 1] = 168 + 40 * (1 - r)
g[..., 2] = 96 + 120 * r
g[..., 3] = a * 255
Image.fromarray(g.astype(np.uint8)).save(os.path.join(A, "glow.png"))

SW, SH = 1024, 256
sh = Image.new("L", (SW, SH), 0)
ImageDraw.Draw(sh).ellipse([SW * 0.12, SH * 0.30, SW * 0.88, SH * 0.70], fill=200)
sh = sh.filter(ImageFilter.GaussianBlur(28))
out = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
out.putalpha(sh)
out.save(os.path.join(A, "shadow.png"))
Image.new("RGBA", (1, 1), (0, 0, 0, 0)).save(os.path.join(A, "clear.png"))
print("stage assets ok")
