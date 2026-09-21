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
    kinds_prospetto = [f.kind for f in prospetto.forme]
    assert prospetto.forme[0].kind == "rect"  # base del meccanismo
    assert prospetto.forme[1].kind == "rect"  # tratto di colonna (sempre presente, indicativo)
    assert kinds_prospetto.count("rect") == 2 + 2  # base + colonna + 2 stinti palo (Rettangolo, non Barre in prospetto)
    assert "bars" not in kinds_prospetto  # i pali in PROSPETTO sono stinti, non cerchi a diametro vero
    assert kinds_prospetto.count("line") == 2 + 1 + 2  # 2 puntoni + 1 tirante + 2 tratti fantasma dei pali
    assert kinds_prospetto.count("arrow") == 2  # reazione N sotto ciascun palo


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
    # appoggio diretto: base + colonna + 1 stinto palo (rect) + 1 fantasma (line) + 1 reazione (arrow)
    assert [f.kind for f in prospetto.forme] == ["rect", "rect", "rect", "line", "arrow"]
    palo = prospetto.forme[2]
    assert palo.x == pytest.approx(-inputs.diametro_pila_mm / 2000.0)
    assert palo.w == pytest.approx(inputs.diametro_pila_mm / 1000.0)


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
def test_tirante_al_livello_delle_barre_non_al_nodo_di_colonna() -> None:
    """Correzione P0 della revisione di design: il tirante deve stare al livello delle barre di
    fondo (vicino ai pali), non al nodo in sommità sotto il pilastro (dove sta il puntone)."""
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
    prospetto = sketch.viste[1]
    tirante = next(f for f in prospetto.forme if f.kind == "line" and f.stile == "tirante")
    puntone_forma = next(f for f in prospetto.forme if f.kind == "line" and f.stile == "puntone")
    y_nodo_colonna = puntone_forma.p2[1]  # estremo del puntone al nodo di colonna (sommità)
    y_atteso_tirante = inputs.copriferro_cm / 100.0 + inputs.diametro_inf_x_mm / 1000.0 / 2.0
    assert tirante.p1[1] == pytest.approx(y_atteso_tirante)
    assert tirante.p1[1] < y_nodo_colonna  # il tirante è vicino ai pali, non al nodo di colonna
    assert tirante.p1[1] < 0.5 * inputs.h_plinto_m  # ben nella metà inferiore del plinto


@pytest.mark.unit
def test_palo_come_stinto_verticale_e_reazione_non_sovrapposta() -> None:
    """Correzione P0: in prospetto i pali sono stinti (Rettangolo), non cerchi (Barre, riservati
    alla pianta), e la freccia/etichetta di reazione N sta sotto il tratto fantasma del palo, mai
    sovrapposta al rettangolo nero."""
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
    prospetto = sketch.viste[1]
    pali = [f for f in prospetto.forme if f.kind == "rect" and f.stile == "calcestruzzo"][2:]  # esclude base + colonna
    frecce = [f for f in prospetto.forme if f.kind == "arrow"]
    assert len(pali) == len(frecce) == 2
    for palo, freccia in zip(pali, frecce, strict=True):
        assert palo.y < 0.0 and palo.y + palo.h == pytest.approx(0.0)  # sotto la testa palo (y=0)
        # l'etichetta (alla coda della freccia) resta sotto il rettangolo del palo, mai dentro.
        assert freccia.coda[1] < palo.y


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
