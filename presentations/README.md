# Примеры презентаций (`presentations/`)

В этой папке лежат **эталонные примеры презентаций** (исходный код моделей, фонов и сборки слайдов), а также **общий движок и утилиты**, которые переиспользует любая новая презентация в репозитории.

Если вы ИИ-агент и делаете новую презентацию — начните с пошагового плейбука в [`../AGENTS.md`](../AGENTS.md) и учебника [`../train-ai/`](../train-ai/), а папки ниже используйте как рабочие референсы и библиотеку хелперов.

---

## Каталог примеров презентаций

| Папка | Тема и жанр | Слайдов | Моделей / анимация | Чему учиться в этом примере |
|---|---|---:|---|---|
| [`cantillon/`](cantillon/) | **Ричард Кантильон** — историко-экономический доклад («музей экспонатов XVIII века») | 10 | 10 rigged `.glb` + жетон `louis` | **Главный эталон скелетной анимации** (`models/rig.py`): сундук с ключом, арфа со струнами, корабль на волнах, листающаяся книга, пузырь Миссисипи, весы, свеча с мотыльком + Morph-хореография |
| [`impulse/`](impulse/) | **Психология импульсивных трат** — современное проектное исследование | 13 | 13 rigged `.glb` + жетон `token` | Как делать **современные и цифровые объекты** (смартфон с нажатием кнопки, карта у терминала, слот-автомат «ДОФАМИН», чек BNPL, анкета с лупой) + расширение палитры через `EXTRA` (`mm.M = MT`) и холодный цифровой фон в `stage.py` |
| [`schumpeter/`](schumpeter/) | **Йозеф Шумпетер** — биография и теория инноваций | 15 | 14 статичных `.glb` + шестерня `gear_s` | **Ядро общего движка** (`lib.js`, `pptx3d.js`, `models/make_models.py`, `models/render.py`, `package.json`) + классическая сборка длинного академического доклада с катящейся шестернёй прогресса |
| [`wow/`](wow/) | **«Три чуда»** — короткий визуальный шоурил | 3 | 3 rigged `.glb` + `louis` | Сложная многосоставная анимация: маяк с вращающимися лучами и чайкой (14 костей), ярмарочная карусель с лошадками (5 костей), торнадо с кольцами воронки, обломками и молнией (15 костей) |
| [`fun/`](fun/) | **«Остров огня»** — живая фан-диорама на одном слайде | 1 | 5 rigged `.glb` на 1 слайде (64 кости) | Как разместить **несколько живых 3D-моделей одновременно на одном слайде**: извергающийся вулкан с орбитальным драконом (40 костей), парные факелы и кипящие лава-чаши + быстрая GIF-проверка `models/gifcheck.py` |

Готовые выходные файлы всех пяти проектов лежат в [`../exports/`](../exports/) («Примеры экспорта»).

---

## Общий движок и инструменты внутри `presentations/`

Новые презентации **не копируют** движок к себе (кроме при необходимости локальных хелперов), а импортируют его напрямую:

| Путь | Назначение |
|---|---|
| [`tools/setup-env.sh`](tools/setup-env.sh) | Поднимает всё окружение в чистой песочнице без `apt` и GPU: `bpy` (headless Blender), X11/GL-заглушки в `/tmp/bstub`, `pillow`, `numpy`, `python-pptx` и `npm i` в `schumpeter/` |
| [`tools/validate-pptx.py`](tools/validate-pptx.py) | Универсальная структурная проверка готового `.pptx` (валидность XML, наличие `am3d:model3d`, уникальность имён, `embedAnim`, эффект «Сцена», Morph, заметки, отсутствие Draco) |
| [`tools/contact-sheet.py`](tools/contact-sheet.py) | Склейка `preview/slide-*.png` в единый подписанный лист `exports/<slug>-preview.jpg` для быстрой визуальной проверки вёрстки |
| [`tools/build-readme-assets.py`](tools/build-readme-assets.py) | Генератор выставочной витрины `.github/assets/`: проекция реальных `.glb` в гравюры и рентген костей, экспорт `.stl`-слепков, печати и карта репозитория |
| [`schumpeter/lib.js`](schumpeter/lib.js) | Декларативная разметка слайда (`Slide`): один код рендерится и в редактируемый `.pptx` (`pptxgenjs`), и в HTML → PNG (`puppeteer-core` + `@sparticuz/chromium`) |
| [`schumpeter/pptx3d.js`](schumpeter/pptx3d.js) | Пост-обработка `.pptx` через `JSZip`: подмена картинок-заглушек на `am3d:model3d` + `.glb`, расчёт камеры, `a3danim:embedAnim`, тайминг «Сцены», Morph и дедупликация медиа |
| [`schumpeter/models/make_models.py`](schumpeter/models/make_models.py) | Базовые геометрические примитивы (`box`, `cyl`, `sphere`, `torus`, `lathe`, `tube`, `profile2d`, `mesh_obj`, `coin`, `book`) и палитра материалов `M(name)` |
| [`schumpeter/models/render.py`](schumpeter/models/render.py) | Рендер PNG-растров (постер + fallback) в Cycles с камерой, совпадающей с камерой PowerPoint; кэш по `md5` в `models/rasters/` |
| [`cantillon/models/rig.py`](cantillon/models/rig.py) | Скелетная анимация для PowerPoint: класс `Rig`, кривые времени (`ease`, `pulse`, `back_out`, `hop`, `wave`, `puff_pose`, `flyer`) и экспорт `export_rigged(...)` |
| [`cantillon/models/anim_preview.py`](cantillon/models/anim_preview.py), [`anim_sheet.py`](cantillon/models/anim_sheet.py) | Повторный импорт готового `.glb` в Blender → рендер покадровой раскадровки и GIF-сетки всех анимаций без PowerPoint |

---

## Стандартная структура новой презентации `presentations/<slug>/`

```text
presentations/<slug>/
├── README.md               # Как пересобрать проект + таблица 3D-экспонатов
├── .gitignore              # preview/, node_modules/, models/_anim/, models/_look/
├── stage.py                # Генерация assets/stage-bg.jpg, glow.png, shadow.png, clear.png (numpy)
├── build.js                # Слайды, заметки докладчика, Morph-призраки, сборка в ../../exports/
├── assets/                 # Сгенерированные фоны сцены и проверенные public-domain иллюстрации
└── models/
    ├── make_models.py      # Процедурные 3D-модели и функции anim(t) → models/glb/*.glb
    ├── glb/                # Готовые .glb модели (коммитятся в git)
    └── rasters/            # Кэш PNG-растров с префиксом md5 (коммитятся в git)
```
