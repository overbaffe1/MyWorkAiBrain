# 3D-презентация: Ричард Кантильон (v3, 10 слайдов, анимированные экспонаты)

Использует тот же движок, что и `../schumpeter`: `lib.js`, `pptx3d.js`, `models/render.py`, а также `node_modules` из `../schumpeter`.
Окружение целиком (bpy, python-pptx, npm, заглушки X/GL для headless Blender) поднимает `../tools/setup-env.sh`.

```bash
bash ../tools/setup-env.sh                                 # один раз
LD_LIBRARY_PATH=/tmp/bstub python3 models/make_models.py   # .glb → models/glb
python3 stage.py                                           # фон и свечение → assets/
node build.js --preview                                    # → ../../exports/cantillon-3d-presentation.pptx
```

## Анимация внутри моделей

PowerPoint воспроизводит в 3D-моделях только **скелетную** (skinned) glTF-анимацию, поэтому каждая подвижная часть
экспоната привязана к своей кости (`models/rig.py`): крышка сундука, ключ, струны арфы, страницы книги, коромысло весов,
стрелка компаса, пламя свечи, волны под кораблём и т. д. Движение задаётся функцией от времени `t ∈ [0, 1]` и запекается
в ключи; `t = 0` и `t = 1` совпадают, так что цикл бесшовный.

`pptx3d.js` сам находит анимацию в .glb, прописывает `a3danim:embedAnim` и добавляет на слайд эффект «Сцена»
(presetID 100, повтор до конца слайда) — в PowerPoint 365 экспонат начинает двигаться сам при показе слайда.

Проверка без PowerPoint: `LD_LIBRARY_PATH=/tmp/bstub python3 models/anim_preview.py chest` — рендерит раскадровку
и GIF из экспортированного .glb в `models/_anim/`.

Чтобы собрать быстрый черновик с растрами в низком разрешении, используйте `FAST=1`.
