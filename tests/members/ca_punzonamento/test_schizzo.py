"""Live sketch for `ca-punzonamento` (docs/ui/WORKBENCH_SPEC.md §7, COMPOSITION RULES in
shared/sketch.py): the "Pianta" view follows the inputs, stays readable across several realistic
column/slab geometries, and a drawing failure must never fail the calculation."""
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from test_sketch_layout import layout_problems, overlap_problems, readability_problems

from strutture.members.ca_punzonamento import schizzo as schizzo_module
from strutture.members.ca_punzonamento.effective_depth import effective_depth
from strutture.members.ca_punzonamento.governing_capacity import governing_capacity
from strutture.members.ca_punzonamento.models import GeometriaOutput, PerimetroCriticoOutput, PunzonamentoInput
from strutture.members.ca_punzonamento.perimeter_scan import scan_perimetro
from strutture.members.ca_punzonamento.reinforcement_ratio import rho_l
from strutture.members.ca_punzonamento.schizzo import disegna
from strutture.members.ca_punzonamento.tables import POSIZIONE_BETA
from strutture.members.ca_punzonamento.tool import TOOLS
from strutture.shared.ec2_shear import k_size
from strutture.shared.tables import exact_lookup
from strutture.shared.tool import execute

TOOL = TOOLS[0]


def _geometria(inputs: PunzonamentoInput) -> GeometriaOutput:
    dx, dy, d = effective_depth(inputs.h_mm, inputs.copriferro_mm, inputs.phix_mm, inputs.phiy_mm)
    return GeometriaOutput(dx_mm=dx, dy_mm=dy, d_mm=d, u0_mm=0.0)


@pytest.mark.unit
def test_vista_titolo_e_forme_esempio() -> None:
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    sketch = report.data.schizzo
    assert [v.titolo for v in sketch.viste] == ["Pianta"]
    forme = sketch.viste[0].forme
    kinds = [f.kind for f in forme]
    assert kinds.count("rect") == 1
    assert kinds.count("polygon") == 2  # u0 + perimetro governante (esempio senza armatura)
    assert kinds.count("dimension") == 2


@pytest.mark.unit
def test_colonna_disegnata_sopra_i_perimetri_paint_order() -> None:
    """Design review (P0): l'ordine di disegno è l'ordine di stampa — i perimetri (poligoni/
    cerchi) vanno disegnati PRIMA, la colonna/area caricata per ULTIMA, così il riempimento
    traslucido del perimetro governante non copre mai la colonna né le quote."""
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    forme = report.data.schizzo.viste[0].forme
    indice_colonna = next(i for i, f in enumerate(forme) if f.kind == "rect" and f.stile == "calcestruzzo")
    indici_perimetri = [i for i, f in enumerate(forme) if f.kind in ("polygon", "circle")]
    assert indice_colonna > max(indici_perimetri)
    indici_quote = [i for i, f in enumerate(forme) if f.kind == "dimension"]
    assert indice_colonna < min(indici_quote)  # le quote restano leggibili sopra alla colonna


@pytest.mark.unit
def test_colonna_rettangolare_segue_gli_input() -> None:
    inputs = PunzonamentoInput.model_validate(TOOL.example)
    geometria = _geometria(inputs)
    beta = exact_lookup(POSIZIONE_BETA, inputs.posizione)
    k = k_size(geometria.d_mm)
    rho = rho_l(inputs.px_mm, inputs.py_mm, inputs.phix_mm, inputs.phiy_mm, inputs.paddx_mm, inputs.paddy_mm,
                inputs.phiaddx_mm, inputs.phiaddy_mm, geometria.d_mm)
    righe, governing = scan_perimetro(
        inputs.ved_kN, beta, inputs.pterreno_MPa, inputs.lato_a_mm, inputs.lato_b_mm, inputs.diametro_mm,
        inputs.umanuale_mm, geometria.d_mm, k, rho, inputs.fck_MPa, legacy_compat=inputs.legacy_compat,
    )
    capacity = governing_capacity(
        inputs.ved_kN, beta, inputs.pterreno_MPa, inputs.lato_a_mm, inputs.lato_b_mm, inputs.diametro_mm,
        inputs.umanuale_mm, inputs.a_amanuale_mm2, governing.x, geometria.d_mm, k, rho, inputs.fck_MPa,
        legacy_compat=inputs.legacy_compat,
    )
    perimetro_critico = PerimetroCriticoOutput(
        righe=righe, a_governante_su_d=governing.x, a_governante_mm=capacity.a_governante_mm, ui_mm=capacity.ui_mm,
        area_mm2=capacity.area_mm2, rho=rho, k=k, ved_red_ui_kN=capacity.ved_red_ui_kN, v_rd_i_MPa=capacity.v_rd_i_MPa,
        v_ed_i_MPa=capacity.v_ed_i_MPa, rapporto=capacity.rapporto, armatura_necessaria=capacity.armatura_necessaria,
    )
    sketch = disegna(inputs, geometria, perimetro_critico, None)
    rettangolo = next(f for f in sketch.viste[0].forme if f.kind == "rect")
    assert rettangolo.w == pytest.approx(inputs.lato_a_mm / 1000.0)
    assert rettangolo.h == pytest.approx(inputs.lato_b_mm / 1000.0)
    assert rettangolo.x == pytest.approx(-inputs.lato_a_mm / 2000.0)


@pytest.mark.unit
def test_geometria_segue_una_dimensione_modificata() -> None:
    base = execute(TOOL, TOOL.example)
    assert base.ok
    modificato = {**TOOL.example, "lato_a_mm": 600}
    report = execute(TOOL, modificato)
    assert report.ok, report.errors
    rettangolo_base = next(f for f in base.data.schizzo.viste[0].forme if f.kind == "rect")
    rettangolo_mod = next(f for f in report.data.schizzo.viste[0].forme if f.kind == "rect")
    assert rettangolo_base.w == pytest.approx(0.4)
    assert rettangolo_mod.w == pytest.approx(0.6)


@pytest.mark.unit
def test_colonna_circolare_disegna_cerchi() -> None:
    modificato = {**TOOL.example, "lato_a_mm": 0, "lato_b_mm": 0, "diametro_mm": 450}
    report = execute(TOOL, modificato)
    assert report.ok, report.errors
    kinds = [f.kind for f in report.data.schizzo.viste[0].forme]
    assert kinds.count("circle") >= 1
    colonna = next(f for f in report.data.schizzo.viste[0].forme if f.kind == "circle" and f.stile == "calcestruzzo")
    assert colonna.r == pytest.approx(0.225)


@pytest.mark.unit
def test_colonna_circolare_perimetri_di_verifica_sono_tratteggiati() -> None:
    """u0 (e u0,out se presente) sono tratteggiati per distinguerli dal contorno pieno della
    colonna e dal perimetro governante in evidenza; la colonna e il perimetro governante non lo sono."""
    modificato = {**TOOL.example, "lato_a_mm": 0, "lato_b_mm": 0, "diametro_mm": 450, "legacy_compat": True}
    report = execute(TOOL, modificato)
    assert report.ok, report.errors
    assert report.data.armatura is not None
    cerchi = [f for f in report.data.schizzo.viste[0].forme if f.kind == "circle"]
    assert len(cerchi) == 4  # colonna + u0 + governante + u0,out
    colonna = next(f for f in cerchi if f.stile == "calcestruzzo")
    governante = next(f for f in cerchi if f.stile == "evidenza")
    tratteggiati = [f for f in cerchi if f.stile == "quota"]
    assert len(tratteggiati) == 2  # u0 e u0,out
    assert colonna.tratteggio is False
    assert governante.tratteggio is False
    assert all(f.tratteggio is True for f in tratteggiati)
    # paint order: i perimetri (poligoni/cerchi non "calcestruzzo") vengono prima della colonna
    forme = report.data.schizzo.viste[0].forme
    indice_colonna = forme.index(colonna)
    assert all(forme.index(f) < indice_colonna for f in (governante, *tratteggiati))


@pytest.mark.parametrize("posizione,n_linee_bordo", [("interno", 0), ("centrato", 0), ("bordo", 1), ("angolo", 2)])
@pytest.mark.unit
def test_bordo_solaio_segue_la_posizione(posizione: str, n_linee_bordo: int) -> None:
    modificato = {**TOOL.example, "posizione": posizione}
    report = execute(TOOL, modificato)
    assert report.ok, report.errors
    kinds = [f.kind for f in report.data.schizzo.viste[0].forme]
    assert kinds.count("line") == n_linee_bordo


@pytest.mark.unit
def test_u_out_disegnato_quando_larmatura_e_necessaria() -> None:
    modificato = {**TOOL.example, "legacy_compat": True}
    report = execute(TOOL, modificato)
    assert report.ok, report.errors
    assert report.data.armatura is not None
    kinds = [f.kind for f in report.data.schizzo.viste[0].forme]
    assert kinds.count("polygon") == 3  # u0, governante, u0,out


@pytest.mark.unit
def test_quote_a_e_2d_hanno_testo_coerente() -> None:
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    quote = [f for f in report.data.schizzo.viste[0].forme if f.kind == "dimension"]
    assert quote[0].testo.startswith("a_gov = ")  # "a" da solo è il lato del pilastro, un dato
    assert quote[1].testo.startswith("2d = ")
    a_governante_mm = report.data.perimetro_critico.a_governante_mm
    assert quote[0].testo == f"a_gov = {round(a_governante_mm)} mm"


@pytest.mark.unit
@pytest.mark.parametrize(
    "overrides",
    [
        {},  # esempio
        {"lato_a_mm": 800, "lato_b_mm": 300},  # colonna rettangolare molto allungata
        {"lato_a_mm": 0, "lato_b_mm": 0, "diametro_mm": 450},  # colonna circolare
        {"posizione": "angolo"},
        {"posizione": "bordo"},
        {"legacy_compat": True},  # forza il progetto delle armature -> perimetro u0,out disegnato
        {"lato_a_mm": 0, "lato_b_mm": 0, "diametro_mm": 450, "legacy_compat": True, "posizione": "angolo"},
        {"h_mm": 1000, "lato_a_mm": 600, "lato_b_mm": 600},  # platea spessa, colonna grande
    ],
)
def test_geometrie_realistiche_non_hanno_problemi_di_layout(overrides: dict) -> None:
    modificato = {**TOOL.example, **overrides}
    report = execute(TOOL, modificato)
    assert report.ok, report.errors
    sketch = report.data.schizzo
    assert sketch is not None
    problems = layout_problems(sketch) + readability_problems(sketch) + overlap_problems(sketch)
    assert problems == [], problems


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
    import strutture.members.ca_punzonamento.compose as compose_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(compose_module, "disegna_schizzo", _rompi)
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


@pytest.mark.unit
def test_modulo_schizzo_importabile_e_puro() -> None:
    assert hasattr(schizzo_module, "disegna")


@pytest.mark.unit
def test_quote_a_e_2d_misurano_dal_filo_della_colonna() -> None:
    """Una quota sta accanto a ciò che misura: `a` e `2d` partono dal filo della colonna lungo
    l'asse x (p1) e arrivano alla distanza quotata (p2), con la linea di quota portata SOTTO il
    perimetro più esterno. Prima erano due colonnine staccate, a destra del disegno, che non
    misuravano nulla di riconoscibile."""
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    inputs = PunzonamentoInput.model_validate(TOOL.example)
    forme = report.data.schizzo.viste[0].forme
    quota_a, quota_2d = [f for f in forme if f.kind == "dimension"]
    filo_m = (inputs.lato_a_mm / 2.0 if inputs.lato_a_mm > 0 else inputs.diametro_mm / 2.0) / 1000.0
    a_m = report.data.perimetro_critico.a_governante_mm / 1000.0

    for quota in (quota_a, quota_2d):
        assert quota.p1 == pytest.approx((filo_m, 0.0))
        assert quota.p2[1] == pytest.approx(0.0)
        assert quota.distanza < 0  # verso +x la sinistra è +y: negativo = sotto la pianta
    assert quota_a.p2[0] == pytest.approx(filo_m + a_m)
    assert quota_2d.p2[0] == pytest.approx(filo_m + 2.0 * report.data.geometria.d_mm / 1000.0)
    y_min_perimetri = min(y for f in forme if f.kind == "polygon" for _, y in f.punti)
    assert -abs(quota_a.distanza) < y_min_perimetri  # la linea di quota passa sotto tutti i perimetri
    assert abs(quota_2d.distanza) > abs(quota_a.distanza)  # impilate, mai sovrapposte
