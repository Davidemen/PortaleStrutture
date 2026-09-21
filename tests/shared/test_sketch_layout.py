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
