// Minimal deck: one slide with the animated box as a native PowerPoint 3D model (auto-playing "Scene").
//   1) LD_LIBRARY_PATH=/tmp/bstub python3 train-ai/examples/box_with_lid.py          -> out/box.glb
//   2) node train-ai/examples/mini_deck.js                                            -> out/demo.pptx
// Step 2 renders the raster (PNG fallback / poster) with render.py, lets pptxgenjs place it as a placeholder picture,
// then pptx3d.js swaps the picture for am3d:model3d + embedAnim + Scene timing.
const path = require("path");
const fs = require("fs");
const { execSync } = require("child_process");
const SCH = path.join(__dirname, "..", "..", "presentations", "schumpeter");
const req = require("module").createRequire(path.join(SCH, "package.json"));
const { Slide, toPptx } = require(path.join(SCH, "lib"));
const { injectModels, injectTiming, dedupeMedia } = require(path.join(SCH, "pptx3d"));
const OUT = path.join(__dirname, "out");

async function main() {
  const s = new Slide({ notes: "Шкатулка открывается сама — это скелетная анимация внутри glb." });
  s.bg = "0E080A";
  s.text("Шкатулка с секретом", { x: 0.7, y: 0.8, w: 6, h: 0.9, font: "head", size: 36, color: "F5EFE6" });
  s.text("Крышка открывается, монета подпрыгивает — анимация живёт внутри 3D-модели.",
    { x: 0.7, y: 1.8, w: 5.6, h: 1.0, size: 16, color: "BBAEA6", ag: 1 });
  const e = s.model("box", { x: 6.6, y: 0.9, s: 5.6, rot: [18, -28, 0], name: "!!m-box" });

  // raster for the model (same camera as PowerPoint), rendered from the exported .glb
  e.id = "m1";
  e.raster = path.join(OUT, "box.png");
  const jf = path.join(OUT, "_jobs.json");
  fs.writeFileSync(jf, JSON.stringify([{ key: "box", rot: e.rot, px: 700, out: e.raster }]));
  execSync(`python3 ${path.join(SCH, "models", "render.py")} ${jf}`, {
    stdio: ["ignore", "ignore", "inherit"],
    env: { ...process.env, GLB_DIR: OUT, SAMPLES: "32", LD_LIBRARY_PATH: "/tmp/bstub:" + (process.env.LD_LIBRARY_PATH || "") },
  });
  fs.unlinkSync(jf);

  const pptxgen = req("pptxgenjs"), JSZip = req("jszip");
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  toPptx(pres, [s]);
  const zip = await JSZip.loadAsync(await pres.write({ outputType: "nodebuffer" }));
  await injectModels(zip, [s], OUT);   // picture "MODEL::m1::!!m-box" -> 3D model (+ embedAnim, s._scenes)
  await injectTiming(zip, [s]);        // fade-in for ag:1 text + looping 3D Scene for the model
  await dedupeMedia(zip);
  const out = path.join(OUT, "demo.pptx");
  fs.writeFileSync(out, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
  console.log("wrote", out);
}
main().catch((err) => { console.error(err); process.exit(1); });
