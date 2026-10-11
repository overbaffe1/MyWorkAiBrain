// Build: node build.js            ->  ../../exports/fun-fire-island.pptx (+ speaker script .md)
//        node build.js --preview  ->  also renders preview/slide-01.png
//
// "ОСТРОВ ОГНЯ": ONE fan slide where everything is alive — 5 copies of 3 models,
// all created from scratch for this slide (models/make_models.py, Blender -> .glb):
//   volcano  — 40 bones: erupting island, lava fountain, smoke, palms, hut,
//                a dragon circling the crater and breathing fire, dancing gold title
//   torch    — 7 bones x2 (left/right edges): flickering flame, smoke, embers
//   lavapool — 5 bones x2 (bottom corners): breathing lava, growing/popping bubbles
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
const GOLD = "E8A34F", GOLD2 = "F6CF8E", WHITE = "FBF3E8", MUTED = "C4A894", ACC = "E86A4A",
  CARD = "241310", DARK = "120806", FACT = "2A1408";
const L = 0.75, R = 12.583, CW = R - L;
const SW = 13.333;
const slides = [];
const TRACK_Y = 0.44;

// ---------- helpers ----------
function chrome(s, kicker) {
  s.bg = "0D0503";
  s.img(A("stage-bg.jpg"), { x: 0, y: 0, w: SW, h: 7.5, name: "Background" });
  s.line({ x1: L, y1: TRACK_Y, x2: R, y2: TRACK_Y, color: "FFFFFF", lineT: 84, width: 0.75, name: "!!track" });
  s.rect({ x: L, y: TRACK_Y - 0.012, w: CW, h: 0.024, fill: GOLD, name: "!!progress" });
  if (kicker) {
    s.rect({ x: L, y: 0.72, w: 0.34, h: 0.035, fill: GOLD, name: "!!kickerbar" });
    s.text([{ text: kicker }], { x: L + 0.48, y: 0.60, w: 9, h: 0.3, size: 11, bold: true, color: GOLD, charSpacing: 3, name: "!!kicker" });
  }
  s.line({ x1: L, y1: 7.0, x2: R, y2: 7.0, color: "FFFFFF", lineT: 88, width: 0.75, name: "!!footline" });
  s.text("5 МОДЕЛЕЙ  ·  64 КОСТИ  ·  ПЕТЛИ 6 С + 4 С  ·  КРУТИТСЯ МЫШКОЙ", { x: L, y: 7.1, w: 8.5, h: 0.25, size: 9, color: MUTED, charSpacing: 2, name: "!!footer" });
  s.text("01 / 01", { x: R - 1.5, y: 7.1, w: 1.5, h: 0.25, size: 9, color: MUTED, align: "right", charSpacing: 2, name: "!!pagenum" });
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
  s.model(key, { x, y, s: sz, rot, name: o.name || `!!m-${key}`, px: o.px });
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

// small edge model: just a light pool + the model (no rings — it lives on the slide edge)
function edge(s, key, o) {
  const { x, y, s: sz, rot } = o;
  const g = o.glow || sz * 1.15;
  s.img(A("glow.png"), { x: x + sz / 2 - g / 2, y: y + sz / 2 - g / 2, w: g, h: g, name: o.gname || "!!glow-e" });
  s.model(key, { x, y, s: sz, rot, name: o.name, px: o.px });
}

const br = (text, o = {}) => ({ text, options: { ...o, breakLine: true } });
const run = (text, o = {}) => ({ text, options: o });

// "the most interesting fact" — the ★ component
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

// =====================================================================
// THE ONE AND ONLY SLIDE — ОСТРОВ ОГНЯ
{
  const s = new Slide({ notes:
`Это фан-слайд — один-единственный, но живой целиком. Здесь нет ни одного статичного 3D-объекта: пять моделей играют свои анимации одновременно, каждая со своей бесшовной петлёй.\nВ центре — Остров огня: вулкан извергается (фонтан лавы, бомбы, дым, искры), по склонам текут светящиеся потоки, качаются пальмы, а на берегу стоит хижина — кто-то живёт опасно. Над кратером кружит дракон: машет крыльями, планирует и раз за цикл дышит огнём. А выше танцует золотая надпись INFERNO — каждая буква качается в своём ритме.\nПо краям — живой огонь: два факела с трепещущим пламенем слева и справа, две чаши с булькающей лавой по нижним углам.\nСамое интересное: 64 кости на одном слайде — 40 у вулкана, по 7 у факелов, по 5 у чаш. Всё создано кодом в Blender специально для этого слайда, всё крутится само — а мышкой любую модель можно повертеть.` });
  chrome(s, "ФАН-СЛАЙД  ·  ВСЁ НА СЛАЙДЕ ЖИВОЕ");
  stage(s, "volcano", { x: 5.2, y: 0.70, s: 5.4, rot: [10, -24, 0], px: 1100, shy: 0.86, shw: 0.8,
    caption: ["01", "Вулкан извергается, дракон кружит и дышит огнём"], capX: 5.5, capY: 6.15, cw: 4.8 });
  edge(s, "torch", { x: 0.25, y: 3.35, s: 2.4, rot: [8, -15, 0], px: 420, name: "!!m-torch-l", gname: "!!glow-tl" });
  edge(s, "torch", { x: 10.68, y: 3.35, s: 2.4, rot: [8, 15, 0], px: 420, name: "!!m-torch-r", gname: "!!glow-tr" });
  edge(s, "lavapool", { x: 0.75, y: 5.35, s: 1.85, rot: [30, -20, 0], px: 380, name: "!!m-pool-l", gname: "!!glow-pl" });
  edge(s, "lavapool", { x: 11.03, y: 5.35, s: 1.85, rot: [30, 20, 0], px: 380, name: "!!m-pool-r", gname: "!!glow-pr" });
  s.text([run("Остров ", { color: WHITE }), run("огня", { color: GOLD2 })],
    { x: L, y: 0.90, w: 4.2, h: 0.85, font: "head", size: 40, lineSpacingMultiple: 0.95, name: "!!title" });
  s.text("Вулкан, дракон, факелы и лава — всё движется само",
    { x: L, y: 1.80, w: 4.2, h: 0.60, font: "head", italic: true, size: 14.5, color: WHITE, lineSpacingMultiple: 1.05, ag: 1 });
  fact(s, L, 2.50, 4.0, 0.80, [run("64 кости: "), run("вулкан, два факела, две лава-чаши", { bold: true }), run(" — пять моделей играют сразу.")], { size: 11.5 });
  slides.push(s);
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
  pres.title = "Остров огня — один живой слайд (3D)";
  pres.author = "omgGame";
  pres.subject = "Один фан-слайд: 5 моделей, 64 кости, всё анимировано";
  toPptx(pres, slides);
  const buf = await pres.write({ outputType: "nodebuffer" });
  const zip = await JSZip.loadAsync(buf);
  await injectModels(zip, slides, path.join(MODELS, "glb"));
  await injectTiming(zip, slides);
  await dedupeMedia(zip);
  const out = path.join(__dirname, "../../exports/fun-fire-island.pptx");
  fs.writeFileSync(out, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE", compressionOptions: { level: 9 } }));
  console.log("wrote", out, (fs.statSync(out).size / 1e6).toFixed(1) + " MB", slides.length, "slides");
  writeScript();
  if (process.argv.includes("--preview")) await preview();
}

function writeScript() {
  const heads = ["Остров огня — единственный слайд"];
  let md = "# Текст выступления к фан-слайду «Остров огня»\n\n" +
    "**Ориентир:** 1–2 минуты. Один слайд, пять 3D-моделей с автоплеем анимации " +
    "(в PowerPoint 365 анимации запускаются сами и крутятся по кругу). " +
    "Этот же текст лежит в заметках докладчика внутри .pptx. Плашку «★» стоит произнести обязательно.\n";
  slides.forEach((s, i) => { md += `\n## Слайд ${i + 1} — ${heads[i]}\n\n${s.notes.trim()}\n`; });
  fs.writeFileSync(path.join(__dirname, "../../exports/fun-fire-island-script.md"), md);
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
