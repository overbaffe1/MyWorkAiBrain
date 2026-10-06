# Combines kept anim_preview frames (KEEP=1) of several models into one looping GIF grid.
#   python3 models/anim_sheet.py out.gif ship harp chest ...   (frames: models/_anim/<key>_NN.png)
import os, sys, glob
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
out, keys = sys.argv[1], sys.argv[2:]
labels = dict(x.split("=", 1) for x in os.environ.get("LABELS", "").split(";") if "=" in x)
frames = {k: sorted(glob.glob(os.path.join(HERE, "_anim", f"{k}_[0-9][0-9].png"))) for k in keys}
n = min(len(v) for v in frames.values())
px = Image.open(frames[keys[0]][0]).width
cols = 5
rows = (len(keys) + cols - 1) // cols
BG = (22, 12, 16)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
except OSError:
    font = ImageFont.load_default()
gif = []
for f in range(n):
    sheet = Image.new("RGBA", (cols * px, rows * (px + 24)), BG + (255,))
    d = ImageDraw.Draw(sheet)
    for i, k in enumerate(keys):
        im = Image.open(frames[k][f]).convert("RGBA")
        x, y = (i % cols) * px, (i // cols) * (px + 24)
        sheet.alpha_composite(im, (x, y))
        t = labels.get(k, k)
        w = d.textlength(t, font=font)
        d.text((x + (px - w) / 2, y + px), t, fill=(227, 182, 99), font=font)
    gif.append(sheet.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=200))
gif[0].save(out, save_all=True, append_images=gif[1:], loop=0, duration=int(os.environ.get("MS", "250")), optimize=True)
print("wrote", out, os.path.getsize(out) // 1024, "KB,", n, "frames")
