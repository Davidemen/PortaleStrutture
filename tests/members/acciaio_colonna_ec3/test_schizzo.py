"""Live sketch for `acciaio-colonna-h-ec3` (docs/ui/WORKBENCH_SPEC.md §7): the "Sezione" view
follows the inputs, and a drawing failure must never fail the calculation."""
import time

import pytest

from strutture.members.acciaio_colonna_ec3 import schizzo as schizzo_module
from strutture.members.acciaio_colonna_ec3.models import ColonnaEc3Input
from strutture.members.acciaio_colonna_ec3.schizzo import disegna
from strutture.members.acciaio_colonna_ec3.tool import TOOLS
from strutture.shared.tool import execute

TOOL = TOOLS[0]


@pytest.mark.unit
def test_vista_titolo_e_forme_esempio() -> None:
    inputs = ColonnaEc3Input.model_validate(TOOL.example)
    sketch = disegna(inputs)

    assert [v.titolo for v in sketch.viste] == ["Sezione"]
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds.count("rect") == 3
    assert kinds.count("line") == 2
    assert kinds.count("dimension") == 4
    assert kinds.count("label") == 2


@pytest.mark.unit
def test_ali_e_anima_seguono_gli_input() -> None:
    inputs = ColonnaEc3Input.model_validate(TOOL.example)
    sketch = disegna(inputs)
    rettangoli = [f for f in sketch.viste[0].forme if f.kind == "rect"]
    ala_superiore, ala_inferiore, anima = rettangoli

    b_m, h_m = inputs.b_mm / 1000.0, inputs.h_mm / 1000.0
    tw_m, tf_m = inputs.tw_mm / 1000.0, inputs.tf_mm / 1000.0

    assert ala_superiore.x == pytest.approx(-b_m / 2)
    assert ala_superiore.y == pytest.approx(h_m / 2 - tf_m)
    assert ala_superiore.w == pytest.approx(b_m)
    assert ala_superiore.h == pytest.approx(tf_m)

    assert ala_inferiore.x == pytest.approx(-b_m / 2)
    assert ala_inferiore.y == pytest.approx(-h_m / 2)
    assert ala_inferiore.w == pytest.approx(b_m)
    assert ala_inferiore.h == pytest.approx(tf_m)

    assert anima.x == pytest.approx(-tw_m / 2)
    assert anima.y == pytest.approx(-h_m / 2 + tf_m)
    assert anima.w == pytest.approx(tw_m)
    assert anima.h == pytest.approx(h_m - 2 * tf_m)


@pytest.mark.unit
def test_assi_yy_zz_con_etichette() -> None:
    inputs = ColonnaEc3Input.model_validate(TOOL.example)
    sketch = disegna(inputs)
    linee = [f for f in sketch.viste[0].forme if f.kind == "line"]
    etichette = [f for f in sketch.viste[0].forme if f.kind == "label"]

    assert {e.simbolo for e in etichette} == {"y", "z"}
    for linea in linee:
        assert linea.stile == "asse"
    for etichetta in etichette:
        assert etichetta.stile == "asse"
        assert etichetta.ancora == "start"

    asse_yy = next(l for l in linee if l.p1[1] == pytest.approx(0.0) and l.p2[1] == pytest.approx(0.0))
    assert asse_yy.p1[0] == pytest.approx(-asse_yy.p2[0])
    asse_zz = next(l for l in linee if l.p1[0] == pytest.approx(0.0) and l.p2[0] == pytest.approx(0.0))
    assert asse_zz.p1[1] == pytest.approx(-asse_zz.p2[1])


@pytest.mark.unit
def test_geometria_segue_una_dimensione_modificata() -> None:
    """Cambiando h_mm le ali, l'anima e la quota h cambiano di conseguenza."""
    modificato = {**TOOL.example, "h_mm": 700}
    inputs = ColonnaEc3Input.model_validate(modificato)
    sketch = disegna(inputs)
    rettangoli = [f for f in sketch.viste[0].forme if f.kind == "rect"]
    ala_superiore, ala_inferiore, anima = rettangoli
    h_m, tf_m = 700 / 1000.0, inputs.tf_mm / 1000.0

    assert ala_superiore.y == pytest.approx(h_m / 2 - tf_m)
    assert ala_inferiore.y == pytest.approx(-h_m / 2)
    assert anima.h == pytest.approx(h_m - 2 * tf_m)

    quote = [f for f in sketch.viste[0].forme if f.kind == "dimension"]
    quota_h = next(q for q in quote if q.testo.startswith("h ="))
    assert quota_h.testo == "h = 700 mm"


@pytest.mark.unit
def test_quote_riportano_i_valori_corretti() -> None:
    inputs = ColonnaEc3Input.model_validate(TOOL.example)
    sketch = disegna(inputs)
    quote = {q.testo.split(" =")[0]: q.testo for q in sketch.viste[0].forme if q.kind == "dimension"}
    assert quote["h"] == "h = 500 mm"
    assert quote["b"] == "b = 280 mm"
    assert quote["t_f"] == "t_f = 12 mm"
    assert quote["t_w"] == "t_w = 8 mm"


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
    import strutture.members.acciaio_colonna_ec3.tool as tool_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(tool_module, "disegna_schizzo", _rompi)
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


@pytest.mark.unit
def test_modulo_schizzo_importabile_e_puro() -> None:
    assert hasattr(schizzo_module, "disegna")
