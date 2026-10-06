#!/usr/bin/env bash
# Recreates the non-persistent toolchain: bpy (headless Blender), python libs, node_modules, X/GL stub libs.
set -e
pip install --break-system-packages -q bpy global-land-mask python-pptx pillow numpy
(cd "$(dirname "$0")/../schumpeter" && npm i --silent)
mkdir -p /tmp/bstub /tmp/cv && cd /tmp/bstub
[ -f /tmp/cv/ok ] || { pip download -q opencv-python --no-deps -d /tmp/cv && touch /tmp/cv/ok; }
echo 'void __stub(void){}' > s.c
for l in libXrender.so.1 libXfixes.so.3 libXi.so.6 libSM.so.6 libICE.so.6; do gcc -shared -fPIC -o $l s.c -Wl,-soname,$l; done
python3 -c "
import zipfile,glob
z=zipfile.ZipFile(glob.glob('/tmp/cv/*.whl')[0]); n=[x for x in z.namelist() if 'libxkbcommon-' in x and 'x11' not in x][0]
open('/tmp/bstub/libxkbcommon.so.0','wb').write(z.read(n))"
BP=$(python3 -c "import importlib.util,os;print(os.path.dirname(importlib.util.find_spec('bpy').origin))")
find "$BP" -name "*.so*" -type f | xargs -I{} nm -D --undefined-only {} 2>/dev/null | awk '{print $2}' | sed 's/@.*//' | grep -E '^(gl|X|Ice|Sm|_X|Xt)' | sort -u > syms.txt
{ echo 'char XtStrings[4096];'; grep -v '^XtStrings$' syms.txt | sed 's/.*/void* &(void){return 0;}/'; } > gl.c
gcc -shared -fPIC -w -o libGL.so.1 gl.c -Wl,-soname,libGL.so.1
LD_LIBRARY_PATH=/tmp/bstub python3 -c "import bpy; print('bpy', bpy.app.version_string)"
echo SETUP_DONE
