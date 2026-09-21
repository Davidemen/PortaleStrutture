"""Live sketch for `ca-trave-rettangolare` (docs/ui/WORKBENCH_SPEC.md §7): the "Sezione" view
follows the inputs, and a drawing failure must never fail the calculation."""
import time

import pytest

from strutture.members.ca_travi import schizzo as schizzo_module
from strutture.members.ca_travi.flessione_slu import verifica_flessione_slu
from strutture.members.ca_travi.geometria import altezza_utile_mm, braccio_leva_mm
from strutture.members.ca_travi.materiali import materiali_trave
from strutture.members.ca_travi.models import TraveRettangolareInput
from strutture.members.ca_travi.schizzo import disegna
from strutture.members.ca_travi.tool import TOOLS
from strutture.shared.tool import execute

TOOL = TOOLS[0]


def _flessione(inputs: TraveRettangolareInput):
    materiali = materiali_trave(inputs.tipo_cls, inputs.tipo_acciaio, legacy_compat=inputs.legacy_compat)
    d_mm = altezza_utile_mm(inputs.h_mm, inputs.copriferro_mm)
    from strutture.members.ca_travi.armatura_limiti import armatura_minima_massima

    z_mm = braccio_leva_mm(d_mm)
    armatura = armatura_minima_massima(
        b_mm=inputs.b_mm, h_mm=inputs.h_mm, d_mm=d_mm, z_mm=z_mm,
        n_ferri1=inputs.n_ferri1, diametro_ferri1_mm=inputs.diametro_ferri1_mm,
        n_ferri2=inputs.n_ferri2, diametro_ferri2_mm=inputs.diametro_ferri2_mm,
        diametro_staffe1_mm=inputs.diametro_staffe1_mm, n_bracci_staffe1=inputs.n_bracci_staffe1,
        passo_staffe1_mm=inputs.passo_staffe1_mm, diametro_staffe2_mm=inputs.diametro_staffe2_mm,
        n_bracci_staffe2=inputs.n_bracci_staffe2, fck_MPa=materiali.calcestruzzo.fck_MPa,
        fctm_MPa=materiali.calcestruzzo.fctm_MPa, fyk_MPa=materiali.acciaio.fyk_MPa,
        ftk_MPa=materiali.acciaio.ftk_MPa, classe_duttilita=inputs.classe_duttilita,
        legacy_compat=inputs.legacy_compat,
    )
    return verifica_flessione_slu(
        as_o_mm2=armatura.as_o_mm2, fyd_MPa=materiali.acciaio.fyd_MPa, fcd_MPa=materiali.calcestruzzo.fcd_MPa,
        b_mm=inputs.b_mm, d_mm=d_mm, med_slu_kNm=inputs.med_slu_kNm, es_MPa=materiali.acciaio.es_MPa,
        legacy_compat=inputs.legacy_compat,
    )


@pytest.mark.unit
def test_vista_titolo_e_forme_esempio() -> None:
    inputs = TraveRettangolareInput.model_validate(TOOL.example)
    flessione = _flessione(inputs)
    sketch = disegna(inputs, flessione)

    assert [v.titolo for v in sketch.viste] == ["Sezione"]
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds[0] == "rect"
    assert "polygon" in kinds
    assert kinds.count("bars") == 1  # esempio ha n_ferri2 = 0: solo lo strato teso
    assert "line" in kinds
    assert kinds.count("dimension") == 2


@pytest.mark.unit
def test_sezione_rettangolo_e_quote_seguono_gli_input() -> None:
    inputs = TraveRettangolareInput.model_validate(TOOL.example)
    flessione = _flessione(inputs)
    sketch = disegna(inputs, flessione)
    rettangolo = sketch.viste[0].forme[0]
    assert rettangolo.x == pytest.approx(0.0)
    assert rettangolo.y == pytest.approx(0.0)
    assert rettangolo.w == pytest.approx(inputs.b_mm / 1000.0)
    assert rettangolo.h == pytest.approx(inputs.h_mm / 1000.0)

    quote = [f for f in sketch.viste[0].forme if f.kind == "dimension"]
    assert quote[0].testo == "b = 600 mm"
    assert quote[1].testo == "h = 400 mm"


@pytest.mark.unit
def test_barre_tese_al_diametro_vero_e_alla_quota_del_copriferro() -> None:
    inputs = TraveRettangolareInput.model_validate(TOOL.example)
    flessione = _flessione(inputs)
    sketch = disegna(inputs, flessione)
    barre = next(f for f in sketch.viste[0].forme if f.kind == "bars")
    assert barre.diametro == pytest.approx(inputs.diametro_ferri1_mm / 1000.0)
    assert len(barre.centri) == inputs.n_ferri1
    for _, y in barre.centri:
        assert y == pytest.approx(inputs.copriferro_mm / 1000.0)


@pytest.mark.unit
def test_barre_compresse_disegnate_quando_presente_il_secondo_strato() -> None:
    modificato = {**TOOL.example, "n_ferri2": 2, "diametro_ferri2_mm": 16}
    inputs = TraveRettangolareInput.model_validate(modificato)
    flessione = _flessione(inputs)
    sketch = disegna(inputs, flessione)
    gruppi_barre = [f for f in sketch.viste[0].forme if f.kind == "bars"]
    assert len(gruppi_barre) == 2
    compresse = gruppi_barre[1]
    assert compresse.diametro == pytest.approx(16 / 1000.0)
    for _, y in compresse.centri:
        assert y == pytest.approx(inputs.h_mm / 1000.0 - inputs.copriferro_mm / 1000.0)


@pytest.mark.unit
def test_geometria_segue_una_dimensione_modificata() -> None:
    """Cambiando b_mm il rettangolo e la sua quota cambiano di conseguenza."""
    modificato = {**TOOL.example, "b_mm": 800}
    inputs = TraveRettangolareInput.model_validate(modificato)
    flessione = _flessione(inputs)
    sketch = disegna(inputs, flessione)
    rettangolo = sketch.viste[0].forme[0]
    quota_b = next(f for f in sketch.viste[0].forme if f.kind == "dimension")
    assert rettangolo.w == pytest.approx(0.8)
    assert quota_b.testo == "b = 800 mm"


@pytest.mark.unit
def test_asse_neutro_segue_il_risultato_uls() -> None:
    inputs = TraveRettangolareInput.model_validate(TOOL.example)
    flessione = _flessione(inputs)
    sketch = disegna(inputs, flessione)
    linea = next(f for f in sketch.viste[0].forme if f.kind == "line")
    y_atteso = (inputs.h_mm - flessione.y_mm) / 1000.0
    assert linea.p1[1] == pytest.approx(y_atteso)
    assert linea.p2[1] == pytest.approx(y_atteso)
    assert linea.stile == "evidenza"


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
    import strutture.members.ca_travi.tool as tool_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(tool_module, "disegna_schizzo", _rompi)
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


@pytest.mark.unit
def test_modulo_schizzo_importabile_e_puro() -> None:
    assert hasattr(schizzo_module, "disegna")
