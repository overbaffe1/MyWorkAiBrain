# Пример: шкатулка с открывающейся крышкой (весь конвейер за 2 команды)

```bash
bash presentations/tools/setup-env.sh                                   # один раз на песочницу (SETUP_DONE)
LD_LIBRARY_PATH=/tmp/bstub python3 train-ai/examples/box_with_lid.py    # → out/box.glb  (3 кости, цикл 4 с)
node train-ai/examples/mini_deck.js                                     # → out/box.png (растр) + out/demo.pptx
```

Проверить движение без PowerPoint (раскадровка + GIF в `presentations/cantillon/models/_anim/box.*`):

```bash
cd presentations/cantillon
GLB_DIR=$PWD/../../train-ai/examples/out LD_LIBRARY_PATH=/tmp/bstub FRAMES=8 PX=300 ROT="18,-28,0" \
  python3 models/anim_preview.py box
```

Что показывает пример:

* `box_with_lid.py` — статичный корпус (кость `root`), монета и крышка на своих костях (`rig.mark()` → построить →
  `rig.take(m, "lid", head=<петля>)`), функция `anim(t)` и экспорт `export_rigged(...)` в skinned glTF.
* `mini_deck.js` — один слайд: текст + `s.model("box", …)`; рендер растра через `render.py`; `toPptx` →
  `injectModels` (3D-модель + `embedAnim`) → `injectTiming` (появление текста + зацикленная «Сцена»).
* Урок про габариты: в первой версии шкатулка была глубокой (D = 0.6) — открытая крышка торчала вверх и **обрезалась
  кадром**. PowerPoint кадрирует по габаритам позы покоя; решение — делать модель так, чтобы движущиеся части
  оставались в пределах описанной сферы (здесь D = 0.38). Раскадровка `anim_preview.py` кадрирует так же, как
  PowerPoint, поэтому такие ошибки видны сразу.

`out/` в git не попадает — всё пересобирается командами выше.
