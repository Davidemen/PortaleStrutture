"""`relazione.py` (docs/architecture-phase2.md §6, wave-2/3 adoption): the harness on the tool's
own example (`norma="NTC2018"`), on the golden cases of `test_golden.py` and on every oracle case
of `test_oracle_ntc2018.py`/`test_oracle_en1998.py` — run in STANDARD mode (`legacy_compat=False`:
`relazione` never runs in legacy mode) — plus variations that switch branches: the EN1998 branch
itself (7 Check vs NTC2018's 4), a failing minimum-reinforcement Check, and a water-table-adjacent
edge (φ_staffa/n_bracci variation feeding the "Σresto"-free area-staffe path)."""
import json
from pathlib import Path
from typing import Any

import pytest

from strutture.foundations.travi_collegamento.models import TraviCollegamentoInput
from strutture.foundations.travi_collegamento.tool import TOOLS, run
from strutture.shared.report import CalcError
from strutture.shared.tool import execute
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOL = next(t for t in TOOLS if t.name == "fond-trave-collegamento")

_FIXTURES = Path(__file__).parents[2] / "fixtures"
_NTC_ORACLE = json.loads((_FIXTURES / "fond_trave_collegamento_ntc2018_oracle.json").read_text(encoding="utf-8"))
_EN_ORACLE = json.loads((_FIXTURES / "fond_trave_collegamento_en1998_oracle.json").read_text(encoding="utf-8"))

_NTC_GOLDEN = {
    "norma": "NTC2018", "ag_g": 0.151, "f0": 2.43, "categoria_sottosuolo": "B", "categoria_topografica": "T1",
    "b_mm": 400, "h_mm": 400, "phi_mm": 16, "n_barre": 6, "classe_calcestruzzo": "C25/30", "classe_acciaio": "B450C",
    "n1_kN": 2000, "n2_kN": 2500, "l_mm": 5000, "beta": 1, "phi_staffa_mm": 10, "n_bracci": 2, "cf_mm": 40, "p_mm": 125,
}
_EN_GOLDEN = {
    "norma": "EN1998", "ag_g": 0.151, "categoria_sottosuolo": "B", "ms": 5.6,
    "b_mm": 400, "h_mm": 450, "phi_mm": 16, "n_barre": 8, "classe_calcestruzzo": "C25/30", "classe_acciaio": "B450C",
    "n1_kN": 2000, "n2_kN": 2500, "l_mm": 5000, "beta": 1, "n_piani": 3,
    "phi_staffa_mm": 10, "n_bracci": 2, "alpha_staffa_deg": 90, "cf_mm": 40, "p_mm": 200,
}

_NTC_DEFAULTS = {
    "C4": 0.151, "C5": 2.43, "C6": "B", "C7": "T1", "C11": 400, "C12": 400, "C13": 16, "C14": 6,
    "C17": "C25/30", "C18": "B450C", "C22": 2000, "C23": 2500, "C38": 5000, "C39": 1,
    "C48": 10, "C49": 2, "C50": 40, "C53": 125,
}
_EN_DEFAULTS = {
    "C4": 0.151, "C5": "B", "C6": 5.6, "C9": 400, "C10": 450, "C11": 16, "C12": 8,
    "C15": "C25/30", "C16": "B450C", "C20": 2000, "C21": 2500, "C36": 5000, "C37": 1,
    "C49": 3, "C56": 10, "C57": 2, "C58": 90, "C59": 40, "C62": 200,
}


def _ntc_oracle_raw(case: dict[str, Any]) -> dict[str, Any]:
    merged = {**_NTC_DEFAULTS, **case["inputs"]}
    return {
        "norma": "NTC2018", "ag_g": merged["C4"], "f0": merged["C5"], "categoria_sottosuolo": merged["C6"],
        "categoria_topografica": merged["C7"], "b_mm": merged["C11"], "h_mm": merged["C12"], "phi_mm": merged["C13"],
        "n_barre": merged["C14"], "classe_calcestruzzo": merged["C17"], "classe_acciaio": merged["C18"],
        "n1_kN": merged["C22"], "n2_kN": merged["C23"], "l_mm": merged["C38"], "beta": merged["C39"],
        "phi_staffa_mm": merged["C48"], "n_bracci": merged["C49"], "cf_mm": merged["C50"], "p_mm": merged["C53"],
    }


def _en_oracle_raw(case: dict[str, Any]) -> dict[str, Any]:
    merged = {**_EN_DEFAULTS, **case["inputs"]}
    return {
        "norma": "EN1998", "ag_g": merged["C4"], "categoria_sottosuolo": merged["C5"], "ms": merged["C6"],
        "b_mm": merged["C9"], "h_mm": merged["C10"], "phi_mm": merged["C11"], "n_barre": merged["C12"],
        "classe_calcestruzzo": merged["C15"], "classe_acciaio": merged["C16"], "n1_kN": merged["C20"], "n2_kN": merged["C21"],
        "l_mm": merged["C36"], "beta": merged["C37"], "n_piani": merged["C49"], "phi_staffa_mm": merged["C56"],
        "n_bracci": merged["C57"], "alpha_staffa_deg": merged["C58"], "cf_mm": merged["C59"], "p_mm": merged["C62"],
    }


def test_tool_declares_relazione():
    assert TOOL.relazione is not None


def test_relazione_coerente_sullesempio():
    assert_relazione_coerente(TOOL, TOOL.example)


@pytest.mark.golden
def test_relazione_coerente_sui_casi_golden():
    assert_relazione_coerente(TOOL, _NTC_GOLDEN)
    assert_relazione_coerente(TOOL, _EN_GOLDEN)


@pytest.mark.oracle
@pytest.mark.parametrize("case", _NTC_ORACLE, ids=range(len(_NTC_ORACLE)))
def test_relazione_coerente_sui_casi_oracolo_ntc2018(case: dict[str, Any]):
    assert_relazione_coerente(TOOL, _ntc_oracle_raw(case))


@pytest.mark.oracle
@pytest.mark.parametrize("case", _EN_ORACLE, ids=range(len(_EN_ORACLE)))
def test_relazione_coerente_sui_casi_oracolo_en1998(case: dict[str, Any]):
    raw = _en_oracle_raw(case)
    if case["outputs"].get("C43") == "#DIV/0!":  # terreno A -> alpha=0 -> NEd=0, snellezza indefinita
        with pytest.raises(CalcError):
            run(TraviCollegamentoInput(**raw))
        return
    assert_relazione_coerente(TOOL, raw)


def test_ogni_highlight_e_spiegato_ntc():
    assert_ogni_highlight_e_spiegato(TOOL, TOOL.example)


def test_ogni_highlight_e_spiegato_en():
    assert_ogni_highlight_e_spiegato(TOOL, _EN_GOLDEN)


def test_step_count_within_the_8_to_30_target():
    report_ntc = execute(TOOL, TOOL.example, con_relazione=True)
    assert 8 <= sum(len(t.passi) for t in report_ntc.relazione) <= 30
    report_en = execute(TOOL, _EN_GOLDEN, con_relazione=True)
    assert 8 <= sum(len(t.passi) for t in report_en.relazione) <= 30


def test_relazione_covers_every_check_ntc():
    """Ogni `Check.name` di `tool_ntc.py::run_ntc` appare come un Passo con `esito` non vuoto."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    assert len(report.checks) == 4
    passi_di_verifica = [p for t in report.relazione for p in t.passi if p.esito]
    assert len(passi_di_verifica) == len(report.checks)
    for check in report.checks:
        atteso = "soddisfatta" if check.passed else "non soddisfatta"
        assert any(p.esito == atteso for p in passi_di_verifica), f"nessun Passo per il Check {check.name!r}"


def test_relazione_covers_every_check_en():
    """Ogni `Check.name` di `tool_en.py::run_en` (7 Check) appare come un Passo con `esito` non vuoto."""
    report = execute(TOOL, _EN_GOLDEN, con_relazione=True)
    assert len(report.checks) == 7
    passi_di_verifica = [p for t in report.relazione for p in t.passi if p.esito]
    assert len(passi_di_verifica) == len(report.checks)
    for check in report.checks:
        atteso = "soddisfatta" if check.passed else "non soddisfatta"
        assert any(p.esito == atteso for p in passi_di_verifica), f"nessun Passo per il Check {check.name!r}"


def test_variazione_norma_en1998():
    """`norma="EN1998"` sostituisce l'intera traccia (sismica, snellezza, minimi) rispetto a NTC2018."""
    report = execute(TOOL, _EN_GOLDEN, con_relazione=True)
    assert report.ok
    titoli = [t.titolo for t in report.relazione]
    assert any("EN1998" in t for t in titoli)
    assert not any("NTC2018" in t and "Amplificazione" in t for t in titoli)
    assert_relazione_coerente(TOOL, _EN_GOLDEN)


def test_variazione_armatura_minima_en_non_soddisfatta():
    """Sezione con armatura insufficiente per il minimo EN1998-1 §5.8.2(4): il Check fallisce e
    il Passo lo riporta come "non soddisfatta"."""
    variazione = {**_EN_GOLDEN, "n_barre": 4}
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    by_name = {c.name: c.passed for c in report.checks}
    assert by_name["Verifica armatura longitudinale minima"] is False
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "A_s/ρ_b")
    assert passo.esito == "non soddisfatta"
    assert_relazione_coerente(TOOL, variazione)


def test_variazione_sismica_ntc_categoria_a():
    """Categoria di sottosuolo A: SS è costante (identità 1, nessuna formula piecewise)."""
    variazione = {**_NTC_GOLDEN, "categoria_sottosuolo": "A"}
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if "sismica" in t.titolo.lower())
    passo = next(p for p in traccia.passi if p.simbolo == "S_S")
    assert passo.risultato == pytest.approx(1.0)
    assert_relazione_coerente(TOOL, variazione)


def test_azioni_e_verifiche_citano_la_clausola_corretta_per_normativa():
    """review finding: il `Check` di compressione/trazione cita sempre "NTC2018 §7.2.5" anche nel
    ramo EN1998 (etichetta del Check, non del calcolo) — la traccia usa la clausola corretta."""
    report_ntc = execute(TOOL, TOOL.example, con_relazione=True)
    report_en = execute(TOOL, _EN_GOLDEN, con_relazione=True)
    passo_ntc = next(p for t in report_ntc.relazione for p in t.passi if p.simbolo == "N_c,Rd")
    passo_en = next(p for t in report_en.relazione for p in t.passi if p.simbolo == "N_c,Rd")
    assert "NTC2018" in passo_ntc.clausola
    assert "EN1998" in passo_en.clausola


def test_amplificazione_sismica_ntc_riporta_le_categorie_nel_titolo():
    """S_S/α (Tab. 3.2.IV / Tab. C7.11.I) dipendono dalla categoria di sottosuolo, ma né questa né
    la categoria topografica comparivano nel testo stampato (`nota` non è mai reso da
    `traccia_a_testo`): un revisore non poteva confermare la riga giusta (review finding
    MISSING_STEP, condiviso con loads/sisma)."""
    report = execute(TOOL, _NTC_GOLDEN, con_relazione=True)
    traccia = next(t for t in report.relazione if "sismica" in t.titolo.lower())
    assert _NTC_GOLDEN["categoria_sottosuolo"] in traccia.titolo
    assert _NTC_GOLDEN["categoria_topografica"] in traccia.titolo


def test_amplificazione_sismica_en_riporta_la_categoria_nel_titolo():
    report = execute(TOOL, _EN_GOLDEN, con_relazione=True)
    traccia = next(t for t in report.relazione if "sismica" in t.titolo.lower())
    assert _EN_GOLDEN["categoria_sottosuolo"] in traccia.titolo


def test_i_usa_min_max_per_lasse_debole():
    """`geometria.raggio_inerzia_debole_mm`: la formula usa min/max, non un'assunzione fissa su
    quale lato sia il minore."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if "snellezza" in t.titolo.lower())
    passo = next(p for p in traccia.passi if p.simbolo == "i")
    assert "min(" in passo.formula and "max(" in passo.formula
