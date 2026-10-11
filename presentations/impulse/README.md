# Психология импульсивных трат — 3D-презентация

Редизайн исходного `ekonomika123.pptx`: исследовательская презентация на 10 слайдов, с редактируемым текстом, заметками докладчика, нативными 3D-моделями PowerPoint, Morph-переходами, планом опроса, памяткой и источниками.

```bash
bash ../tools/setup-env.sh
LD_LIBRARY_PATH=/tmp/bstub python3 models/make_models.py
python3 stage.py
node build.js --preview
# необязательная проверка 3D-петель и общий GIF предпросмотра:
LD_LIBRARY_PATH=/tmp/bstub GLB_DIR=$PWD/models/glb FRAMES=8 PX=260 python3 ../cantillon/models/anim_preview.py phone brain paylater clipboard timer bag
python3 animation_sheet.py ../cantillon/models/_anim ../../exports/impulse-buying-3d-animations-preview.gif
```

В презентации нет выдуманных результатов опроса. Исследование сформулировано как план: студенты 18–25 лет, целевой минимум N ≥ 50, а анализ проверяет связи, а не причинность. Не подтверждённые источником рыночные оценки BNPL из исходного черновика в новую версию не перенесены.

3D-модели созданы процедурно в Blender специально для темы. Общие хелперы сборки и вставки 3D находятся в `../schumpeter`, скелетная анимация — в `../cantillon/models/rig.py`. PowerPoint 365/2021+ воспроизводит внутренние петли модели; в других просмотрщиках остаётся корректный статичный PNG-fallback.
