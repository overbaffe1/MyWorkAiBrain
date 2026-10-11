# Calm, modern background assets for the impulse-spending deck.
# Generated mathematically; no stock or AI images are used.
import os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)
rng = np.random.default_rng(20261011)

# Deep ink-blue field, with a teal exhibit light on the right and a restrained coral haze.
W, H = 2400, 1350
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
u, v = x / W, y / H
c0 = np.array([7, 12, 22], np.float32)
c1 = np.array([13, 23, 34], np.float32)
img = c0[None, None, :] * (1 - v[..., None]) + c1[None, None, :] * v[..., None]
# Faint cool light behind the 3D object and a distant warm counter-light.
d1 = np.sqrt(((u - 0.76) * 1.55) ** 2 + ((v - 0.42) * 1.08) ** 2)
img += np.array([9, 30, 32], np.float32)[None, None, :] * np.clip(1 - d1 / 0.9, 0, 1)[..., None] ** 2
d2 = np.sqrt(((u - 0.10) * 1.25) ** 2 + ((v - 0.80) * 1.1) ** 2)
img += np.array([18, 7, 8], np.float32)[None, None, :] * np.clip(1 - d2 / 0.75, 0, 1)[..., None] ** 2
# Gentle vignette and fine photographic grain.
dv = np.sqrt(((u - 0.5) * 1.2) ** 2 + ((v - 0.5) * 1.1) ** 2)
img *= (1 - 0.48 * np.clip(dv - 0.28, 0, 1) ** 1.55)[..., None]
img += rng.normal(0, 1.1, (H, W, 1))
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(os.path.join(ASSETS, "stage-bg.jpg"), quality=93)

# Soft teal spotlight behind the model (transparent PNG).
S = 900
y, x = np.mgrid[0:S, 0:S].astype(np.float32)
r = np.sqrt(((x - S / 2) / (S / 2)) ** 2 + ((y - S / 2) / (S / 2)) ** 2)
a = np.clip(1 - r, 0, 1) ** 2.15 * 0.46
glow = np.zeros((S, S, 4), np.uint8)
glow[..., 0], glow[..., 1], glow[..., 2] = 67, 198, 190
glow[..., 3] = np.clip(a * 255, 0, 255).astype(np.uint8)
Image.fromarray(glow).save(os.path.join(ASSETS, "glow.png"))

# Soft contact shadow used under the floating 3D exhibit.
SW, SH = 1100, 280
shadow = Image.new("L", (SW, SH), 0)
ImageDraw.Draw(shadow).ellipse([SW * 0.10, SH * 0.28, SW * 0.90, SH * 0.72], fill=150)
shadow = shadow.filter(ImageFilter.GaussianBlur(32))
out = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
out.putalpha(shadow)
out.save(os.path.join(ASSETS, "shadow.png"))
Image.new("RGBA", (1, 1), (0, 0, 0, 0)).save(os.path.join(ASSETS, "clear.png"))
print("impulse stage assets ready")
