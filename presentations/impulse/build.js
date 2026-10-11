// Rebuild the editable 16:9 deck in the original meme/collage style, retaining
// native PowerPoint 3D models, looping GLB animations, Morph, notes and previews.
const path = require("path");
const fs = require("fs");
const crypto = require("crypto");
const { execSync } = require("child_process");
const SCH = path.join(__dirname, "..", "schumpeter");
const req = require("module").createRequire(path.join(SCH, "package.json"));
const { Slide, toPptx, toHtml } = require(path.join(SCH, "lib"));
const { injectModels, injectTiming, dedupeMedia } = require(path.join(SCH, "pptx3d"));

const A = (name) => path.join(__dirname, "assets", name);
const M = (name) => A(path.join("memes", name));
const OUT = path.resolve(__dirname, "../../exports");
const MODELS = path.join(__dirname, "models");
const SW = 13.333, SH = 7.5, N = 10;
const C = {
  bg: "22528D", blue: "22528D", deep: "143A68", white: "FFFDF6",
  paper: "F5F1E7", ink: "171C22", red: "EF2634", yellow: "FFD84A",
  muted: "D9E7F6", grey: "59616B", green: "4F9C75", line: "1D2731",
};
const X = .72, RIGHT = 12.62, CW = RIGHT-X;
const slides = [];

const br = (text, options={}) => ({ text, options: { ...options, breakLine:true } });

function chrome(s, idx) {
  s.bg = C.bg;
  s.img(M("blue-grunge-16x9.jpg"), {x:0,y:0,w:SW,h:SH,name:"!!blue-grunge"});
  // The source deck's blue grain, hand-painted red swash and white scrap-paper look.
  s.text("ПСИХОЛОГИЯ ИМПУЛЬСИВНЫХ ПОКУПОК", {
    x:X,y:.20,w:6.0,h:.22,font:"meme",size:9.4,bold:true,color:C.white,charSpacing:1.1,name:"!!series"
  });
  s.img(M("red-brush.png"), {x:X,y:.48,w:2.25,h:.18,name:"!!red-swash"});
  s.rect({x:11.47,y:.16,w:1.15,h:.43,fill:C.yellow,line:C.ink,lineW:.8,rotate:2,shadow:true,name:"!!page-sticker"});
  s.text(`${String(idx).padStart(2,"0")} / ${N}`, {
    x:11.53,y:.26,w:1.02,h:.20,font:"meme",size:10.5,bold:true,color:C.ink,align:"center",name:"!!page"
  });
  s.text("#план_исследования  ·  СОБСТВЕННЫХ ДАННЫХ ПОКА НЕТ", {
    x:X,y:7.16,w:8.6,h:.18,font:"meme",size:8.4,bold:true,color:C.white,charSpacing:.35,name:"!!footer"
  });
}

function title(s, text, opts={}) {
  s.text(text, {
    x:opts.x??X,y:opts.y??.91,w:opts.w??7.3,h:opts.h??.9,
    font:"meme",size:opts.size??29,bold:true,color:opts.color??C.white,
    lineSpacingMultiple:opts.lh??.92,valign:"top",align:opts.align??"left",
    name:opts.name??"!!meme-title",ag:opts.ag
  });
}
function body(s,text,x,y,w,h,opts={}) {
  s.text(text, {x,y,w,h,font:opts.font??"body",size:opts.size??12,
    bold:opts.bold??false,italic:opts.italic??false,color:opts.color??C.ink,
    lineSpacingMultiple:opts.lh??1.0,valign:opts.valign??"top",
    align:opts.align??"left",charSpacing:opts.spacing??0,ag:opts.ag});
}
function paper(s,x,y,w,h,opts={}) {
  s.rect({x,y,w,h,fill:opts.fill??C.paper,line:opts.line??C.ink,
    lineW:opts.lineW??1.0,lineT:opts.lineT??0,shadow:opts.shadow??true,
    radius:opts.radius??.025,rotate:opts.rotate??0,ag:opts.ag});
  if(opts.lined){
    s.img(M("notebook-lines-horizontal.png"),{x:x+.035,y:y+.045,w:w-.07,h:h-.09,transparency:opts.lineTransparency??18,ag:opts.ag});
  }
  if(opts.torn!==false && h>.45){
    s.img(M("torn-paper.png"),{x:x+.03,y:y+.025,w:w-.06,h:.17,transparency:opts.edgeTransparency??4,ag:opts.ag});
  }
}
function photo(s,file,x,y,w,h,opts={}) {
  // Coordinates are selected to match each source image's aspect ratio; a slight
  // white frame keeps the pasted-in meme recognizable against the blue texture.
  s.rect({x,y,w,h,fill:opts.fill??"FFFFFF",line:opts.line??C.ink,
    lineW:opts.lineW??1.0,shadow:opts.shadow??true,rotate:opts.rotate??0,ag:opts.ag});
  const p=opts.pad??.065;
  s.img(M(file),{x:x+p,y:y+p,w:w-2*p,h:h-2*p,transparency:opts.transparency??0,ag:opts.ag});
}
function swash(s,x,y,w=3.2,h=.25) {
  s.img(M("red-brush.png"),{x,y,w,h,name:"!!red-underline"});
}
function sticker(s,text,x,y,w,h,opts={}) {
  const fill=opts.fill??C.yellow, color=opts.color??C.ink;
  s.rect({x,y,w,h,fill,line:opts.line??C.ink,lineW:opts.lineW??.85,
    rotate:opts.rotate??0,shadow:opts.shadow??true,radius:opts.radius??0,ag:opts.ag});
  s.text(text,{x:x+.06,y:y+.045,w:w-.12,h:h-.09,font:opts.font??"meme",
    size:opts.size??11,bold:true,color,align:opts.align??"center",
    valign:"middle",lineSpacingMultiple:.92,ag:opts.ag});
}
function tag(s,text,x,y,w,opts={}) {
  s.text(text.toUpperCase(),{x,y,w,h:opts.h??.18,font:"meme",size:opts.size??8.4,
    bold:true,color:opts.color??C.white,charSpacing:opts.spacing??.45,ag:opts.ag});
}
function stage(s,key,o={}) {
  const x=o.x??8.4,y=o.y??1.55,size=o.s??3.8,rot=o.rot??[10,-18,0];
  const cx=x+size/2,cy=y+size/2+(o.dy??0),d=size*(o.disc??1.05);
  s.img(A("glow.png"),{x:cx-d*.60,y:cy-d*.60,w:d*1.2,h:d*1.2,transparency:38,name:"!!warm-glow"});
  s.rect({x:cx-d*.42,y:cy-d*.42,w:d*.84,h:d*.84,shape:"ellipse",
    fill:C.paper,fillT:22,line:C.white,lineW:1.2,lineT:8,name:"!!paper-sticker"});
  s.rect({x:cx-d*.48,y:cy-d*.48,w:d*.96,h:d*.96,shape:"ellipse",
    line:C.red,lineW:1.5,lineT:6,dash:"dash",name:"!!comic-ring"});
  s.model(key,{x,y,s:size,rot,name:`!!m-${key}`,px:o.px??720});
  s.hero={key,x,y,s:size,rot};
  if(o.sticker!==false){
    const tx=o.tx??(x+size*.68),ty=o.ty??(y+size*.03),tw=o.tw??.85,th=o.th??.35;
    sticker(s,o.stickerText??"3D!",tx,ty,tw,th,{fill:o.stickerFill??C.yellow,size:o.stickerSize??9,rotate:2});
  }
}
function smallCitation(s,text,x=X,y=6.73,w=8.4){
  body(s,text,x,y,w,.25,{size:8.2,color:C.white,bold:true});
}
function numberCard(s,num,head,desc,x,y,w,h,opts={}){
  paper(s,x,y,w,h,{ag:opts.ag});
  sticker(s,num,x+.13,y+.18,.48,.40,{fill:opts.fill??C.red,color:C.white,size:12,rotate:-2,ag:opts.ag});
  body(s,head,x+.76,y+.14,w-.94,.25,{font:"meme",size:opts.headSize??12.3,bold:true,color:C.ink,ag:opts.ag});
  body(s,desc,x+.76,y+.44,w-.96,h-.50,{size:opts.bodySize??10.2,color:C.ink,ag:opts.ag});
}

// 1 — cover: keep the original money-fall meme and add an animated 3D cart.
{
  const s=new Slide({notes:
`Представьте: вы открыли маркетплейс «на минутку», а через несколько нажатий в корзине уже то, что не планировали. Исходная работа была о психологии импульсивных трат; я сохранила её тему, шутки и коллажный визуальный язык, но собрала проект заново. Здесь мемы — не украшение поверх сухого доклада, а способ показать знакомые ситуации. При этом исследовательская часть остаётся аккуратной: опрос ещё не проводился, проценты и выводы не выдуманы. Мы пройдём путь от триггера до плана пилотного опроса, отдельно проверим гипотезы и закончим памяткой. В сцене — корзина с анимированной 3D-моделью.`});
  chrome(s,1);
  tag(s,"версия 2.0 · мемы сохранены",X, .83,5.4,{size:9.2,color:C.yellow});
  title(s,"ПОЧЕМУ МЫ\nПОКУПАЕМ\nНЕНУЖНОЕ?",{x:X,y:1.18,w:6.0,h:2.76,size:39,lh:.9});
  swash(s,X,4.05,4.85,.31);
  paper(s,X,4.54,5.75,1.52,{ag:2,lined:true,lineTransparency:28});
  body(s,"Я: «просто посмотрю»\nМаркетплейс: «держи 18 товаров»",X+.28,4.87,5.18,.81,{font:"meme",size:17,bold:true,color:C.ink,lh:.95,ag:2});
  tag(s,"психология импульсивных трат · студенты 18–25",X,6.39,6.0,{color:C.yellow,size:9.1});
  photo(s,"rich-money.jpeg",7.05,1.02,5.50,3.72,{ag:2});
  stage(s,"cart",{x:8.94,y:3.18,s:3.52,rot:[8,-17,0],px:780,stickerText:"В КОРЗИНУ",tw:1.18,th:.40});
  sticker(s,"НЕ ПЛАНИРОВАЛА",10.65,.79,1.75,.46,{fill:C.yellow,size:10,rotate:2,ag:3});
  slides.push(s);
}

// 2 — market relevance, with the source's 106-ruble meme and clear caveats.
{
  const s=new Slide({notes:
`Почему эта тема актуальна? В исходном deck уже была шутка про 106 рублей на карте и несколько экранов маркетплейсов — я возвращаю её как узнаваемую сцену, но не выдаю за данные исследования. По оценке сервиса «Долями» от Т-Банка, оборот BNPL в России за 2025 год составил около 940 миллиардов рублей. Это оценка объёма оплат частями, не измерение импульсивных покупок и не статистика по студентам. Закон № 283-ФЗ о деятельности сервисов рассрочки действует с 1 апреля 2026 года. Это регуляторный контекст, а не доказательство вреда или причины трат. Вопрос проекта — какие психологические и ситуационные факторы связаны с незапланированными покупками.`});
  chrome(s,2);
  title(s,"КАРТА: 106 ₽.\nКОРЗИНА: «УЖЕ ОФОРМЛЕНО»",{x:X,y:.94,w:7.2,h:1.10,size:27,lh:.92});
  swash(s,X,2.12,3.9,.24);
  paper(s,X,2.46,6.86,3.52,{ag:2});
  tag(s,"оценка рынка · 2025",X+.28,2.78,4.2,{color:C.red,size:9.0,ag:2});
  body(s,"≈ 940 млрд ₽",X+.28,3.09,4.9,.56,{font:"meme",size:28,bold:true,color:C.ink,ag:2});
  body(s,"оборот BNPL в России по оценке сервиса «Долями» (Т-Банк).",X+.30,3.74,6.18,.45,{size:12,color:C.ink,ag:2});
  s.line({x1:X+.27,y1:4.31,x2:X+6.54,y2:4.31,color:C.red,width:1.4,ag:2});
  body(s,"283-ФЗ · действует с 01.04.2026\nНовые требования к сервисам рассрочки — финансовый контекст, не ярлык поведения.",X+.30,4.48,6.16,.81,{size:11.4,bold:true,color:C.ink,ag:2});
  sticker(s,"BNPL ≠ ИМПУЛЬСИВНОСТЬ",X+.28,5.47,3.18,.37,{fill:C.yellow,size:9.1,rotate:-1,ag:3});
  photo(s,"106-rubles.jpeg",8.26,1.38,3.96,3.28,{ag:2});
  stage(s,"wallet",{x:9.14,y:3.67,s:3.20,rot:[10,-18,0],px:700,stickerText:"ПЛАТЁЖ",tw:.95,th:.34});
  sticker(s,"я только зашла посмотреть",8.43,5.28,3.55,.47,{fill:C.paper,size:10,rotate:-1,ag:3});
  smallCitation(s,"[1] «Ведомости» / оценка «Долями»; [2] официальный текст 283-ФЗ. Подробности — в файле источников.",X,6.72,11.7);
  slides.push(s);
}

// 3 — an illustrative chain with the original product/meme collage.
{
  const s=new Slide({notes:
`Рабочая схема проекта короткая: сигнал — внутренний отклик — действие — оценка покупки после оплаты. В сигнал могут попасть уведомление, рекомендация или акция; откликом могут стать интерес, предвкушение либо FOMO. Затем человек может добавить товар в корзину или оплатить его; после покупки эмоции и оценка необходимости у всех будут разными. Это иллюстрация для исследования, а не диагноз и не обязательный сценарий для каждого покупателя. На нижней ленте — товары и логотипы из исходного коллажа: энергетик, шаурма, фастфуд и сладости. Их присутствие — визуальная шутка, а не реклама и не утверждение о конкретном поведении.`});
  chrome(s,3);
  title(s,"ВИЖУ → ХОЧУ → КУПИЛ → «ОЙ»",{x:X,y:.94,w:8.0,h:.64,size:30});
  body(s,"Упрощённая модель: внешний сигнал и эмоция могут ускорить выбор — исход у людей разный.",X,1.68,7.15,.39,{size:12.2,color:C.white,bold:true});
  paper(s,X,2.19,7.02,1.05,{ag:2});
  const flow=["СИГНАЛ","ОТКЛИК","ДЕЙСТВИЕ","ПОСЛЕ"];
  const flowNotes=["таймер","FOMO","корзина","радость / «ой»"];
  flow.forEach((h,i)=>{
    const x=X+.18+i*1.69;
    body(s,h,x,2.43,1.37,.23,{font:"meme",size:10.1,bold:true,color:i===1?C.red:C.ink,align:"center",ag:2});
    body(s,flowNotes[i],x,2.75,1.37,.23,{size:9.2,color:C.ink,align:"center",ag:2});
    if(i<3) body(s,"→",x+1.40,2.60,.26,.25,{font:"meme",size:14,bold:true,color:C.red,align:"center",ag:2});
  });
  const products=[
    ["redbull.jpeg","энергетик"],["shaverma.png","шаурма"],["rostics.png","перекус"],
    ["kinder-country.jpeg","сладкое"],["coke-zero.jpeg","напиток"],
  ];
  products.forEach(([file,cap],i)=>{
    const x=X+i*1.34;
    photo(s,file,x,3.53,1.12,1.12,{pad:.045,ag:3});
    body(s,cap,x-.03,4.72,1.18,.22,{font:"meme",size:8.2,bold:true,color:C.white,align:"center",ag:3});
  });
  sticker(s,"С ЭТОГО ДНЯ БРОСАЮ ЛЁГКИЙ ДОФАМИН",X,5.27,6.98,.62,{fill:C.red,color:C.white,size:15.2,rotate:-.4,ag:4});
  stage(s,"cycle",{x:8.45,y:1.51,s:3.76,rot:[11,-20,0],px:760,stickerText:"ЦИКЛ",tw:.76,th:.34});
  smallCitation(s,"Теоретическая опора: Rook (1987); Beatty & Ferrell (1998). Схема — концептуальная, не «универсальный закон».",X,6.70,11.5);
  slides.push(s);
}

// 4 — the original task slide's exact odd-couple collage: GDE PAPA? + chestnut.
{
  const s=new Slide({notes:
`Здесь я восстановил логику исходного четвёртого слайда: слева перечислены задачи проекта, а справа вместе стоят мем «ГДЕ ПАПА?» и фото каштана. Каштан не отдельная тема исследования и не переменная анкеты — это тот самый визуальный прикол из оригинального коллажа. Подпись «100%» относится к обязательному возвращению этого фрагмента в презентацию, не к результатам. Сами задачи — ещё план: разобрать теорию, описать цифровой контекст, подготовить и провести пилотный опрос, проверить гипотезы и на его основе сделать памятку. На фото и рядом с ним оставлен исходный мемный абсурд; научные выводы из него не извлекаются.`});
  chrome(s,4);
  title(s,"ЗАДАЧИ ПРОЕКТА",{x:X,y:.94,w:6.7,h:.66,size:31});
  swash(s,X,1.68,3.8,.24);
  paper(s,X,2.03,6.52,4.10,{ag:2});
  tag(s,"план работ · ещё не отчёт о выполнении",X+.28,2.36,5.9,{color:C.red,size:8.8,ag:2});
  const tasks=[
    ["01","ТЕОРИЯ","когнитивные искажения · поведенческая экономика"],
    ["02","КОНТЕКСТ","BNPL · кредиты · цифровые триггеры"],
    ["03","АНКЕТА","собрать вопросы и проверить понятность"],
    ["04","ПИЛОТ","студенты 18–25 · ориентир N ≥ 50"],
    ["05","ФИНАЛ","проверить H1–H3 · сделать памятку"],
  ];
  tasks.forEach(([n,h,d],i)=>{
    const y=2.76+i*.59;
    sticker(s,n,X+.28,y,.46,.34,{fill:i===4?C.red:C.yellow,color:i===4?C.white:C.ink,size:9.8,ag:2});
    body(s,h,X+.91,y+.01,1.37,.23,{font:"meme",size:9.8,bold:true,color:i===4?C.red:C.ink,ag:2});
    body(s,d,X+2.20,y+.01,4.0,.30,{size:9.5,bold:true,color:C.ink,ag:2});
  });
  photo(s,"where-papa.jpeg",7.62,1.49,3.38,3.38,{ag:2});
  photo(s,"chestnuts.jpeg",9.14,3.55,3.38,2.26,{ag:3});
  stage(s,"chestnut",{x:10.96,y:4.48,s:1.52,rot:[10,-18,0],px:460,stickerText:"3D!",tw:.62,th:.30,stickerSize:8});
  sticker(s,"КАШТАН 100% · ГДЕ ПАПА?",9.29,5.91,3.14,.42,{fill:C.red,color:C.white,size:9.4,rotate:-.6,ag:3});
  smallCitation(s,"Каштан остался в исходной паре мемов на слайде задач — не стал отдельной темой доклада.",X,6.71,11.7);
  slides.push(s);
}

// 5 — triggers: keep the source serotonin meme, with research context underneath.
{
  const s=new Slide({notes:
`Проверяем не «слабую волю», а возможные условия выбора. В первом блоке — FOMO: опасение упустить опыт или выгоду. Во втором — социальное сравнение и ощущение «у всех уже есть». Третий блок — срочность и дефицит, например таймер или сообщение «осталось мало». Четвёртый — низкое трение интерфейса: сохранённая карта и покупка в несколько касаний. Метаанализ исследований онлайн-покупок описывает связи с контекстными, маркетинговыми и платформенными факторами. Но литература не доказывает, что один триггер обязательно вызовет покупку у каждого студента. Мем «инвестировала в серотонин» — узнаваемый внутренний монолог, а не измерение настроения или научный результат.`});
  chrome(s,5);
  title(s,"ТРИГГЕРЫ: «Я ТОЛЬКО ПОСМОТРЕТЬ»",{x:X,y:.94,w:7.85,h:.67,size:28.5});
  swash(s,X,1.67,4.0,.24);
  paper(s,X,2.03,7.05,3.92,{ag:2});
  const triggers=[
    ["FOMO","«вдруг упущу»",C.red],
    ["СРАВНЕНИЕ","«у всех уже есть»","2860D9"],
    ["СРОЧНОСТЬ","таймер · «осталось мало»",C.red],
    ["МЕНЬШЕ ТРЕНИЯ","один тап · карта сохранена",C.green],
  ];
  triggers.forEach(([h,d,color],i)=>{
    const y=2.41+i*.78;
    body(s,h,X+.25,y,2.55,.22,{font:"meme",size:10.7,bold:true,color,ag:2});
    body(s,d,X+2.68,y,3.95,.30,{font:"meme",size:10.1,bold:true,color:C.ink,ag:2});
    if(i<3)s.line({x1:X+.25,y1:y+.53,x2:X+6.69,y2:y+.53,color:"9AA4AC",lineT:25,width:.65,ag:2});
  });
  sticker(s,"МОЗГ: «НО ТАМ СКИДКА!»",X,6.10,6.93,.43,{fill:C.red,color:C.white,size:12.2,rotate:-.4,ag:4});
  photo(s,"serotonin-cat.jpeg",8.64,1.16,3.70,2.64,{ag:2});
  stage(s,"triggers",{x:8.52,y:3.11,s:3.72,rot:[12,-20,0],px:740,stickerText:"ПИНГ!",tw:.8,th:.34});
  smallCitation(s,"Опора: Anoop & Rahman (2025); Przybylski et al. (2013); Gibbons & Buunk (1999). Связь ≠ причинность.",X,6.72,11.6);
  slides.push(s);
}

// 6 — hypotheses: retain the research, but let the original rose/serotonin image do the punchline.
{
  const s=new Slide({notes:
`Сохраняю три гипотезы исходного проекта и обозначаю, как именно их планируется проверять. H1: более высокий FoMO связан с большей частотой незапланированных покупок за последние тридцать дней; оплату частями разумно описать отдельно. H2: выраженная склонность к социальному сравнению связана с самоотчётами о трендовых или статусных покупках. H3: финансовые знания могут быть связаны с выраженностью импульсивных покупок, но мы не предполагаем заранее защитный эффект. Это предположения, не результаты: ни одна связь пока не измерялась. Одномоментная анкета позволит обсуждать связи, но не причины. Мемная подпись на фото — шутка, а не результат опроса.`});
  chrome(s,6);
  title(s,"ГИПОТЕЗЫ: ВОТ ЭТО МЫ ПРОВЕРИМ",{x:X,y:.94,w:7.75,h:.67,size:27.5});
  swash(s,X,1.67,4.0,.24);
  const hs=[
    ["H1","FoMO ↔ незапланированные покупки","Больше FoMO — возможно, чаще покупки «не по плану».",C.red],
    ["H2","Социальное сравнение ↔ статусные траты","«У всех есть» может быть связано с покупками «как у всех».","2860D9"],
    ["H3","Финансовые знания ↔ импульсивность","Проверяем связь; не обещаем, что знания «выключат» эмоции.",C.green],
  ];
  hs.forEach(([n,h,d,color],i)=>numberCard(s,n,h,d,X,2.03+i*1.08,7.05,.91,{fill:color,headSize:11.5,bodySize:9.9,ag:2+i}));
  sticker(s,"СНАЧАЛА ИЗМЕРИТЬ. ПОТОМ ДЕЛАТЬ ВЫВОД.",X,5.47,6.98,.51,{fill:C.yellow,size:12.1,rotate:.4,ag:5});
  photo(s,"serotonin-flowers.jpeg",8.65,1.15,3.36,3.36,{ag:2});
  stage(s,"scale",{x:8.49,y:3.13,s:3.70,rot:[8,-19,0],px:740,stickerText:"H1–H3",tw:.92,th:.36});
  sticker(s,"Я: ХОЧУ ВЕРИТЬ В СВЯЗЬ / ДАННЫЕ: СПОКОЙНО",8.78,5.83,3.65,.50,{fill:C.red,color:C.white,size:9.3,rotate:-.6,ag:4});
  smallCitation(s,"FoMO [5] · социальное сравнение [6] · финансовая грамотность [7]. Ни одна гипотеза пока не проверена.",X,6.72,11.6);
  slides.push(s);
}

// 7 — target group + pilot survey; the original budget-jars meme gives it some bite.
{
  const s=new Slide({notes:
`Целевая аудитория — совершеннолетние студенты вузов 18–25 лет; результаты адресованы студентам, преподавателям и центрам финансовой грамотности. Планируется анонимный добровольный пилотный онлайн-опрос, ориентир — не менее пятидесяти ответов. Такая удобная выборка не представляет всех студентов России. В анкете — эпизоды незапланированных покупок за последние тридцать дней, способ оплаты, FoMO, социальное сравнение и короткий блок базовых финансовых знаний. Для шкал нужно использовать опубликованные формулировки и проверить перевод. Не собираем имена, контакты и номера карт; до старта — согласие и понятное объяснение цели. Мем с банками — оригинальная иллюстрация бюджета, а не характеристика каждого студента.`});
  chrome(s,7);
  title(s,"КОМУ АНКЕТА? СТУДЕНТАМ 18–25",{x:X,y:.94,w:7.85,h:.68,size:27.5});
  swash(s,X,1.67,4.15,.24);
  paper(s,X,2.03,6.95,4.05,{ag:2});
  body(s,"N ≥ 50",X+.28,2.35,1.80,.52,{font:"meme",size:26,bold:true,color:C.red,ag:2});
  body(s,"пилотная удобная выборка —\nне «все студенты России»",X+2.02,2.40,4.45,.49,{font:"meme",size:10.8,bold:true,color:C.ink,ag:2});
  const survey=[
    ["КТО","совершеннолетние студенты 18–25"],
    ["ЧТО","покупки за 30 дней · BNPL отдельно"],
    ["КАК","добровольно · анонимно · минимум данных"],
    ["ЗАЧЕМ","студентам · преподавателям · центрам грамотности"],
  ];
  survey.forEach(([a,b],i)=>{
    const y=3.18+i*.58;
    sticker(s,a,X+.30,y,.84,.33,{fill:i===1?C.red:C.yellow,color:i===1?C.white:C.ink,size:8.9,ag:2});
    body(s,b,X+1.31,y+.025,5.25,.29,{font:"meme",size:9.3,bold:true,color:C.ink,ag:2});
  });
  body(s,"Не репрезентативно. Не собираем имена, контакты и номера карт.",X+.30,5.62,6.25,.25,{size:9.7,bold:true,color:C.red,ag:2});
  photo(s,"budget-jars.jpeg",8.44,1.42,3.24,2.95,{ag:2});
  stage(s,"clipboard",{x:8.90,y:3.06,s:3.48,rot:[10,-19,0],px:720,stickerText:"АНКЕТА",tw:1.02,th:.38});
  sticker(s,"МЕМ ПРО БЮДЖЕТ · НЕ ПРО ВСЕХ",8.30,6.00,4.20,.43,{fill:C.yellow,size:9.0,rotate:-.7,ag:3});
  smallCitation(s,"Шкалы и финансовые вопросы: [5]–[7]. Перевод и понятность проверяются до запуска.",X,6.71,11.6);
  slides.push(s);
}

// 8 — analysis plan, not invented results; re-use the source Doctor Mom product cutout as a joke.
{
  const s=new Slide({notes:
`Для анализа пилота сначала описать распределения и пропуски, затем проверить качество измерительных блоков и только после этого смотреть ранговые корреляции Спирмена с доверительными интервалами. Частоту незапланированных покупок лучше задать заранее как основной показатель; BNPL описать отдельным пунктом, не подменяя им импульсивность. При N около пятидесяти не перегружать модель предикторами. Удобная выборка, самоотчёт и одномоментный срез ограничивают обобщение и не доказывают причинность. Баночка «Доктор Мом» — ещё одна вырезка из исходного коллажа: это не сироп от статистики, а просто мемная подпись. Результаты появятся только после реального сбора данных.`});
  chrome(s,8);
  title(s,"КОРРЕЛЯЦИЯ ≠ ПРИЧИНА. СИРОПА НЕТ.",{x:X,y:.94,w:7.55,h:.67,size:26.5});
  swash(s,X,1.68,3.8,.24);
  photo(s,"doctor-mom.jpeg",X,2.15,3.23,3.23,{ag:2});
  sticker(s,"СИРОП ОТ КОРРЕЛЯЦИИ НЕ ВЫПИШЕШЬ",X+.06,5.48,3.95,.40,{fill:C.yellow,size:8.7,rotate:-.7,ag:3});
  paper(s,4.91,1.93,3.30,3.98,{ag:2});
  tag(s,"план анализа",5.18,2.27,2.65,{color:C.red,size:9.1,ag:2});
  const analysis=[
    "описать ответы и пропуски",
    "Спирмен · доверительные интервалы",
    "BNPL анализировать отдельно",
    "не делать причинных выводов",
  ];
  analysis.forEach((t,i)=>{
    const y=2.72+i*.68;
    sticker(s,`${i+1}`,5.18,y,.36,.32,{fill:i===3?C.red:C.yellow,color:i===3?C.white:C.ink,size:9.4,ag:2});
    body(s,t,5.67,y+.02,2.26,.43,{font:"meme",size:9.7,bold:true,color:C.ink,ag:2});
  });
  stage(s,"chart",{x:8.48,y:1.89,s:3.78,rot:[9,-19,0],px:750,stickerText:"ЧТО ВИДНО?",tw:1.30,th:.36});
  smallCitation(s,"Опрос ещё не проведён. Планируемая удобная выборка не будет репрезентативной.",X,6.71,11.6);
  slides.push(s);
}

// 9 — actionable pause/check/total-price memo, without claiming proven effects.
{
  const s=new Slide({notes:
`Практический финал проекта — короткая памятка без стыда и запретов. Первое: поставить паузу на необязательную покупку, особенно если её подгоняет таймер. Второе: проверить, была ли вещь в плане, нужна ли она вне скидки и какая у неё полная стоимость. Третье: посмотреть на уже запланированные платежи за месяц; полезное трение — отключить лишние уведомления и убрать сохранённую карту там, где это удобно. Оплата частями может менять расписание платежей, но не уменьшает полную цену. Это предложения для памятки, а не гарантированный способ изменить поведение и не клиническая рекомендация. Их эффект потребует отдельной проверки.`});
  chrome(s,9);
  title(s,"ПЕРЕД ОПЛАТОЙ —\nТРИ ШАГА (КОРЗИНА ПОДОЖДЁТ)",{x:X,y:.94,w:7.1,h:1.06,size:27.5,lh:.92});
  swash(s,X,2.09,3.1,.23);
  const tips=[
    ["01","ПАУЗА","до завтра. Таймер переживёт.",C.red],
    ["02","ПОЛНАЯ ЦЕНА","считай всю сумму, не один платёж.",C.green],
    ["03","МОЙ ПЛАН?","если нет — пусть корзина полежит.",C.red],
  ];
  tips.forEach(([n,h,d,color],i)=>numberCard(s,n,h,d,X,2.40+i*.95,7.02,.78,{fill:color,headSize:11.8,bodySize:9.7,ag:2+i}));
  sticker(s,"ТАЙМЕР ПОДОЖДЁТ. КОРЗИНА НЕ УБЕЖИТ.",X,5.51,7.03,.56,{fill:C.yellow,size:12.0,rotate:.4,ag:5});
  stage(s,"hourglass",{x:8.45,y:1.82,s:3.83,rot:[11,-16,0],px:760,stickerText:"ПАУЗА",tw:.95,th:.36});
  photo(s,"serotonin-flowers.jpeg",10.33,5.04,1.72,1.72,{ag:3});
  smallCitation(s,"Памятка — предложение проекта, не обещание эффекта и не индивидуальная финансовая рекомендация.",X,6.75,11.7);
  slides.push(s);
}

// 10 — sources and the iconic final 100-ruble meme.
{
  const s=new Slide({notes:
`Спасибо за внимание. На последнем слайде — источники и тот самый мем «с вас списано 100 рублей» из оригинала. Это шутка, никаких списаний нет. Полные библиографические записи и привязка источников к слайдам находятся в отдельном файле. Ключевые опоры — классическая работа о buying impulse, систематический обзор онлайн-покупок, первоисточники FoMO и социального сравнения, инструмент OECD по финансовой грамотности, оценка BNPL от отраслевого участника и официальный текст 283-ФЗ. Снова оговорка: 940 миллиардов — оценка оборота оплат частями, а не результат опроса или показатель количества импульсивных покупок. Наш опрос пока в планах; гипотезы ещё предстоит проверить.`});
  chrome(s,10);
  title(s,"СПАСИБО!\nВОПРОСЫ?",{x:X,y:.94,w:6.1,h:1.25,size:34,lh:.92});
  swash(s,X,2.25,2.6,.23);
  paper(s,X,2.61,7.06,3.54,{ag:2});
  tag(s,"короткий список · полный — в отдельном файле",X+.28,2.94,6.25,{color:C.red,size:8.9,ag:2});
  const refs=[
    ["[1]","Ведомости, 03.02.2026 · оценка BNPL от «Долями» / Т-Банка"],
    ["[2]","ФЗ № 283-ФЗ · официальный текст, 31.07.2025"],
    ["[3]","Rook (1987) · The Buying Impulse · doi:10.1086/209105"],
    ["[4]","Anoop & Rahman (2025) · online impulse buying · doi:10.1002/cb.2418"],
    ["[5]","Przybylski et al. (2013) · FoMO · doi:10.1016/j.chb.2013.02.014"],
    ["[6]","Gibbons & Buunk (1999) · social comparison · doi:10.1037/0022-3514.76.1.129"],
    ["[7]","OECD/INFE (2022) · Financial Literacy Toolkit"],
  ];
  refs.forEach(([n,t],i)=>{
    const y=3.28+i*.37;
    body(s,n,X+.29,y,.42,.22,{font:"meme",size:9.2,bold:true,color:C.red,ag:2});
    body(s,t,X+.78,y,6.05,.25,{size:8.8,bold:true,color:C.ink,ag:2});
  });
  photo(s,"charged-cat.jpeg",8.50,1.22,3.69,3.69,{ag:2});
  stage(s,"cart",{x:9.04,y:3.67,s:3.34,rot:[9,-17,0],px:720,stickerText:"ШУТКА",tw:.88,th:.36});
  sticker(s,"100 ₽ НЕ СПИСЫВАЕМ",8.66,5.59,3.58,.47,{fill:C.yellow,size:11,rotate:-1,ag:3});
  body(s,"План исследования ≠ результаты опроса.",8.51,6.22,3.75,.27,{font:"meme",size:10.2,bold:true,color:C.white,align:"center"});
  smallCitation(s,"Полные библиографические записи, ссылки и методологические оговорки — в exports/ekonomika123-3d-presentation-sources.md.",X,6.73,11.8);
  slides.push(s);
}

// Morph: adjacent main exhibits travel into / out of frame as hidden 3D ghosts.
for(let i=0;i<slides.length;i++){
  const cur=slides[i].hero,nxt=slides[i+1]?.hero;
  if(nxt&&(!cur||cur.key!==nxt.key)){
    slides[i].model(nxt.key,{x:SW+.65,y:nxt.y+.35,s:nxt.s,rot:[nxt.rot[0],nxt.rot[1]+72,nxt.rot[2]],name:`!!m-${nxt.key}`,ghost:true});
  }
  if(cur&&slides[i+1]&&(!nxt||nxt.key!==cur.key)){
    slides[i+1].model(cur.key,{x:-cur.s-.65,y:cur.y+.35,s:cur.s,rot:[cur.rot[0],cur.rot[1]-72,cur.rot[2]],name:`!!m-${cur.key}`,ghost:true});
  }
}

function prepareModels(){
  const env={...process.env,GLB_DIR:path.join(MODELS,"glb"),LD_LIBRARY_PATH:[process.env.BLENDER_LIBS||"/tmp/bstub",process.env.LD_LIBRARY_PATH||""].join(":")};
  const keys=new Set();
  slides.forEach(s=>s.els.forEach(e=>{if(e.t==="model")keys.add(e.key);}));
  const missing=[...keys].filter(k=>!fs.existsSync(path.join(MODELS,"glb",k+".glb")));
  if(missing.length)execSync(`python3 ${path.join(MODELS,"make_models.py")} ${missing.join(" ")}`,{stdio:"inherit",env});
  const jobs=[];fs.mkdirSync(path.join(MODELS,"rasters"),{recursive:true});let n=0;
  slides.forEach(s=>s.els.forEach(e=>{
    if(e.t!=="model")return;
    e.id=`m${++n}`;
    if(e.ghost){e.raster=A("clear.png");return;}
    let px=e.px||Math.round(Math.max(260,e.s*150));if(process.env.FAST)px=Math.max(180,Math.round(px/3));
    const glb=fs.readFileSync(path.join(MODELS,"glb",e.key+".glb"));
    const hash=crypto.createHash("md5").update(glb).update(JSON.stringify([e.rot,px,3])).digest("hex").slice(0,10);
    e.raster=path.join(MODELS,"rasters",`${e.key}-${hash}.png`);
    if(!fs.existsSync(e.raster)&&!jobs.some(j=>j.out===e.raster))jobs.push({key:e.key,rot:e.rot,px,out:e.raster});
  }));
  if(jobs.length){
    console.log(`Rendering ${jobs.length} 3D meme-deck posters…`);
    const jobFile=path.join(MODELS,"rasters","_jobs.json");fs.writeFileSync(jobFile,JSON.stringify(jobs));
    execSync(`python3 ${path.join(SCH,"models","render.py")} ${jobFile}`,{stdio:"inherit",env});fs.unlinkSync(jobFile);
  }
  if(!process.env.FAST){
    const used=new Set(slides.flatMap(s=>s.els.filter(e=>e.t==="model"&&!e.ghost).map(e=>path.basename(e.raster))));
    for(const f of fs.readdirSync(path.join(MODELS,"rasters")))
      if(f.endsWith(".png")&&!used.has(f))fs.unlinkSync(path.join(MODELS,"rasters",f));
  }
}

function writeScript(){
  const out=path.join(OUT,"ekonomika123-3d-presentation-script.md");
  let md="# Текст выступления к презентации «Почему мы покупаем ненужное?»\n\n"+
    "**Формат:** 10 слайдов, ориентир 5–6 минут. Встроенные заметки — тот же текст. " +
    "Стиль намеренно возвращён к исходному: синий гранжевый фон, мемы, бумажные вырезки и красные мазки; каштан возвращён в оригинальную пару с мемом «ГДЕ ПАПА?» на слайде задач, без отдельного каштан-слайда. " +
    "Опрос пока не проводился, результаты и проценты не придуманы. 3D-модели и их циклические анимации остаются редактируемыми в PowerPoint.\n";
  slides.forEach((s,i)=>{md+=`\n## Слайд ${i+1}\n\n${s.notes.trim()}\n`;});
  fs.writeFileSync(out,md);console.log("wrote",out);
}

async function preview(){
  const fontsDir=path.join(SCH,"node_modules/@fontsource");
  const pages=toHtml(slides,path.join(__dirname,"assets"),fontsDir);
  const outDir=path.join(__dirname,"preview");fs.mkdirSync(outDir,{recursive:true});
  const chromiumMod=req("@sparticuz/chromium");const chromium=chromiumMod.default||chromiumMod;
  const puppeteer=req("puppeteer-core");
  if(!fs.existsSync("/tmp/al/lib/libnspr4.so")){
    const zlib=require("zlib");fs.mkdirSync("/tmp/al",{recursive:true});
    const brf=req.resolve("@sparticuz/chromium").replace(/build\/.*$/,"bin/al2023.tar.br");
    fs.writeFileSync("/tmp/al/al.tar",zlib.brotliDecompressSync(fs.readFileSync(brf)));execSync("tar xf al.tar",{cwd:"/tmp/al"});
  }
  process.env.LD_LIBRARY_PATH=(process.env.LD_LIBRARY_PATH||"")+":/tmp/al/lib";
  const browser=await puppeteer.launch({args:[...chromium.args,"--allow-file-access-from-files"],executablePath:await chromium.executablePath(),headless:true});
  const page=await browser.newPage();await page.setViewport({width:1920,height:1080});
  const only=process.argv.find(a=>a.startsWith("--only="));const want=only?only.slice(7).split(",").map(Number):null;
  for(let i=0;i<pages.length;i++){
    if(want&&!want.includes(i+1))continue;
    const html=path.join(outDir,`slide-${String(i+1).padStart(2,"0")}.html`);fs.writeFileSync(html,pages[i]);
    await page.goto("file://"+html,{waitUntil:"networkidle0"});await page.evaluate(()=>document.fonts.ready);
    await page.screenshot({path:html.replace(".html",".png")});fs.unlinkSync(html);
  }
  await browser.close();
  if(!want){
    const sheet=path.join(__dirname,"make_preview.py");
    execSync(`python3 ${sheet} "${path.join(outDir,"slide-*.png")}" "${path.join(OUT,"ekonomika123-3d-presentation-preview.jpg")}"`,{stdio:"inherit"});
  }
  console.log("slide previews ->",outDir);
}

async function main(){
  prepareModels();
  const pptxgen=req("pptxgenjs"),JSZip=req("jszip"),pres=new pptxgen();
  pres.layout="LAYOUT_WIDE";
  pres.author="MyWorkAiBrain";
  pres.subject="Мем-коллаж в стиле оригинала; проект исследования импульсивных трат у студентов";
  pres.title="Почему мы покупаем ненужное? — мемная 3D-презентация";
  pres.company="MyWorkAiBrain";
  toPptx(pres,slides);
  const buf=await pres.write({outputType:"nodebuffer"});
  const zip=await JSZip.loadAsync(buf);
  await injectModels(zip,slides,path.join(MODELS,"glb"));
  await injectTiming(zip,slides);
  await dedupeMedia(zip);
  fs.mkdirSync(OUT,{recursive:true});
  const outfile=path.join(OUT,"ekonomika123-3d-presentation.pptx");
  fs.writeFileSync(outfile,await zip.generateAsync({type:"nodebuffer",compression:"DEFLATE",compressionOptions:{level:9}}));
  console.log("wrote",outfile,(fs.statSync(outfile).size/1e6).toFixed(1)+" MB",slides.length,"slides");
  writeScript();
  fs.copyFileSync(path.join(__dirname,"sources.md"),path.join(OUT,"ekonomika123-3d-presentation-sources.md"));
  if(process.argv.includes("--preview"))await preview();
}
main().catch(err=>{console.error(err);process.exit(1);});
