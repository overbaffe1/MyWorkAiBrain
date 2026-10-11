# «Почему мы покупаем ненужное?» — 3D-презентация

Проектная презентация об импульсивных покупках у студентов 18–25 лет. Это **план исследования**, а не отчёт о собранных данных: выводы и проценты по опросу не придуманы.

## Сборка

```bash
bash ../tools/setup-env.sh
LD_LIBRARY_PATH=/tmp/bstub python3 models/make_models.py
python3 stage.py
node build.js --preview
LD_LIBRARY_PATH=/tmp/bstub KEEP=1 FRAMES=8 PX=300 SAMPLES=8 python3 models/anim_preview.py cart wallet cycle triggers scale clipboard chart hourglass compass
python3 models/anim_sheet.py ../../exports/ekonomika123-3d-presentation-animations-preview.gif cart wallet cycle triggers scale clipboard chart hourglass compass
```

Готовые файлы создаются в `exports/`: `.pptx`, текст выступления, источники, лист PNG-превью и GIF анимаций. В PowerPoint 365/2021+ GLB-модели вращаются и запускают встроенную циклическую анимацию; в других офисных пакетах остаётся PNG-fallback.

Модели созданы процедурно в Blender; код использует общий движок презентаций (`presentations/schumpeter`) и скелетную анимацию из `presentations/cantillon/models/rig.py`.
