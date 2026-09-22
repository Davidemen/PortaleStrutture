// Characterisation test for the WORKBENCH_SPEC.md §22 `sketch-fit.js` split (module cap):
// `fitVista`/`applyDimensionOffsets`/`uniformScale` are moved verbatim into three files with no
// behaviour change, so every tool example's sketch views must fit EXACTLY as they did before the
// split -- `tests/fixtures/sketch_fit_expected.json` was recorded from the pre-split file by
// `scripts/gen_sketch_fit_expected.mjs`, `tests/fixtures/sketch_viste.json` by
// `scripts/dump_sketch_viste.py`. Written and passing BEFORE the file is split; kept afterwards
// as a permanent regression guard for the fitting pipeline.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fitVista, uniformScale } from "../../src/strutture/web/static/js/sketch-fit.js";
import { applyDimensionOffsets } from "../../src/strutture/web/static/js/sketch-dimensions.js";

const BOX_PX = { width: 340, height: 220 };
const viste = JSON.parse(readFileSync(new URL("../fixtures/sketch_viste.json", import.meta.url), "utf-8"));
const expected = JSON.parse(readFileSync(new URL("../fixtures/sketch_fit_expected.json", import.meta.url), "utf-8"));
// Both sides go through a JSON round trip before comparing: the recorded fixture is itself JSON,
// and `-0`/`0` (both mean "zero", never a distinguishable renderer outcome) already collapse to
// `0` on that trip -- comparing the live value directly against the fixture would otherwise fail
// on that distinction alone, which is not a real behaviour difference.
const normalise = (value) => JSON.parse(JSON.stringify(value));

test("fitVista + applyDimensionOffsets match the pre-split recording for every tool example", () => {
  const keys = Object.keys(viste);
  assert.ok(keys.length > 0, "fixture must not be empty");
  assert.deepEqual(keys.sort(), Object.keys(expected).sort());
  for (const key of keys) {
    const views = viste[key];
    const expectedViews = expected[key];
    assert.equal(views.length, expectedViews.length, `${key}: view count`);
    views.forEach((vista, i) => {
      const view = fitVista(vista, { boxPx: BOX_PX });
      const wanted = expectedViews[i];
      assert.deepEqual(normalise(view), wanted.view, `${key}[${i}]: fitVista`);
      if (view) {
        const scale = uniformScale(view, BOX_PX);
        const forme = applyDimensionOffsets(vista.forme, scale, view.side);
        assert.deepEqual(normalise(forme), wanted.forme, `${key}[${i}]: applyDimensionOffsets`);
      }
    });
  }
});
