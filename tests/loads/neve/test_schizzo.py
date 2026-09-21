"""Live sketches for `neve-carico-falda` and `neve-accumulo` (docs/ui/WORKBENCH_SPEC.md §7): the
"Sezione copertura" view follows the inputs, and a drawing failure must never fail the calculation."""
import time

import pytest

from strutture.loads.neve import schizzo as schizzo_module
from strutture.loads.neve.models import AccumuloInput, AccumuloOutput, CaricoFaldaInput, CaricoFaldaOutput
from strutture.loads.neve.schizzo import disegna_accumulo, disegna_carico_falda
from strutture.loads.neve.tool import TOOLS, run_accumulo, run_carico_falda
from strutture.shared.tool import execute

TOOL_FALDA = next(t for t in TOOLS if t.name == "neve-carico-falda")
TOOL_ACCUMULO = next(t for t in TOOLS if t.name == "neve-accumulo")


def _output_falda(overrides: dict) -> tuple[CaricoFaldaInput, CaricoFaldaOutput]:
    inputs = CaricoFaldaInput.model_validate({**TOOL_FALDA.example, **overrides})
    report = run_carico_falda(inputs)
    assert report.ok, report.errors
    return inputs, report.data


def _output_accumulo(overrides: dict) -> tuple[AccumuloInput, AccumuloOutput]:
    inputs = AccumuloInput.model_validate({**TOOL_ACCUMULO.example, **overrides})
    report = run_accumulo(inputs)
    assert report.ok, report.errors
    return inputs, report.data


@pytest.mark.unit
def test_falda_esempio_una_falda_disegna_una_sola_falda() -> None:
    """L'esempio ha `tipo_copertura="Copertura ad una falda"` (con a1/parapetto1/a2/parapetto2
    comunque presenti): solo la falda singola deve comparire."""
    inputs, output = _output_falda({})
    assert output.qs is not None and output.qs1 is None and output.qs2 is None
    sketch = disegna_carico_falda(inputs, output)
    assert [v.titolo for v in sketch.viste] == ["Sezione copertura"]
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds.count("line") == 1
    assert kinds.count("diagram") == 1


@pytest.mark.unit
def test_falda_due_falde_disegna_entrambe_le_falde() -> None:
    """Stesso set di campi dell'esempio, ma con `tipo_copertura="Copertura a due falde"`: ora
    devono comparire le due falde, non quella singola."""
    inputs, output = _output_falda({"tipo_copertura": "Copertura a due falde"})
    assert output.qs is None and output.qs1 is not None and output.qs2 is not None
    sketch = disegna_carico_falda(inputs, output)
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds.count("line") == 2
    assert kinds.count("diagram") == 2


@pytest.mark.unit
def test_falda_legacy_compat_disegna_entrambi_i_blocchi_insieme() -> None:
    """Sotto `legacy_compat=True` il foglio valorizza sempre entrambi i blocchi: lo schizzo li
    disegna entrambi nella stessa vista, senza scartarne uno."""
    inputs, output = _output_falda({"legacy_compat": True})
    assert output.qs is not None and output.qs1 is not None and output.qs2 is not None
    sketch = disegna_carico_falda(inputs, output)
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds.count("line") == 3
    assert kinds.count("diagram") == 3


@pytest.mark.unit
def test_falda_diagramma_riporta_qs_e_usa_la_virgola_decimale() -> None:
    inputs, output = _output_falda({})
    sketch = disegna_carico_falda(inputs, output)
    diagramma = next(f for f in sketch.viste[0].forme if f.kind == "diagram")
    assert diagramma.valori == pytest.approx((output.qs, output.qs))
    assert diagramma.etichette[0].startswith("q_s =")

    etichetta = next(f for f in sketch.viste[0].forme if f.kind == "label")
    assert etichetta.simbolo == "μ·q_sk"
    assert "," in etichetta.testo
    assert "." not in etichetta.testo


@pytest.mark.unit
def test_accumulo_vista_e_forme_esempio() -> None:
    inputs, output = _output_accumulo({})
    sketch = disegna_accumulo(inputs, output)
    assert [v.titolo for v in sketch.viste] == ["Sezione copertura"]
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds[0] == "rect"
    assert "line" in kinds
    assert "polygon" in kinds
    assert "dimension" in kinds
    assert "label" in kinds


@pytest.mark.unit
def test_accumulo_geometria_segue_h() -> None:
    """Cambiando `h` cambia l'altezza del muro disegnato e la quota `l_s` (dipende da `h`)."""
    inputs_a, output_a = _output_accumulo({"h": 6.0})
    inputs_b, output_b = _output_accumulo({"h": 12.0})
    sketch_a = disegna_accumulo(inputs_a, output_a)
    sketch_b = disegna_accumulo(inputs_b, output_b)

    muro_a = sketch_a.viste[0].forme[0]
    muro_b = sketch_b.viste[0].forme[0]
    assert muro_a.kind == "rect" and muro_b.kind == "rect"
    assert muro_a.h == pytest.approx(6.0)
    assert muro_b.h == pytest.approx(12.0)

    quota_a = next(f for f in sketch_a.viste[0].forme if f.kind == "dimension")
    quota_b = next(f for f in sketch_b.viste[0].forme if f.kind == "dimension")
    assert quota_a.testo != quota_b.testo
    assert output_a.ls_final != pytest.approx(output_b.ls_final)


@pytest.mark.unit
def test_accumulo_geometria_segue_b2() -> None:
    """Cambiando `b2` cambia la lunghezza della falda inferiore disegnata."""
    inputs_a, output_a = _output_accumulo({"b2": 20.0})
    inputs_b, output_b = _output_accumulo({"b2": 40.0})
    sketch_a = disegna_accumulo(inputs_a, output_a)
    sketch_b = disegna_accumulo(inputs_b, output_b)

    tetto_a = next(f for f in sketch_a.viste[0].forme if f.kind == "line")
    tetto_b = next(f for f in sketch_b.viste[0].forme if f.kind == "line")
    assert tetto_a.p2 != tetto_b.p2
    assert tetto_a.p2[0] == pytest.approx(schizzo_module.LARGHEZZA_MURO_M + 20.0)
    assert tetto_b.p2[0] == pytest.approx(schizzo_module.LARGHEZZA_MURO_M + 40.0)


@pytest.mark.unit
def test_accumulo_poligono_e_quota_riportano_ls_final() -> None:
    inputs, output = _output_accumulo({})
    sketch = disegna_accumulo(inputs, output)
    poligono = next(f for f in sketch.viste[0].forme if f.kind == "polygon")
    assert poligono.punti[-1][0] == pytest.approx(schizzo_module.LARGHEZZA_MURO_M + output.ls_final)

    quota = next(f for f in sketch.viste[0].forme if f.kind == "dimension")
    assert quota.testo == f"l_s = {output.ls_final:.2f} m".replace(".", ",")

    etichetta = next(f for f in sketch.viste[0].forme if f.kind == "label")
    assert etichetta.simbolo == "q_s2"


@pytest.mark.unit
def test_esempio_falda_ha_schizzo_e_gira_in_meno_di_300ms() -> None:
    inizio = time.perf_counter()
    report = execute(TOOL_FALDA, TOOL_FALDA.example)
    durata = time.perf_counter() - inizio
    assert report.ok, report.errors
    assert report.data.schizzo is not None
    assert len(report.data.schizzo.viste) == 1
    assert durata < 0.3, f"esempio in {durata:.3f}s"


@pytest.mark.unit
def test_esempio_accumulo_ha_schizzo_e_gira_in_meno_di_300ms() -> None:
    inizio = time.perf_counter()
    report = execute(TOOL_ACCUMULO, TOOL_ACCUMULO.example)
    durata = time.perf_counter() - inizio
    assert report.ok, report.errors
    assert report.data.schizzo is not None
    assert len(report.data.schizzo.viste) == 1
    assert durata < 0.3, f"esempio in {durata:.3f}s"


@pytest.mark.unit
def test_errore_nel_disegno_falda_non_fa_fallire_il_calcolo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un'eccezione nello schizzo deve essere loggata e assorbita: il calcolo resta valido."""
    import strutture.loads.neve.tool as tool_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(tool_module, "disegna_schizzo_falda", _rompi)
    report = execute(TOOL_FALDA, TOOL_FALDA.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


@pytest.mark.unit
def test_errore_nel_disegno_accumulo_non_fa_fallire_il_calcolo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un'eccezione nello schizzo deve essere loggata e assorbita: il calcolo resta valido."""
    import strutture.loads.neve.tool as tool_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(tool_module, "disegna_schizzo_accumulo", _rompi)
    report = execute(TOOL_ACCUMULO, TOOL_ACCUMULO.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


@pytest.mark.unit
def test_modulo_schizzo_importabile_e_puro() -> None:
    """Il modulo non tocca I/O: verifica solo che sia importabile senza effetti collaterali."""
    assert hasattr(schizzo_module, "disegna_carico_falda")
    assert hasattr(schizzo_module, "disegna_accumulo")
