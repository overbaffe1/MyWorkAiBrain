# train-ai — как делать «3D-презентации» с анимированными моделями

Инструкция-конспект всех приёмов, которыми в этом репозитории собраны презентации
Шумпетер / Кантильон / Львов (`presentations/`, готовые файлы — `exports/`).
Написана так, чтобы другой ИИ-агент (или человек) мог повторить весь конвейер с нуля.

## Что получается на выходе

* Обычный редактируемый `.pptx` (16:9), в котором на каждом слайде стоит **настоящая 3D-модель PowerPoint**
  (`am3d:model3d`, файл `.glb` внутри pptx): её можно вращать мышкой, она без фона.
* Внутри каждой модели — **собственная анимация частей** (крышка сундука открывается, струны дрожат, стрелка компаса
  качается…). Это скелетная (skinned) glTF-анимация; PowerPoint 365 запускает её сам как эффект «Сцена» и крутит по кругу.
* Между слайдами — переход **Morph**: экспонаты «влетают» и «улетают» в 3D.
* Текст выступления в заметках докладчика + `*-script.md`, список источников `*-sources.md`, PNG-превью всех слайдов,
  GIF со всеми анимациями.

## Конвейер (одна картинка)

```
Blender (bpy, Python)                      Node.js (pptxgenjs)                    пост-обработка XML (JSZip)
─────────────────────                      ───────────────────                    ──────────────────────────
make_models.py ──► процедурные меши        build.js: описание слайдов             pptx3d.js:
rig.py         ──► кости + ключи    ──►    (lib.js: text/rect/img/model)  ──►     • картинка-заглушка → am3d:model3d + .glb
               ──► models/glb/*.glb        toPptx() → .pptx с картинками-         • embedAnim (анимация в модели)
render.py      ──► PNG-растр модели        заглушками "MODEL::id::name"           • timing: «Сцена» + fade-in + Morph
anim_preview   ──► GIF для проверки        toHtml() → PNG-превью (Chromium)       • дедупликация картинок
```

## Оглавление

| Файл | О чём |
|---|---|
| [01-okruzhenie.md](01-okruzhenie.md) | Окружение: headless Blender (`bpy`) без GPU и X11, заглушки библиотек, сброс песочницы, git |
| [02-modeli-blender.md](02-modeli-blender.md) | Как создаются 3D-объекты кодом: примитивы, lathe, трубки, поверхности, текст, материалы, правила «чтобы не выглядело как ИИ» |
| [03-animaciya.md](03-animaciya.md) | Анимация внутри модели: почему только кости, `rig.py`, функция `anim(t)`, бесшовные циклы, рецепты (крышка, струны, страницы, птица, дым…) |
| [04-3d-v-pptx.md](04-3d-v-pptx.md) | Как 3D-модель вставляется в pptx: XML `am3d:model3d`, камера, растр-заглушка, `embedAnim`, эффект «Сцена», Morph |
| [05-sborka-prezentacii.md](05-sborka-prezentacii.md) | Сборка слайдов: `lib.js`, компоненты (экспонат, плашка «★», строки), дизайн-правила, содержание, текст выступления |
| [06-proverka-i-oshibki.md](06-proverka-i-oshibki.md) | Проверка (превью, GIF, валидация XML) + список всех граблей, на которые уже наступили |
| [examples/](examples/) | Минимальный рабочий пример: шкатулка с крышкой и монетой → `.glb` с анимацией → однослайдовый `demo.pptx` с 3D-сценой (проверено) |

## Карта файлов репозитория

| Путь | Роль |
|---|---|
| `presentations/tools/setup-env.sh` | Поднимает всё окружение одной командой |
| `presentations/schumpeter/lib.js` | Слой разметки: `Slide` → pptx (pptxgenjs) и → HTML для превью |
| `presentations/schumpeter/pptx3d.js` | Вставка 3D-моделей, анимации модели, тайминга, Morph в готовый pptx |
| `presentations/schumpeter/models/make_models.py` | Базовые хелперы моделирования + палитра материалов (`M()`) |
| `presentations/schumpeter/models/render.py` | Рендер PNG-растров моделей (Cycles) с камерой «как в PowerPoint» |
| `presentations/cantillon/models/rig.py` | Кости, привязка частей, запекание анимации, экспорт skinned glTF |
| `presentations/cantillon/models/make_models.py` | 10 анимированных экспонатов (лучший пример для подражания) |
| `presentations/cantillon/models/anim_preview.py`, `anim_sheet.py` | Раскадровка/GIF анимации из готового .glb |
| `presentations/cantillon/build.js` | Сборка 10-слайдовой презентации (компоненты, Morph-хореография) |
| `presentations/cantillon/stage.py` | Фон, световое пятно и тень под моделью (numpy, без ИИ-картинок) |

## Быстрый старт

```bash
bash presentations/tools/setup-env.sh                         # ~2–3 мин, печатает SETUP_DONE
cd presentations/cantillon
LD_LIBRARY_PATH=/tmp/bstub python3 models/make_models.py      # все .glb (или: ... make_models.py chest harp)
LD_LIBRARY_PATH=/tmp/bstub python3 models/anim_preview.py chest   # models/_anim/chest.gif — проверить движение
python3 stage.py                                              # фоновые ассеты
node build.js --preview                                       # → exports/cantillon-3d-presentation.pptx + preview/*.png
```

Полная сборка с рендером всех растров идёт 5–15 минут — запускать фоновым процессом, а не в блокирующей команде.
