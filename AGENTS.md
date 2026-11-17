# AGENTS.md — Инструкция для ИИ-агента: как создавать 3D-презентации

Этот репозиторий — конвейер и база знаний для сборки **редактируемых презентаций PowerPoint (`.pptx`, 16:9) с настоящими интерактивными анимированными 3D-моделями** (`am3d:model3d` + `.glb` со скелетной glTF-анимацией + переходы **Morph**).

Когда пользователь просит сделать презентацию на любую тему (историческую, научную, учебную, продуктовую, техническую или шоурил), действуй строго по этому плейбуку.

---

## 1. Как устроен репозиторий и куда смотреть перед стартом

1. **[`train-ai/`](train-ai/)** — технический учебник по узлам конвейера (читай нужную главу перед написанием кода):
   * [`01-okruzhenie.md`](train-ai/01-okruzhenie.md) — headless Blender (`bpy`) без GPU/X11, заглушки `/tmp/bstub`, защита от сброса песочницы.
   * [`02-modeli-blender.md`](train-ai/02-modeli-blender.md) — процедурное 3D-моделирование кодом (`lathe`, `tube`, `grid_surface`, `extrude_profile`, `text_mesh`) и палитра материалов `M()`.
   * [`03-animaciya.md`](train-ai/03-animaciya.md) — скелетная анимация через `Rig` + `export_rigged`, кривые времени и готовые рецепты движения.
   * [`04-3d-v-pptx.md`](train-ai/04-3d-v-pptx.md) — устройство `am3d:model3d`, расчёт камеры, `a3danim:embedAnim`, эффект «Сцена» и Morph.
   * [`05-sborka-prezentacii.md`](train-ai/05-sborka-prezentacii.md) — API `lib.js`, дизайн-система слайдов, типографика, драматургия и заметки докладчика.
   * [`06-proverka-i-oshibki.md`](train-ai/06-proverka-i-oshibki.md) — чек-лист приёмки и полный список граблей PowerPoint / Blender.
   * [`train-ai/examples/`](train-ai/examples/) — минимальный end-to-end пример на ~100 строк (`box_with_lid.py` + `mini_deck.js`).
2. **[`presentations/`](presentations/) — Примеры презентаций (и общий движок)**:
   * **Общий движок** (импортируй его, не переписывай с нуля):
     * `presentations/schumpeter/lib.js` — слой разметки `Slide` → `.pptx` (`pptxgenjs`) и HTML-превью.
     * `presentations/schumpeter/pptx3d.js` — вставка `.glb` (`injectModels`), тайминг + Morph (`injectTiming`), дедупликация картинок (`dedupeMedia`).
     * `presentations/schumpeter/models/make_models.py` — базовые 3D-примитивы и материалы `M()`.
     * `presentations/schumpeter/models/render.py` — Cycles-рендер PNG-постеров с камерой «как в PowerPoint».
     * `presentations/cantillon/models/rig.py` — класс `Rig` и `export_rigged(...)` для скелетной анимации.
   * **Какой пример брать за образец под задачу**:
     * *Историческая / академическая / биографическая тема со скелетной анимацией* → [`presentations/cantillon/`](presentations/cantillon/) (10 слайдов, 10 музейных экспонатов).
     * *Длинный структурированный доклад и ядро движка* → [`presentations/schumpeter/`](presentations/schumpeter/) (15 слайдов, 14 экспонатов + шестерня прогресса).
     * *Короткий визуальный шоурил со сложной динамикой* → [`presentations/wow/`](presentations/wow/) (3 слайда: маяк, карусель, торнадо).
     * *Мульти-модельная сцена / диорама на одном слайде* → [`presentations/fun/`](presentations/fun/) (5 живых моделей одновременно, 64 кости).
3. **[`exports/`](exports/) — Примеры экспорта**:
   * Образец того, какие именно файлы и какого качества должны лежать в `exports/` по завершении работы (см. [`exports/README.md`](exports/README.md)).

---

## 2. Что должно получиться на выходе (Definition of Done)

Для новой презентации с ключом `<slug>` ты создаёшь исходники в `presentations/<slug>/` и выгружаешь в `exports/` полный пакет:

1. `exports/<slug>-3d-presentation.pptx` — редактируемый `.pptx` (16:9), проходящий `presentations/tools/validate-pptx.py`.
2. `exports/<slug>-presentation-script.md` — живой разговорный текст выступления по слайдам (40–60 с на слайд), также записанный внутрь заметок докладчика (`notes`) каждого слайда.
3. `exports/<slug>-presentation-sources.md` — таблица проверенных источников «Слайд | Факт / тезис | Источник» + библиография (для содержательных и учебных докладов).
4. `exports/<slug>-preview.jpg` — контакт-лист всех слайдов, проверенный тобой визуально (без наложений, обрезанных строк и мелкого текста).
5. `exports/<slug>-animations-preview.gif` — анимированная GIF-сетка всех 3D-экспонатов, отрендеренная из реальных экспортированных `.glb`.

---

## 3. Пошаговый алгоритм сборки новой презентации

### Шаг 0. Поднять окружение

В начале сессии (или после сброса песочницы) запусти установку тулчейна:

```bash
bash presentations/tools/setup-env.sh
```

Дождись вывода `bpy ...` и `SETUP_DONE`.
* **Важно:** каждый запуск Python-скрипта с `bpy` выполняй с `LD_LIBRARY_PATH=/tmp/bstub`.
* Тяжёлые задачи (рендер всех Cycles-растров или GIF) запускай с логированием или через фоновый процесс, чтобы не упереться в таймаут команды.

### Шаг 1. Продумать структуру, фактологию и драматургию

* **Один слайд = один сильный заголовок-тезис** (не «Биография» или «Методология», а содержательное утверждение) + 3–4 компактных смысловых блока + плашка «★ САМОЕ ИНТЕРЕСНОЕ» + **один предметный 3D-экспонат** справа (на титульном слайде — крупнее).
* **Честность фактов:** никогда не выдумывай цитаты, цифры рынка, законы или результаты ещё не проведённых опросов. Спорные исторические байки помечай явно («по легенде…», «по оценке…»). Сразу фиксируй источники для `exports/<slug>-presentation-sources.md`.
* **Никаких ИИ-сгенерированных картинок:** фоны, свечения и тени генерируются кодом (`stage.py` на `numpy`), 3D-модели строятся процедурно в Blender (`bpy`). Допускаются только реальные исторические изображения в общественном достоянии (Wikimedia Commons) с атрибуцией.

### Шаг 2. Спроектировать и собрать 3D-экспонаты (`presentations/<slug>/models/make_models.py`)

Создай `presentations/<slug>/models/make_models.py`, подключив общий движок моделирования и риггинга:

```python
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "cantillon", "models"))   # rig.py
sys.path.insert(0, os.path.join(HERE, "..", "..", "schumpeter", "models"))  # make_models.py
import make_models as mm
from make_models import (bpy, bmesh, Vector, Matrix, TAU, M, finish, mesh_obj,
                         lathe, box, cyl, sphere, torus, tube, to_mesh, profile2d, coin, book)
from rig import Rig, export_rigged, clamp01, smooth, ease, pulse, back_out, hop, wave

mm.OUT = os.path.join(HERE, "glb")
os.makedirs(mm.OUT, exist_ok=True)
```

Если теме нужны дополнительные материалы (экраны, пластик, неон UI, банкноты и т.п.), расширь базовую палитру `M()` своими PBR-материалами прямо в `presentations/<slug>/models/make_models.py` (без прозрачности `BLEND`).

**Правила моделирования и анимации:**
* **Только скелетная анимация (`Rig` + `export_rigged`):** PowerPoint **игнорирует** обычную анимацию объектов (node TRS) и shape keys. Все подвижные детали привязываются к костям одной армутуры (`m = rig.mark()` → геометрия → `rig.take(m, "part", head=(x, y, z))`).
* **Бесшовный цикл `t ∈ [0, 1)`:** функция `anim(t)` обязана давать **одинаковую позу при `t = 0` и `t = 1`**. Длина петли — обычно `4.0–6.0` с.
* **Кадр `t = 0` — это постер и PNG-fallback:** если в `t = 0` модель выглядит пусто или закрыто, сдвинь фазу: `return rig, (lambda t: anim((t + 0.25) % 1.0)), 5.0`.
* **Габариты покоя:** PowerPoint ставит камеру по описанной сфере в **позе покоя**. Открывающаяся крышка, вылетающая монета или дым не должны выходить далеко за эту сферу (запас ~20–35 %), иначе края обрежутся.
* **Читаемость деталей и материалов:** мелкие элементы (стрелки, частицы, значки, птицы) делай в 1.5–2 раза крупнее физического масштаба; у металлов держи `roughness ≥ 0.3` (зеркальный хром на тёмном фоне становится чёрным).
* **Бюджет модели:** ~3–30 тыс. треугольников, размер `.glb` до ~1.5 МБ.

Собери модели:
```bash
cd presentations/<slug>
LD_LIBRARY_PATH=/tmp/bstub python3 models/make_models.py
```

### Шаг 3. Проверить анимацию каждого `.glb` глазами ДО сборки слайдов

Прогони раскадровку (она импортирует готовый `.glb` обратно в Blender ровно с той же камерой, что будет у PowerPoint):

```bash
cd presentations/<slug>
GLB_DIR=$PWD/models/glb LD_LIBRARY_PATH=/tmp/bstub KEEP=1 FRAMES=8 PX=300 SAMPLES=10 \
  python3 ../cantillon/models/anim_preview.py <key1> <key2> ...
```

Открой полоски `../cantillon/models/_anim/<key>.png` через `read_file` и убедись глазами:
1. Детали не вылетают за края квадрата на пике движения.
2. Движение хорошо заметно, знак углов поворота правильный (крышка открывается наружу, а не сквозь корпус).
3. Материалы не проваливаются в черноту, кадр `00` выглядит выигрышно.

Если что-то не так — поправь `make_models.py` и перепроверь конкретный ключ.

### Шаг 4. Сгенерировать фон сцены (`stage.py`) и собрать слайды (`build.js`)

1. **`stage.py`** (по образцу `presentations/cantillon/stage.py` или `presentations/wow/stage.py`): генерирует `assets/stage-bg.jpg` (градиент + мягкая виньетка + лёгкое зерно без полос), `assets/glow.png`, `assets/shadow.png` и прозрачный `assets/clear.png` (для Morph-призраков).
2. **`build.js`** (по образцу `presentations/cantillon/build.js` или `presentations/wow/build.js`):
   * Подключает `../schumpeter/lib.js` и `../schumpeter/pptx3d.js` (а пакеты `pptxgenjs` / `jszip` резолвит из `../schumpeter/package.json`).
   * На каждом слайде размещает главный экспонат `!!m-<key>`, а за правым и левым краями слайда — «призраки» соседних экспонатов с `clear.png`, чтобы **Morph** плавно ввозил и увозил 3D-модели с поворотом.
   * На верхней шкале прогресса двигает и вращает 3D-жетон (`!!coin` / `!!token`, ~`-146°` на слайд).
   * Для быстрой отладки вёрстки используй `FAST=1 node build.js --preview --only=1,2`, а перед финалом — полный прогон без `FAST`:
     ```bash
     python3 stage.py
     node build.js --preview
     ```

### Шаг 5. Финальные превью, проверка глазами и структурная валидация

1. **Собери обзорный контакт-лист всех слайдов и просмотри его глазами** (через `read_file`):
   ```bash
   python3 presentations/tools/contact-sheet.py presentations/<slug>/preview exports/<slug>-preview.jpg
   ```
   Проверь каждый слайд: нет ли переноса заголовка на лишнюю строку с наездом на подзаголовок, не вылезает ли текст из карточек, нет ли кегля мельче 9 pt. При малейшем дефекте поправь координаты/размер в `build.js` и пересобери.
2. **Собери сводный GIF анимаций экспонатов в `exports/`**:
   ```bash
   python3 presentations/cantillon/models/anim_sheet.py exports/<slug>-animations-preview.gif <key1> <key2> ...
   ```
   *(Либо скопируй/адаптируй `anim_preview.py` + `anim_sheet.py` локально в `presentations/<slug>/models/`).*
3. **Запусти автоматический валидатор `.pptx`**:
   ```bash
   python3 presentations/tools/validate-pptx.py exports/<slug>-3d-presentation.pptx --expect-slides <N>
   ```
   Убедись, что скрипт напечатал `VALIDATED ...` с кодом возврата `0`.
4. **Добавь `presentations/<slug>/README.md` и `.gitignore`** (`preview/`, `node_modules/`, `models/_anim/`, `models/_look/`, `__pycache__/`).

---

## 4. Красная зона: 10 правил, нарушение которых ломает PowerPoint

1. **Никакого node TRS и shape keys в `.glb`** — только кости (`skins` ≥ 1).
2. **Ровно одна армутура и одно действие (`animations` == 1)** внутри каждого `.glb`.
3. **Никакого Draco-сжатия** при экспорте glTF — PowerPoint не умеет читать Draco.
4. **Никаких дубликатов `name` у 3D-моделей на одном слайде** — PowerPoint молча удалит модель.
5. **Одинаковый `id` у `p:graphicFrame` (`mc:Choice`) и `p:pic` (`mc:Fallback`)** — это делает `pptx3d.js`, не ломай структуру XML.
6. **Строгий порядок тегов внутри `<am3d:model3d>`:** `spPr → camera → trans → raster → extLst → objViewport → ambientLight → ptLight`.
7. **Исключать коллекцию `glTF_not_exported`** при повторном импорте в Blender (уже учтено в `render.py`), иначе служебная икосфера костей сломает масштаб камеры.
8. **Применять все модификаторы и `transform_apply` до привязки к костям и экспорта** (`export_rigged` делает это сам).
9. **Не ставить `inset: 0` в `pptxgenjs`** (он игнорируется) — используй `margin: [0, 0, 0, 0]` (уже зашито в `lib.js`).
10. **Честно предупреждать пользователя в ответе:** живое 3D и Morph работают в **PowerPoint 365 / PowerPoint 2021+** (Windows/macOS); в старых версиях, Google Slides, Keynote, LibreOffice и веб-просмотрщиках автоматически показываются встроенные статичные PNG-рендеры (`mc:Fallback`).
