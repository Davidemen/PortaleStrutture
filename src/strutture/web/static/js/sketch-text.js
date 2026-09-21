// Text-width ESTIMATE for the sketch fitter (WORKBENCH_SPEC #5, finding C3): "include a
// text-width estimate (0.55em per char at 11.5px) in the margin computation" so a long
// dimension/label/arrow string is never clipped at the figure's edge. Split out of sketch-fit.js
// (module-length guideline) -- pure, no DOM, unit-testable on its own.
export const CHAR_WIDTH_EM = 0.55;
export const TEXT_PX = 11.5; // constant on-screen size regardless of model scale (sketch-shapes.js)
export const LABEL_GAP_PX = 6; // clearance beyond the raw text-width estimate (tick length + breathing room)

export function textWidthPx(text) {
  return String(text || "").length * CHAR_WIDTH_EM * TEXT_PX;
}

// Longest label-ish string in a Vista's shapes (dimension/label/arrow text, diagram ordinate
// labels) -- the single number `fitVista`'s margin is sized from.
export function longestTextPx(forme) {
  let max = 0;
  for (const shape of forme) {
    const texts = [];
    if (shape.kind === "dimension" && shape.testo) texts.push(shape.testo);
    if (shape.kind === "label") texts.push([shape.simbolo, shape.testo].filter(Boolean).join(" = "));
    if (shape.kind === "arrow" && shape.testo) texts.push(shape.testo);
    if (shape.kind === "diagram" && Array.isArray(shape.etichette)) texts.push(...shape.etichette.filter(Boolean));
    for (const t of texts) max = Math.max(max, textWidthPx(t));
  }
  return max;
}
