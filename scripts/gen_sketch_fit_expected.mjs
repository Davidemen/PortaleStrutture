// Dev tool (not shipped): records fitVista/applyDimensionOffsets/uniformScale outputs for every
// fixture view from the CURRENT sketch-fit.js, before the WORKBENCH_SPEC.md §22 module split.
// Run once, before moving any code; tests/e2e/sketch_fit.test.mjs then guards that the split
// never changes these numbers. Rerun only if the fitting algorithm itself intentionally changes.
import { readFileSync, writeFileSync } from "node:fs";
import { fitVista, uniformScale } from "../src/strutture/web/static/js/sketch-fit.js";
import { applyDimensionOffsets } from "../src/strutture/web/static/js/sketch-dimensions.js";

const BOX_PX = { width: 340, height: 220 };
const viste = JSON.parse(readFileSync(new URL("../tests/fixtures/sketch_viste.json", import.meta.url), "utf-8"));

const expected = {};
for (const [key, views] of Object.entries(viste)) {
  expected[key] = views.map((vista) => {
    const view = fitVista(vista, { boxPx: BOX_PX });
    if (!view) return { view: null, forme: null };
    const scale = uniformScale(view, BOX_PX);
    const forme = applyDimensionOffsets(vista.forme, scale, view.side);
    return { view, forme };
  });
}

writeFileSync(
  new URL("../tests/fixtures/sketch_fit_expected.json", import.meta.url),
  JSON.stringify(expected, null, 1) + "\n",
  "utf-8",
);
console.log(`wrote ${Object.keys(expected).length} entries`);
