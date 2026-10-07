// Build: node build.js            ->  ../../exports/wow-3d-wonders.pptx (+ speaker script .md)
//        node build.js --preview  ->  also renders preview/slide-XX.png
//
// "ТРИ ЧУДА": 3 слайда с тремя 3D-моделями, созданными с нуля специально
// для этой презентации (models/make_models.py, Blender -> .glb):
//   lighthouse — 14 костей: вращающиеся лучи, бегущие волны, чайка
//   carousel   — 5 костей: оборот карусели, скачущие лошадки, лампочки
//   tornado    — 15 костей: воронка, орбиты мусора, пыль, молния
// Same engine as the other decks (../schumpeter: lib.js, pptx3d.js).
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
  s.text("ТРИ ЧУДА  ·  МАЯК  ·  КАРУСЕЛЬ  ·  ТОРНАДО", { x: L, y: 7.1, w: 6.5, h: 0.25, size: 9, color: MUTED, charSpacing: 2, name: "!!footer" });
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
// 1. TITLE + LIGHTHOUSE
{
  const s = new Slide({ notes:
`Добро пожаловать! Перед вами три чуда — три 3D-модели, созданные кодом с нуля специально для этой презентации.
Каждая модель — настоящая: её можно крутить мышкой прямо на слайде. Но главное — она двигается сама. Внутри каждой спрятана скелетная анимация: PowerPoint крутит её по кругу, пока открыт слайд. Никакого видео — только модель и кости.
Первое чудо — маяк в шторм. Два луча обходят горизонт дважды за цикл, волны бегут по-настоящему, лампа дышит, а над башней кружит чайка. Всего 14 костей.
Дайте слайду постоять шесть секунд — и вы увидите полный оборот: лучи religioso обойдут башню, волна прокатится, чайка спланирует.` });
  chrome(s, 1, "ТРИ ЧУДА  ·  СДЕЛАНО КОДОМ В BLENDER");
  stage(s, "lighthouse", { x: 5.85, y: 0.65, s: 7.3, rot: [10, -32, 0], px: 1050, shy: 0.86, shw: 0.8, caption: ["01", "Маяк: лучи обходят горизонт, над башней кружит чайка"], capX: 8.6, capY: 1.3, cw: 4.0, capAlign: "right" });
  s.text([br("Три", { color: GOLD2, size: 52 }), run("чуда", { size: 72 })],
    { x: L, y: 1.25, w: 7, h: 2.5, font: "head", color: WHITE, lineSpacingMultiple: 0.92, name: "!!title" });
  s.rect({ x: L, y: 3.92, w: 1.1, h: 0.04, fill: GOLD, ag: 1 });
  s.text("Три 3D-модели, созданные с нуля: их можно крутить мышкой — а двигаются они сами",
    { x: L, y: 4.1, w: 5.9, h: 1.0, font: "head", italic: true, size: 18, color: WHITE, lineSpacingMultiple: 1.05, ag: 1 });
  s.text("МАЯК   ·   КАРУСЕЛЬ   ·   ТОРНАДО", { x: L, y: 5.22, w: 6.4, h: 0.3, size: 12, color: MUTED, charSpacing: 2.5, bold: true, ag: 2 });
  fact(s, L, 5.85, 5.6, 0.92, [run("14 костей: "), run("два луча обходят горизонт дважды за цикл", { bold: true }), run(", волны бегут, чайка кружит — и всё это внутри одного .glb.")], { size: 12.5 });
  slides.push(s);
}

// 2. CAROUSEL
{
  const s = new Slide({ notes:
`Второе чудо — карусель, которая не останавливается. Вся карусель делает полный оборот за шесть секунд — и шва не видно, потому что оборот ровно один.
А лошадки скачут: белая, гнедая и вороная взлетают и опускаются со сдвигом в треть цикла — как настоящие, вразнобой. Под куполом светятся четырнадцать лампочек.
Самое интересное — как это устроено: лошадки — дети вращающейся кости. Они скачут вверх-вниз, а карусель несёт их по кругу. Всего пять костей: одна крутит всё, три качают лошадок.` });
  chrome(s, 2, "02 — КАРУСЕЛЬ");
  stage(s, "carousel", { x: 8.2, y: 0.95, s: 4.8, rot: [12, -30, 0], px: 900, shy: 0.86, shw: 0.62, caption: ["02", "Карусель крутится, лошадки скачут вразнобой"], cw: 3.9 });
  title(s, "Карусель, которая не останавливается", { size: 31, w: 7.3 });
  rows(s, [
    ["Полный оборот", "Вся карусель делает оборот за 6 секунд — шва не видно."],
    ["Лошадки скачут", "Белая, гнедая и вороная взлетают и опускаются вразнобой."],
    ["Лампочки светятся", "Четырнадцать лампочек под куполом едут по кругу вместе со всеми."],
    ["Всего 5 костей", "Одна крутит всё, три качают лошадок — и никакого видео."],
  ], { y0: 2.42, step: 0.78, w: 6.3, nums: ["I", "II", "III", "IV"] });
  fact(s, L, 5.62, 7.0, 1.16, [run("Лошадки — "), run("дети вращающейся кости", { bold: true }), run(": скачут вверх-вниз, а карусель несёт их по кругу.")], { size: 12.5, tag: "КАК ЭТО УСТРОЕНО" });
  slides.push(s);
}

// 3. TORNADO + finale
{
  const s = new Slide({ notes:
`Третье чудо — торнадо, буря в стакане. Воронка собрана из шести колец, и каждое вращается со своей скоростью — кольца сдвигаются друг мимо друга, и воронка живёт.
Вокруг кружит мусор: доски, бочка, дерево и ящик летят на трёх орбитах с разной скоростью. У подножия поднимается пыль, наверху клубится грозовое облако — а дважды за цикл небо прошивает молния и гаснет без следа.
Самое интересное: пятнадцать костей — воронка, облако, три орбиты мусора, пыль и молния. Хаос, замкнутый в бесшовное кольцо длиной пять секунд.
Итог: три чуда, три характера движения — свет, праздник и буря. Всё создано кодом в Blender, всё крутится само. Спасибо за внимание!` });
  chrome(s, 3, "03 — ТОРНАДО");
  stage(s, "tornado", { x: 8.35, y: 0.75, s: 4.6, rot: [10, -26, 0], px: 900, shy: 0.86, shw: 0.75, caption: ["03", "Торнадо: воронка ревёт, молния бьёт дважды"], capY: 4.75, cw: 3.6 });
  title(s, "Буря в стакане", { w: 7.6, h: 0.8 });
  rows(s, [
    ["Воронка из шести колец", "Каждое кольцо вращается со своей скоростью — они сдвигаются друг мимо друга."],
    ["Мусор на орбитах", "Доски, бочка, дерево и ящик кружат на трёх кольцах с разной скоростью."],
    ["Молния", "Дважды за цикл небо прошивает разряд — и гаснет без следа."],
  ], { y0: 2.1, step: 0.85, w: 6.3, nums: ["I", "II", "III"] });
  fact(s, L, 4.85, 7.4, 1.05, [run("15 костей: "), run("воронка, облако, три орбиты мусора, пыль и молния", { bold: true }), run(" — хаос, замкнутый в кольцо.")], { size: 12.5, tag: "КАК ЭТО УСТРОЕНО", ag: 5 });
  s.text("Спасибо за внимание!", { x: 8.2, y: 5.25, w: 4.38, h: 0.6, font: "head", italic: true, size: 26, color: GOLD2, align: "right", ag: 6 });
  s.text([run("Как это сделано: ", { bold: true, color: GOLD }),
    run("все 3D-экспонаты и их анимации созданы кодом в Blender специально для этой презентации (models/make_models.py). В PowerPoint 365 модели крутятся мышкой, а встроенная скелетная анимация играет сама.", { color: MUTED })],
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
  pres.title = "Три чуда — маяк, карусель и торнадо (3D-презентация)";
  pres.author = "omgGame";
  pres.subject = "Три 3D-модели, созданные с нуля: настоящие модели с автоплеем анимации";
  toPptx(pres, slides);
  const buf = await pres.write({ outputType: "nodebuffer" });
  const zip = await JSZip.loadAsync(buf);
  await injectModels(zip, slides, path.join(MODELS, "glb"));
  await injectTiming(zip, slides);
  await dedupeMedia(zip);
  const out = path.join(__dirname, "../../exports/wow-3d-wonders.pptx");
  fs.writeFileSync(out, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE", compressionOptions: { level: 9 } }));
  console.log("wrote", out, (fs.statSync(out).size / 1e6).toFixed(1) + " MB", slides.length, "slides");
  writeScript();
  if (process.argv.includes("--preview")) await preview();
}

function writeScript() {
  const heads = ["Титул — три чуда, маяк",
    "Карусель, которая не останавливается",
    "Буря в стакане — финал"];
  let md = "# Текст выступления к презентации «Три чуда»\n\n" +
    "**Ориентир:** 3–4 минуты спокойной речи, 3 слайда. В каждом 3D-экспонате есть собственная анимация " +
    "(в PowerPoint 365 она запускается сама и крутится по кругу, пока открыт слайд). " +
    "Этот же текст лежит в заметках докладчика внутри .pptx. На каждом слайде есть плашка «★» — " +
    "её стоит произнести обязательно.\n";
  slides.forEach((s, i) => { md += `\n## Слайд ${i + 1} — ${heads[i]}\n\n${s.notes.trim()}\n`; });
  fs.writeFileSync(path.join(__dirname, "../../exports/wow-wonders-script.md"), md);
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
