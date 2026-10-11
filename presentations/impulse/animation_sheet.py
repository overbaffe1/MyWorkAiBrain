"""Combine all eight animated 3D QA previews into one meme-deck GIF."""
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps

src, out = sys.argv[1:3]
keys = ["chestnut", "phone", "brain", "paylater", "clipboard", "timer", "bag", "scales"]
size, label_h, gap, margin = 224, 28, 12, 14
cols, rows = 4, 2
files = [os.path.join(src, key + ".gif") for key in keys]
for p in files:
    if not os.path.isfile(p):
        raise FileNotFoundError(p)

gifs = [Image.open(p) for p in files]
frame_counts = [getattr(im, "n_frames", 1) for im in gifs]
frame_n = max(frame_counts)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
except OSError:
    font = ImageFont.load_default()
canvas_w = margin * 2 + cols * size + (cols - 1) * gap
canvas_h = margin * 2 + rows * (size + label_h) + (rows - 1) * gap
frames = []
for fi in range(frame_n):
    sheet = Image.new("RGB", (canvas_w, canvas_h), "#faf7ec")
    draw = ImageDraw.Draw(sheet)
    for i, (key, gif) in enumerate(zip(keys, gifs)):
        gif.seek(fi % frame_counts[i])
        tile = gif.convert("RGBA")
        tile = ImageOps.contain(tile, (size, size), method=Image.Resampling.LANCZOS)
        x = margin + (i % cols) * (size + gap)
        y = margin + (i // cols) * (size + label_h + gap)
        sheet.paste((255, 254, 248), (x, y, x + size, y + size))
        sheet.paste(tile, (x + (size - tile.width) // 2, y + (size - tile.height) // 2), tile)
        draw.rectangle((x, y, x + size - 1, y + size - 1), outline="#17181c", width=2)
        draw.text((x + 5, y + size + 4), key.upper(), font=font, fill="#17181c")
    frames.append(sheet)
frames[0].save(out, save_all=True, append_images=frames[1:], duration=150, loop=0, optimize=True)
print("animation preview ->", out)
