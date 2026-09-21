"""Live sketch for `fond-trave-collegamento` (docs/ui/WORKBENCH_SPEC.md §7): Sezione follows the
inputs on both the NTC2018 and EN1998 branches, and a drawing failure must never fail the
calculation on either branch."""
import time

import pytest

from strutture.foundations.travi_collegamento import schizzo as schizzo_module
from strutture.foundations.travi_collegamento.models import TraviCollegamentoInput
from strutture.foundations.travi_collegamento.schizzo import disegna
from strutture.foundations.travi_collegamento.tool import TOOLS
from strutture.shared.tool import execute

TOOL = TOOLS[0]
_ESEMPIO_EN1998 = {
    **TOOL.example, "norma": "EN1998", "f0": None, "categoria_topografica": None,
    "ms": 5.6, "n_piani": 3, "h_mm": 450, "n_barre": 8,
}


@pytest.mark.unit
def test_vista_titolo_e_forme_esempio() -> None:
    inputs = TraviCollegamentoInput.model_validate(TOOL.example)
    sketch = disegna(inputs)

    assert [v.titolo for v in sketch.viste] == ["Sezione"]
    forme = sketch.viste[0].forme
    assert [f.kind for f in forme] == ["rect", "rect", "bars", "dimension", "dimension"]


@pytest.mark.unit
def test_sezione_rettangolo_segue_base_e_altezza() -> None:
    inputs = TraviCollegamentoInput.model_validate(TOOL.example)
    sketch = disegna(inputs)
    sezione = sketch.viste[0].forme[0]
    assert sezione.x == pytest.approx(-inputs.b_mm / 2000.0)
    assert sezione.y == pytest.approx(-inputs.h_mm / 2000.0)
    assert sezione.w == pytest.approx(inputs.b_mm / 1000.0)
    assert sezione.h == pytest.approx(inputs.h_mm / 1000.0)

    quota_b, quota_h = sketch.viste[0].forme[3], sketch.viste[0].forme[4]
    assert quota_b.testo == "B = 0,40 m"
    assert quota_h.testo == "H = 0,40 m"


@pytest.mark.unit
def test_staffa_scostata_del_copriferro() -> None:
    inputs = TraviCollegamentoInput.model_validate(TOOL.example)
    sketch = disegna(inputs)
    staffa = sketch.viste[0].forme[1]
    cf = inputs.cf_mm / 1000.0
    assert staffa.x == pytest.approx(-inputs.b_mm / 2000.0 + cf)
    assert staffa.y == pytest.approx(-inputs.h_mm / 2000.0 + cf)
    assert staffa.w == pytest.approx(inputs.b_mm / 1000.0 - 2 * cf)
    assert staffa.h == pytest.approx(inputs.h_mm / 1000.0 - 2 * cf)
    assert staffa.stile == "armatura"


@pytest.mark.unit
def test_barre_numero_e_diametro_e_dentro_la_sezione() -> None:
    inputs = TraviCollegamentoInput.model_validate(TOOL.example)
    sketch = disegna(inputs)
    barre = sketch.viste[0].forme[2]
    assert len(barre.centri) == inputs.n_barre
    assert barre.diametro == pytest.approx(inputs.phi_mm / 1000.0)

    meta_b, meta_h = inputs.b_mm / 2000.0, inputs.h_mm / 2000.0
    for x, y in barre.centri:
        assert -meta_b < x < meta_b
        assert -meta_h < y < meta_h

    inset = (inputs.cf_mm + inputs.phi_staffa_mm + inputs.phi_mm / 2.0) / 1000.0
    primo = barre.centri[0]
    assert primo == pytest.approx((meta_b - inset, meta_h - inset))


@pytest.mark.unit
def test_geometria_segue_una_dimensione_modificata() -> None:
    """Cambiando b_mm la sezione, la staffa e la relativa quota cambiano di conseguenza."""
    modificato = {**TOOL.example, "b_mm": 600}
    inputs = TraviCollegamentoInput.model_validate(modificato)
    sketch = disegna(inputs)
    sezione, staffa = sketch.viste[0].forme[0], sketch.viste[0].forme[1]
    quota_b = sketch.viste[0].forme[3]
    assert sezione.w == pytest.approx(0.6)
    assert staffa.w == pytest.approx(0.6 - 2 * inputs.cf_mm / 1000.0)
    assert quota_b.testo == "B = 0,60 m"


@pytest.mark.unit
def test_esempio_ntc2018_ha_schizzo_e_gira_in_meno_di_300ms() -> None:
    inizio = time.perf_counter()
    report = execute(TOOL, TOOL.example)
    durata = time.perf_counter() - inizio
    assert report.ok, report.errors
    assert report.data.schizzo is not None
    assert len(report.data.schizzo.viste) == 1
    assert durata < 0.3, f"esempio in {durata:.3f}s"


@pytest.mark.unit
def test_esempio_en1998_ha_schizzo() -> None:
    """Ramo EN1998, percorso di codice separato da NTC2018: deve produrre lo schizzo allo stesso modo."""
    report = execute(TOOL, _ESEMPIO_EN1998)
    assert report.ok, report.errors
    assert report.data.schizzo is not None
    assert [v.titolo for v in report.data.schizzo.viste] == ["Sezione"]


@pytest.mark.unit
def test_errore_nel_disegno_non_fa_fallire_il_calcolo_ntc(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un'eccezione nello schizzo deve essere loggata e assorbita: il calcolo NTC2018 resta valido."""
    import strutture.foundations.travi_collegamento.tool_ntc as tool_ntc_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(tool_ntc_module, "disegna_schizzo", _rompi)
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


@pytest.mark.unit
def test_errore_nel_disegno_non_fa_fallire_il_calcolo_en(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stesso guardiano sul ramo EN1998, che passa da un modulo (`tool_en`) diverso da NTC2018."""
    import strutture.foundations.travi_collegamento.tool_en as tool_en_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(tool_en_module, "disegna_schizzo", _rompi)
    report = execute(TOOL, _ESEMPIO_EN1998)
    assert report.ok, report.errors
    assert report.data.schizzo is None


@pytest.mark.unit
def test_modulo_schizzo_importabile_e_puro() -> None:
    assert hasattr(schizzo_module, "disegna")


@pytest.mark.unit
def test_punto_a_distanza_ricade_sul_fallback_con_lati_degeneri() -> None:
    """Lati di lunghezza nulla (rettangolo degenere) non soddisfano mai la condizione del ciclo:
    la funzione deve ricadere sull'ultimo estremo invece di sollevare un'eccezione."""
    lati = (((0.0, 0.0), (0.0, 0.0), 0.0),)
    assert schizzo_module._punto_a_distanza(lati, 5.0) == (0.0, 0.0)
