// Rail pictograms (WORKBENCH_SPEC.md #12): 24x24 viewBox, stroke=currentColor 1.5, round caps/
// joins, built with createElementNS from the exact path data the design lead specified -- no
// icon font, no external file (CSP-safe). buildIcon(key) returns a detached, aria-hidden <svg>;
// the button it is appended to supplies the accessible name.
const NS = "http://www.w3.org/2000/svg";

function shape(tag, attrs) {
  const node = document.createElementNS(NS, tag);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  return node;
}

function path(d, extra = {}) {
  return shape("path", { d, ...extra });
}

function dot(cx, cy) {
  return shape("circle", { cx, cy, r: "1.1", fill: "currentColor", stroke: "none" });
}

// One entry per destination key, each a list of child shapes drawn on top of the shared 24x24
// stroke base the <svg> itself carries (see buildIcon).
const SHAPES = {
  home: () => [path("M4 11 12 4l8 7M6 10v10h12V10")],
  cerca: () => [shape("circle", { cx: "10.5", cy: "10.5", r: "5.5" }), path("M15 15l5 5")],
  preferiti: () => [path("M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.8L12 16.9 6.8 19.6l1-5.8L3.5 9.7l5.9-.8z")],
  recenti: () => [shape("circle", { cx: "12", cy: "12", r: "8" }), path("M12 7.5V12l3 2")],
  carichi: () => [
    path(
      "M4 5h16M6 5v6M10 5v6M14 5v6M18 5v6" +
        "M4.8 9.5 6 11l1.2-1.5M8.8 9.5 10 11l1.2-1.5M12.8 9.5 14 11l1.2-1.5M16.8 9.5 18 11l1.2-1.5" +
        "M3 14h18M5 14l-2 4h4zM19 14l-2 4h4z"
    ),
  ],
  "calcestruzzo-armato": () => [
    path("M6 4h12v16H6z"),
    dot(9, 17), dot(12, 17), dot(15, 17), dot(9, 7), dot(15, 7),
  ],
  acciaio: () => [path("M6 4h12v3h-4.5v10H18v3H6v-3h4.5V7H6z")],
  geotecnica: () => [
    path("M3 8h18M5 8l-2 3M9 8l-2 3M13 8l-2 3M17 8l-2 3M21 8l-2 3"),
    path("M3 14h18M3 19h18", { "stroke-dasharray": "2 2" }),
  ],
  fondazioni: () => [path("M10 3h4v9h-4zM4 12h16v5H4zM3 20h18")],
  registro: () => [path("M5 6l1.5 1.5L9 5M5 12l1.5 1.5L9 11M5 18l1.5 1.5L9 17M12 6h7M12 12h7M12 18h7")],
  progetti: () => [path("M3 7h6l2 2h10v10H3z")],
  // Gear with a ruler tick (WORKBENCH_SPEC §26.8): distinct from "registro"'s ledger checkmarks
  // and from every category pictogram above.
  impostazioni: () => [
    shape("circle", { cx: "12", cy: "12", r: "3.2" }),
    path(
      "M12 4.5v2.2M12 17.3v2.2M4.5 12h2.2M17.3 12h2.2" +
        "M6.9 6.9l1.6 1.6M15.5 15.5l1.6 1.6M17.1 6.9l-1.6 1.6M8.5 15.5l-1.6 1.6"
    ),
    path("M19 4v3M17.5 5.5h3", { "stroke-width": "1" }),
  ],
  espandi: () => [path("M9 6l6 6-6 6")],
  comprimi: () => [path("M15 6l-6 6 6 6")],
};

export const ICON_KEYS = Object.keys(SHAPES);

export function buildIcon(key) {
  const svg = shape("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    "stroke-width": "1.5",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
    "aria-hidden": "true",
    class: "sm-icon",
  });
  const build = SHAPES[key] || SHAPES.progetti;
  for (const node of build()) svg.append(node);
  return svg;
}
