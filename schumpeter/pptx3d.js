// Post-processing of the pptxgenjs output:
//  * injectModels: turns placeholder pictures named "MODEL::<id>::<name>" into native
//    PowerPoint 3D models (mc:AlternateContent → p:graphicFrame/am3d:model3d, with the
//    rendered PNG as raster + p:pic fallback for apps without 3D support)
//  * injectTiming: Morph transition + auto-playing entrance animations (fade-up)
// XML structure follows PowerPoint's own output for inserted 3D models (Office3DRenderer).
const fs = require("fs");
const path = require("path");

const AM3D = "http://schemas.microsoft.com/office/drawing/2017/model3d";
const REL_MODEL = "http://schemas.microsoft.com/office/2017/06/relationships/model3d";
const EMU = 914400;

// ---------- glb bounding box (world space, scene 0) ----------
function glbBounds(buf) {
  const jsonLen = buf.readUInt32LE(12);
  const gltf = JSON.parse(buf.slice(20, 20 + jsonLen).toString("utf8"));
  const meshB = (gltf.meshes || []).map((m) => {
    const mn = [Infinity, Infinity, Infinity], mx = [-Infinity, -Infinity, -Infinity];
    for (const p of m.primitives) {
      const a = gltf.accessors[p.attributes.POSITION];
      for (let i = 0; i < 3; i++) { mn[i] = Math.min(mn[i], a.min[i]); mx[i] = Math.max(mx[i], a.max[i]); }
    }
    return [mn, mx];
  });
  const mul = (a, b) => {
    const r = new Array(16).fill(0);
    for (let c = 0; c < 4; c++) for (let rr = 0; rr < 4; rr++)
      for (let k = 0; k < 4; k++) r[c * 4 + rr] += a[k * 4 + rr] * b[c * 4 + k];
    return r;
  };
  const local = (n) => {
    if (n.matrix) return n.matrix;
    const [tx, ty, tz] = n.translation || [0, 0, 0];
    const [qx, qy, qz, qw] = n.rotation || [0, 0, 0, 1];
    const [sx, sy, sz] = n.scale || [1, 1, 1];
    const x2 = qx + qx, y2 = qy + qy, z2 = qz + qz;
    const xx = qx * x2, xy = qx * y2, xz = qx * z2, yy = qy * y2, yz = qy * z2, zz = qz * z2;
    const wx = qw * x2, wy = qw * y2, wz = qw * z2;
    return [(1 - yy - zz) * sx, (xy + wz) * sx, (xz - wy) * sx, 0, (xy - wz) * sy, (1 - xx - zz) * sy, (yz + wx) * sy, 0,
      (xz + wy) * sz, (yz - wx) * sz, (1 - xx - yy) * sz, 0, tx, ty, tz, 1];
  };
  const mn = [Infinity, Infinity, Infinity], mx = [-Infinity, -Infinity, -Infinity];
  const visit = (ni, parent) => {
    const n = gltf.nodes[ni];
    const w = mul(parent, local(n));
    if (n.mesh !== undefined) {
      const [a, b] = meshB[n.mesh];
      for (let c = 0; c < 8; c++) {
        const p = [c & 1 ? b[0] : a[0], c & 2 ? b[1] : a[1], c & 4 ? b[2] : a[2]];
        for (let i = 0; i < 3; i++) {
          const v = w[i] * p[0] + w[4 + i] * p[1] + w[8 + i] * p[2] + w[12 + i];
          mn[i] = Math.min(mn[i], v); mx[i] = Math.max(mx[i], v);
        }
      }
    }
    (n.children || []).forEach((c) => visit(c, w));
  };
  const I = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
  gltf.scenes[gltf.scene || 0].nodes.forEach((n) => visit(n, I));
  const ext = mx.map((v, i) => v - mn[i]);
  const center = mx.map((v, i) => (v + mn[i]) / 2);
  return { ext, center, maxExt: Math.max(...ext) };
}

// ---------- embedded (skinned) animation: loop length in ms, 0 if the glb has none ----------
function glbAnimMs(buf) {
  const jsonLen = buf.readUInt32LE(12);
  const gltf = JSON.parse(buf.slice(20, 20 + jsonLen).toString("utf8"));
  const anim = (gltf.animations || [])[0];
  if (!anim || !(gltf.skins || []).length) return 0;  // PowerPoint only plays skinned animations
  let t = 0;
  for (const smp of anim.samplers) t = Math.max(t, (gltf.accessors[smp.input].max || [0])[0]);
  return Math.round(t * 1000);
}

const A3DANIM = "http://schemas.microsoft.com/office/drawing/2018/animation/model3d";
const animExt = (ms) => `<am3d:extLst>` +
  `<a:ext uri="{9A65AA19-BECB-4387-8358-8AD5134E1D82}"><a3danim:embedAnim xmlns:a3danim="${A3DANIM}" animId="0"><a3danim:animPr length="${ms}" count="indefinite"/></a3danim:embedAnim></a:ext>` +
  `<a:ext uri="{E9DE012E-A134-456F-84FE-255F9AAD75C6}"><a3danim:posterFrame xmlns:a3danim="${A3DANIM}" animId="0"/></a:ext>` +
  `</am3d:extLst>`;

const ptLight = (r, g, b, n, x, y, z) =>
  `<am3d:ptLight rad="0"><am3d:clr><a:scrgbClr r="${r}" g="${g}" b="${b}"/></am3d:clr><am3d:intensity n="${n}" d="1000000"/><am3d:pos x="${x}" y="${y}" z="${z}"/></am3d:ptLight>`;

function model3dXml({ id, name, x, y, size, rot, glbRel, imgRel, bounds, guid, animMs }) {
  const { ext, center, maxExt } = bounds;
  const mpu = 1 / maxExt;
  const r = Math.hypot(...ext.map((e) => e / maxExt / 2));
  const camZ = Math.round((r / Math.sin((22.5 * Math.PI) / 180)) * 36e6);
  const pre = center.map((c) => Math.round(-c * mpu * 36e6));
  const [ax, ay, az] = rot.map((d) => Math.round(d * 60000));
  const off = `<a:off x="${Math.round(x * EMU)}" y="${Math.round(y * EMU)}"/><a:ext cx="${Math.round(size * EMU)}" cy="${Math.round(size * EMU)}"/>`;
  const sz = Math.round(size * EMU);
  const nm = name.replace(/&/g, "&amp;").replace(/"/g, "&quot;");
  const cnv = `<p:cNvPr id="${id}" name="${nm}"><a:extLst><a:ext uri="{FF2B5EF4-FFF2-40B4-BE49-F238E27FC236}"><a16:creationId xmlns:a16="http://schemas.microsoft.com/office/drawing/2014/main" id="${guid}"/></a:ext></a:extLst></p:cNvPr>`;
  return `<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">` +
    `<mc:Choice xmlns:am3d="${AM3D}" Requires="am3d"><p:graphicFrame>` +
    `<p:nvGraphicFramePr>${cnv}<p:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></p:cNvGraphicFramePr><p:nvPr/></p:nvGraphicFramePr>` +
    `<p:xfrm>${off}</p:xfrm><a:graphic><a:graphicData uri="${AM3D}"><am3d:model3d r:embed="${glbRel}">` +
    `<am3d:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="${sz}" cy="${sz}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></am3d:spPr>` +
    `<am3d:camera><am3d:pos x="0" y="0" z="${camZ}"/><am3d:up dx="0" dy="36000000" dz="0"/><am3d:lookAt x="0" y="0" z="0"/><am3d:perspective fov="2700000"/></am3d:camera>` +
    `<am3d:trans><am3d:meterPerModelUnit n="${Math.round(mpu * 1e6)}" d="1000000"/><am3d:preTrans dx="${pre[0]}" dy="${pre[1]}" dz="${pre[2]}"/>` +
    `<am3d:scale><am3d:sx n="1000000" d="1000000"/><am3d:sy n="1000000" d="1000000"/><am3d:sz n="1000000" d="1000000"/></am3d:scale>` +
    `<am3d:rot ax="${ax}" ay="${ay}" az="${az}"/><am3d:postTrans dx="0" dy="0" dz="0"/></am3d:trans>` +
    `<am3d:raster rName="Office3DRenderer" rVer="16.0.8326"><am3d:blip r:embed="${imgRel}"/></am3d:raster>` +
    (animMs ? animExt(animMs) : "") +
    `<am3d:objViewport viewportSz="${sz}"/>` +
    `<am3d:ambientLight><am3d:clr><a:scrgbClr r="50000" g="50000" b="50000"/></am3d:clr><am3d:illuminance n="500000" d="1000000"/></am3d:ambientLight>` +
    ptLight(100000, 75000, 50000, 9765625, 21959998, 70920001, 16344003) +
    ptLight(40000, 60000, 95000, 12250000, -37964106, 51130435, 57631972) +
    ptLight(86837, 72700, 100000, 3125000, -37739122, 58056624, -34769649) +
    `</am3d:model3d></a:graphicData></a:graphic></p:graphicFrame></mc:Choice>` +
    `<mc:Fallback><p:pic><p:nvPicPr>${cnv}<p:cNvPicPr><a:picLocks noGrp="1" noRot="1" noChangeAspect="1" noMove="1" noResize="1" noEditPoints="1" noAdjustHandles="1" noChangeArrowheads="1" noChangeShapeType="1" noCrop="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>` +
    `<p:blipFill><a:blip r:embed="${imgRel}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>` +
    `<p:spPr><a:xfrm>${off}</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic></mc:Fallback></mc:AlternateContent>`;
}

function guidFor(s) {
  const h = require("crypto").createHash("md5").update(s).digest("hex").toUpperCase();
  return `{${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20, 32)}}`;
}

async function injectModels(zip, slides, glbDir) {
  let ct = await zip.file("[Content_Types].xml").async("string");
  if (!/Extension="glb"/.test(ct)) ct = ct.replace("<Default ", '<Default Extension="glb" ContentType="model/gltf.binary"/><Default ');
  zip.file("[Content_Types].xml", ct);
  const cache = {};
  let n = 0;
  for (let i = 0; i < slides.length; i++) {
    const f = `ppt/slides/slide${i + 1}.xml`, rf = `ppt/slides/_rels/slide${i + 1}.xml.rels`;
    let x = await zip.file(f).async("string");
    let rels = await zip.file(rf).async("string");
    const models = slides[i].els.filter((e) => e.t === "model");
    if (!models.length) continue;
    for (const e of models) {
      const at = x.indexOf(`name="MODEL::${e.id}::`);
      if (at < 0) throw new Error(`model placeholder ${e.id} not found on slide ${i + 1}`);
      const start = x.lastIndexOf("<p:pic>", at), end = x.indexOf("</p:pic>", at) + "</p:pic>".length;
      const pic = x.slice(start, end);
      const spid = /<p:cNvPr id="(\d+)"/.exec(pic)[1];
      const imgRel = /r:embed="([^"]+)"/.exec(pic)[1];
      if (!cache[e.key]) {
        const buf = fs.readFileSync(path.join(glbDir, e.key + ".glb"));
        cache[e.key] = { buf, bounds: glbBounds(buf), animMs: glbAnimMs(buf) };
      }
      n++;
      const target = `model3d${n}.glb`;
      zip.file(`ppt/media/${target}`, cache[e.key].buf);
      const glbRel = `rIdM3d${n}`;
      rels = rels.replace("</Relationships>", `<Relationship Id="${glbRel}" Type="${REL_MODEL}" Target="../media/${target}"/></Relationships>`);
      x = x.slice(0, start) + model3dXml({
        id: spid, name: e.name, x: e.x, y: e.y, size: e.s, rot: e.rot, glbRel, imgRel, bounds: cache[e.key].bounds,
        guid: guidFor(`${i}-${e.id}-${e.name}`), animMs: e.anim === false ? 0 : cache[e.key].animMs,
      }) + x.slice(end);
      // visible animated models get a looping "Scene" effect (see injectTiming)
      if (cache[e.key].animMs && !e.ghost && e.anim !== false)
        (slides[i]._scenes = slides[i]._scenes || []).push({ spid, ms: cache[e.key].animMs });
    }
    // declare am3d on the slide root and mark it ignorable (as PowerPoint does)
    x = x.replace(/<p:sld ([^>]*)>/, (m, attrs) => {
      let a = attrs;
      if (!/xmlns:mc=/.test(a)) a += ' xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"';
      if (!/xmlns:am3d=/.test(a)) a += ` xmlns:am3d="${AM3D}"`;
      if (/mc:Ignorable="/.test(a)) a = a.replace(/mc:Ignorable="([^"]*)"/, (mm, v) => `mc:Ignorable="${v.includes("am3d") ? v : (v + " am3d").trim()}"`);
      else a += ' mc:Ignorable="am3d"';
      return `<p:sld ${a}>`;
    });
    zip.file(f, x);
    zip.file(rf, rels);
  }
}

// ---------- animations ----------
function timingXml(effects, scenes = []) {
  let id = 4;
  const nid = () => ++id;
  const par = effects.map((e, k) => {
    const s = e.spid;
    const set = `<p:set><p:cBhvr><p:cTn id="${nid()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="${s}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>`;
    const fade = `<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="${nid()}" dur="700"/><p:tgtEl><p:spTgt spid="${s}"/></p:tgtEl></p:cBhvr></p:animEffect>`;
    const anim = (attr, from, to) => `<p:anim calcmode="lin" valueType="num"><p:cBhvr><p:cTn id="${nid()}" dur="700" decel="100000" fill="hold"/><p:tgtEl><p:spTgt spid="${s}"/></p:tgtEl><p:attrNameLst><p:attrName>${attr}</p:attrName></p:attrNameLst></p:cBhvr><p:tavLst><p:tav tm="0"><p:val><p:strVal val="${from}"/></p:val></p:tav><p:tav tm="100000"><p:val><p:strVal val="${to}"/></p:val></p:tav></p:tavLst></p:anim>`;
    const ctn = nid();
    const body = set + fade + anim("ppt_x", "#ppt_x", "#ppt_x") + anim("ppt_y", "#ppt_y+0.035", "#ppt_y");
    return `<p:par><p:cTn id="${ctn}" presetID="42" presetClass="entr" presetSubtype="0" fill="hold" grpId="0" nodeType="${k === 0 ? "afterEffect" : "withEffect"}"><p:stCondLst><p:cond delay="${e.delay}"/></p:stCondLst><p:childTnLst>${body}</p:childTnLst></p:cTn></p:par>`;
  }).join("") + scenes.map((sc, k) => {
    // 3D "Scene" playback of the embedded animation, repeated until the end of the slide
    const ctn = nid(), bt = nid();
    const first = !effects.length && k === 0;
    return `<p:par><p:cTn id="${ctn}" presetID="100" presetClass="emph" presetSubtype="1" repeatCount="indefinite" fill="hold" nodeType="${first ? "afterEffect" : "withEffect"}">` +
      `<p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst><p:anim calcmode="lin" valueType="num"><p:cBhvr>` +
      `<p:cTn id="${bt}" dur="${sc.ms}" fill="hold"/><p:tgtEl><p:spTgt spid="${sc.spid}"/></p:tgtEl><p:attrNameLst><p:attrName>embedded1</p:attrName></p:attrNameLst></p:cBhvr>` +
      `<p:tavLst><p:tav tm="0"><p:val><p:fltVal val="0"/></p:val></p:tav><p:tav tm="100000"><p:val><p:fltVal val="1"/></p:val></p:tav></p:tavLst></p:anim>` +
      `</p:childTnLst></p:cTn></p:par>`;
  }).join("");
  const bld = effects.filter((e) => e.sp).map((e) => `<p:bldP spid="${e.spid}" grpId="0" animBg="1"/>`).join("");
  return `<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>` +
    `<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>` +
    `<p:par><p:cTn id="3" fill="hold"><p:stCondLst><p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst><p:childTnLst>` +
    `<p:par><p:cTn id="4" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>${par}</p:childTnLst></p:cTn></p:par>` +
    `</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn>` +
    `<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>` +
    `<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>` +
    `</p:childTnLst></p:cTn></p:par></p:tnLst>${bld ? `<p:bldLst>${bld}</p:bldLst>` : ""}</p:timing>`;
}

const MORPH = `<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"><mc:Choice xmlns:p159="http://schemas.microsoft.com/office/powerpoint/2015/09/main" Requires="p159"><p:transition spd="slow" xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main" p14:dur="1600"><p159:morph option="byObject"/></p:transition></mc:Choice><mc:Fallback><p:transition spd="slow"><p:fade/></p:transition></mc:Fallback></mc:AlternateContent>`;

async function injectTiming(zip, slides) {
  for (let i = 0; i < slides.length; i++) {
    const f = `ppt/slides/slide${i + 1}.xml`;
    let x = await zip.file(f).async("string");
    const groups = [...new Set((slides[i]._anims || []).map((a) => a.ag))].sort((a, b) => a - b);
    const effects = [];
    for (const a of slides[i]._anims || []) {
      const m = new RegExp(`<p:(nvSpPr|nvPicPr|nvCxnSpPr)><p:cNvPr id="(\\d+)" name="${a.name}"`).exec(x);
      if (!m) throw new Error(`anim target ${a.name} not found on slide ${i + 1}`);
      effects.push({ spid: m[2], sp: m[1] === "nvSpPr", delay: 150 + groups.indexOf(a.ag) * 260, ag: a.ag });
    }
    effects.sort((a, b) => a.delay - b.delay);
    const scenes = slides[i]._scenes || [];
    const tail = (i > 0 ? MORPH : "") + (effects.length || scenes.length ? timingXml(effects, scenes) : "");
    if (!x.includes("</p:clrMapOvr>")) throw new Error("no clrMapOvr on slide " + (i + 1));
    x = x.replace("</p:clrMapOvr>", "</p:clrMapOvr>" + tail);
    zip.file(f, x);
  }
}

// pptxgenjs writes a separate copy of an image for every slide; share identical images instead
async function dedupeMedia(zip) {
  const crypto = require("crypto");
  const byHash = {}, alias = {};
  const media = Object.keys(zip.files).filter((f) => /^ppt\/media\/.*\.(png|jpe?g)$/i.test(f)).sort();
  for (const f of media) {
    const h = crypto.createHash("sha1").update(await zip.file(f).async("nodebuffer")).digest("hex");
    if (byHash[h]) { alias[f.slice(10)] = byHash[h].slice(10); zip.remove(f); } else byHash[h] = f;
  }
  for (const rf of Object.keys(zip.files).filter((f) => /^ppt\/(slides|slideLayouts|slideMasters)\/_rels\/.*\.rels$/.test(f))) {
    const x = await zip.file(rf).async("string");
    const y = x.replace(/Target="\.\.\/media\/([^"]+)"/g, (m, t) => `Target="../media/${alias[t] || t}"`);
    if (y !== x) zip.file(rf, y);
  }
}

module.exports = { injectModels, injectTiming, dedupeMedia, glbBounds, glbAnimMs };
