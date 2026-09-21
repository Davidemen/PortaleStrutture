"""Live sketch for `ca-taglio-non-armato` (docs/ui/WORKBENCH_SPEC.md §7): the "Sezione" view
follows the inputs, and a drawing failure must never fail the calculation."""
import math
import time

import pytest

from strutture.members.ca_taglio_non_armato import schizzo as schizzo_module
from strutture.members.ca_taglio_non_armato.asl_from_bars import asl_from_barre_mm2
from strutture.members.ca_taglio_non_armato.effective_depth import effective_depth_mm
from strutture.members.ca_taglio_non_armato.models import GeometriaOutput, TaglioNonArmatoInput
from strutture.members.ca_taglio_non_armato.schizzo import DIAMETRO_ILLUSTRATIVO_MM, disegna
from strutture.members.ca_taglio_non_armato.tool import TOOLS
from strutture.shared.tool import execute

TOOL = TOOLS[0]


def _geometria(inputs: TaglioNonArmatoInput) -> GeometriaOutput:
    d = effective_depth_mm(inputs.h_mm, inputs.c_mm)
    asl = inputs.asl_mm2 if inputs.asl_mm2 is not None else asl_from_barre_mm2(inputs.n_barre, inputs.diametro_barre_mm)
    return GeometriaOutput(d_mm=d, asl_mm2=asl)


@pytest.mark.unit
def test_vista_titolo_e_forme_esempio() -> None:
    inputs = TaglioNonArmatoInput.model_validate(TOOL.example)
    geometria = _geometria(inputs)
    sketch = disegna(inputs, geometria)

    assert [v.titolo for v in sketch.viste] == ["Sezione"]
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds[0] == "rect"
    assert kinds.count("bars") == 1
    assert kinds.count("dimension") == 2


@pytest.mark.unit
def test_sezione_rettangolo_e_quote_seguono_gli_input() -> None:
    inputs = TaglioNonArmatoInput.model_validate(TOOL.example)
    geometria = _geometria(inputs)
    sketch = disegna(inputs, geometria)
    rettangolo = sketch.viste[0].forme[0]
    assert rettangolo.x == pytest.approx(0.0)
    assert rettangolo.y == pytest.approx(0.0)
    assert rettangolo.w == pytest.approx(inputs.bw_mm / 1000.0)
    assert rettangolo.h == pytest.approx(inputs.h_mm / 1000.0)

    quote = [f for f in sketch.viste[0].forme if f.kind == "dimension"]
    assert quote[0].testo == "b = 1000 mm"
    assert quote[1].testo == "d = 450 mm"


@pytest.mark.unit
def test_barre_esempio_usano_il_diametro_illustrativo_con_area_totale_vicina_ad_asl() -> None:
    """Esempio aureo: solo asl_mm2 e' dato (n_barre/diametro_barre_mm sono None) -> nessun
    diametro vero disponibile per il disegno, si usa il fallback illustrativo fisso."""
    inputs = TaglioNonArmatoInput.model_validate(TOOL.example)
    assert inputs.n_barre is None
    assert inputs.diametro_barre_mm is None
    geometria = _geometria(inputs)
    sketch = disegna(inputs, geometria)
    barre = next(f for f in sketch.viste[0].forme if f.kind == "bars")

    assert barre.diametro == pytest.approx(DIAMETRO_ILLUSTRATIVO_MM / 1000.0)
    area_totale_mm2 = len(barre.centri) * math.pi / 4.0 * (barre.diametro * 1000.0) ** 2
    assert area_totale_mm2 == pytest.approx(geometria.asl_mm2, rel=0.15)
    for _, y in barre.centri:
        assert y == pytest.approx(inputs.c_mm / 1000.0)
    # diametro illustrativo, non un dato vero: stile "fantasma" + nota esplicativa sullo Sketch
    assert barre.stile == "fantasma"
    assert sketch.nota != ""


@pytest.mark.unit
def test_barre_al_diametro_vero_quando_n_barre_e_diametro_sono_dati() -> None:
    """Quando N°/Ø sono forniti in input (percorso alternativo ad Asl) il disegno usa il
    diametro vero, non il fallback illustrativo."""
    modificato = {**TOOL.example, "n_barre": 5, "diametro_barre_mm": 16, "asl_mm2": None}
    inputs = TaglioNonArmatoInput.model_validate(modificato)
    geometria = _geometria(inputs)
    sketch = disegna(inputs, geometria)
    barre = next(f for f in sketch.viste[0].forme if f.kind == "bars")

    assert barre.diametro == pytest.approx(16 / 1000.0)
    assert len(barre.centri) == 5
    for _, y in barre.centri:
        assert y == pytest.approx(inputs.c_mm / 1000.0)
    # diametro vero, dato dall'utente: stile "armatura", nessuna nota di diametro illustrativo
    assert barre.stile == "armatura"
    assert sketch.nota == ""


@pytest.mark.unit
def test_geometria_segue_una_dimensione_modificata() -> None:
    """Cambiando bw_mm il rettangolo e la sua quota b cambiano di conseguenza."""
    modificato = {**TOOL.example, "bw_mm": 1200}
    inputs = TaglioNonArmatoInput.model_validate(modificato)
    geometria = _geometria(inputs)
    sketch = disegna(inputs, geometria)
    rettangolo = sketch.viste[0].forme[0]
    quota_b = next(f for f in sketch.viste[0].forme if f.kind == "dimension")
    assert rettangolo.w == pytest.approx(1.2)
    assert quota_b.testo == "b = 1200 mm"


@pytest.mark.unit
def test_esempio_ha_schizzo_e_gira_veloce() -> None:
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
    import strutture.members.ca_taglio_non_armato.compose as compose_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(compose_module, "disegna_schizzo", _rompi)
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


@pytest.mark.unit
def test_modulo_schizzo_importabile_e_puro() -> None:
    assert hasattr(schizzo_module, "disegna")
