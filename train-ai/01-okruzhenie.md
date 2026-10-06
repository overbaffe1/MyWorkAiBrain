# 01. Окружение

## Что нужно

| Инструмент | Зачем | Как ставится |
|---|---|---|
| `bpy` (Blender как Python-модуль, проверено 5.0.1) | моделирование, кости, экспорт `.glb`, рендер растров | `pip install --break-system-packages bpy` |
| `pillow`, `numpy` | фоны, свечение, тени, склейка превью и GIF | pip |
| `python-pptx`, `lxml` | только для проверки готового pptx | pip |
| Node.js + `pptxgenjs`, `jszip` | генерация pptx и пост-обработка XML | `npm i` в `presentations/schumpeter` |
| `puppeteer-core` + `@sparticuz/chromium` | PNG-превью слайдов из HTML | там же |
| `@fontsource/*` | шрифты для HTML-превью | там же |

Всё это делает **`presentations/tools/setup-env.sh`** (в конце печатает `bpy 5.0.1` и `SETUP_DONE`).

## Headless Blender без GPU и без X11

`import bpy` в голом контейнере падает с `ImportError: libXrender.so.1 …` — модуль слинкован с X11/OpenGL,
хотя для фоновой работы они не нужны. `apt-get` при этом недоступен. Решение — **библиотеки-заглушки**:

1. Пустые `.so` с нужным `soname` для `libXrender.so.1 libXfixes.so.3 libXi.so.6 libSM.so.6 libICE.so.6`
   (`gcc -shared -fPIC -o libX.so s.c -Wl,-soname,libX.so`).
2. `libxkbcommon.so.0` — настоящий, вынимается из колеса `opencv-python` (`pip download opencv-python --no-deps`).
3. `libGL.so.1` — генерируется: собираем все неопределённые символы `gl*`, `X*`, `Ice*`, `Sm*` из `.so` внутри пакета bpy
   (`nm -D --undefined-only`) и создаём функции-пустышки `void* glFoo(void){return 0;}`.
4. Всё кладётся в `/tmp/bstub`, и **каждый** запуск Blender-скриптов идёт с `LD_LIBRARY_PATH=/tmp/bstub`.

Ограничения такого Blender:

* Рендерит **только Cycles на CPU** (EEVEE/Workbench требуют OpenGL). Для растров 700–1100 px хватает 48–64 сэмплов + денойз.
* Операторы `bpy.ops.*`, которым нужен контекст (join, mode_set), работают через
  `with bpy.context.temp_override(active_object=..., selected_editable_objects=[...]):` или через
  `bpy.context.view_layer.objects.active = obj`.

## Песочница сбрасывается

Песочница периодически откатывается (в том числе посреди работы): пропадают `/tmp`, pip-пакеты, `node_modules`,
а репозиторий возвращается к старому коммиту. Отсюда правила:

* **Всё ценное коммитить и пушить сразу** (включая `setup-env.sh`, сгенерированные `.glb`, растры, экспорт).
* После сброса:
  ```bash
  timeout 90 git fetch --depth=1 origin <ветка>
  git reset --hard FETCH_HEAD                 # если незакоммиченной работы нет
  # если есть незакоммиченная работа — сохранить её дерево поверх свежего коммита:
  git reset --soft FETCH_HEAD && git commit -m "…"
  bash presentations/tools/setup-env.sh
  ```
* Клон неглубокий: обычный `git fetch` может висеть — только `--depth=1` и с `timeout`.
* Перед коммитом сверить `git ls-remote origin <ветка>` с `HEAD`. Если push отклонён как non-fast-forward —
  значит коммит лёг на откатившуюся базу: `fetch` + `reset --soft FETCH_HEAD` + повторный коммит.

## Долгие процессы

Сборка презентации (рендер 10–25 растров в Cycles) и рендер GIF занимают минуты. Запускать в фоне,
писать лог в файл и ждать завершения (`… > /tmp/build.log 2>&1; echo EXIT $? >> /tmp/build.log`), а не держать
блокирующую команду — иначе таймаут.

## Превью через Chromium

`@sparticuz/chromium` содержит архив с системными библиотеками (`bin/al2023.tar.br`): его распаковывают в `/tmp/al`
и добавляют `/tmp/al/lib` в `LD_LIBRARY_PATH` (это делает `build.js` сам). Импорт: `const c = mod.default || mod`.
Шрифт `@fontsource/gelasio` без кириллицы — для превью используется Noto Serif.
