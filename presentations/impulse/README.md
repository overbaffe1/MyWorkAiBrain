# «Почему мы покупаем ненужное?» — мемная 3D-презентация

Полная переделка проекта об импульсивных покупках у студентов 18–25 лет. Визуально возвращён язык исходного PowerPoint: синий гранжевый фон, мемы/коллажи, бумажные вырезки, красные мазки и более шутливые подписи. Фото каштанов не вынесено в отдельную тему: оно возвращено в исходную пару с мемом «ГДЕ ПАПА?» на слайде задач; «КАШТАН 100%» — короткая подпись внутри этого коллажа. Процедурная 3D-модель каштана тоже стоит там же.

Содержание остаётся проектным исследованием: собственный опрос ещё не проведён, результаты не выдуманы. «N ≥ 50» обозначено как ориентир для пилотной удобной выборки, не как репрезентативный результат.

## Сборка

```bash
bash ../tools/setup-env.sh
LD_LIBRARY_PATH=/tmp/bstub python3 models/make_models.py
python3 stage.py
node build.js --preview
LD_LIBRARY_PATH=/tmp/bstub KEEP=1 FRAMES=8 PX=300 SAMPLES=8 python3 models/anim_preview.py cart wallet cycle triggers scale chestnut clipboard chart hourglass
python3 models/anim_sheet.py ../../exports/ekonomika123-3d-presentation-animations-preview.gif cart wallet cycle triggers scale chestnut clipboard chart hourglass
```

Готовые материалы создаются в `exports/`: `.pptx`, текст выступления, источники, лист превью и GIF анимаций. В PowerPoint 365/2021+ модели вставлены как native 3D с циклической анимацией; для остальных просмотрщиков в `.pptx` остаются PNG-заглушки.

Модели созданы процедурно в Blender; код использует общий слой презентаций (`presentations/schumpeter`) и скелетную анимацию из `presentations/cantillon/models/rig.py`. Мем-изображения извлечены из предоставленного оригинала `ekonomika123.pptx` и используются как его визуальные элементы, не как источники фактов.
