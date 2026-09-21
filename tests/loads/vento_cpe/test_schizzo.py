"""Live sketch for `vento-cpe-rettangolare` (docs/ui/WORKBENCH_SPEC.md §7, COMPOSITION RULES in
shared/sketch.py): two Vista, one per wind direction, follow the inputs, stay readable across
several realistic plans, and a drawing failure must never fail the calculation."""
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from test_sketch_layout import layout_problems, overlap_problems, readability_problems

from strutture.loads.vento_cpe import schizzo as schizzo_module
from strutture.loads.vento_cpe.cpe_leeward import cpe_leeward
from strutture.loads.vento_cpe.cpe_side import cpe_side
from strutture.loads.vento_cpe.cpe_windward import cpe_windward
from strutture.loads.vento_cpe.hd_ratio import hd_ratio
from strutture.loads.vento_cpe.models import DirectionResult, VentoCpeInput
from strutture.loads.vento_cpe.schizzo import disegna
from strutture.loads.vento_cpe.tool import TOOLS
from strutture.shared.tool import execute

TOOL = TOOLS[0]


def _direction(h: float, d: float) -> DirectionResult:
    hd = hd_ratio(h, d)
    return DirectionResult(h_d=hd, cpe_windward=cpe_windward(hd), cpe_side=cpe_side(hd), cpe_leeward=cpe_leeward(hd))


def _dirs(inputs: dict) -> tuple[DirectionResult, DirectionResult]:
    return _direction(inputs["h"], inputs["d"]), _direction(inputs["h"], inputs["b"])


@pytest.mark.unit
def test_viste_titoli_e_forme_esempio() -> None:
    """Esempio: h/d=0.6 e h/b=0.75, entrambi <=5 -> tutti i cpe definiti in entrambe le direzioni."""
    inputs = VentoCpeInput.model_validate(TOOL.example)
    dir1, dir2 = _dirs(TOOL.example)
    sketch = disegna(inputs, dir1, dir2)

    assert [v.titolo for v in sketch.viste] == ["Pianta — direzione 1", "Pianta — direzione 2"]
    for vista in sketch.viste:
        kinds = [f.kind for f in vista.forme]
        assert kinds.count("rect") == 1
        assert kinds.count("arrow") == 1
        assert kinds.count("label") == 4  # sopravento + 2 laterali + sottovento
        assert kinds.count("dimension") == 2


@pytest.mark.unit
def test_pianta_rettangolo_segue_gli_input() -> None:
    inputs = VentoCpeInput.model_validate(TOOL.example)
    dir1, dir2 = _dirs(TOOL.example)
    sketch = disegna(inputs, dir1, dir2)
    for vista in sketch.viste:
        rettangolo = next(f for f in vista.forme if f.kind == "rect")
        assert rettangolo.x == pytest.approx(0.0)
        assert rettangolo.y == pytest.approx(0.0)
        assert rettangolo.w == pytest.approx(inputs.b)
        assert rettangolo.h == pytest.approx(inputs.d)


@pytest.mark.unit
def test_geometria_e_quota_b_seguono_una_dimensione_modificata() -> None:
    """Cambiando b il rettangolo e la quota 'b' cambiano di conseguenza in ENTRAMBE le viste."""
    modificato = {**TOOL.example, "b": 20.0}
    inputs = VentoCpeInput.model_validate(modificato)
    dir1, dir2 = _dirs(modificato)
    sketch = disegna(inputs, dir1, dir2)
    for vista in sketch.viste:
        rettangolo = next(f for f in vista.forme if f.kind == "rect")
        assert rettangolo.w == pytest.approx(20.0)
        quota_b = next(f for f in vista.forme if f.kind == "dimension" and f.testo.startswith("b ="))
        assert quota_b.testo == "b = 20,00 m"


@pytest.mark.unit
def test_meno_facce_definite_quando_hd_supera_cinque() -> None:
    """h/d>5 (direzione 1): tutti i cpe di dir1 sono None ("ND") -> la vista 1 perde le etichette.
    b e' allargata cosi' che h/b resti <=5 e la direzione 2 mantenga le sue etichette."""
    modificato = {**TOOL.example, "h": 100.0, "d": 10.0, "b": 50.0}
    inputs = VentoCpeInput.model_validate(modificato)
    dir1, dir2 = _dirs(modificato)
    assert dir1.h_d > 5.0
    assert dir1.cpe_windward is None and dir1.cpe_side is None and dir1.cpe_leeward is None
    assert dir2.h_d <= 5.0

    sketch = disegna(inputs, dir1, dir2)
    vista1, vista2 = sketch.viste
    assert sum(1 for f in vista1.forme if f.kind == "label") == 0
    # la geometria resta disegnata, solo le etichette del cpe spariscono
    assert any(f.kind == "rect" for f in vista1.forme)
    assert any(f.kind == "arrow" for f in vista1.forme)
    assert sum(1 for f in vista2.forme if f.kind == "label") == 4


@pytest.mark.unit
def test_etichette_c_pe_riportano_il_simbolo_e_il_valore_giusti() -> None:
    inputs = VentoCpeInput.model_validate(TOOL.example)
    dir1, dir2 = _dirs(TOOL.example)
    sketch = disegna(inputs, dir1, dir2)
    etichette = [f for f in sketch.viste[0].forme if f.kind == "label"]
    simboli = sorted(e.simbolo for e in etichette)
    assert simboli == ["c_pe,l", "c_pe,l", "c_pe,s", "c_pe,w"]
    windward = next(e for e in etichette if e.simbolo == "c_pe,w")
    # regola 4 (COMPOSITION RULES): con `simbolo` impostato, `testo` è solo il valore.
    assert windward.testo == f"{dir1.cpe_windward:.2f}".replace(".", ",")
    assert not windward.testo.startswith("c_pe")
    assert not windward.testo.endswith(" ")  # cpe è adimensionale: nessuna unità in coda


@pytest.mark.unit
def test_pianta_molto_allungata_e_compressa_ma_la_quota_resta_vera() -> None:
    """b/d=4: oltre l'aspetto massimo leggibile, il lato maggiore viene compresso nel disegno ma
    la quota riporta sempre il valore vero di b."""
    modificato = {**TOOL.example, "b": 40.0, "d": 10.0}
    inputs = VentoCpeInput.model_validate(modificato)
    dir1, dir2 = _dirs(modificato)
    sketch = disegna(inputs, dir1, dir2)
    rettangolo = next(f for f in sketch.viste[0].forme if f.kind == "rect")
    assert rettangolo.w < 40.0  # disegnato compresso
    quota_b = next(f for f in sketch.viste[0].forme if f.kind == "dimension" and f.testo.startswith("b ="))
    assert quota_b.testo == "b = 40,00 m"  # ma la quota riporta il valore vero
    assert sketch.nota != ""


@pytest.mark.unit
@pytest.mark.parametrize(
    "overrides",
    [
        {},  # esempio
        {"b": 40.0, "d": 10.0, "h": 8.0},  # pianta molto allungata, b/d=4
        {"b": 10.0, "d": 40.0, "h": 8.0},  # allungata nell'altra direzione, d/b=4
        {"b": 100.0, "d": 5.0, "h": 8.0},  # allungamento estremo
        {"h": 100.0, "d": 10.0, "b": 50.0},  # h/d>5: etichette assenti in una direzione
        {"b": 5.0, "d": 5.0, "h": 5.0},  # pianta quadrata
    ],
)
def test_piante_realistiche_non_hanno_problemi_di_layout(overrides: dict) -> None:
    modificato = {**TOOL.example, **overrides}
    inputs = VentoCpeInput.model_validate(modificato)
    dir1, dir2 = _dirs(modificato)
    sketch = disegna(inputs, dir1, dir2)
    problems = layout_problems(sketch) + readability_problems(sketch) + overlap_problems(sketch)
    assert problems == [], problems


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
    import strutture.loads.vento_cpe.tool as tool_module

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
