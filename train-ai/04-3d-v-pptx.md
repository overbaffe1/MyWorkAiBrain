# 04. Как 3D-модель попадает в PowerPoint

pptxgenjs не умеет 3D-модели, поэтому схема такая: сначала pptxgenjs кладёт на место модели обычную **картинку-заглушку**
(PNG-рендер модели) с именем `MODEL::<id>::<имя>`, потом `pptx3d.js` открывает готовый pptx через JSZip и
**заменяет эту картинку на XML 3D-модели**. Код: `presentations/schumpeter/pptx3d.js`.

## 1. Файлы внутри pptx

* `.glb` кладётся в `ppt/media/model3dN.glb`.
* В `[Content_Types].xml`: `<Default Extension="glb" ContentType="model/gltf.binary"/>`.
* В `ppt/slides/_rels/slideK.xml.rels`:
  `<Relationship Id="rIdM3dN" Type="http://schemas.microsoft.com/office/2017/06/relationships/model3d" Target="../media/model3dN.glb"/>`.
* PNG-растр, который уже вставил pptxgenjs, переиспользуется (его `r:embed`).

## 2. XML модели на слайде

Модель — `mc:AlternateContent`: `mc:Choice Requires="am3d"` с `p:graphicFrame` для PowerPoint 2019+/365 и
`mc:Fallback` с обычной картинкой `p:pic` для всех остальных (Keynote, Google Slides, старые версии).

```xml
<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">
 <mc:Choice xmlns:am3d="http://schemas.microsoft.com/office/drawing/2017/model3d" Requires="am3d">
  <p:graphicFrame>
   <p:nvGraphicFramePr><p:cNvPr id="15" name="!!m-chest">…a16:creationId…</p:cNvPr>
     <p:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></p:cNvGraphicFramePr><p:nvPr/></p:nvGraphicFramePr>
   <p:xfrm><a:off x="…" y="…"/><a:ext cx="S" cy="S"/></p:xfrm>
   <a:graphic><a:graphicData uri="http://schemas.microsoft.com/office/drawing/2017/model3d">
    <am3d:model3d r:embed="rIdM3d1">
      <am3d:spPr> xfrm 0,0 S×S + prstGeom rect </am3d:spPr>
      <am3d:camera><am3d:pos x="0" y="0" z="CAMZ"/><am3d:up dx="0" dy="36000000" dz="0"/><am3d:lookAt x="0" y="0" z="0"/>
                   <am3d:perspective fov="2700000"/></am3d:camera>
      <am3d:trans><am3d:meterPerModelUnit n="MPU·1e6" d="1000000"/><am3d:preTrans dx dy dz = −center·MPU·36e6/>
                  <am3d:scale>1,1,1</am3d:scale><am3d:rot ax ay az (градусы·60000)/><am3d:postTrans 0,0,0/></am3d:trans>
      <am3d:raster rName="Office3DRenderer" rVer="16.0.8326"><am3d:blip r:embed="rIdPNG"/></am3d:raster>
      <am3d:extLst> …анимация, см. п. 4… </am3d:extLst>
      <am3d:objViewport viewportSz="S"/>
      <am3d:ambientLight>…</am3d:ambientLight>
      <am3d:ptLight>…×3 (тёплый ключевой, холодный контровой, заполняющий)</am3d:ptLight>
    </am3d:model3d>
   </a:graphicData></a:graphic>
  </p:graphicFrame>
 </mc:Choice>
 <mc:Fallback><p:pic> тот же cNvPr id и name, тот же PNG, тот же xfrm </p:pic></mc:Fallback>
</mc:AlternateContent>
```

На корневом `<p:sld>` объявляются `xmlns:mc`, `xmlns:am3d` и `mc:Ignorable="am3d"` (как делает сам PowerPoint).

### Математика камеры (чтобы модель целиком влезала в квадрат)

`glbBounds(buf)` читает JSON-чанк glb, берёт `min/max` POSITION-аксессоров и прогоняет 8 углов через иерархию узлов →
габариты `ext`, центр `center`, `maxExt`.

* `MPU = 1 / maxExt` — модель нормируется к размеру 1;
* `preTrans = −center · MPU` (в единицах 1/36 000 000 м — отсюда множитель `36e6`);
* `r = |ext / maxExt / 2|` — радиус описанной сферы нормированного бокса;
* `CAMZ = r / sin(22.5°) · 36e6`, `fov = 45°` (`2700000` = 45·60000).

Для skinned-моделей габариты берутся в позе покоя (вершины лежат в bind-пространстве) — поэтому анимация не должна
сильно выходить за габариты покоя (см. 03).

### Растр-заглушка (`models/render.py`)

Растр нужен трижды: как `am3d:raster` (PowerPoint показывает его до первой перерисовки), как fallback-картинка и в
HTML-превью. `render.py` воспроизводит ту же камеру: модель нормируется (`1/maxExt`, сдвиг на −center), перспектива 45°,
расстояние `r/sin(22.5°)`, квадратный кадр, поворот `rot` в осях glTF (X→X, Y→Z, Z→−Y). Cycles, прозрачный фон,
студийный HDRI для отражений + 3 area-лампы, AgX. Для анимированных моделей ставится первый кадр действия
(= постер). Объекты из коллекции `glTF_not_exported` (служебная икосфера формы костей, которую добавляет импортёр)
скрываются и не участвуют в кадрировании — иначе модель получается крошечной.
Растры кешируются по md5(glb + rot + px) в `models/rasters/`.

## 3. Правила, без которых PowerPoint ломается

* **Имена объектов на слайде уникальны.** Дубликат имени у model3d → PowerPoint молча удаляет модель.
* `id` у `graphicFrame` и fallback-`pic` одинаковый (это один объект в двух представлениях).
* Никакого Draco в glb.
* Порядок дочерних элементов `am3d:model3d` строгий: `spPr, camera, trans, raster, extLst, objViewport, ambientLight, ptLight…`.

## 4. Анимация модели: `embedAnim` + эффект «Сцена»

Формат взят из официального примера Open XML SDK (`samples/AnimatedModel3DExample`).

**а) В самой модели** (после `am3d:raster`) — какая анимация и сколько длится:

```xml
<am3d:extLst>
 <a:ext uri="{9A65AA19-BECB-4387-8358-8AD5134E1D82}">
  <a3danim:embedAnim xmlns:a3danim="http://schemas.microsoft.com/office/drawing/2018/animation/model3d" animId="0">
   <a3danim:animPr length="5000" count="indefinite"/>      <!-- length в мс -->
  </a3danim:embedAnim>
 </a:ext>
 <a:ext uri="{E9DE012E-A134-456F-84FE-255F9AAD75C6}">
  <a3danim:posterFrame xmlns:a3danim="…model3d" animId="0"/>
 </a:ext>
</am3d:extLst>
```

Длина определяется автоматически: `glbAnimMs(buf)` — максимум `accessors[sampler.input].max` по сэмплерам первой
анимации × 1000; если в glb нет `skins`, анимации считается нет (статичные модели не трогаются).

**б) В тайминге слайда** — эффект «Сцена» (presetID 100, класс emph), повтор до конца слайда, стартует вместе с
показом слайда (внутри главной последовательности, `withEffect`, или `afterEffect`, если других эффектов нет):

```xml
<p:par><p:cTn id="…" presetID="100" presetClass="emph" presetSubtype="1" repeatCount="indefinite" fill="hold" nodeType="withEffect">
 <p:stCondLst><p:cond delay="0"/></p:stCondLst>
 <p:childTnLst><p:anim calcmode="lin" valueType="num">
  <p:cBhvr><p:cTn id="…" dur="5000" fill="hold"/><p:tgtEl><p:spTgt spid="15"/></p:tgtEl>
           <p:attrNameLst><p:attrName>embedded1</p:attrName></p:attrNameLst></p:cBhvr>
  <p:tavLst><p:tav tm="0"><p:val><p:fltVal val="0"/></p:val></p:tav>
            <p:tav tm="100000"><p:val><p:fltVal val="1"/></p:val></p:tav></p:tavLst>
 </p:anim></p:childTnLst>
</p:cTn></p:par>
```

Обёртка тайминга стандартная: `tmRoot` → `seq mainSeq (concurrent=1, nextAc=seek)` → `par id=3` с условиями
`delay=indefinite` + `evt=onBegin` (`<p:tn val="2"/>`) → `par id=4 delay=0` → эффекты. Сцену получает только
видимая «главная» модель слайда (не призрачные копии для Morph, см. ниже).

В `build.js` ничего специально делать не нужно: если `.glb` анимирован, `injectModels` сам добавит `embedAnim`
и запишет `slides[i]._scenes`, а `injectTiming` вставит «Сцену». Отключить у конкретной модели: `s.model(key, {anim: false})`.

## 5. Появление элементов и Morph

* Элементы с `ag: N` (группа анимации) получают имя `fx…` и эффект «Возникновение + подъём» (fade + `ppt_y` от
  `#ppt_y+0.035`), группы стартуют с шагом 260 мс после 150 мс.
* Переход **Morph** на всех слайдах, кроме первого:
  `<mc:AlternateContent><mc:Choice Requires="p159"><p:transition spd="slow" p14:dur="1600"><p159:morph option="byObject"/></p:transition></mc:Choice><mc:Fallback><p:transition spd="slow"><p:fade/></p:transition></mc:Fallback></mc:AlternateContent>`
  — вставляется сразу после `</p:clrMapOvr>`.
* Morph сопоставляет объекты по имени. Имена, начинающиеся с `!!` (`!!title`, `!!coin`, `!!m-chest`), PowerPoint
  трактует как принудительное совпадение → элементы «перетекают» между слайдами.
* **Хореография экспонатов:** на слайд *i* добавляется «призрак» следующего экспоната за правым краем
  (`x = 13.33 + 0.6`, поворот `+80°`, прозрачный растр `clear.png`), а на слайд *i+1* — призрак предыдущего за левым краем
  (`x = −s − 0.6`, `−80°`). Morph интерполирует положение и 3D-поворот → модели влетают справа и улетают влево, крутясь.
* Жетон прогресса: 3D-луидор `!!coin` на верхней шкале, на каждом слайде сдвинут вправо и повернут на −146° — при Morph
  он «катится».

## 6. Дедупликация

pptxgenjs кладёт копию картинки на каждый слайд; `dedupeMedia` хеширует `ppt/media/*.png|jpg` (sha1), удаляет дубли
и переписывает ссылки в `.rels`. Фон и свечение хранятся один раз → файл 10 МБ вместо 30+.
