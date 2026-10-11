import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps

src, out = sys.argv[1:3]
files = [os.path.join(src, f"slide-{i:02d}.png") for i in range(1, 11)]
thumb_w, thumb_h, gap = 384, 216, 18
margin, label_h = 22, 28
cols, rows = 5, 2
sheet = Image.new("RGB", (margin * 2 + cols * thumb_w + (cols - 1) * gap,
                           margin * 2 + rows * (thumb_h + label_h) + (rows - 1) * gap), "#080e18")
draw = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
except OSError:
    font = ImageFont.load_default()
for i, path in enumerate(files):
    if not os.path.exists(path):
        continue
    im = Image.open(path).convert("RGB")
    im = ImageOps.fit(im, (thumb_w, thumb_h), method=Image.Resampling.LANCZOS)
    x = margin + (i % cols) * (thumb_w + gap)
    y = margin + (i // cols) * (thumb_h + label_h + gap)
    sheet.paste(im, (x, y))
    draw.rectangle((x, y, x + thumb_w - 1, y + thumb_h - 1), outline="#3b5568", width=1)
    draw.text((x, y + thumb_h + 5), f"СЛАЙД {i + 1:02d}", font=font, fill="#afc1cf")
sheet.save(out, quality=91, optimize=True)
print("contact sheet ->", out)
