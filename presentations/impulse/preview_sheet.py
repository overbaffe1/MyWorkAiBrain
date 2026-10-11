"""Compose the ten rendered slides into a labelled 2 x 5 contact sheet."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREVIEW = HERE / "preview"
OUT = ROOT / "exports" / "impulse-spending-preview.jpg"
OUT.parent.mkdir(parents=True, exist_ok=True)

thumb_w, thumb_h = 760, 428
pad, gap, header, label_h = 34, 26, 80, 34
cols, rows = 2, 5
canvas = Image.new("RGB", (pad * 2 + cols * thumb_w + gap, pad * 2 + header + rows * (thumb_h + label_h + gap)), "#f2ede3")
draw = ImageDraw.Draw(canvas)
try:
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
except OSError:
    title_font = label_font = ImageFont.load_default()
draw.text((pad, 20), "ПОКУПКА НА АВТОПИЛОТЕ  ·  10 СЛАЙДОВ", font=title_font, fill="#202a35")
for i in range(1, 11):
    p = PREVIEW / f"slide-{i:02d}.png"
    im = Image.open(p).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
    x = pad + (i - 1) % cols * (thumb_w + gap)
    y = pad + header + (i - 1) // cols * (thumb_h + label_h + gap)
    canvas.paste(im, (x, y))
    draw.rectangle((x, y, x + thumb_w, y + thumb_h), outline="#d5c9b6", width=2)
    draw.text((x + 3, y + thumb_h + 5), f"СЛАЙД {i:02d}", font=label_font, fill="#a63c34")
canvas.save(OUT, quality=89, optimize=True)
print("contact sheet ->", OUT)
