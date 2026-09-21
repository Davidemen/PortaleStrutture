"""Layout lint for every tool's example sketch: dimension lines and pressure diagrams must point
AWAY from the element (the side convention of shared/sketch.py is easy to get backwards)."""
import math

import pytest

from strutture.shared.sketch import Diagramma, Quota, Sketch, Vista, linea_quota, normale_sinistra
from strutture.shared.tool import discover, execute

SOLID_STYLES = {"calcestruzzo", "acciaio", "palo"}
TOLERANCE_M = 1e-6


def _solid_points(vista: Vista) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for forma in vista.forme:
        if getattr(forma, "stile", None) not in SOLID_STYLES:
            continue
        if forma.kind == "rect":
            points += [(forma.x, forma.y), (forma.x + forma.w, forma.y + forma.h)]
        elif forma.kind == "polygon":
            points += list(forma.punti)
        elif forma.kind == "circle":
            points += [(forma.centro[0] - forma.r, forma.centro[1] - forma.r), (forma.centro[0] + forma.r, forma.centro[1] + forma.r)]
    return points


def _centre(points: list[tuple[float, float]]) -> tuple[float, float]:
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)


def _mid(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def layout_problems(sketch: Sketch) -> list[str]:
    problems: list[str] = []
    for vista in sketch.viste:
        solids = _solid_points(vista)
        if not solids:
            continue
        centre = _centre(solids)
        for forma in vista.forme:
            if isinstance(forma, Quota) and forma.distanza != 0:
                inward = math.dist(_mid(*linea_quota(forma)), centre) < math.dist(_mid(forma.p1, forma.p2), centre) - TOLERANCE_M
                if inward:
                    problems.append(f"{vista.titolo}: quota {forma.testo!r} is drawn towards the element (flip the sign of distanza)")
            if isinstance(forma, Diagramma) and forma.stile == "pressione" and any(v > 0 for v in forma.valori):
                nx, ny = normale_sinistra(*forma.base)
                base_mid = _mid(*forma.base)
                step = 0.01 * max(math.dist(*forma.base), TOLERANCE_M)  # a small move along the ordinate direction
                tip = (base_mid[0] + nx * step, base_mid[1] + ny * step)
                if math.dist(tip, centre) < math.dist(base_mid, centre) - TOLERANCE_M:
                    problems.append(f"{vista.titolo}: pressure diagram projects into the element (reverse the baseline)")
    return problems


def _example_sketches() -> list[tuple[str, Sketch]]:
    found = []
    for name, tool in sorted(discover().items()):
        if not tool.example:
            continue
        report = execute(tool, {**tool.example, "legacy_compat": False})
        sketch = getattr(report.data, "schizzo", None) if report.ok else None
        if sketch is not None:
            found.append((name, sketch))
    return found


@pytest.mark.unit
def test_the_lint_catches_an_inward_dimension_and_an_inward_diagram() -> None:
    from strutture.shared.sketch import Rettangolo

    base = Rettangolo(x=0, y=0, w=2, h=1, stile="calcestruzzo")
    bad = Sketch(viste=(Vista(titolo="T", forme=(
        base,
        Quota(p1=(0, 0), p2=(2, 0), distanza=0.3, testo="B"),          # left of (0,0)->(2,0) = up = inside
        Diagramma(base=((0, 0), (2, 0)), valori=(100.0, 50.0)),          # projects up, into the footing
    )),))
    good = Sketch(viste=(Vista(titolo="T", forme=(
        base,
        Quota(p1=(0, 0), p2=(2, 0), distanza=-0.3, testo="B"),
        Diagramma(base=((2, 0), (0, 0)), valori=(50.0, 100.0)),
    )),))
    assert len(layout_problems(bad)) == 2 and layout_problems(good) == []


@pytest.mark.unit
def test_every_tool_sketch_places_dimensions_and_pressures_outside_the_element() -> None:
    problems = {name: layout_problems(sketch) for name, sketch in _example_sketches()}
    assert {name: found for name, found in problems.items() if found} == {}


# ---- readability lint (user feedback 2026-09-21: "a bit messy and cramped") -----------------------
MAX_ASPECT = 3.5          # a view flatter/taller than this wastes the figure: crop or break long elements
MIN_FEATURE_SHARE = 0.02  # a solid thinner than 2 % of the view's larger side is an unreadable sliver


def _extent(vista: Vista) -> tuple[float, float]:
    points = _solid_points(vista)
    for forma in vista.forme:
        if forma.kind == "line":
            points += [forma.p1, forma.p2]
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return (max(xs) - min(xs), max(ys) - min(ys)) if points else (0.0, 0.0)


def readability_problems(sketch: Sketch) -> list[str]:
    problems: list[str] = []
    for vista in sketch.viste:
        width, height = _extent(vista)
        larger, smaller = max(width, height), min(width, height)
        if smaller > 0 and larger / smaller > MAX_ASPECT:
            problems.append(f"{vista.titolo}: drawing is {larger / smaller:.1f}:1 — crop or break the long element so it reads")
        for forma in vista.forme:
            is_solid_rect = forma.kind == "rect" and forma.stile in SOLID_STYLES and larger > 0
            if is_solid_rect and min(forma.w, forma.h) / larger < MIN_FEATURE_SHARE:
                problems.append(f"{vista.titolo}: a solid {forma.w:.2f}×{forma.h:.2f} m is a sliver at this scale — draw it schematically thicker")
            if forma.kind == "label" and forma.simbolo and forma.testo.replace(" ", "").startswith(forma.simbolo.replace(" ", "")):
                problems.append(f"{vista.titolo}: label repeats its symbol in the text ({forma.testo!r}) — testo is the value only")
    return problems


@pytest.mark.unit
def test_the_readability_lint_flags_the_snow_drift_case() -> None:
    from strutture.shared.sketch import Etichetta, Linea, Rettangolo

    cramped = Sketch(viste=(Vista(titolo="T", forme=(
        Rettangolo(x=0, y=0, w=0.3, h=10, stile="calcestruzzo"),
        Linea(p1=(0.3, 0), p2=(36.5, 0), stile="calcestruzzo"),
        Etichetta(punto=(0.3, 5), simbolo="q_s2", testo="q_s2 = 6,16 kN/m²"),
    )),))
    found = readability_problems(cramped)
    assert len(found) == 3 and any("sliver" in f for f in found) and any("repeats its symbol" in f for f in found)


@pytest.mark.unit
def test_every_tool_sketch_is_readable() -> None:
    problems = {name: readability_problems(sketch) for name, sketch in _example_sketches()}
    assert {name: found for name, found in problems.items() if found} == {}


# ---- text overlap lint: estimates every text box at the size the UI draws it ---------------------
FIGURE_PX = (340.0, 220.0)   # a typical sketch cell in the Sintesi block
FONT_PX = 11.5
CHAR_W = 0.55                # average glyph width in em
MAX_TEXTS = 8                # more than this cannot stay legible in one view


def _text_boxes(vista: Vista) -> list[tuple[str, float, float, float, float]]:
    """(text, x0, y0, x1, y1) in MODEL units for every text item, at the assumed on-screen scale."""
    width, height = _extent(vista)
    if width <= 0 or height <= 0:
        return []
    scale = min(FIGURE_PX[0] / width, FIGURE_PX[1] / height) * 0.8   # px per metre, with margins
    boxes = []
    for forma in vista.forme:
        if forma.kind == "label":
            text = f"{forma.simbolo or ''} {forma.testo}".strip()
            anchor_x, (px, py) = {"start": 0.0, "middle": 0.5, "end": 1.0}[forma.ancora], forma.punto
        elif forma.kind == "dimension":
            text, anchor_x = forma.testo, 0.5
            px, py = _mid(*linea_quota(forma))
        elif forma.kind == "arrow" and forma.testo:
            text, anchor_x, (px, py) = forma.testo, 0.0, forma.coda
        else:
            continue
        w, h = CHAR_W * FONT_PX * len(text) / scale, 1.3 * FONT_PX / scale
        boxes.append((text, px - anchor_x * w, py, px - anchor_x * w + w, py + h))
    return boxes


def overlap_problems(sketch: Sketch) -> list[str]:
    problems: list[str] = []
    for vista in sketch.viste:
        boxes = _text_boxes(vista)
        if len(boxes) > MAX_TEXTS:
            problems.append(f"{vista.titolo}: {len(boxes)} text items (max {MAX_TEXTS}) — move secondary values to the results")
        for i, a in enumerate(boxes):
            for b in boxes[i + 1:]:
                if a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4]:
                    problems.append(f"{vista.titolo}: texts overlap: {a[0]!r} / {b[0]!r}")
    return problems


@pytest.mark.unit
def test_every_tool_sketch_has_no_overlapping_text() -> None:
    problems = {name: overlap_problems(sketch) for name, sketch in _example_sketches()}
    assert {name: found for name, found in problems.items() if found} == {}
