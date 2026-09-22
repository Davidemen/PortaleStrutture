"""`relazione_newmark.py` / `relazione_timoshenko_goodier.py` (docs/architecture-phase2.md §6,
wave-2/3 adoption): the harness on each tool's own example, on every oracle/golden case of the
package's existing tests (imported/rebuilt here) — run in STANDARD mode (`legacy_compat=False`:
`relazione` only ever describes standard mode) — plus variations that switch branches: Newmark's
PUNTO mode (vs the example's CENTRO), an asymmetric PUNTO point, a small depth grid (≤3 slices, no
"resto" lumping), and Timoshenko-Goodier's manual `H` override and a many-layer stratigraphy
(triggers the "resto" lumping of `Es`'s weighted sum)."""
import json
import re
from pathlib import Path
from typing import Any

import pytest

from strutture.geotechnics.cedimenti_elastico.tool_newmark import TOOLS as NEWMARK_TOOLS
from strutture.geotechnics.cedimenti_elastico.tool_timoshenko_goodier import TOOLS as TG_TOOLS
from strutture.shared.tool import execute
from strutture.shared.units import kgcm2_to_mpa
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

NEWMARK = NEWMARK_TOOLS[0]
TG = TG_TOOLS[0]

FIXTURES = Path(__file__).parents[2] / "fixtures"

CENTRO_STRATI = [
    {"z_top_m": 0.80, "z_bot_m": 4.80, "modulo_MPa": 5.5}, {"z_top_m": 4.80, "z_bot_m": 5.80, "modulo_MPa": 7.0},
    {"z_top_m": 5.80, "z_bot_m": 6.60, "modulo_MPa": 9.0}, {"z_top_m": 6.60, "z_bot_m": 32.60, "modulo_MPa": 7.0},
    {"z_top_m": 32.60, "z_bot_m": 120.0, "modulo_MPa": 7.0},
]
PUNTO_STRATI = [
    {"z_top_m": 0.0, "z_bot_m": 15.0, "modulo_MPa": 100 * 0.0980665},
    {"z_top_m": 15.0, "z_bot_m": 120.0, "modulo_MPa": 180 * 0.0980665},
]
CENTRO_DEFAULT_STRATI = [
    {"z_top_m": 0.80, "z_bot_m": 4.80, "modulo_MPa": kgcm2_to_mpa(5500 / 98.0665)},
    {"z_top_m": 4.80, "z_bot_m": 5.80, "modulo_MPa": kgcm2_to_mpa(7000 / 98.0665)},
    {"z_top_m": 5.80, "z_bot_m": 6.60, "modulo_MPa": kgcm2_to_mpa(9000 / 98.0665)},
    {"z_top_m": 6.60, "z_bot_m": 32.60, "modulo_MPa": kgcm2_to_mpa(7000 / 98.0665)},
    {"z_top_m": 32.60, "z_bot_m": 120.0, "modulo_MPa": kgcm2_to_mpa(7000 / 98.0665)},
]
PUNTO_500_DEFAULT_STRATI = [
    {"z_top_m": 0.0, "z_bot_m": 15.0, "modulo_MPa": kgcm2_to_mpa(100)},
    {"z_top_m": 15.0, "z_bot_m": 16.0, "modulo_MPa": kgcm2_to_mpa(180)},
    {"z_top_m": 16.0, "z_bot_m": 17.0, "modulo_MPa": kgcm2_to_mpa(180)},
    {"z_top_m": 17.0, "z_bot_m": 30.0, "modulo_MPa": kgcm2_to_mpa(180)},
    {"z_top_m": 30.0, "z_bot_m": 120.0, "modulo_MPa": kgcm2_to_mpa(180)},
]
PUNTO_400_STRATI = [
    {"z_top_m": 0.0, "z_bot_m": 2.40, "modulo_MPa": kgcm2_to_mpa(80)},
    {"z_top_m": 2.40, "z_bot_m": 12.0, "modulo_MPa": kgcm2_to_mpa(200)},
    {"z_top_m": 12.0, "z_bot_m": 15.0, "modulo_MPa": kgcm2_to_mpa(120)},
    {"z_top_m": 15.0, "z_bot_m": 20.0, "modulo_MPa": kgcm2_to_mpa(120)},
    {"z_top_m": 20.0, "z_bot_m": 120.0, "modulo_MPa": kgcm2_to_mpa(120)},
]
TG_STRATI = [
    {"z_top_m": 0.0, "z_bot_m": 2.10, "modulo_MPa": 180 * 0.0980665},
    {"z_top_m": 2.10, "z_bot_m": 5.00, "modulo_MPa": 140 * 0.0980665},
    {"z_top_m": 5.00, "z_bot_m": 5.00 + 1e-9, "modulo_MPa": 140 * 0.0980665},
    {"z_top_m": 5.00 + 1e-9, "z_bot_m": 5.00 + 2e-9, "modulo_MPa": 280 * 0.0980665},
    {"z_top_m": 5.00 + 2e-9, "z_bot_m": 120.0, "modulo_MPa": 280 * 0.0980665},
]

_CENTRO_ORACLE = json.loads((FIXTURES / "geo_cedimento_elastico_newmark_centro_oracle.json").read_text(encoding="utf-8"))
_PUNTO_ORACLE = json.loads((FIXTURES / "geo_cedimento_elastico_newmark_punto_oracle.json").read_text(encoding="utf-8"))


def _centro_oracle_raw(case: dict[str, Any]) -> dict[str, Any]:
    overrides = case["inputs"]
    strati = CENTRO_DEFAULT_STRATI
    if "F7" in overrides:
        strati = [{**strati[0], "modulo_MPa": kgcm2_to_mpa(overrides["F7"])}, *strati[1:]]
    return {
        "modalita": "CENTRO", "q": overrides.get("D3", 0.5) * 98.0665, "d": overrides.get("G1", 110) / 100,
        "b": overrides.get("D1", 350) / 100, "l": overrides.get("D2", 500) / 100, "strati": strati,
    }


def _punto_oracle_raw(case: dict[str, Any]) -> dict[str, Any]:
    overrides = case["inputs"]
    strati = PUNTO_500_DEFAULT_STRATI
    if "F16" in overrides:
        strati = [strati[0], {**strati[1], "modulo_MPa": kgcm2_to_mpa(overrides["F16"])}, *strati[2:]]
    return {
        "modalita": "PUNTO", "q": overrides.get("C1", 0.8) * 98.0665, "d": overrides.get("G1", 220) / 100,
        "side_p": overrides.get("F5", 4000) / 100, "side_q": overrides.get("F6", 4000) / 100,
        "e1": overrides.get("F7", 2000) / 100, "e2": overrides.get("F8", 2000) / 100, "strati": strati,
    }


# --- Newmark --------------------------------------------------------------------------------


def test_newmark_tool_declares_relazione():
    assert NEWMARK.relazione is not None


def test_newmark_relazione_coerente_sullesempio():
    assert_relazione_coerente(NEWMARK, NEWMARK.example)


@pytest.mark.golden
def test_newmark_relazione_coerente_sul_caso_golden_centro():
    raw = {"modalita": "CENTRO", "q": 0.5 * 98.0665, "d": 1.10, "b": 3.5, "l": 5.0, "strati": CENTRO_STRATI}
    assert_relazione_coerente(NEWMARK, raw)


@pytest.mark.golden
def test_newmark_relazione_coerente_sul_caso_golden_punto_500():
    raw = {"modalita": "PUNTO", "q": 0.8 * 98.0665, "d": 2.20, "side_p": 40.0, "side_q": 40.0, "e1": 20.0, "e2": 20.0, "strati": PUNTO_STRATI}
    assert_relazione_coerente(NEWMARK, raw)


@pytest.mark.golden
def test_newmark_relazione_coerente_sui_casi_liberi_400_350():
    raw_400 = {"modalita": "PUNTO", "q": 0.98 * 98.0665, "d": 2.20, "side_p": 4.0, "side_q": 4.0, "e1": 2.0, "e2": 2.0, "strati": PUNTO_400_STRATI}
    raw_350 = {"modalita": "PUNTO", "q": 1.32 * 98.0665, "d": 2.20, "side_p": 3.5, "side_q": 3.5, "e1": 1.75, "e2": 1.75, "strati": PUNTO_400_STRATI}
    assert_relazione_coerente(NEWMARK, raw_400)
    assert_relazione_coerente(NEWMARK, raw_350)


@pytest.mark.oracle
@pytest.mark.parametrize("case", _CENTRO_ORACLE, ids=range(len(_CENTRO_ORACLE)))
def test_newmark_relazione_coerente_sui_casi_oracolo_centro(case: dict[str, Any]):
    assert_relazione_coerente(NEWMARK, _centro_oracle_raw(case))


@pytest.mark.oracle
@pytest.mark.parametrize("case", _PUNTO_ORACLE[:4], ids=range(4))
def test_newmark_relazione_coerente_sui_casi_oracolo_punto(case: dict[str, Any]):
    assert_relazione_coerente(NEWMARK, _punto_oracle_raw(case))


def test_newmark_ogni_highlight_e_spiegato_centro():
    assert_ogni_highlight_e_spiegato(NEWMARK, NEWMARK.example)


def test_newmark_ogni_highlight_e_spiegato_punto():
    raw = {"modalita": "PUNTO", "q": 0.8 * 98.0665, "d": 2.20, "side_p": 40.0, "side_q": 40.0, "e1": 20.0, "e2": 20.0, "strati": PUNTO_STRATI}
    assert_ogni_highlight_e_spiegato(NEWMARK, raw)


def test_newmark_step_count_within_the_8_to_30_target():
    report = execute(NEWMARK, NEWMARK.example, con_relazione=True)
    assert 8 <= sum(len(t.passi) for t in report.relazione) <= 30
    raw_punto = {"modalita": "PUNTO", "q": 0.8 * 98.0665, "d": 2.20, "side_p": 40.0, "side_q": 40.0, "e1": 20.0, "e2": 20.0, "strati": PUNTO_STRATI}
    report_punto = execute(NEWMARK, raw_punto, con_relazione=True)
    assert 8 <= sum(len(t.passi) for t in report_punto.relazione) <= 30


def test_newmark_variazione_modalita_punto():
    """La modalità PUNTO usa `under_point` (Fadum) invece di `under_center`, e traccia anche il
    percorso di riferimento O'."""
    raw = {"modalita": "PUNTO", "q": 0.8 * 98.0665, "d": 2.20, "side_p": 40.0, "side_q": 40.0, "e1": 20.0, "e2": 20.0, "strati": PUNTO_STRATI}
    report = execute(NEWMARK, raw, con_relazione=True)
    assert report.ok
    titoli = [t.titolo for t in report.relazione]
    assert any("punto O" in t for t in titoli)
    assert any("O'" in t for t in titoli)
    simboli = {p.simbolo for t in report.relazione for p in t.passi}
    assert "w_O" in simboli and "w_O'" in simboli
    assert_relazione_coerente(NEWMARK, raw)


def test_newmark_variazione_punto_asimmetrico_e_griglia_piccola():
    """Punto O non centrato (e1 != e2, lati diseguali) e una griglia di profondità con 2 sole
    fette (nessun passo "resto")."""
    raw = {
        "modalita": "PUNTO", "sistema_unita": "SI", "q": 0.8 * 98.0665, "d": 2.2,
        "side_p": 40.0, "side_q": 30.0, "e1": 10.0, "e2": 25.0, "strati": PUNTO_STRATI,
        "z_max": 1.0, "dz": 0.5,
    }
    report = execute(NEWMARK, raw, con_relazione=True)
    assert report.ok
    traccia_o = next(t for t in report.relazione if "punto O" in t.titolo)
    assert not any(p.simbolo == "Δwresto" for p in traccia_o.passi)
    assert_relazione_coerente(NEWMARK, raw)


def test_newmark_controllo_qa_non_e_una_verifica_normativa():
    """Il titolo della Traccia lo dichiara esplicitamente (lezione: un rapporto informativo che
    non è una verifica normativa deve dirlo nel titolo), e nessun Passo della traccia ha `esito`."""
    report = execute(NEWMARK, NEWMARK.example, con_relazione=True)
    traccia_qa = next(t for t in report.relazione if "QA" in t.titolo)
    assert "non è una verifica normativa" in traccia_qa.titolo
    assert all(p.esito == "" for p in traccia_qa.passi)


def test_newmark_scarto_qa_e_zero_in_modalita_standard():
    """centro.py: in modalità standard i due percorsi (principale/QA) sono algebricamente
    identici (stessa griglia, stessa formula chiusa)."""
    report = execute(NEWMARK, NEWMARK.example, con_relazione=True)
    assert report.data.centro.scarto_qa_pct == pytest.approx(0.0)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "Δ%")
    assert passo.risultato == pytest.approx(0.0)


def test_newmark_stress_valutato_a_meta_fetta_non_al_fondo():
    """integrate.py, modalità standard: Δσz è valutato a z_metà=(z_prec+z)/2, non a z_m (il fondo
    della fetta) — la nota del passo lo dichiara."""
    report = execute(NEWMARK, NEWMARK.example, con_relazione=True)
    traccia = next(t for t in report.relazione if "fette di profondità" in t.titolo)
    passo = next(p for p in traccia.passi if p.simbolo.startswith("Δσz_"))
    assert "z_metà" in passo.nota


def test_newmark_delta_w_mostra_la_conversione_kpa_mpa_in_chiaro():
    """review finding MISLEADING: Δσz_1 è stampato in kPa e riappare nel passo successivo come
    0,04903 senza alcun fattore visibile (conversione silenziosa kPa->MPa) — a differenza del
    tool gemello `cedimenti_edometrico`, che stampa sempre il proprio fattore di scala. La
    formula di Δw deve mostrare la conversione (es. '/1000'), non nasconderla dentro il valore
    sostituito."""
    report = execute(NEWMARK, NEWMARK.example, con_relazione=True)
    traccia = next(t for t in report.relazione if "fette di profondità" in t.titolo)
    passo_dw = next(p for p in traccia.passi if p.simbolo.startswith("Δw_"))
    assert "1000" in passo_dw.formula
    valore_sigma = next(v for v in passo_dw.valori if v.simbolo == "Δσz")
    assert valore_sigma.unita == "kPa"


def test_newmark_delta_w_resto_riporta_conteggio_e_intervallo():
    """review finding MISSING_STEP: Δwresto (0,03004 m su un totale di 0,0312 m nel caso
    dell'esempio) non aveva né conteggio né intervallo di profondità visibili."""
    report = execute(NEWMARK, NEWMARK.example, con_relazione=True)
    traccia = next(t for t in report.relazione if "fette di profondità" in t.titolo)
    passo_resto = next(p for p in traccia.passi if p.simbolo.startswith("Δwresto"))
    assert passo_resto.simbolo != "Δwresto"
    assert re.search(r"\d+\s*fette", passo_resto.simbolo)
    assert "z=" in passo_resto.simbolo


def test_newmark_qa_non_riusa_w_con_ununita_diversa():
    """review finding MISLEADING: 'w = ... = 31,2 mm' (Traccia principale) e 'w' riapparso come
    3,12 (cm) nel controllo QA sono lo stesso simbolo con due unità diverse in righe adiacenti
    della stessa Sviluppo dei calcoli. Il passo Δ% deve usare un simbolo distinto (es. w_cm)."""
    report = execute(NEWMARK, NEWMARK.example, con_relazione=True)
    traccia_qa = next(t for t in report.relazione if "QA" in t.titolo)
    passo_delta_pct = next(p for p in traccia_qa.passi if p.simbolo == "Δ%")
    assert not any(v.simbolo == "w" for v in passo_delta_pct.valori)
    assert any(v.simbolo == "w_cm" for v in passo_delta_pct.valori)


# --- Timoshenko & Goodier ---------------------------------------------------------------------


def test_tg_tool_declares_relazione():
    assert TG.relazione is not None


def test_tg_relazione_coerente_sullesempio():
    assert_relazione_coerente(TG, TG.example)


@pytest.mark.golden
def test_tg_relazione_coerente_sul_caso_golden():
    raw = {"b": 1.0, "l": 1.0, "d": 0.5, "mu": 0.35, "q": 0.92 * 98.0665, "strati": TG_STRATI, "if_centro": 0.65, "if_bordo": 0.78}
    assert_relazione_coerente(TG, raw)


def test_tg_ogni_highlight_e_spiegato():
    assert_ogni_highlight_e_spiegato(TG, TG.example)


def test_tg_step_count_within_the_8_to_30_target():
    report = execute(TG, TG.example, con_relazione=True)
    assert 8 <= sum(len(t.passi) for t in report.relazione) <= 30


def test_tg_variazione_h_significativo_manuale():
    """`H` sovrascritto manualmente invece del default 5·B."""
    variazione = {**TG.example, "h_significativo": 3.0}
    report = execute(TG, variazione, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if "Geometria" in t.titolo)
    passo_h = next(p for p in traccia.passi if p.simbolo == "b_bordo")
    assert passo_h.risultato == pytest.approx(report.data.geometria.b_bordo)
    assert_relazione_coerente(TG, variazione)


def test_tg_variazione_molti_strati_attiva_il_resto():
    """Più di 6 strati compresi in [0, H]: il passo "Σresto" compare e la somma pesata resta
    coerente con l'output."""
    strati = [{"z_top_m": 0.5 * i, "z_bot_m": 0.5 * (i + 1), "modulo_MPa": 10.0 + i} for i in range(7)]
    strati.append({"z_top_m": 3.5, "z_bot_m": 120.0, "modulo_MPa": 24.0})
    variazione = {**TG.example, "strati": strati}
    report = execute(TG, variazione, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if "Modulo medio pesato" in t.titolo)
    assert any(p.simbolo == "Σresto" for p in traccia.passi)
    assert_relazione_coerente(TG, variazione)


def test_tg_is_bordo_usa_a_dimezzato_non_il_fattore_di_spigolo():
    """Review-equivalent guard (steinbrenner_factors.py): il fattore IS_bordo non è lo stesso
    calcolo del centro con un fattore 2 esterno bare — la formula stampata usa `(a / 2)`."""
    report = execute(TG, TG.example, con_relazione=True)
    traccia = next(t for t in report.relazione if "Geometria" in t.titolo)
    passo = next(p for p in traccia.passi if p.simbolo == "IS_bordo")
    assert "a / 2" in passo.formula


def test_tg_deltah_centro_e_bordo_sono_evidenziati():
    report = execute(TG, TG.example, con_relazione=True)
    simboli = {p.simbolo for t in report.relazione for p in t.passi}
    assert {"ΔH_centro", "ΔH_bordo"} <= simboli
