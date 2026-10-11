// 10-slide, Russian-language research presentation about impulse spending.
// Native PowerPoint 3D models are inserted from rigged GLB files; all slide text remains editable.
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
const C = {
  bg: "080E18", white: "F3F2EC", ivory: "E9E5DA", muted: "A8B3C2",
  teal: "59D7CC", teal2: "B5F0E8", coral: "F47D70", gold: "E5B66A",
  card: "111B28", card2: "142233", ink: "08121C", line: "FFFFFF", deep: "0B131D",
};
const slides = [];
const N = 10;

function chrome(s, idx, kicker) {
  s.img(A("stage-bg.jpg"), { x: 0, y: 0, w: SW, h: SH, name: `Background ${idx}` });
  s.line({ x1: L, y1: 0.39, x2: R, y2: 0.39, color: "FFFFFF", lineT: 86, width: 0.8, name: "!!progress-track" });
  const x = L + CW * ((idx - 1) / (N - 1));
  if (x > L + 0.02) s.rect({ x: L, y: 0.375, w: x - L, h: 0.03, fill: C.teal, name: "!!progress-fill" });
  s.rect({ x: x - 0.06, y: 0.33, w: 0.12, h: 0.12, shape: "ellipse", fill: C.coral, line: C.white, lineT: 12, lineW: 0.8, name: "!!progress-dot" });
  s.text(kicker.toUpperCase(), { x: L, y: 0.62, w: 10.9, h: 0.28, size: 9.5, color: C.teal2, bold: true, charSpacing: 2.3, name: `kicker-${idx}` });
  s.line({ x1: L, y1: 6.98, x2: R, y2: 6.98, color: C.line, lineT: 88, width: 0.7, name: "!!footer-line" });
  s.text("ПСИХОЛОГИЯ ПОТРЕБИТЕЛЬСКОГО ВЫБОРА  ·  ИССЛЕДОВАТЕЛЬСКИЙ ПРОЕКТ", {
    x: L, y: 7.08, w: 9.3, h: 0.22, size: 8.5, color: C.muted, charSpacing: 1.35, name: "!!footer-label",
  });
  s.text(`${String(idx).padStart(2, "0")} / ${N}`, {
    x: R - 1.05, y: 7.07, w: 1.05, h: 0.24, size: 9, color: C.muted, align: "right", charSpacing: 1.6, name: "!!page-number",
  });
}

function title(s, t, o = {}) {
  s.text(t, {
    x: o.x ?? L, y: o.y ?? 1.05, w: o.w ?? 7.2, h: o.h ?? 1.02,
    font: "head", size: o.size ?? 32, color: o.color ?? C.white,
    lineSpacingMultiple: 0.96, valign: "top", name: "!!title",
  });
}
function label(s, t, x, y, w, color = C.teal, ag) {
  s.text(t.toUpperCase(), { x, y, w, h: 0.23, size: 8.8, color, bold: true, charSpacing: 1.5, ag });
}
function card(s, x, y, w, h, o = {}) {
  s.rect({ x, y, w, h, fill: o.fill || C.card, fillT: o.fillT ?? 8, line: o.line || C.teal, lineT: o.lineT ?? 76,
    lineW: o.lineW || 0.75, radius: o.radius ?? 0.08, shadow: o.shadow, ag: o.ag, name: o.name });
}
function fact(s, x, y, w, h, body, o = {}) {
  const ag = o.ag ?? 8;
  card(s, x, y, w, h, { fill: C.card2, fillT: 3, line: o.color || C.gold, lineT: 46, lineW: 0.9, ag, shadow: true });
  s.rect({ x, y: y + 0.13, w: 0.055, h: h - 0.26, fill: o.color || C.gold, ag });
  const tag = o.tag || "КЛЮЧЕВАЯ МЫСЛЬ";
  const tw = Math.min(w - 0.5, Math.max(1.3, tag.length * 0.09 + 0.36));
  s.rect({ x: x + 0.23, y: y - 0.12, w: tw, h: 0.25, fill: o.color || C.gold, radius: 0.12, ag });
  s.text("✦  " + tag, { x: x + 0.24, y: y - 0.12, w: tw, h: 0.25, size: 7.8, bold: true, color: C.ink, charSpacing: 1.1, align: "center", valign: "middle", ag });
  const runs = typeof body === "string" ? [{ text: body }] : body;
  s.text(runs, { x: x + 0.27, y: y + 0.10, w: w - 0.48, h: h - 0.16, font: "head", size: o.size || 12.3, color: C.white, valign: "middle", lineSpacingMultiple: 1.03, ag });
}
function cite(s, t) {
  s.text(`ОПОРА: ${t}`, { x: L, y: 6.68, w: 7.2, h: 0.19, size: 8.3, color: C.muted, charSpacing: 0.2 });
}

// Consistent museum-like 3D stage: transparent 3D GLB, soft light, drafting rings and caption.
function stage(s, key, o) {
  const { x, y, s: size, rot } = o;
  const cx = x + size / 2, cy = y + size / 2 + (o.dy || 0);
  const g = size * (o.glow || 1.42);
  s.img(A("glow.png"), { x: cx - g / 2, y: cy - g / 2, w: g, h: g, name: `glow-${slides.length + 1}` });
  const r1 = size * 0.49, r2 = size * 0.61;
  s.rect({ x: cx - r1, y: cy - r1, w: 2 * r1, h: 2 * r1, shape: "ellipse", line: C.teal, lineT: 84, lineW: 0.7, name: `ring-in-${slides.length + 1}` });
  s.rect({ x: cx - r2, y: cy - r2, w: 2 * r2, h: 2 * r2, shape: "ellipse", line: C.gold, lineT: 91, lineW: 0.7, dash: "dash", name: `ring-out-${slides.length + 1}` });
  const shw = size * (o.shw || 0.72), shy = y + size * (o.shy || 0.84);
  s.img(A("shadow.png"), { x: cx - shw / 2, y: shy - shw / 8, w: shw, h: shw / 4, name: `shadow-${slides.length + 1}` });
  const e = s.model(key, { x, y, s: size, rot, name: `!!m-${key}`, px: o.px || Math.round(size * 155) });
  s.hero = { key, x, y, s: size, rot };
  if (o.caption) {
    s.text([{ text: `ОБЪЁМНЫЙ ЭКСПОНАТ  ${String(slides.length + 1).padStart(2, "0")}`, options: { bold: true, color: C.teal, charSpacing: 1.55, breakLine: true } },
      { text: o.caption, options: { color: C.muted } }], {
      x: o.capX ?? (cx - (o.cw || 4.6) / 2), y: o.capY ?? (y + size + 0.08), w: o.cw || 4.6, h: 0.42,
      size: 9, align: o.capAlign || "center", lineSpacingMultiple: 1.0,
    });
  }
  return e;
}
function textRuns(...parts) { return parts.map(([text, options = {}]) => ({ text, options })); }

// ---------------------------------------------------------------------------
// 1. Cover
{
  const s = new Slide({ notes: `Импульсивные траты знакомы почти каждому, но объяснять их одной фразой «не хватает силы воли» слишком просто. На выбор одновременно влияют личные привычки, настроение и то, как устроена покупка: уведомление, ограниченный срок, сохранённая карта или рассрочка. В проекте мы разбираем эти механизмы и планируем проверить их на студенческой выборке 18–25 лет. Это исследовательский план, а не отчёт о готовых результатах. Справа — телефон с витриной и мигающим уведомлением: маленький сигнал, который делает покупку заметной прямо сейчас.` });
  chrome(s, 1, "Психология импульсивных трат  ·  исследовательский проект");
  stage(s, "phone", { x: 7.2, y: 0.86, s: 5.35, rot: [11, -24, -3], px: 920, shy: 0.79,
    caption: "Уведомление превращает витрину в срочное решение", capX: 8.05, capY: 6.26, cw: 4.7, capAlign: "right" });
  s.text("Почему мы", { x: L, y: 1.43, w: 6.7, h: 0.78, font: "head", size: 48, color: C.ivory, name: "!!cover-line-1" });
  s.text("покупаем", { x: L, y: 2.12, w: 6.9, h: 0.9, font: "head", size: 57, color: C.white, name: "!!cover-line-2" });
  s.text("ненужное?", { x: L, y: 2.99, w: 6.9, h: 0.91, font: "head", size: 57, color: C.teal, name: "!!cover-line-3" });
  s.rect({ x: L, y: 4.14, w: 0.9, h: 0.045, fill: C.coral, ag: 1 });
  s.text("Импульсивные траты: ловушки выбора\nи простой план защиты бюджета", {
    x: L, y: 4.34, w: 5.9, h: 0.8, font: "head", italic: true, size: 18, color: C.white, lineSpacingMultiple: 1.05, ag: 1,
  });
  s.text("ПЛАН ИССЛЕДОВАНИЯ  ·  СТУДЕНТЫ 18–25 ЛЕТ", { x: L, y: 5.28, w: 5.9, h: 0.25, size: 10.5, bold: true, color: C.muted, charSpacing: 1.7, ag: 2 });
  fact(s, L, 5.83, 5.75, 0.77, "Покупка — не только характер. На неё влияют человек, сигнал и момент.", { size: 12.3, tag: "ГЛАВНЫЙ ТЕЗИС", ag: 3 });
  slides.push(s);
}

// 2. Relevance
{
  const s = new Slide({ notes: `Почему тема особенно заметна в цифровой среде? Путь от рекламы до платежа теперь часто укладывается в несколько действий. Лента подбрасывает предложение, кнопка ведёт в карточку товара, а сохранённый способ оплаты убирает часть паузы. Если предлагается рассрочка, человек видит отдельные платежи, и общая сумма может оказаться менее заметной — именно влияние способа оплаты изучал Дилеп Соман. Мы не используем в новой версии неподтверждённые цифры рынка BNPL из исходного черновика: без ссылки на первичный отчёт они создают ложную точность. Наш вопрос уже: какие факторы связаны с незапланированными тратами студентов?` });
  chrome(s, 2, "01  ·  почему это важно");
  stage(s, "phone", { x: 8.18, y: 1.30, s: 4.45, rot: [8, -34, 2], px: 820, caption: "Один экран — несколько шагов до оплаты", cw: 4.2 });
  title(s, "От «увидел» до «оплатил» — всё меньше пауз", { w: 7.15, size: 30, h: 0.92 });
  s.text("В интерфейсе покупки складываются три быстрых шага:", { x: L, y: 2.18, w: 6.7, h: 0.35, size: 13.4, color: C.muted });
  const rows = [
    ["01", "Сигнал", "реклама, push-уведомление, тренд"],
    ["02", "Решение", "карточка товара, таймер, «осталось мало»"],
    ["03", "Оплата", "сохранённая карта или разбивка платежа"],
  ];
  rows.forEach(([n, h, d], i) => {
    const y = 2.75 + i * 0.88;
    s.rect({ x: L, y, w: 0.46, h: 0.46, shape: "ellipse", fill: C.teal, fillT: 7, ag: i + 1 });
    s.text(n, { x: L, y: y + 0.05, w: 0.46, h: 0.28, size: 10, bold: true, color: C.ink, align: "center", valign: "middle", ag: i + 1 });
    s.text(h, { x: L + 0.63, y: y - 0.01, w: 1.45, h: 0.33, font: "head", size: 16, color: C.white, ag: i + 1 });
    s.text(d, { x: L + 2.05, y: y + 0.02, w: 4.55, h: 0.4, size: 12.4, color: C.muted, ag: i + 1 });
    if (i < 2) s.line({ x1: L + 0.23, y1: y + 0.47, x2: L + 0.23, y2: y + 0.82, color: C.teal, lineT: 65, width: 1, ag: i + 1 });
  });
  fact(s, L, 5.68, 6.95, 0.83, "Удобство снижает трение. Это не доказывает, что каждый покупатель потратит больше — это повод проверить механизм.", { size: 11.9, tag: "ВОПРОС ПРОЕКТА" });
  cite(s, "[6] Soman, 2001");
  slides.push(s);
}

// 3. Definition and model
{
  const s = new Slide({ notes: `В исследованиях импульсивную покупку обычно описывают как незапланированное решение, сопровождаемое сильным желанием купить здесь и сейчас. Это не синоним любой онлайн-покупки и не медицинский диагноз. Важно различать черту — насколько человеку вообще свойственно действовать импульсивно — и состояние в конкретный момент: он увидел скидку, устал или получил уведомление. Исследовательская модель проста: внешний или внутренний сигнал вызывает порыв, затем следует решение, а после него — удовлетворение, сожаление или нейтральная оценка. Модель помогает задавать вопросы, но не сводит поведение к «дофамину» или слабой воле.` });
  chrome(s, 3, "02  ·  что именно называем импульсивной покупкой");
  stage(s, "brain", { x: 8.22, y: 1.28, s: 4.46, rot: [12, -28, -4], px: 840, caption: "Сигнал встречается с текущим состоянием человека", cw: 4.4 });
  title(s, "Импульс — порыв, а не диагноз", { w: 7.15, size: 32 });
  s.text("Рабочее определение проекта: незапланированное решение купить, сопровождаемое сильным желанием сделать это немедленно.", {
    x: L, y: 2.12, w: 6.85, h: 0.94, font: "head", size: 17, color: C.white, lineSpacingMultiple: 1.04,
  });
  const phases = ["СИГНАЛ", "ПОТЯГ", "КЛИК", "ОЦЕНКА ПОСЛЕ"];
  const pw = [1.34, 1.34, 1.20, 1.70], gap = 0.22;
  let x = L;
  phases.forEach((t, i) => {
    const w = pw[i];
    card(s, x, 3.45, w, 0.62, { fill: i === 1 ? "231C24" : C.card, line: i === 1 ? C.coral : C.teal, lineT: 54, ag: i + 1 });
    s.text(t, { x: x + 0.05, y: 3.63, w: w - 0.10, h: 0.22, size: 8.8, bold: true, color: i === 1 ? C.coral : C.white, align: "center", ag: i + 1 });
    x += w;
    if (i < phases.length - 1) {
      s.text("→", { x: x + 0.01, y: 3.55, w: gap - 0.02, h: 0.32, font: "head", size: 18, color: C.gold, align: "center", ag: i + 1 });
      x += gap;
    }
  });
  card(s, L, 4.42, 3.28, 0.87, { fill: C.card, line: C.teal, lineT: 78, ag: 5 });
  label(s, "СОСТОЯНИЕ", L + 0.2, 4.57, 2.8, C.teal, 5);
  s.text("порыв в конкретный момент", { x: L + 0.2, y: 4.84, w: 2.85, h: 0.25, size: 11.2, color: C.white, ag: 5 });
  card(s, L + 3.48, 4.42, 3.48, 0.87, { fill: C.card, line: C.gold, lineT: 78, ag: 6 });
  label(s, "СКЛОННОСТЬ", L + 3.68, 4.57, 3.0, C.gold, 6);
  s.text("как часто человек поддаётся порыву", { x: L + 3.68, y: 4.84, w: 3.0, h: 0.25, size: 10.8, color: C.white, ag: 6 });
  fact(s, L, 5.73, 6.96, 0.79, "Незапланированная покупка ≠ «слабый характер». Контекст и самоконтроль тоже важны.", { size: 12.2, tag: "ВАЖНО РАЗЛИЧАТЬ" });
  cite(s, "[1–3] Rook, 1987; Beatty & Ferrell, 1998; Verplanken & Herabadi, 2001");
  slides.push(s);
}

// 4. Triggers
{
  const s = new Slide({ notes: `Четыре сигнала могут ускорять решение: FOMO — страх упустить что-то важное; социальное сравнение — желание не отстать от окружения; зачёркнутая цена — якорь, относительно которого новая стоимость кажется выгоднее; простая оплата — меньшая заметность самого расхода. Настроение — не пятый рекламный триггер, а контекст, который может усилить или ослабить порыв. Ни один сигнал не управляет каждым человеком автоматически. Мы рассматриваем их как факторы для анкеты и гипотезы, а не как доказанные причины поведения конкретного студента.` });
  chrome(s, 4, "03  ·  сигналы и когнитивные ловушки");
  stage(s, "phone", { x: 8.18, y: 1.30, s: 4.45, rot: [8, 32, -4], px: 820, caption: "Срочный сигнал заметен — но не решает за нас", cw: 4.45 });
  title(s, "Четыре триггера ускоряют «купить сейчас»", { w: 7.1, size: 29.5, h: 0.92 });
  const traps = [
    ["FOMO", "«Только сегодня» / «осталось 2»", "СРОЧНОСТЬ"],
    ["Социальное сравнение", "Блогер, тренд, чужая покупка", "НОРМЫ"],
    ["Якорь скидки", "Сначала старая цена, потом новая", "ЦЕНА"],
    ["Лёгкая оплата", "Карта сохранена; сумма разбита", "ПЛАТЁЖ"],
  ];
  traps.forEach(([h, d, tag], i) => {
    const col = i % 2, row = Math.floor(i / 2), x = L + col * 3.53, y = 2.28 + row * 1.45;
    const ag = i + 1;
    card(s, x, y, 3.34, 1.23, { fill: C.card, line: i === 0 ? C.coral : C.teal, lineT: 70, ag });
    label(s, tag, x + 0.2, y + 0.16, 2.9, i === 0 ? C.coral : C.teal, ag);
    s.text(h, { x: x + 0.2, y: y + 0.43, w: 2.95, h: 0.3, font: "head", size: 15, color: C.white, ag });
    s.text(d, { x: x + 0.2, y: y + 0.79, w: 2.94, h: 0.32, size: 10.7, color: C.muted, ag });
  });
  fact(s, L, 5.42, 6.9, 0.90, "Триггер — не приговор: эффект зависит от человека, ситуации и того, насколько заметна полная цена.", { size: 11.9, tag: "НЕ ДЕТЕРМИНИЗМ" });
  cite(s, "[4–7] Rook & Fisher, 1995; Przybylski et al., 2013; Tversky & Kahneman, 1974; Soman, 2001");
  slides.push(s);
}

// 5. BNPL and payment salience
{
  const s = new Slide({ notes: `Рассрочка и «оплата частями» полезны, если человеку нужен удобный график, однако формат предъявления суммы меняет то, на что он обращает внимание. В условном примере двенадцать тысяч рублей превращаются в четыре платежа по три тысячи. Арифметически итог тот же, но отдельная часть может казаться психологически легче полной суммы. Исследования способа оплаты показывают, что момент и заметность платежа могут влиять на расходование; это не означает, что любой BNPL обязательно приводит к перерасходу. Практический вывод нейтральный: перед согласием сложить платежи, проверить даты, комиссии и последствия просрочки.` });
  chrome(s, 5, "04  ·  рассрочка и ощущение цены");
  stage(s, "paylater", { x: 8.08, y: 1.34, s: 4.55, rot: [13, -30, -2], px: 900, caption: "Одна покупка — несколько отдельных платежей", cw: 4.5 });
  title(s, "Рассрочка меняет ощущение цены — не сумму", { w: 7.15, size: 29.5, h: 0.96 });
  card(s, L, 2.31, 6.9, 1.16, { fill: "102127", line: C.teal, lineT: 45, ag: 1 });
  s.text("12 000 ₽", { x: L + 0.28, y: 2.51, w: 2.35, h: 0.56, font: "head", size: 26, color: C.white, ag: 1 });
  s.text("→", { x: L + 2.76, y: 2.51, w: 0.52, h: 0.52, font: "head", size: 26, color: C.gold, align: "center", ag: 1 });
  s.text("4 × 3 000 ₽", { x: L + 3.52, y: 2.51, w: 2.95, h: 0.56, font: "head", size: 25, color: C.teal, ag: 1 });
  s.text("Условная арифметика: без комиссий, переплат и индивидуальных условий сервиса.", { x: L + 0.28, y: 3.10, w: 6.28, h: 0.22, size: 8.8, color: C.muted, ag: 1 });
  const checks = [
    ["Сложи полную сумму", "Сколько заплачу за всё, а не за первый платёж?"],
    ["Проверь календарь", "Совпадают ли даты с уже обязательными расходами?"],
    ["Прочитай условия", "Комиссия, просрочка, возврат товара, досрочная оплата."],
  ];
  checks.forEach(([h, d], i) => {
    const y = 3.78 + i * 0.56, ag = i + 2;
    s.rect({ x: L + 0.02, y: y + 0.02, w: 0.18, h: 0.18, shape: "ellipse", fill: i === 0 ? C.coral : C.gold, ag });
    s.text(h, { x: L + 0.34, y, w: 1.85, h: 0.27, size: 11.7, bold: true, color: C.white, ag });
    s.text(d, { x: L + 2.15, y, w: 4.5, h: 0.32, size: 10.9, color: C.muted, ag });
  });
  fact(s, L, 5.66, 6.92, 0.83, "Рассрочка — инструмент, а не бесплатные деньги: сравнивай полную стоимость и даты.", { size: 12.2, tag: "ПРОВЕРКА ПЕРЕД СОГЛАСИЕМ" });
  cite(s, "[6, 8] Soman, 2001; Thaler, 1999");
  slides.push(s);
}

// 6. Aim, audience and hypotheses
{
  const s = new Slide({ notes: `Цель проекта — изучить, какие психологические факторы связаны с незапланированными расходами и покупками в рассрочку у студентов, а затем сделать короткую памятку. Целевая группа — студенты вузов от восемнадцати до двадцати пяти лет: не потому, что все они импульсивны, а потому что именно на этой группе проект собирается провести опрос. Три гипотезы не описывают уже доказанный результат. Первая связывает FOMO и импульсивность с более частыми незапланированными покупками. Вторая проверяет связь социального сравнения со статусными тратами. Третья проверяет, будет ли финансовая грамотность связана с меньшим риском, но не предполагает полной защиты.` });
  chrome(s, 6, "05  ·  исследовательская цель и гипотезы");
  stage(s, "scales", { x: 8.18, y: 1.30, s: 4.45, rot: [7, -20, 0], px: 820, caption: "Ищем баланс факторов, а не «виноватого»", cw: 4.4 });
  title(s, "Три гипотезы — без ярлыков и обещаний результата", { w: 7.12, size: 28.5, h: 1.00 });
  s.text("Цель: изучить связи психологических факторов с незапланированными тратами и подготовить памятку.", {
    x: L, y: 2.22, w: 6.9, h: 0.52, size: 13.2, color: C.white,
  });
  s.rect({ x: L, y: 2.83, w: 6.9, h: 0.36, fill: "12262A", line: C.teal, lineT: 62, radius: 0.08 });
  s.text("ЦЕЛЕВАЯ ГРУППА  ·  студенты вузов 18–25 лет", { x: L + 0.18, y: 2.92, w: 6.55, h: 0.18, size: 9.3, bold: true, color: C.teal2, charSpacing: 0.8 });
  const hs = [
    ["H1", "FOMO и импульсивность связаны с более частыми незапланированными покупками и использованием рассрочки."],
    ["H2", "Социальное сравнение связано с большим числом статусных покупок."],
    ["H3", "Финансовая грамотность может быть связана с меньшим риском, но не обязательно устраняет влияние триггеров."],
  ];
  hs.forEach(([n, t], i) => {
    const y = 3.37 + i * 0.79, ag = i + 1;
    card(s, L, y, 6.9, 0.68, { fill: C.card, line: i === 2 ? C.gold : C.teal, lineT: 70, ag });
    s.text(n, { x: L + 0.18, y: y + 0.17, w: 0.5, h: 0.27, font: "head", size: 15, color: i === 2 ? C.gold : C.teal, ag });
    s.text(t, { x: L + 0.82, y: y + 0.12, w: 5.82, h: 0.48, size: 11.2, color: C.white, valign: "middle", lineSpacingMultiple: 1.0, ag });
  });
  fact(s, L, 5.85, 6.9, 0.67, "Это проверяемые предположения, не результаты проведённого опроса.", { size: 11.5, tag: "СТАТУС РАБОТЫ", ag: 5 });
  cite(s, "[3–5] Verplanken & Herabadi, 2001; Rook & Fisher, 1995; Przybylski et al., 2013");
  slides.push(s);
}

// 7. Method
{
  const s = new Slide({ notes: `Планируем анонимный добровольный онлайн-опрос не менее пятидесяти студентов от восемнадцати до двадцати пяти лет. Вопросы будут касаться частоты незапланированных покупок за последний месяц, FOMO и социального сравнения, опыта оплаты частями, бюджетирования и самооценки финансовых знаний. Сначала опишем выборку и распределения ответов, затем проверим ранговые связи между порядковыми показателями. Это поперечный опрос с самоотчётом: он не показывает, что именно вызвало покупку, и выборка из одного круга не представляет всех студентов. Этапы работы: обзор литературы, анкета, анализ, памятка.` });
  chrome(s, 7, "06  ·  как будет устроено исследование");
  stage(s, "clipboard", { x: 8.16, y: 1.28, s: 4.47, rot: [8, -28, 1], px: 840, caption: "Вопросы → наблюдения → памятка", cw: 4.3 });
  title(s, "Опрос покажет связи, а не причинность", { w: 7.15, size: 30.5 });
  s.text("План: онлайн-анкета · добровольно · без имени", { x: L, y: 2.20, w: 6.7, h: 0.3, size: 12.2, color: C.teal2, bold: true });
  s.text("N ≥ 50", { x: L, y: 2.57, w: 2.0, h: 0.6, font: "head", size: 29, color: C.gold });
  s.text("студентов 18–25 лет", { x: L + 2.05, y: 2.74, w: 4.45, h: 0.3, size: 14, color: C.white });
  const measures = [
    ["Частота", "незапланированные покупки за 30 дней"],
    ["Триггеры", "FOMO, сравнение, срочные предложения"],
    ["Оплата", "использование рассрочки / BNPL"],
    ["Навыки", "самооценка знаний + ведение бюджета"],
  ];
  measures.forEach(([h, d], i) => {
    const col = i % 2, row = Math.floor(i / 2), x = L + col * 3.5, y = 3.26 + row * 0.88, ag = i + 1;
    card(s, x, y, 3.31, 0.74, { fill: C.card, line: i === 2 ? C.coral : C.teal, lineT: 78, ag });
    label(s, h, x + 0.16, y + 0.11, 2.96, i === 2 ? C.coral : C.teal, ag);
    s.text(d, { x: x + 0.16, y: y + 0.36, w: 2.96, h: 0.26, size: 9.8, color: C.white, ag });
  });
  s.text("ОБЗОР  →  АНКЕТА  →  ОПИСАТЕЛЬНАЯ СТАТИСТИКА + SPEARMAN  →  ПАМЯТКА", {
    x: L, y: 5.23, w: 6.9, h: 0.28, size: 8.7, bold: true, color: C.gold, charSpacing: 0.38,
  });
  fact(s, L, 5.67, 6.9, 0.83, "N ≥ 50 и самоотчёт дают предварительную картину; выводы нельзя автоматически переносить на всех студентов.", { size: 11.4, tag: "ОГРАНИЧЕНИЕ ДИЗАЙНА" });
  cite(s, "план проекта; метод анализа — ранговая корреляция Спирмена");
  slides.push(s);
}

// 8. Practical takeaway
{
  const s = new Slide({ notes: `Пока опрос не проведён, памятка — практическое предложение, а не результат эксперимента. Первый шаг — поставить паузу: несрочную вещь добавить в список и вернуться к ней завтра. Второй — проверить три вещи: была ли покупка в плане, какова полная стоимость и не ломает ли платёж бюджет месяца. Для рассрочки отдельно записать все даты. Третий — изменить среду: отключить рекламные уведомления, убрать сохранённую карту или заранее определить сумму на спонтанные покупки. Цель не в тотальном запрете и не в стыде, а в том, чтобы у решения появилась дополнительная минута.` });
  chrome(s, 8, "07  ·  практический результат проекта");
  stage(s, "timer", { x: 8.18, y: 1.28, s: 4.45, rot: [12, -30, 1], px: 820, caption: "Пауза даёт решению время созреть", cw: 4.3 });
  title(s, "Три шага между желанием и оплатой", { w: 7.05, size: 31 });
  const steps = [
    ["ПАУЗА", "Несрочную покупку — в список на 24 часа. Не теряй решение, просто отложи его."],
    ["ПРОВЕРКА", "Нужна ли вещь? Какова полная цена? Вписывается ли она в бюджет месяца?"],
    ["БАРЬЕР", "Отключи промо-push, убери сохранённую карту, задай лимит на покупки «для себя»."],
  ];
  steps.forEach(([h, d], i) => {
    const y = 2.22 + i * 1.10, ag = i + 1;
    s.rect({ x: L, y: y + 0.02, w: 0.48, h: 0.48, shape: "ellipse", fill: i === 0 ? C.coral : C.teal, ag });
    s.text(String(i + 1), { x: L, y: y + 0.13, w: 0.48, h: 0.20, size: 11, bold: true, color: C.ink, align: "center", ag });
    s.text(h, { x: L + 0.69, y: y - 0.01, w: 1.35, h: 0.28, size: 10.2, bold: true, color: i === 0 ? C.coral : C.teal, charSpacing: 1.0, ag });
    s.text(d, { x: L + 2.0, y: y - 0.02, w: 4.75, h: 0.67, size: 11.3, color: C.white, lineSpacingMultiple: 1.0, ag });
    if (i < 2) s.line({ x1: L + 0.24, y1: y + 0.51, x2: L + 0.24, y2: y + 0.94, color: C.teal, lineT: 70, width: 1, ag });
  });
  fact(s, L, 5.66, 6.9, 0.84, "Если выбираешь рассрочку — сначала сложи все платежи и даты. Памятка не заменяет условия договора.", { size: 11.6, tag: "ПАМЯТКА · НЕ РЕЗУЛЬТАТ ОПРОСА" });
  cite(s, "практические барьеры выведены из механизмов [1, 2, 6]; их эффект предстоит проверять");
  slides.push(s);
}

// 9. Takeaways and limits
{
  const s = new Slide({ notes: `Главный вывод проекта — импульсивную покупку полезно рассматривать не как моральный изъян, а как встречу человека и ситуации. На решение могут влиять привычка, эмоции, социальные сигналы и то, как показана оплата. Поэтому одной лекции о бюджете может быть недостаточно: рядом с знаниями нужны простые инструменты, возвращающие паузу. Но мы пока не знаем, какие факторы окажутся сильнее именно в нашей группе, и не можем обещать, что памятка изменит поведение. Для этого сначала нужен опрос, затем — желательно отдельная проверка самой памятки.` });
  chrome(s, 9, "08  ·  вывод и критическая оценка");
  stage(s, "bag", { x: 8.18, y: 1.28, s: 4.45, rot: [10, -29, -2], px: 840, caption: "Вернуть себе не вещь — а время на выбор", cw: 4.35 });
  title(s, "Наша цель — вернуть время на выбор", { w: 7.1, size: 31 });
  const takeaways = [
    ["01", "Покупка = человек × сигнал × момент", "Не сводим решение к «слабой воле» или одному триггеру."],
    ["02", "Знания важны, но их надо применять", "План, полный расчёт цены и пауза делают выбор заметнее."],
    ["03", "Выводы должны выдерживать проверку", "Сначала соберём ответы; только потом оценим гипотезы."],
  ];
  takeaways.forEach(([n, h, d], i) => {
    const y = 2.18 + i * 1.02, ag = i + 1;
    card(s, L, y, 6.9, 0.87, { fill: C.card, line: i === 2 ? C.gold : C.teal, lineT: 76, ag });
    s.text(n, { x: L + 0.17, y: y + 0.18, w: 0.48, h: 0.28, font: "head", size: 16, color: i === 2 ? C.gold : C.teal, ag });
    s.text(h, { x: L + 0.79, y: y + 0.12, w: 5.85, h: 0.29, size: 12.3, bold: true, color: C.white, ag });
    s.text(d, { x: L + 0.79, y: y + 0.48, w: 5.82, h: 0.24, size: 10.1, color: C.muted, ag });
  });
  fact(s, L, 5.66, 6.9, 0.84, "Опрос ещё впереди. Эти рекомендации — проектный продукт, не доказанный эффект вмешательства.", { size: 11.7, tag: "ЧЕСТНОЕ ОГРАНИЧЕНИЕ", color: C.coral });
  cite(s, "ограничения: поперечный самоотчёт, небольшая выборка, отсутствие экспериментальной группы");
  slides.push(s);
}

// 10. Sources
{
  const s = new Slide({ notes: "Слайд с источниками. Полные библиографические данные и карта утверждений по слайдам сохранены в exports/impulse-buying-3d-sources.md." });
  chrome(s, 10, "09  ·  источники и проверяемость");
  title(s, "На чём основаны определения и гипотезы", { w: 8.7, size: 31, h: 0.85 });
  const refs = [
    ["1", "Rook, 1987", "The Buying Impulse. Journal of Consumer Research, 14(2)."],
    ["2", "Beatty & Ferrell, 1998", "Impulse buying: Modeling its precursors. Journal of Retailing, 74(2)."],
    ["3", "Verplanken & Herabadi, 2001", "Individual differences in impulse buying tendency. European Journal of Personality, 15(S1)."],
    ["4", "Rook & Fisher, 1995", "Normative influences on impulsive buying behavior. Journal of Consumer Research, 22(3)."],
    ["5", "Przybylski et al., 2013", "Motivational, emotional, and behavioral correlates of FOMO. Computers in Human Behavior, 29(4)."],
    ["6", "Soman, 2001", "Effects of payment mechanism on spending behavior. Journal of Consumer Research, 27(4)."],
    ["7", "Tversky & Kahneman, 1974", "Judgment under uncertainty: Heuristics and biases. Science, 185(4157)."],
    ["8", "Thaler, 1999", "Mental accounting matters. Journal of Behavioral Decision Making, 12(3)."],
  ];
  refs.forEach(([n, h, d], i) => {
    const col = i < 4 ? 0 : 1, row = i % 4, x = L + col * 4.14, y = 2.15 + row * 1.04, ag = row + 1;
    card(s, x, y, 3.92, 0.91, { fill: C.card, line: i === 5 ? C.coral : C.teal, lineT: 84, ag });
    s.text(n, { x: x + 0.15, y: y + 0.13, w: 0.30, h: 0.25, font: "head", size: 13, color: i === 5 ? C.coral : C.teal, ag });
    s.text(h, { x: x + 0.52, y: y + 0.12, w: 3.20, h: 0.23, size: 9.7, bold: true, color: C.white, ag });
    s.text(d, { x: x + 0.52, y: y + 0.39, w: 3.22, h: 0.40, size: 9, color: C.muted, lineSpacingMultiple: 1.0, ag });
  });
  stage(s, "books", { x: 9.73, y: 2.10, s: 2.90, rot: [16, -28, 2], px: 560, glow: 1.24,
    caption: "Проверяемая база проекта", capX: 9.28, capY: 5.14, cw: 3.8 });
  s.text("Полные DOI, список фактов по слайдам и редакторские примечания — в файле источников.", {
    x: L, y: 6.43, w: 8.35, h: 0.26, size: 9.2, color: C.muted,
  });
  slides.push(s);
}

// Morph choreography: the next exhibit waits outside the right edge; the current one leaves left.
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
  const heads = ["Почему мы покупаем ненужное?", "От увидел до оплатил", "Что такое импульсивная покупка", "Сигналы и ловушки", "Рассрочка и ощущение цены", "Цель и гипотезы", "План опроса", "Памятка перед оплатой", "Вывод и ограничения", "Источники"];
  let md = "# Текст выступления — «Психология импульсивных трат»\n\n" +
    "10 слайдов. Ориентир: 6–7 минут спокойной речи; последний слайд с источниками вслух не читается. " +
    "Это план исследования, а не презентация уже собранных результатов. Анимированные 3D-экспонаты обозначены в тексте.\n";
  slides.forEach((s, i) => { md += `\n## Слайд ${i + 1} — ${heads[i]}\n\n${s.notes.trim()}\n`; });
  fs.writeFileSync(path.join(ROOT, "exports", "impulse-buying-3d-script.md"), md);
}

function writeSources() {
  const md = `# Источники и карта утверждений — «Психология импульсивных трат»

## Библиография

1. Rook, D. W. (1987). The Buying Impulse. *Journal of Consumer Research*, 14(2), 189–199. https://doi.org/10.1086/209105
2. Beatty, S. E., & Ferrell, M. E. (1998). Impulse buying: Modeling its precursors. *Journal of Retailing*, 74(2), 169–191. https://doi.org/10.1016/S0022-4359(99)80092-X
3. Verplanken, B., & Herabadi, A. (2001). Individual differences in impulse buying tendency: Feeling and no thinking. *European Journal of Personality*, 15(S1), S71–S83. https://doi.org/10.1002/per.423
4. Rook, D. W., & Fisher, R. J. (1995). Normative influences on impulsive buying behavior. *Journal of Consumer Research*, 22(3), 305–313. https://doi.org/10.1086/209452
5. Przybylski, A. K., Murayama, K., DeHaan, C. R., & Gladwell, V. (2013). Motivational, emotional, and behavioral correlates of fear of missing out. *Computers in Human Behavior*, 29(4), 1841–1848. https://doi.org/10.1016/j.chb.2013.02.014
6. Soman, D. (2001). Effects of payment mechanism on spending behavior: The role of rehearsal and immediacy of payments. *Journal of Consumer Research*, 27(4), 460–474. https://doi.org/10.1086/319621
7. Tversky, A., & Kahneman, D. (1974). Judgment under uncertainty: Heuristics and biases. *Science*, 185(4157), 1124–1131. https://doi.org/10.1126/science.185.4157.1124
8. Thaler, R. H. (1999). Mental accounting matters. *Journal of Behavioral Decision Making*, 12(3), 183–206. https://doi.org/10.1002/(SICI)1099-0771(199909)12:3<183::AID-BDM318>3.0.CO;2-F

## Карта фактов и тезисов по слайдам

| Слайд | Тезис / содержание | Основание |
|---|---|---|
| 1 | Импульсивные траты объясняются взаимодействием человека, сигнала и ситуации; в проекте изучается студенческая группа 18–25 лет | Исследовательская рамка проекта; [1–3] |
| 2 | Способ предъявления и момент оплаты могут менять заметность расхода; точные оценки рынка BNPL не используются | [6]; конкретные оценки BNPL из исходного черновика исключены из-за отсутствия первичной ссылки |
| 3 | Рабочее определение импульсивной покупки; различие между склонностью и состоянием | [1–3] |
| 4 | FOMO, социальные нормы, ценовые эвристики и механизм оплаты рассматриваются как возможные триггеры, но не как гарантированные причины | [4–7] |
| 5 | Пример 12 000 ₽ = 4 × 3 000 ₽ — условная арифметика, не тариф и не обещание беспроцентности; заметность платежа зависит от механизма оплаты | [6, 8] |
| 6 | Цель, целевая группа и H1–H3 — проектные вопросы для проверки, не эмпирические результаты | Исходный замысел пользователя; формулировки гипотез уточнены как корреляционные; обоснование факторов [3–5] |
| 7 | N ≥ 50, добровольная анонимная анкета, самоотчёт, описательная статистика и ранговая корреляция Спирмена — предложенный дизайн | План проекта; оценка склонности опирается на конструкт [3] |
| 8 | Пауза, проверка полной суммы и снижение промо-триггеров — практическая памятка, эффективность которой ещё не проверена этим исследованием | Проектная рекомендация; механизмы [1, 2, 6] |
| 9 | Поперечный самоотчёт и небольшая выборка не позволяют делать причинные выводы или обобщать результаты на всех студентов | Ограничения предлагаемого дизайна исследования |
| 10 | Полный перечень использованной литературы | [1–8] |

## Редакторские примечания

- В исходном файле ekonomika123.pptx были оценки объёма BNPL-рынка и прогноз на 2026 год без указания первичного отчёта. Чтобы не выдавать неподтверждённые числа за факт, они в новую презентацию не перенесены.
- Слоган «бросаю лёгкий дофамин» убран: он упрощает психологический механизм до популярной нейрохимической метафоры. В презентации используется поведенческая модель «сигнал → порыв → решение → оценка после».
- H1–H3 сформулированы как связи. Опрос одного временного среза не может доказать, что FOMO, социальное сравнение или грамотность вызывают изменение покупок.
- Для итоговой работы следует отдельно зафиксировать локальный протокол опроса, способ набора участников, точные формулировки вопросов, порядок согласия/анонимности и правила обработки ответов. Если используются адаптированные шкалы, нужно сохранить формулировки, источник и процедуру адаптации.
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
  pres.subject = "Психология импульсивных трат; план исследования среди студентов";
  pres.title = "Почему мы покупаем ненужное? — 3D-презентация";
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
