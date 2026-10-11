# Покупка на автопилоте — редизайн `ekonomika123.pptx`

Десять слайдов о психологии импульсивных трат. Сохранена лёгкая мемная интонация исходника и его каштановая фотография; к ней добавлен повторяющийся процедурный 3D-персонаж Каштан. Мемы перенесены из оригинального файла и используются как иллюстрации, не как данные.

## Что изменено

- Оставлена тема исходного проекта: импульсивные покупки и студенты 18–25 лет.
- Переработана структура: определение → механизм → возможные триггеры → вопрос и гипотезы → план опроса → практическая памятка.
- Непроверенные числа о BNPL и законе из черновика не повторяются как факты; тема оплаты частями оставлена как возможная переменная анкеты.
- N ≥ 50 обозначено как планируемый набор, а не уже полученная выборка. Результаты опроса не придуманы.
- Все десять слайдов содержат настоящую 3D-модель PowerPoint с skinned glTF-анимацией, Morph-переходы и заметки докладчика; файл источников отдельно связывает утверждения с публикациями и помечает статус плана/гипотез.
- Главный файл на месте исходной ссылки: `../../ekonomika123.pptx`.

## Сборка

```bash
bash presentations/tools/setup-env.sh
cd presentations/impulse
python3 stage.py
LD_LIBRARY_PATH=/tmp/bstub python3 models/make_models.py kashtan
node build.js --preview
python3 preview_sheet.py
LD_LIBRARY_PATH=/tmp/bstub FRAMES=10 PX=300 SAMPLES=10 python3 models/anim_preview.py
cp preview/kashtan-animation.gif ../../exports/impulse-spending-animations-preview.gif
python3 validate.py
```

`node build.js --preview --only=2,5` can be used for quick layout checks; `FAST=1 node build.js --preview` renders a low-resolution draft. PowerPoint assets are produced by the shared repo pipeline (`presentations/schumpeter/lib.js`, `pptx3d.js`, and `models/render.py`). The mascot uses `presentations/cantillon/models/rig.py` for the tested skinned-animation exporter.

## Output

- `ekonomika123.pptx` — editable 16:9 PowerPoint deck, 10 slides, real 3D GLB models, auto-playing animation and Morph.
- `exports/impulse-spending-script.md` — speaker script, also placed in slide notes.
- `exports/impulse-spending-sources.md` — source-to-slide map, limitations and full bibliography.
- `exports/impulse-spending-preview.jpg` — 2×5 slide overview.
- `exports/impulse-spending-animations-preview.gif` — loop preview of the mascot animation.

3D playback and Morph are intended for PowerPoint 365 / PowerPoint 2021+; apps without native PowerPoint 3D display the embedded still-image fallback. The survey is still a plan: only report results after collecting and analyzing responses.
