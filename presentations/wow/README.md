# «Три чуда» (3 слайда, 3 новые анимированные 3D-модели)

Три 3D-экспоната, созданные кодом с нуля специально для этой презентации
(`models/make_models.py`, Blender → `.glb` со скелетной анимацией):

| Модель | Кости | Что движется |
|---|---|---|
| `lighthouse` | 14 | два луча обходят горизонт (2 оборота/цикл), бегущие волны, пульс лампы, чайка |
| `carousel` | 5 | оборот всей карусели, три лошадки скачут вразнобой, светящиеся лампочки |
| `tornado` | 15 | шесть колец воронки на разных скоростях, три орбиты мусора, пыль, молния |

Движок сборки — `../schumpeter` (`lib.js`, `pptx3d.js`, `node_modules`);
монета-жетон `louis.glb` переиспользуется из коллекции cantillon.

```bash
bash ../tools/setup-env.sh                                  # один раз: Blender-окружение
LD_LIBRARY_PATH=/tmp/bstub python3 models/make_models.py    # .glb → models/glb
python3 stage.py                                            # фон и свечение → assets/
node build.js --preview                                     # → ../../exports/wow-3d-wonders.pptx + preview/
```
