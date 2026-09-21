"""Live sketch for `fond-pavimento-industriale` (docs/ui/WORKBENCH_SPEC.md §7): Pianta follows the
inputs, and a drawing failure must never fail the calculation."""
import sys
import time
from pathlib import Path

import pytest

from strutture.foundations.pavimento_industriale import schizzo as schizzo_module
from strutture.foundations.pavimento_industriale.models import PavimentoIndustrialeInput
from strutture.foundations.pavimento_industriale.schizzo import disegna
from strutture.foundations.pavimento_industriale.sottofondo import sottofondo
from strutture.foundations.pavimento_industriale.tool import TOOLS
from strutture.shared.tool import execute

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from test_sketch_layout import layout_problems, overlap_problems, readability_problems

TOOL = TOOLS[0]
_L_MM_ESEMPIO = 1200.0  # valore comodo per i test che non ricalcolano il sottofondo


def _l_mm(inputs: PavimentoIndustrialeInput) -> float:
    mat_ecm_MPa, mat_fck_MPa = 31475.8, 25.0  # C25/30, coerenti col golden case
    return sottofondo(
        inputs.h_mm, inputs.c_mm, inputs.nu_poisson, mat_ecm_MPa, mat_fck_MPa,
        sottofondo_tipo=inputs.sottofondo_tipo, kt_manuale_N_mm3=inputs.kt_manuale_N_mm3,
    ).l_mm


@pytest.mark.unit
def test_vista_titolo_e_forme_esempio() -> None:
    inputs = PavimentoIndustrialeInput.model_validate(TOOL.example)
    sketch = disegna(inputs, _l_mm(inputs))

    assert [v.titolo for v in sketch.viste] == ["Pianta"]
    pianta = sketch.viste[0]
    n_carichi = len(TOOL.example["carichi"])
    # rettangolo piastra, 2 quote, 1 cerchio di riferimento, un'impronta per carico, poi le
    # etichette esterne (una per carico, fuori dal pannello sul lato sinistro).
    attese = ["rect", "dimension", "dimension", "circle"] + ["rect"] * n_carichi + ["label"] * n_carichi
    assert [f.kind for f in pianta.forme] == attese


@pytest.mark.unit
def test_rettangolo_piastra_segue_le_dimensioni_dei_giunti_di_contrazione() -> None:
    inputs = PavimentoIndustrialeInput.model_validate(TOOL.example)
    sketch = disegna(inputs, _l_mm(inputs))
    rettangolo = sketch.viste[0].forme[0]
    assert rettangolo.x == pytest.approx(-inputs.a_contrazione_m / 2)
    assert rettangolo.y == pytest.approx(-inputs.b_contrazione_m / 2)
    assert rettangolo.w == pytest.approx(inputs.a_contrazione_m)
    assert rettangolo.h == pytest.approx(inputs.b_contrazione_m)

    quota_a, quota_b = sketch.viste[0].forme[1], sketch.viste[0].forme[2]
    assert quota_a.testo == "a' = 20,00 m"
    assert quota_b.testo == "b' = 18,00 m"


@pytest.mark.unit
def test_geometria_segue_una_dimensione_modificata() -> None:
    """Cambiando a_contrazione_m il rettangolo e la sua quota cambiano di conseguenza."""
    modificato = {**TOOL.example, "a_contrazione_m": 12.5}
    inputs = PavimentoIndustrialeInput.model_validate(modificato)
    sketch = disegna(inputs, _l_mm(inputs))
    rettangolo = sketch.viste[0].forme[0]
    quota_a = sketch.viste[0].forme[1]
    assert rettangolo.w == pytest.approx(12.5)
    assert quota_a.testo == "a' = 12,50 m"


@pytest.mark.unit
def test_cerchio_raggio_relativa_rigidezza_segue_l_mm() -> None:
    inputs = PavimentoIndustrialeInput.model_validate(TOOL.example)
    sketch = disegna(inputs, _L_MM_ESEMPIO)
    cerchio = sketch.viste[0].forme[3]
    assert cerchio.kind == "circle"
    assert cerchio.centro == pytest.approx((0.0, 0.0))
    assert cerchio.r == pytest.approx(_L_MM_ESEMPIO / 1000.0)
    assert cerchio.stile == "quota"
    assert cerchio.tratteggio is True


@pytest.mark.unit
def test_impronte_posizionate_per_centro_bordo_spigolo() -> None:
    """L'esempio ha le tre posizioni: centro (a cavallo del centro piastra), bordo (a cavallo del
    lato inferiore) e spigolo (a cavallo dello spigolo inferiore sinistro)."""
    inputs = PavimentoIndustrialeInput.model_validate(TOOL.example)
    sketch = disegna(inputs, _L_MM_ESEMPIO)
    rettangoli_carico = [f for f in sketch.viste[0].forme if f.kind == "rect" and f.stile == "carico"]
    assert len(rettangoli_carico) == 4

    a, b = inputs.a_contrazione_m, inputs.b_contrazione_m
    centro, bordo, spigolo = rettangoli_carico[0], rettangoli_carico[1], rettangoli_carico[2]
    # centro (prima riga 'centro'): centrato sull'origine, quindi x0 = -w/2
    assert centro.x == pytest.approx(-centro.w / 2)
    assert centro.y == pytest.approx(-centro.h / 2)
    # bordo: centrato sulla mezzeria del lato inferiore (a cavallo, meta' dentro meta' fuori)
    assert bordo.x == pytest.approx(-bordo.w / 2)
    assert bordo.y == pytest.approx(-b / 2 - bordo.h / 2)
    # spigolo: centrato sullo spigolo inferiore sinistro (a cavallo in entrambe le direzioni)
    assert spigolo.x == pytest.approx(-a / 2 - spigolo.w / 2)
    assert spigolo.y == pytest.approx(-b / 2 - spigolo.h / 2)


@pytest.mark.unit
def test_impronte_sulla_stessa_posizione_condividono_il_centro() -> None:
    """Nell'esempio 'ruota motrice' e 'ruote anteriori' sono entrambe in posizione 'centro':
    entrambe le impronte sono centrate sullo stesso punto (approssimazione accettabile per lo
    schema)."""
    inputs = PavimentoIndustrialeInput.model_validate(TOOL.example)
    sketch = disegna(inputs, _L_MM_ESEMPIO)
    rettangoli_carico = [f for f in sketch.viste[0].forme if f.kind == "rect" and f.stile == "carico"]
    primo_centro, secondo_centro = rettangoli_carico[0], rettangoli_carico[3]
    assert primo_centro.x + primo_centro.w / 2 == pytest.approx(secondo_centro.x + secondo_centro.w / 2)


@pytest.mark.unit
def test_etichette_esterne_una_per_carico_fuori_dal_pannello() -> None:
    """Correzione P1: un'etichetta per carico (con il proprio valore P), elencata fuori dal
    pannello sul lato sinistro (mai sul contorno), a livelli verticali distinti."""
    inputs = PavimentoIndustrialeInput.model_validate(TOOL.example)
    sketch = disegna(inputs, _L_MM_ESEMPIO)
    etichette = [f for f in sketch.viste[0].forme if f.kind == "label"]
    assert len(etichette) == len(TOOL.example["carichi"])
    for etichetta, riga in zip(etichette, TOOL.example["carichi"], strict=True):
        assert etichetta.testo.startswith(riga["caso"])
        assert f"{riga['p_kN']:.0f}" in etichetta.testo
        assert etichetta.punto[0] < -inputs.a_contrazione_m / 2  # fuori dal pannello, a sinistra
    livelli_y = {e.punto[1] for e in etichette}
    assert len(livelli_y) == len(etichette)  # ogni etichetta a un livello verticale distinto


@pytest.mark.unit
def test_impronta_ha_dimensione_minima_visibile() -> None:
    """Correzione P1: un'impronta reale in mm (spesso una piccola frazione del pannello) è
    disegnata a una dimensione minima schematica, cosi' resta visibile."""
    modificato = {**TOOL.example, "a_contrazione_m": 40.0, "b_contrazione_m": 35.0}
    inputs = PavimentoIndustrialeInput.model_validate(modificato)
    sketch = disegna(inputs, _L_MM_ESEMPIO)
    impronte = [f for f in sketch.viste[0].forme if f.kind == "rect" and f.stile == "carico"]
    minimo_atteso = 0.03 * 40.0
    for impronta in impronte:
        assert impronta.w >= minimo_atteso - 1e-9
        assert impronta.h >= minimo_atteso - 1e-9


@pytest.mark.unit
def test_esempio_ha_schizzo_e_gira_in_meno_di_300ms() -> None:
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
    import strutture.foundations.pavimento_industriale.tool as tool_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(tool_module, "disegna_schizzo", _rompi)
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


@pytest.mark.unit
def test_modulo_schizzo_importabile_e_puro() -> None:
    assert hasattr(schizzo_module, "disegna")


# --- composizione: layout/leggibilità/sovrapposizioni su input realistici oltre l'esempio --------

_UNA_RIGA = [{"caso": "ruota", "posizione": "centro", "p_kN": 15.5, "impronta_a_mm": 500,
              "impronta_b_mm": 100, "gamma": 1.5, "psi1": 0.9}]

_CASI_COMPOSIZIONE = {
    "pannello molto stretto": {"a_contrazione_m": 24.0, "b_contrazione_m": 8.0},
    "molti carichi stessa posizione": {"carichi": [
        {"caso": f"caso {i}", "posizione": "centro", "p_kN": 10.0 + i, "impronta_a_mm": 200 + i * 10,
         "impronta_b_mm": 150, "gamma": 1.5, "psi1": 0.9} for i in range(8)
    ]},
    "pannello piccolo": {"a_contrazione_m": 4.0, "b_contrazione_m": 3.5, "carichi": _UNA_RIGA},
}


@pytest.mark.unit
@pytest.mark.parametrize("nome", list(_CASI_COMPOSIZIONE))
def test_composizione_su_input_realistici(nome: str) -> None:
    modificato = {**TOOL.example, **_CASI_COMPOSIZIONE[nome]}
    inputs = PavimentoIndustrialeInput.model_validate(modificato)
    sketch = disegna(inputs, _l_mm(inputs))
    problemi = layout_problems(sketch) + readability_problems(sketch) + overlap_problems(sketch)
    assert problemi == [], f"{nome}: {problemi}"
