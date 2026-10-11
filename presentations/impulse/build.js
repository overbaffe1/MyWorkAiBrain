// Build the editable 16:9 deck with native PowerPoint 3D models, GLB animations,
// Morph transitions, speaker notes, per-slide PNG previews and a contact sheet.
const path = require("path");
const fs = require("fs");
const crypto = require("crypto");
const { execSync } = require("child_process");
const SCH = path.join(__dirname, "..", "schumpeter");
const req = require("module").createRequire(path.join(SCH, "package.json"));
const { Slide, toPptx, toHtml } = require(path.join(SCH, "lib"));
const { injectModels, injectTiming, dedupeMedia } = require(path.join(SCH, "pptx3d"));

const A = (name) => path.join(__dirname, "assets", name);
const OUT = path.resolve(__dirname, "../../exports");
const MODELS = path.join(__dirname, "models");
const SW = 13.333, SH = 7.5, N = 10;
const C = {
  bg: "0B1422", paper: "F4F1E8", muted: "AAB6C6", muted2: "75859A",
  blue: "8EB9F4", teal: "76D6C5", gold: "EABF72", coral: "FF8272",
  card: "152238", card2: "1A2A42", ink: "09111D", line: "50647A",
};
const L = 0.76, RIGHT = 12.58, CW = RIGHT-L;
const slides = [];

const run = (text, options={}) => ({ text, options });
const br = (text, options={}) => ({ text, options: { ...options, breakLine:true } });

function chrome(s, idx, kicker) {
  s.bg = C.bg;
  s.img(A("stage-bg.jpg"), {x:0,y:0,w:SW,h:SH,name:"Background"});
  s.line({x1:L,y1:.36,x2:RIGHT,y2:.36,color:"FFFFFF",lineT:91,width:.65,name:"!!toprule"});
  s.rect({x:L,y:.348,w:CW*idx/N,h:.024,fill:C.teal,name:"!!progress"});
  s.text("ПСИХОЛОГИЯ ПОКУПКИ  /  ПРОЕКТ", {
    x:L,y:.49,w:5.9,h:.24,size:9.5,bold:true,color:C.teal,charSpacing:1.8,name:"!!series"
  });
  s.text(`${String(idx).padStart(2,"0")}  /  ${N}`, {
    x:RIGHT-1.1,y:.48,w:1.1,h:.24,size:9.5,bold:true,color:C.muted,align:"right",charSpacing:1.5,name:"!!page"
  });
  if(kicker) s.text(kicker.toUpperCase(), {
    x:L,y:.82,w:7.0,h:.25,size:9.5,bold:true,color:C.gold,charSpacing:2.2,name:"!!kicker",ag:1
  });
  s.line({x1:L,y1:7.02,x2:RIGHT,y2:7.02,color:"FFFFFF",lineT:90,width:.65,name:"!!bottomrule"});
  s.text("ПРОЕКТ ИССЛЕДОВАНИЯ  ·  НЕ РЕЗУЛЬТАТЫ ОПРОСА", {
    x:L,y:7.12,w:7.6,h:.2,size:8.3,color:C.muted2,charSpacing:1.0,name:"!!footer"
  });
}

function title(s, text, opts={}) {
  s.text(text, {
    x:opts.x??L,y:opts.y??1.13,w:opts.w??7.0,h:opts.h??.92,
    font:"head",size:opts.size??32,bold:opts.bold??false,color:opts.color??C.paper,
    lineSpacingMultiple:.94,valign:"top",name:opts.name??"!!title",ag:opts.ag??1
  });
}
function label(s,text,x,y,w,color=C.teal,opts={}) {
  s.text(text.toUpperCase(),{x,y,w,h:opts.h??.22,size:opts.size??9,bold:true,color,charSpacing:opts.spacing??1.4,ag:opts.ag});
}
function card(s,x,y,w,h,opts={}) {
  s.rect({x,y,w,h,fill:opts.fill??C.card,fillT:opts.fillT??4,line:opts.line??C.line,lineT:opts.lineT??72,
    lineW:opts.lineW??.8,radius:opts.radius??.075,shadow:opts.shadow??false,ag:opts.ag});
}
function stage(s,key,o={}) {
  const x=o.x??8.08, y=o.y??1.06, size=o.s??4.55, rot=o.rot??[12,-24,0];
  const cx=x+size/2,cy=y+size/2+(o.dy??0),g=size*(o.glow??1.40);
  s.img(A("glow.png"),{x:cx-g/2,y:cy-g/2,w:g,h:g,name:"!!stageglow"});
  const r1=size*.48,r2=size*.61;
  s.rect({x:cx-r1,y:cy-r1,w:r1*2,h:r1*2,shape:"ellipse",line:C.teal,lineT:82,lineW:.7,name:"!!ring1"});
  s.rect({x:cx-r2,y:cy-r2,w:r2*2,h:r2*2,shape:"ellipse",line:C.blue,lineT:90,lineW:.7,dash:"dash",name:"!!ring2"});
  const shw=size*(o.shw??.78),shy=y+size*(o.shy??.83);
  s.img(A("shadow.png"),{x:cx-shw/2,y:shy-shw/8,w:shw,h:shw/4,name:"!!shadow"});
  s.model(key,{x,y,s:size,rot,name:`!!m-${key}`,px:o.px??Math.min(850,Math.round(size*160))});
  s.hero={key,x,y,s:size,rot};
  if(o.caption){
    const cw=o.cw??4.4,capx=o.capx??cx-cw/2,capy=o.capy??(y+size+.10);
    s.text([{text:o.caption,options:{color:C.muted,size:9.5,breakLine:true}},
      {text:o.subcaption??"3D-ЭКСПОНАТ · ЦИКЛИЧЕСКАЯ АНИМАЦИЯ",options:{color:C.muted2,size:8,bold:true,charSpacing:.9}}],
      {x:capx,y:capy,w:cw,h:.48,align:o.align??"center",lineSpacingMultiple:1.0,ag:8});
  }
}
function citation(s,text,y=6.55) {
  s.text(text,{x:L,y,w:7.1,h:.24,size:8.5,color:C.muted2,charSpacing:.35});
}
function body(s,text,x,y,w,h,opts={}) {
  s.text(text,{x,y,w,h,size:opts.size??12.5,color:opts.color??C.muted,
    bold:opts.bold??false,font:opts.font??"body",lineSpacingMultiple:opts.lh??1.04,
    valign:opts.valign??"top",align:opts.align??"left",ag:opts.ag});
}
function numberedCard(s,n,head,desc,x,y,w,h,opts={}) {
  card(s,x,y,w,h,{ag:opts.ag??2,fill:opts.fill??C.card,line:opts.line??C.line,lineT:opts.lineT??75});
  s.text(n,{x:x+.18,y:y+.16,w:.55,h:.36,font:"head",size:18,color:opts.accent??C.teal,ag:opts.ag??2});
  s.text(head,{x:x+.80,y:y+.10,w:w-.98,h:.24,size:opts.headSize??13.2,bold:true,color:C.paper,ag:opts.ag??2});
  body(s,desc,x+.80,y+.38,w-1.0,.20,{size:opts.bodySize??10.5,ag:opts.ag??2});
}

// 1 — cover: a cart and a phone, not a stock photo.
{
  const s=new Slide({notes:
`Представьте: вы открыли маркетплейс на минуту, а через несколько кликов уже заказали вещь, которую не планировали. Это не диагноз и не просто недостаток силы воли: здесь взаимодействуют условия покупки, эмоции и быстрый интерфейс. В исходной презентации был проект о психологических механизмах незапланированных трат у студентов. Я сохранила тему и задачи, но перестроила материал: от актуальности и модели поведения — к проверяемым гипотезам, дизайну исследования и памятке. Важно: опрос ещё не проведён, поэтому предположения не выдаются за результаты. На слайдах — созданные для этой работы анимированные 3D-экспонаты.`});
  chrome(s,1,"Тема проекта");
  stage(s,"cart",{x:6.70,y:.72,s:5.90,rot:[9,-20,0],px:920,shy:.86,caption:"Корзина, посылка и сигнал нового заказа",subcaption:"Покупка становится простой — решение не всегда" ,capx:7.6,capy:6.02,cw:4.8});
  label(s,"Исследование · студенты 18–25 лет",L,1.40,6.4,C.teal,{size:10});
  s.text([br("Почему мы",{size:45,bold:true,color:C.paper}),br("покупаем",{size:45,bold:true,color:C.paper}),run("ненужное?",{size:45,bold:true,color:C.gold})],
    {x:L,y:1.83,w:5.9,h:2.35,font:"head",color:C.paper,lineSpacingMultiple:.91,name:"!!cover-title",ag:2});
  s.rect({x:L,y:4.42,w:.74,h:.045,fill:C.teal,ag:3});
  body(s,"Психология импульсивных трат — от цифрового триггера до проверяемой гипотезы",L,4.67,5.55,.73,{size:16,color:C.paper,lh:1.03,ag:3});
  card(s,L,5.70,5.25,.53,{fill:C.card2,line:C.teal,lineT:58,ag:4});
  s.text("ПЛАН ИССЛЕДОВАНИЯ  ·  НЕ ОТЧЁТ О РЕЗУЛЬТАТАХ",{x:L+.20,y:5.87,w:4.88,h:.19,size:9.2,bold:true,color:C.teal,charSpacing:.7,ag:4});
  slides.push(s);
}

// 2 — relevance, with the market figure carefully described.
{
  const s=new Slide({notes:
`Почему тема актуальна? По оценке сервиса «Долями» от Т-Банка, российский оборот BNPL-сервисов в 2025 году составил около 940 миллиардов рублей. Это оценка рынка оплаты частями, а не измерение импульсивных покупок и не официальная статистика поведения студентов. С 1 апреля 2026 года действует федеральный закон № 283-ФЗ о сервисах рассрочки. Он вводит требования к операторам, но сам по себе не отключает уведомления, социальные сигналы и ощущение срочности. Поэтому финансовый контекст соединяется с психологическим вопросом: какие ситуации связаны с незапланированными решениями?`});
  chrome(s,2,"Почему это важно сейчас");
  title(s,"Платёж стал проще — вопрос стал важнее",{w:7.05,size:29,h:1.0});
  card(s,L,2.36,6.82,1.46,{fill:C.card2,line:C.blue,lineT:50,ag:2});
  label(s,"Оценка рынка BNPL в России · 2025",L+.23,2.58,5.9,C.blue,{ag:2});
  s.text("≈ 940 млрд ₽",{x:L+.22,y:2.90,w:3.45,h:.52,font:"head",size:31,bold:true,color:C.paper,ag:2});
  body(s,"оборот оплат частями по оценке сервиса «Долями» (Т-Банк)",L+3.55,2.99,3.55,.48,{size:11,color:C.muted,ag:2});
  card(s,L,4.00,6.82,1.35,{fill:C.card,line:C.teal,lineT:66,ag:3});
  label(s,"Регуляторный контекст",L+.23,4.20,5.8,C.teal,{ag:3});
  s.text("283-ФЗ · с 1 апреля 2026",{x:L+.22,y:4.51,w:3.9,h:.38,font:"head",size:20,color:C.paper,ag:3});
  body(s,"Новые требования к сервисам рассрочки — не замена личному бюджету и саморегуляции.",L+3.62,4.46,3.60,.65,{size:10.5,color:C.muted,ag:3});
  card(s,L,5.67,6.82,.61,{fill:"261F18",line:C.gold,lineT:55,ag:4});
  body(s,"Важно: оборот BNPL ≠ число импульсивных покупок. Это контекст, не доказательство причины.",L+.20,5.85,6.40,.26,{size:10.3,color:C.gold,bold:true,ag:4});
  citation(s,"Источники: [1] оценка «Долями» в «Ведомостях»; [2] официальный текст закона № 283-ФЗ.",6.50);
  stage(s,"wallet",{x:8.11,y:1.13,s:4.47,rot:[12,-22,0],px:740,caption:"Монета выходит из кошелька и возвращается",subcaption:"Оплата частями — финансовый контекст, не ярлык поведения",cw:4.6});
  slides.push(s);
}

// 3 — the mechanism as a cautious conceptual sequence.
{
  const s=new Slide({notes:
`В исследованиях импульсивную покупку описывают не как любую спонтанность, а как сильный позыв купить при ограниченном обдумывании. Упрощённая схема здесь: внешний сигнал — например, уведомление или ограниченная акция; внутренний отклик — предвкушение или страх упустить; действие — быстрый заказ; затем может появиться удовлетворение, сожаление или вопрос, укладывается ли покупка в бюджет. Это не обязательные стадии для каждого человека, а рабочая карта проекта. Важно измерять и сам позыв, и фактические эпизоды за период, а не спрашивать только «считаете ли вы себя импульсивным».`});
  chrome(s,3,"Как возникает импульс");
  title(s,"Импульс — это цепочка, а не одна кнопка",{w:7.1,size:29,h:1.0});
  body(s,"Рабочая модель для исследования: контекст и переживание участвуют в решении; исход у людей различается.",L,2.18,6.7,.50,{size:13,color:C.muted,ag:2});
  const items=[
    ["01","СИГНАЛ","уведомление · таймер"],
    ["02","ОТКЛИК","интерес · FOMO"],
    ["03","ДЕЙСТВИЕ","корзина · оплата"],
    ["04","ПОСЛЕ","радость · сожаление"],
  ];
  const w=1.58,gap=.14,y=3.05;
  items.forEach(([n,h,d],i)=>{
    const x=L+i*(w+gap),accent=i===1?C.coral:(i===3?C.gold:C.teal);
    card(s,x,y,w,1.43,{fill:i===1?"241D2B":C.card,line:accent,lineT:68,ag:2+i});
    s.text(n,{x:x+.17,y:y+.16,w:.45,h:.3,font:"head",size:15,color:accent,ag:2+i});
    s.text(h,{x:x+.17,y:y+.55,w:w-.30,h:.24,size:9.5,bold:true,color:C.paper,charSpacing:.8,ag:2+i});
    body(s,d,x+.17,y+.88,w-.30,.37,{size:9.8,color:C.muted,ag:2+i});
    if(i<3)s.text("→",{x:x+w,y:y+.48,w:gap,h:.30,size:15,bold:true,color:C.muted2,align:"center",ag:2+i});
  });
  card(s,L,4.93,6.82,.90,{fill:C.card2,line:C.blue,lineT:74,ag:6});
  label(s,"Операционное определение",L+.20,5.10,4.5,C.blue,{ag:6});
  body(s,"Незапланированная покупка за последние 30 дней + частота сильного желания купить «здесь и сейчас».",L+.20,5.40,6.28,.27,{size:11.0,color:C.paper,ag:6});
  citation(s,"Теоретическая опора: Rook (1987); Beatty & Ferrell (1998). См. [3], [4].",6.48);
  stage(s,"cycle",{x:8.10,y:1.12,s:4.48,rot:[12,-20,0],px:740,caption:"Четыре сигнала вращаются вокруг покупки",subcaption:"Схема — модель для проверки, не универсальный сценарий",cw:4.65});
  slides.push(s);
}

// 4 — possible triggers.
{
  const s=new Slide({notes:
`Проверяем не «плохой характер», а возможные условия решения. Первый блок — FOMO, тревога, что упустишь выгодный или социально значимый опыт. Второй — социальное сравнение: тренд, рекомендация, лайки, ощущение «все уже купили». Третий — срочность и дефицит, например таймер. Четвёртый — низкое трение: сохранённая карта и оформление в пару касаний. Метаанализ исследований онлайн-покупок обнаруживает связи импульсивного поведения с ситуационными, маркетинговыми и платформенными факторами. Но это не доказывает, что любой баннер вызовет покупку у любого студента. Гипотезы поэтому сформулированы как проверяемые связи.`});
  chrome(s,4,"Что может подтолкнуть");
  title(s,"Четыре триггера встречаются на одном экране",{w:7.15,size:28,h:1.0});
  const rows=[
    ["FOMO","«Вдруг упущу»","ограниченная акция · тренд",C.coral],
    ["Сравнение","«У всех уже есть»","лайки · рекомендации · блогеры",C.blue],
    ["Срочность","«Решай сейчас»","таймер · «осталось мало»",C.gold],
    ["Меньше трения","«Всего один тап»","сохранённая карта · автозаполнение",C.teal],
  ];
  rows.forEach(([h,q,d,accent],i)=>{
    const y=2.35+i*.86;
    card(s,L,y,6.82,.70,{fill:i===0?"241D2B":C.card,line:accent,lineT:72,ag:2+i});
    s.rect({x:L+.17,y:y+.17,w:.055,h:.36,fill:accent,ag:2+i});
    s.text(h,{x:L+.36,y:y+.13,w:1.60,h:.24,size:12.3,bold:true,color:C.paper,ag:2+i});
    s.text(q,{x:L+2.0,y:y+.13,w:2.35,h:.24,size:11.3,bold:true,color:accent,ag:2+i});
    body(s,d,L+2.0,y+.39,4.46,.18,{size:9.6,color:C.muted,ag:2+i});
  });
  card(s,L,5.98,6.82,.43,{fill:"152435",line:C.blue,lineT:83,ag:6});
  body(s,"Связь в литературе — не доказательство причинности для нашей выборки.",L+.18,6.10,6.40,.20,{size:9.4,color:C.blue,bold:true,ag:6});
  citation(s,"Опора: Anoop & Rahman (2025); Przybylski et al. (2013); Gibbons & Buunk (1999). [4]–[6]",6.54);
  stage(s,"triggers",{x:8.12,y:1.11,s:4.46,rot:[12,-23,0],px:740,caption:"Телефон и три пульсирующих сигнала",subcaption:"Уведомление · социальное одобрение · срочность",cw:4.65});
  slides.push(s);
}

// 5 — hypotheses retained and made falsifiable.
{
  const s=new Slide({notes:
`Сохраняю три гипотезы исходной работы, но делаю их измеримыми. Первая: более высокий FOMO связан с более частыми незапланированными покупками за последние 30 дней, включая использование оплаты частями. Вторая: склонность сравнивать себя с другими связана с самоотчётами о статусных или трендовых покупках. Третья — финансовая грамотность может быть связана с более низкой выраженностью импульсивных покупок, но мы не предполагаем, что знания полностью устраняют эмоциональные триггеры. Это гипотезы, не предварительные выводы. Одномоментный онлайн-опрос покажет корреляции, но не докажет, что один фактор вызвал другой.`});
  chrome(s,5,"Гипотезы проекта");
  title(s,"Три гипотезы — и ни одной заранее доказанной",{w:7.2,size:27.5,h:1.0});
  const hs=[
    ["H1","FoMO ↔ незапланированные покупки","Более высокий FoMO связан с большей частотой незапланированных покупок / оплаты частями.",C.coral],
    ["H2","Социальное сравнение ↔ статусные траты","Склонность сравнивать себя с другими связана с более частыми покупками «как у всех».",C.blue],
    ["H3","Финансовые знания ↔ импульсивность","Проверяем связь; не предполагаем, что одни знания полностью снимают влияние эмоций.",C.teal],
  ];
  hs.forEach(([n,h,d,accent],i)=>{
    const y=2.38+i*1.04;
    card(s,L,y,6.82,.88,{fill:i===2?"172723":C.card,line:accent,lineT:67,ag:2+i});
    s.text(n,{x:L+.20,y:y+.20,w:.60,h:.36,font:"head",size:19,bold:true,color:accent,ag:2+i});
    s.text(h,{x:L+.95,y:y+.15,w:5.55,h:.26,size:12.0,bold:true,color:C.paper,ag:2+i});
    body(s,d,L+.95,y+.47,5.58,.29,{size:10,color:C.muted,ag:2+i});
  });
  card(s,L,5.72,6.82,.54,{fill:"261F18",line:C.gold,lineT:63,ag:5});
  body(s,"H1–H3 — проверяемые предположения. Никакой связи пока не измеряли.",L+.20,5.88,6.39,.20,{size:10.1,color:C.gold,bold:true,ag:5});
  citation(s,"Шкалы FoMO и социального сравнения: первоисточники [5], [6]. Финансовая грамотность: [7].",6.50);
  stage(s,"scale",{x:8.10,y:1.12,s:4.48,rot:[8,-22,0],px:740,caption:"Весы мягко колеблются — баланс не предрешён",subcaption:"Гипотеза может подтвердиться, ослабнуть или не подтвердиться",cw:4.7});
  slides.push(s);
}

// 6 — study design.
{
  const s=new Slide({notes:
`План выборки: студенты 18–25 лет, ориентир — не менее пятидесяти ответов. При такой удобной выборке результат следует считать пилотным, а не описанием всех студентов России. Анкета анонимная: возрастной диапазон, эпизоды незапланированных покупок за последние 30 дней, сценарии оплаты и несколько блоков измерений. Для FoMO и социального сравнения нужно брать опубликованные шкалы, аккуратно перевести и проверить понятность на небольшом пилоте; нельзя произвольно менять формулировки, если это разрушит смысл шкалы. Финансовые знания можно оценить коротким блоком базовых вопросов по инструментарию OECD. До опроса — добровольное согласие, минимум данных, без имён и контактов.`});
  chrome(s,6,"Дизайн исследования");
  title(s,"Опрос: студенты 18–25 лет, анонимно",{w:7.2,size:29,h:.92});
  card(s,L,2.28,6.82,.70,{fill:C.card2,line:C.teal,lineT:60,ag:2});
  s.text("N ≥ 50",{x:L+.22,y:2.43,w:1.45,h:.33,font:"head",size:22,bold:true,color:C.teal,ag:2});
  body(s,"пилотная удобная выборка · результат не представляет всех студентов",L+1.78,2.47,4.76,.23,{size:10.6,color:C.paper,ag:2});
  const methods=[
    ["01","Кого","совершеннолетние студенты 18–25 лет"],
    ["02","Что спросить","эпизоды за 30 дней · BNPL отдельно"],
    ["03","Как беречь данные","добровольно · анонимно · минимум сведений"],
  ];
  methods.forEach(([n,h,d],i)=>numberedCard(s,n,h,d,L,3.23+i*.79,6.82,.65,{ag:3+i,headSize:12.0,bodySize:9.7}));
  card(s,L,5.76,6.82,.59,{fill:"152435",line:C.blue,lineT:80,ag:6});
  body(s,"Измерения: FoMO · социальное сравнение · базовые финансовые знания · импульсивные покупки.",L+.20,5.91,6.4,.22,{size:9.7,color:C.blue,bold:true,ag:6});
  citation(s,"Ориентиры для измерений: [5]–[7]. Перевод и пилот шкал — до основного опроса.",6.51);
  stage(s,"clipboard",{x:8.11,y:1.10,s:4.48,rot:[12,-20,0],px:740,caption:"Карандаш отмечает ответ — без имени и телефона",subcaption:"N ≥ 50 — пилот, а не репрезентативный опрос",cw:4.7});
  slides.push(s);
}

// 7 — analysis and its limits.
{
  const s=new Slide({notes:
`Для пилотных данных подойдут описательные распределения, проверка внутренней согласованности блоков и ранговые корреляции Спирмена с доверительными интервалами. Зависимую переменную нужно задать заранее: например, частота незапланированных покупок; оплату частями анализировать отдельным пунктом. При небольшой выборке не стоит перегружать модель множеством предикторов или искать причинность. Главные ограничения тоже видны на слайде: добровольный опрос может не представлять всех, самоотчёты зависят от памяти и готовности отвечать, а одномоментные данные не показывают, что было причиной. Если гипотеза не подтвердится — это содержательный результат, а не провал проекта.`});
  chrome(s,7,"Как читать результаты");
  title(s,"Статистика покажет связи — но не причинность",{w:7.2,size:27.8,h:1.04});
  const tests=[
    ["H1","FoMO ↔ частота незапланированных покупок","Спирмен · отдельно описать BNPL",C.coral],
    ["H2","Сравнение ↔ статусные / трендовые покупки","Спирмен · показать доверительный интервал",C.blue],
    ["H3","Финансовые знания ↔ импульсивность","Исследовательская связь; не обещать защитный эффект",C.teal],
  ];
  tests.forEach(([n,h,d,accent],i)=>{
    const y=2.31+i*.76;
    s.text(n,{x:L,y:y+.05,w:.55,h:.30,font:"head",size:17,color:accent,ag:2+i});
    s.text(h,{x:L+.64,y,w:6.0,h:.25,size:11.8,bold:true,color:C.paper,ag:2+i});
    body(s,d,L+.64,y+.30,6.0,.22,{size:9.6,color:C.muted,ag:2+i});
    if(i<2)s.line({x1:L+.64,y1:y+.64,x2:L+6.75,y2:y+.64,color:"FFFFFF",lineT:89,width:.6,ag:2+i});
  });
  label(s,"Ограничения",L,4.79,2.2,C.gold,{ag:5});
  const limits=[["удобная выборка","не все студенты"],["самоотчёт","память и ответы"],["один замер","не причинность"]];
  limits.forEach(([a,b],i)=>{
    const x=L+i*2.30;
    card(s,x,5.08,2.16,.78,{fill:C.card,line:C.gold,lineT:78,ag:5+i});
    s.text(a,{x:x+.13,y:5.22,w:1.91,h:.22,size:10.2,bold:true,color:C.paper,align:"center",ag:5+i});
    body(s,b,x+.13,5.50,1.91,.20,{size:9.4,color:C.muted,align:"center",ag:5+i});
  });
  citation(s,"Итоги будут предварительными. Нужны прозрачные метрики и описание пропусков/ограничений.",6.48);
  stage(s,"chart",{x:8.11,y:1.10,s:4.48,rot:[10,-22,0],px:740,caption:"Три показателя и лупа: ищем связь, не причину",subcaption:"Пилотные данные требуют осторожной интерпретации",cw:4.7});
  slides.push(s);
}

// 8 — a practical guide/memo.
{
  const s=new Slide({notes:
`Памятка должна быть простой и не обвиняющей. Первое — создать паузу: отложить необязательную покупку хотя бы до следующего дня, особенно если на экране таймер. Второе — проверить три вещи: нужна ли вещь вне акции, какова полная цена и сколько уже платежей приходится на месяц. Третье — добавить полезное трение: убрать лишние уведомления, не хранить карту на каждом сайте, возвращаться к отложенной корзине позже. Рассрочка может быть удобным способом оплаты, но маленький платёж не отменяет общей суммы. Это поведенческие подсказки для будущей памятки, а не обещание, что они подходят всем или решают проблему.`});
  chrome(s,8,"Практическая часть проекта");
  title(s,"Памятка: пауза, проверка, выбор",{w:7.0,size:29,h:.94});
  const tips=[
    ["01","Пауза","Отложи необязательную покупку до завтра — особенно при таймере.",C.teal],
    ["02","Проверка","Нужна ли вещь без скидки? Какова полная цена? Сколько платежей уже в месяце?",C.gold],
    ["03","Трение","Отключи лишние уведомления; убери сохранённую карту; вернись к корзине позже.",C.blue],
  ];
  tips.forEach(([n,h,d,accent],i)=>{
    const y=2.35+i*1.03;
    card(s,L,y,6.82,.89,{fill:C.card,line:accent,lineT:73,ag:2+i});
    s.text(n,{x:L+.18,y:y+.19,w:.59,h:.35,font:"head",size:18,color:accent,ag:2+i});
    s.text(h,{x:L+.91,y:y+.16,w:1.55,h:.25,size:12.4,bold:true,color:C.paper,ag:2+i});
    body(s,d,L+2.25,y+.16,4.28,.52,{size:10.5,color:C.muted,ag:2+i});
  });
  card(s,L,5.66,6.82,.63,{fill:"261F18",line:C.gold,lineT:58,ag:5});
  body(s,"Оплата частями меняет график платежа, но не уменьшает полную стоимость покупки.",L+.20,5.84,6.41,.23,{size:10.5,color:C.gold,bold:true,ag:5});
  citation(s,"Материал для самопроверки, не медицинская рекомендация и не обещание эффекта.",6.51);
  stage(s,"hourglass",{x:8.10,y:1.10,s:4.48,rot:[12,-18,0],px:740,caption:"Песчинка проходит через стекло: сначала пауза",subcaption:"Небольшой промежуток возвращает время на выбор",cw:4.7});
  slides.push(s);
}

// 9 — contribution and the project's own conclusion.
{
  const s=new Slide({notes:
`Цель проекта — понять, какие когнитивные и эмоциональные факторы связаны с незапланированными покупками студентов, и подготовить на этой основе короткую памятку. Даже если связь между грамотностью и импульсивностью окажется слабой или неоднозначной, это будет полезным выводом: значит, одной теории бюджета недостаточно и стоит отдельно проверять самоконтроль, стресс или контекст интерфейса. Мы не будем утверждать, что маркетплейсы «управляют мозгом» или что рассрочка автоматически ведёт к долгам. Более точный вывод: среда может облегчать решение, а исследование проверит, с какими факторами оно связано у выбранной группы. Главная практическая идея — не запретить покупки, а вернуть человеку паузу и ясность полной цены.`});
  chrome(s,9,"Ожидаемый результат");
  title(s,"Что даст проект — даже если связи нет",{w:7.2,size:29,h:1.0});
  body(s,"Цель: проверить факторы, связанные с незапланированными тратами студентов, и превратить выводы в полезную памятку.",L,2.26,6.75,.56,{size:12.6,color:C.muted,ag:2});
  const outcomes=[
    ["Измерить","частоту эпизодов и контекст оплаты"],
    ["Сопоставить","FoMO · сравнение · знания"],
    ["Сделать","короткий инструмент самопроверки"],
  ];
  outcomes.forEach(([h,d],i)=>{
    const y=3.10+i*.80;
    card(s,L,y,6.82,.64,{fill:i===2?"172723":C.card,line:i===2?C.teal:C.line,lineT:75,ag:3+i});
    label(s,String(i+1).padStart(2,"0"),L+.19,y+.20,.46,i===2?C.teal:C.blue,{ag:3+i});
    s.text(h,{x:L+.84,y:y+.13,w:1.48,h:.26,size:12.0,bold:true,color:C.paper,ag:3+i});
    body(s,d,L+2.30,y+.15,4.13,.26,{size:10.2,color:C.muted,ag:3+i});
  });
  card(s,L,5.73,6.82,.68,{fill:"182235",line:C.gold,lineT:57,ag:6});
  s.text("«Не запретить себе покупать, а вернуть себе секунду выбора»",{x:L+.18,y:5.90,w:6.45,h:.31,font:"head",size:14.3,italic:true,color:C.gold,align:"center",ag:6});
  citation(s,"Результат опроса пока отсутствует. Гипотезы, выводы и памятка требуют проверки.",6.52);
  stage(s,"compass",{x:8.10,y:1.10,s:4.48,rot:[10,-22,0],px:740,caption:"Стрелка колеблется и возвращается к направлению",subcaption:"Осознанный выбор — не идеальная рациональность",cw:4.7});
  slides.push(s);
}

// 10 — concise references, accessible full list in the companion sources file.
{
  const s=new Slide({notes:
`В завершение — основные источники: классическая работа Денниса Рука о субъективном опыте импульсивной покупки; метаанализ онлайн-покупок; оригинальная работа по шкале FoMO; руководство OECD для измерения финансовой грамотности; официальный текст закона об услугах рассрочки и публикация деловой прессы, откуда взята оценка рынка. Полные ссылки и карта того, какие факты к какому слайду относятся, есть в файле источников. Ещё раз: 940 миллиардов — оборот BNPL по оценке отраслевого участника, а не число импульсивных покупок. Наш собственный опрос пока только запланирован. Спасибо — какие вопросы?`});
  chrome(s,10,"Источники и вопросы");
  title(s,"Спасибо! Вопросы?",{w:6.8,size:32,h:.88});
  label(s,"Ключевые источники · полный список в приложении",L,2.05,6.8,C.teal,{ag:2});
  const refs=[
    ["[1]","Ведомости, 03.02.2026 · оценка BNPL от «Долями» / Т-Банка"],
    ["[2]","ФЗ от 31.07.2025 № 283-ФЗ · официальный текст"],
    ["[3]","Rook, 1987 · The Buying Impulse · doi:10.1086/209105"],
    ["[4]","Anoop & Rahman, 2025 · online impulse buying · doi:10.1002/cb.2418"],
    ["[5]","Przybylski et al., 2013 · FoMO · doi:10.1016/j.chb.2013.02.014"],
    ["[6]","Gibbons & Buunk, 1999 · social comparison · doi:10.1037/0022-3514.76.1.129"],
    ["[7]","OECD/INFE, 2022 · financial literacy toolkit"],
  ];
  refs.forEach(([n,t],i)=>{
    const y=2.42+i*.49;
    s.text(n,{x:L,y,w:.43,h:.24,size:10.3,bold:true,color:C.gold,ag:2+Math.floor(i/3)});
    body(s,t,L+.53,y,6.48,.28,{size:9.6,color:C.paper,ag:2+Math.floor(i/3)});
  });
  body(s,"Полные библиографические записи, ссылки и примечания к цифрам — в exports/ekonomika123-3d-presentation-sources.md.",L,5.97,6.85,.44,{size:9.3,color:C.muted,ag:5});
  stage(s,"cart",{x:8.12,y:1.15,s:4.45,rot:[9,-16,0],px:700,caption:"Возвращаемся к главному вопросу",subcaption:"Пауза — тоже часть решения",cw:4.65});
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
    console.log(`Rendering ${jobs.length} 3D model posters…`);
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
    "**Формат:** 10 слайдов, ориентир 5–6 минут спокойной речи. Тот же текст встроен в заметки докладчика `.pptx`. " +
    "Это план исследования: собственный опрос ещё не проведён, поэтому фактические результаты не заявляются. " +
    "На каждом слайде — процедурно созданный 3D-экспонат со скелетной циклической анимацией.\n";
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
  pres.subject="Психология импульсивных трат у студентов; исследовательский проект";
  pres.title="Почему мы покупаем ненужное? — 3D-презентация";
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
