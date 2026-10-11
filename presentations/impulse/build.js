// Rebuilds the user's original ekonomika123.pptx as a ten-slide, editable deck:
// one real animated PowerPoint 3D chestnut mascot per slide, Morph between slides,
// original meme/photo assets retained, speaker notes, source sheet and PNG previews.
const path = require("path");
const fs = require("fs");
const crypto = require("crypto");
const { execSync } = require("child_process");

const HERE = __dirname;
const ROOT = path.resolve(HERE, "../..");
const SCH = path.join(HERE, "..", "schumpeter");
const req = require("module").createRequire(path.join(SCH, "package.json"));
const { Slide, toPptx, toHtml } = require(path.join(SCH, "lib"));
const { injectModels, injectTiming, dedupeMedia } = require(path.join(SCH, "pptx3d"));

const A = (name) => path.join(HERE, "assets", name);
const BG = "F8F5ED", INK = "202A35", MUTED = "64707A", RED = "E64D42", RED_D = "B93532",
  ORANGE = "D28B43", CARD = "FFFDF8", BLUE = "7399AD", GREEN = "3D8560", PALE = "F3E8D9";
const L = 0.78, R = 12.55, SW = 13.333, SH = 7.5, N = 10;
const slides = [];
const REF = {
  1: "Rook, D. W. (1987). The Buying Impulse. Journal of Consumer Research, 14(2), 189–199. https://doi.org/10.1086/209105",
  2: "Verplanken, B., & Herabadi, A. (2001). Individual differences in impulse buying tendency: Feeling and no thinking. European Journal of Personality, 15(S1), S71–S83. https://doi.org/10.1002/per.423",
  3: "Dholakia, U. M. (2000). Temptation and resistance: An integrated model of consumption impulse formation and enactment. Psychology & Marketing, 17(11), 955–982. https://doi.org/10.1002/1520-6793(200011)17:11<955::AID-MAR3>3.0.CO;2-J",
  4: "Soman, D. (2001). Effects of payment mechanism on spending behavior: The role of rehearsal and immediacy of payments. Journal of Consumer Research, 27(4), 460–474. https://doi.org/10.1086/319621",
  5: "Aggarwal, P., Jun, S. Y., & Huh, J. H. (2011). Scarcity messages: A consumer competition perspective. Journal of Advertising, 40(3), 19–30. https://doi.org/10.2753/JOA0091-3367400302",
  6: "Cialdini, R. B. (2009). Influence: Science and Practice (5th ed.). Pearson.",
  7: "Przybylski, A. K., Murayama, K., DeHaan, C. R., & Gladwell, V. (2013). Motivational, emotional, and behavioral correlates of fear of missing out. Computers in Human Behavior, 29(4), 1841–1848. https://doi.org/10.1016/j.chb.2013.02.014",
  8: "Tversky, A., & Kahneman, D. (1981). The framing of decisions and the psychology of choice. Science, 211(4481), 453–458. https://doi.org/10.1126/science.7455683",
};
const TITLES = [
  "Покупка на автопилоте",
  "Между «посмотреть» и оплатой — пара кликов",
  "Не всякая незапланированная покупка импульсивна",
  "Петля: триггер → импульс → чек",
  "Витрина нажимает на разные кнопки",
  "Кого и о чём мы спрашиваем?",
  "Гипотезы: проверяем связи, не виноватых",
  "План: от анкеты до памятки",
  "Пауза вместо чувства вины",
  "Каштан проверил чек. Ваш ход.",
];
const KICKERS = ["СТАРТ", "КОНТЕКСТ", "ОПРЕДЕЛЕНИЕ", "МЕХАНИЗМ", "ТРИГГЕРЫ", "ВОПРОС", "ГИПОТЕЗЫ", "МЕТОД", "ПАМЯТКА", "ИТОГ"];

function chrome(s, idx) {
  s.bg = BG;
  s.img(A("stage-bg.jpg"), { x: 0, y: 0, w: SW, h: SH, name: "!!paper-bg" });
  s.rect({ x: L, y: 0.34, w: 0.14, h: 0.14, shape: "ellipse", fill: RED, name: "!!brand-dot" });
  s.text("ПСИХОЛОГИЯ ИМПУЛЬСИВНЫХ ТРАТ", {
    x: L + 0.28, y: 0.26, w: 5.8, h: 0.25, size: 9, bold: true, color: RED_D,
    charSpacing: 1.8, name: "!!brand",
  });
  s.text(KICKERS[idx - 1], {
    x: 9.2, y: 0.26, w: 2.3, h: 0.25, size: 9, bold: true, color: MUTED,
    align: "right", charSpacing: 1.4, name: "!!section",
  });
  s.text(`${String(idx).padStart(2, "0")} / ${N}`, {
    x: 11.65, y: 0.26, w: 0.9, h: 0.25, size: 9, bold: true, color: RED_D,
    align: "right", charSpacing: 1.2, name: "!!page",
  });
  const progress = (R - L) * idx / N;
  s.rect({ x: L, y: 0.69, w: R - L, h: 0.025, fill: "D6D4CD", name: "!!track" });
  s.rect({ x: L, y: 0.69, w: progress, h: 0.025, fill: RED, name: "!!progress" });
  s.line({ x1: L, y1: 6.97, x2: R, y2: 6.97, color: INK, lineT: 85, width: 0.65, name: "!!footer-line" });
  s.text("УЧЕБНЫЙ ПРОЕКТ  ·  ПЛАН И ГИПОТЕЗЫ, НЕ РЕЗУЛЬТАТЫ ОПРОСА", {
    x: L, y: 7.07, w: 8.2, h: 0.22, size: 8, color: MUTED, charSpacing: 0.6, name: "!!footer",
  });
  s.text("2026", { x: R - 0.55, y: 7.07, w: 0.55, h: 0.22, size: 8, color: MUTED, align: "right", name: "!!year" });
}

function title(s, text, o = {}) {
  s.text(text, {
    x: o.x ?? L, y: o.y ?? 1.02, w: o.w ?? 7.45, h: o.h ?? 1.0,
    font: "body", size: o.size ?? 31, bold: true, color: INK,
    lineSpacingMultiple: 0.94, valign: "top", name: "!!title",
  });
  const y = (o.y ?? 1.02) + (o.underlineY ?? 0.94);
  const w = Math.min(o.underlineW ?? 1.45, o.w ?? 7.45);
  s.line({ x1: o.x ?? L, y1: y, x2: (o.x ?? L) + w, y2: y + 0.015, color: RED, width: 2.3, name: "!!title-underline" });
  s.line({ x1: (o.x ?? L) + 0.06, y1: y + 0.045, x2: (o.x ?? L) + w * 0.83, y2: y + 0.035, color: RED, lineT: 42, width: 0.9 });
}

function text(s, value, x, y, w, h, o = {}) {
  s.text(value, {
    x, y, w, h, font: o.font || "body", size: o.size ?? 13, color: o.color || INK,
    bold: o.bold ?? false, italic: o.italic ?? false, align: o.align || "left",
    valign: o.valign || "top", lineSpacingMultiple: o.lineSpacingMultiple ?? 1.05,
    charSpacing: o.charSpacing, ag: o.ag, name: o.name,
  });
}

function label(s, value, x, y, w, o = {}) {
  text(s, value.toUpperCase(), x, y, w, o.h || 0.22, {
    size: o.size || 8.5, bold: true, color: o.color || RED_D,
    charSpacing: o.charSpacing ?? 1.25, ag: o.ag,
  });
}

function card(s, x, y, w, h, o = {}) {
  s.rect({
    x, y, w, h, fill: o.fill || CARD, fillT: o.fillT ?? 3,
    line: o.line || "D9D3C8", lineT: o.lineT ?? 10, lineW: o.lineW ?? 0.75,
    radius: o.radius ?? 0.08, shadow: o.shadow ?? true, ag: o.ag,
  });
  if (o.tape) {
    s.rect({ x: x + w * 0.38, y: y - 0.055, w: w * 0.23, h: 0.14, fill: o.tape, fillT: 12, rotate: -2 });
  }
}

function fact(s, x, y, w, h, body, o = {}) {
  const ag = o.ag ?? 8;
  card(s, x, y, w, h, { fill: o.fill || "FFF6E8", line: o.line || "E7C89C", lineT: 0, ag });
  s.rect({ x, y: y + 0.10, w: 0.055, h: h - 0.20, fill: RED, ag });
  const tag = o.tag || "КАШТАН НАПОМИНАЕТ";
  const tw = Math.min(w - 0.55, Math.max(1.28, 0.10 * tag.length + 0.25));
  s.rect({ x: x + 0.22, y: y - 0.12, w: tw, h: 0.25, fill: RED, radius: 0.12, ag });
  text(s, tag, x + 0.3, y - 0.11, tw - 0.15, 0.21, { size: 7.5, bold: true, color: "FFFFFF", charSpacing: 0.8, ag });
  text(s, body, x + 0.25, y + 0.19, w - 0.45, h - 0.26, {
    size: o.size || 11.5, color: INK, bold: o.bold ?? false, valign: "middle", ag,
  });
}

function tagPill(s, value, x, y, w, o = {}) {
  s.rect({ x, y, w, h: o.h || 0.32, fill: o.fill || RED, radius: 0.16, fillT: o.fillT ?? 0, ag: o.ag });
  text(s, value, x + 0.10, y + 0.055, w - 0.20, (o.h || 0.32) - 0.08, {
    size: o.size || 8.5, color: o.color || "FFFFFF", bold: true, align: "center", valign: "middle", ag: o.ag,
  });
}

function photoCard(s, src, x, y, w, h, caption, o = {}) {
  card(s, x, y, w, h, { fill: "FFFEFA", line: "D2CCC1", lineT: 4, tape: o.tape || "EBD5B6", ag: o.ag });
  const capH = caption ? (o.capH || 0.25) : 0.05;
  const pad = o.pad || 0.10;
  s.img(src, { x: x + pad, y: y + pad, w: w - 2 * pad, h: h - capH - 1.5 * pad, name: o.name });
  if (caption) text(s, caption, x + pad, y + h - capH - 0.06, w - 2 * pad, capH, {
    size: o.size || 7.8, color: MUTED, bold: o.bold ?? false, align: o.align || "center", valign: "middle", ag: o.ag,
  });
}

function stage(s, o = {}) {
  const x = o.x ?? 8.6, y = o.y ?? 1.43, size = o.size ?? 4.0;
  const cx = x + size / 2, cy = y + size / 2;
  const halo = size * 1.34;
  s.img(A("glow.png"), { x: cx - halo / 2, y: cy - halo / 2, w: halo, h: halo, name: "!!kashtan-glow" });
  s.rect({ x: cx - size * 0.53, y: cy - size * 0.53, w: size * 1.06, h: size * 1.06, shape: "ellipse", line: ORANGE, lineT: 76, lineW: 0.9, name: "!!kashtan-ring" });
  s.img(A("shadow.png"), { x: cx - size * 0.45, y: y + size * 0.84, w: size * 0.9, h: size * 0.19, name: "!!kashtan-shadow" });
  s.model("kashtan", {
    x, y, s: size, rot: o.rot || [10, -18, 0], name: "!!m-kashtan", px: o.px || 820,
  });
  tagPill(s, o.badge || "КАШТАН · РЕВИЗОР ЧЕКА", o.badgeX ?? x + 0.35, o.badgeY ?? y + size - 0.04,
    o.badgeW || size - 0.7, { fill: INK, h: 0.31, size: 7.6, ag: o.ag });
  if (o.quote) text(s, o.quote, x + 0.15, y - 0.15, size - 0.30, 0.36, {
    size: 9.6, bold: true, color: INK, align: "center", valign: "middle", ag: o.ag,
  });
}

function numberedCard(s, x, y, w, h, n, head, body, o = {}) {
  card(s, x, y, w, h, { fill: o.fill, line: o.line, ag: o.ag ?? n });
  text(s, String(n).padStart(2, "0"), x + 0.16, y + 0.14, 0.38, 0.35, {
    font: "head", size: 18, color: o.ncolor || RED, bold: true, ag: o.ag ?? n,
  });
  text(s, head, x + 0.62, y + 0.17, w - 0.78, 0.40, { size: o.headSize || 12, bold: true, color: INK, ag: o.ag ?? n });
  text(s, body, x + 0.18, y + 0.65, w - 0.35, h - 0.75, {
    size: o.bodySize || 10.5, color: MUTED, lineSpacingMultiple: 1.0, ag: o.ag ?? n,
  });
}

function addSlide(s, idx) {
  chrome(s, idx);
  slides.push(s);
}

// 1 — title / callback to the original chestnut picture and meme collage.
{
  const s = new Slide({ notes:
`Сегодня говорим о психологии импульсивных трат. В центре — знакомая сцена: собирался только посмотреть, а в корзине уже несколько вещей. Каштан здесь не научная переменная, а талисман проекта и намеренная отсылка к исходной презентации: оригинальная фотография каштанов сохранена, а рядом появился её 3D-герой. Мы не будем стыдить покупателя и сводить всё к «слабой воле». Посмотрим на сигналы среды, самоконтроль и то, как устроен момент оплаты. В конце предложим несколько способов создать паузу перед решением. Важно: результаты опроса пока не собраны; далее показаны план и гипотезы, а не готовые выводы.` });
  addSlide(s, 1);
  label(s, "Когда шёл только посмотреть", L, 1.12, 5.6, { size: 9.5, color: RED_D });
  title(s, "ПОКУПКА\nНА АВТОПИЛОТЕ", { y: 1.55, w: 6.6, h: 1.65, size: 38, underlineY: 1.52, underlineW: 2.2 });
  text(s, "Почему мы берём лишнее — и как вернуть себе кнопку «пауза».", L, 3.48, 6.2, 0.75, {
    size: 19, color: INK, bold: false, lineSpacingMultiple: 1.0, ag: 1,
  });
  tagPill(s, "КОГНИТИВНЫЕ ИСКАЖЕНИЯ  ·  САМОКОНТРОЛЬ  ·  ДЕНЬГИ", L, 4.55, 5.65, { fill: RED, h: 0.38, size: 8.1, ag: 2 });
  card(s, L, 5.20, 4.40, 0.88, { fill: "FFFDF8", line: "E4D6C3", ag: 3 });
  text(s, "Я: «просто посмотрю»     Корзина: «принято»", L + 0.22, 5.43, 3.95, 0.40, {
    size: 13.2, bold: true, color: INK, align: "center", valign: "middle", ag: 3,
  });
  photoCard(s, A("chestnuts-original.jpg"), 5.52, 4.50, 2.12, 1.53, "ФОТО КАШТАНА ИЗ ОРИГИНАЛА", { pad: 0.09, capH: 0.23, size: 7.0, tape: "EFCBA3" });
  stage(s, { x: 8.45, y: 1.18, size: 4.25, quote: "«Я только за каштанами»", badge: "ЗНАКОМЬТЕСЬ: КАШТАН", badgeY: 5.45, badgeW: 3.45, px: 900 });
  fact(s, L, 6.17, 7.0, 0.57, "Это проект-исследование: сначала проверим гипотезы — потом делаем выводы.", { tag: "ВАЖНО", size: 10.4, ag: 4 });
}

// 2 — motivation/context, retaining the original shopping meme.
{
  const s = new Slide({ notes:
`В исходной версии важность темы объяснялась тем, что покупки всё чаще начинаются в телефоне: подборка, пуш-уведомление, таймер, сохранённая карта, оплата частями. Мы сохраняем саму тему BNPL, но не переносим непроверенные цифры о рынке и законе как установленный факт. Для проекта важен более точный вопрос: какие ситуации участники сами связывают со спонтанными покупками? На картинке — мем из исходника про 106 рублей и пять маркетплейсов. Это смешная иллюстрация узнаваемого поведения, а не доказательство его распространённости. Исследование будет измерять ответы студентов, а не выдавать мем за статистику.` });
  addSlide(s, 2);
  title(s, "«Просто посмотрю» — и уже оплата", { w: 7.55, size: 31, underlineW: 1.65 });
  numberedCard(s, L, 2.30, 2.15, 1.52, 1, "СИГНАЛ", "Уведомление, подборка, яркая витрина", { ag: 1 });
  numberedCard(s, 3.08, 2.30, 2.15, 1.52, 2, "ТОРОПЯТ", "Таймер, «последний шанс», отзывы", { ag: 2 });
  numberedCard(s, 5.38, 2.30, 2.15, 1.52, 3, "ОПЛАТА", "Сохранённая карта или «частями»", { ag: 3 });
  photoCard(s, A("meme-shopping-106.jpg"), L, 4.18, 2.82, 2.27,
    "МЕМ ИЗ ИСХОДНОЙ ПРЕЗЕНТАЦИИ", { pad: 0.12, capH: 0.28, size: 7.3, tape: "F3D0C7" });
  card(s, 3.82, 4.24, 3.72, 1.28, { fill: "EAF1F3", line: "B7CBD4", ag: 4 });
  label(s, "Что проверяем", 4.04, 4.45, 2.9, { color: BLUE, ag: 4 });
  text(s, "Какие триггеры студенты замечают перед незапланированной покупкой?", 4.04, 4.80, 3.20, 0.55, {
    size: 13, bold: true, color: INK, ag: 4,
  });
  fact(s, 3.82, 5.77, 3.72, 0.70, "В исходнике были цифры о BNPL. Без первоисточника мы не выдаём их за факт.", {
    tag: "ЧЕСТНО ПРО ДАННЫЕ", size: 9.6, ag: 5,
  });
  stage(s, { x: 8.55, y: 1.53, size: 3.95, quote: "«Сначала избранное»", badge: "ПРОВЕРЯЕМ, НЕ ОБВИНЯЕМ", badgeW: 3.2, px: 820 });
}

// 3 — operational definition; original chestnut mascot remains central.
{
  const s = new Slide({ notes:
`Важно различать незапланированную покупку и импульсивную. Незапланированная — это любая покупка, которой не было в исходном списке: например, вспомнил дома, что закончился чай. В исследованиях импульсивную покупку обычно описывают как внезапное сильное желание приобрести что-то, при котором обдумывание может сократиться. Это не означает, что каждая такая покупка вредна или что человека надо обвинять. Для анкеты нужно дать участникам одно и то же определение, иначе ответы окажутся несопоставимыми. Определение опирается на работы Рука и Верпланкен с Херабади; буквальную цитату не используем.` });
  addSlide(s, 3);
  title(s, "Незапланированная ≠ импульсивная", { w: 7.6, size: 32, underlineW: 1.8 });
  numberedCard(s, L, 2.38, 2.12, 1.68, 1, "ЗАПЛАНИРОВАНА", "В списке до похода в магазин", { ag: 1, headSize: 11.1, bodySize: 10.2 });
  numberedCard(s, 3.05, 2.38, 2.12, 1.68, 2, "НЕ ЗАПЛАНИРОВАНА", "Вспомнил по пути: «а, ещё чай»", { ag: 2, headSize: 10.4, bodySize: 10.2 });
  numberedCard(s, 5.32, 2.38, 2.12, 1.68, 3, "ИМПУЛЬСИВНАЯ", "Сильное внезапное «хочу сейчас»", { ag: 3, headSize: 10.8, bodySize: 10.2 });
  card(s, L, 4.50, 6.66, 0.86, { fill: "FFFDF8", line: "DED5C7", ag: 4 });
  label(s, "Рабочее определение для анкеты · [1, 2]", L + 0.20, 4.67, 5.9, { color: RED_D, ag: 4 });
  text(s, "Внезапное сильное желание купить, при котором на обдумывание может оставаться меньше времени.", L + 0.20, 4.97, 6.15, 0.28, {
    size: 11.3, bold: true, color: INK, ag: 4,
  });
  fact(s, L, 5.78, 6.66, 0.78, "Импульс — описание ситуации и решения, а не диагноз и не «плохой характер».", {
    tag: "КАШТАН СНЯЛ ОБВИНЕНИЕ", size: 10.5, ag: 5,
  });
  stage(s, { x: 8.63, y: 1.58, size: 3.92, quote: "«Список? Какой список?»", badge: "СНАЧАЛА ОПРЕДЕЛИМ ТЕРМИНЫ", badgeW: 3.25, px: 820 });
}

// 4 — a careful, simplified impulse loop and the original 100-ruble cat meme.
{
  const s = new Slide({ notes:
`На этом слайде — упрощённая рабочая схема, а не универсальный закон. Сначала появляется триггер — скидка, настроение, рекомендация или напоминание. Затем может возникнуть желание купить прямо сейчас. Быстрый checkout сокращает паузу, после которой человек иногда испытывает радость, иногда сожаление, а иногда не чувствует ничего особенного. Теория Дхолакиа рассматривает и ситуацию, и внутреннее желание, и сопротивление импульсу. Вопрос анкеты не будет звучать «вы безвольный?». Мы спросим, как часто покупки возникали внезапно и как часто человек позже сожалел о них. Мем с котом и списанием ста рублей сохранён из оригинала — он иллюстрирует узнаваемый момент, но ничего не доказывает.` });
  addSlide(s, 4);
  title(s, "Петля: триггер → импульс → чек", { w: 7.5, size: 31, underlineW: 1.42 });
  numberedCard(s, L, 2.34, 1.58, 1.55, 1, "ТРИГГЕР", "Таймер / лента / настроение", { ag: 1, headSize: 10.6, bodySize: 9.4 });
  text(s, "→", 2.40, 2.78, 0.25, 0.4, { size: 20, bold: true, color: RED, align: "center", ag: 2 });
  numberedCard(s, 2.68, 2.34, 1.58, 1.55, 2, "ХОЧУ", "«Надо взять сейчас»", { ag: 2, headSize: 10.8, bodySize: 9.6 });
  text(s, "→", 4.34, 2.78, 0.25, 0.4, { size: 20, bold: true, color: RED, align: "center", ag: 3 });
  numberedCard(s, 4.62, 2.34, 1.58, 1.55, 3, "КЛИК", "Оплата почти без паузы", { ag: 3, headSize: 10.8, bodySize: 9.4 });
  text(s, "→", 6.28, 2.78, 0.25, 0.4, { size: 20, bold: true, color: RED, align: "center", ag: 4 });
  numberedCard(s, 6.56, 2.34, 1.58, 1.55, 4, "ПОТОМ", "«Зачем?»", { ag: 4, headSize: 10.8, bodySize: 9.6 });
  card(s, L, 4.25, 4.66, 1.07, { fill: "EAF1F3", line: "B7CBD4", ag: 5 });
  label(s, "Модель для исследования · [3]", L + 0.20, 4.43, 4.1, { color: BLUE, ag: 5 });
  text(s, "Один и тот же триггер не приводит к покупке у каждого человека.", L + 0.20, 4.77, 4.14, 0.36, {
    size: 11.4, color: INK, bold: true, ag: 5,
  });
  photoCard(s, A("meme-charge-100.jpg"), 5.62, 4.25, 2.88, 2.12, "«С ВАС СПИСАНО 100 РУБ» · МЕМ ИЗ ОРИГИНАЛА", {
    pad: 0.13, capH: 0.28, size: 7.2, tape: "F3D0C7",
  });
  fact(s, L, 5.77, 4.66, 0.78, "Наблюдаем паттерн; не клеим ярлык на человека.", { tag: "МЕМ ≠ ДОКАЗАТЕЛЬСТВО", size: 10.4, ag: 6 });
  stage(s, { x: 8.67, y: 1.55, size: 3.90, quote: "«Чек уже в чате»", badge: "ПАУЗА МЕЖДУ «ХОЧУ» И «ОПЛАТИТЬ»", badgeW: 3.5, px: 820 });
}

// 5 — digital cues; includes the original serotonin meme as a playful example only.
{
  const s = new Slide({ notes:
`Мы выделяем несколько возможных сигналов среды, которые можно спросить в анкете: дефицит и таймеры, отзывы и ощущение «все уже купили», сравнение с чужими покупками, а также дистанция между решением и оплатой. Исследования дефицита и социального влияния помогают обосновать, почему такие сигналы стоит измерять, но не позволяют заранее обвинить конкретный интерфейс или доказать причину в нашем маленьком опросе. Мем про «инвестировала в серотонин» мы сохранили из исходника как юмористическую иллюстрацию покупки ради настроения. Это не медицинское объяснение и не буквальное измерение нейромедиаторов. В анкете фиксируем самоотчёт: что человек заметил, что купил и как потом оценил решение.` });
  addSlide(s, 5);
  title(s, "Витрина нажимает на разные кнопки", { w: 7.55, size: 31, underlineW: 1.55 });
  numberedCard(s, L, 2.30, 3.22, 1.30, 1, "ДЕФИЦИТ / СРОЧНОСТЬ", "Таймер, «осталось 2 штуки» · [5]", { ag: 1, headSize: 11.1, bodySize: 10 });
  numberedCard(s, 4.18, 2.30, 3.22, 1.30, 2, "СОЦИАЛЬНОЕ ДОКАЗАТЕЛЬСТВО", "Отзывы, счётчик покупок · [6]", { ag: 2, headSize: 10.0, bodySize: 10 });
  numberedCard(s, L, 3.85, 3.22, 1.30, 3, "FOMO / СРАВНЕНИЕ", "«Все уже взяли» · [7]", { ag: 3, headSize: 10.7, bodySize: 10 });
  numberedCard(s, 4.18, 3.85, 3.22, 1.30, 4, "ОПЛАТА / ФРЕЙМИНГ", "Карта, «частями», цена со скидкой · [4, 8]", { ag: 4, headSize: 10.5, bodySize: 9.8 });
  photoCard(s, A("meme-serotonin.jpg"), 5.66, 5.35, 1.74, 1.36, "МЕМ ИЗ ИСХОДНИКА — НЕ ДИАГНОЗ", { pad: 0.08, capH: 0.23, size: 6.4, tape: "EACEEB" });
  fact(s, L, 5.55, 4.65, 0.98, "Триггеры — переменные исследования, а не ярлыки вроде «шопоголик».", { tag: "НЕ ПУТАЕМ С ПРИЧИНОЙ", size: 10.4, ag: 5 });
  stage(s, { x: 8.66, y: 1.55, size: 3.91, quote: "«Акция заканчивается… когда?»", badge: "ПРОВЕРЯЕМ ТРИГГЕРЫ", badgeW: 3.15, px: 820 });
}

// 6 — audience, research question and ethical survey plan.
{
  const s = new Slide({ notes:
`Целевая группа сохранена из исходного проекта: студенты вузов от восемнадцати до двадцати пяти лет. Планируем набрать не менее пятидесяти добровольцев; это целевой размер для учебного разведочного исследования, а не уже собранная выборка. Главный вопрос: какие ситуации и способы оплаты студенты сами связывают с незапланированными покупками? Анкета будет анонимной и добровольной. Не спрашиваем номер карты, точные банковские данные, имя или логин. Для учебной работы достаточно частоты самоотчётов и оценки ситуаций. Если опрос ещё не прошёл, на защите честно говорим «планируем» и не рисуем результаты заранее.` });
  addSlide(s, 6);
  title(s, "Кого и о чём мы спрашиваем?", { w: 7.50, size: 32, underlineW: 1.55 });
  card(s, L, 2.28, 6.80, 1.13, { fill: "FFFDF8", line: "D8D2C8", ag: 1 });
  label(s, "Исследовательский вопрос", L + 0.22, 2.48, 4.2, { ag: 1 });
  text(s, "Какие триггеры студенты связывают со спонтанными тратами — и что помогает им остановиться?", L + 0.22, 2.82, 6.32, 0.39, {
    size: 13, bold: true, color: INK, ag: 1,
  });
  numberedCard(s, L, 3.73, 3.18, 1.25, 1, "КТО", "Студенты вузов · 18–25 лет", { ag: 2, headSize: 11.5, bodySize: 10.7 });
  numberedCard(s, 4.18, 3.73, 3.18, 1.25, 2, "СКОЛЬКО", "Планируемый набор: N ≥ 50", { ag: 3, headSize: 11.5, bodySize: 10.7 });
  card(s, L, 5.27, 6.80, 0.74, { fill: "EAF1F3", line: "B7CBD4", ag: 4 });
  label(s, "Формат", L + 0.22, 5.43, 1.0, { color: BLUE, ag: 4 });
  text(s, "Анонимный добровольный онлайн-опрос · без ФИО, логинов и данных банковской карты.", L + 1.25, 5.42, 5.25, 0.36, {
    size: 10.7, color: INK, bold: true, ag: 4,
  });
  fact(s, L, 6.19, 6.80, 0.52, "N ≥ 50 — цель набора, не число уже опрошенных.", { tag: "БЕЗ ВЫДУМАННЫХ ДАННЫХ", size: 9.7, ag: 5 });
  stage(s, { x: 8.68, y: 1.55, size: 3.91, quote: "«Личные данные? Не, спасибо»", badge: "АНОНИМНО И ДОБРОВОЛЬНО", badgeW: 3.20, px: 820 });
}

// 7 — measurable hypotheses, explicitly correlational.
{
  const s = new Slide({ notes:
`Три исходные гипотезы уточнены так, чтобы их можно было проверять вопросами анкеты. Первая: выраженность FOMO и склонность к импульсивным покупкам связаны с частотой незапланированных покупок и использованием оплаты частями. Вторая: социальное сравнение связано с самоотчётами о статусных покупках. Третья: финансовая грамотность может быть связана с более частым планированием бюджета, но мы не предполагаем, что знания полностью устраняют импульсы. Это именно гипотезы, а не результаты. Поскольку планируется однократный опрос, мы сможем говорить о связях в ответах, но не докажем, что один фактор вызвал другой.` });
  addSlide(s, 7);
  title(s, "Гипотезы: ищем связи, не виноватых", { w: 7.6, size: 31, underlineW: 1.8 });
  const rows = [
    ["H1", "FOMO / импульсивность связаны с более частыми незапланированными покупками.", "Переменные: частота, FOMO, оплата частями."],
    ["H2", "Социальное сравнение связано с большим числом статусных покупок.", "Переменные: сравнение, категории покупок."],
    ["H3", "Финансовая грамотность связана с планированием, но не гарантирует «иммунитет».", "Переменные: самопроверка знаний, бюджет, импульс."],
  ];
  rows.forEach(([n, h, d], i) => {
    const y = 2.30 + i * 1.00;
    card(s, L, y, 7.00, 0.82, { fill: i === 1 ? "FFF8EF" : "FFFDF8", line: "DAD2C6", ag: i + 1 });
    text(s, n, L + 0.18, y + 0.19, 0.56, 0.37, { font: "head", size: 19, color: RED, bold: true, ag: i + 1 });
    text(s, h, L + 0.84, y + 0.12, 5.88, 0.35, { size: 11.9, color: INK, bold: true, ag: i + 1 });
    text(s, d, L + 0.84, y + 0.49, 5.92, 0.20, { size: 9.5, color: MUTED, ag: i + 1 });
  });
  card(s, L, 5.54, 7.00, 0.65, { fill: "EAF1F3", line: "B7CBD4", ag: 4 });
  label(s, "Как проверяем", L + 0.20, 5.69, 1.48, { color: BLUE, ag: 4 });
  text(s, "Частоты и связи рангов (например, Спирмен). Поперечный опрос не доказывает причинность.", L + 1.75, 5.68, 4.98, 0.32, {
    size: 10, color: INK, bold: true, ag: 4,
  });
  fact(s, L, 6.30, 7.00, 0.42, "До сбора ответов ни одну H1–H3 нельзя объявлять подтверждённой.", { tag: "ГИПОТЕЗА ≠ ВЫВОД", size: 9.3, ag: 5 });
  stage(s, { x: 8.68, y: 1.55, size: 3.91, quote: "«Сначала данные, потом выводы»", badge: "НЕ ПРИДУМЫВАЕМ РЕЗУЛЬТАТЫ", badgeW: 3.35, px: 820 });
}

// 8 — revised task list and project timeline; preserves the original budget meme.
{
  const s = new Slide({ notes:
`План проекта превращаем в последовательность, у которой есть проверяемый результат на каждом шаге. Сначала изучаем литературу и выбираем определения. Затем составляем короткую анкету и проверяем, понятны ли вопросы нескольким добровольцам. После этого собираем ответы студентов, кодируем их без идентификаторов и считаем описательные показатели и простые связи. Наконец, делаем памятку о паузе перед покупкой. Мем из исходника про разные «банки» оставлен как лёгкая иллюстрация конфликта приоритетов, не как рекомендация тратить на одно или другое. В реальном опросе мы не просим раскрывать личные расходы; достаточно диапазонов и самооценок.` });
  addSlide(s, 8);
  title(s, "План: от анкеты до памятки", { w: 7.55, size: 32, underlineW: 1.44 });
  const items = [
    ["Теория", "Термины, триггеры, границы исследования"],
    ["Анкета", "Короткие вопросы + проверка формулировок"],
    ["Опрос", "Добровольные ответы студентов 18–25"],
    ["Анализ", "Частоты, описательная статистика, связи"],
    ["Памятка", "Пауза, бюджет, осознанный checkout"],
  ];
  items.forEach(([head, desc], i) => {
    const y = 2.22 + i * 0.62;
    s.rect({ x: L + 0.18, y: y + 0.08, w: 0.28, h: 0.28, shape: "ellipse", fill: i === 4 ? GREEN : RED, ag: i + 1 });
    if (i < items.length - 1) s.line({ x1: L + 0.32, y1: y + 0.34, x2: L + 0.32, y2: y + 0.70, color: "CFBFB1", width: 1.5, ag: i + 1 });
    text(s, String(i + 1).padStart(2, "0"), L + 0.62, y + 0.05, 0.46, 0.33, { size: 15, bold: true, color: RED_D, ag: i + 1 });
    text(s, head, L + 1.12, y + 0.04, 1.48, 0.29, { size: 12.4, bold: true, color: INK, ag: i + 1 });
    text(s, desc, L + 2.67, y + 0.06, 3.40, 0.34, { size: 10.3, color: MUTED, ag: i + 1 });
  });
  photoCard(s, A("meme-budget-jars.jpg"), 6.18, 4.79, 1.58, 1.72, "БЮДЖЕТНЫЙ МЕМ ИЗ ОРИГИНАЛА", { pad: 0.08, capH: 0.25, size: 6.1, tape: "D7E7D4" });
  fact(s, L, 5.71, 4.96, 0.95, "Собираем минимум данных: никакой банковской тайны в анкете.", { tag: "ЭТИКА ПРЕЖДЕ ВСЕГО", size: 10.2, ag: 6 });
  stage(s, { x: 8.68, y: 1.55, size: 3.91, quote: "«Без личных данных, пожалуйста»", badge: "5 ШАГОВ · 1 ЧЕСТНЫЙ ВЫВОД", badgeW: 3.30, px: 820 });
}

// 9 — practical output, preserving the original money-fall meme without overclaiming.
{
  const s = new Slide({ notes:
`Практический результат — памятка не про запреты и не про стыд, а про возможность добавить несколько секунд на решение. Первый приём — отложить несрочную покупку в избранное и вернуться к ней завтра. Второй — посмотреть, не мешает ли сохранённая карта или автопокупка: если да, убрать быстрый сценарий. Третий — перед оплатой задать три вопроса: действительно ли вещь нужна, подходит ли она бюджету, купил бы я её без таймера и скидки? Это предложения проекта, а не обещание, что каждый приём сработает у всех. После сбора данных памятку можно обсудить со студентами и улучшить. Мем с деньгами из исходника остаётся визуальной шуткой, а не финансовым советом.` });
  addSlide(s, 9);
  title(s, "Пауза вместо чувства вины", { w: 7.55, size: 33, underlineW: 1.38 });
  const tips = [
    ["СОХРАНИ", "Положи несрочную вещь в избранное. Вернись завтра."],
    ["ДОБАВЬ ТРЕНИЕ", "Если быстрый checkout мешает — убери сохранённую карту."],
    ["СПРОСИ СЕБЯ", "Нужно? В бюджете? Взял(а) бы без таймера и скидки?"],
  ];
  tips.forEach(([tag, body], i) => {
    const y = 2.24 + i * 1.02;
    card(s, L, y, 6.86, 0.82, { fill: i === 1 ? "FFF6E8" : "FFFDF8", line: "DAD2C6", ag: i + 1 });
    tagPill(s, tag, L + 0.16, y + 0.23, 1.42, { fill: i === 1 ? ORANGE : RED, h: 0.32, size: 7.7, ag: i + 1 });
    text(s, body, L + 1.76, y + 0.18, 4.84, 0.45, { size: 11.4, bold: true, color: INK, valign: "middle", ag: i + 1 });
  });
  photoCard(s, A("meme-money-fall.jpg"), 5.92, 5.44, 1.78, 1.25, "ДЕНЬГИ ПАДАЮТ, БЮДЖЕТ ПЛАЧЕТ · МЕМ ИЗ ОРИГИНАЛА", { pad: 0.08, capH: 0.27, size: 5.9, tape: "F3D0C7" });
  fact(s, L, 5.55, 4.74, 0.94, "Не запрет, а небольшая пауза возвращает выбор покупателю.", { tag: "ИДЕЯ ПАМЯТКИ", size: 10.5, ag: 5 });
  stage(s, { x: 8.68, y: 1.55, size: 3.91, quote: "«В избранное — и завтра решим»", badge: "НЕ ЗАПРЕТ, А ПАУЗА", badgeW: 2.75, px: 820 });
}

// 10 — conclusion + compact bibliography. Full, slide-mapped citations go to exports/*.md.
{
  const s = new Slide({ notes:
`Подведём итог. Исходная презентация уже содержала удачную интонацию — мемы, каштан и узнаваемые ситуации с покупками. Мы сохранили эту интонацию, но уточнили определения, отделили мемы от данных, добавили проверяемые гипотезы, анонимный план опроса, ограничения и источники. Наш собственный вывод для проекта: разумный контроль — это не только «держи себя в руках», но и среда, в которой можно сделать паузу и проверить бюджет. Это предложение, не результат эксперимента. Каштан возвращает нас к исходному образу и закрывает чек. Спасибо за внимание; после опроса гипотезы нужно будет подтвердить, уточнить или отвергнуть.` });
  addSlide(s, 10);
  title(s, "Каштан проверил чек.\nТеперь — ваш ход.", { w: 7.15, h: 1.55, size: 32, underlineY: 1.43, underlineW: 1.45 });
  card(s, L, 2.93, 7.02, 0.93, { fill: "FFF6E8", line: "E7C89C", ag: 1 });
  label(s, "Наш вывод для проекта", L + 0.20, 3.10, 4.0, { ag: 1 });
  text(s, "Контроль — это не стыд, а понятный бюджет + пауза + меньше кнопок «купить сейчас».", L + 0.20, 3.42, 6.55, 0.32, {
    size: 12.0, bold: true, color: INK, ag: 1,
  });
  text(s, "ИСТОЧНИКИ · КЛЮЧЕВЫЕ РАБОТЫ", L, 4.08, 6.80, 0.22, { size: 8.2, bold: true, color: RED_D, charSpacing: 1.0 });
  const compact = [
    "[1] Rook (1987), The Buying Impulse. J. Consumer Research, 14(2), 189–199.",
    "[2] Verplanken & Herabadi (2001), Impulse buying tendency. Eur. J. Personality, 15(S1), S71–S83.",
    "[3] Dholakia (2000), Temptation and resistance. Psychology & Marketing, 17(11), 955–982.",
    "[4] Soman (2001), Payment mechanism and spending. J. Consumer Research, 27(4), 460–474.",
    "[5] Aggarwal et al. (2011), Scarcity messages. Journal of Advertising, 40(3), 19–30.",
    "[6] Cialdini (2009), Influence: Science and Practice, 5th ed. · [7] Przybylski et al. (2013), FoMO.",
    "[8] Tversky & Kahneman (1981), The framing of decisions. Science, 211(4481), 453–458.",
  ];
  compact.forEach((item, i) => text(s, item, L, 4.35 + i * 0.26, 7.00, 0.22, {
    size: 7.3, color: MUTED, ag: 2 + Math.floor(i / 3),
  }));
  photoCard(s, A("chestnuts-original.jpg"), 7.88, 5.30, 1.75, 1.30, "КАШТАН ИЗ ОРИГИНАЛЬНОГО ФАЙЛА", { pad: 0.08, capH: 0.22, size: 5.9, tape: "EFCBA3" });
  stage(s, { x: 9.46, y: 1.48, size: 3.18, quote: "«Пауза. Потом покупка.»", badge: "СПАСИБО!", badgeW: 1.70, px: 760 });
  fact(s, L, 6.42, 6.80, 0.48, "Сначала соберём ответы — затем сообщим результаты.", { tag: "ПРОЕКТ ПРОДОЛЖАЕТСЯ", size: 9.0, ag: 5 });
}

const MODELS = path.join(HERE, "models");
function prepareModels() {
  const env = {
    ...process.env,
    GLB_DIR: path.join(MODELS, "glb"),
    LD_LIBRARY_PATH: [process.env.BLENDER_LIBS || "/tmp/bstub", process.env.LD_LIBRARY_PATH || ""].filter(Boolean).join(":"),
  };
  const keys = new Set();
  slides.forEach((s) => s.els.forEach((e) => e.t === "model" && keys.add(e.key)));
  const missing = [...keys].filter((key) => !fs.existsSync(path.join(MODELS, "glb", `${key}.glb`)));
  if (missing.length) execSync(`python3 ${path.join(MODELS, "make_models.py")} ${missing.join(" ")}`, { stdio: "inherit", env });

  const jobs = [];
  fs.mkdirSync(path.join(MODELS, "rasters"), { recursive: true });
  let id = 0;
  for (const s of slides) for (const e of s.els) {
    if (e.t !== "model") continue;
    e.id = `m${++id}`;
    const px = process.env.FAST ? Math.round((e.px || 820) / 3) : (e.px || 820);
    const data = fs.readFileSync(path.join(MODELS, "glb", `${e.key}.glb`));
    const hash = crypto.createHash("md5").update(data).update(JSON.stringify([e.rot, px, 3])).digest("hex").slice(0, 10);
    e.raster = path.join(MODELS, "rasters", `${e.key}-${hash}.png`);
    if (!fs.existsSync(e.raster) && !jobs.some((job) => job.out === e.raster))
      jobs.push({ key: e.key, rot: e.rot, px, out: e.raster });
  }
  if (jobs.length) {
    console.log(`Rendering ${jobs.length} chestnut poster raster(s)…`);
    const list = path.join(MODELS, "rasters", "_jobs.json");
    fs.writeFileSync(list, JSON.stringify(jobs));
    execSync(`python3 ${path.join(SCH, "models", "render.py")} ${list}`, { stdio: "inherit", env });
    fs.unlinkSync(list);
  }
}

function writeScript() {
  let md = "# Текст выступления к презентации «Покупка на автопилоте»\n\n" +
    "**Формат:** учебный проект, 10 слайдов. В заметках каждого слайда находится тот же текст. " +
    "Результаты опроса не придуманы: выборка N ≥ 50 — цель набора, не собранные ответы.\n";
  slides.forEach((s, i) => { md += `\n## Слайд ${i + 1} — ${TITLES[i]}\n\n${s.notes.trim()}\n`; });
  fs.writeFileSync(path.join(ROOT, "exports/impulse-spending-script.md"), md);
}

function writeSources() {
  const mapping = [
    [1, "Объект проекта и мемы — из исходного файла; это не эмпирические данные."],
    [2, "Платёжный сценарий и связь оплаты с поведением: [4]. Рыночные цифры BNPL из черновика не перенесены без проверенного первоисточника."],
    [3, "Рабочее определение импульсивной покупки: [1], [2]. Пересказ, не дословная цитата."],
    [4, "Триггер — желание — сопротивление/действие: концептуальная схема по [3]; показана как упрощённая модель, не универсальный закон."],
    [5, "Дефицит: [5]; социальное влияние: [6]; FoMO: [7]; платёжный механизм: [4]; фрейминг: [8]. Эти работы обосновывают темы вопросов, но не доказывают гипотезы на нашей выборке."],
    [6, "Целевая аудитория, вопрос, план N ≥ 50 и этика — собственный план учебного исследования; данные ещё не собраны."],
    [7, "H1–H3 — гипотезы собственного проекта; будущий поперечный опрос может показать связь, но не причинность."],
    [8, "Этапы — план выполнения собственного проекта. Изображение банков сбережений сохранено из оригинальной презентации как мем."],
    [9, "Пауза, проверка бюджета и добавление трения — предложения памятки, не обещание гарантированного эффекта."],
    [10, "Собственный вывод проекта сформулирован как предложение. Библиографические записи [1]–[8] приведены ниже."],
  ];
  let md = "# Источники и проверка фактов — «Покупка на автопилоте»\n\n" +
    "## Что важно не перепутать\n\n" +
    "- Опрос пока не проведён. N ≥ 50 — план набора, не реальное число участников.\n" +
    "- Ни одна гипотеза H1–H3 не представлена как подтверждённый результат.\n" +
    "- Поскольку исследование планируется как поперечное, результаты будут говорить о связях, а не о причинности.\n" +
    "- Цифры о BNPL и ФЗ из исходника не перенесены: к ним не приложен проверяемый первоисточник. Тема оплаты частями оставлена как возможная переменная анкеты.\n" +
    "- Мемы и фотография каштанов сохранены из пользовательского файла `ekonomika123.pptx`. Мем — визуальная иллюстрация, не источник факта.\n\n" +
    "## Источники по слайдам\n\n| Слайд | Основание утверждений / статус |\n|---:|---|\n" +
    mapping.map(([i, note]) => `| ${i} | ${note} |`).join("\n") + "\n\n## Библиография\n\n" +
    Object.entries(REF).map(([n, citation]) => `[${n}] ${citation}`).join("\n\n") + "\n\n" +
    "## Исходные изображения\n\n" +
    "Фото каштанов и мемы взяты из пользовательского исходника `ekonomika123.pptx` и перенесены в `presentations/impulse/assets/` для воспроизводимой сборки. Авторские права на исходные мемы не устанавливаются этим проектом.\n";
  fs.writeFileSync(path.join(ROOT, "exports/impulse-spending-sources.md"), md);
}

async function preview() {
  const fontsDir = path.join(SCH, "node_modules/@fontsource");
  const pages = toHtml(slides, path.join(HERE, "assets"), fontsDir);
  const outDir = path.join(HERE, "preview");
  fs.mkdirSync(outDir, { recursive: true });
  const chromiumMod = req("@sparticuz/chromium");
  const chromium = chromiumMod.default || chromiumMod;
  const puppeteer = req("puppeteer-core");
  if (!fs.existsSync("/tmp/al/lib/libnspr4.so")) {
    const zlib = require("zlib");
    fs.mkdirSync("/tmp/al", { recursive: true });
    const archive = req.resolve("@sparticuz/chromium").replace(/build\/.*$/, "bin/al2023.tar.br");
    fs.writeFileSync("/tmp/al/al.tar", zlib.brotliDecompressSync(fs.readFileSync(archive)));
    execSync("tar xf al.tar", { cwd: "/tmp/al" });
  }
  process.env.LD_LIBRARY_PATH = [process.env.LD_LIBRARY_PATH || "", "/tmp/al/lib"].filter(Boolean).join(":");
  const browser = await puppeteer.launch({
    args: [...chromium.args, "--allow-file-access-from-files"],
    executablePath: await chromium.executablePath(), headless: true,
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  const only = process.argv.find((arg) => arg.startsWith("--only="));
  const wanted = only ? only.slice(7).split(",").map(Number) : null;
  for (let i = 0; i < pages.length; i++) {
    if (wanted && !wanted.includes(i + 1)) continue;
    const html = path.join(outDir, `slide-${String(i + 1).padStart(2, "0")}.html`);
    fs.writeFileSync(html, pages[i]);
    await page.goto(`file://${html}`, { waitUntil: "networkidle0" });
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: html.replace(/\.html$/, ".png") });
    fs.unlinkSync(html);
  }
  await browser.close();
  console.log("PNG previews ->", outDir);
}

async function main() {
  prepareModels();
  const pptxgen = req("pptxgenjs");
  const JSZip = req("jszip");
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.author = "MyWorkAiBrain — учебный проект";
  pres.subject = "Психология импульсивных трат; исходный мем-стиль и каштан сохранены";
  pres.title = "Покупка на автопилоте — психология импульсивных трат";
  pres.company = "MyWorkAiBrain";
  toPptx(pres, slides);
  const buffer = await pres.write({ outputType: "nodebuffer" });
  const zip = await JSZip.loadAsync(buffer);
  await injectModels(zip, slides, path.join(MODELS, "glb"));
  await injectTiming(zip, slides);
  await dedupeMedia(zip);
  const output = path.join(ROOT, "ekonomika123.pptx");
  fs.writeFileSync(output, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE", compressionOptions: { level: 9 } }));
  console.log(`Wrote ${output} (${(fs.statSync(output).size / 1e6).toFixed(2)} MB), ${slides.length} slides`);
  writeScript();
  writeSources();
  if (process.argv.includes("--preview")) await preview();
}

main().catch((error) => { console.error(error); process.exit(1); });
