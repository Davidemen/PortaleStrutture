"""Live sketch for `ca-mensola-tozza` (docs/ui/WORKBENCH_SPEC.md §7, COMPOSITION RULES in
shared/sketch.py): the "Prospetto" view follows the inputs, stays readable across several
realistic corbel geometries, and a drawing failure must never fail the calculation."""
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from test_sketch_layout import layout_problems, overlap_problems, readability_problems

from strutture.members.ca_mensole import schizzo as schizzo_module
from strutture.members.ca_mensole.geometria import geometria
from strutture.members.ca_mensole.models import MensolaTozzaInput
from strutture.members.ca_mensole.schizzo import disegna
from strutture.members.ca_mensole.tool import TOOLS
from strutture.shared.tool import execute

TOOL = TOOLS[0]


def _geometria(inputs: MensolaTozzaInput):
    return geometria(inputs.a_mm, inputs.h_mm, inputs.c_mm)


@pytest.mark.unit
def test_vista_titolo_e_forme_esempio() -> None:
    inputs = MensolaTozzaInput.model_validate(TOOL.example)
    geo = _geometria(inputs)
    sketch = disegna(inputs, geo)

    assert [v.titolo for v in sketch.viste] == ["Prospetto"]
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds.count("rect") == 1
    assert kinds.count("polygon") == 1
    assert kinds.count("arrow") == 1
    assert kinds.count("line") == 2  # puntone + tirante
    assert kinds.count("dimension") == 2  # a, h
    assert kinds.count("label") == 1  # b (fuori piano)


@pytest.mark.unit
def test_mensola_segue_gli_input() -> None:
    inputs = MensolaTozzaInput.model_validate(TOOL.example)
    geo = _geometria(inputs)
    sketch = disegna(inputs, geo)
    poligono = next(f for f in sketch.viste[0].forme if f.kind == "polygon")
    assert poligono.punti[0] == pytest.approx((0.0, 0.0))
    assert poligono.punti[1] == pytest.approx((inputs.a_mm / 1000.0, 0.0))
    assert poligono.punti[2] == pytest.approx((inputs.a_mm / 1000.0, geo.d_mm / 1000.0))
    assert poligono.punti[3] == pytest.approx((0.0, inputs.h_mm / 1000.0))


@pytest.mark.unit
def test_cambiando_h_mm_cambia_il_vertice_superiore_del_poligono_e_la_quota_h() -> None:
    """Cambiando h_mm il vertice superiore della mensola e il testo della quota h cambiano."""
    modificato = {**TOOL.example, "h_mm": 600}
    inputs = MensolaTozzaInput.model_validate(modificato)
    geo = _geometria(inputs)
    sketch = disegna(inputs, geo)

    poligono = next(f for f in sketch.viste[0].forme if f.kind == "polygon")
    assert poligono.punti[3] == pytest.approx((0.0, 0.6))

    quote = [f for f in sketch.viste[0].forme if f.kind == "dimension"]
    quota_h = next(q for q in quote if q.testo.startswith("h ="))
    assert quota_h.testo == "h = 600 mm"


@pytest.mark.unit
def test_quota_a_e_etichetta_b_seguono_gli_input() -> None:
    inputs = MensolaTozzaInput.model_validate(TOOL.example)
    geo = _geometria(inputs)
    sketch = disegna(inputs, geo)

    quote = [f for f in sketch.viste[0].forme if f.kind == "dimension"]
    quota_a = next(q for q in quote if q.testo.startswith("a ="))
    assert quota_a.testo == "a = 177 mm"

    etichetta = next(f for f in sketch.viste[0].forme if f.kind == "label")
    assert etichetta.simbolo == "b"
    # regola 4 (COMPOSITION RULES): con `simbolo` impostato, `testo` è solo il valore.
    assert etichetta.testo == "800 mm"
    assert not etichetta.testo.startswith("b")


@pytest.mark.unit
def test_carico_puntone_e_tirante_convergono_sul_punto_di_carico() -> None:
    inputs = MensolaTozzaInput.model_validate(TOOL.example)
    geo = _geometria(inputs)
    sketch = disegna(inputs, geo)
    punto_carico = (inputs.a_mm / 1000.0, geo.d_mm / 1000.0)

    freccia = next(f for f in sketch.viste[0].forme if f.kind == "arrow")
    assert freccia.punta == pytest.approx(punto_carico)
    assert freccia.testo == "P_Ed = 136 kN"

    puntone = next(f for f in sketch.viste[0].forme if f.stile == "puntone")
    tirante = next(f for f in sketch.viste[0].forme if f.stile == "tirante")
    assert puntone.p1 == pytest.approx(punto_carico)
    assert puntone.p2 == pytest.approx((0.0, inputs.c_mm / 1000.0))
    assert tirante.p1 == pytest.approx(punto_carico)
    assert tirante.p2 == pytest.approx((0.0, (inputs.h_mm - inputs.c_mm) / 1000.0))


@pytest.mark.unit
@pytest.mark.parametrize(
    "overrides",
    [
        {},  # esempio
        {"a_mm": 100, "h_mm": 300, "b_mm": 400, "c_mm": 30},  # mensola piccola e tozza
        {"a_mm": 350, "h_mm": 900, "b_mm": 1000, "c_mm": 60},  # mensola grande
        {"a_mm": 250, "h_mm": 350, "b_mm": 300, "c_mm": 40},  # a vicino ad h (mensola "corta")
    ],
)
def test_geometrie_realistiche_non_hanno_problemi_di_layout(overrides: dict) -> None:
    modificato = {**TOOL.example, **overrides}
    inputs = MensolaTozzaInput.model_validate(modificato)
    geo = _geometria(inputs)
    sketch = disegna(inputs, geo)
    problems = layout_problems(sketch) + readability_problems(sketch) + overlap_problems(sketch)
    assert problems == [], problems


@pytest.mark.unit
def test_esempio_ha_schizzo_e_gira_veloce() -> None:
    inizio = time.perf_counter()
    report = execute(TOOL, TOOL.example)
    durata = time.perf_counter() - inizio
    assert report.ok, report.errors
    assert report.data.schizzo is not None
    assert len(report.data.schizzo.viste) == 1
    assert durata < 0.3, f"esempio in {durata:.3f}s"


@pytest.mark.unit
def test_errore_nel_disegno_non_fa_fallire_il_calcolo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un'eccezione nello schizzo deve essere loggata e assorbita: il calcolo resta valido."""
    import strutture.members.ca_mensole.tool as tool_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(tool_module, "disegna_schizzo", _rompi)
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


@pytest.mark.unit
def test_modulo_schizzo_importabile_e_puro() -> None:
    assert hasattr(schizzo_module, "disegna")
