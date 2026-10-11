# Re-import each shipped GLB and render several poses: this is what checks the
# exported skin and loop, rather than only the original Blender scene.
import os, sys
HERE=os.path.dirname(os.path.abspath(__file__))
LIB=os.path.join(HERE,"..","..","schumpeter","models")
sys.path.insert(0,LIB)
os.environ.setdefault("GLB_DIR",os.path.join(HERE,"glb"))
import render
import bpy
OUT=os.path.join(HERE,"_anim")
os.makedirs(OUT,exist_ok=True)

def frames_for(key,n,px,samples,rot):
    sc=render.setup_scene(px,samples)
    root,r=render.load_model(key)
    render.camera(sc,r)
    render.add_lights(sc,0)
    render.set_rot(root,*rot)
    acts=[o.animation_data.action for o in bpy.data.objects if o.animation_data and o.animation_data.action]
    f0,f1=acts[0].frame_range if acts else (0,0)
    paths=[]
    for i in range(n):
        f=f0+(f1-f0)*i/n
        sc.frame_set(int(f),subframe=f-int(f))
        p=os.path.join(OUT,f"{key}_{i:02d}.png")
        sc.render.filepath=p
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    return paths,(f1-f0)/sc.render.fps

if __name__=="__main__":
    from PIL import Image
    n=int(os.environ.get("FRAMES","8"));px=int(os.environ.get("PX","300"));samples=int(os.environ.get("SAMPLES","8"))
    rot=tuple(float(v) for v in os.environ.get("ROT","12,-24,0").split(","))
    for key in sys.argv[1:]:
        paths,secs=frames_for(key,n,px,samples,rot)
        ims=[Image.open(p).convert("RGBA") for p in paths]
        gif=[]
        for im in ims:
            bg=Image.new("RGBA",im.size,(10,18,31,255));bg.alpha_composite(im)
            gif.append(bg.convert("RGB").convert("P",palette=Image.ADAPTIVE))
        out=os.path.join(OUT,f"{key}.gif")
        gif[0].save(out,save_all=True,append_images=gif[1:],loop=0,duration=int(secs*1000/len(gif)))
        if not os.environ.get("KEEP"):
            for p in paths: os.remove(p)
        print(f"[anim] {key}: {len(ims)} frames over {secs:.2f}s",flush=True)
