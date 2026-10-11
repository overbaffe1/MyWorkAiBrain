// Meme-forward 10-slide Russian research deck: impulse spending, with the original chestnut as a recurring mascot.
// All text stays editable; every slide keeps a native, skinned PowerPoint 3D model and Morph choreography.
const path = require("path");
const fs = require("fs");
const crypto = require("crypto");
const { execSync } = require("child_process");
const { createRequire } = require("module");

const ROOT = path.resolve(__dirname, "../..");
const SCH = path.join(ROOT, "presentations", "schumpeter");
const req = createRequire(path.join(SCH, "package.json"));
const { Slide, toPptx, toHtml } = require(path.join(SCH, "lib"));
const { injectModels, injectTiming, dedupeMedia } = require(path.join(SCH, "pptx3d"));

const A = (f) => path.join(__dirname, "assets", f);
const MODELS = path.join(__dirname, "models");
const GLB = path.join(MODELS, "glb");
const RASTERS = path.join(MODELS, "rasters");
const SW = 13.333, SH = 7.5;
const L = 0.76, R = 12.58, CW = R - L;
const N = 10;
const C = {
  paper: "FAF7EC", white: "FFFEF8", ink: "17181C", muted: "59616B",
  blue: "2E70B7", red: "E6373F", yellow: "FFDD55", teal: "57BFB2",
  green: "3E8A5A", orange: "F39A36", lilac: "D9C8F2", grey: "DDE1E5",
};
const slides = [];
const MEMES = {
  chestnut: { file: "chestnut-photo.jpeg", ar: 600 / 401 },
  budget106: { file: "meme-106-rubles.jpeg", ar: 736 / 594 },
  jars: { file: "meme-budget-jars.jpeg", ar: 736 / 669 },
  hamster: { file: "meme-charge-hamster.jpeg", ar: 1 },
  rich: { file: "meme-rich-guy.jpeg", ar: 1.5 },
  serotonin: { file: "meme-serotonin.jpeg", ar: 735 / 524 },
  papa: { file: "meme-where-papa.jpeg", ar: 1 },
};

function chrome(s, idx, kicker) {
  s.bg = C.paper;
  s.img(A("stage-bg.jpg"), { x: 0, y: 0, w: SW, h: SH, name: `Paper ${idx}` });
  // Marker-like progress and sticky labels echo the graph-paper/meme collage of the source deck.
  sticker(s, "КАШТАНСКИЙ РАЗБОР", L, 0.20, 2.30, 0.32, { fill: C.red, color: C.white, size: 8.3 });
  s.text(kicker.toUpperCase(), { x: L + 2.48, y: 0.25, w: 8.4, h: 0.22, font: "meme", size: 8.3, color: C.ink, bold: true, charSpacing: 0.55 });
  s.line({ x1: L, y1: 0.77, x2: R, y2: 0.77, color: C.ink, lineT: 46, width: 0.65 });
  const progress = CW * idx / N;
  s.line({ x1: L, y1: 0.77, x2: L + progress, y2: 0.77, color: C.red, width: 2.3 });
  sticker(s, `${String(idx).padStart(2, "0")} / ${N}`, 11.86, 0.15, 0.70, 0.34, { fill: C.yellow, color: C.ink, size: 8.5 });
  // recurring doodle marks, deliberately light so the content remains readable
  s.poly([[11.65, 0.98], [11.90, 0.94], [12.12, 0.99], [12.35, 0.94]], { color: C.blue, width: 1.8 });
  s.line({ x1: L, y1: 7.06, x2: R, y2: 7.06, color: C.ink, lineT: 68, width: 0.65 });
  s.text("МЕМЫ — ДЛЯ ИЛЛЮСТРАЦИИ. ВЫВОДЫ — ТОЛЬКО ПО ДАННЫМ.", {
    x: L, y: 7.16, w: 8.0, h: 0.17, font: "meme", size: 6.8, color: C.muted, charSpacing: 0.2,
  });
  s.text("КАШТАН  ·  ПРОЕКТ", { x: 10.0, y: 7.16, w: 2.0, h: 0.17, font: "meme", size: 6.8, color: C.muted, align: "right", charSpacing: 0.4 });
}

function title(s, t, o = {}) {
  const x = o.x ?? L, y = o.y ?? 1.08, w = o.w ?? 7.65, h = o.h ?? 0.92;
  const markW = o.markW ?? Math.min(w * 0.74, Math.max(2.2, t.length * 0.075));
  // A slightly crooked yellow marker swipe under every loud meme-style headline.
  s.poly([[x, y + h - 0.06], [x + markW * 0.28, y + h - 0.02], [x + markW * 0.62, y + h - 0.07], [x + markW, y + h - 0.025]], {
    color: C.yellow, width: 8.5, lineT: 5,
  });
  s.text(t.toUpperCase(), { x, y, w, h, font: "meme", size: o.size ?? 27, color: C.ink, bold: true, lineSpacingMultiple: 0.94, valign: "top" });
}

function sticker(s, text, x, y, w, h, o = {}) {
  s.rect({ x: x + 0.045, y: y + 0.055, w, h, fill: o.shadow || C.ink, line: C.ink, lineW: 0.8, radius: 0.025 });
  s.rect({ x, y, w, h, fill: o.fill || C.yellow, line: C.ink, lineW: 1.05, radius: 0.025, rotate: o.rotate || 0 });
  s.text(text, { x: x + 0.07, y: y + 0.015, w: w - 0.14, h: h - 0.035, font: o.font || "meme", size: o.size || 8.7,
    color: o.color || C.ink, bold: true, align: o.align || "center", valign: "middle", lineSpacingMultiple: 0.95 });
}

function card(s, x, y, w, h, o = {}) {
  const accent = o.accent || C.yellow;
  s.rect({ x: x + 0.07, y: y + 0.07, w, h, fill: accent, line: C.ink, lineW: 1.0, radius: o.radius ?? 0.045 });
  s.rect({ x, y, w, h, fill: o.fill || C.white, line: C.ink, lineW: o.lineW || 1.25, radius: o.radius ?? 0.045, shadow: o.shadow ?? true });
}

function label(s, t, x, y, w, color = C.blue, o = {}) {
  s.text(t.toUpperCase(), { x, y, w, h: o.h || 0.20, font: "meme", size: o.size || 8.1, color, bold: true, charSpacing: 0.35 });
}

function fact(s, x, y, w, h, body, o = {}) {
  card(s, x, y, w, h, { accent: o.accent || C.yellow });
  const tag = o.tag || "КАШТАН ПРОВЕРИЛ";
  const tw = Math.min(w - 0.26, Math.max(1.35, tag.length * 0.078 + 0.3));
  sticker(s, tag, x + 0.15, y - 0.13, tw, 0.25, { fill: o.tagFill || C.yellow, color: C.ink, size: o.tagSize || 7.2 });
  s.text(body, { x: x + 0.20, y: y + 0.21, w: w - 0.40, h: h - 0.30, font: "body", size: o.size || 11.4, color: C.ink, bold: o.bold || false, valign: "middle", lineSpacingMultiple: 1.02 });
}

function cite(s, t) {
  s.text(`ОПОРА: ${t}`, { x: L, y: 6.82, w: 9.5, h: 0.16, size: 7.0, color: C.muted, charSpacing: 0.1 });
}

function memeCard(s, key, x, y, w, h, caption, o = {}) {
  const entry = MEMES[key];
  if (!entry) throw new Error(`unknown original meme asset: ${key}`);
  card(s, x, y, w, h, { accent: o.accent || C.yellow, lineW: 1.35 });
  const pad = 0.085, barH = o.barH || Math.min(0.43, Math.max(0.31, h * 0.19));
  const bx = x + pad, by = y + pad, bw = w - pad * 2, bh = h - pad * 2 - barH;
  s.rect({ x: bx, y: by, w: bw, h: bh, fill: C.white, line: C.ink, lineW: 0.45 });
  let iw = bw, ih = iw / entry.ar;
  if (ih > bh) { ih = bh; iw = ih * entry.ar; }
  s.img(A(path.join("memes", entry.file)), { x: bx + (bw - iw) / 2, y: by + (bh - ih) / 2, w: iw, h: ih, name: `original-meme-${key}` });
  s.rect({ x: bx, y: by + bh, w: bw, h: barH, fill: C.ink });
  s.text(caption.toUpperCase(), { x: bx + 0.06, y: by + bh + 0.025, w: bw - 0.12, h: barH - 0.04,
    font: "meme", size: o.size || Math.min(8.4, Math.max(6.4, 33 / caption.length * 7)), color: C.white, bold: true, align: "center", valign: "middle", lineSpacingMultiple: 0.95 });
}

// Museum-style 3D stage is reimagined as a framed comic sticker on graph paper.
function stage(s, key, o) {
  const { x, y, s: size, rot } = o;
  const cx = x + size / 2, cy = y + size / 2 + (o.dy || 0);
  const burst = size * (o.burst || 1.26);
  s.img(A("glow.png"), { x: cx - burst / 2, y: cy - burst / 2, w: burst, h: burst, name: `burst-${slides.length + 1}` });
  // White cutout card with the deliberately visible yellow offset edge.
  card(s, x - 0.045, y - 0.035, size + 0.09, size + 0.09, { accent: o.accent || C.yellow, lineW: 1.55 });
  const shw = size * 0.72, shy = y + size * 0.87;
  s.img(A("shadow.png"), { x: cx - shw / 2, y: shy - shw / 8, w: shw, h: shw / 4, name: `paper-shadow-${slides.length + 1}` });
  const e = s.model(key, { x, y, s: size, rot, name: `!!m-${key}`, px: o.px || Math.round(size * 165) });
  s.hero = { key, x, y, s: size, rot };
  if (o.caption) {
    const cw = o.cw || Math.min(4.2, size + 0.8);
    sticker(s, o.caption, o.capX ?? cx - cw / 2, o.capY ?? y + size + 0.13, cw, o.capH || 0.43,
      { fill: o.capFill || C.yellow, color: C.ink, size: o.capSize || 7.7 });
  }
  return e;
}

// 1. Cover — the original chestnut becomes the running meme character.
{
  const s = new Slide({ notes: `Сегодня главный герой — каштан. В исходной презентации он уже был рядом с мемами о покупках; теперь это сквозной персонаж, который каждый раз собирается «только посмотреть». Сам проект — о психологии импульсивных трат у студентов 18–25 лет. Это план исследования, а не результаты уже проведённого опроса. Мемы помогают узнать ситуации, но не служат доказательствами.` });
  chrome(s, 1, "мемный исследовательский план · импульсивные траты");
  sticker(s, "Я: ЗА ОДНИМ КАШТАНОМ", L, 1.11, 2.82, 0.34, { fill: C.blue, color: C.white, size: 8.0 });
  title(s, "Я ТОЛЬКО\nПОСМОТРЮ", { x: L, y: 1.58, w: 6.75, h: 1.60, size: 44, markW: 4.8 });
  s.text("Психология импульсивных трат", { x: L, y: 3.36, w: 6.8, h: 0.42, font: "meme", size: 18, color: C.ink, bold: true });
  s.text("Мемный исследовательский план · студенты 18–25 лет", { x: L, y: 3.83, w: 6.8, h: 0.31, size: 11.8, color: C.muted });
  memeCard(s, "chestnut", 0.88, 4.42, 3.50, 2.18, "Каштан: «я только посмотреть»", { accent: C.red, size: 7.8 });
  fact(s, 4.68, 4.64, 3.35, 1.50, "Проверяем, что связано с незапланированными покупками. Гипотезы — не готовые результаты.", { tag: "СТАТУС: ПЛАН", size: 11.1, accent: C.blue, tagFill: C.yellow });
  stage(s, "chestnut", { x: 8.55, y: 1.42, s: 3.75, rot: [8, -21, 0], px: 900, capX: 8.16, capY: 5.45, cw: 4.35,
    caption: "КАШТАН — МАСКОТ. НЕ УЧАСТНИК ВЫБОРКИ." });
  cite(s, "проектная рамка; теоретическая основа [1–3]");
  slides.push(s);
}

// 2. The short path from signal to payment.
{
  const s = new Slide({ notes: `В ленте путь от сигнала до оплаты может состоять из нескольких простых действий: человек замечает предложение, чувствует желание купить и оплачивает. Push-уведомление, сохранённая карта и рассрочка могут сократить паузу. Это описание возможного механизма, а не утверждение, что интерфейс заставляет каждого тратить больше. В исходном мем-коллаже была шутка про покупки при остатке 106 рублей; она иллюстрирует знакомое переживание, но не измеряет поведение.` });
  chrome(s, 2, "01 · от сигнала до клика");
  title(s, "ТРИ КЛИКА — И КАШТАН УЖЕ В КОРЗИНЕ?", { w: 8.1, size: 25.5 });
  const steps = [
    ["01 · УВИДЕЛ", "push · реклама · тренд"],
    ["02 · ЗАХОТЕЛ", "срочно? красиво? у всех?"],
    ["03 · ОПЛАТИЛ", "карта сохранена · BNPL"],
  ];
  steps.forEach(([h, d], i) => {
    const x = 0.82 + i * 2.42, y = 2.30, w = 2.15, ag = i + 1;
    card(s, x, y, w, 1.12, { accent: i === 1 ? C.red : C.yellow });
    label(s, h, x + 0.16, y + 0.16, w - 0.30, i === 1 ? C.red : C.blue, { size: 8.0 });
    s.text(d, { x: x + 0.16, y: y + 0.48, w: w - 0.30, h: 0.42, font: "body", size: 10.4, color: C.ink, bold: true, valign: "middle" });
    if (i < 2) s.text("→", { x: x + w + 0.04, y: y + 0.35, w: 0.20, h: 0.34, font: "meme", size: 18, color: C.red, bold: true, align: "center" });
  });
  fact(s, 0.84, 3.78, 7.05, 0.72, "Меньше трения может означать меньше пауз. Насколько это связано с тратами студентов — проверим опросом.", { tag: "МЕХАНИЗМ ≠ ДОКАЗАТЕЛЬСТВО", size: 10.6, accent: C.teal });
  memeCard(s, "budget106", 0.91, 4.76, 3.72, 1.91, "«я только открыл маркетплейс»", { accent: C.red, size: 7.4 });
  stage(s, "phone", { x: 8.67, y: 1.38, s: 3.45, rot: [9, -30, 2], px: 820, capX: 8.50, capY: 5.00, cw: 3.8,
    caption: "УВЕДОМЛЕНИЕ: «КАШТАН, ТЫ ЭТО ВИДЕЛ?»" });
  cite(s, "[6] Soman, 2001; мем-иллюстрация из исходного файла");
  slides.push(s);
}

// 3. Definition without moral labels.
{
  const s = new Slide({ notes: `Рабочее определение: импульсивная покупка — незапланированное решение купить, сопровождаемое сильным желанием сделать это немедленно. Это не диагноз и не характеристика «плохого человека». Нужно различать ситуативный порыв и более устойчивую склонность к импульсивным покупкам. Мемы про дофамин и серотонин — часть разговорного юмора; они не заменяют научное объяснение и не используются как измерения.` });
  chrome(s, 3, "02 · что считаем импульсивной покупкой");
  title(s, "ИМПУЛЬС — ПОТЯГ, А НЕ ДИАГНОЗ", { w: 7.85, size: 27 });
  card(s, 0.84, 2.15, 7.42, 0.91, { accent: C.yellow });
  s.text("Незапланированное решение + сильное желание купить «прямо сейчас».", { x: 1.06, y: 2.38, w: 6.95, h: 0.44, font: "body", size: 14, color: C.ink, bold: true, valign: "middle" });
  const phases = ["СИГНАЛ", "ПОТЯГ", "КЛИК", "ОЦЕНКА ПОСЛЕ"];
  const pw = [1.55, 1.55, 1.40, 1.75];
  let x = 0.88;
  phases.forEach((t, i) => {
    const w = pw[i];
    card(s, x, 3.37, w, 0.66, { accent: i === 1 ? C.red : C.yellow });
    s.text(t, { x: x + 0.08, y: 3.57, w: w - 0.16, h: 0.23, font: "meme", size: 8.0, color: C.ink, bold: true, align: "center", valign: "middle" });
    x += w;
    if (i < phases.length - 1) {
      s.text("→", { x: x + 0.015, y: 3.52, w: 0.23, h: 0.30, font: "meme", size: 17, color: C.red, bold: true, align: "center" });
      x += 0.30;
    }
  });
  card(s, 0.84, 4.35, 3.55, 0.91, { accent: C.teal });
  label(s, "СОСТОЯНИЕ", 1.05, 4.51, 2.9, C.blue);
  s.text("«сейчас хочу это купить»", { x: 1.05, y: 4.80, w: 3.08, h: 0.24, size: 10.7, color: C.ink, bold: true });
  card(s, 4.62, 4.35, 3.64, 0.91, { accent: C.lilac });
  label(s, "СКЛОННОСТЬ", 4.84, 4.51, 3.0, C.blue);
  s.text("как часто порыв повторяется", { x: 4.84, y: 4.80, w: 3.18, h: 0.24, size: 10.7, color: C.ink, bold: true });
  sticker(s, "МЕМ ПРО ДОФАМИН ≠ НЕЙРОНАУЧНЫЙ ФАКТ", 1.02, 5.67, 4.65, 0.37, { fill: C.red, color: C.white, size: 7.2 });
  stage(s, "brain", { x: 9.08, y: 1.46, s: 3.18, rot: [12, -29, -4], px: 780, capX: 8.53, capY: 4.91, cw: 4.2,
    caption: "КАШТАН: «НЕ СТАВЬ МНЕ ДИАГНОЗ»" });
  cite(s, "[1–3] Rook, 1987; Beatty & Ferrell, 1998; Verplanken & Herabadi, 2001");
  slides.push(s);
}

// 4. Four candidate triggers; all phrased as things to test.
{
  const s = new Slide({ notes: `В анкете можно проверить четыре группы сигналов: FOMO и ограниченные предложения; социальное сравнение; якорение на зачёркнутой цене; удобство оплаты. Они не действуют одинаково на всех, поэтому в презентации это не «кнопки управления человеком», а возможные факторы. Оригинальная картинка с двумя банками — смешная метафора того, как деньги мысленно раскладываются по разным категориям; она не является исследовательским результатом.` });
  chrome(s, 4, "03 · возможные триггеры");
  title(s, "КТО ПОДСОВЫВАЕТ КАШТАНУ «КУПИ»?", { w: 7.9, size: 25.7 });
  const traps = [
    ["FOMO", "«Только сегодня!» — мозг спешит, даже если товар подождёт.", C.red],
    ["СРАВНЕНИЕ", "У блогера есть — и каштану тоже надо?", C.teal],
    ["ЯКОРЬ СКИДКИ", "Старая цена меняет точку сравнения.", C.blue],
    ["ЛЁГКАЯ ОПЛАТА", "Сохранённая карта убирает часть паузы.", C.orange],
  ];
  traps.forEach(([h, d, accent], i) => {
    const col = i % 2, row = Math.floor(i / 2), x = 0.84 + col * 3.64, y = 2.23 + row * 1.42;
    card(s, x, y, 3.36, 1.20, { accent });
    label(s, h, x + 0.18, y + 0.15, 2.95, accent, { size: 8.2 });
    s.text(d, { x: x + 0.18, y: y + 0.45, w: 2.98, h: 0.56, size: 10.7, color: C.ink, bold: true, valign: "middle", lineSpacingMultiple: 1.0 });
  });
  fact(s, 0.85, 5.30, 6.99, 1.02, "Триггер — не приговор: связь зависит от человека и ситуации. Вопрос анкеты звучит «что связано?», а не «кто виноват?»", { tag: "ПРОВЕРЯЕМ, НЕ ОБВИНЯЕМ", size: 10.5, accent: C.lilac });
  stage(s, "phone", { x: 9.00, y: 1.36, s: 2.72, rot: [7, 31, -3], px: 690, capX: 8.54, capY: 4.28, cw: 3.70,
    caption: "КАШТАН УВИДЕЛ «-30%»" });
  memeCard(s, "jars", 9.17, 4.94, 2.36, 1.75, "в голове два бюджета", { accent: C.blue, size: 6.7 });
  cite(s, "[4–7] Rook & Fisher; Przybylski et al.; Tversky & Kahneman; Soman");
  slides.push(s);
}

// 5. Payment framing and BNPL, with the caveat prominent.
{
  const s = new Slide({ notes: `Рассрочка дробит отображение платежа, но не обязательно уменьшает итоговую стоимость. Пример 12 000 рублей = четыре раза по 3 000 рублей — только условная арифметика, не тариф конкретного сервиса. Перед согласием важно сложить платежи, проверить комиссии, даты, просрочку и правила возврата. Картинка «С вас списано 100 рублей» — мем из исходника, а не доказательство частоты списаний или долгов.` });
  chrome(s, 5, "04 · рассрочка и заметность цены");
  title(s, "МАЛЕНЬКИЙ ПЛАТЁЖ. БОЛЬШАЯ СУММА?", { w: 8.0, size: 26.2 });
  card(s, 0.84, 2.22, 6.55, 1.12, { accent: C.teal });
  s.text("12 000 ₽", { x: 1.10, y: 2.43, w: 2.15, h: 0.52, font: "meme", size: 25, color: C.ink, bold: true });
  s.text("=", { x: 3.35, y: 2.42, w: 0.48, h: 0.48, font: "meme", size: 24, color: C.red, bold: true, align: "center" });
  s.text("4 × 3 000 ₽", { x: 3.95, y: 2.43, w: 3.08, h: 0.52, font: "meme", size: 24, color: C.ink, bold: true });
  sticker(s, "УСЛОВНАЯ АРИФМЕТИКА · НЕ ТАРИФ", 1.05, 3.02, 3.75, 0.22, { fill: C.yellow, size: 6.8 });
  s.text("Перед оплатой проверь:", { x: 0.90, y: 3.67, w: 5.0, h: 0.30, font: "meme", size: 12.2, color: C.blue, bold: true });
  const checks = [
    ["Полную сумму", "сколько уйдёт за весь срок?"],
    ["Даты и комиссии", "совпадают ли с бюджетом месяца?"],
    ["Последствия просрочки", "что написано в условиях сервиса?"],
  ];
  checks.forEach(([h, d], i) => {
    const y = 4.10 + i * 0.62;
    s.rect({ x: 0.92, y: y + 0.03, w: 0.20, h: 0.20, shape: "rect", fill: i === 0 ? C.red : C.yellow, line: C.ink, lineW: 0.8 });
    s.text(h, { x: 1.28, y, w: 2.14, h: 0.27, font: "meme", size: 9.3, color: C.ink, bold: true });
    s.text(d, { x: 3.44, y, w: 3.75, h: 0.34, font: "body", size: 9.7, color: C.muted });
  });
  memeCard(s, "hamster", 7.88, 1.49, 2.08, 2.15, "с вас списано 100 руб.", { accent: C.red, size: 6.6 });
  stage(s, "paylater", { x: 9.68, y: 3.77, s: 2.35, rot: [13, -30, -2], px: 670, capX: 9.32, capY: 6.20, cw: 3.2,
    caption: "КАШТАН СЛОЖИЛ ПЛАТЕЖИ" });
  cite(s, "[6, 8] Soman, 2001; Thaler, 1999");
  slides.push(s);
}

// 6. Goal and three hypotheses, clearly marked as untested.
{
  const s = new Slide({ notes: `Цель — изучить связи психологических факторов с незапланированными тратами и разработать памятку. Целевая группа проекта — студенты вузов 18–25 лет. H1 предполагает связь FOMO и импульсивности с более частыми незапланированными покупками и использованием рассрочки; H2 — связь социального сравнения со статусными покупками; H3 — возможную связь финансовой грамотности с меньшим риском, без обещания полной защиты. Каштан здесь только маскот, он не участник выборки. Все гипотезы ещё нужно проверять.` });
  chrome(s, 6, "05 · цель и гипотезы");
  title(s, "КАШТАН ПРОВЕРЯЕТ: ЭТО ТОЧНО ФАКТ?", { w: 8.1, size: 25.5 });
  fact(s, 0.84, 2.15, 7.35, 0.76, "Цель: найти связи факторов с незапланированными тратами и подготовить памятку.", { tag: "ЗАДАЧА ПРОЕКТА", size: 10.9, accent: C.teal });
  sticker(s, "ЦЕЛЕВАЯ ГРУППА · СТУДЕНТЫ 18–25 ЛЕТ", 0.90, 3.08, 3.55, 0.34, { fill: C.blue, color: C.white, size: 7.6 });
  const hs = [
    ["H1", "FOMO и импульсивность связаны с более частыми незапланированными покупками / BNPL."],
    ["H2", "Социальное сравнение связано с большим числом статусных покупок."],
    ["H3", "Финансовая грамотность может быть связана с меньшим риском, но не убирает все триггеры."],
  ];
  hs.forEach(([n, t], i) => {
    const y = 3.62 + i * 0.86;
    card(s, 0.84, y, 7.35, 0.69, { accent: i === 2 ? C.lilac : C.yellow });
    s.text(n, { x: 1.03, y: y + 0.18, w: 0.50, h: 0.26, font: "meme", size: 14, color: i === 2 ? C.blue : C.red, bold: true, align: "center" });
    s.text(t, { x: 1.68, y: y + 0.12, w: 6.26, h: 0.46, size: 10.1, color: C.ink, bold: true, valign: "middle" });
  });
  sticker(s, "ПРЕДПОЛОЖЕНИЯ ≠ РЕЗУЛЬТАТЫ", 1.05, 6.29, 3.45, 0.32, { fill: C.red, color: C.white, size: 7.5 });
  stage(s, "chestnut", { x: 9.24, y: 1.48, s: 2.98, rot: [6, -14, 0], px: 760, capX: 8.84, capY: 4.60, cw: 3.82,
    caption: "КАШТАН — МАСКОТ, НЕ РЕСПОНДЕНТ" });
  cite(s, "[3–5] Verplanken & Herabadi; Rook & Fisher; Przybylski et al.");
  slides.push(s);
}

// 7. Method and ethics.
{
  const s = new Slide({ notes: `Предлагается добровольная анонимная онлайн-анкета для не менее чем 50 студентов 18–25 лет. Вопросы касаются частоты незапланированных покупок за 30 дней, FOMO и социального сравнения, использования BNPL и бюджетных навыков. Сначала рассчитываются описательные показатели, затем — ранговая корреляция Спирмена для порядковых ответов. Это план: результаты ещё не собраны. Небольшая выборка самоотчётов не позволяет автоматически обобщать выводы на всех студентов или доказывать причинность.` });
  chrome(s, 7, "06 · как будет устроен опрос");
  title(s, "ОПРОС: КАШТАН НЕ ГАДАЕТ — СПРАШИВАЕТ", { w: 8.15, size: 25.0 });
  sticker(s, "N ≥ 50", 0.88, 2.18, 1.70, 0.63, { fill: C.yellow, color: C.ink, size: 18 });
  s.text("студентов 18–25 лет", { x: 2.80, y: 2.36, w: 3.65, h: 0.32, font: "meme", size: 12.0, color: C.ink, bold: true });
  s.text("добровольно · онлайн · без имени", { x: 0.92, y: 2.95, w: 6.85, h: 0.28, font: "body", size: 11.0, color: C.muted, bold: true });
  const measures = [
    ["ЧАСТОТА", "покупки вне плана за 30 дней", C.yellow],
    ["ТРИГГЕРЫ", "FOMO · сравнение · срочность", C.teal],
    ["ОПЛАТА", "опыт рассрочки / BNPL", C.orange],
    ["НАВЫКИ", "знания о деньгах + бюджет", C.lilac],
  ];
  measures.forEach(([h, d, accent], i) => {
    const col = i % 2, row = Math.floor(i / 2), x = 0.84 + col * 3.68, y = 3.43 + row * 0.93;
    card(s, x, y, 3.40, 0.75, { accent });
    label(s, h, x + 0.16, y + 0.12, 2.95, C.blue, { size: 7.9 });
    s.text(d, { x: x + 0.16, y: y + 0.39, w: 3.05, h: 0.25, size: 9.4, color: C.ink, bold: true });
  });
  s.text("ОБЗОР  →  АНКЕТА  →  ОПИСАТЕЛЬНАЯ СТАТИСТИКА + SPEARMAN  →  ПАМЯТКА", {
    x: 0.88, y: 5.52, w: 7.24, h: 0.28, font: "meme", size: 8.1, color: C.red, bold: true,
  });
  fact(s, 0.84, 5.89, 7.35, 0.71, "Самоотчёт и N ≥ 50 дают предварительную картину; это не портрет всех студентов.", { tag: "ОГРАНИЧЕНИЕ", size: 10.5, accent: C.lilac });
  stage(s, "clipboard", { x: 9.18, y: 1.51, s: 3.02, rot: [8, -28, 1], px: 780, capX: 8.83, capY: 4.67, cw: 3.75,
    caption: "КАШТАН ОТМЕЧАЕТ: ЭТО ПЛАН" });
  cite(s, "метод проекта; анализ связей — ранговая корреляция Спирмена");
  slides.push(s);
}

// 8. Practical pause, explicitly a proposal rather than an observed result.
{
  const s = new Slide({ notes: `Памятка — практическая идея проекта, а не доказанный эффект. Перед несрочной покупкой можно выдержать паузу, проверить полную сумму и спросить себя, была ли вещь в плане. Для рассрочки нужно сверить все даты и условия; рекламные уведомления можно отключить, а карту не сохранять. Цель не в стыде или тотальном запрете, а в том, чтобы вернуть себе время на выбор. Оригинальный мем про «инвестицию в серотонин» здесь только шутливая иллюстрация, не медицинский тезис.` });
  chrome(s, 8, "07 · памятка перед оплатой");
  title(s, "ПАУЗА ПЕРЕД КНОПКОЙ «ОПЛАТИТЬ»", { w: 8.1, size: 26.0 });
  const steps = [
    ["01 · ПАУЗА", "Отложи несрочную покупку на сутки. Желание не запрещаем — просто проверяем позже."],
    ["02 · ПОЛНАЯ ЦЕНА", "Сложи платежи, комиссии и даты. Подходит ли сумма бюджету месяца?"],
    ["03 · БАРЬЕР", "Отключи промо-push, убери сохранённую карту, задай лимит на спонтанные траты."],
  ];
  steps.forEach(([h, d], i) => {
    const y = 2.23 + i * 1.14;
    card(s, 0.84, y, 5.18, 0.91, { accent: i === 0 ? C.red : C.yellow });
    label(s, h, 1.03, y + 0.12, 4.65, i === 0 ? C.red : C.blue, { size: 8.1 });
    s.text(d, { x: 1.03, y: y + 0.40, w: 4.72, h: 0.39, size: 9.8, color: C.ink, bold: true, valign: "middle" });
  });
  memeCard(s, "serotonin", 6.38, 3.40, 2.28, 2.91, "смешно — да. совет — не совсем", { accent: C.teal, size: 6.6 });
  stage(s, "timer", { x: 9.27, y: 1.44, s: 2.98, rot: [12, -30, 1], px: 760, capX: 8.86, capY: 4.56, cw: 3.80,
    caption: "КАШТАН ДАЁТ СЕБЕ 24 ЧАСА" });
  fact(s, 0.84, 5.95, 5.18, 0.66, "Памятка — рекомендация для проверки, не результат опроса.", { tag: "ЧЕСТНАЯ ОГОВОРКА", size: 10.3, accent: C.lilac });
  cite(s, "практическая идея на основе [1, 2, 6]; эффективность ещё предстоит проверить");
  slides.push(s);
}

// 9. Limitations and a humane conclusion.
{
  const s = new Slide({ notes: `Импульсивная покупка — не моральный дефект и не автоматический результат одного рекламного приёма. На неё могут быть связаны и личные привычки, и ситуация, и то, как показана цена. Но у проекта есть ограничения: поперечный опрос не показывает причинность; самоотчёты могут быть неточными; небольшая выборка студентов не представляет всех людей. Мем делает ситуацию узнаваемой, но только собранные данные могут ответить на исследовательский вопрос.` });
  chrome(s, 9, "08 · выводы и ограничения");
  title(s, "МЕМ ПОМОГАЕТ ПОНЯТЬ. НЕ ДОКАЗЫВАЕТ.", { w: 8.15, size: 26.0 });
  const limits = [
    ["САМООТЧЁТ", "люди могут не помнить каждую покупку"],
    ["N ≥ 50", "пилотная выборка не равна всем студентам"],
    ["КОРРЕЛЯЦИЯ ≠ ПРИЧИНА", "опрос одного среза проверяет связи, не причинность"],
  ];
  limits.forEach(([h, d], i) => {
    const y = 2.25 + i * 1.12;
    card(s, 0.84, y, 7.18, 0.88, { accent: i === 2 ? C.red : C.yellow });
    label(s, h, 1.04, y + 0.13, 6.60, i === 2 ? C.red : C.blue, { size: 8.2 });
    s.text(d, { x: 1.04, y: y + 0.43, w: 6.65, h: 0.27, size: 10.0, color: C.ink, bold: true });
  });
  fact(s, 0.84, 5.79, 7.18, 0.78, "Не ищем «виноватого». Ищем связи — и проверяем их честно.", { tag: "ФИНАЛЬНЫЙ ТЕЗИС", size: 11.6, accent: C.teal });
  stage(s, "scales", { x: 9.16, y: 1.42, s: 3.08, rot: [7, -20, 0], px: 770, capX: 8.78, capY: 4.65, cw: 3.82,
    caption: "ВЕСОМЫ — ДАННЫЕ, НЕ МЕМ" });
  cite(s, "ограничения дизайна: самоотчёт, выборка, поперечное исследование");
  slides.push(s);
}

// 10. Sources; the original chestnut image gets the final word.
{
  const s = new Slide({ notes: `Источники — научные работы о порыве к покупке, индивидуальной склонности, социальных нормах, FOMO, оплате и эвристиках. Полные библиографические данные и карта тезисов по слайдам приведены в exports/impulse-buying-3d-sources.md. Каштан и мемы — визуальная рамка, не источник фактов и не участники исследования.` });
  chrome(s, 10, "09 · источники и проверяемость");
  title(s, "НЕ «ПОВЕРЬ КАШТАНУ». ПРОВЕРЬ ИСТОЧНИКИ.", { w: 8.45, size: 24.2 });
  const refs = [
    ["1", "Rook, 1987", "The Buying Impulse · JCR 14(2)"],
    ["2", "Beatty & Ferrell, 1998", "Impulse buying: Modeling its precursors"],
    ["3", "Verplanken & Herabadi, 2001", "Individual differences in impulse buying tendency"],
    ["4", "Rook & Fisher, 1995", "Normative influences on impulsive buying"],
    ["5", "Przybylski et al., 2013", "Motivational, emotional, behavioral correlates of FOMO"],
    ["6", "Soman, 2001", "Effects of payment mechanism on spending behavior"],
    ["7", "Tversky & Kahneman, 1974", "Judgment under uncertainty: Heuristics and biases"],
    ["8", "Thaler, 1999", "Mental accounting matters"],
  ];
  refs.forEach(([n, h, d], i) => {
    const col = i < 4 ? 0 : 1, row = i % 4, x = 0.82 + col * 4.02, y = 2.18 + row * 1.02;
    card(s, x, y, 3.76, 0.89, { accent: i === 5 ? C.red : C.yellow });
    s.text(n, { x: x + 0.14, y: y + 0.16, w: 0.30, h: 0.25, font: "meme", size: 12.5, color: i === 5 ? C.red : C.blue, bold: true, align: "center" });
    s.text(h, { x: x + 0.55, y: y + 0.12, w: 3.02, h: 0.23, font: "meme", size: 7.6, color: C.ink, bold: true });
    s.text(d, { x: x + 0.55, y: y + 0.40, w: 3.03, h: 0.37, size: 8.2, color: C.muted, lineSpacingMultiple: 1.0 });
  });
  stage(s, "books", { x: 9.47, y: 1.35, s: 2.65, rot: [16, -28, 2], px: 600, burst: 1.17, capX: 9.17, capY: 4.12, cw: 3.25,
    caption: "ИСТОЧНИКИ ПРОВЕРЕНЫ" });
  memeCard(s, "chestnut", 9.15, 4.78, 3.35, 1.90, "каштан: «ссылки приложены»", { accent: C.red, size: 7.2 });
  s.text("Полные DOI и карта утверждений по слайдам — в файле источников.", { x: 0.85, y: 6.49, w: 7.7, h: 0.18, size: 8.5, color: C.muted });
  slides.push(s);
}

// Morph choreography: the next exhibit enters from the right, the current one exits left.
for (let i = 0; i < slides.length; i++) {
  const cur = slides[i].hero, nxt = slides[i + 1] && slides[i + 1].hero;
  if (nxt && (!cur || cur.key !== nxt.key)) {
    slides[i].model(nxt.key, { x: SW + 0.55, y: nxt.y + 0.35, s: nxt.s,
      rot: [nxt.rot[0], nxt.rot[1] + 78, nxt.rot[2]], name: `!!m-${nxt.key}`, ghost: true });
  }
  if (cur && slides[i + 1] && (!nxt || nxt.key !== cur.key)) {
    slides[i + 1].model(cur.key, { x: -cur.s - 0.55, y: cur.y + 0.35, s: cur.s,
      rot: [cur.rot[0], cur.rot[1] - 78, cur.rot[2]], name: `!!m-${cur.key}`, ghost: true });
  }
}

const SHARED_GLB = {
  scales: path.join(ROOT, "presentations", "cantillon", "models", "glb", "scales.glb"),
  books: path.join(ROOT, "presentations", "schumpeter", "models", "glb", "books.glb"),
};
function prepareModels() {
  fs.mkdirSync(GLB, { recursive: true });
  fs.mkdirSync(RASTERS, { recursive: true });
  const keys = new Set();
  slides.forEach((s) => s.els.forEach((e) => e.t === "model" && keys.add(e.key)));
  for (const key of keys) {
    const dest = path.join(GLB, key + ".glb");
    if (!fs.existsSync(dest) && SHARED_GLB[key]) fs.copyFileSync(SHARED_GLB[key], dest);
  }
  const missing = [...keys].filter((k) => !fs.existsSync(path.join(GLB, k + ".glb")));
  const env = { ...process.env, LD_LIBRARY_PATH: [process.env.BLENDER_LIBS || "/tmp/bstub", process.env.LD_LIBRARY_PATH || ""].join(":") };
  if (missing.length) {
    console.log("building procedural models:", missing.join(", "));
    execSync(`python3 ${path.join(MODELS, "make_models.py")} ${missing.join(" ")}`, { stdio: "inherit", env });
  }
  let n = 0;
  const jobs = [];
  slides.forEach((s) => s.els.forEach((e) => {
    if (e.t !== "model") return;
    e.id = `m${++n}`;
    if (e.ghost) { e.raster = A("clear.png"); return; }
    let px = e.px || 700;
    if (process.env.FAST) px = Math.max(180, Math.round(px / 3));
    const buf = fs.readFileSync(path.join(GLB, e.key + ".glb"));
    const digest = crypto.createHash("md5").update(buf).update(JSON.stringify([e.rot, px, 3])).digest("hex").slice(0, 10);
    e.raster = path.join(RASTERS, `${e.key}-${digest}.png`);
    if (!fs.existsSync(e.raster) && !jobs.some((j) => j.out === e.raster)) jobs.push({ key: e.key, rot: e.rot, px, out: e.raster });
  }));
  if (jobs.length) {
    console.log(`rendering ${jobs.length} model rasters with Blender Cycles…`);
    const jf = path.join(RASTERS, "_jobs.json");
    fs.writeFileSync(jf, JSON.stringify(jobs));
    execSync(`python3 ${path.join(SCH, "models", "render.py")} ${jf}`, {
      stdio: ["ignore", "ignore", "inherit"], env: { ...env, GLB_DIR: GLB, SAMPLES: process.env.FAST ? "12" : (process.env.SAMPLES || "40") },
    });
    fs.unlinkSync(jf);
  }
  const usedRasters = new Set(slides.flatMap((s) => s.els.filter((e) => e.t === "model" && !e.ghost).map((e) => path.basename(e.raster))));
  for (const f of fs.readdirSync(RASTERS)) if (f.endsWith(".png") && !usedRasters.has(f)) fs.unlinkSync(path.join(RASTERS, f));
}

function writeScript() {
  const heads = ["Я только посмотрю", "От сигнала до оплаты", "Что такое импульсивная покупка", "Возможные триггеры", "Рассрочка и полная сумма", "Цель и гипотезы", "План опроса", "Пауза перед оплатой", "Выводы и ограничения", "Источники"];
  let md = "# Текст выступления — «Я только посмотрю: психология импульсивных трат»\n\n" +
    "10 слайдов; ориентир — 6–7 минут. Мемы и каштан — узнаваемые иллюстрации, не доказательства и не данные опроса. " +
    "Исследование представлено как план: студенты 18–25 лет, целевой минимум N ≥ 50.\n";
  slides.forEach((s, i) => { md += `\n## Слайд ${i + 1} — ${heads[i]}\n\n${s.notes.trim()}\n`; });
  fs.writeFileSync(path.join(ROOT, "exports", "impulse-buying-3d-script.md"), md);
}

function writeSources() {
  const md = `# Источники и карта утверждений — «Я только посмотрю»

## Библиография

1. Rook, D. W. (1987). The Buying Impulse. *Journal of Consumer Research*, 14(2), 189–199. https://doi.org/10.1086/209105
2. Beatty, S. E., & Ferrell, M. E. (1998). Impulse buying: Modeling its precursors. *Journal of Retailing*, 74(2), 169–191. https://doi.org/10.1016/S0022-4359(99)80092-X
3. Verplanken, B., & Herabadi, A. (2001). Individual differences in impulse buying tendency: Feeling and no thinking. *European Journal of Personality*, 15(S1), S71–S83. https://doi.org/10.1002/per.423
4. Rook, D. W., & Fisher, R. J. (1995). Normative influences on impulsive buying behavior. *Journal of Consumer Research*, 22(3), 305–313. https://doi.org/10.1086/209452
5. Przybylski, A. K., Murayama, K., DeHaan, C. R., & Gladwell, V. (2013). Motivational, emotional, and behavioral correlates of fear of missing out. *Computers in Human Behavior*, 29(4), 1841–1848. https://doi.org/10.1016/j.chb.2013.02.014
6. Soman, D. (2001). Effects of payment mechanism on spending behavior: The role of rehearsal and immediacy of payments. *Journal of Consumer Research*, 27(4), 460–474. https://doi.org/10.1086/319621
7. Tversky, A., & Kahneman, D. (1974). Judgment under uncertainty: Heuristics and biases. *Science*, 185(4157), 1124–1131. https://doi.org/10.1126/science.185.4157.1124
8. Thaler, R. H. (1999). Mental accounting matters. *Journal of Behavioral Decision Making*, 12(3), 183–206. https://doi.org/10.1002/(SICI)1099-0771(199909)12:3<183::AID-BDM318>3.0.CO;2-F

## Карта утверждений

| Слайд | Тезис | Основание / оговорка |
|---|---|---|
| 1 | Проект изучает импульсивные траты студентов 18–25 лет | Рамка проекта; это план исследования |
| 2 | Способ оплаты и её момент могут влиять на заметность расхода | [6]; мем про остаток на карте — иллюстрация, не данные |
| 3 | Рабочее определение импульсивной покупки; различие состояния и склонности | [1–3] |
| 4 | FOMO, нормы, ценовые эвристики и способ оплаты рассматриваются как возможные факторы | [4–7]; не гарантированные причины |
| 5 | 12 000 ₽ = 4 × 3 000 ₽ — условная арифметика, не тариф | [6, 8]; проверить комиссии, даты и полные условия |
| 6 | H1–H3 сформулированы как проверяемые связи, не как выводы | План проекта; теоретические конструкты [3–5] |
| 7 | Добровольная анонимная анкета, N ≥ 50; описательная статистика и корреляция Спирмена | Предлагаемый метод; причинность не устанавливает |
| 8 | Пауза и проверка полной цены — рекомендации для дальнейшей проверки | [1, 2, 6]; эффективность в этом проекте пока не измерена |
| 9 | Поперечный самоотчёт и небольшая выборка ограничивают выводы | Ограничения дизайна исследования |
| 10 | Приведена научная база проекта | [1–8] |

## Редакторские примечания

- Числа о рынке BNPL и прогнозах из исходного черновика не перенесены: для них не была указана проверяемая первичная ссылка.
- Пример с рассрочкой — арифметика без комиссии, тарифа или обещания беспроцентности.
- Фразы про «дофамин/серотонин» относятся к мемам, а не к научной модели проекта.
- Каштан — сквозной персонаж-маскот из исходного визуального ряда. Он не респондент и не эмпирическое доказательство. Фотографии/мемы взяты из исходного пользовательского файла и используются только как иллюстрации.
- H1–H3 проверяют связи. Поперечный самоотчёт не доказывает, что фактор вызывает изменение поведения.
- Для реального опроса нужно заранее зафиксировать набор участников, точные формулировки анкеты, согласие, анонимность и обработку данных.
`;
  fs.writeFileSync(path.join(ROOT, "exports", "impulse-buying-3d-sources.md"), md);
}

async function preview() {
  const fontsDir = path.join(SCH, "node_modules", "@fontsource");
  const pages = toHtml(slides, A("."), fontsDir);
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
  if (!want) {
    execSync(`python3 ${path.join(__dirname, "contact_sheet.py")} ${outDir} ${path.join(ROOT, "exports", "impulse-buying-3d-preview.jpg")}`, { stdio: "inherit" });
  }
  console.log("slide previews ->", outDir);
}

async function main() {
  prepareModels();
  const pptxgen = req("pptxgenjs"), JSZip = req("jszip");
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.author = "MyWorkAiBrain";
  pres.subject = "Мемный исследовательский план о психологии импульсивных трат";
  pres.title = "Я только посмотрю — психология импульсивных трат";
  toPptx(pres, slides);
  const zip = await JSZip.loadAsync(await pres.write({ outputType: "nodebuffer" }));
  await injectModels(zip, slides, GLB);
  await injectTiming(zip, slides);
  await dedupeMedia(zip);
  const out = path.join(ROOT, "exports", "impulse-buying-3d-presentation.pptx");
  fs.writeFileSync(out, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE", compressionOptions: { level: 9 } }));
  console.log("wrote", out, (fs.statSync(out).size / 1e6).toFixed(1) + " MB", `${slides.length} slides`);
  writeScript();
  writeSources();
  if (process.argv.includes("--preview")) await preview();
}
main().catch((err) => { console.error(err); process.exit(1); });
