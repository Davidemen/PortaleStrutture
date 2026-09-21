"""Live sketch for `muro-sostegno` (docs/ui/WORKBENCH_SPEC.md §7): the section follows the
inputs, and a drawing failure must never fail the calculation."""
import sys
import time
from pathlib import Path

import pytest

from strutture.members.muro.models import MuroSostegnoInput
from strutture.members.muro.tool import TOOLS
from strutture.shared.tool import execute

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from test_sketch_layout import layout_problems, overlap_problems, readability_problems

TOOL = TOOLS[0]


@pytest.mark.unit
def test_vista_titolo_e_forme_esempio() -> None:
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    sketch = report.data.schizzo
    assert sketch is not None
    assert [v.titolo for v in sketch.viste] == ["Sezione"]
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds[0] == "rect"  # fondazione
    assert kinds.count("polygon") == 2  # paramento + terreno di riporto
    assert kinds.count("diagram") == 2  # pressioni di base + banda del sovraccarico
    assert kinds.count("dimension") == 2  # B, H
    assert kinds.count("arrow") == 2  # spinte statica/sismica (il sovraccarico non è più una freccia)
    assert kinds.count("label") == 2  # valore di S_stat/S_sism, ancorato alla coda di ciascuna freccia


@pytest.mark.unit
def test_fondazione_e_quote_seguono_gli_input() -> None:
    inputs = MuroSostegnoInput.model_validate(TOOL.example)
    report = execute(TOOL, TOOL.example)
    forme = report.data.schizzo.viste[0].forme
    fondazione = forme[0]
    b_fond = inputs.b_valle_m + inputs.s_base_m + inputs.b_monte_m
    assert fondazione.w == pytest.approx(b_fond)
    assert fondazione.h == pytest.approx(inputs.s_fond_m)

    quota_b = next(f for f in forme if f.kind == "dimension" and f.testo.startswith("B ="))
    quota_h = next(f for f in forme if f.kind == "dimension" and f.testo.startswith("H ="))
    assert quota_b.testo == f"B = {b_fond:.2f} m".replace(".", ",")
    h_tot = inputs.h_muro_m + inputs.s_fond_m
    assert quota_h.testo == f"H = {h_tot:.2f} m".replace(".", ",")


@pytest.mark.unit
def test_geometria_segue_una_dimensione_modificata() -> None:
    """Cambiando b_monte_m la fondazione e la quota B cambiano di conseguenza."""
    inputs_base = MuroSostegnoInput.model_validate(TOOL.example)
    modificato = {**TOOL.example, "b_monte_m": inputs_base.b_monte_m + 1.0}
    report = execute(TOOL, modificato)
    assert report.ok, report.errors
    fondazione = report.data.schizzo.viste[0].forme[0]
    b_fond_atteso = inputs_base.b_valle_m + inputs_base.s_base_m + inputs_base.b_monte_m + 1.0
    assert fondazione.w == pytest.approx(b_fond_atteso)
    quota_b = next(f for f in report.data.schizzo.viste[0].forme if f.kind == "dimension" and f.testo.startswith("B ="))
    assert quota_b.testo == f"B = {b_fond_atteso:.2f} m".replace(".", ",")


@pytest.mark.unit
def test_sovraccarico_assente_quando_q_zero() -> None:
    """Il sovraccarico è una `Diagramma` stile "carico" (non una freccia): senza sovraccarico deve
    sparire, restando solo il diagramma delle pressioni di base (stile "pressione")."""
    modificato = {**TOOL.example, "q_kN_m2": 0.0}
    report = execute(TOOL, modificato)
    assert report.ok, report.errors
    diagrammi = [f for f in report.data.schizzo.viste[0].forme if f.kind == "diagram"]
    assert len(diagrammi) == 1
    assert diagrammi[0].stile == "pressione"


@pytest.mark.unit
def test_sovraccarico_e_banda_con_un_solo_valore_etichettato() -> None:
    """Il sovraccarico q è uniforme: una sola etichetta (valore, il simbolo "q" è nel testo perché
    `Diagramma` non separa simbolo/valore come `Etichetta`), l'altro capo resta senza testo."""
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    sovraccarico = next(f for f in report.data.schizzo.viste[0].forme if f.kind == "diagram" and f.stile == "carico")
    assert sovraccarico.valori[0] == pytest.approx(sovraccarico.valori[1])  # banda uniforme
    assert sovraccarico.etichette[0].startswith("q =")
    assert sovraccarico.etichette[1] == ""
    # sinistra -> destra: la banda sporge verso l'alto (sopra il rinterro), non verso il basso.
    assert sovraccarico.base[0][0] < sovraccarico.base[1][0]


@pytest.mark.unit
def test_frecce_spinta_hanno_etichetta_separata_ancorata_alla_coda() -> None:
    """Correzione P1: il testo della spinta non è più incorporato nella `Freccia` (poteva cadere
    sul paramento a seconda di come il renderer posiziona il testo di una freccia) ma un `Etichetta`
    a sé, ancorata (`ancora="start"`) alla coda, sul lato libero del cuneo di terreno."""
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    forme = report.data.schizzo.viste[0].forme
    frecce_spinta = [f for f in forme if f.kind == "arrow"]
    assert all(f.testo == "" for f in frecce_spinta)
    etichette_spinta = [f for f in forme if f.kind == "label" and f.simbolo in ("S_stat", "S_sism")]
    assert len(etichette_spinta) == 2
    for etichetta, freccia in zip(etichette_spinta, frecce_spinta, strict=True):
        assert etichetta.ancora == "start"
        assert etichetta.punto == freccia.coda
        assert not etichetta.testo.startswith(etichetta.simbolo)  # testo = solo valore


@pytest.mark.unit
def test_diagramma_pressioni_riporta_p_valle_e_p_monte() -> None:
    """`base` va da x=B (monte, destra) a x=0 (valle, sinistra): `valori`/`etichette` devono seguire
    lo stesso ordine (monte poi valle), altrimenti il diagramma risulta specchiato (bug P0 della
    revisione di design: il picco compariva sotto il tacco invece che sotto la punta)."""
    report = execute(TOOL, TOOL.example)
    diagramma = next(f for f in report.data.schizzo.viste[0].forme if f.kind == "diagram" and f.stile == "pressione")
    governante = max(report.data.pressioni_terreno, key=lambda p: max(p.p_valle_kPa, p.p_monte_kPa))
    assert diagramma.base[0][0] > diagramma.base[1][0]  # base[0] è il lato monte (x=B, destra)
    assert diagramma.valori == pytest.approx((governante.p_monte_kPa, governante.p_valle_kPa))
    # l'ordinata più grande deve stare dal lato di x corrispondente alla pressione più grande.
    lato_monte_x, lato_valle_x = diagramma.base[0][0], diagramma.base[1][0]
    valore_al_monte, _valore_alla_valle = diagramma.valori
    if governante.p_monte_kPa >= governante.p_valle_kPa:
        assert valore_al_monte == pytest.approx(max(governante.p_monte_kPa, governante.p_valle_kPa))
    assert lato_monte_x > lato_valle_x
    # capi a pressione nulla restano senza etichetta.
    if governante.p_monte_kPa <= 0:
        assert diagramma.etichette[0] == ""
    else:
        assert diagramma.etichette[0].startswith("p_monte =")
    if governante.p_valle_kPa <= 0:
        assert diagramma.etichette[1] == ""
    else:
        assert diagramma.etichette[1].startswith("p_valle =")


@pytest.mark.unit
def test_esempio_ha_schizzo_e_gira_in_meno_di_300ms() -> None:
    inizio = time.perf_counter()
    report = execute(TOOL, TOOL.example)
    durata = time.perf_counter() - inizio
    assert report.ok, report.errors
    assert report.data.schizzo is not None
    assert durata < 0.3, f"esempio in {durata:.3f}s"


@pytest.mark.unit
def test_spinta_assente_restituisce_none() -> None:
    """`_spinta` con una lista vuota (nessuna combinazione con quel nome) non deve rompersi."""
    from strutture.members.muro.schizzo import _spinta

    assert _spinta("STR_1", (), ()) is None


@pytest.mark.unit
def test_errore_nel_disegno_non_fa_fallire_il_calcolo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un'eccezione nello schizzo deve essere loggata e assorbita: il calcolo resta valido."""
    import strutture.members.muro.tool as tool_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(tool_module, "disegna_schizzo", _rompi)
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


# --- composizione: layout/leggibilità/sovrapposizioni su input realistici oltre l'esempio --------

_CASI_COMPOSIZIONE = {
    "muro alto": {"h_muro_m": 4.0, "b_valle_m": 0.5, "b_monte_m": 2.2, "s_base_m": 0.8},
    "sovraccarico elevato": {"q_kN_m2": 20.0},
    "fondazione larga": {"b_valle_m": 1.5, "b_monte_m": 3.0},
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
