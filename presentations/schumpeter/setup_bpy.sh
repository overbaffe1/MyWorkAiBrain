#!/bin/sh
# Restores the Blender-as-a-module environment in a sandbox WITHOUT apt access.
#   1. pip-installs `bpy` (needs PyPI access)
#   2. builds tiny STUB shared libs for the 7 X11/GL libs bpy links but never
#      calls in background mode (modeling + glTF export + Cycles CPU render):
#      GHOST/X11/GLX/xkbcommon entry points only (48 functions, return NULL)
#   3. registers them with the dynamic loader (ld.so.conf.d + ldconfig)
# Idempotent. Needs sudo for step 3 (falls back to a printed LD_LIBRARY_PATH hint).
set -e
STUB_DIR=/usr/local/lib/bpy-stubs
SYMS="XCloseDevice XFixesHideCursor XFixesShowCursor XFreeDeviceList XFreeDeviceState \
XGetExtensionVersion XListInputDevices XOpenDevice XQueryDeviceState XSelectExtensionEvent \
_XiGetDevicePresenceNotifyEvent glFinish glXChooseFBConfig glXCreateContext glXCreateNewContext \
glXCreateWindow glXDestroyContext glXGetCurrentContext glXGetCurrentDisplay glXGetCurrentDrawable \
glXGetProcAddress glXGetProcAddressARB glXGetVisualFromFBConfig glXMakeContextCurrent glXMakeCurrent \
glXQueryContext glXSwapBuffers xkb_compose_state_feed xkb_compose_state_get_status \
xkb_compose_state_get_utf8 xkb_compose_state_new xkb_compose_state_reset xkb_compose_state_unref \
xkb_compose_table_new_from_locale xkb_compose_table_unref xkb_context_new xkb_context_unref \
xkb_keymap_key_repeats xkb_keymap_mod_get_index xkb_keymap_new_from_string xkb_keymap_unref \
xkb_state_get_keymap xkb_state_key_get_one_sym xkb_state_key_get_utf8 xkb_state_new \
xkb_state_serialize_mods xkb_state_unref xkb_state_update_mask"
LIBS="libXrender.so.1 libXfixes.so.3 libXi.so.6 libxkbcommon.so.0 libSM.so.6 libICE.so.6 libGL.so.1"

pip install --break-system-packages -q bpy Pillow 2>&1 | tail -1
D=$(mktemp -d)
{
  echo "/* bpy stubs: GHOST/X11/GLX/xkbcommon entry points, never called headless. */"
  # shellcheck disable=SC2086
  for s in $SYMS; do echo "void *$s(void) { return (void*)0; }"; done
} > "$D/stub.c"
for lib in $LIBS; do gcc -shared -fPIC -O1 -o "$D/$lib" "$D/stub.c" -Wl,-soname,"$lib"; done
if sudo -n true 2>/dev/null; then
  sudo -n mkdir -p "$STUB_DIR"
  sudo -n cp "$D"/lib*.so.* "$STUB_DIR"/
  echo "$STUB_DIR" | sudo -n tee /etc/ld.so.conf.d/bpy-stubs.conf >/dev/null
  sudo -n ldconfig
else
  echo "NO SUDO: copy $D/lib*.so.* somewhere and set LD_LIBRARY_PATH" >&2
  echo "STUBS_AT=$D" >&2
  exit 1
fi
rm -rf "$D"
python3 -c "import bpy; print('bpy', bpy.app.version_string)"
