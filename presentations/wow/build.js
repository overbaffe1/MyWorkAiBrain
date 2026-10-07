// Build: node build.js            ->  ../../exports/wow-3d-showreel.pptx (+ speaker script .md)
//        node build.js --preview  ->  also renders preview/slide-XX.png
//
// "Музей оживших вещей": 3 слайда с тремя самыми богатыми анимированными
// экспонатами коллекции (модели и растры переиспользуются из ../cantillon):
//   ship   — 23 кости: волны, дышащие паруса, полощущийся вымпел, чайка
//   harp   — 17 костей: глиссандо по струнам, взлетающие ноты
//   candle — 10 костей: мерцающее пламя, дым, мотылёк на орбите
// Same engine as the other decks (../schumpeter: lib.js, pptx3d.js).
const path = require("path");
const fs = require("fs");
const crypto = require("crypto");
const { execSync } = require("child_process");
const SCH = path.join(__dirname, "..", "schumpeter");
const req = require("module").createRequire(path.join(SCH, "package.json"));
const { Slide, toPptx, toHtml } = require(path.join(SCH, "lib"));
const { injectModels, injectTiming, dedupeMedia } = require(path.join(SCH, "pptx3d"));

const A = (f) => path.join(__dirname, "..", "cantillon", "assets", f);
const GOLD = "E3B663", GOLD2 = "F3DDAE", WHITE = "F5EFE6", MUTED = "BBAEA6", ACC = "E8866A",
  CARD = "22121A", DARK = "0D0709", FACT = "22170B";
const L = 0.75, R = 12.583, CW = R - L;
const SW = 13.333;
const slides = [];
const N = 3;
const TRACK_Y = 0.44;

// ---------- helpers ----------
function chrome(s, idx, kicker) {
  s.bg = "0E080A";
  s.img(A("stage-bg.jpg"), { x: 0, y: 0, w: SW, h: 7.5, name: "Background" });
  // progress track with a rolling gold louis d'or (3D) — position = progress through the deck
  s.line({ x1: L, y1: TRACK_Y, x2: R, y2: TRACK_Y, color: "FFFFFF", lineT: 84, width: 0.75, name: "!!track" });
  const gx = N > 1 ? L + (CW * (idx - 1)) / (N - 1) : R;
  if (gx - L > 0.01) s.rect({ x: L, y: TRACK_Y - 0.012, w: gx - L, h: 0.024, fill: GOLD, name: "!!progress" });
  const gs = 0.6;
  s.model("louis", { x: gx - gs / 2, y: TRACK_Y - 0.02 - gs / 2 - 0.012, s: gs, rot: [0, -12, -146 * (idx - 1)], name: "!!coin", px: 220 });
  if (kicker) {
    s.rect({ x: L, y: 0.78, w: 0.34, h: 0.035, fill: GOLD, name: "!!kickerbar" });
    s.text([{ text: kicker }], { x: L + 0.48, y: 0.65, w: 9, h: 0.3, size: 11, bold: true, color: GOLD, charSpacing: 3, name: "!!kicker" });
  }
  s.line({ x1: L, y1: 7.0, x2: R, y2: 7.0, color: "FFFFFF", lineT: 88, width: 0.75, name: "!!footline" });
  s.text("МУЗЕЙ ОЖИВШИХ ВЕЩЕЙ  ·  ТОП-3", { x: L, y: 7.1, w: 5, h: 0.25, size: 9, color: MUTED, charSpacing: 2, name: "!!footer" });
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
// 1. TITLE + SHIP
{
  const s = new Slide({ notes:
`Добро пожаловать в музей оживших вещей! Перед вами три самых богатых анимированных экспоната нашей коллекции.
Каждый экспонат — это настоящая 3D-модель внутри PowerPoint: её можно крутить мышкой прямо на слайде. Но главное — она двигается сама: внутри каждой модели спрятана скелетная анимация, и PowerPoint крутит её по кругу, пока открыт слайд. Никакого видео — только модель и кости.
Первый экспонат — торговый корабль, чемпион коллекции: 23 кости, 69 каналов анимации. Он идёт по волнам — а волны бегут по-настоящему, у воды восемь шарниров. Паруса дышат, вымпел полощется, а над мачтами кружит чайка и время от времени планирует с неподвижными крыльями.
Как смотреть: дайте слайду постоять 6–7 секунд — и вы увидите полный цикл: качку, волну, взмах крыльев.` });
  chrome(s, 1, "МУЗЕЙ ОЖИВШИХ ВЕЩЕЙ  ·  ТОП-3");
  stage(s, "ship", { x: 5.85, y: 0.65, s: 7.3, rot: [6, -34, 0], px: 1150, shy: 0.86, shw: 0.8, caption: ["01", "Корабль идёт по волнам, над мачтами кружит чайка"], capX: 8.6, capY: 1.3, cw: 4.0, capAlign: "right" });
  s.text([br("Музей", { color: GOLD2, size: 52 }), run("оживших вещей", { size: 52 })],
    { x: L, y: 1.25, w: 7, h: 2.2, font: "head", color: WHITE, lineSpacingMultiple: 0.92, name: "!!title" });
  s.rect({ x: L, y: 3.62, w: 1.1, h: 0.04, fill: GOLD, ag: 1 });
  s.text("Три самые богатые анимированные 3D-модели коллекции: их можно крутить мышкой — а двигаются они сами",
    { x: L, y: 3.8, w: 5.9, h: 1.0, font: "head", italic: true, size: 18, color: WHITE, lineSpacingMultiple: 1.05, ag: 1 });
  s.text("КОРАБЛЬ   ·   АРФА   ·   СВЕЧА", { x: L, y: 4.95, w: 6.4, h: 0.3, size: 12, color: MUTED, charSpacing: 2.5, bold: true, ag: 2 });
  fact(s, L, 5.7, 5.6, 1.05, [run("23 кости, 69 каналов анимации: "), run("волны бегут, паруса дышат, вымпел полощется, чайка кружит", { bold: true }), run(" — и всё это внутри одного .glb без единого кадра видео.")], { size: 12.5 });
  slides.push(s);
}

// 2. HARP
{
  const s = new Slide({ notes:
`Второй экспонат — арфа, которая играет сама. Смотрите на струны: по ним пробегает глиссандо — волна дрожи идёт вверх, потом обратно вниз. У каждой струны свой шарнир на верхнем конце, а веса настроены так, что концы закреплены, а гнётся только середина — как у настоящей струны.
А из струн вылетают золотые ноты: они поднимаются вверх, растут и тают — всего в модели 17 костей.
Самое интересное: дрожь каждой струны — это затухающая синусоида с частотой 22 колебания за цикл. На слух мы её не слышим, но глаз читает её как настоящий звук.` });
  chrome(s, 2, "02 — АРФА");
  stage(s, "harp", { x: 8.2, y: 0.95, s: 4.8, rot: [6, -26, 0], px: 780, shy: 0.86, shw: 0.62, caption: ["02", "Арфа: глиссандо по струнам — и ноты взлетают"], cw: 3.9 });
  title(s, "Арфа, которая играет сама", { size: 33 });
  rows(s, [
    ["Глиссандо вверх и вниз", "Волна дрожи пробегает по струнам туда и обратно — у каждой своя задержка."],
    ["Ноты взлетают", "Золотые ноты поднимаются из струн вверх, растут и растворяются."],
    ["Концы закреплены", "Гнётся только середина струны — веса настроены синусом, как у настоящей."],
    ["17 костей", "Шарнир у каждой струны плюс летящие ноты — всё в одном бесшовном цикле."],
  ], { y0: 2.42, step: 0.78, w: 6.3, nums: ["I", "II", "III", "IV"] });
  fact(s, L, 5.62, 7.0, 1.16, [run("Дрожь струны — затухающая синусоида, "), run("22 колебания за цикл", { bold: true }), run(". Звука нет, но глаз слышит глиссандо.")], { size: 12.5, tag: "КАК ЭТО УСТРОЕНО" });
  slides.push(s);
}

// 3. CANDLE + finale
{
  const s = new Slide({ notes:
`Третий экспонат — свеча. Пламя мерцает, вьётся дымок, а вокруг огня по орбите кружит мотылёк и машет крыльями.
Самое интересное — как сделано мерцание: это сумма синусов с целыми частотами — 3, 7, 13 и 5, 11, 17 колебаний за цикл. Выглядит как случайное дрожание огня, но начало и конец цикла совпадают идеально — шва не видно.
Дым — это вереница клубов: каждый поднимается, растёт и исчезает ровно к концу своей жизни, поэтому прыжок назад незаметен. А мотылёк летит по кругу: кость орбиты делает полный оборот, крылья машут в противофазе.
Итог нашего маленького музея: три предмета, три характера движения — море, музыка и огонь. Всё смоделировано кодом в Blender, всё крутится само. Спасибо за внимание!` });
  chrome(s, 3, "03 — СВЕЧА");
  stage(s, "candle", { x: 8.75, y: 0.75, s: 4.2, rot: [10, -20, 0], px: 700, shy: 0.86, shw: 0.55, caption: ["03", "Свеча мерцает, мотылёк летит на свет"], capY: 4.75 });
  title(s, "Огонь, дым и мотылёк", { w: 7.6, h: 0.8 });
  rows(s, [
    ["Пламя мерцает", "Язычок огня дрожит и покачивается — у внутреннего ядра свой ритм."],
    ["Дым вьётся", "Клубы дыма поднимаются вверх, растут и тают один за другим."],
    ["Мотылёк на орбите", "Кружится вокруг огня и машет крыльями в противофазе."],
  ], { y0: 2.1, step: 0.85, w: 6.3, nums: ["I", "II", "III"] });
  fact(s, L, 4.85, 7.4, 1.05, [run("Мерцание — сумма синусов с частотами "), run("3, 7, 13 и 5, 11, 17 колебаний за цикл", { bold: true }), run(": выглядит случайно, но цикл бесшовный.")], { size: 12.5, tag: "КАК ЭТО УСТРОЕНО", ag: 5 });
  s.text("Спасибо за внимание!", { x: 8.2, y: 5.25, w: 4.38, h: 0.6, font: "head", italic: true, size: 26, color: GOLD2, align: "right", ag: 6 });
  s.text([run("Как это сделано: ", { bold: true, color: GOLD }),
    run("все 3D-экспонаты и их анимации смоделированы кодом в Blender; в PowerPoint 365 модели крутятся мышкой, а встроенная скелетная анимация играет сама. Модели ship / harp / candle — из коллекции cantillon.", { color: MUTED })],
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

// ---------- 3D assets: glb models + rendered rasters (reused from ../cantillon) ----------
const MODELS = path.join(__dirname, "..", "cantillon", "models");
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
  // NB: no raster cleanup here — the rasters dir belongs to the cantillon deck, shared, do not prune.
}

// ---------- output ----------
async function main() {
  prepareModels();
  const pptxgen = req("pptxgenjs");
  const JSZip = req("jszip");
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.title = "Музей оживших вещей — топ-3 анимированных 3D-экспоната";
  pres.author = "omgGame";
  pres.subject = "Шоурил: корабль, арфа и свеча — настоящие 3D-модели с автоплеем анимации";
  toPptx(pres, slides);
  const buf = await pres.write({ outputType: "nodebuffer" });
  const zip = await JSZip.loadAsync(buf);
  await injectModels(zip, slides, path.join(MODELS, "glb"));
  await injectTiming(zip, slides);
  await dedupeMedia(zip);
  const out = path.join(__dirname, "../../exports/wow-3d-showreel.pptx");
  fs.writeFileSync(out, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE", compressionOptions: { level: 9 } }));
  console.log("wrote", out, (fs.statSync(out).size / 1e6).toFixed(1) + " MB", slides.length, "slides");
  writeScript();
  if (process.argv.includes("--preview")) await preview();
}

function writeScript() {
  const heads = ["Титул — музей оживших вещей, корабль",
    "Арфа, которая играет сама",
    "Огонь, дым и мотылёк — финал"];
  let md = "# Текст выступления к шоурилу «Музей оживших вещей»\n\n" +
    "**Ориентир:** 3–4 минуты спокойной речи, 3 слайда. В каждом 3D-экспонате есть собственная анимация " +
    "(в PowerPoint 365 она запускается сама и крутится по кругу, пока открыт слайд). " +
    "Этот же текст лежит в заметках докладчика внутри .pptx. На каждом слайде есть плашка «★» — " +
    "её стоит произнести обязательно.\n";
  slides.forEach((s, i) => { md += `\n## Слайд ${i + 1} — ${heads[i]}\n\n${s.notes.trim()}\n`; });
  fs.writeFileSync(path.join(__dirname, "../../exports/wow-showreel-script.md"), md);
}

async function preview() {
  const fontsDir = path.join(SCH, "node_modules/@fontsource");
  const pages = toHtml(slides, path.join(__dirname, "..", "cantillon", "assets"), fontsDir);
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
