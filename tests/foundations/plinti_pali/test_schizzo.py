"""Live sketch for `fond-plinto-su-pali` (docs/ui/WORKBENCH_SPEC.md §7): Pianta + Prospetto S&T
follow the inputs, and a drawing failure must never fail the calculation."""
import sys
import time
from pathlib import Path

import pytest

from strutture.foundations.plinti_pali.input import PlintoSuPaliInput
from strutture.foundations.plinti_pali.puntoni_tiranti import puntoni_tiranti
from strutture.foundations.plinti_pali.schizzo import disegna
from strutture.foundations.plinti_pali.tool import TOOLS
from strutture.shared.pile_group import pile_coordinates
from strutture.shared.tool import execute

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from test_sketch_layout import layout_problems, overlap_problems, readability_problems

TOOL = TOOLS[0]


@pytest.mark.unit
def test_viste_titoli_e_forme_esempio() -> None:
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    sketch = report.data.schizzo
    assert sketch is not None
    assert [v.titolo for v in sketch.viste] == ["Pianta", "Prospetto S&T"]
    pianta, prospetto = sketch.viste
    assert [f.kind for f in pianta.forme] == ["rect", "rect", "bars", "dimension", "dimension",
                                               "dimension", "dimension"]
    assert prospetto.forme[0].kind == "rect"  # base del meccanismo
    assert prospetto.forme[1].kind == "rect"  # tratto di colonna (sempre presente, indicativo)
    assert prospetto.forme[2].kind == "bars"
    assert "line" in [f.kind for f in prospetto.forme]
    assert "arrow" in [f.kind for f in prospetto.forme]


@pytest.mark.unit
def test_pianta_pali_alle_coordinate_vere() -> None:
    inputs = PlintoSuPaliInput.model_validate(TOOL.example)
    piles = pile_coordinates(inputs.schema_pali, inputs.lx_m, inputs.ly_m)
    pt = puntoni_tiranti(
        2, 2, inputs.lx_m, inputs.ly_m, inputs.h_plinto_m, inputs.copriferro_cm * 10.0,
        inputs.diametro_inf_x_mm, inputs.diametro_inf_y_mm, inputs.diametro_pila_mm,
        inputs.diametro_tirante_xy_mm, inputs.diametro_tirante_x_mm, inputs.diametro_tirante_y_mm,
        inputs.n_tirante_xy, inputs.n_tirante_x, inputs.n_tirante_y, 800.0,
        inputs.bx_pilastro_m * 1000.0, inputs.by_pilastro_m * 1000.0, 32.0, 1.5, 391.3, legacy_compat=False,
    )
    sketch = disegna(inputs, piles, pt, 800.0)
    barre = sketch.viste[0].forme[2]
    assert barre.centri == ((-1.0, -1.0), (1.0, -1.0), (-1.0, 1.0), (1.0, 1.0))
    assert barre.diametro == pytest.approx(0.6)  # 600 mm


@pytest.mark.unit
def test_geometria_segue_una_dimensione_modificata() -> None:
    """Cambiando ax_m il rettangolo del plinto e la sua quota cambiano di conseguenza."""
    modificato = {**TOOL.example, "ax_m": 5.5}
    report = execute(TOOL, modificato)
    assert report.ok, report.errors
    rettangolo = report.data.schizzo.viste[0].forme[0]
    quota_ax = report.data.schizzo.viste[0].forme[3]
    assert rettangolo.w == pytest.approx(5.5)
    assert quota_ax.testo == "A_X = 5,50 m"


@pytest.mark.unit
def test_schema_1x1_appoggio_diretto_senza_puntoni() -> None:
    """Con un solo palo (appoggio diretto) il prospetto disegna solo colonna e palo, senza puntoni/tiranti."""
    inputs = PlintoSuPaliInput.model_validate({**TOOL.example, "schema_pali": "1x1", "lx_m": 0.0, "ly_m": 0.0})
    piles = pile_coordinates("1x1", 0.0, 0.0)
    pt = puntoni_tiranti(
        1, 1, 0.0, 0.0, inputs.h_plinto_m, inputs.copriferro_cm * 10.0,
        inputs.diametro_inf_x_mm, inputs.diametro_inf_y_mm, inputs.diametro_pila_mm,
        inputs.diametro_tirante_xy_mm, inputs.diametro_tirante_x_mm, inputs.diametro_tirante_y_mm,
        inputs.n_tirante_xy, inputs.n_tirante_x, inputs.n_tirante_y, 1000.0,
        inputs.bx_pilastro_m * 1000.0, inputs.by_pilastro_m * 1000.0, 32.0, 1.5, 391.3, legacy_compat=False,
    )
    assert pt.puntone.theta_deg is None
    sketch = disegna(inputs, piles, pt, 1000.0)
    prospetto = sketch.viste[1]
    assert [f.kind for f in prospetto.forme] == ["rect", "rect", "bars", "arrow"]
    palo = prospetto.forme[2]
    assert palo.centri == ((0.0, 0.0),)


@pytest.mark.unit
def test_esempio_ha_schizzo_e_gira_in_meno_di_300ms() -> None:
    inizio = time.perf_counter()
    report = execute(TOOL, TOOL.example)
    durata = time.perf_counter() - inizio
    assert report.ok, report.errors
    assert report.data.schizzo is not None
    assert len(report.data.schizzo.viste) == 2
    assert durata < 0.3, f"esempio in {durata:.3f}s"


@pytest.mark.unit
def test_errore_nel_disegno_non_fa_fallire_il_calcolo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un'eccezione nello schizzo deve essere loggata e assorbita: il calcolo resta valido."""
    import strutture.foundations.plinti_pali.tool as tool_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(tool_module, "disegna_schizzo", _rompi)
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


# --- composizione: layout/leggibilità/sovrapposizioni su input realistici oltre l'esempio --------

_CASI_COMPOSIZIONE = {
    "plinto molto largo": {"ax_m": 8.0, "by_m": 8.0, "lx_m": 4.0, "ly_m": 4.0},
    "plinto alto": {"h_plinto_m": 2.5},
}


@pytest.mark.unit
@pytest.mark.parametrize("nome", list(_CASI_COMPOSIZIONE))
def test_composizione_su_input_realistici(nome: str) -> None:
    modificato = {**TOOL.example, **_CASI_COMPOSIZIONE[nome]}
    report = execute(TOOL, modificato)
    assert report.ok, report.errors
    sketch = report.data.schizzo
    problemi = layout_problems(sketch) + readability_problems(sketch) + overlap_problems(sketch)
    assert problemi == [], f"{nome}: {problemi}"


@pytest.mark.unit
def test_composizione_schema_1x1() -> None:
    """Schema 1x1 (appoggio diretto): `tool.run` ha un bug pre-esistente non nostro su questo
    schema (nessun tirante -> `max()` a un solo argomento non iterabile) — si costruisce lo
    schizzo direttamente, bypassando `run`, senza toccare quel codice di calcolo."""
    inputs = PlintoSuPaliInput.model_validate({**TOOL.example, "schema_pali": "1x1", "lx_m": 0.0, "ly_m": 0.0})
    piles = pile_coordinates("1x1", 0.0, 0.0)
    pt = puntoni_tiranti(
        1, 1, 0.0, 0.0, inputs.h_plinto_m, inputs.copriferro_cm * 10.0,
        inputs.diametro_inf_x_mm, inputs.diametro_inf_y_mm, inputs.diametro_pila_mm,
        inputs.diametro_tirante_xy_mm, inputs.diametro_tirante_x_mm, inputs.diametro_tirante_y_mm,
        inputs.n_tirante_xy, inputs.n_tirante_x, inputs.n_tirante_y, 1000.0,
        inputs.bx_pilastro_m * 1000.0, inputs.by_pilastro_m * 1000.0, 32.0, 1.5, 391.3, legacy_compat=False,
    )
    sketch = disegna(inputs, piles, pt, 1000.0)
    problemi = layout_problems(sketch) + readability_problems(sketch) + overlap_problems(sketch)
    assert problemi == [], problemi
