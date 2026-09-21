"""Live sketch for `pilastro-rettangolare`/`pilastro-circolare` (docs/ui/WORKBENCH_SPEC.md §7):
the "Sezione" view follows the inputs, and a drawing failure must never fail the calculation."""
import time

import pytest

from strutture.members.ca_pilastri import schizzo as schizzo_module
from strutture.members.ca_pilastri.models import PilastroCircolareInput, PilastroRettangolareInput
from strutture.members.ca_pilastri.schizzo import disegna_circolare, disegna_rettangolare
from strutture.members.ca_pilastri.tool import TOOLS
from strutture.shared.tool import execute

TOOL_RETT = next(t for t in TOOLS if t.name == "ca-pilastro-rettangolare")
TOOL_CIRC = next(t for t in TOOLS if t.name == "ca-pilastro-circolare")


@pytest.mark.unit
def test_rettangolare_vista_titolo_e_forme() -> None:
    inputs = PilastroRettangolareInput.model_validate(TOOL_RETT.example)
    sketch = disegna_rettangolare(inputs)
    assert [v.titolo for v in sketch.viste] == ["Sezione"]
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds[0] == "rect"
    assert "polygon" in kinds
    assert "bars" in kinds
    assert kinds.count("dimension") == 2


@pytest.mark.unit
def test_rettangolare_rettangolo_e_quote_seguono_gli_input() -> None:
    inputs = PilastroRettangolareInput.model_validate(TOOL_RETT.example)
    sketch = disegna_rettangolare(inputs)
    rettangolo = sketch.viste[0].forme[0]
    assert rettangolo.w == pytest.approx(inputs.l1_mm / 1000.0)
    assert rettangolo.h == pytest.approx(inputs.l2_mm / 1000.0)
    quote = [f for f in sketch.viste[0].forme if f.kind == "dimension"]
    assert quote[0].testo == "L_1 = 400 mm"
    assert quote[1].testo == "L_2 = 400 mm"


@pytest.mark.unit
def test_rettangolare_barre_al_perimetro_conteggio_e_diametro_vero() -> None:
    inputs = PilastroRettangolareInput.model_validate(TOOL_RETT.example)
    sketch = disegna_rettangolare(inputs)
    barre = next(f for f in sketch.viste[0].forme if f.kind == "bars")
    assert len(barre.centri) == inputs.n_ferri
    assert barre.diametro == pytest.approx(inputs.diametro_ferri_mm / 1000.0)


@pytest.mark.unit
def test_rettangolare_geometria_segue_una_dimensione_modificata() -> None:
    modificato = {**TOOL_RETT.example, "l1_mm": 600}
    inputs = PilastroRettangolareInput.model_validate(modificato)
    sketch = disegna_rettangolare(inputs)
    rettangolo = sketch.viste[0].forme[0]
    quota_l1 = next(f for f in sketch.viste[0].forme if f.kind == "dimension")
    assert rettangolo.w == pytest.approx(0.6)
    assert quota_l1.testo == "L_1 = 600 mm"


@pytest.mark.unit
def test_circolare_vista_titolo_e_forme() -> None:
    inputs = PilastroCircolareInput.model_validate(TOOL_CIRC.example)
    sketch = disegna_circolare(inputs)
    assert [v.titolo for v in sketch.viste] == ["Sezione"]
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds.count("circle") == 2
    assert "bars" in kinds
    assert "dimension" in kinds


@pytest.mark.unit
def test_circolare_cerchio_barre_e_quota_seguono_gli_input() -> None:
    inputs = PilastroCircolareInput.model_validate(TOOL_CIRC.example)
    sketch = disegna_circolare(inputs)
    cerchio_cls = next(f for f in sketch.viste[0].forme if f.kind == "circle")
    assert cerchio_cls.r == pytest.approx(inputs.d_mm / 2000.0)
    barre = next(f for f in sketch.viste[0].forme if f.kind == "bars")
    assert len(barre.centri) == inputs.n_ferri
    assert barre.diametro == pytest.approx(inputs.diametro_ferri_mm / 1000.0)
    quota_d = next(f for f in sketch.viste[0].forme if f.kind == "dimension")
    assert quota_d.testo == "D = 400 mm"


@pytest.mark.unit
def test_circolare_geometria_segue_una_dimensione_modificata() -> None:
    modificato = {**TOOL_CIRC.example, "d_mm": 500}
    inputs = PilastroCircolareInput.model_validate(modificato)
    sketch = disegna_circolare(inputs)
    cerchio_cls = next(f for f in sketch.viste[0].forme if f.kind == "circle")
    quota_d = next(f for f in sketch.viste[0].forme if f.kind == "dimension")
    assert cerchio_cls.r == pytest.approx(0.25)
    assert quota_d.testo == "D = 500 mm"


@pytest.mark.unit
def test_esempi_hanno_schizzo_e_girano_veloce() -> None:
    for tool in (TOOL_RETT, TOOL_CIRC):
        inizio = time.perf_counter()
        report = execute(tool, tool.example)
        durata = time.perf_counter() - inizio
        assert report.ok, report.errors
        assert report.data.schizzo is not None
        assert len(report.data.schizzo.viste) == 1
        assert durata < 0.3, f"{tool.name} in {durata:.3f}s"


@pytest.mark.unit
def test_errore_nel_disegno_non_fa_fallire_il_calcolo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un'eccezione nello schizzo deve essere loggata e assorbita: il calcolo resta valido."""
    import strutture.members.ca_pilastri.tool_circolare as circolare_module
    import strutture.members.ca_pilastri.tool_rettangolare as rettangolare_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(rettangolare_module, "disegna_schizzo", _rompi)
    monkeypatch.setattr(circolare_module, "disegna_schizzo", _rompi)
    for tool in (TOOL_RETT, TOOL_CIRC):
        report = execute(tool, tool.example)
        assert report.ok, report.errors
        assert report.data.schizzo is None


@pytest.mark.unit
def test_modulo_schizzo_importabile_e_puro() -> None:
    assert hasattr(schizzo_module, "disegna_rettangolare")
    assert hasattr(schizzo_module, "disegna_circolare")
