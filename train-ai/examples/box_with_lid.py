# Minimal end-to-end example: a jewellery box whose lid opens, a coin pops out and the lid closes again.
# Shows the whole recipe: procedural parts -> bones (rig.take) -> anim(t) -> skinned .glb that PowerPoint plays.
#
#   bash presentations/tools/setup-env.sh                      # once per sandbox
#   LD_LIBRARY_PATH=/tmp/bstub python3 train-ai/examples/box_with_lid.py
#   -> train-ai/examples/out/box.glb
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..", "presentations")
sys.path.insert(0, os.path.join(ROOT, "cantillon", "models"))   # rig.py
sys.path.insert(0, os.path.join(ROOT, "schumpeter", "models"))  # make_models.py: helpers + material palette
import make_models as mm  # noqa: E402
from make_models import box, lathe, coin, sphere  # noqa: E402
from rig import Rig, export_rigged, ease, back_out, hop, clamp01, smooth  # noqa: E402

mm.OUT = os.path.join(HERE, "out")
os.makedirs(mm.OUT, exist_ok=True)


def m_box():
    rig = Rig()                                   # bone "root" = everything that does not move
    # NB: PowerPoint frames the model by its REST-pose bounds (+ the margin of the bounding sphere).
    # An opened lid sticks up by ~D, so the box is kept shallow (D=0.38): with D=0.6 the open lid was cut off.
    W, D, H, th = 0.9, 0.38, 0.32, 0.035
    # 1) static body: open-topped box built from walls, so the inside is visible when the lid opens
    box("floor", (W, D, th), (0, 0, th / 2), "walnut", 0.006)
    for y in (-1, 1):
        box("wallY", (W, th, H), (0, y * (D / 2 - th / 2), H / 2), "walnut", 0.006)
    for x in (-1, 1):
        box("wallX", (th, D, H), (x * (W / 2 - th / 2), 0, H / 2), "walnut", 0.006)
    box("velvet", (W - 2 * th, D - 2 * th, 0.01), (0, 0, th + 0.005), "wine", 0.0)
    for x in (-1, 1):
        sphere("foot", 0.04, (x * 0.36, -0.13, 0.0), "brass", 16, 8)
        sphere("foot", 0.04, (x * 0.36, 0.13, 0.0), "brass", 16, 8)
    box("lock", (0.10, 0.012, 0.08), (0, -D / 2 - 0.006, H - 0.05), "gold", 0.004)

    # 2) the coin inside -> its own bone, pivot at its centre
    m = rig.mark()
    coin("coin", (0, 0, th + 0.03), (0, 0, 0), r=0.085, t=0.03)
    rig.take(m, "coin", head=(0, 0, th + 0.03))

    # 3) the lid -> bone on the hinge line (back top edge); everything created after mark() follows it
    m = rig.mark()
    box("lid", (W + 0.02, D + 0.02, 0.06), (0, 0, H + 0.03), "walnut", 0.012)
    box("lidtop", (W - 0.12, D - 0.12, 0.012), (0, 0, H + 0.066), "leather", 0.004)
    box("lidlining", (W - 2 * th, D - 2 * th, 0.006), (0, 0, H - 0.001), "wine", 0.0)
    lathe("knob", [(0, 0), (0.03, 0), (0.035, 0.02), (0.02, 0.035), (0, 0.04)], "gold", 32, loc=(0, -0.05, H + 0.07))
    rig.take(m, "lid", head=(0, D / 2, H))

    rig.shift(dz=-0.2)                            # centre the model; bone pivots move with it

    def anim(t):
        # 0.05-0.30 lid opens with a little overshoot, 0.30-0.65 coin jumps & flips, 0.75-0.92 lid closes
        lid = -105 * back_out((t - 0.05) / 0.25, 1.3) * (1 - ease(t, 0.75, 0.92)) if t > 0.05 else 0.0
        q = clamp01((t - 0.32) / 0.30)
        return {
            "lid": {"rot": [((1, 0, 0), lid)]},                      # negative angle about +X lifts the front edge
            "coin": {"loc": (0, 0, 0.30 * hop(q)), "rot": [((1, 0, 0), 360 * smooth(q))]},
        }
    return rig, anim, 4.0                          # loop length in seconds (t=0 and t=1 give the same pose)


if __name__ == "__main__":
    mm.reset()
    mm._mats.clear()
    export_rigged("box", *m_box())
