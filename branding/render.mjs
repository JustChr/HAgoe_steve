import { Resvg } from "@resvg/resvg-js";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";

function render(svgPath, outPath, width) {
  const svg = readFileSync(svgPath, "utf8");
  const r = new Resvg(svg, { fitTo: { mode: "width", value: width } });
  writeFileSync(outPath, r.render().asPng());
  console.log("rendered", outPath, `(${width}px wide)`);
}

// Render an SVG string trimmed to its non-transparent bounds, at the given output width.
function renderTrimmed(svgPath, outPath, outWidth) {
  const svg = readFileSync(svgPath, "utf8");
  const vb = svg.match(/viewBox="([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+)"/).slice(1).map(Number);
  const [, , vbw, vbh] = vb;
  // Pass 1: render at high res, find the alpha bounding box.
  const probeW = 1600;
  const img = new Resvg(svg, { fitTo: { mode: "width", value: probeW } }).render();
  const { width: pw, height: ph, pixels } = img;
  let minX = pw, minY = ph, maxX = 0, maxY = 0;
  for (let y = 0; y < ph; y++) {
    for (let x = 0; x < pw; x++) {
      if (pixels[(y * pw + x) * 4 + 3] > 8) {
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
    }
  }
  // Convert pixel bbox back to SVG user units.
  const s = vbw / pw; // user units per pixel
  const nx = minX * s, ny = minY * s;
  const nw = (maxX - minX + 1) * s, nh = (maxY - minY + 1) * s;
  const trimmed = svg
    .replace(/viewBox="[^"]*"/, `viewBox="${nx} ${ny} ${nw} ${nh}"`)
    .replace(/<svg([^>]*?)width="[^"]*"/, "<svg$1")
    .replace(/<svg([^>]*?)height="[^"]*"/, "<svg$1");
  const outH = Math.round((outWidth * nh) / nw);
  const r = new Resvg(trimmed, { fitTo: { mode: "width", value: outWidth } });
  writeFileSync(outPath, r.render().asPng());
  console.log("rendered", outPath, `(${outWidth}x${outH}, trimmed)`);
}

// Concept previews (all options, with their display margins).
for (const name of ["icon-option-1", "icon-option-2", "icon-option-3", "icon-option-4"]) {
  render(`${name}.svg`, `${name}.png`, 512);
  render(`${name}.svg`, `${name}-128.png`, 128);
}
render("logo-lockup.svg", "logo-lockup.png", 840);

// HACS / home-assistant brands deliverables — Option 3, trimmed per brands CI rules.
const dir = "hacs/custom_integrations/goe_steve";
mkdirSync(dir, { recursive: true });
render("icon-brands.svg", `${dir}/icon.png`, 256);
render("icon-brands.svg", `${dir}/icon@2x.png`, 512);
renderTrimmed("logo-lockup.svg", `${dir}/logo.png`, 512);
renderTrimmed("logo-lockup.svg", `${dir}/logo@2x.png`, 1024);
