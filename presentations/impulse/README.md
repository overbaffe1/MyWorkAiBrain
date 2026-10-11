# «Я только посмотрю» — мемная 3D-презентация

Полный редизайн исходной `ekonomika123.pptx`: мемный коллаж на фоне тетрадной бумаги, исходные мем-картинки и сквозной каштан-маскот. Содержание остаётся исследовательским планом об импульсивных тратах у студентов 18–25 лет: текст редактируется, заметки докладчика сохранены, на каждом слайде — нативная анимированная 3D-модель PowerPoint и Morph-переходы.

```bash
bash ../tools/setup-env.sh
LD_LIBRARY_PATH=/tmp/bstub python3 models/make_models.py
python3 stage.py
node build.js --preview
# проверить петли всех моделей и собрать общий GIF:
LD_LIBRARY_PATH=/tmp/bstub GLB_DIR=$PWD/models/glb FRAMES=8 PX=260 python3 ../cantillon/models/anim_preview.py chestnut phone brain paylater clipboard timer bag scales
python3 animation_sheet.py ../cantillon/models/_anim ../../exports/impulse-buying-3d-animations-preview.gif
python3 validate.py
```

Мемы и каштан — иллюстрации, не доказательства и не результаты опроса. Цифры рынка BNPL без проверяемого первичного источника не используются; пример `12 000 ₽ = 4 × 3 000 ₽` — только условная арифметика, не тариф.

Общие хелперы сборки и вставки 3D находятся в `../schumpeter`, скелетная анимация — в `../cantillon/models/rig.py`. PowerPoint 365/2021+ воспроизводит внутренние петли моделей; в других просмотрщиках остаётся PNG-fallback.
