"""Live sketch for `fond-plinto-isolato` (docs/ui/WORKBENCH_SPEC.md §7): Pianta + Sezione follow
the inputs, and a drawing failure must never fail the calculation."""
import sys
import time
from pathlib import Path

import pytest

from strutture.foundations.plinti_isolati import schizzo as schizzo_module
from strutture.foundations.plinti_isolati.riga_verifica import riga_verifica
from strutture.foundations.plinti_isolati.schizzo import disegna
from strutture.foundations.plinti_isolati.tool import TOOLS
from strutture.shared.load_table import ReactionRow
from strutture.shared.tool import execute

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from test_sketch_layout import layout_problems, overlap_problems, readability_problems

TOOL = TOOLS[0]


def _governante(inputs: dict):
    row = ReactionRow.model_validate(inputs["reazioni"][0])
    return riga_verifica(
        row, inputs["ax_m"], inputs["by_m"], inputs["h_plinto_m"], inputs["h_interro_m"],
        inputs.get("a_pedestal_m", 0.0), inputs.get("b_pedestal_m", 0.0),
        inputs.get("h_pedestal_sopra_m", 0.0), inputs.get("h_pedestal_sotto_m", 0.0),
        inputs.get("offset_leva_m", 0.05), inputs.get("ex_m", 0.0), inputs.get("ey_m", 0.0),
        inputs["gamma_terreno_kNm3"], inputs["phi_terreno_deg"],
        metodo_pressioni=inputs.get("metodo_pressioni", "esatto"), legacy_compat=inputs.get("legacy_compat", False),
    )


@pytest.mark.unit
def test_viste_titoli_e_forme_esempio() -> None:
    from strutture.foundations.plinti_isolati.input import PlintoIsolatoInput

    inputs = PlintoIsolatoInput.model_validate(TOOL.example)
    governante = _governante(TOOL.example)
    sketch = disegna(inputs, governante)

    assert [v.titolo for v in sketch.viste] == ["Pianta", "Sezione"]
    pianta, sezione = sketch.viste
    assert [f.kind for f in pianta.forme] == ["rect", "circle", "label", "dimension", "dimension"]
    kinds_sezione = [f.kind for f in sezione.forme]
    assert kinds_sezione[0] == "rect"
    assert "arrow" in kinds_sezione
    assert "dimension" in kinds_sezione
    assert "diagram" in kinds_sezione


@pytest.mark.unit
def test_pianta_rettangolo_segue_gli_input() -> None:
    from strutture.foundations.plinti_isolati.input import PlintoIsolatoInput

    inputs = PlintoIsolatoInput.model_validate(TOOL.example)
    governante = _governante(TOOL.example)
    sketch = disegna(inputs, governante)
    rettangolo = sketch.viste[0].forme[0]
    assert rettangolo.x == pytest.approx(-inputs.ax_m / 2)
    assert rettangolo.y == pytest.approx(-inputs.by_m / 2)
    assert rettangolo.w == pytest.approx(inputs.ax_m)
    assert rettangolo.h == pytest.approx(inputs.by_m)

    quota_ax = sketch.viste[0].forme[3]
    assert quota_ax.testo == "A_X = 4,00 m"
    quota_by = sketch.viste[0].forme[4]
    assert quota_by.testo == "B_Y = 4,00 m"


@pytest.mark.unit
def test_geometria_segue_una_dimensione_modificata() -> None:
    """Cambiando ax_m il rettangolo e la sua quota cambiano di conseguenza."""
    from strutture.foundations.plinti_isolati.input import PlintoIsolatoInput

    modificato = {**TOOL.example, "ax_m": 6.5}
    inputs = PlintoIsolatoInput.model_validate(modificato)
    governante = _governante(modificato)
    sketch = disegna(inputs, governante)
    rettangolo = sketch.viste[0].forme[0]
    quota_ax = sketch.viste[0].forme[3]
    assert rettangolo.w == pytest.approx(6.5)
    assert quota_ax.testo == "A_X = 6,50 m"


@pytest.mark.unit
def test_diagramma_pressioni_riporta_sigma_max_e_min() -> None:
    from strutture.foundations.plinti_isolati.input import PlintoIsolatoInput

    inputs = PlintoIsolatoInput.model_validate(TOOL.example)
    governante = _governante(TOOL.example)
    sketch = disegna(inputs, governante)
    diagramma = next(f for f in sketch.viste[1].forme if f.kind == "diagram")
    assert diagramma.valori == pytest.approx((governante.sigma_max_kpa, governante.sigma_min_kpa))
    assert diagramma.etichette[0].startswith("σmax =")
    assert diagramma.etichette[1].startswith("σmin =")


@pytest.mark.unit
def test_pilastro_disegnato_quando_presente() -> None:
    """Con bicchiere non nullo compare il rettangolo del pilastro in pianta e in sezione."""
    from strutture.foundations.plinti_isolati.input import PlintoIsolatoInput

    modificato = {**TOOL.example, "a_pedestal_m": 0.6, "b_pedestal_m": 0.6, "h_pedestal_sopra_m": 0.5}
    inputs = PlintoIsolatoInput.model_validate(modificato)
    governante = _governante(modificato)
    sketch = disegna(inputs, governante)
    pianta_rects = [f for f in sketch.viste[0].forme if f.kind == "rect"]
    assert len(pianta_rects) == 2
    assert pianta_rects[1].w == pytest.approx(0.6)
    sezione_rects = [f for f in sketch.viste[1].forme if f.kind == "rect"]
    assert len(sezione_rects) == 2


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
    import strutture.foundations.plinti_isolati.tool as tool_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(tool_module, "disegna_schizzo", _rompi)
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


@pytest.mark.unit
def test_modulo_schizzo_importabile_e_puro() -> None:
    """Il modulo non tocca I/O: verifica solo che sia importabile senza effetti collaterali."""
    assert hasattr(schizzo_module, "disegna")


# --- composizione: layout/leggibilità/sovrapposizioni su input realistici oltre l'esempio --------

_CASI_COMPOSIZIONE = {
    "plinto molto largo": {"ax_m": 8.0, "by_m": 8.0, "h_plinto_m": 0.6},
    "bicchiere alto": {"a_pedestal_m": 1.0, "b_pedestal_m": 1.0, "h_pedestal_sopra_m": 2.2},
    "carico eccentrico": {"ex_m": 0.6, "ey_m": 0.4},
}


@pytest.mark.unit
@pytest.mark.parametrize("nome", list(_CASI_COMPOSIZIONE))
def test_composizione_su_input_realistici(nome: str) -> None:
    from strutture.foundations.plinti_isolati.input import PlintoIsolatoInput

    modificato = {**TOOL.example, **_CASI_COMPOSIZIONE[nome]}
    inputs = PlintoIsolatoInput.model_validate(modificato)
    governante = _governante(modificato)
    sketch = disegna(inputs, governante)
    problemi = layout_problems(sketch) + readability_problems(sketch) + overlap_problems(sketch)
    assert problemi == [], f"{nome}: {problemi}"
