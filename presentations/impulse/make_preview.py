#!/usr/bin/env python3
"""Build a labeled contact sheet from the 10 slide PNG previews."""
import glob, os, sys
from PIL import Image, ImageDraw, ImageFont

if len(sys.argv) != 3:
    raise SystemExit("usage: make_preview.py 'preview/slide-*.png' output.jpg")
paths = sorted(glob.glob(sys.argv[1]))
if not paths:
    raise SystemExit("No slide preview PNGs found")
thumb_w = 640
margin, gap, label_h = 28, 18, 34
thumbs=[]
for p in paths:
    im=Image.open(p).convert("RGB")
    h=round(im.height*thumb_w/im.width)
    thumbs.append((os.path.basename(p),im.resize((thumb_w,h),Image.Resampling.LANCZOS)))
cols=2
rows=(len(thumbs)+cols-1)//cols
cell_h=thumbs[0][1].height+label_h
W=margin*2+cols*thumb_w+(cols-1)*gap
H=margin*2+rows*cell_h+(rows-1)*gap
sheet=Image.new("RGB",(W,H),(10,18,31))
d=ImageDraw.Draw(sheet)
try: font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",18)
except OSError: font=ImageFont.load_default()
for i,(name,im) in enumerate(thumbs):
    x=margin+(i%cols)*(thumb_w+gap)
    y=margin+(i//cols)*(cell_h+gap)
    sheet.paste(im,(x,y))
    d.text((x,y+im.height+8),f"СЛАЙД {i+1:02d}  ·  {name}",fill=(142,185,244),font=font)
out=sys.argv[2]
os.makedirs(os.path.dirname(os.path.abspath(out)),exist_ok=True)
sheet.save(out,"JPEG",quality=91,optimize=True)
print("contact sheet ->",out, f"({len(thumbs)} slides)")
