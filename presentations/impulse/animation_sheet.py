"""Combine per-model Blender previews into one six-panel animated QA GIF."""
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps

src, out = sys.argv[1:3]
keys = ["phone", "brain", "paylater", "clipboard", "timer", "bag"]
size, label_h, gap, margin = 260, 28, 12, 14
cols, rows = 3, 2
files = [os.path.join(src, key + ".gif") for key in keys]
for p in files:
    if not os.path.isfile(p):
        raise FileNotFoundError(p)

gifs = [Image.open(p) for p in files]
frame_counts = [getattr(im, "n_frames", 1) for im in gifs]
frame_n = max(frame_counts)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
except OSError:
    font = ImageFont.load_default()
canvas_w = margin * 2 + cols * size + (cols - 1) * gap
canvas_h = margin * 2 + rows * (size + label_h) + (rows - 1) * gap
frames = []
for fi in range(frame_n):
    sheet = Image.new("RGB", (canvas_w, canvas_h), "#080e18")
    draw = ImageDraw.Draw(sheet)
    for i, (key, gif) in enumerate(zip(keys, gifs)):
        gif.seek(fi % frame_counts[i])
        tile = gif.convert("RGBA")
        tile = ImageOps.contain(tile, (size, size), method=Image.Resampling.LANCZOS)
        x = margin + (i % cols) * (size + gap)
        y = margin + (i // cols) * (size + label_h + gap)
        sheet.paste((13, 24, 34), (x, y, x + size, y + size))
        sheet.paste(tile, (x + (size - tile.width) // 2, y + (size - tile.height) // 2), tile)
        draw.rectangle((x, y, x + size - 1, y + size - 1), outline="#294556", width=1)
        draw.text((x + 4, y + size + 5), key.upper(), font=font, fill="#b5f0e8")
    frames.append(sheet)
frames[0].save(out, save_all=True, append_images=frames[1:], duration=150, loop=0, optimize=True)
print("animation preview ->", out)
