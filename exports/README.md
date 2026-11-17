# Примеры экспорта (`exports/`)

В этой папке лежат **готовые выходные артефакты** презентаций из [`../presentations/`](../presentations/) — то, что непосредственно отдаётся пользователю, открывается в PowerPoint или отправляется на защиту.

Для ИИ-агента эта папка служит **эталоном выходного пакета**: любая новая презентация `presentations/<slug>/` должна складывать свои финальные файлы именно сюда.

---

## Стандарт выходного пакета для новой презентации

Полный комплект экспорта для презентации `<slug>` включает:

1. **`<slug>-3d-presentation.pptx`** — редактируемая широкоэкранная (16:9) презентация PowerPoint с нативными 3D-моделями (`am3d:model3d`), встроенной скелетной glTF-анимацией (`a3danim:embedAnim` + бесконечный эффект «Сцена»), переходами **Morph** между слайдами, PNG-fallback растрами и текстом выступления в заметках докладчика.
2. **`<slug>-presentation-script.md`** — полный текст устного выступления по слайдам (дублирует заметки докладчика внутри `.pptx` + подсказки по таймингу и движению экспонатов).
3. **`<slug>-presentation-sources.md`** — таблица проверяемых источников по каждому слайду и факту + библиография (обязательно для учебных, научных и аналитических тем).
4. **`<slug>-preview.jpg`** — контакт-лист (сетка PNG-превью всех слайдов, собирается через `presentations/tools/contact-sheet.py`) для мгновенного визуального обзора вёрстки.
5. **`<slug>-animations-preview.gif`** — анимированная GIF-сетка всех 3D-экспонатов (собирается из реальных `.glb` через `anim_preview.py` + `anim_sheet.py`).

---

## Содержимое папки (готовые примеры)

| Проект | Файлы в `exports/` | Слайдов | Особенности экспорта |
|---|---|---:|---|
| **Психология импульсивных трат** (`presentations/impulse`) | `impulse-3d-presentation.pptx`<br>`impulse-presentation-script.md`<br>`impulse-presentation-sources.md`<br>`impulse-preview.jpg`<br>`impulse-animations-preview.gif` | 13 | Полный эталонный комплект из всех 5 типов артефактов: 13 скелетно-анимированных 3D-моделей, Morph, заметки, таблица источников, контакт-лист и GIF-превью |
| **Ричард Кантильон** (`presentations/cantillon`) | `cantillon-3d-presentation.pptx`<br>`cantillon-presentation-script.md`<br>`cantillon-preview.jpg` | 10 | 10 анимированных музейных экспонатов XVIII века + катящийся по шкале прогресса 3D-луидор + контакт-лист |
| **Йозеф Шумпетер** (`presentations/schumpeter`) | `schumpeter-3d-presentation.pptx`<br>`schumpeter-presentation-script.md`<br>`schumpeter-preview.jpg` | 15 | 14 процедурных 3D-моделей + Morph-хореография, вращающаяся латунная шестерня прогресса и контакт-лист |
| **Три чуда** (`presentations/wow`) | `wow-3d-wonders.pptx`<br>`wow-wonders-script.md`<br>`wow-preview.jpg` | 3 | Короткий шоурил из 3 сложных составных анимаций (маяк, карусель, торнадо) + контакт-лист |
| **Остров огня** (`presentations/fun`) | `fun-fire-island.pptx`<br>`fun-fire-island-script.md` | 1 | 5 одновременно работающих 3D-моделей на одном слайде (64 кости: вулкан, дракон, факелы, лава) |

---

## Быстрая проверка любого `.pptx` в `exports/`

```bash
python3 presentations/tools/validate-pptx.py exports/impulse-3d-presentation.pptx
python3 presentations/tools/validate-pptx.py exports/cantillon-3d-presentation.pptx
python3 presentations/tools/validate-pptx.py exports/schumpeter-3d-presentation.pptx --allow-static
```

## Где и как открывать `.pptx`

* **PowerPoint 365 / PowerPoint 2021+ (Windows и macOS)** — полная поддержка: настоящие интерактивные 3D-модели (вращаются мышью в режиме редактирования), автоматическое воспроизведение скелетных анимаций при показе слайдов и плавные 3D-переходы **Morph**.
* **Старые версии PowerPoint, Keynote, Google Slides, LibreOffice Impress, веб-просмотрщики LMS/Moodle** — автоматически открывается встроенный высокодетализированный Cycles PNG-растр (`mc:Fallback`), а вместо Morph срабатывает плавный `Fade`. Ни один слайд не «разваливается».
