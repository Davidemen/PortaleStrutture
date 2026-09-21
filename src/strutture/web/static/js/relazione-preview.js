// "Anteprima" pane of the report personalisation overlay (WORKBENCH_SPEC §11): renders the REAL
// report DOM (`buildRelazione`, the same function print uses) inside page frames that look like A4
// sheets, scaled to fit the pane width, with a "pagina n di N" indicator. Pagination here is an
// APPROXIMATION the spec explicitly allows ("split on the same break rules as print.css: never
// inside a group header + first row, tables break between rows with a repeated header... must
// never cut a line of text in half") -- it measures the built DOM and only ever splits BETWEEN
// whole top-level sections, or (for one section too tall to fit alone) between its own row-like
// children, so a line of text is never cut mid-element.
import { el, clear } from "./dom.js";
import { buildRelazione } from "./relazione.js";

const PX_PER_MM = 96 / 25.4;
const MARGIN_MM = 18;
const PREVIEW_TABLE_ROW_CAP = 40;
const DEBOUNCE_MS = 300;

function pageSizePx(pagina) {
  const landscape = pagina.orientamento === "orizzontale";
  const wMm = landscape ? 297 : 210;
  const hMm = landscape ? 210 : 297;
  return {
    width: Math.round(wMm * PX_PER_MM),
    height: Math.round(hMm * PX_PER_MM),
    contentWidth: Math.round((wMm - 2 * MARGIN_MM) * PX_PER_MM),
    contentHeight: Math.round((hMm - 2 * MARGIN_MM) * PX_PER_MM),
  };
}

// WORKBENCH_SPEC §11: "very large tables render the first page of rows in the preview with
// '… N righe in stampa'" -- the ACTUAL print document (js/relazione-table.js) still gets every
// row up to the §10 2000-row policy; this only caps what the preview measures/paginates.
function capTablesForPreview(root) {
  for (const wrap of root.querySelectorAll(".r-table-print")) {
    const tbody = wrap.querySelector("tbody");
    if (!tbody) continue;
    const rows = [...tbody.children];
    if (rows.length <= PREVIEW_TABLE_ROW_CAP) continue;
    const total = rows.length;
    rows.slice(PREVIEW_TABLE_ROW_CAP).forEach((row) => row.remove());
    wrap.append(el("p", { class: "rel-preview-note", text: `… ${total} righe in stampa` }));
  }
}

// Splits ONE over-tall `.r-group` section into several same-titled pieces, breaking only between
// its direct row-like children (never inside a row/check/table) -- the header always travels with
// at least its first row (the loop only ever starts a new piece once `bodyHost` already holds one).
function splitSection(section, contentHeight) {
  const titleEl = section.querySelector(":scope > .r-group-title");
  const body = section.querySelector(":scope > .r-group-body");
  const titleHeight = titleEl ? titleEl.getBoundingClientRect().height : 0;
  if (!body) return [{ node: section, height: section.getBoundingClientRect().height }];
  const pieces = [];
  let bodyHost = null;
  let used = 0;
  const startPiece = () => {
    const piece = el("section", { class: "r-group r-group--print" });
    if (titleEl) piece.append(titleEl.cloneNode(true));
    bodyHost = el("div", { class: "r-group-body" });
    piece.append(bodyHost);
    pieces.push({ node: piece, height: titleHeight });
    used = titleHeight;
  };
  startPiece();
  for (const child of [...body.children]) {
    const h = child.getBoundingClientRect().height;
    if (bodyHost.childElementCount > 0 && used + h > contentHeight) startPiece();
    bodyHost.append(child); // moves the already-measured node out of the original body
    used += h;
    pieces[pieces.length - 1].height = used;
  }
  return pieces;
}

function paginate(sourceRoot, contentHeight) {
  const pages = [[]];
  let used = 0;
  const place = (node, h) => {
    if (pages[pages.length - 1].length > 0 && used + h > contentHeight) {
      pages.push([]);
      used = 0;
    }
    pages[pages.length - 1].push(node);
    used += h;
  };
  for (const child of [...sourceRoot.children]) {
    const h = child.getBoundingClientRect().height;
    if (h > contentHeight && child.classList.contains("r-group")) {
      for (const { node, height } of splitSection(child, contentHeight)) place(node, height);
    } else {
      place(child, h);
    }
  }
  return pages;
}

let observer = null;

function wireIndicator(scrollHost, frames, indicatorEl, total) {
  if (observer) observer.disconnect();
  if (frames.length === 0) {
    indicatorEl.textContent = "pagina 0 di 0";
    return;
  }
  indicatorEl.textContent = `pagina 1 di ${total}`;
  observer = new IntersectionObserver(
    (entries) => {
      const top = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (!top) return;
      const index = frames.indexOf(top.target);
      if (index >= 0) indicatorEl.textContent = `pagina ${index + 1} di ${total}`;
    },
    { root: scrollHost, threshold: [0.5] },
  );
  frames.forEach((frame) => observer.observe(frame));
}

// `session = {tool, report, options}` -- `options` already fully resolved WITH `cartiglio` merged
// in (the overlay's job, so this module stays a plain renderer with no cartiglio/persistence
// knowledge of its own).
function renderNow({ pagesHost, indicatorEl, scrollHost }, session) {
  clear(pagesHost);
  const pagina = session.options.pagina;
  const { width, height, contentWidth, contentHeight } = pageSizePx(pagina);
  const compact = pagina.corpo === "compatto";

  const measure = el("div", { class: "rel-measure" });
  measure.style.setProperty("position", "fixed");
  measure.style.setProperty("left", "-10000px");
  measure.style.setProperty("top", "0");
  measure.style.setProperty("width", `${contentWidth}px`);
  if (compact) measure.classList.add("rel-page--compact");
  document.body.append(measure);
  // "v" (never "p", the print root's own prefix, review finding 7): this preview and the actual
  // print document can both be in the DOM at once -- opening the overlay builds this preview, and
  // "Stampa / Salva PDF" then builds the print root WITHOUT closing the overlay first (it prints,
  // then the user still sees the dialog) -- same-id `url(#...)` sketch references would otherwise
  // collide between the two.
  buildRelazione(
    measure,
    { tool: session.tool, report: session.report, outputNodes: session.tool.outputNodes, fields: session.tool.fields },
    session.options,
    "v",
  );
  capTablesForPreview(measure);
  const pages = paginate(measure, contentHeight);
  measure.remove();

  const paneWidth = pagesHost.clientWidth || width;
  const scale = Math.min(1, paneWidth / width);
  const frames = pages.map((nodes) => {
    const page = el("div", { class: `rel-page${compact ? " rel-page--compact" : ""}` });
    page.style.setProperty("width", `${width}px`);
    page.style.setProperty("height", `${height}px`);
    page.style.setProperty("transform", `scale(${scale})`);
    const content = el("div", { class: "rel-page-content" });
    content.style.setProperty("width", `${contentWidth}px`);
    for (const node of nodes) content.append(node);
    page.append(content);
    const frame = el("div", { class: "rel-page-frame" });
    frame.style.setProperty("width", `${paneWidth}px`);
    frame.style.setProperty("height", `${height * scale}px`);
    frame.append(page);
    pagesHost.append(frame);
    return frame;
  });
  wireIndicator(scrollHost, frames, indicatorEl, pages.length || 1);
}

let timer = null;

// Debounced (WORKBENCH_SPEC §11: "updates within 300 ms of an option change"); `immediate` skips
// the debounce for the overlay's own first paint on open.
export function schedulePreviewUpdate(elements, session, { immediate = false } = {}) {
  if (timer) {
    clearTimeout(timer);
    timer = null;
  }
  if (immediate) {
    renderNow(elements, session);
    return;
  }
  timer = setTimeout(() => renderNow(elements, session), DEBOUNCE_MS);
}
