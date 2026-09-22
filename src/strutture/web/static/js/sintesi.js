// The sticky Sintesi block (WORKBENCH_SPEC #4/#8): verdict in words + icon, eta max with the
// governing check's name/clause + utilisation bar, the <=3 highlighted outputs as large figures,
// a warnings count that opens the warnings panel, and the sketch views (WORKBENCH_SPEC finding B:
// a two-column layout at >=640px of the Sintesi's own width -- left `.r-si-main` = verdict/eta/
// highlights/warnings, right `.r-si-side` = the sketches, each filling its cell; below that width
// a single column with the sketch FIRST, per finding B/K). Also fills the mobile #bottom-bar
// (verdict + eta max, tap -> Risultati). Tools with no checks show the highlights only (no verdict
// words, no eta line -- there is no governing check).
import { el, clear } from "./dom.js";
import { readPath } from "./output-schema.js";
import { valueNode, formatValue, formatCopyValue, formatUtilisation, formatCount, formatUnit, sentenceCase } from "./format.js";
import { symbolNode } from "./symbols.js";
import { checkMark, governingCheck, effectiveUtilisation, buildBar, displayCheckName } from "./verdict.js";
import { createCopyStatus, wireValueCopy } from "./results-toolbar.js";
import { renderChart } from "./chart.js";
import { buildChartArgs } from "./results-rows.js";

const EXPAND_BELOW_PX = 40; // hysteresis: re-expand only back near the top
const COLLAPSE_AFTER_PX = 200;

function verdictWord(checks) {
  const failing = checks.filter((check) => !check.passed).length;
  return failing === 0 ? "Tutte le verifiche soddisfatte" : `${failing} verifiche non soddisfatte`;
}

// The verdict/eta text is what `#sintesi`'s aria-live="polite" (shell, index.html) should
// announce -- WORKBENCH_SPEC #2: "announces only when the verdict or the governing check
// changes... not on every keystroke". `renderSintesi` rebuilds the whole block on every run
// (simplest correct implementation for a small, cheap subtree), so this key + the aria-live
// on/off toggle around unchanged renders is what suppresses the repeat announcement instead.
function announceKeyFor(checks) {
  if (checks.length === 0) return "";
  const governing = governingCheck(checks);
  if (!governing) return "";
  const ratio = effectiveUtilisation(governing);
  return `${verdictWord(checks)}|${governing.name}|${ratio === null ? "" : formatUtilisation(ratio)}`;
}

function buildVerdictLine(checks) {
  const ok = checks.every((check) => check.passed);
  const line = el("div", { class: "r-si-verdict" });
  line.append(el("span", { class: "r-icon-wrap" }, [checkMark(ok)]));
  line.append(el("span", { class: `r-si-verdict-word ${ok ? "r-verdict-word--ok" : "r-verdict-word--ko"}`, text: verdictWord(checks) }));
  return line;
}

function buildEtaMax(checks, copyCtx) {
  const governing = governingCheck(checks);
  if (!governing) return null;
  const ratio = effectiveUtilisation(governing);
  const wrap = el("div", { class: "r-si-eta" });
  const value = el("span", { class: "r-si-eta-value", "data-check": governing.name }, [symbolNode("η_max")]);
  if (ratio !== null) {
    const text = ` ${formatUtilisation(ratio)}`;
    value.append(document.createTextNode(text));
    if (copyCtx) wireValueCopy(value, formatCopyValue(ratio), copyCtx.announce);
  }
  wrap.append(value);
  const governingName = displayCheckName(governing.name);
  wrap.append(el("span", { class: "r-si-eta-name", text: `${governingName}${governing.clause ? ` — ${governing.clause}` : ""}` }));
  if (ratio !== null) wrap.append(buildBar(ratio, governing.passed));
  return wrap;
}

// Review finding 19: a highlight with no `symbol` hint used to print its plain-Italian description
// in the SAME class as the mathematical-italic STIX symbol (`.r-si-figure-symbol`) -- a description
// is UI text, not a formula, and reads wrong set in italic serif. A distinct class instead (Barlow,
// upright, graphite, 2-line clamp so a long description never balloons the figure); a bare unit
// hint of "-" (JSON-schema "no unit", not a real unit string) is never shown as if it were one.
function buildHighlightFigure({ node, value }, copyCtx) {
  const fig = el("div", { class: "r-si-figure", "data-field": node.path });
  const lead = node.symbol
    ? el("div", { class: "r-si-figure-symbol" }, [symbolNode(node.symbol)])
    : el("div", { class: "r-si-figure-label", text: sentenceCase(node.label) });
  fig.append(lead);
  const valueEl = el("div", { class: "r-si-figure-value" }, [valueNode(value, node)]);
  const { title } = formatValue(value, node);
  if (title) valueEl.title = title;
  if (copyCtx) wireValueCopy(valueEl, formatCopyValue(value), copyCtx.announce);
  fig.append(valueEl);
  if (node.unit && node.unit !== "-") fig.append(el("div", { class: "r-si-figure-unit", text: formatUnit(node.unit) }));
  return fig;
}

function buildWarningsButton(count) {
  const btn = el("button", { type: "button", class: "r-si-warnings", text: formatCount(count, "avviso", "avvisi") });
  btn.addEventListener("click", () => {
    const panel = document.getElementById("r-warnings-panel");
    if (!panel) return;
    panel.open = true;
    panel.scrollIntoView({ block: "start" });
  });
  return btn;
}

// `token` guards against a slow dynamic import resolving after a NEWER renderSintesi() call
// already cleared/rebuilt `root` (live calculation can fire several runs in a row).
async function appendSketches(container, sketchPairs, previousData, token, campi) {
  if (sketchPairs.length === 0) return;
  let renderSketch;
  try {
    ({ renderSketch } = await import("./sketch.js"));
  } catch (error) {
    return; // sketch package not present yet / failed to load: Sintesi still works without it
  }
  if (typeof renderSketch !== "function" || token !== renderToken) return;
  const wrap = el("div", { class: "r-si-sketches" });
  container.append(wrap);
  for (const { node, value } of sketchPairs) {
    if (!value) continue;
    const holder = el("div", { class: "r-si-sketch" });
    wrap.append(holder);
    const previous = previousData ? readPath(previousData, node.path) : undefined;
    try {
      renderSketch(holder, value, { previous, campi });
    } catch (error) {
      holder.remove(); // a broken sketch must never break the Sintesi
    }
  }
}

let renderToken = 0;
const lastAnnounceKey = new WeakMap();

// `options` (WORKBENCH_SPEC §10, print reuse): `{copy = true, sketches = true, warnings = true}`
// -- print calls this with all three off (its own Schizzo section already shows every sketch view
// full-size earlier in the document, its own Avvisi section shows every warning in full later, and
// nothing in a printed report is click-to-copy).
// Orchestrator finding: no checks, no `highlight` outputs and no sketch (e.g. sisma-spettro,
// vento-pressione) used to leave the Sintesi block visibly blank. `chartFallback` (results.js/
// relazione.js -- only ever computed in exactly this situation) is the tool's own FIRST charted
// `rows` output; shown here as a preview (its full group + accessible table still render normally
// below, same "summary here, detail below" relationship the verdict/eta line already has with the
// full Verifiche list). Lacking even that, a one-line "Calcolo eseguito" replaces the blank space.
function buildEmptyFallback(chartFallback) {
  if (chartFallback) {
    const figure = el("figure", { class: "r-chart" });
    const hasChart = renderChart(figure, buildChartArgs(chartFallback.node, chartFallback.rows));
    if (!hasChart) return el("p", { class: "r-si-empty", text: "Calcolo eseguito" });
    const { chart, label } = chartFallback.node;
    const axes = chart.y_label && chart.x_label ? `${chart.y_label} in funzione di ${chart.x_label}` : label;
    figure.append(el("figcaption", { text: axes }));
    return figure;
  }
  return el("p", { class: "r-si-empty", text: "Calcolo eseguito" });
}

export function renderSintesi(root, { report, highlightPairs = [], sketchPairs = [], chartFallback = null, previousData, options = {}, campi = null } = {}) {
  const showCopy = options.copy !== false;
  const showSketches = options.sketches !== false;
  const showWarnings = options.warnings !== false;
  const checks = (report && report.checks) || [];
  const warnings = (report && report.warnings) || [];

  const announceKey = announceKeyFor(checks);
  const previousKey = lastAnnounceKey.get(root);
  const suppressAnnounce = previousKey !== undefined && previousKey === announceKey;
  if (suppressAnnounce) root.setAttribute("aria-live", "off");
  lastAnnounceKey.set(root, announceKey);

  clear(root);
  const token = ++renderToken;
  // Visibility is pure CSS, off `#sintesi[aria-busy="true"]` (results.js toggles that attribute
  // on run-start/run-result) -- the element itself is rebuilt every render like everything else
  // here, but that never matters because nothing about its state lives on the node.
  root.append(el("div", { class: "r-si-progress", "aria-hidden": "true" }));
  const copyCtx = showCopy ? createCopyStatus(root) : null;

  // Two-column layout (finding B): `.r-si-main` (verdict/eta/highlights/warnings) + `.r-si-side`
  // (sketches). CSS alone decides column vs. single-column-sketch-first via a container query on
  // `#sintesi`'s own width -- `.r-si-side:empty` collapses away when a tool has no sketch output.
  const layout = el("div", { class: "r-si-layout" });
  const main = el("div", { class: "r-si-main" });
  const side = el("div", { class: "r-si-side" });
  layout.append(main, side);
  root.append(layout);

  if (checks.length > 0) {
    main.append(buildVerdictLine(checks));
    const eta = buildEtaMax(checks, copyCtx);
    if (eta) main.append(eta);
  }

  if (highlightPairs.length > 0) {
    const figures = el("div", { class: "r-si-figures" });
    for (const pair of highlightPairs) figures.append(buildHighlightFigure(pair, copyCtx));
    main.append(figures);
  }

  if (checks.length === 0 && highlightPairs.length === 0 && sketchPairs.length === 0) {
    main.append(buildEmptyFallback(chartFallback));
  }

  if (warnings.length > 0 && showWarnings) main.append(buildWarningsButton(warnings.length));

  if (showSketches) appendSketches(side, sketchPairs, previousData, token, campi);

  if (suppressAnnounce) {
    // Restore politeness on the next frame, once this render's mutations have already landed --
    // a same-frame `polite` would let the screen reader pick the mutation up anyway.
    requestAnimationFrame(() => root.setAttribute("aria-live", "polite"));
  }
}

// `root` (`#bottom-bar`) IS ALREADY the tap target: shell (index.html + layout.js) declares it as
// a `<button>` and wires the pane switch itself ("shell owns the click-to-jump behaviour, the
// results package fills its text content" -- js/layout.js). This module only ever writes its
// TEXT content, never a nested interactive element and never its own click handler.
// Review finding 25: a tool with no checks (e.g. sisma-spettro) used to show the mute "Calcolo
// completato" here even when it DOES have a governing figure to show -- its first `highlight`
// output instead, the same figure the Sintesi block itself leads with.
export function renderBottomBar(root, { report, highlightPairs = [] } = {}) {
  if (!root) return;
  clear(root);
  if (!report) return;
  const checks = report.checks || [];
  if (checks.length > 0) {
    const ok = checks.every((check) => check.passed);
    root.append(el("span", { class: `r-bb-word ${ok ? "r-verdict-word--ok" : "r-verdict-word--ko"}`, text: verdictWord(checks) }));
    const governing = governingCheck(checks);
    const ratio = governing ? effectiveUtilisation(governing) : null;
    if (ratio !== null) {
      root.append(el("span", { class: "r-bb-eta", text: `η max ${formatUtilisation(ratio)}` }));
    }
  } else if (highlightPairs.length > 0) {
    const { node, value } = highlightPairs[0];
    const word = el("span", { class: "r-bb-word" });
    if (node.symbol) word.append(symbolNode(node.symbol));
    else word.append(document.createTextNode(sentenceCase(node.label)));
    const { text } = formatValue(value, node);
    const unit = node.unit && node.unit !== "-" ? ` ${formatUnit(node.unit)}` : "";
    word.append(document.createTextNode(` ${text}${unit}`));
    root.append(word);
  } else {
    root.append(el("span", { class: "r-bb-word", text: "Calcolo completato" }));
  }
}

let scrollWired = false;
export function initSintesiCollapse(sintesiRoot) {
  if (scrollWired || !sintesiRoot) return;
  scrollWired = true;
  const pane = document.getElementById("results-pane");
  // `#results-pane` only scrolls itself at >=720px (layout.css `overflow-y:auto`) -- below that
  // the whole page/window scrolls instead, and a listener on `#results-pane` ALONE never fires
  // there, so the Sintesi never collapses (bug: a tall block, e.g. this module's own chart-
  // fallback preview, then permanently covers whatever scrolls underneath its sticky position on
  // a narrow viewport). Both hosts stay wired for the app's lifetime rather than picking one at
  // this single init call -- simpler and correct across a live breakpoint change mid-session too.
  const read = () => Math.max(pane ? pane.scrollTop : 0, window.scrollY || document.documentElement.scrollTop || 0);
  // Collapsing removes up to ~260px of sticky block: the pane's scroll range shrinks by as much, the
  // browser clamps scrollTop back under the threshold, the block re-expands, and so on -- the
  // "flicker and jump back up" the engineer saw when opening a group and scrolling. Two guards:
  // hysteresis (collapse past COLLAPSE_AFTER_PX, expand only back near the top) and a bottom
  // spacer on the scrolling pane equal to the height just removed, so the range never shrinks.
  const setSpacer = (px) => {
    const host = pane || document.documentElement;
    host.style.setProperty("--sm-collapse-spacer", `${Math.max(0, Math.round(px))}px`);
  };
  const onScroll = () => {
    const collapsed = sintesiRoot.classList.contains("r-sintesi--collapsed");
    const y = read();
    if (!collapsed && y > COLLAPSE_AFTER_PX) {
      const before = sintesiRoot.offsetHeight;
      sintesiRoot.classList.add("r-sintesi--collapsed");
      setSpacer(before - sintesiRoot.offsetHeight);
    } else if (collapsed && y < EXPAND_BELOW_PX) {
      sintesiRoot.classList.remove("r-sintesi--collapsed");
      setSpacer(0);
    }
  };
  if (pane) pane.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("scroll", onScroll, { passive: true });
}
