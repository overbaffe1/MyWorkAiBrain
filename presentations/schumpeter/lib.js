// Tiny layout layer: every slide is described once, then rendered
// (1) into a native, editable .pptx via pptxgenjs and
// (2) into HTML for pixel previews (headless Chromium).
const fs = require("fs");
const path = require("path");

const W = 13.333, H = 7.5;
const FONTS = { head: "Georgia", body: "Arial" };

class Slide {
  constructor(opts) {
    this.els = [];
    this.notes = opts.notes || "";
    this.bg = opts.bg || null;
  }
  img(src, o) { this.els.push({ t: "img", src, ...o }); return this; }
  rect(o) { this.els.push({ t: "rect", ...o }); return this; }
  line(o) { this.els.push({ t: "line", ...o }); return this; }
  poly(points, o) { this.els.push({ t: "poly", points, ...o }); return this; }
  // native PowerPoint 3D model (square frame of side o.s); raster/glb are attached at build time
  model(key, o) { const e = { t: "model", key, rot: [0, 0, 0], ...o }; this.els.push(e); return e; }
  text(runs, o) {
    if (typeof runs === "string") runs = [{ text: runs }];
    this.els.push({ t: "text", runs, ...o });
    return this;
  }
}

// ---------- pptx backend ----------
function runOpts(r, o) {
  const ro = r.options || {};
  return {
    fontFace: FONTS[ro.font || o.font || "body"],
    fontSize: ro.size || o.size || 14,
    color: ro.color || o.color || "FFFFFF",
    bold: ro.bold ?? o.bold ?? false,
    italic: ro.italic ?? o.italic ?? false,
    charSpacing: ro.charSpacing ?? o.charSpacing,
    breakLine: ro.breakLine,
    bullet: ro.bullet ?? o.bullet,
    paraSpaceAfter: ro.paraSpaceAfter ?? o.paraSpaceAfter,
    lineSpacingMultiple: ro.lineSpacingMultiple ?? o.lineSpacingMultiple ?? 1.0,
    align: ro.align || o.align || "left",
  };
}

function toPptx(pres, slides) {
  slides.forEach((s, si) => {
    const ps = pres.addSlide();
    ps.background = { color: s.bg || "080D1A" };
    s._anims = [];
    let k = 0;
    for (const e of s.els) {
      const base = { x: e.x, y: e.y, w: e.w, h: e.h };
      if (e.name) base.objectName = e.name;
      if (e.ag !== undefined) {
        // entrance-animated element: give it a unique, findable name
        base.objectName = e.name || `fx${si + 1}_${e.ag}_${k++}`;
        s._anims.push({ name: base.objectName, ag: e.ag, fx: e.fx || "up" });
      }
      if (e.t === "model") {
        ps.addImage({ path: e.raster, x: e.x, y: e.y, w: e.s, h: e.s, objectName: `MODEL::${e.id}::${e.name}` });
      } else if (e.t === "img") {
        ps.addImage({ path: e.src, ...base, transparency: e.transparency, rounding: e.rounding });
      } else if (e.t === "rect") {
        const shape = e.shape === "ellipse" ? pres.ShapeType.ellipse
          : e.radius ? pres.ShapeType.roundRect
          : e.shape === "tri" ? pres.ShapeType.triangle
          : pres.ShapeType.rect;
        const so = { ...base };
        so.fill = e.fill ? { color: e.fill, transparency: e.fillT || 0 } : { type: "none" };
        so.line = e.line ? { color: e.line, width: e.lineW || 0.75, transparency: e.lineT || 0, dashType: e.dash } : { type: "none" };
        if (e.radius) so.rectRadius = e.radius;
        if (e.rotate) so.rotate = e.rotate;
        if (e.shadow) so.shadow = { type: "outer", blur: 18, offset: 6, angle: 90, color: "000000", opacity: 0.45 };
        ps.addShape(shape, so);
      } else if (e.t === "line") {
        ps.addShape(pres.ShapeType.line, {
          x: Math.min(e.x1, e.x2), y: Math.min(e.y1, e.y2),
          w: Math.max(Math.abs(e.x2 - e.x1), 0.0001), h: Math.max(Math.abs(e.y2 - e.y1), 0.0001),
          flipV: (e.y2 < e.y1) !== (e.x2 < e.x1) && e.x1 !== e.x2 && e.y1 !== e.y2,
          line: { color: e.color, width: e.width || 1, transparency: e.lineT || 0, dashType: e.dash },
          objectName: base.objectName,
        });
      } else if (e.t === "poly") {
        const xs = e.points.map((p) => p[0]), ys = e.points.map((p) => p[1]);
        const x0 = Math.min(...xs), y0 = Math.min(...ys);
        const w = Math.max(...xs) - x0, h = Math.max(...ys) - y0;
        ps.addShape(pres.ShapeType.custGeom, {
          x: x0, y: y0, w, h,
          points: e.points.map((p, i) => ({ x: p[0] - x0, y: p[1] - y0, ...(i === 0 ? { moveTo: true } : {}) })),
          line: { color: e.color, width: e.width || 2, dashType: e.dash, transparency: e.lineT || 0 },
          fill: { type: "none" },
          objectName: base.objectName,
        });
      } else if (e.t === "text") {
        const runs = e.runs.map((r) => ({ text: r.text, options: runOpts(r, e) }));
        ps.addText(runs, {
          ...base,
          margin: [0, 0, 0, 0],
          valign: e.valign || "top",
          align: e.align || "left",
          fit: "none",
          wrap: true,
          lineSpacingMultiple: e.lineSpacingMultiple || 1.0,
          fill: e.fill ? { color: e.fill, transparency: e.fillT || 0 } : undefined,
        });
      }
    }
    if (s.notes) ps.addNotes(s.notes);
  });
}

// ---------- html backend ----------
const PX = 144; // px per inch -> 1920x1080
const hex = (c, t = 0) => {
  const n = parseInt(c, 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${1 - t / 100})`;
};
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");

function htmlText(e) {
  // group runs into paragraphs (pptx semantics: breakLine ends a paragraph)
  const paras = [[]];
  e.runs.forEach((r) => {
    paras[paras.length - 1].push(r);
    if (r.options && r.options.breakLine) paras.push([]);
  });
  if (!paras[paras.length - 1].length) paras.pop();
  const ps = paras.map((p) => {
    const o0 = runOpts(p[0], e);
    const lh = 1.17 * (o0.lineSpacingMultiple || 1);
    const bullet = o0.bullet;
    const style = [
      `text-align:${o0.align}`,
      `line-height:${lh}`,
      `margin:0 0 ${(o0.paraSpaceAfter || 0) * 2}px 0`,
      bullet ? `padding-left:${o0.fontSize * 2 * 1.1}px;text-indent:-${o0.fontSize * 2 * 1.1}px` : "",
    ].join(";");
    const spans = p.map((r) => {
      const o = runOpts(r, e);
      const fam = o.fontFace === "Georgia" ? "'NotoSerifPreview', Georgia, serif" : "'ArimoPreview', Arial, sans-serif";
      return `<span style="font-family:${fam};font-size:${o.fontSize * 2}px;color:${hex(o.color)};font-weight:${o.bold ? 700 : 400};font-style:${o.italic ? "italic" : "normal"};letter-spacing:${(o.charSpacing || 0) * 2}px">${esc(r.text)}</span>`;
    }).join("");
    const b = bullet ? `<span style="display:inline-block;width:${o0.fontSize * 2 * 1.1}px;text-indent:0;color:${hex(o0.color)};font-size:${o0.fontSize * 2}px">•</span>` : "";
    return `<p style="${style}">${b}${spans}</p>`;
  }).join("");
  const jc = { top: "flex-start", middle: "center", bottom: "flex-end" }[e.valign || "top"];
  const bg = e.fill ? `background:${hex(e.fill, e.fillT || 0)};` : "";
  return `<div class="tb" style="left:${e.x * PX}px;top:${e.y * PX}px;width:${e.w * PX}px;height:${e.h * PX}px;justify-content:${jc};${bg}${process.env.DEBUG_BOXES ? "outline:1px dashed rgba(255,0,0,.6);" : ""}">${ps}</div>`;
}

function toHtml(slides, assetsDir, fontsDir) {
  const font = (name, file, w, st) => `@font-face{font-family:'${name}';src:url('file://${fontsDir}/${file}');font-weight:${w};font-style:${st}}`;
  const faces = [];
  for (const sub of ["latin", "cyrillic"]) {
    faces.push(font("ArimoPreview", `arimo/files/arimo-${sub}-400-normal.woff2`, 400, "normal"));
    faces.push(font("ArimoPreview", `arimo/files/arimo-${sub}-700-normal.woff2`, 700, "normal"));
    faces.push(font("ArimoPreview", `arimo/files/arimo-${sub}-400-italic.woff2`, 400, "italic"));
    faces.push(font("NotoSerifPreview", `noto-serif/files/noto-serif-${sub}-400-normal.woff2`, 400, "normal"));
    faces.push(font("NotoSerifPreview", `noto-serif/files/noto-serif-${sub}-700-normal.woff2`, 700, "normal"));
    faces.push(font("NotoSerifPreview", `noto-serif/files/noto-serif-${sub}-400-italic.woff2`, 400, "italic"));
  }
  return slides.map((s) => {
    const parts = s.els.map((e) => {
      if (e.t === "model") {
        if (e.ghost) return "";
        return `<img src="file://${path.resolve(e.raster)}" style="position:absolute;left:${e.x * PX}px;top:${e.y * PX}px;width:${e.s * PX}px;height:${e.s * PX}px">`;
      }
      if (e.t === "img") {
        const r = e.rounding ? "border-radius:50%;" : "";
        return `<img src="file://${path.resolve(e.src)}" style="position:absolute;left:${e.x * PX}px;top:${e.y * PX}px;width:${e.w * PX}px;height:${e.h * PX}px;object-fit:fill;opacity:${1 - (e.transparency || 0) / 100};${r}">`;
      }
      if (e.t === "rect") {
        if (e.shape === "tri") {
          return `<svg style="position:absolute;left:${e.x * PX}px;top:${e.y * PX}px;overflow:visible" width="${e.w * PX}" height="${e.h * PX}"><polygon points="${e.w * PX / 2},0 ${e.w * PX},${e.h * PX} 0,${e.h * PX}" fill="${hex(e.fill, e.fillT || 0)}" transform="rotate(${e.rotate || 0} ${e.w * PX / 2} ${e.h * PX / 2})"/></svg>`;
        }
        const br = e.shape === "ellipse" ? "50%" : e.radius ? `${e.radius * PX}px` : "0";
        const bd = e.line ? `border:${(e.lineW || 0.75) * 2}px ${e.dash ? "dashed" : "solid"} ${hex(e.line, e.lineT || 0)};` : "";
        const sh = e.shadow ? "box-shadow:0 12px 36px rgba(0,0,0,.45);" : "";
        return `<div style="position:absolute;box-sizing:border-box;left:${e.x * PX}px;top:${e.y * PX}px;width:${e.w * PX}px;height:${e.h * PX}px;background:${e.fill ? hex(e.fill, e.fillT || 0) : "transparent"};${bd}border-radius:${br};${sh}transform:rotate(${e.rotate || 0}deg)"></div>`;
      }
      if (e.t === "line") {
        const da = e.dash ? `stroke-dasharray="${(e.width || 1) * 6} ${(e.width || 1) * 5}"` : "";
        return `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1"><line x1="${e.x1 * PX}" y1="${e.y1 * PX}" x2="${e.x2 * PX}" y2="${e.y2 * PX}" stroke="${hex(e.color, e.lineT || 0)}" stroke-width="${(e.width || 1) * 2}" ${da}/></svg>`;
      }
      if (e.t === "poly") {
        const d = e.points.map((p, i) => `${i ? "L" : "M"}${p[0] * PX},${p[1] * PX}`).join(" ");
        const da = e.dash ? `stroke-dasharray="${(e.width || 2) * 5} ${(e.width || 2) * 4}"` : "";
        return `<svg style="position:absolute;left:0;top:0;overflow:visible" width="1" height="1"><path d="${d}" fill="none" stroke="${hex(e.color, e.lineT || 0)}" stroke-width="${(e.width || 2) * 2}" stroke-linejoin="round" ${da}/></svg>`;
      }
      if (e.t === "text") return htmlText(e);
      return "";
    }).join("\n");
    return `<!doctype html><html><head><meta charset="utf-8"><style>${faces.join("")}
      html,body{margin:0;padding:0;background:#080D1A}
      .s{position:relative;width:1920px;height:1080px;overflow:hidden;background:#080D1A}
      .tb{position:absolute;display:flex;flex-direction:column;box-sizing:border-box;overflow:visible}
      p{white-space:pre-wrap}
    </style></head><body><div class="s">${parts}</div></body></html>`;
  });
}

module.exports = { Slide, toPptx, toHtml, W, H };
