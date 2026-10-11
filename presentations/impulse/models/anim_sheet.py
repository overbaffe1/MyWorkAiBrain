# Combine frames kept by anim_preview.py into one looping GIF contact sheet.
import os,sys,glob
from PIL import Image,ImageDraw,ImageFont
HERE=os.path.dirname(os.path.abspath(__file__))
if len(sys.argv)<3:raise SystemExit("usage: anim_sheet.py out.gif model1 model2 ...")
out,keys=sys.argv[1],sys.argv[2:]
labels=dict(x.split("=",1) for x in os.environ.get("LABELS","").split(";") if "=" in x)
frames={k:sorted(glob.glob(os.path.join(HERE,"_anim",f"{k}_[0-9][0-9].png"))) for k in keys}
missing=[k for k,v in frames.items() if not v]
if missing:raise SystemExit("missing kept frames for: "+", ".join(missing)+"; run anim_preview.py with KEEP=1")
n=min(len(v) for v in frames.values());px=Image.open(frames[keys[0]][0]).width
cols=3;rows=(len(keys)+cols-1)//cols;label_h=24;bg=(10,18,31)
try:font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",14)
except OSError:font=ImageFont.load_default()
gif=[]
for f in range(n):
    sheet=Image.new("RGBA",(cols*px,rows*(px+label_h)),bg+(255,));d=ImageDraw.Draw(sheet)
    for i,k in enumerate(keys):
        im=Image.open(frames[k][f]).convert("RGBA")
        x,y=(i%cols)*px,(i//cols)*(px+label_h)
        sheet.alpha_composite(im,(x,y))
        text=labels.get(k,k);w=d.textlength(text,font=font)
        d.text((x+(px-w)/2,y+px+3),text,fill=(234,191,114),font=font)
    gif.append(sheet.convert("RGB").convert("P",palette=Image.ADAPTIVE,colors=200))
os.makedirs(os.path.dirname(os.path.abspath(out)),exist_ok=True)
gif[0].save(out,save_all=True,append_images=gif[1:],loop=0,duration=int(os.environ.get("MS","250")),optimize=True)
print("wrote",out,os.path.getsize(out)//1024,"KB",n,"frames")
