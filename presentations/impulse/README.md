# «Каштан в корзине» — 3D-презентация об импульсивных тратах

Переработка `ekonomika123.pptx` в 9-слайдовую редактируемую PowerPoint-презентацию. Сохраняются тема исходника, исследовательская логика, самоирония и отдельные мемы; оригинальное фото каштанов оставлено, а каштан дополнительно стал процедурной 3D-моделью-маскотом.

## Что внутри

- Настоящие модели PowerPoint 3D (`am3d:model3d`, glTF `.glb` внутри `.pptx`), а не только 3D-картинки.
- Бесшовные анимации на костях: каштан машет, телефон мигает уведомлением, товары подпрыгивают в корзине, кошелёк шевелит картой и монетой.
- Переходы Morph между слайдами; обычная картинка остаётся fallback для просмотрщиков без поддержки 3D.
- Текст выступления — в заметках докладчика и в `exports/impulse-spending-presentation-script.md`.
- Полные источники, границы данных и формулировок — `exports/impulse-spending-sources.md`.
- Мемы и фото каштанов взяты из исходной презентации; данные исследования не придуманы — опрос обозначен как план.

## Сборка

Один раз подготовить bpy, Node-зависимости и headless-библиотеки:

```bash
bash presentations/tools/setup-env.sh
```

Затем из этой папки:

```bash
node build.js --preview
```

Результаты:

```text
../../exports/impulse-spending-3d.pptx
../../exports/impulse-spending-presentation-script.md
../../exports/impulse-spending-sources.md
preview/slide-01.png … preview/slide-09.png
```

Быстрый черновик: `FAST=1 node build.js --preview` (постеры моделей рендерятся в меньшем разрешении).

Раскадровка циклов анимации и общий GIF-превью:

```bash
LD_LIBRARY_PATH=/tmp/bstub GLB_DIR="$PWD/models/glb" FRAMES=8 PX=280 SAMPLES=8 \\
  python3 ../cantillon/models/anim_preview.py chestnut smartphone cart wallet
python3 models/combine_anim_gifs.py ../cantillon/models/_anim ../../exports/impulse-spending-animations-preview.gif
```

## Модели

`models/make_models.py` создаёт процедурные модели `chestnut`, `smartphone`, `cart`, `wallet` в Blender. Используется общий движок из `presentations/schumpeter/lib.js` и `pptx3d.js`, а также `presentations/cantillon/models/rig.py` для skinned-анимации.

Анимации встроены как glTF skin + PowerPoint effect «Scene». Они автоматически проигрываются в PowerPoint 365 / 2021+; в Google Slides, Keynote, LibreOffice и браузерных просмотрщиках может отображаться статичный PNG-fallback.
