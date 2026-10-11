# ОСТРОВ ОГНЯ — один фан-слайд, живой целиком

Один слайд, пять 3D-моделей, 64 кости — всё анимировано, всё играет само.

| Модель | Кости | Что живёт | Петля |
|---|---|---|---|
| `volcano` | 40 | фонтан лавы, бомбы, дым, искры, кратерное озеро, потоки, пар, 3 пальмы, хижина, дракон (орбита, крылья, хвост, дыхание огнём), 7 букв INFERNO | 6 с |
| `torch` ×2 | 7+7 | трепещущее пламя, ядро, дым, искры | 4 с |
| `lavapool` ×2 | 5+5 | дышащая лава, растущие и лопающиеся пузыри | 4 с |

Всё смоделировано и анимировано кодом с нуля в Blender (bpy) — см. `models/make_models.py`.
Движок слайда общий (`../schumpeter`: `lib.js`, `pptx3d.js`).

## Сборка

```sh
python3 stage.py          # assets/stage-bg.jpg, glow.png, shadow.png, clear.png
node build.js             # -> ../../exports/fun-fire-island.pptx (+ -script.md)
node build.js --preview   # + preview/slide-01.png
```

Окружение Blender (pip `bpy` + стабы X11/GL, песочница без apt): `../schumpeter/setup_bpy.sh`.

## Файлы

| Путь | Что это |
|---|---|
| `build.js` | единственный слайд: вулкан-диорама + факелы и лава-чаши по краям |
| `stage.py` | генератор фоновых ассетов (ember-палитра) |
| `models/make_models.py` | процедурные модели → `models/glb/*.glb` |
| `models/gifcheck.py` | быстрая GIF-проверка анимаций (`GLB_DIR=... python3 gifcheck.py volcano`) |
| `models/glb/` | собранные модели (коммитятся) |
| `models/rasters/` | отрендеренные постер-кадры (коммитятся) |
| `preview/` | PNG-превью слайда + GIF анимаций |
