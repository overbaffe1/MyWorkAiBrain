// Build: node build.js            ->  ../../exports/cantillon-3d-presentation.pptx (+ speaker script .md)
//        node build.js --preview  ->  also renders preview/slide-XX.png
//
// Same engine as the Schumpeter deck (../schumpeter: lib.js, pptx3d.js, models/render.py):
// every slide carries a real PowerPoint 3D model (am3d:model3d, .glb modelled in Blender, see models/),
// exhibits fly in/out with Morph, and a gold louis d'or of 1720 rolls along the progress track.
const path = require("path");
const fs = require("fs");
const crypto = require("crypto");
const { execSync } = require("child_process");
const SCH = path.join(__dirname, "..", "schumpeter");
const req = require("module").createRequire(path.join(SCH, "package.json"));
const { Slide, toPptx, toHtml } = require(path.join(SCH, "lib"));
const { injectModels, injectTiming, dedupeMedia } = require(path.join(SCH, "pptx3d"));

const A = (f) => path.join(__dirname, "assets", f);
const GOLD = "E3B663", GOLD2 = "F3DDAE", WHITE = "F5EFE6", MUTED = "BBAEA6", ACC = "E8866A",
  CARD = "22121A", DARK = "0D0709", FACT = "22170B";
const L = 0.75, R = 12.583, CW = R - L;
const SW = 13.333;
const slides = [];
const N = 10;
const TRACK_Y = 0.44;

// ---------- helpers ----------
function chrome(s, idx, kicker) {
  s.bg = "0E080A";
  s.img(A("stage-bg.jpg"), { x: 0, y: 0, w: SW, h: 7.5, name: "Background" });
  // progress track with a rolling gold louis d'or (3D) — position = progress through the deck
  s.line({ x1: L, y1: TRACK_Y, x2: R, y2: TRACK_Y, color: "FFFFFF", lineT: 84, width: 0.75, name: "!!track" });
  const gx = L + (CW * (idx - 1)) / (N - 1);
  if (gx - L > 0.01) s.rect({ x: L, y: TRACK_Y - 0.012, w: gx - L, h: 0.024, fill: GOLD, name: "!!progress" });
  const gs = 0.6;
  s.model("louis", { x: gx - gs / 2, y: TRACK_Y - 0.02 - gs / 2 - 0.012, s: gs, rot: [0, -12, -146 * (idx - 1)], name: "!!coin", px: 220 });
  if (kicker) {
    s.rect({ x: L, y: 0.78, w: 0.34, h: 0.035, fill: GOLD, name: "!!kickerbar" });
    s.text([{ text: kicker }], { x: L + 0.48, y: 0.65, w: 9, h: 0.3, size: 11, bold: true, color: GOLD, charSpacing: 3, name: "!!kicker" });
  }
  s.line({ x1: L, y1: 7.0, x2: R, y2: 7.0, color: "FFFFFF", lineT: 88, width: 0.75, name: "!!footline" });
  s.text("РИЧАРД КАНТИЛЬОН  ·  1680-е – 1734", { x: L, y: 7.1, w: 5, h: 0.25, size: 9, color: MUTED, charSpacing: 2, name: "!!footer" });
  s.text(`${String(idx).padStart(2, "0")} / ${N}`, { x: R - 1.5, y: 7.1, w: 1.5, h: 0.25, size: 9, color: MUTED, align: "right", charSpacing: 2, name: "!!pagenum" });
}

// 3D "exhibit": light pool + drafting rings + contact shadow + the model + a museum caption
function stage(s, key, o) {
  const { x, y, s: sz, rot } = o;
  const cx = x + sz / 2, cy = y + sz / 2 + (o.dy || 0);
  const g = sz * (o.glow || 1.45);
  s.img(A("glow.png"), { x: cx - g / 2, y: cy - g / 2, w: g, h: g, name: "!!glow" });
  const r1 = sz * 0.47, r2 = sz * 0.6;
  s.rect({ x: cx - r1, y: cy - r1, w: 2 * r1, h: 2 * r1, shape: "ellipse", line: GOLD, lineT: 82, lineW: 0.75, name: "!!ring1" });
  s.rect({ x: cx - r2, y: cy - r2, w: 2 * r2, h: 2 * r2, shape: "ellipse", line: GOLD, lineT: 88, lineW: 0.75, dash: "dash", name: "!!ring2" });
  const shw = sz * (o.shw || 0.78), shy = y + sz * (o.shy || 0.8);
  s.img(A("shadow.png"), { x: cx - shw / 2, y: shy - shw / 8, w: shw, h: shw / 4, name: "!!shadow" });
  s.model(key, { x, y, s: sz, rot, name: `!!m-${key}`, px: o.px });
  s.hero = { key, x, y, s: sz, rot };
  if (o.caption) {
    const [no, t] = o.caption;
    const cw = o.cw || 3.6, capY = o.capY ?? y + sz * 0.93;
    const capX = o.capX ?? cx - cw / 2;
    s.text([{ text: `ЭКСПОНАТ ${no}`, options: { bold: true, color: GOLD, charSpacing: 2.5, breakLine: true } },
      { text: t, options: { color: MUTED } }],
    { x: capX, y: capY, w: cw, h: 0.5, size: 9, align: o.capAlign || "center", lineSpacingMultiple: 1.1, ag: 9 });
  }
}

const title = (s, t, o = {}) =>
  s.text(t, { x: L, y: o.y ?? 1.08, w: o.w ?? 6.6, h: o.h ?? 1.3, font: "head", size: o.size ?? 36, color: WHITE, lineSpacingMultiple: 0.95, name: "!!title", valign: "top" });
const label = (s, t, x, y, w, color = GOLD, ag) =>
  s.text(t, { x, y, w, h: 0.25, size: 9.5, bold: true, color, charSpacing: 2, ag });
const card = (s, x, y, w, h, o = {}) =>
  s.rect({ x, y, w, h, fill: o.fill || CARD, fillT: o.fillT ?? 22, line: o.line || GOLD, lineT: o.lineT ?? 72, lineW: 0.75, radius: o.radius ?? 0.08, shadow: o.shadow, ag: o.ag });
const br = (text, o = {}) => ({ text, options: { ...o, breakLine: true } });
const run = (text, o = {}) => ({ text, options: o });

// "the most interesting fact" — the same component on every slide
function fact(s, x, y, w, h, body, o = {}) {
  const ag = o.ag ?? 8;
  const tag = o.tag || "САМОЕ ИНТЕРЕСНОЕ";
  s.rect({ x, y, w, h, fill: FACT, fillT: 8, line: GOLD, lineT: 45, lineW: 1, radius: 0.08, shadow: true, ag });
  s.rect({ x, y: y + 0.16, w: 0.055, h: h - 0.32, fill: GOLD, ag });
  const tw = 0.105 * tag.length + 0.5;
  s.rect({ x: x + 0.28, y: y - 0.15, w: tw, h: 0.3, fill: GOLD, radius: 0.15, ag });
  s.text("★  " + tag, { x: x + 0.28, y: y - 0.15, w: tw, h: 0.3, size: 8.5, bold: true, color: DARK, charSpacing: 1.5, align: "center", valign: "middle", ag });
  const runs = typeof body === "string" ? [run(body)] : body;
  s.text(runs, { x: x + 0.3, y: y + 0.2, w: w - 0.5, h: h - 0.3, font: "head", italic: true, size: o.size || 13.5, color: WHITE, valign: "middle", lineSpacingMultiple: 1.05, ag });
}

// numbered rows: [[head, sub], …]
function rows(s, items, o) {
  const { x = L, y0, step, w = 6.0, ag0 = 1, numW = 0.65, head = 14, sub = 11.5, nums } = o;
  items.forEach(([t, d], i) => {
    const y = y0 + i * step, ag = ag0 + i;
    s.text(nums ? nums[i] : String(i + 1).padStart(2, "0"), { x, y: y - 0.04, w: numW + 0.4, h: 0.4, font: "head", size: 18, color: GOLD, ag });
    s.text(t, { x: x + numW, y, w, h: 0.3, size: head, bold: true, color: WHITE, ag });
    s.text(d, { x: x + numW, y: y + 0.3, w, h: step - 0.3, size: sub, color: MUTED, lineSpacingMultiple: 1.03, ag });
  });
}

// =====================================================================
// 1. TITLE
{
  const s = new Slide({ notes:
`Сегодня я расскажу о Ричарде Кантильоне — ирландско-французском банкире XVIII века. Его имя знают меньше, чем имя Адама Смита, но именно он первым описал в экономической теории фигуру предпринимателя.
Самое интересное: само французское слово entrepreneur существовало и раньше, но именно Кантильон, примерно в 1730 году, первым сделал предпринимателя центральной фигурой экономической теории. Это часто приписывают Жан-Батисту Сэю, но Сэй писал на семьдесят лет позже.
А ещё его жизнь — готовый сюжет для сериала: миллионы на финансовом пузыре, угроза Бастилией и загадочная смерть, которую до сих пор не могут объяснить.
Каждый слайд сопровождает «экспонат» — 3D-предмет, связанный с его жизнью или идеями. И они не просто стоят: в каждом экспонате что-то движется. Первый — торговый корабль: он идёт по волнам, паруса дышат, вымпел полощется, а над мачтами кружит чайка. Это риск, морская торговля и, возможно, бегство за океан.
План: где он родился, чем занимался, его главная мысль и что он дал теории предпринимательства.` });
  chrome(s, 1, "ЭКОНОМИКА  ·  РИСК  ·  ПРЕДПРИНИМАТЕЛЬСТВО");
  stage(s, "ship", { x: 5.85, y: 0.65, s: 7.3, rot: [6, -34, 0], px: 1150, shy: 0.86, shw: 0.8, caption: ["01", "Корабль идёт по волнам, над мачтами кружит чайка"], capX: 8.6, capY: 1.3, cw: 4.0, capAlign: "right" });
  s.text([br("Ричард", { color: GOLD2, size: 52 }), run("Кантильон", { size: 72 })],
    { x: L, y: 1.25, w: 7, h: 2.5, font: "head", color: WHITE, lineSpacingMultiple: 0.92, name: "!!title" });
  s.rect({ x: L, y: 3.92, w: 1.1, h: 0.04, fill: GOLD, ag: 1 });
  s.text("Банкир-миллионер, который первым описал предпринимателя — и исчез при загадочных обстоятельствах",
    { x: L, y: 4.1, w: 5.9, h: 1.0, font: "head", italic: true, size: 18, color: WHITE, lineSpacingMultiple: 1.05, ag: 1 });
  s.text("1680-е — 1734   ·   ИРЛАНДИЯ → ПАРИЖ → ЛОНДОН", { x: L, y: 5.22, w: 6.4, h: 0.3, size: 12, color: MUTED, charSpacing: 2.5, bold: true, ag: 2 });
  fact(s, L, 5.85, 5.6, 0.92, [run("Предпринимателя "), run("центральной фигурой экономики", { bold: true }), run(" первым сделал он — примерно за 70 лет до Сэя, которому это часто приписывают.")], { size: 12.5 });
  slides.push(s);
}

// 2. BIRTH
{
  const s = new Slide({ notes:
`Ричард Кантильон родился в 1680-х годах в графстве Керри на юго-западе Ирландии, в католической дворянской семье. Его род потерял земли при конфискациях Кромвеля и Вильгельма Оранского — и, как многие ирландские католики, молодой Кантильон уехал во Францию. В 1708 году он получил французское подданство.
В семье были банкиры: двоюродный брат вёл банк в Париже — позже это станет стартом его карьеры. Он свободно жил между английским и французским мирами, а главную книгу написал по-французски.
Экспонат — ирландская арфа, символ его родины: по струнам пробегает глиссандо, каждая струна дрожит, и из неё вылетают ноты.
А вот самое интересное: мы не знаем ни точной даты его рождения, ни даже того, как он выглядел. Достоверных портретов нет. Есть лишь гипотеза экономиста Марка Торнтона, что Кантильон — мужчина слева на семейном портрете кисти Николя де Ларжильера, около 1710 года. Атрибуция спорная, поэтому я показываю его со знаком вопроса.` });
  chrome(s, 2, "01 — ГДЕ РОДИЛСЯ");
  stage(s, "harp", { x: 8.2, y: 0.95, s: 4.8, rot: [6, -26, 0], px: 780, shy: 0.86, shw: 0.62, caption: ["02", "Арфа: глиссандо по струнам — и ноты взлетают"], cw: 3.9 });
  title(s, "Ирландец из графства Керри", { size: 33 });
  const facts = [
    ["РОДИЛСЯ", "1680-е годы", "графство Керри, Ирландия"],
    ["СЕМЬЯ", "Католики-дворяне", "лишились земель при Кромвеле"],
    ["ПЕРЕЕЗД", "Франция", "французское подданство — 1708"],
    ["РОДНЯ", "Банкиры", "двоюродный брат вёл банк в Париже"],
  ];
  facts.forEach(([l, v, sub], i) => {
    const x = L + (i % 2) * 3.3, y = 2.3 + Math.floor(i / 2) * 1.1, w = 3.15, h = 0.98;
    const ag = 1 + Math.floor(i / 2);
    card(s, x, y, w, h, { ag });
    s.rect({ x, y: y + 0.18, w: 0.045, h: h - 0.36, fill: GOLD, ag });
    label(s, l, x + 0.25, y + 0.13, w - 0.35, GOLD, ag);
    s.text(v, { x: x + 0.25, y: y + 0.36, w: w - 0.35, h: 0.34, font: "head", size: 16.5, color: WHITE, ag });
    s.text(sub, { x: x + 0.25, y: y + 0.68, w: w - 0.35, h: 0.25, size: 10.5, color: MUTED, ag });
  });
  // the only candidate likeness: Largillière's family portrait (identification disputed)
  const px0 = L, py0 = 4.6, pw = 2.45, ph = pw / 1.369;
  s.rect({ x: px0 - 0.07, y: py0 - 0.07, w: pw + 0.14, h: ph + 0.14, fill: "2A1A0C", line: GOLD, lineW: 1.5, shadow: true, ag: 3 });
  s.img(A("largilliere-family.jpg"), { x: px0, y: py0, w: pw, h: ph, ag: 3 });
  s.text([run("Н. де Ларжильер, ок. 1710. ", { color: MUTED }), run("Кантильон слева?", { color: GOLD, bold: true })],
    { x: px0 - 0.07, y: py0 + ph + 0.1, w: pw + 0.5, h: 0.25, size: 9, ag: 3 });
  fact(s, L + 2.75, 4.68, 3.75, 1.95, [run("Мы не знаем ни точной даты его рождения, ни "), run("как он выглядел", { bold: true }), run(": достоверных портретов нет. Есть лишь гипотеза (М. Торнтон, 2018), что он — мужчина на семейном портрете Ларжильера.")], { size: 12.5, tag: "ЗАГАДКА № 1", ag: 4 });
  slides.push(s);
}

// 3. CAREER — banker, financier, speculator (+ his European network)
{
  const s = new Slide({ notes:
`Чем он занимался? Если коротко — деньгами. Около 1711 года он в Испании, во время войны за испанское наследство, работает на британского генерального казначея Джеймса Бриджеса: организует выплаты британским военнопленным. Так появляются связи и покровитель.
В 1714 году он возвращается в Париж и начинает в банке двоюродного брата, а в 1716-м при поддержке Бриджеса выкупает банк и становится хозяином. Его клиенты — двор изгнанных Стюартов, ирландские и британские эмигранты, поэт Александр Поуп, политик Болингброк.
И наконец — спекулянт: на пузыре Миссисипской компании он заработает огромное состояние. По завещанию 1732 года видно, насколько он был богат и осторожен: деньги на депозитах в банках Лондона, Амстердама, Брюсселя, Вены и Кадиса, поместья — в Англии и во французской Луизиане.
Экспонат — окованный сундук: смотрите, ключ поворачивается и крышка открывается. Самое интересное: уезжая из Парижа, Кантильон запер все бумаги в сундук и оставил его на хранение английским монахам-бенедиктинцам — переждать «финансовую бурю», которую он предвидел.` });
  chrome(s, 3, "02 — ЧЕМ ЗАНИМАЛСЯ");
  stage(s, "chest", { x: 8.1, y: 1.05, s: 4.9, rot: [16, -28, 0], px: 780, shy: 0.76, caption: ["03", "Сундук открывается: ключ, бумаги, луидоры"], cw: 3.9 });
  title(s, "Банкир, финансист, спекулянт", { w: 7.6, h: 0.8, size: 32 });
  const roles = [
    ["I", "Агент казначейства · 1711", "В Испании организует выплаты британским пленным. Покровитель — казначей Джеймс Бриджес."],
    ["II", "Парижский банкир · 1714–1716", "Начинает в банке кузена, а в 1716-м выкупает его и становится хозяином."],
    ["III", "Банкир изгнанников", "Двор Стюартов, ирландские эмигранты, поэт Поуп, политик Болингброк."],
    ["IV", "Спекулянт · 1719–1720", "Состояние на пузыре Миссисипи. Деньги — в банках Лондона, Амстердама, Вены и Кадиса."],
  ];
  roles.forEach(([n, t, d], i) => {
    const x = L + (i % 2) * 3.68, y = 2.15 + Math.floor(i / 2) * 1.68, w = 3.53, h = 1.54, ag = 1 + i;
    card(s, x, y, w, h, { fillT: 15, ag });
    s.text(n, { x: x + 0.22, y: y + 0.14, w: 0.7, h: 0.45, font: "head", size: 22, color: GOLD, ag });
    s.text(t, { x: x + 0.8, y: y + 0.2, w: w - 0.95, h: 0.35, size: 13, bold: true, color: WHITE, ag });
    s.text(d, { x: x + 0.22, y: y + 0.66, w: w - 0.4, h: 0.82, size: 11, color: MUTED, lineSpacingMultiple: 1.05, ag });
  });
  fact(s, L, 5.75, 7.21, 1.02, [run("Уезжая из Парижа, он "), run("запер все бумаги в сундук", { bold: true }), run(" и оставил его на хранение английским монахам-бенедиктинцам — переждать «финансовую бурю».")], { size: 12.5 });
  slides.push(s);
}

// 4. MISSISSIPPI BUBBLE + the duel with John Law
{
  const s = new Slide({ notes:
`Главная финансовая история его жизни — пузырь Миссисипи. В 1716 году шотландец Джон Ло убеждает регента Франции, что бумажные деньги решат проблему огромного государственного долга, и открывает банк. Затем появляется Миссисипская компания — монополия на освоение французской Луизианы. Её акции за пару лет взлетают примерно в двадцать раз.
Кантильон считал систему Ло обречённой — и именно поэтому на ней заработал: купил рано, продал дорого, а клиентам давал кредиты под залог акций. Когда в 1720 году пузырь лопнул, он стал одним из «миссисипских миллионеров» — около двадцати миллионов ливров.
Экспонат — пузырь над стопкой акций: он раздувается, лопается, бумаги взлетают — и всё начинается снова.
Самое интересное — «дуэль» с Ло. По рассказу барона Гримма, Ло пригрозил: «Я могу сегодня же вечером отправить вас в Бастилию, если вы не покинете королевство». Кантильон подумал и ответил: «Хорошо. Я не уеду — и помогу вашей системе преуспеть». Взял массу новых бумаг, выгодно разместил их, обменял на золото — и всё-таки уехал. Это рассказ современника, его стоит подавать как легенду. Итог: Ло умер в 1729 году в Венеции разорённым, а Кантильон остался мультимиллионером.` });
  chrome(s, 4, "03 — ПУЗЫРЬ И ДУЭЛЬ С ДЖОНОМ ЛО");
  stage(s, "bubble", { x: 8.25, y: 0.95, s: 4.7, rot: [14, -24, 0], px: 760, shy: 0.82, shw: 0.7, caption: ["04", "Пузырь раздувается, лопается — и растёт снова"], cw: 3.8 });
  title(s, "Пузырь Миссисипи: как он разбогател", { w: 7.4, size: 32 });
  rows(s, [
    ["Банк Джона Ло · 1716", "Шотландец убеждает регента: бумажные деньги спасут Францию от долгов."],
    ["Миссисипская компания · 1717–1719", "Монополия на Луизиану; акции дорожают примерно в 20 раз."],
    ["Ход Кантильона", "Считает систему обречённой: покупает рано, продаёт дорого, кредитует под залог."],
    ["Крах · 1720", "Пузырь лопается — а у него ≈ 20 млн ливров (порядка €60 млн сегодня)."],
  ], { y0: 2.42, step: 0.78, w: 6.3, nums: ["I", "II", "III", "IV"] });
  fact(s, L, 5.62, 7.0, 1.16, [run("Ло: «Я могу сегодня же отправить вас в Бастилию». Кантильон: "), run("«Хорошо. Я не уеду — и помогу вашей системе»", { bold: true }), run(". Нажился на ней — и всё равно уехал.")], { size: 12.5, tag: "ДУЭЛЬ С ДЖОНОМ ЛО" });
  slides.push(s);
}

// 7. ESSAI
{
  const s = new Slide({ notes:
`Главный труд Кантильона — «Опыт о природе торговли вообще», по-французски «Essai sur la nature du commerce en général». Он написан примерно в 1730 году и считается первым систематическим трактатом, который охватывает экономику целиком: производство, деньги, цены, процент, международную торговлю.
История книги — сама по себе детектив. Она вышла только в 1755 году, через двадцать один год после смерти автора, анонимно, с фальшивым адресом «Лондон, у Флетчера Джайлса» и пометкой «переведено с английского». В рукописи её успели прочитать французские экономисты — физиократы.
Адам Смит в «Богатстве народов» 1776 года ссылается на Кантильона — это один из немногих авторов, которых Смит вообще цитирует. Потом книгу забыли почти на сто лет, пока в 1881 году Стэнли Джевонс не открыл её заново и не назвал «колыбелью политической экономии».
Экспонат — раскрытая книга: страницы листаются сами, а перо макается в чернильницу.
Самое интересное: Шумпетер — тот самый, про которого другая презентация, — назвал «Essai» «первым систематическим проникновением в область экономики». А статистическое приложение к книге потеряно до сих пор.` });
  chrome(s, 5, "04 — ГЛАВНЫЙ ТРУД");
  stage(s, "quill", { x: 7.8, y: 1.05, s: 5.0, rot: [20, -24, 0], px: 800, shy: 0.78, caption: ["05", "Страницы «Essai» листаются сами, перо макает чернила"] });
  title(s, "Книга, опередившая Адама Смита", { w: 6.9 });
  const works = [
    ["≈1730", "Написан «Essai sur la nature du commerce»", "Первый трактат об экономике целиком: цены, деньги, процент, торговля."],
    ["1755", "Издан через 21 год после смерти автора", "Анонимно, с фальшивым адресом «Лондон» и пометкой «перевод с английского»."],
    ["1776", "Адам Смит ссылается на Кантильона", "Один из немногих авторов, которых цитирует «Богатство народов»."],
    ["1881", "Джевонс открывает книгу заново", "И называет её «колыбелью политической экономии»."],
  ];
  works.forEach(([yr, t, d], i) => {
    const y = 2.45 + i * 0.84, ag = 1 + i;
    if (i) s.line({ x1: L, y1: y - 0.12, x2: L + 6.6, y2: y - 0.12, color: "FFFFFF", lineT: 85, width: 0.75, ag });
    s.text(yr, { x: L, y: y - 0.02, w: 1.35, h: 0.45, font: "head", size: 21, color: GOLD, ag });
    s.text(t, { x: L + 1.4, y, w: 5.4, h: 0.34, font: "head", size: 14.5, color: WHITE, bold: true, ag });
    s.text(d, { x: L + 1.4, y: y + 0.37, w: 5.3, h: 0.32, size: 11, color: MUTED, ag });
  });
  fact(s, L, 5.9, 6.7, 0.88, [run("Шумпетер назвал «Essai» "), run("«первым систематическим проникновением в область экономики»", { bold: true }), run(". А статистическое приложение к книге потеряно.")], { size: 12.5 });
  slides.push(s);
}

// 8. MAIN IDEA — three classes
{
  const s = new Slide({ notes:
`Главная мысль Кантильона: экономика — это система, которая сама себя регулирует через рынки, цены и деньги. Не государство и не казна, а миллионы решений людей определяют, что производится и по какой цене.
В этой системе он выделил три группы. Землевладельцы — независимы, их расходы задают спрос. Наёмные работники живут на фиксированном доходе. И предприниматели — все, чей доход заранее неизвестен: они покупают по известной цене, а продают по неизвестной. Именно они подстраивают производство под спрос.
Экспонат — весы: коромысло само качается и ищет равновесие, как рынок. На одной чаше монеты — известный доход, на другой — игральная кость: доход неизвестный.
Самое парадоксальное: у Кантильона генерал на жалованье — наёмный работник, а трубочист и водонос — предприниматели. Важен не размер дохода и не статус, а то, известен ли доход заранее.` });
  chrome(s, 6, "05 — ГЛАВНАЯ МЫСЛЬ");
  stage(s, "scales", { x: 8.35, y: 0.95, s: 4.8, rot: [8, -18, 0], px: 780, shy: 0.86, shw: 0.6, caption: ["06", "Весы сами ищут равновесие — как рынок"], cw: 3.6 });
  title(s, "Экономика — система, а не казна", { w: 7.6, h: 0.8, size: 31 });
  s.text("Рынки, цены и деньги регулируют хозяйство сами. Всё общество — три группы:", { x: L, y: 1.9, w: 7.4, h: 0.35, size: 13, color: MUTED, ag: 1 });
  const cols = [
    ["ЗЕМЛЕВЛАДЕЛЬЦЫ", "Независимы", "Их расходы задают спрос всей экономики.", false],
    ["НАЁМНЫЕ", "Фиксированный доход", "Генерал на жалованье, придворный с пенсией, слуга с зарплатой.", false],
    ["ПРЕДПРИНИМАТЕЛИ", "Неизвестный доход", "Покупают по известной цене, продают по неизвестной.", true],
  ];
  const cw = 2.35;
  cols.forEach(([l, h, d, hi], i) => {
    const x = L + i * (cw + 0.15), y = 2.45, ag = 2 + i;
    card(s, x, y, cw, 2.75, { line: hi ? GOLD : "9A8C86", lineT: hi ? 30 : 70, fillT: hi ? 0 : 12, fill: hi ? "2E1E10" : CARD, ag });
    label(s, l, x + 0.2, y + 0.2, cw - 0.3, hi ? GOLD : MUTED, ag);
    s.text(h, { x: x + 0.2, y: y + 0.5, w: cw - 0.35, h: 0.75, font: "head", size: 18, color: WHITE, lineSpacingMultiple: 0.95, ag });
    s.text(d, { x: x + 0.2, y: y + 1.3, w: cw - 0.35, h: 1.3, size: 11.5, color: MUTED, lineSpacingMultiple: 1.05, ag });
  });
  fact(s, L, 5.65, 7.35, 1.1, [run("Парадокс Кантильона: "), run("генерал на жалованье — наёмный работник, а трубочист и водонос — предприниматели", { bold: true }), run(". Важно лишь, известен ли доход заранее.")], { size: 13, tag: "ПАРАДОКС" });
  slides.push(s);
}

// 9. ENTREPRENEUR
{
  const s = new Slide({ notes:
`Теперь главное для нашей темы — кто такой предприниматель у Кантильона. Его определение очень простое: предприниматель платит известную цену сегодня, чтобы продать по неизвестной цене завтра. Между этими двумя ценами — неопределённость: никто не знает, каким будет спрос, сколько продержатся клиенты и что сделают конкуренты. Если угадал — прибыль, если нет — банкротство.
Экспонат — игральные кости, которые всё время катятся, и монета-ставка, крутящаяся волчком: результат заранее не знает никто. Прибыль — плата за взятую неопределённость, убыток — её цена.
Отсюда очень широкий список: фермер, оптовик, пекарь, мясник, трактирщик, купец, а ещё — трубочист, водонос, швея, художник, врач, адвокат. Все, кто живёт «в неопределённости».
И самая удивительная фраза из книги: «…даже нищие и грабители — предприниматели этого класса». Для Кантильона важна не мораль и не размер дела, а только одно — неопределённость дохода.` });
  chrome(s, 7, "06 — ПРЕДПРИНИМАТЕЛЬ ПО КАНТИЛЬОНУ");
  stage(s, "dice", { x: 8.6, y: 1.2, s: 4.2, rot: [18, -24, 0], px: 680, shy: 0.76, shw: 0.7, caption: ["07", "Кости катятся, ставка крутится волчком"] });
  title(s, "Купить по известной цене, продать — по неизвестной", { size: 31, w: 7.3 });
  const bx = [["СЕГОДНЯ", "Известная цена", "платит за сырьё, товар, труд"], ["МЕЖДУ НИМИ", "Неопределённость", "спрос, клиенты, конкуренты"], ["ЗАВТРА", "Неизвестная цена", "прибыль — или банкротство"]];
  const bw = 2.25;
  bx.forEach(([l, t, d], i) => {
    const x = L + i * (bw + 0.3), y = 2.38, ag = 1 + i, hi = i === 1;
    card(s, x, y, bw, 1.3, { line: hi ? ACC : GOLD, lineT: hi ? 35 : 65, fillT: 10, ag });
    label(s, l, x + 0.2, y + 0.14, bw - 0.3, hi ? ACC : GOLD, ag);
    s.text(t, { x: x + 0.2, y: y + 0.42, w: bw - 0.3, h: 0.4, font: "head", size: 13.5, color: WHITE, ag });
    s.text(d, { x: x + 0.2, y: y + 0.84, w: bw - 0.3, h: 0.4, size: 10.5, color: MUTED, ag });
    if (i < 2) s.text("→", { x: x + bw, y: y + 0.38, w: 0.3, h: 0.5, font: "head", size: 20, color: GOLD, align: "center", ag });
  });
  label(s, "КТО ЖИВЁТ «В НЕОПРЕДЕЛЁННОСТИ» — ПРИМЕРЫ ИЗ КНИГИ", L, 3.92, 7.2, GOLD, 4);
  const ex = ["фермер", "оптовик", "пекарь", "мясник", "трактирщик", "купец", "трубочист", "водонос", "швея", "художник", "врач", "адвокат"];
  ex.forEach((t, i) => {
    const x = L + (i % 6) * 1.21, y = 4.22 + Math.floor(i / 6) * 0.5, ag = 4 + Math.floor(i / 6);
    s.rect({ x, y, w: 1.13, h: 0.38, fill: CARD, fillT: 15, line: "9A8C86", lineT: 55, radius: 0.19, ag });
    s.text(t, { x, y, w: 1.13, h: 0.38, size: 11, color: WHITE, align: "center", valign: "middle", ag });
  });
  fact(s, L, 5.65, 7.3, 1.12, [br("«…даже нищие и грабители — предприниматели этого класса».", { size: 16 }),
    run("— «Essai», ч. I, гл. XIII", { size: 10.5, italic: false, color: MUTED })], { tag: "ЦИТАТА, КОТОРАЯ УДИВЛЯЕТ" });
  slides.push(s);
}

// 11. CANTILLON EFFECT
{
  const s = new Slide({ notes:
`Вторая большая идея Кантильона — его именем её и назвали: эффект Кантильона. Он наблюдал пузырь Ло изнутри и понял: новые деньги не распределяются по экономике равномерно, как вода в ванне. Они входят в конкретной точке — и расходятся кругами. Экспонат — монета падает в воду, и по ней расходятся круги.
Механизм такой. Появляются новые деньги — от нового рудника, печатного станка или кредита. Первые получатели тратят их по старым ценам и выигрывают. Цены растут на то, что покупают именно они. А те, к кому деньги приходят последними, — получают их уже после роста цен и проигрывают.
Пример самого Кантильона: если открыли новые серебряные рудники, разбогатевшие шахтёры начинают есть больше мяса и пить вино вместо пива — мясо и вино дорожают, и фермеры переводят землю под скот и виноградники. Деньги меняют не только уровень цен, но и структуру всей экономики.
Самое интересное: термин жив и сегодня. Эффектом Кантильона объясняют, почему от печатания денег центробанками раньше всех выигрывают банки и владельцы активов, а люди с фиксированным доходом — проигрывают.` });
  chrome(s, 8, "07 — ЭФФЕКТ КАНТИЛЬОНА");
  stage(s, "ripple", { x: 8.3, y: 1.1, s: 4.6, rot: [26, -10, 0], px: 760, shy: 0.74, shw: 0.85, caption: ["08", "Монета падает в воду — и расходятся круги"] });
  title(s, "Кто первым получает новые деньги — выигрывает", { w: 7.4, size: 32 });
  const chain = [
    ["Новые деньги", "рудник, печатный станок, кредит"],
    ["Первые", "получатели тратят по старым ценам — выигрывают"],
    ["Рост цен", "дорожает то, что покупают именно они"],
    ["Последние", "получают деньги после роста цен — проигрывают"],
  ];
  const cw4 = (7.4 - 0.45) / 4;
  chain.forEach(([t, d], i) => {
    const x = L + i * (cw4 + 0.15), y = 2.45, h = 1.75, ag = 1 + i;
    const last = i === 3;
    s.rect({ x, y, w: cw4, h, fill: last ? "2A1210" : CARD, fillT: 5, line: last ? ACC : GOLD, lineT: last ? 40 : 70, radius: 0.08, shadow: true, ag });
    s.rect({ x: x + cw4 / 2 - 0.22, y: y + 0.18, w: 0.44, h: 0.44, shape: "ellipse", line: last ? ACC : GOLD, lineW: 1.25, fill: DARK, ag });
    s.text(String(i + 1), { x: x + cw4 / 2 - 0.22, y: y + 0.18, w: 0.44, h: 0.44, font: "head", size: 15, color: last ? ACC : GOLD, align: "center", valign: "middle", ag });
    s.text(t, { x: x + 0.12, y: y + 0.72, w: cw4 - 0.24, h: 0.3, size: 12.5, bold: true, color: WHITE, align: "center", ag });
    s.text(d, { x: x + 0.12, y: y + 1.02, w: cw4 - 0.24, h: 0.7, size: 10, color: MUTED, align: "center", lineSpacingMultiple: 1.05, ag });
  });
  s.text([run("Пример из «Essai»: ", { bold: true, color: GOLD }), run("новое серебро → шахтёры едят больше мяса и пьют вино → фермеры переводят землю под скот и виноградники.", { color: WHITE })],
    { x: L, y: 4.38, w: 7.4, h: 0.75, size: 12, lineSpacingMultiple: 1.05, ag: 5 });
  fact(s, L, 5.65, 7.4, 1.1, [run("Термин жив и сегодня: «эффектом Кантильона» объясняют, почему от печатания денег центробанками "), run("раньше всех выигрывают банки и владельцы активов", { bold: true }), run(".")], { size: 12.5 });
  slides.push(s);
}

// 12. CONTRIBUTION TO ENTREPRENEURSHIP
{
  const s = new Slide({ notes:
`Итак, что Кантильон дал теории предпринимательства. Первое: он ввёл само понятие и сделал предпринимателя центральной фигурой экономики, а не просто «торговцем». Второе: определил его функцию — нести неопределённость; это не капитал и не профессия, а доход «по неизвестной цене». Третье: показал, что предприниматели координируют рынок — подстраивают предложение под спрос и связывают рынки разных мест.
С этого начинается эстафета идей, которую можно проследить до наших дней. Кантильон, около 1730 года: предприниматель несёт риск. Сэй, 1803: предприниматель — организатор производства. Шумпетер, 1911: предприниматель — новатор, который осуществляет новые комбинации. Найт, 1921: прибыль — награда за неизмеримую неопределённость. Кирцнер, 1973: предприниматель — тот, кто первым замечает возможность.
Экспонат — компас: его встряхивает, стрелка мечется — и снова находит север. Инструмент для движения в неопределённости.
Самое интересное: американский экономист Мюррей Ротбард назвал Кантильона «отцом-основателем современной экономики» — то есть поставил его раньше Адама Смита.` });
  chrome(s, 9, "08 — ВКЛАД В ПРЕДПРИНИМАТЕЛЬСТВО");
  stage(s, "compass", { x: 9.75, y: 0.15, s: 2.95, rot: [6, -20, 0], px: 520, glow: 1.3, shy: 0.86, shw: 0.6, caption: ["09", "Толчок — и стрелка снова находит север"], capX: 7.0, capY: 1.0, cw: 2.65, capAlign: "right" });
  title(s, "С него началась теория предпринимателя", { w: 6.2, h: 1.3, size: 33 });
  const pts = [
    ["Ввёл само понятие", "Предприниматель — центральная фигура экономики."],
    ["Функция — нести неопределённость", "Не капитал и не профессия, а доход «по неизвестной цене»."],
    ["Предприниматель координирует рынок", "Подстраивает предложение под спрос и связывает рынки."],
  ];
  rows(s, pts, { y0: 2.42, step: 0.7, w: 10.5, head: 14, sub: 11.5 });
  // relay of ideas
  const relay = [
    ["Кантильон", "≈1730", "несёт риск", true],
    ["Сэй", "1803", "организатор производства"],
    ["Шумпетер", "1911", "новатор, новые комбинации"],
    ["Найт", "1921", "неопределённость и прибыль"],
    ["Кирцнер", "1973", "бдительность к возможностям"],
  ];
  label(s, "ЭСТАФЕТА ИДЕЙ", L, 4.62, 4, GOLD, 4);
  const rw = CW / 5, ry = 5.08;
  s.line({ x1: L + rw / 2, y1: ry, x2: R - rw / 2, y2: ry, color: GOLD, lineT: 40, width: 1.5, ag: 4 });
  relay.forEach(([n, y, d, hi], i) => {
    const cx = L + rw * (i + 0.5), ag = 4 + Math.floor(i / 2);
    s.rect({ x: cx - 0.11, y: ry - 0.11, w: 0.22, h: 0.22, shape: "ellipse", fill: hi ? GOLD : DARK, line: GOLD, lineW: 2, ag });
    s.text([run(n + "  ", { bold: true, color: hi ? GOLD : WHITE, size: 13 }), run(y, { color: GOLD, size: 12 })], { x: cx - rw / 2, y: ry + 0.17, w: rw, h: 0.3, align: "center", ag });
    s.text(d, { x: cx - rw / 2 + 0.1, y: ry + 0.47, w: rw - 0.2, h: 0.3, size: 10.5, color: MUTED, align: "center", ag });
  });
  fact(s, L, 6.08, 7.2, 0.72, [run("Мюррей Ротбард назвал его "), run("«отцом-основателем современной экономики»", { bold: true }), run(" — раньше Адама Смита.")], { size: 12.5, ag: 7 });
  slides.push(s);
}

// 10. THE FIRE — murdered or escaped? + finale
{
  const s = new Slide({ notes:
`И самая загадочная часть. 14 мая 1734 года, около трёх часов ночи, в лондонском доме Кантильона на Албемарл-стрит начинается пожар. Сгорает его дом и два соседних. В постели находят обгоревшее тело. В доме, по сообщениям, было ценностей на двести тысяч фунтов; повар-француз, уволенный за три недели до этого, бежал за море под чужим именем. Трёх слуг судили за убийство и поджог — и в декабре оправдали.
Экспонат — свеча: пламя дрожит, вьётся дымок, по свече ползёт капля воска, а вокруг огня кружит мотылёк. Сосед, граф Эгмонт, записал в дневник версии, ходившие по городу: пришёл пьяным и поджёг полог кровати; уснул со свечой; или слуги убили его и подожгли дом.
Самая распространённая версия — убийство. Но главный биограф Кантильона, Антуан Мёрфи, предложил другую: Кантильон мог инсценировать собственную смерть — у него было много причин исчезнуть, от бесконечных судов до угроз бывших клиентов. Улика: в декабре 1734 года в голландском Суринаме появился «шевалье де Лувиньи» с бумагами Кантильона и его новым завещанием, датированным 11 апреля 1734 года — за месяц до пожара. И вскоре этот человек исчез.
Подведу итог. Кто он: ирландско-французский банкир, миллионер пузыря Миссисипи, автор первого трактата обо всей экономике. Главная мысль: экономика — саморегулирующаяся система, а деньги не нейтральны. Вклад: предприниматель — тот, кто покупает по известной цене и продаёт по неизвестной, то есть несёт неопределённость. Спасибо за внимание!` });
  chrome(s, 10, "09 — ЗАГАДКА И ИТОГ");
  stage(s, "candle", { x: 8.75, y: 0.75, s: 4.2, rot: [10, -20, 0], px: 700, shy: 0.86, shw: 0.55, caption: ["10", "Свеча мерцает, мотылёк летит на свет · 14 мая 1734"], capY: 4.75 });
  title(s, "Убит — или сбежал?", { w: 7.6, h: 0.8 });
  rows(s, [
    ["Пожар на Албемарл-стрит", "Около 3 часов ночи сгорели его дом и два соседних; в постели — тело."],
    ["Улики", "Ценностей на £200 000. Уволенный повар бежал за море под чужим именем."],
  ], { y0: 2.0, step: 0.72, w: 6.3, nums: ["03:00", "Улики"], numW: 1.15, head: 13.5, sub: 11 });
  const v = [
    ["ВЕРСИЯ 1 · УБИЙСТВО", "Повар ограбил и убил хозяина, а пожаром скрыл следы.", false],
    ["ВЕРСИЯ 2 · ПОБЕГ", "Сам инсценировал смерть и уплыл в Суринам (А. Мёрфи).", true],
  ];
  const vw = (7.4 - 0.2) / 2;
  v.forEach(([l, t, hi], i) => {
    const x = L + i * (vw + 0.2), y = 3.6, ag = 3 + i;
    card(s, x, y, vw, 1.1, { line: hi ? ACC : "9A8C86", lineT: hi ? 35 : 65, fillT: 10, ag });
    label(s, l, x + 0.22, y + 0.14, vw - 0.3, hi ? ACC : MUTED, ag);
    s.text(t, { x: x + 0.22, y: y + 0.4, w: vw - 0.4, h: 0.62, font: "head", size: 13, color: WHITE, lineSpacingMultiple: 1.0, ag });
  });
  fact(s, L, 4.98, 7.4, 0.95, [run("В Суринаме «шевалье де Лувиньи» имел при себе "), run("новое завещание Кантильона от 11 апреля 1734 года", { bold: true }), run(" — за месяц до пожара.")], { size: 12.5, tag: "ГЛАВНАЯ ЗАГАДКА", ag: 5 });
  s.text("Спасибо за внимание!", { x: 8.2, y: 5.25, w: 4.38, h: 0.6, font: "head", italic: true, size: 26, color: GOLD2, align: "right", ag: 6 });
  s.text([run("Источники: ", { bold: true, color: GOLD }),
    run("A. E. Murphy, Richard Cantillon: Entrepreneur and Economist (1986) · Dictionary of Irish Biography · H. Higgs (1931) · W. S. Jevons (1881) · F. A. Hayek (1931) · M. Rothbard · M. Thornton (2018) · Mises Institute · Irish Independent (2013) · «Essai sur la nature du commerce en général» (1755). Все 3D-экспонаты и их анимации смоделированы в Blender для этой презентации.", { color: MUTED })],
  { x: L, y: 6.1, w: CW, h: 0.75, size: 8.5, lineSpacingMultiple: 1.05, ag: 7 });
  slides.push(s);
}

// ---------- Morph choreography: neighbouring exhibits fly in / out of the frame in 3D ----------
for (let i = 0; i < slides.length; i++) {
  const cur = slides[i].hero, nxt = slides[i + 1] && slides[i + 1].hero;
  if (nxt && (!cur || cur.key !== nxt.key)) {
    slides[i].model(nxt.key, { x: SW + 0.6, y: nxt.y + 0.4, s: nxt.s, rot: [nxt.rot[0], nxt.rot[1] + 80, nxt.rot[2]], name: `!!m-${nxt.key}`, ghost: true });
  }
  if (cur && slides[i + 1] && (!nxt || nxt.key !== cur.key)) {
    slides[i + 1].model(cur.key, { x: -cur.s - 0.6, y: cur.y + 0.4, s: cur.s, rot: [cur.rot[0], cur.rot[1] - 80, cur.rot[2]], name: `!!m-${cur.key}`, ghost: true });
  }
}

// ---------- 3D assets: glb models + rendered rasters ----------
const MODELS = path.join(__dirname, "models");
function prepareModels() {
  const env = { ...process.env, GLB_DIR: path.join(MODELS, "glb"),
    LD_LIBRARY_PATH: [process.env.BLENDER_LIBS || "/tmp/bstub", process.env.LD_LIBRARY_PATH || ""].join(":") };
  const keys = new Set();
  slides.forEach((s) => s.els.forEach((e) => e.t === "model" && keys.add(e.key)));
  const missing = [...keys].filter((k) => !fs.existsSync(path.join(MODELS, "glb", k + ".glb")));
  if (missing.length) execSync(`python3 ${path.join(MODELS, "make_models.py")} ${missing.join(" ")}`, { stdio: "inherit", env });
  const jobs = [];
  fs.mkdirSync(path.join(MODELS, "rasters"), { recursive: true });
  let n = 0;
  slides.forEach((s) => s.els.forEach((e) => {
    if (e.t !== "model") return;
    e.id = `m${++n}`;
    if (e.ghost) { e.raster = A("clear.png"); return; }
    let px = e.px || Math.round(Math.min(1100, Math.max(220, e.s * 150)));
    if (process.env.FAST) px = Math.round(px / 3);
    const glb = fs.readFileSync(path.join(MODELS, "glb", e.key + ".glb"));
    const h = crypto.createHash("md5").update(glb).update(JSON.stringify([e.rot, px, 3])).digest("hex").slice(0, 10);
    e.raster = path.join(MODELS, "rasters", `${e.key}-${h}.png`);
    if (!fs.existsSync(e.raster) && !jobs.find((j) => j.out === e.raster)) jobs.push({ key: e.key, rot: e.rot, px, out: e.raster });
  }));
  if (jobs.length) {
    console.log(`rendering ${jobs.length} model rasters with Blender…`);
    const jf = path.join(MODELS, "rasters", "_jobs.json");
    fs.writeFileSync(jf, JSON.stringify(jobs));
    execSync(`python3 ${path.join(SCH, "models", "render.py")} ${jf}`, { stdio: ["ignore", "ignore", "inherit"], env });
    fs.unlinkSync(jf);
  }
  if (!process.env.FAST) {
    const used = new Set(slides.flatMap((s) => s.els.filter((e) => e.t === "model").map((e) => path.basename(e.raster))));
    for (const f of fs.readdirSync(path.join(MODELS, "rasters"))) if (f.endsWith(".png") && !used.has(f)) fs.unlinkSync(path.join(MODELS, "rasters", f));
  }
}

// ---------- output ----------
async function main() {
  prepareModels();
  const pptxgen = req("pptxgenjs");
  const JSZip = req("jszip");
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.title = "Ричард Кантильон — 3D-презентация";
  pres.author = "omgGame";
  pres.subject = "Биография, главная мысль и вклад в теорию предпринимательства";
  toPptx(pres, slides);
  const buf = await pres.write({ outputType: "nodebuffer" });
  const zip = await JSZip.loadAsync(buf);
  await injectModels(zip, slides, path.join(MODELS, "glb"));
  await injectTiming(zip, slides);
  await dedupeMedia(zip);
  const out = path.join(__dirname, "../../exports/cantillon-3d-presentation.pptx");
  fs.writeFileSync(out, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE", compressionOptions: { level: 9 } }));
  console.log("wrote", out, (fs.statSync(out).size / 1e6).toFixed(1) + " MB", slides.length, "slides");
  writeScript();
  if (process.argv.includes("--preview")) await preview();
}

function writeScript() {
  const heads = ["Титул", "Где родился", "Чем занимался", "Пузырь Миссисипи и дуэль с Ло", "Главный труд — «Essai»",
    "Главная мысль: система и три группы", "Предприниматель по Кантильону", "Эффект Кантильона", "Вклад в теорию предпринимательства",
    "Загадка пожара и итог"];
  let md = "# Текст выступления к 3D-презентации о Ричарде Кантильоне\n\n" +
    "**Ориентир:** 6–7 минут спокойной речи, 10 слайдов. В каждом 3D-экспонате есть собственная анимация " +
    "(в PowerPoint 365 она запускается сама и крутится по кругу, пока открыт слайд). " +
    "Этот же текст лежит в заметках докладчика внутри .pptx. На каждом слайде есть плашка «★» с самым интересным фактом — " +
    "её стоит произнести обязательно.\n";
  slides.forEach((s, i) => { md += `\n## Слайд ${i + 1} — ${heads[i]}\n\n${s.notes.trim()}\n`; });
  fs.writeFileSync(path.join(__dirname, "../../exports/cantillon-presentation-script.md"), md);
}

async function preview() {
  const fontsDir = path.join(SCH, "node_modules/@fontsource");
  const pages = toHtml(slides, path.join(__dirname, "assets"), fontsDir);
  const outDir = path.join(__dirname, "preview");
  fs.mkdirSync(outDir, { recursive: true });
  const chromiumMod = req("@sparticuz/chromium");
  const chromium = chromiumMod.default || chromiumMod;
  const puppeteer = req("puppeteer-core");
  if (!fs.existsSync("/tmp/al/lib/libnspr4.so")) {
    const zlib = require("zlib");
    fs.mkdirSync("/tmp/al", { recursive: true });
    const brf = req.resolve("@sparticuz/chromium").replace(/build\/.*$/, "bin/al2023.tar.br");
    fs.writeFileSync("/tmp/al/al.tar", zlib.brotliDecompressSync(fs.readFileSync(brf)));
    execSync("tar xf al.tar", { cwd: "/tmp/al" });
  }
  process.env.LD_LIBRARY_PATH = (process.env.LD_LIBRARY_PATH || "") + ":/tmp/al/lib";
  const browser = await puppeteer.launch({ args: [...chromium.args, "--allow-file-access-from-files"], executablePath: await chromium.executablePath(), headless: true });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  const only = process.argv.find((a) => a.startsWith("--only="));
  const want = only ? only.slice(7).split(",").map(Number) : null;
  for (let i = 0; i < pages.length; i++) {
    if (want && !want.includes(i + 1)) continue;
    const hf = path.join(outDir, `slide-${String(i + 1).padStart(2, "0")}.html`);
    fs.writeFileSync(hf, pages[i]);
    await page.goto("file://" + hf, { waitUntil: "networkidle0" });
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: hf.replace(".html", ".png") });
    fs.unlinkSync(hf);
  }
  await browser.close();
  console.log("previews ->", outDir);
}
main().catch((e) => { console.error(e); process.exit(1); });
