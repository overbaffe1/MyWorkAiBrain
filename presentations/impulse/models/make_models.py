# Procedural 3D exhibits for the impulse-spending deck.
# Blender Z is up; exhibits face the viewer at -Y. Every export is a compact,
# skinned GLB so PowerPoint 365/2021 can play its single looping animation.
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "schumpeter", "models"))
import make_models as mm
from make_models import bpy, Vector, M, box, cyl, sphere, torus, tube, lathe, mesh_obj, finish
sys.path.insert(0, os.path.join(HERE, "..", "..", "cantillon", "models"))
from rig import Rig, export_rigged, wave, smooth, ease

mm.OUT = os.path.join(HERE, "glb")
os.makedirs(mm.OUT, exist_ok=True)
TAU = math.tau


def loop_points(x, y, z, w, d):
    return [(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),(x+w/2,y+d/2,z),
            (x-w/2,y+d/2,z),(x-w/2,y-d/2,z)]


def m_cart():
    """Shopping cart + parcel + a pulsing notification: checkout in two taps."""
    mm.reset(); mm._mats.clear(); rig = Rig()
    # trolley base and four wheels
    box("chassis", (0.93,0.12,0.07), (0.08,0.0,0.32), "iron", .035)
    for x in (-.39,.49):
        for y in (-.25,.25):
            torus("wheel", .105,.035,(x,y,.17),"rubber",rot=(math.pi/2,0,0),seg=28,mseg=8)
            cyl("axle",.035,.12,(x,y,.17),"brass",rot=(0,math.pi/2,0),seg=16)
    # basket rails
    for z in (.70,1.26):
        tube("basket_rim",loop_points(0,0,z,.94,.60),.021,"brass",3,False)
    for x in (-.45,.45):
        for y in (-.28,.28):
            tube("basket_upright",[(x,y,.70),(x,y,1.26)],.018,"satin_steel",2,False)
    for z in (.82,.96,1.10):
        tube("basket_wire_front",[(-.43,-.29,z),(.43,-.29,z)],.011,"satin_steel",2,False)
        tube("basket_wire_back",[(-.43,.29,z),(.43,.29,z)],.011,"satin_steel",2,False)
        for x in (-.45,.45):
            tube("basket_wire_side",[(x,-.27,z),(x,.27,z)],.011,"satin_steel",2,False)
    # handle, neck and a parcel with a ribbon
    tube("handle",[(-.39,0,.36),(-.63,0,.58),(-.70,0,1.42),(-1.04,0,1.42)],.035,"iron",4,True)
    tube("grip",[(-1.05,0,1.42),(-.78,0,1.42)],.058,"leather",4,False)
    box("parcel",(.43,.38,.40),(.05,-.015,1.02),"oxblood",.035)
    box("parcel_ribbon_x",(.075,.40,.405),(.05,-.015,1.02),"gold",.012)
    box("parcel_ribbon_z",(.44,.405,.075),(.05,-.015,1.02),"gold",.012)
    # a glossy phone face tucked into the basket
    box("phone",(.30,.085,.52),(.31,-.12,1.30),"navy",.045,rot=(0,math.radians(-10),0))
    box("phone_screen",(.255,.018,.42),(.31,-.17,1.30),"teal",.025,rot=(0,math.radians(-10),0))
    m=rig.mark()
    sphere("notification",.14,(.48,-.22,1.51),"red",24,14)
    sphere("notification_glint",.036,(.45,-.33,1.54),"ivory",14,8)
    rig.take(m,"ping",head=(.48,-.22,1.51))
    rig.shift(dz=-.78)
    def anim(t):
        return {"ping":{"scale":1.0 + .34*(.5+.5*math.sin(TAU*t)),
                        "loc":(0,0,.075*math.sin(TAU*t))}}
    return rig,anim,4.0


def m_wallet():
    """Wallet, budget card and one coin that lifts then settles back."""
    mm.reset(); mm._mats.clear(); rig = Rig()
    box("wallet_body",(1.18,.24,.64),(0,.015,.43),"leather",.09)
    box("wallet_front",(1.11,.055,.48),(0,-.14,.41),"wine",.055)
    box("wallet_seam",(1.00,.022,.025),(0,-.178,.27),"gold",.009)
    box("clasp",(.19,.075,.16),(.42,-.19,.42),"brass",.025)
    box("clasp_inset",(.08,.02,.07),(.42,-.235,.42),"navy",.012)
    # paper notes in the open edge
    for i in range(3):
        box("budget_note",(.70,.025,.34),(-.12+i*.035,.02,.77+i*.014),"teal" if i==0 else "ivory",.02)
        box("note_band",(.045,.012,.31),(.12+i*.035,-.001,.77+i*.014),"gold",.008)
    # three instalment markers
    for i,x in enumerate((-.40,0,.40)):
        cyl("installment",.105,.035,(x,-.18,.78),"brass" if i<2 else "gold",rot=(math.pi/2,0,0),seg=32,bevel=.006)
        torus("coin_rim",.087,.009,(x,-.204,.78),"gold_satin",rot=(math.pi/2,0,0),seg=32,mseg=6)
    m=rig.mark()
    cyl("active_coin",.145,.045,(.48,-.23,.82),"gold",rot=(math.pi/2,0,0),seg=40,bevel=.008)
    torus("active_coin_rim",.127,.012,(.48,-.255,.82),"ivory",rot=(math.pi/2,0,0),seg=36,mseg=8)
    sphere("coin_mark",.024,(.48,-.282,.82),"ivory",12,8)
    rig.take(m,"coin",head=(.48,-.23,.82))
    rig.shift(dz=-.66)
    def anim(t):
        # The coin rises and drops in a short, smooth loop; every endpoint matches.
        z=.22*(.5-.5*math.cos(TAU*t))
        return {"coin":{"loc":(0,0,z),"rot":[((0,1,0),360*t)]}}
    return rig,anim,4.2


def m_cycle():
    """A gift inside a circular four-stage loop; the outer path turns continuously."""
    mm.reset(); mm._mats.clear(); rig = Rig()
    # stationary parcel at the centre
    box("gift",(.53,.42,.52),(0,0,.83),"teal",.045)
    box("gift_band_x",(.09,.45,.54),(0,-.01,.83),"gold",.01)
    box("gift_band_z",(.55,.44,.08),(0,-.01,.83),"oxblood",.01)
    sphere("gift_seal",.10,(0,-.245,.83),"ivory",20,12)
    # The vertical ring and its four signal tokens share a pivot.
    m=rig.mark()
    torus("decision_loop",.69,.025,(0,0,.86),"satin_steel",rot=(math.pi/2,0,0),seg=64,mseg=8)
    positions=[(0,-.015,1.55),(.69,-.015,.86),(0,-.015,.17),(-.69,-.015,.86)]
    colors=["gold","red","teal","brass"]
    for i,(p,c) in enumerate(zip(positions,colors)):
        sphere("loop_node",.115,p,c,20,12)
        sphere("loop_core",.045,(p[0],p[1]-.087,p[2]),"ivory",12,8)
    # four small blocks give the orbit visual rhythm
    for i in range(4):
        a=TAU*(i+.5)/4
        box("loop_tick",(.09,.07,.09),(.69*math.cos(a),-.02,.86+.69*math.sin(a)),"gold",.014)
    rig.take(m,"orbit",head=(0,0,.86))
    rig.shift(dz=-.82)
    def anim(t):
        return {"orbit":{"rot":[((0,1,0),360*t)]}}
    return rig,anim,5.0


def m_triggers():
    """Phone with FOMO, social-proof and urgency cues pulsing around it."""
    mm.reset(); mm._mats.clear(); rig = Rig()
    box("phone_body",(.78,.13,1.38),(0,0,.88),"satin",.095)
    box("phone_screen",(.67,.025,1.20),(0,-.083,.88),"navy",.065)
    box("screen_header",(.52,.018,.11),(0,-.105,1.37),"teal",.018)
    box("product_photo",(.47,.022,.48),(0,-.11,.98),"wine",.025)
    box("product_gloss",(.31,.014,.045),(0,-.127,1.14),"gold",.01)
    box("buy_button",(.47,.026,.12),(0,-.12,.64),"red",.045)
    cyl("speaker",.085,.022,(0,-.099,1.49),"iron",rot=(math.pi/2,0,0),seg=20)
    sphere("home",.03,(0,-.105,.25),"brass",12,8)
    # three prominent floating cues. Each has a separate bone, timed in sequence.
    m=rig.mark()
    torus("fomo_ring",.20,.035,(-.72,-.13,1.35),"red",rot=(math.pi/2,0,0),seg=40,mseg=8)
    sphere("fomo_dot",.075,(-.72,-.17,1.35),"gold",18,10)
    rig.take(m,"fomo",head=(-.72,-.13,1.35))
    m=rig.mark()
    torus("social_ring",.18,.034,(.74,-.13,1.04),"teal",rot=(math.pi/2,0,0),seg=36,mseg=8)
    sphere("social_dot",.075,(.74,-.17,1.04),"ivory",18,10)
    rig.take(m,"social",head=(.74,-.13,1.04))
    m=rig.mark()
    torus("clock_ring",.17,.032,(-.67,-.13,.55),"gold",rot=(math.pi/2,0,0),seg=36,mseg=8)
    tube("clock_hand",[(-.67,-.17,.55),(-.67,-.17,.65)],.014,"ivory",2,False)
    tube("clock_hand",[(-.67,-.17,.55),(-.58,-.17,.50)],.014,"ivory",2,False)
    rig.take(m,"urgency",head=(-.67,-.13,.55))
    rig.shift(dz=-.85)
    def anim(t):
        def pulse(ph): return 1.0 + .36*max(0,math.sin(TAU*t+ph))
        return {"fomo":{"scale":pulse(0)},"social":{"scale":pulse(-2.1)},"urgency":{"scale":pulse(-4.2)}}
    return rig,anim,4.0


def m_scale():
    """A balance beam compares a pause/plan with the shopping urge."""
    mm.reset(); mm._mats.clear(); rig=Rig()
    cyl("base",.39,.10,(0,0,.10),"iron",seg=48,bevel=.02)
    lathe("pedestal",[(0,.12),(.20,.12),(.20,.18),(.12,.22),(.10,.80),(.20,.86),(.20,.90),(0,.90)],"brass",56,30)
    sphere("pivot",.13,(0,0,1.07),"gold",24,14)
    m=rig.mark()
    box("beam",(1.45,.105,.10),(0,0,1.10),"satin_steel",.035)
    sphere("beam_cap",.105,(-.71,0,1.10),"teal",18,10)
    sphere("beam_cap",.105,(.71,0,1.10),"red",18,10)
    rig.take(m,"beam",head=(0,0,1.10))
    # Left and right hanging pans, with a coin and a soft red cue.
    for side,bn,color in [(-1,"panL","teal"),(1,"panR","red")]:
        x=side*.58
        m=rig.mark()
        for dx in (-.16,.16):
            tube("pan_chain",[(x+dx,0,1.05),(x+dx,0,.73)],.012,"brass",2,False)
        torus("pan_rim",.24,.025,(x,0,.69),"brass",seg=40,mseg=8)
        cyl("pan_bowl",.19,.045,(x,0,.66),color,seg=36,bevel=.014)
        if side < 0:
            cyl("budget_coin",.095,.035,(x,-.20,.73),"gold",rot=(math.pi/2,0,0),seg=28)
        else:
            sphere("urge",.095,(x,-.20,.73),"ivory",18,10)
        rig.take(m,bn,head=(x,0,.74),parent="beam")
    rig.shift(dz=-.65)
    def anim(t):
        a=14.0*math.sin(TAU*t)
        return {"beam":{"rot":[((0,1,0),a)]},
                "panL":{"rot":[((0,1,0),-.90*a)]},
                "panR":{"rot":[((0,1,0),-.90*a)]}}
    return rig,anim,4.0


def m_clipboard():
    """An anonymous survey sheet and a pencil that marks an answer."""
    mm.reset(); mm._mats.clear(); rig=Rig()
    box("clipboard_board",(1.10,.14,1.62),(0,0,.92),"walnut",.075)
    box("paper",(.91,.026,1.40),(0,-.088,.91),"ivory",.022)
    box("clip",(.32,.07,.12),(0,-.13,1.65),"brass",.025)
    # printed rows / question blocks
    for z,w in [(1.42,.59),(1.28,.73),(1.14,.66),(.87,.60),(.73,.72),(.59,.52)]:
        box("question_line",(w,.014,.025),(.055,-.112,z),"navy",.006)
    for i,z in enumerate((1.28,.87,.59)):
        box("checkbox",(.095,.018,.095),(-.34,-.116,z),"teal" if i<2 else "gold",.012)
        if i<2:
            tube("checkmark",[(-.37,-.132,z),(-.34,-.14,z-.03),(-.29,-.14,z+.04)],.012,"ivory",2,False)
    m=rig.mark()
    tube("pencil",[(.47,-.20,.50),(.53,-.20,.66),(.79,-.20,1.40)],.032,"gold",3,False)
    sphere("pencil_tip",.045,(.47,-.20,.50),"red",14,8)
    rig.take(m,"pencil",head=(.48,-.20,.52))
    rig.shift(dz=-.92)
    def anim(t):
        return {"pencil":{"loc":(-.20*math.sin(TAU*t),0,.09*math.sin(TAU*t)),
                           "rot":[((0,1,0),12.0*math.sin(TAU*t))]}}
    return rig,anim,4.2


def m_chart():
    """Three survey measures and a gently moving magnifier; bars pulse as a draft chart."""
    mm.reset(); mm._mats.clear(); rig=Rig()
    box("chart_base",(1.50,.18,.12),(0,0,.12),"iron",.035)
    box("axis_y",(.055,.08,1.38),(-.61,-.02,.79),"satin_steel",.015)
    box("axis_x",(1.35,.08,.055),(0,-.02,.20),"satin_steel",.015)
    heights=(.60,.91,1.18)
    colors=("teal","gold","red")
    for i,(h,c) in enumerate(zip(heights,colors)):
        x=-.34+i*.43
        m=rig.mark()
        box("bar",(.25,.12,h),(x,-.04,.22+h/2),c,.025)
        rig.take(m,f"bar{i}",head=(x,-.04,.22))
        # tiny round data point, separate from bars for visual detail
        sphere("data_point",.045,(x,-.12,.22+h),"ivory",14,8)
    m=rig.mark()
    torus("magnifier",.22,.035,(.47,-.20,1.31),"brass",rot=(math.pi/2,0,0),seg=40,mseg=8)
    sphere("lens",.095,(.47,-.20,1.31),"teal",20,10)
    tube("magnifier_handle",[(.59,-.20,1.18),(.76,-.20,.94)],.045,"brass",3,False)
    rig.take(m,"lens",head=(.47,-.20,1.31))
    rig.shift(dz=-.80)
    def anim(t):
        return {"bar0":{"scale":(1,1,1.0+.18*math.sin(TAU*t))},
                "bar1":{"scale":(1,1,1.0+.15*math.sin(TAU*t+1.8))},
                "bar2":{"scale":(1,1,1.0+.12*math.sin(TAU*t+3.2))},
                "lens":{"rot":[((0,1,0),16.0*math.sin(TAU*t))]}}
    return rig,anim,4.0


def m_hourglass():
    """A quiet hourglass: pause before pressing the checkout button."""
    mm.reset(); mm._mats.clear(); rig=Rig()
    # A simple brass frame keeps the glass readable against a dark background.
    cyl("base",.48,.12,(0,0,.12),"brass",seg=48,bevel=.025)
    cyl("top",.48,.12,(0,0,1.64),"brass",seg=48,bevel=.025)
    for x in (-.34,.34):
        for y in (-.22,.22):
            tube("support",[(x,y,.19),(x*.78,y*.78,.54),(x*.22,y*.22,.88),(x*.78,y*.78,1.22),(x,y,1.58)],.027,"satin_steel",3,True)
    torus("top_rim",.38,.035,(0,0,1.36),"teal",seg=48,mseg=8)
    torus("middle_rim",.16,.027,(0,0,.87),"teal",seg=40,mseg=8)
    torus("bottom_rim",.38,.035,(0,0,.37),"teal",seg=48,mseg=8)
    # sand piles / small grain stream
    lathe("upper_sand",[(0,1.30),(.32,1.30),(.25,1.22),(.16,1.16),(.08,1.09),(0,1.06)],"gold",40,20)
    lathe("lower_sand",[(0,.43),(.08,.43),(.19,.48),(.29,.55),(.35,.60),(0,.61)],"gold",40,20)
    m=rig.mark()
    sphere("falling_grain",.11,(0,-.02,1.00),"ivory",16,10)
    rig.take(m,"grain",head=(0,-.02,1.00))
    rig.shift(dz=-.86)
    def anim(t):
        q=(t+.22)%1.0
        # The grain disappears at the reset point, so the loop remains visually seamless.
        sc=max(.025,math.sin(math.pi*q))
        z=-.90*q
        return {"grain":{"loc":(0,0,z),"scale":sc}}
    return rig,anim,4.0


def m_compass():
    """A small compass whose needle keeps gently finding its direction."""
    mm.reset(); mm._mats.clear(); rig=Rig()
    lathe("case",[(0,0),(.57,0),(.64,.035),(.68,.10),(.64,.17),(.56,.20),(0,.20)],"iron",64,32,loc=(0,0,.32))
    lathe("dial",[(0,.51),(.55,.51),(.58,.53),(.55,.56),(0,.56)],"ivory",64,25)
    torus("bezel",.60,.035,(0,0,.53),"brass",seg=64,mseg=10)
    for k in range(16):
        a=TAU*k/16
        r=.47
        tick=box("tick",(.025,.10 if k%4==0 else .065,.025),(r*math.cos(a),r*math.sin(a),.58),"navy",.004)
        tick.rotation_euler[2]=a-math.pi/2
    # needle in the horizontal dial plane; the full model is tilted toward the viewer below.
    m=rig.mark()
    verts=[(-.055,-.02,.60),(.0,.43,.60),(.055,-.02,.60),(0,-.29,.60),(0,0,.64)]
    faces=[(0,1,4),(1,2,4),(2,3,4),(3,0,4)]
    obj=mesh_obj("needle",verts,faces)
    finish(obj,"red",20)
    sphere("needle_hub",.075,(0,0,.64),"gold",18,10)
    rig.take(m,"needle",head=(0,0,.60))
    # An angled dial reads correctly from PowerPoint's front-facing 3D camera.
    rig.rotate(rx=48)
    rig.shift(dz=-.42)
    def anim(t):
        return {"needle":{"rot":[((0,0,1),22.0*math.sin(TAU*t))]}}
    return rig,anim,4.0


MODELS={
    "cart":m_cart,"wallet":m_wallet,"cycle":m_cycle,"triggers":m_triggers,
    "scale":m_scale,"clipboard":m_clipboard,"chart":m_chart,
    "hourglass":m_hourglass,"compass":m_compass,
}

if __name__=="__main__":
    wanted=sys.argv[1:] or list(MODELS)
    bad=[k for k in wanted if k not in MODELS]
    if bad:
        raise SystemExit("Unknown models: "+", ".join(bad))
    for key in wanted:
        print("building",key,flush=True)
        result=MODELS[key]()
        export_rigged(key,*result)
