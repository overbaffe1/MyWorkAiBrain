// Build the 3D, meme-aware research presentation on impulse spending.
// Output: ../../exports/impulse-spending-3d.pptx + speaker script + sources.
// Each slide contains a native PowerPoint 3D model (.glb), a looping skinned animation,
// and Morph transitions. The original chestnut photo and selected memes are retained.
const path = require("path");
const fs = require("fs");
const crypto = require("crypto");
const { execSync } = require("child_process");
const SCH = path.join(__dirname, "..", "schumpeter");
const req = require("module").createRequire(path.join(SCH, "package.json"));
const { Slide, toPptx, toHtml } = require(path.join(SCH, "lib"));
const { injectModels, injectTiming, dedupeMedia } = require(path.join(SCH, "pptx3d"));

const A = (f) => path.join(__dirname, "assets", f);
const OUT = path.join(__dirname, "../../exports");
const GOLD = "E3B663", GOLD2 = "F3DDAE", WHITE = "F5EFE6", MUTED = "BBAEA6";
const CORAL = "E8866A", MINT = "A4D9C6", CARD = "21131A", DARK = "0D0709", FACT = "251714";
const L = 0.76, R = 12.58, CW = R - L, SW = 13.333, N = 9;
const slides = [];
const slideTitles = [
  "Каштан в корзине",
  "Почему это важно: рассрочка и BNPL",
  "Как срабатывает импульсная покупка",
  "Гипотезы исследования",
  "Цель и задачи проекта",
  "Метод и целевая аудитория",
  "Памятка: пауза до оплаты",
  "Ограничения и честный вывод",
  "Итог и источники",
];
const run = (text, options = {}) => ({ text, options });
const br = (text, options = {}) => ({ text, options: { ...options, breakLine: true } });

function chrome(s, idx, kicker) {
  s.bg = DARK;
  s.img(A("stage-bg.jpg"), { x: 0, y: 0, w: SW, h: 7.5, name: "!!background" });
  const trackY = 0.43, gx = L + CW * ((idx - 1) / (N - 1));
  s.line({ x1: L, y1: trackY, x2: R, y2: trackY, color: "FFFFFF", lineT: 87, width: 0.75, name: "!!track" });
  if (idx > 1) s.rect({ x: L, y: trackY - 0.014, w: gx - L, h: 0.028, fill: GOLD, name: "!!progress" });
  if (kicker) {
    s.rect({ x: L, y: 0.77, w: 0.32, h: 0.035, fill: CORAL, name: "!!kickerbar" });
    s.text(kicker, { x: L + 0.46, y: 0.64, w: 9.8, h: 0.28, size: 10.5, bold: true,
      color: GOLD, charSpacing: 2.5, name: "!!kicker" });
  }
  s.line({ x1: L, y1: 7.0, x2: R, y2: 7.0, color: "FFFFFF", lineT: 88, width: 0.7, name: "!!footline" });
  s.text("ПОВЕДЕНЧЕСКАЯ ЭКОНОМИКА  ·  ПРОЕКТ-ИССЛЕДОВАНИЕ", {
    x: L, y: 7.1, w: 7.6, h: 0.24, size: 8.8, color: MUTED, charSpacing: 1.5, name: "!!footer" });
  s.text(`${String(idx).padStart(2, "0")} / ${N}`, {
    x: R - 1.0, y: 7.1, w: 1.0, h: 0.24, size: 8.8, color: MUTED,
    align: "right", charSpacing: 2, name: "!!pagenum" });
}

function title(s, text, o = {}) {
  s.text(text, { x: o.x ?? L, y: o.y ?? 1.02, w: o.w ?? 7.1, h: o.h ?? 1.0,
    font: "head", size: o.size ?? 32, color: o.color ?? WHITE, bold: o.bold ?? false,
    lineSpacingMultiple: 0.97, name: "!!title", valign: "top" });
}

function card(s, x, y, w, h, o = {}) {
  s.rect({ x, y, w, h, fill: o.fill || CARD, fillT: o.fillT ?? 14,
    line: o.line || GOLD, lineT: o.lineT ?? 72, lineW: o.lineW || 0.8,
    radius: o.radius ?? 0.10, shadow: o.shadow ?? false, ag: o.ag });
}

function label(s, text, x, y, w, color = GOLD, o = {}) {
  s.text(text, { x, y, w, h: o.h || 0.24, size: o.size || 9.5, bold: true,
    color, charSpacing: o.charSpacing ?? 1.8, align: o.align || "left", valign: o.valign || "top", ag: o.ag });
}

function fact(s, x, y, w, h, text, o = {}) {
  card(s, x, y, w, h, { fill: FACT, fillT: 6, line: o.line || CORAL, lineT: 38, lineW: 1, ag: o.ag });
  s.rect({ x: x + 0.16, y: y + 0.17, w: 0.045, h: h - 0.34, fill: o.line || CORAL, ag: o.ag });
  if (o.tag) label(s, o.tag, x + 0.32, y + 0.13, w - 0.54, GOLD, { size: 8.5, ag: o.ag });
  s.text(text, { x: x + 0.32, y: y + (o.tag ? 0.40 : 0.17), w: w - 0.55,
    h: h - (o.tag ? 0.48 : 0.28), font: o.font || "head", size: o.size || 14,
    color: WHITE, italic: o.italic ?? false, valign: "middle", lineSpacingMultiple: 1.02, ag: o.ag });
}

function stage(s, key, o) {
  const { x, y, s: sz } = o;
  const rot = o.rot || [10, -20, 0];
  const cx = x + sz / 2, cy = y + sz / 2 + (o.dy || 0);
  const glow = sz * (o.glow || 1.42);
  s.img(A("glow.png"), { x: cx - glow / 2, y: cy - glow / 2, w: glow, h: glow, name: "!!glow" });
  const r1 = sz * 0.48, r2 = sz * 0.59;
  s.rect({ x: cx - r1, y: cy - r1, w: 2 * r1, h: 2 * r1, shape: "ellipse",
    line: GOLD, lineT: 84, lineW: 0.75, name: "!!ring1" });
  s.rect({ x: cx - r2, y: cy - r2, w: 2 * r2, h: 2 * r2, shape: "ellipse",
    line: GOLD, lineT: 90, lineW: 0.65, dash: "dash", name: "!!ring2" });
  const shw = sz * (o.shw || 0.72), shy = y + sz * (o.shy || 0.83);
  s.img(A("shadow.png"), { x: cx - shw / 2, y: shy - shw / 8, w: shw, h: shw / 4, name: "!!shadow" });
  s.model(key, { x, y, s: sz, rot, name: o.name || `!!m-${key}`, px: o.px || 760, anim: o.anim });
  s.hero = { key, x, y, s: sz, rot };
  if (o.caption) {
    const cw = o.cw || 4.0;
    const capX = o.capX ?? cx - cw / 2;
    const capY = o.capY ?? y + sz * 0.93;
    s.text([br(o.caption[0], { bold: true, color: GOLD, charSpacing: 2 }),
      run(o.caption[1], { color: MUTED })], {
      x: capX, y: capY, w: cw, h: o.capH || 0.48, size: 8.8,
      align: o.capAlign || "center", lineSpacingMultiple: 1.05, ag: o.ag ?? 8 });
  }
}

const MEME_RATIO = {
  "chestnuts-original.jpeg": 600 / 401,
  "meme-100-rub.jpeg": 1,
  "meme-serotonin.jpeg": 735 / 524,
  "meme-budget-jars.jpeg": 736 / 669,
};
function memeCard(s, file, x, y, w, h, caption, o = {}) {
  const pad = o.pad ?? 0.11, foot = o.foot ?? 0.36;
  card(s, x, y, w, h, { fill: "F5EFE6", fillT: 0, line: o.line || "F5EFE6", lineT: 0, radius: 0.06, shadow: true, ag: o.ag });
  const maxW = w - pad * 2, maxH = h - foot - pad * 1.5, ratio = MEME_RATIO[file];
  let iw = maxW, ih = iw / ratio;
  if (ih > maxH) { ih = maxH; iw = ih * ratio; }
  const ix = x + (w - iw) / 2, iy = y + pad + (maxH - ih) / 2;
  s.img(A(file), { x: ix, y: iy, w: iw, h: ih, name: o.name });
  if (caption) s.text(caption, { x: x + pad, y: y + h - foot + 0.02, w: w - pad * 2,
    h: foot - 0.05, size: o.size || 8.4, bold: true, color: DARK,
    align: o.align || "center", valign: "middle", lineSpacingMultiple: 1.0, ag: o.ag });
}

function stepRow(s, n, head, body, x, y, w, o = {}) {
  const h = o.h || 0.84;
  s.text(n, { x, y: y + 0.02, w: 0.52, h: 0.35, font: "head", size: 19,
    color: o.accent || CORAL, bold: true, ag: o.ag });
  s.text(head, { x: x + 0.66, y, w: w - 0.72, h: 0.29, size: o.headSize || 13.4,
    color: WHITE, bold: true, ag: o.ag });
  s.text(body, { x: x + 0.66, y: y + 0.32, w: w - 0.72, h: h - 0.34,
    size: o.bodySize || 10.8, color: MUTED, lineSpacingMultiple: 1.0, ag: o.ag });
}

function chip(s, text, x, y, w, o = {}) {
  s.rect({ x, y, w, h: o.h || 0.34, fill: o.fill || "2E201C", fillT: o.fillT ?? 4,
    line: o.line || CORAL, lineT: o.lineT ?? 42, lineW: 0.8, radius: 0.17, ag: o.ag });
  s.text(text, { x: x + 0.12, y: y + 0.03, w: w - 0.24, h: (o.h || 0.34) - 0.06,
    size: o.size || 8.8, bold: true, color: o.color || GOLD2,
    align: "center", valign: "middle", charSpacing: o.charSpacing ?? 0.7, ag: o.ag });
}

// -----------------------------------------------------------------------------
// 1. TITLE — the source chestnut is retained, and the new 3D Kash mascot opens the talk.
{
  const s = new Slide({ notes: `В оригинале у проекта была простая, узнаваемая интонация: серьёзная тема, рассказанная через мемы и самоиронию. Я её сохраняю, но собираю в одну историю — каштан теперь наш постоянный ревизор корзины. На экране рядом с его новой 3D-версией осталась и исходная фотография каштанов из оригинальной презентации.\nТема проекта — психология импульсивных трат: почему мы покупаем незапланированное и какие цифровые триггеры могут ускорять решение. Это не рассказ о том, что люди «плохо обращаются с деньгами», а план небольшого исследования поведения студентов 18–25 лет. Важно: результаты ещё не собраны, поэтому дальше будут гипотезы и методика, а не выдуманные цифры.` });
  chrome(s, 1, "ПСИХОЛОГИЯ ИМПУЛЬСИВНЫХ ТРАТ  ·  МЕМЫ СОХРАНЕНЫ");
  title(s, "Каштан\nв корзине.", { x: L, y: 1.28, w: 5.8, h: 1.65, size: 50 });
  s.text("ПОЧЕМУ МЫ ПОКУПАЕМ НЕНУЖНОЕ — И КАК ВЕРНУТЬ СЕБЕ ПАУЗУ", {
    x: L + 0.03, y: 3.17, w: 5.7, h: 0.72, font: "head", size: 18,
    color: GOLD2, italic: true, lineSpacingMultiple: 1.03 });
  chip(s, "ПРОЕКТ-ИССЛЕДОВАНИЕ  ·  СТУДЕНТЫ 18–25  ·  ПЛАН N ≥ 50", L + 0.03, 4.07, 5.35, { line: GOLD, size: 8.6 });
  memeCard(s, "chestnuts-original.jpeg", L, 4.75, 2.80, 2.03,
    "ОРИГИНАЛЬНЫЙ КАШТАН — НА МЕСТЕ ✓", { size: 8.2 });
  s.text("Каштан-ревизор:\n«Ты это хотел — или\nтебе показали скидку?»", {
    x: 3.82, y: 5.10, w: 2.86, h: 1.22, font: "head", size: 16,
    color: WHITE, italic: true, lineSpacingMultiple: 1.1 });
  stage(s, "chestnut", { x: 6.80, y: 0.82, s: 5.70, rot: [8, -18, 0], px: 920,
    shy: 0.83, shw: 0.72, caption: ["КАШТАН-РЕВИЗОР", "Машет, моргает и не осуждает"], capX: 7.42, capY: 6.47, cw: 4.45 });
  slides.push(s);
}

// 2. CONTEXT — keep the original BNPL point, cite it and label the estimate correctly.
{
  const s = new Slide({ notes: `Почему эта тема актуальна именно сейчас? В оригинальном проекте был приведён рост BNPL — сервисов оплаты частями. По опубликованной в феврале 2026 года оценке, совокупные транзакции крупнейших таких сервисов в России за 2025 год составили около 940 миллиардов рублей, примерно в два с половиной раза больше оценки за 2024 год. Это именно оценка оборота ряда сервисов, не общий долг домохозяйств и не официальная статистика всех покупок.\nА с первого апреля 2026 года действует федеральный закон номер 283-ФЗ о деятельности сервисов рассрочки. Для нашей темы это контекст: способы оплаты и интерфейс меняются, а решение часто принимается прямо в приложении. Мем «С вас списано 100 рублей» здесь не доказательство, а узнаваемая шутка про мелкие, но повторяющиеся траты.` });
  chrome(s, 2, "01  /  КОНТЕКСТ  ·  ОПЛАТА ЧАСТЯМИ");
  title(s, "Рассрочка стала\nобычным кликом", { w: 6.7, h: 1.22, size: 33 });
  card(s, L, 2.50, 6.62, 1.36, { line: GOLD, lineT: 50, fill: "271719", fillT: 5 });
  s.text("940 млрд ₽", { x: L + 0.24, y: 2.66, w: 2.95, h: 0.58,
    font: "head", size: 35, color: GOLD2, bold: true });
  s.text("Оценка транзакций крупнейших BNPL-сервисов в России за 2025 год: ≈2,5× к 2024-му. [1]", {
    x: L + 3.10, y: 2.70, w: 3.24, h: 0.86, size: 11.5, color: WHITE, lineSpacingMultiple: 1.08 });
  fact(s, L, 4.03, 6.62, 0.84,
    "С 1 апреля 2026 года действует ФЗ № 283-ФЗ о сервисах рассрочки. [2]", {
      tag: "НОВЫЙ КОНТЕКСТ", size: 12.6, line: CORAL });
  memeCard(s, "meme-100-rub.jpeg", L, 5.10, 2.43, 1.73,
    "«С ВАС СПИСАНО 100 ₽» — И ТАК КАЖДЫЙ ДЕНЬ", { size: 7.8, foot: 0.32 });
  s.text("Небольшой платёж выглядит легче\nполной цены. Исследуем, когда\nэто влияет на выбор — без ярлыка\n«у людей нет финансовой грамотности». ", {
    x: 3.48, y: 5.23, w: 3.80, h: 1.30, size: 12.4,
    color: MUTED, lineSpacingMultiple: 1.12 });
  stage(s, "smartphone", { x: 7.72, y: 1.15, s: 4.55, rot: [8, -16, 0], px: 780,
    shy: 0.85, shw: 0.70, caption: ["ЭКРАН ПОКУПКИ", "Уведомление мигает — кнопка ждёт"], capX: 8.0, capY: 6.03, cw: 4.0 });
  s.text("Сноска: оценка «Долями» / публикация о рынке BNPL; это не сумма просрочки. [1]", {
    x: L, y: 6.86, w: 7.0, h: 0.16, size: 7.6, color: MUTED });
  slides.push(s);
}

// 3. MECHANISM — no pop-neuroscience, just a readable behavioral sequence.
{
  const s = new Slide({ notes: `Импульсивная покупка — не синоним любой спонтанной покупки и не диагноз. В исследованиях её связывают с незапланированным решением, сильным желанием купить сразу и меньшим вниманием к последствиям. На решение могут влиять и особенности человека, и контекст: что показал экран, есть ли ощущение срочности, насколько легко оплатить.\nВ этой презентации мы показываем короткую модель для проверки: стимул — например, скидка или рекомендация; чувство «надо сейчас»; упрощённая оплата; затем уже оценка покупки. Это схема гипотезы, не утверждение, что каждый пользователь проходит один и тот же путь. Мем про «инвестиции в серотонин» оставляем как мем, но не сводим психологию к одному нейромедиатору.` });
  chrome(s, 3, "02  /  МЕХАНИЗМ  ·  ОТ СТИМУЛА ДО ЧЕКА");
  title(s, "Импульс — короткий\nмаршрут к клику", { w: 6.9, h: 1.2, size: 33 });
  stepRow(s, "01", "СТИМУЛ", "Пуш, таймер «успей», блогер, знакомая вещь в ленте.", L + 0.04, 2.43, 4.96, { h: 0.82 });
  stepRow(s, "02", "СРОЧНОСТЬ", "«Потом будет поздно» или «у всех уже есть».", L + 0.04, 3.35, 4.96, { h: 0.82 });
  stepRow(s, "03", "КЛИК", "Сохранённая карта и оплата частями сокращают паузу.", L + 0.04, 4.27, 4.96, { h: 0.82 });
  stepRow(s, "04", "ПОСЛЕ", "Радость, «норм» или сожаление — проверим в анкете.", L + 0.04, 5.19, 4.96, { h: 0.82 });
  memeCard(s, "meme-serotonin.jpeg", 5.84, 2.45, 1.84, 2.42,
    "МЕМ ИЗ ОРИГИНАЛА: «ВЛОЖИЛАСЬ В СЕРОТОНИН»", { size: 6.8, foot: 0.34, pad: 0.08 });
  chip(s, "НЕ «СЛАБАЯ ВОЛЯ»  ·  ЧЕЛОВЕК + СИТУАЦИЯ + ИНТЕРФЕЙС", L + 0.04, 6.18, 6.75, { line: CORAL, size: 8.4 });
  stage(s, "cart", { x: 8.18, y: 1.24, s: 4.20, rot: [10, -22, 0], px: 760,
    shy: 0.85, shw: 0.70, caption: ["КОРЗИНА", "Товары сами подпрыгивают к покупке"], capX: 8.28, capY: 5.90, cw: 4.0 });
  s.text("Определения: Rook & Fisher (1995); Verplanken & Herabadi (2001). FOMO: Przybylski et al. (2013). [3][4][7]", {
    x: L, y: 6.79, w: 7.35, h: 0.17, size: 7.6, color: MUTED });
  slides.push(s);
}

// 4. HYPOTHESES — explicitly prospective, not reported findings.
{
  const s = new Slide({ notes: `Теперь — три проверяемые гипотезы. Первая: чем чаще человек испытывает FOMO и чем выше склонность к импульсивным покупкам, тем больше у него незапланированных покупок и опыта оплаты частями. Вторая: социальное сравнение и контент блогеров могут быть связаны с покупками ради статуса или «как у других». Третья: финансовая грамотность может быть связана с меньшей частотой спонтанных трат, но сама по себе не создаёт иммунитет.\nВсе три пункта — именно гипотезы. В публикациях есть основания их изучать, но это не значит, что мы уже получили такой результат на студентах нашего вуза. В небольшом опросе мы сможем говорить об ассоциациях, но не доказывать причинно-следственные связи.` });
  chrome(s, 4, "03  /  ГИПОТЕЗЫ  ·  ЧТО ПРОВЕРИМ");
  title(s, "Гипотезы — вопросы,\nа не готовые ответы", { w: 7.4, h: 1.25, size: 32 });
  const hyps = [
    ["H1", "FOMO + импульсивность", "связаны с большим числом незапланированных покупок и более частым BNPL."],
    ["H2", "Социальное сравнение", "связано со статусными покупками и покупками под влиянием рекомендаций."],
    ["H3", "Финансовая грамотность", "может ослаблять связь, но не даёт автоматического «иммунитета»."],
  ];
  hyps.forEach(([n, head, body], i) => {
    const y = 2.42 + i * 1.20;
    card(s, L, y, 7.05, 0.98, { line: i === 2 ? MINT : GOLD, lineT: 60, fill: "21131A", fillT: 9 });
    s.text(n, { x: L + 0.19, y: y + 0.19, w: 0.60, h: 0.40, font: "head", size: 21, color: i === 2 ? MINT : CORAL, bold: true });
    s.text(head, { x: L + 0.88, y: y + 0.13, w: 5.95, h: 0.28, size: 13, color: WHITE, bold: true });
    s.text(body, { x: L + 0.88, y: y + 0.45, w: 5.93, h: 0.40, size: 10.7, color: MUTED, lineSpacingMultiple: 1.02 });
  });
  chip(s, "КОРРЕЛЯЦИЯ ≠ ПРИЧИНА", L + 0.02, 6.19, 2.55, { line: CORAL, size: 8.8 });
  stage(s, "chestnut", { x: 8.22, y: 1.27, s: 4.18, rot: [8, -18, 0], px: 760,
    shy: 0.85, shw: 0.70, caption: ["КАШТАН СПРАШИВАЕТ", "«Это гипотеза или ты уже купил?»"], capX: 8.28, capY: 5.90, cw: 4.0 });
  s.text("Основания для гипотез: FOMO [4], сравнение [5], финансовая грамотность [6].", {
    x: L, y: 6.79, w: 7.45, h: 0.17, size: 7.7, color: MUTED });
  slides.push(s);
}

// 5. GOAL + TASKS — preserves the original project proposal.
{
  const s = new Slide({ notes: `Цель проекта сохраняется из оригинала: изучить психологические механизмы импульсивных покупок и их связь с финансовым поведением студентов, а затем подготовить понятную памятку. Мы не пытаемся пристыдить человека за чипсы или кружку «по акции». Вопрос другой: что произошло до клика и какую небольшую паузу можно вернуть?\nЧтобы прийти к этой цели, сначала разбираем понятия и источники, затем описываем типичные цифровые триггеры, составляем анкету и собираем ответы, а после аккуратно проверяем гипотезы. Финальный продукт — короткая памятка, которую можно использовать в повседневных покупках. Четыре пункта на слайде — план действий, а не уже завершённые этапы.` });
  chrome(s, 5, "04  /  ПЛАН ПРОЕКТА  ·  ОТ ВОПРОСА К ПАМЯТКЕ");
  title(s, "От теории — к полезной\nпамятке без морали", { w: 7.2, h: 1.2, size: 32 });
  fact(s, L, 2.35, 7.10, 0.94,
    "Понять, какие психологические механизмы и цифровые триггеры связаны с импульсивными тратами студентов.", {
      tag: "ЦЕЛЬ", size: 12.5, line: GOLD });
  const tasks = [
    ["01", "Разобрать теорию", "Импульсивность, FOMO, самоконтроль и поведенческие подсказки."],
    ["02", "Описать контекст", "Реклама, скидки, таймеры, маркетплейсы и BNPL."],
    ["03", "Провести опрос", "Студенты 18–25 лет; целевой минимум — 50 ответов."],
    ["04", "Собрать результат", "Проверить связи и сделать памятку «пауза до оплаты»."],
  ];
  tasks.forEach(([n, h, b], i) => {
    const col = i % 2, row = Math.floor(i / 2), x = L + col * 3.62, y = 3.62 + row * 1.32;
    card(s, x, y, 3.43, 1.10, { line: i === 3 ? CORAL : GOLD, lineT: 72, fill: CARD, fillT: 15 });
    label(s, n, x + 0.20, y + 0.15, 0.55, CORAL, { size: 13, charSpacing: 0 });
    s.text(h, { x: x + 0.78, y: y + 0.15, w: 2.42, h: 0.27, size: 12.2, color: WHITE, bold: true });
    s.text(b, { x: x + 0.78, y: y + 0.49, w: 2.42, h: 0.47, size: 9.7, color: MUTED, lineSpacingMultiple: 1.02 });
  });
  stage(s, "wallet", { x: 8.20, y: 1.35, s: 4.18, rot: [9, -20, 0], px: 760,
    shy: 0.85, shw: 0.7, caption: ["КОШЕЛЁК", "Лучше планировать, чем стыдить"], capX: 8.32, capY: 5.97, cw: 4.0 });
  slides.push(s);
}

// 6. TARGET + METHOD — keep the original audience and N>=50, say clearly it is a plan.
{
  const s = new Slide({ notes: `Аудитория исследования — студенты вузов от 18 до 25 лет. В оригинальном проекте был задан минимум в 50 участников; сохраняем его как плановый порог для учебного, разведочного опроса. Это не репрезентативная выборка всех молодых людей России.\nПланируем добровольную анонимную онлайн-анкету. В ней можно спросить о незапланированных покупках за последний месяц, использовании оплаты частями, реакции на ограниченные скидки и рекомендации в соцсетях, а также о простых практиках бюджета. В анализе начнём с описательной статистики и проверки связей между ответами. Опрос — срез самоотчётов: он не докажет, что именно FOMO «вызвал» покупку. И ещё раз: данных пока нет, этот слайд описывает будущую методику.` });
  chrome(s, 6, "05  /  МЕТОД  ·  ЦЕЛЕВАЯ АУДИТОРИЯ");
  title(s, "Проверяем на студентах —\nне гадаем по мемам", { w: 7.3, h: 1.22, size: 31 });
  const blocks = [
    ["КОГО", "Студенты 18–25 лет", "минимальный целевой объём — N ≥ 50"],
    ["КАК", "Анонимная онлайн-анкета", "участие добровольное; без имён и оценок"],
    ["ЧТО", "Покупки и триггеры", "FOMO, соцсети, импульсивность, бюджет, BNPL"],
    ["АНАЛИЗ", "Сначала — описательная статистика", "затем — связи; не причинные выводы"],
  ];
  blocks.forEach(([tag, head, sub], i) => {
    const y = 2.46 + i * 0.91;
    label(s, tag, L + 0.05, y + 0.03, 1.00, i === 2 ? MINT : GOLD, { size: 8.9 });
    s.text(head, { x: L + 1.18, y, w: 5.72, h: 0.30, size: 12.8, bold: true, color: WHITE });
    s.text(sub, { x: L + 1.18, y: y + 0.33, w: 5.72, h: 0.32, size: 10.5, color: MUTED });
    if (i < blocks.length - 1) s.line({ x1: L + 1.17, y1: y + 0.77, x2: L + 6.80, y2: y + 0.77, color: "FFFFFF", lineT: 90, width: 0.5 });
  });
  chip(s, "ПЛАН ИССЛЕДОВАНИЯ  ·  ДАННЫЕ ЕЩЁ НЕ СОБРАНЫ", L + 0.05, 6.22, 5.90, { line: CORAL, color: GOLD2, size: 8.6 });
  stage(s, "smartphone", { x: 8.20, y: 1.25, s: 4.18, rot: [8, -16, 0], px: 760,
    shy: 0.85, shw: 0.70, caption: ["АНКЕТА В ТЕЛЕФОНЕ", "Вопросы — да. Выдуманные итоги — нет"], capX: 8.22, capY: 5.90, cw: 4.1 });
  slides.push(s);
}

// 7. PRACTICAL TAKEAWAY — preserve the jars meme and turn it into a useful checklist.
{
  const s = new Slide({ notes: `Памятка — практический выход проекта. Она не обещает, что один лайфхак отменит все спонтанные покупки. Это простые способы вернуть время на выбор. Первый вопрос: я хотел эту вещь до того, как увидел скидку или рекомендацию? Второй: купил бы её по полной цене и завтра? Третий: могу ли я оплатить её целиком, не ухудшая обязательные платежи?\nДля необязательных покупок можно испытать правило паузы — добавить вещь в список желаний и вернуться к ней через сутки. Убрать сохранённую карту или отключить рекламные уведомления — значит добавить трение. А расходы на «приятное» можно заранее выделить в отдельный бюджет. Поэтому исходный мем с банками — не мораль, а шутливое напоминание: чипсы тоже входят в бюджет, если ты так решил заранее.` });
  chrome(s, 7, "06  /  ПРАКТИКА  ·  ПАУЗА ПЕРЕД ОПЛАТОЙ");
  title(s, "Каштановый анти-импульс:\nтри вопроса до оплаты", { w: 7.35, h: 1.23, size: 31 });
  const checks = [
    ["1", "Я хотел(а) это до того, как увидел(а) скидку?"],
    ["2", "Купил(а) бы это завтра — и по полной цене?"],
    ["3", "Могу оплатить всю сумму без нового долга?"],
  ];
  checks.forEach(([n, text], i) => {
    const y = 2.48 + i * 0.91;
    card(s, L, y, 4.18, 0.76, { line: i === 2 ? MINT : GOLD, lineT: 72, fill: CARD, fillT: 12 });
    s.text(n, { x: L + 0.16, y: y + 0.15, w: 0.42, h: 0.38, size: 19, font: "head", bold: true, color: CORAL });
    s.text(text, { x: L + 0.68, y: y + 0.10, w: 3.30, h: 0.54, size: 10.8, color: WHITE, bold: true, valign: "middle", lineSpacingMultiple: 1.02 });
  });
  memeCard(s, "meme-budget-jars.jpeg", 5.20, 2.55, 2.34, 2.65,
    "ДВА ФОНДА: НА ВАЖНОЕ / НА ЧИПСЫ", { size: 7.4, foot: 0.31 });
  chip(s, "ПАУЗА 24 ЧАСА  ·  ВИШЛИСТ  ·  БЕЗ СОХРАНЁННОЙ КАРТЫ", L, 5.38, 4.18, { line: CORAL, size: 7.9 });
  s.text("Это инструменты выбора, не универсальное лечение и не повод стыдить себя.", {
    x: L + 0.03, y: 5.91, w: 4.16, h: 0.58, size: 9.8, color: MUTED, lineSpacingMultiple: 1.08 });
  stage(s, "wallet", { x: 8.20, y: 1.22, s: 4.18, rot: [9, -20, 0], px: 760,
    shy: 0.85, shw: 0.70, caption: ["КОШЕЛЁК", "Оплата подождёт. Выбор — останется"], capX: 8.25, capY: 5.90, cw: 4.05 });
  slides.push(s);
}

// 8. LIMITATIONS — a real critical appraisal rather than a fake success slide.
{
  const s = new Slide({ notes: `У проекта есть ограничения, и лучше назвать их заранее. Если мы наберём не менее 50 человек через доступные студенческие каналы, выборка будет удобной, а не случайной. Ответы о тратах — самоотчёт: человек может забыть покупку или округлить сумму. Один опрос показывает связи в конкретный момент, но не объясняет причину и следствие. Результаты нельзя автоматически переносить на всех студентов и тем более на всех потребителей.\nЗначит, будущий итог должен быть осторожным: проверить, какие факторы в этой группе связаны с незапланированными тратами, и подготовить понятную памятку. Сейчас это план исследования, а не готовые результаты, диагноз или обвинение.` });
  chrome(s, 8, "07  /  ЧЕСТНЫЕ ОГРАНИЧЕНИЯ");
  title(s, "50 ответов — не 50 миллионов", { w: 7.2, h: 0.80, size: 33 });
  s.text("Мини-опрос помогает увидеть сигналы, но не выдаёт их за истину для всех.", {
    x: L, y: 1.91, w: 7.05, h: 0.54, size: 13.2, font: "head", italic: true, color: GOLD2 });
  const limits = [
    ["ВЫБОРКА", "N ≥ 50 — учебный минимум, а не репрезентативность."],
    ["САМООТЧЁТ", "Память и желание выглядеть рациональнее могут искажать ответы."],
    ["ОДИН СРЕЗ", "Связь между факторами не доказывает причинность."],
    ["НЕ ДИАГНОЗ", "Мы изучаем покупки, не ставим психологические ярлыки."],
  ];
  limits.forEach(([head, body], i) => {
    const col = i % 2, row = Math.floor(i / 2), x = L + col * 3.60, y = 2.83 + row * 1.23;
    card(s, x, y, 3.42, 1.03, { line: i === 3 ? MINT : GOLD, lineT: 73, fill: CARD, fillT: 13 });
    label(s, head, x + 0.19, y + 0.16, 3.05, i === 3 ? MINT : GOLD, { size: 8.8 });
    s.text(body, { x: x + 0.19, y: y + 0.47, w: 3.02, h: 0.44, size: 10.4, color: WHITE, lineSpacingMultiple: 1.02 });
  });
  fact(s, L, 5.56, 7.02, 0.83,
    "Цель проекта: вернуть паузу перед оплатой и выбирать без самостыда.", {
      tag: "ОЖИДАЕМЫЙ ПРОДУКТ", size: 12.3, line: CORAL });
  stage(s, "chestnut", { x: 8.22, y: 1.25, s: 4.18, rot: [8, -18, 0], px: 760,
    shy: 0.85, shw: 0.70, caption: ["КАШТАН ЗА ЧЕСТНОСТЬ", "Мем — не метод, но хороший крючок"], capX: 8.22, capY: 5.90, cw: 4.08 });
  slides.push(s);
}

// 9. CLOSE — direct, warm, source-aware and easy to present.
{
  const s = new Slide({ notes: `Итог проекта можно уместить в одну мысль: импульсивная покупка — это не только личное качество и не только реклама. Важны человек, ситуация и устройство интерфейса. Мы планируем проверить три связи на небольшой студенческой выборке и подготовить инструменты, которые возвращают выбор: пауза, список желаний, понятный лимит и проверка полной суммы.\nА каштан остаётся с нами — как в оригинале. Его вопрос перед последним кликом: «Я это планировал? Смогу спокойно оплатить? Захочу ли я это завтра?» Спасибо за внимание. Все источники и полный текст выступления находятся в сопроводительных файлах, а заметки докладчика — внутри презентации.` });
  chrome(s, 9, "08  /  ИТОГ  ·  СПАСИБО ЗА ВНИМАНИЕ");
  title(s, "Сначала пауза.\nПотом оплата.", { x: L, y: 1.24, w: 6.6, h: 1.75, size: 42 });
  s.text("Покупка — это человек + ситуация + интерфейс.\nЦель — не запретить радость, а вернуть себе выбор.", {
    x: L + 0.04, y: 3.25, w: 6.28, h: 0.98, size: 16.5, font: "head",
    color: GOLD2, lineSpacingMultiple: 1.12 });
  chip(s, "КАШТАН СПРАШИВАЕТ: «Я ЭТО ПЛАНИРОВАЛ(А)?»", L + 0.04, 4.52, 5.95, { line: CORAL, size: 8.8 });
  s.text("Спасибо за внимание!", { x: L + 0.06, y: 4.93, w: 5.7, h: 0.38, font: "head", size: 18, italic: true, color: CORAL });
  memeCard(s, "chestnuts-original.jpeg", L, 5.40, 2.48, 1.46,
    "КАШТАН — ЛЕГЕНДА ОРИГИНАЛА ✓", { size: 7.4, foot: 0.27, pad: 0.07 });
  s.text("Источники: [1] оценка BNPL 2025; [2] ФЗ № 283-ФЗ; [3–7] научные работы об импульсивных покупках, FOMO, сравнении и финансовой грамотности.\nПолные библиографические данные и ссылки — в отдельном файле источников.", {
    x: 3.48, y: 5.47, w: 3.38, h: 1.20, size: 9.8, color: MUTED, lineSpacingMultiple: 1.12 });
  stage(s, "chestnut", { x: 7.15, y: 0.82, s: 5.45, rot: [8, -18, 0], px: 900,
    shy: 0.84, shw: 0.72, caption: ["КАШТАН ОСТАЛСЯ", "Мем-легенда оригинала — теперь 3D"], capX: 7.65, capY: 6.40, cw: 4.48 });
  slides.push(s);
}

// Morph choreography: the next 3D exhibit waits outside the right edge; the previous leaves left.
for (let i = 0; i < slides.length; i++) {
  const cur = slides[i].hero, next = slides[i + 1]?.hero;
  if (next && cur && next.key !== cur.key) {
    slides[i].model(next.key, { x: SW + 0.60, y: next.y + 0.32, s: next.s,
      rot: [next.rot[0], next.rot[1] + 78, next.rot[2]], name: `!!m-${next.key}`, ghost: true });
    slides[i + 1].model(cur.key, { x: -cur.s - 0.60, y: cur.y + 0.32, s: cur.s,
      rot: [cur.rot[0], cur.rot[1] - 78, cur.rot[2]], name: `!!m-${cur.key}`, ghost: true });
  }
}

// ---------- 3D assets: generate missing .glb files and poster rasters ----------
const MODELS = path.join(__dirname, "models");
function prepareModels() {
  const glbDir = path.join(MODELS, "glb");
  const env = { ...process.env, GLB_DIR: glbDir,
    LD_LIBRARY_PATH: [process.env.BLENDER_LIBS || "/tmp/bstub", process.env.LD_LIBRARY_PATH || ""].join(":") };
  const keys = new Set();
  slides.forEach((s) => s.els.forEach((e) => e.t === "model" && keys.add(e.key)));
  const missing = [...keys].filter((key) => !fs.existsSync(path.join(glbDir, key + ".glb")));
  if (missing.length) {
    console.log("building 3D models:", missing.join(", "));
    execSync(`python3 ${path.join(MODELS, "make_models.py")} ${missing.join(" ")}`, { stdio: "inherit", env });
  }
  const rasterDir = path.join(MODELS, "rasters");
  fs.mkdirSync(rasterDir, { recursive: true });
  const jobs = [];
  let n = 0;
  slides.forEach((s) => s.els.forEach((e) => {
    if (e.t !== "model") return;
    e.id = `imp${++n}`;
    if (e.ghost) { e.raster = A("clear.png"); return; }
    let px = e.px || Math.round(Math.min(980, Math.max(220, e.s * 165)));
    if (process.env.FAST) px = Math.max(180, Math.round(px / 3));
    const glb = fs.readFileSync(path.join(glbDir, e.key + ".glb"));
    const hash = crypto.createHash("md5").update(glb).update(JSON.stringify([e.rot, px, 3])).digest("hex").slice(0, 10);
    e.raster = path.join(rasterDir, `${e.key}-${hash}.png`);
    if (!fs.existsSync(e.raster) && !jobs.some((j) => j.out === e.raster)) jobs.push({ key: e.key, rot: e.rot, px, out: e.raster });
  }));
  if (jobs.length) {
    console.log(`rendering ${jobs.length} model poster(s) with Blender…`);
    const jobsFile = path.join(rasterDir, "_jobs.json");
    fs.writeFileSync(jobsFile, JSON.stringify(jobs));
    execSync(`python3 ${path.join(SCH, "models", "render.py")} ${jobsFile}`, { stdio: "inherit", env });
    fs.unlinkSync(jobsFile);
  }
  if (!process.env.FAST) {
    const used = new Set(slides.flatMap((s) => s.els.filter((e) => e.t === "model").map((e) => path.basename(e.raster))));
    for (const file of fs.readdirSync(rasterDir)) {
      if (file.endsWith(".png") && !used.has(file)) fs.unlinkSync(path.join(rasterDir, file));
    }
  }
}

// ---------- deliverables ----------
async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  prepareModels();
  const pptxgen = req("pptxgenjs");
  const JSZip = req("jszip");
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.author = "Arena Agent";
  pres.title = "Каштан в корзине — психология импульсивных трат";
  pres.subject = "Учебный проект об импульсивных покупках, BNPL и финансовом поведении студентов";
  pres.company = "";
  toPptx(pres, slides);
  const buf = await pres.write({ outputType: "nodebuffer" });
  const zip = await JSZip.loadAsync(buf);
  await injectModels(zip, slides, path.join(MODELS, "glb"));
  await injectTiming(zip, slides);
  await dedupeMedia(zip);
  const output = path.join(OUT, "impulse-spending-3d.pptx");
  fs.writeFileSync(output, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE", compressionOptions: { level: 9 } }));
  console.log("wrote", output, (fs.statSync(output).size / 1e6).toFixed(1) + " MB", slides.length, "slides");
  writeScript();
  writeSources();
  if (process.argv.includes("--preview")) await preview();
}

function writeScript() {
  let md = "# Текст выступления — «Каштан в корзине»\n\n" +
    "**Тема:** психология импульсивных трат у студентов. **Формат:** 9 слайдов, учебное предложение исследования; " +
    "результаты ещё не собраны. В заметках докладчика к каждому слайду лежит тот же текст. " +
    "В PowerPoint 365 / 2021+ анимации встроенных 3D-моделей запускаются автоматически; в остальных просмотрщиках может отображаться статичный PNG-fallback.\n";
  slides.forEach((s, i) => { md += `\n## Слайд ${i + 1} — ${slideTitles[i]}\n\n${s.notes.trim()}\n`; });
  fs.writeFileSync(path.join(OUT, "impulse-spending-presentation-script.md"), md);
}

function writeSources() {
  const md = `# Источники и привязка фактов — «Каштан в корзине»

Дата подготовки: 11 октября 2026. Ссылки и формулировки отделяют опубликованные данные от гипотез проекта. В презентации нет выдуманных результатов опроса.

## Использование на слайдах

| № | Слайды | Для чего используется |
|---|---:|---|
| [1] | 2, 9 | Оценка транзакций крупнейших российских BNPL-сервисов за 2025 год: 940 млрд ₽ и рост примерно в 2,5 раза к 2024 году. Это отраслевой расчёт/оценка, не официальный подсчёт всех долгов и не просрочка. |
| [2] | 2, 9 | Дата и правовая рамка Федерального закона № 283-ФЗ: вступил в силу 1 апреля 2026 года (кроме отдельных положений, указанных в законе). |
| [3] | 3, 9 | Исследования импульсивных покупок: роль нормативной оценки ситуации в связи между склонностью и поведением. |
| [4] | 3–4, 9 | Определение FOMO и его психологические/поведенческие корреляты; используется как обоснование гипотезы, а не доказательство результатов этого проекта. |
| [5] | 4, 9 | Исследование социальной оценки/сравнения с инфлюенсерами и импульсивных покупок; обосновывает исследовательский вопрос. |
| [6] | 4, 9 | Работа об ассоциации финансовой грамотности и импульсивных онлайн-покупок у студенческой выборки; эффект нельзя автоматически переносить на нашу выборку. |
| [7] | 3, 9 | Концептуализация склонности к импульсивным покупкам и различение эмоционального и когнитивного аспектов. |

## Полные библиографические данные

1. TAdviser. «Сервисы рассрочки (BNPL) в России»: хроника рынка; данные за 2025 год приведены со ссылкой на оценку сервиса «Долями» / публикацию «Ведомостей» от 3 февраля 2026 года. [Статья TAdviser](https://www.tadviser.ru/index.php/%D0%A1%D1%82%D0%B0%D1%82%D1%8C%D1%8F:%D0%A1%D0%B5%D1%80%D0%B2%D0%B8%D1%81%D1%8B_%D1%80%D0%B0%D1%81%D1%81%D1%80%D0%BE%D1%87%D0%BA%D0%B8_(BNPL)_%D0%B2_%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D0%B8). Дополнительно: [«Ведомости», 03.02.2026](https://www.vedomosti.ru/business/articles/2026/02/03/1173546-rinok-servisov-oplati-pokupok-chastyami-viros).
2. Федеральный закон от 31.07.2025 № 283-ФЗ «О деятельности по предоставлению сервиса рассрочки». Официальное опубликование правовых актов Российской Федерации, номер публикации 0001202507310014. [Официальный текст](http://publication.pravo.gov.ru/Document/View/0001202507310014).
3. Rook, D. W., & Fisher, R. J. (1995). Normative Influences on Impulsive Buying Behavior. *Journal of Consumer Research*, 22(3), 305–313. https://doi.org/10.1086/209452.
4. Przybylski, A. K., Murayama, K., DeHaan, C. R., & Gladwell, V. (2013). Motivational, emotional, and behavioral correlates of fear of missing out. *Computers in Human Behavior*, 29(4), 1841–1848. https://doi.org/10.1016/j.chb.2013.02.014.
5. Mundel, J., Wan, A., & Yang, J. (2024). Processes underlying social comparison with influencers and subsequent impulsive buying: The roles of social anxiety and social media addiction. *Journal of Marketing Communications*, 30(7), 834–851. https://doi.org/10.1080/13527266.2023.2183426.
6. Anisa, N. A., Arifin, S., Setyowati, L., Hidayah, N., & Megasari, A. D. (2020). Financial Literacy on Impulsive Buying Behavior in Y Generation. *Quantitative Economics and Management Studies*, 1(1), 70–75. https://doi.org/10.35877/454RI.qems80. Использовать как один частный эмпирический пример, не как универсальный закон.
7. Verplanken, B., & Herabadi, A. (2001). Individual differences in impulse buying tendency: feeling and no thinking. *European Journal of Personality*, 15(S1), S71–S83. https://doi.org/10.1002/per.423.

## Этические и методологические оговорки

- N ≥ 50 — плановый минимальный объём учебного разведочного опроса, а не гарантия репрезентативности.
- До сбора данных нужно сообщить участникам цель опроса, сделать участие добровольным и не собирать идентификаторы без необходимости.
- Корреляции в одноразовом самоотчётном опросе не доказывают причинность; слайды 4, 6 и 8 это прямо оговаривают.
- Практические шаги на слайде 7 — предложенные пользователю инструменты паузы, а не доказанное лечение или универсальная рекомендация.
`;
  fs.writeFileSync(path.join(OUT, "impulse-spending-sources.md"), md);
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
  const browser = await puppeteer.launch({ args: [...chromium.args, "--allow-file-access-from-files"],
    executablePath: await chromium.executablePath(), headless: true });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  const only = process.argv.find((arg) => arg.startsWith("--only="));
  const wanted = only ? only.slice(7).split(",").map(Number) : null;
  for (let i = 0; i < pages.length; i++) {
    if (wanted && !wanted.includes(i + 1)) continue;
    const html = path.join(outDir, `slide-${String(i + 1).padStart(2, "0")}.html`);
    fs.writeFileSync(html, pages[i]);
    await page.goto("file://" + html, { waitUntil: "networkidle0" });
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: html.replace(".html", ".png") });
    fs.unlinkSync(html);
  }
  await browser.close();
  console.log("previews ->", outDir);
}

main().catch((error) => { console.error(error); process.exit(1); });
