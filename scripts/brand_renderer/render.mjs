import { readFileSync, writeFileSync } from "node:fs";
import { Resvg } from "@resvg/resvg-js";

const [svgPath, outPath, sizeStr] = process.argv.slice(2);
if (!svgPath || !outPath || !sizeStr) {
  console.error("usage: node render.mjs <svg> <png-out> <size>");
  process.exit(2);
}

const size = Number(sizeStr);
const svg = readFileSync(svgPath);
const resvg = new Resvg(svg, {
  fitTo: { mode: "width", value: size },
  background: "transparent",
});
const png = resvg.render().asPng();
writeFileSync(outPath, png);
