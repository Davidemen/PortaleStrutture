"""Live sketches shared by `geo-cedimento-elastico-newmark` and
`geo-cedimento-elastico-timoshenko-goodier` (docs/ui/WORKBENCH_SPEC.md §7): the sections follow the
inputs, and a drawing failure must never fail the calculation."""
import sys
import time
from pathlib import Path

import pytest

from strutture.geotechnics.cedimenti_elastico import schizzo as schizzo_module
from strutture.geotechnics.cedimenti_elastico.models_newmark import NewmarkInput
from strutture.geotechnics.cedimenti_elastico.models_tg import TimoshenkoGoodierInput
from strutture.geotechnics.cedimenti_elastico.schizzo import disegna_newmark, disegna_timoshenko_goodier
from strutture.geotechnics.cedimenti_elastico.tool_newmark import TOOLS as NEWMARK_TOOLS
from strutture.geotechnics.cedimenti_elastico.tool_timoshenko_goodier import TOOLS as TG_TOOLS
from strutture.shared.tool import execute

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from test_sketch_layout import layout_problems, overlap_problems, readability_problems

NEWMARK_TOOL = NEWMARK_TOOLS[0]
TG_TOOL = TG_TOOLS[0]

_PUNTO_ESEMPIO = {
    "modalita": "PUNTO", "sistema_unita": "SI", "q": 100.0, "d": 0.0,
    "side_p": 2.0, "side_q": 3.0, "e1": 1.0, "e2": 1.5,
    "strati": [{"z_top_m": 0.0, "z_bot_m": 20.0, "modulo_MPa": 10.0}],
    "z_max": 5.0, "dz": 0.5,
}


# --- Newmark, modalità CENTRO (TOOL.example) ----------------------------------------------------

@pytest.mark.unit
def test_newmark_centro_vista_titolo_e_forme() -> None:
    """L'esempio ha 5 strati fino a 120 m: molto oltre il budget di profondità visibile, quindi
    l'ultimo strato è escluso (4 disegnati) e al massimo 2 sono etichettati (quota di spessore +
    modulo E), con un tratto "fantasma" a indicare la prosecuzione in profondità (oltre ai
    fantasma laterali, sempre presenti)."""
    inputs = NewmarkInput.model_validate(NEWMARK_TOOL.example)
    sketch = disegna_newmark(inputs)
    assert [v.titolo for v in sketch.viste] == ["Sezione"]
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds[0] == "rect"
    assert kinds.count("rect") == 1 + 4  # plinto + 4 strati visibili
    assert kinds.count("label") <= 2 + 1  # <=2 E (limite/scostamento minimo) + 1 z_max
    assert kinds.count("line") == 1 + 2 + 1  # z_max + 2 fantasma laterali + 1 fantasma di profondità
    assert kinds.count("dimension") == 2 + 2  # B, D + <=2 quote di spessore strato (Δz)
    assert "interrotta" in sketch.nota


@pytest.mark.unit
def test_newmark_quota_b_sopra_il_plinto_e_terreno_largo_3b() -> None:
    """Correzione P1: la quota B sta sopra il plinto (non sotto), e il blocco di terreno è
    disegnato 3 volte più largo del plinto (non deve leggersi come un palo), con un tacco
    tratteggiato "fantasma" per lato."""
    inputs = NewmarkInput.model_validate(NEWMARK_TOOL.example)
    sketch = disegna_newmark(inputs)
    forme = sketch.viste[0].forme
    plinto = forme[0]
    quota_b = next(f for f in forme if f.kind == "dimension" and f.testo.startswith("B ="))
    assert quota_b.p1[1] == pytest.approx(plinto.y + plinto.h)
    assert quota_b.distanza > 0  # verso l'alto: fuori dal plinto
    primo_strato = next(f for f in forme if f.kind == "rect" and f.stile == "terreno")
    assert primo_strato.w == pytest.approx(3.5 * 3.0)
    fantasmi_laterali = [f for f in forme if f.kind == "line" and f.stile == "fantasma"
                          and f.p1[1] == pytest.approx(f.p2[1])]
    assert len(fantasmi_laterali) == 2


@pytest.mark.unit
def test_newmark_spessore_a_sinistra_modulo_a_destra() -> None:
    """Correzione P1: per ogni strato etichettato, la quota di spessore Δz è a sinistra del blocco
    di terreno e l'etichetta del modulo E è a destra — mai sullo stesso lato."""
    inputs = NewmarkInput.model_validate(NEWMARK_TOOL.example)
    sketch = disegna_newmark(inputs)
    forme = sketch.viste[0].forme
    quote_spessore = [f for f in forme if f.kind == "dimension" and f.testo.startswith("Δz")]
    etichette_modulo = [f for f in forme if f.kind == "label" and f.testo.startswith("E =")]
    assert len(quote_spessore) == len(etichette_modulo) == 2
    for quota in quote_spessore:
        assert quota.p1[0] < 0  # a sinistra
    for etichetta in etichette_modulo:
        assert etichetta.punto[0] > 0  # a destra


@pytest.mark.unit
def test_newmark_centro_plinto_e_quote_seguono_gli_input() -> None:
    inputs = NewmarkInput.model_validate(NEWMARK_TOOL.example)
    sketch = disegna_newmark(inputs)
    forme = sketch.viste[0].forme
    plinto = forme[0]
    assert plinto.x == pytest.approx(-3.5 / 2)
    assert plinto.y == pytest.approx(-1.10)
    assert plinto.w == pytest.approx(3.5)
    quota_b = next(f for f in forme if f.kind == "dimension" and f.testo.startswith("B ="))
    quota_d = next(f for f in forme if f.kind == "dimension" and f.testo.startswith("D ="))
    assert quota_b.testo == "B = 3,50 m"
    assert quota_d.testo == "D = 1,10 m"


@pytest.mark.unit
def test_newmark_centro_evidenza_a_d_piu_zmax() -> None:
    """D + z_max = 10,20 m è entro il budget di profondità visibile (12,32 m): la linea sta alla
    sua vera posizione (nessun ritaglio necessario per l'evidenza stessa)."""
    inputs = NewmarkInput.model_validate(NEWMARK_TOOL.example)
    sketch = disegna_newmark(inputs)
    forme = sketch.viste[0].forme
    linea = next(f for f in forme if f.kind == "line" and f.stile == "evidenza")
    etichetta = next(f for f in forme if f.kind == "label" and f.testo.startswith("z_max ="))
    assert linea.p1[1] == pytest.approx(-(1.10 + 9.10))
    assert linea.p2[1] == pytest.approx(-(1.10 + 9.10))
    assert etichetta.testo == "z_max = 10,20 m"


@pytest.mark.unit
def test_newmark_geometria_segue_una_dimensione_modificata() -> None:
    """Cambiando `b` (in sistema tecnico, cm) il plinto e la quota B cambiano di conseguenza."""
    modificato = {**NEWMARK_TOOL.example, "b": 500}
    inputs = NewmarkInput.model_validate(modificato)
    sketch = disegna_newmark(inputs)
    forme = sketch.viste[0].forme
    plinto = forme[0]
    quota_b = next(f for f in forme if f.kind == "dimension" and f.testo.startswith("B ="))
    assert plinto.w == pytest.approx(5.0)
    assert quota_b.testo == "B = 5,00 m"


@pytest.mark.unit
def test_newmark_quota_d_assente_quando_lembedment_e_zero() -> None:
    modificato = {**NEWMARK_TOOL.example, "d": 0}
    inputs = NewmarkInput.model_validate(modificato)
    sketch = disegna_newmark(inputs)
    forme = sketch.viste[0].forme
    assert not any(f.kind == "dimension" and f.testo.startswith("D =") for f in forme)
    assert any(f.kind == "dimension" and f.testo.startswith("B =") for f in forme)


# --- Newmark, modalità PUNTO --------------------------------------------------------------------

@pytest.mark.unit
def test_newmark_punto_ha_due_viste() -> None:
    inputs = NewmarkInput.model_validate(_PUNTO_ESEMPIO)
    sketch = disegna_newmark(inputs)
    assert [v.titolo for v in sketch.viste] == ["Sezione", "Pianta"]


@pytest.mark.unit
def test_newmark_punto_pianta_rettangolo_o_e_o_primo() -> None:
    inputs = NewmarkInput.model_validate(_PUNTO_ESEMPIO)
    sketch = disegna_newmark(inputs)
    pianta = sketch.viste[1]
    kinds = [f.kind for f in pianta.forme]
    assert kinds == ["rect", "circle", "label", "circle", "label", "dimension", "dimension"]

    rettangolo, cerchio_o_prime, etichetta_o_prime, cerchio_o, etichetta_o, quota_od, quota_og = pianta.forme
    assert rettangolo.w == pytest.approx(2.0)
    assert rettangolo.h == pytest.approx(3.0)
    assert cerchio_o_prime.centro == pytest.approx((0.0, 0.0))
    assert etichetta_o_prime.testo == "O'"
    assert cerchio_o.centro == pytest.approx((1.0, 1.5))
    assert etichetta_o.testo == "O"
    assert quota_od.testo == "O'd = 2,00 m"
    assert quota_og.testo == "O'g = 3,00 m"


@pytest.mark.unit
def test_newmark_punto_o_puo_cadere_fuori_dal_rettangolo() -> None:
    """`e1`/`e2` possono eccedere `side_p`/`side_q`: geometria valida per il metodo di Newmark, da
    non tagliare fuori dal disegno."""
    modificato = {**_PUNTO_ESEMPIO, "e1": 5.0, "e2": 5.0}
    inputs = NewmarkInput.model_validate(modificato)
    sketch = disegna_newmark(inputs)
    cerchio_o = sketch.viste[1].forme[3]
    assert cerchio_o.centro == pytest.approx((5.0, 5.0))


# --- Timoshenko & Goodier -------------------------------------------------------------------------

@pytest.mark.unit
def test_tg_vista_titolo_e_forme() -> None:
    """Con B=1 m il budget di profondità visibile (2,2×larghezza terreno) è piccolo: anche H (5×B
    di default) cade oltre, quindi compare il tratto "fantasma"."""
    inputs = TimoshenkoGoodierInput.model_validate(TG_TOOL.example)
    sketch = disegna_timoshenko_goodier(inputs)
    assert [v.titolo for v in sketch.viste] == ["Sezione"]
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds.count("rect") == 1 + 2
    assert kinds.count("label") == 2 + 1
    assert kinds.count("line") == 1 + 2 + 1  # H + 2 fantasma laterali + 1 fantasma di profondità
    assert kinds.count("dimension") == 2 + 2  # B, D + 2 quote di spessore strato (Δz)
    assert "interrotta" in sketch.nota


@pytest.mark.unit
def test_tg_evidenza_usa_h_significativo_di_default() -> None:
    """`h_significativo` assente -> H = 5·B (default del foglio)."""
    inputs = TimoshenkoGoodierInput.model_validate(TG_TOOL.example)
    sketch = disegna_timoshenko_goodier(inputs)
    etichetta = next(f for f in sketch.viste[0].forme if f.kind == "label" and f.testo.startswith("H ="))
    atteso_m = inputs.d + 5.0 * inputs.b
    assert etichetta.testo == f"H = {atteso_m:.2f} m".replace(".", ",")


@pytest.mark.unit
def test_tg_geometria_segue_una_dimensione_modificata() -> None:
    modificato = {**TG_TOOL.example, "b": 2.0}
    inputs = TimoshenkoGoodierInput.model_validate(modificato)
    sketch = disegna_timoshenko_goodier(inputs)
    plinto = sketch.viste[0].forme[0]
    quota_b = next(f for f in sketch.viste[0].forme if f.kind == "dimension" and f.testo.startswith("B ="))
    assert plinto.w == pytest.approx(2.0)
    assert quota_b.testo == "B = 2,00 m"


# --- Timing, guardia di errore, importabilità -----------------------------------------------------

@pytest.mark.unit
def test_newmark_esempio_ha_schizzo_e_gira_in_meno_di_300ms() -> None:
    inizio = time.perf_counter()
    report = execute(NEWMARK_TOOL, NEWMARK_TOOL.example)
    durata = time.perf_counter() - inizio
    assert report.ok, report.errors
    assert report.data.schizzo is not None
    assert durata < 0.3, f"esempio in {durata:.3f}s"


@pytest.mark.unit
def test_tg_esempio_ha_schizzo_e_gira_in_meno_di_300ms() -> None:
    inizio = time.perf_counter()
    report = execute(TG_TOOL, TG_TOOL.example)
    durata = time.perf_counter() - inizio
    assert report.ok, report.errors
    assert report.data.schizzo is not None
    assert durata < 0.3, f"esempio in {durata:.3f}s"


@pytest.mark.unit
def test_newmark_errore_nel_disegno_non_fa_fallire_il_calcolo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un'eccezione nello schizzo deve essere loggata e assorbita: il calcolo resta valido."""
    import strutture.geotechnics.cedimenti_elastico.tool_newmark as tool_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(tool_module, "disegna_newmark", _rompi)
    report = execute(NEWMARK_TOOL, NEWMARK_TOOL.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


@pytest.mark.unit
def test_tg_errore_nel_disegno_non_fa_fallire_il_calcolo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un'eccezione nello schizzo deve essere loggata e assorbita: il calcolo resta valido."""
    import strutture.geotechnics.cedimenti_elastico.tool_timoshenko_goodier as tool_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(tool_module, "disegna_timoshenko_goodier", _rompi)
    report = execute(TG_TOOL, TG_TOOL.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


@pytest.mark.unit
def test_modulo_schizzo_importabile_e_puro() -> None:
    assert hasattr(schizzo_module, "disegna_newmark")
    assert hasattr(schizzo_module, "disegna_timoshenko_goodier")


# --- composizione: layout/leggibilità/sovrapposizioni su input realistici oltre l'esempio --------

_CASI_NEWMARK = {
    "infissione profonda": {"d": 250},  # tecnico: 250 cm = 2.5 m
    "molti strati": {"strati": [{"z_top_m": float(i) * 0.8, "z_bot_m": float(i + 1) * 0.8,
                                  "modulo_MPa": 5.0 + i} for i in range(12)]},
    "plinto molto largo": {"b": 1200, "l": 1200},  # tecnico: 1200 cm = 12 m
    "modalità PUNTO": {"modalita": "PUNTO", "b": None, "l": None,
                        "side_p": 350, "side_q": 500, "e1": 100, "e2": 150},
}


@pytest.mark.unit
@pytest.mark.parametrize("nome", list(_CASI_NEWMARK))
def test_newmark_composizione_su_input_realistici(nome: str) -> None:
    modificato = {**NEWMARK_TOOL.example, **_CASI_NEWMARK[nome]}
    inputs = NewmarkInput.model_validate(modificato)
    sketch = disegna_newmark(inputs)
    problemi = layout_problems(sketch) + readability_problems(sketch) + overlap_problems(sketch)
    assert problemi == [], f"{nome}: {problemi}"


_CASI_TG = {
    "infissione profonda": {"d": 3.0},
    "profondità significativa elevata": {"h_significativo": 15.0},
    "plinto molto largo": {"b": 3.0, "l": 3.0},
}


@pytest.mark.unit
@pytest.mark.parametrize("nome", list(_CASI_TG))
def test_tg_composizione_su_input_realistici(nome: str) -> None:
    modificato = {**TG_TOOL.example, **_CASI_TG[nome]}
    inputs = TimoshenkoGoodierInput.model_validate(modificato)
    sketch = disegna_timoshenko_goodier(inputs)
    problemi = layout_problems(sketch) + readability_problems(sketch) + overlap_problems(sketch)
    assert problemi == [], f"{nome}: {problemi}"
