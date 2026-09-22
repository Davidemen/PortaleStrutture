"""`relazione.py` (docs/architecture-phase2.md §6, wave 2/3 adoption) for the three
`ca_fessurazione` tools: the harness on each tool's own example, on its golden case (reconstructed
from `test_golden.py`'s literals WITHOUT `legacy_compat`, since `relazione` only ever describes
standard mode — docs/architecture-phase2.md §1) and on every oracle case of `test_oracle_*.py`
(same fixtures, same column mapping, `legacy_compat` dropped), plus 3 variations across the
package that switch branches: the §C4.1.10 crack-spacing branch, a non-default crack-width class,
and a failing stress-limitation check."""
import json
from pathlib import Path
from typing import Any

import pytest

from strutture.members.ca_fessurazione.tool import TOOLS
from strutture.shared.tool import Tool, execute
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

_FIXTURES_DIR = Path(__file__).parents[2] / "fixtures"


def _tool(nome: str) -> Tool:
    return next(t for t in TOOLS if t.name == nome)


TOOL_LIMITAZIONE = _tool("ca-sle-limitazione-tensioni")
TOOL_APERTURA = _tool("ca-apertura-fessure")
TOOL_SEMPLIFICATA = _tool("ca-apertura-fessure-semplificata")

# Golden-case inputs (test_golden.py), WITHOUT `legacy_compat=True`: relazione never runs in
# legacy mode (docs/architecture-phase2.md §1), so these reproduce the sheet's own worked example
# read through the standard-mode formulas instead.
GOLDEN_LIMITAZIONE = {
    "rck_MPa": 45, "fyk_MPa": 450,
    "sigma_c_rar_1_MPa": 4.5, "sigma_c_qpe_1_MPa": 4.5, "sigma_s_rar_1_MPa": 255.8,
    "sigma_c_rar_2_MPa": 10, "sigma_c_qpe_2_MPa": 5.3, "sigma_s_rar_2_MPa": 274,
    "sigma_c_rar_3_MPa": 6, "sigma_c_qpe_3_MPa": 6, "sigma_s_rar_3_MPa": 237,
}
GOLDEN_APERTURA = {
    "classe_calcestruzzo": "C28/35", "tipo_barre": "barre aderenza migliorata",
    "tipo_sollecitazione": "caso di flessione", "durata_carico": "lunga durata",
    "classe_fessurazione": "w3 (0.40 mm)", "interferro_mm": 200, "sigma_s_MPa": 286,
    "es_MPa": 210000, "h_mm": 250, "x_mm": 75.84, "b_mm": 1000,
    "n1": 5, "phi1_mm": 20, "n2": 0, "phi2_mm": 0, "copriferro_mm": 35, "k3": 3.4, "k4": 0.425,
}
GOLDEN_SEMPLIFICATA = {
    "diametro_mm_1": 16, "sigma_fre_MPa_1": 231, "sigma_qpe_MPa_1": 218,
    "diametro_mm_2": 16, "sigma_fre_MPa_2": 206, "sigma_qpe_MPa_2": 233,
    "diametro_mm_3": 16, "sigma_fre_MPa_3": 180, "sigma_qpe_MPa_3": 171,
}

_SOLLECITAZIONE_SHEET_TO_TOOL = {
    "caso di flessione": "caso di flessione",
    "caso di trazione smplice": "caso di trazione semplice",
}
_DIAMETRI_ORACLE_SEMPLIFICATA: tuple[tuple[float, float, float], ...] = (
    (16, 16, 16), (10, 20, 32), (12, 14, 18), (22, 24, 26), (28, 30, 32), (20, 32, 10),
)


def _fixture(nome: str) -> list[dict[str, Any]]:
    return json.loads((_FIXTURES_DIR / nome).read_text())


def _oracle_limitazione(case: dict[str, Any]) -> dict[str, Any]:
    inp = case["inputs"]
    return {
        "rck_MPa": inp["C6"], "fyk_MPa": inp["C8"],
        "sigma_c_rar_1_MPa": inp["D13"], "sigma_c_qpe_1_MPa": inp["D14"], "sigma_s_rar_1_MPa": inp["D15"],
        "sigma_c_rar_2_MPa": inp["D21"], "sigma_c_qpe_2_MPa": inp["D22"], "sigma_s_rar_2_MPa": inp["D23"],
        "sigma_c_rar_3_MPa": inp["D29"], "sigma_c_qpe_3_MPa": inp["D30"], "sigma_s_rar_3_MPa": inp["D31"],
    }


def _oracle_apertura(case: dict[str, Any]) -> dict[str, Any]:
    inp = case["inputs"]
    return {
        "classe_calcestruzzo": inp["E4"], "tipo_barre": inp["E5"],
        "tipo_sollecitazione": _SOLLECITAZIONE_SHEET_TO_TOOL[inp["E6"]],
        "durata_carico": inp["E7"], "classe_fessurazione": inp["E8"],
        "interferro_mm": inp["E9"], "sigma_s_MPa": inp["E10"],
        "h_mm": inp["E23"], "x_mm": inp["E25"], "b_mm": inp["E26"],
        "n1": inp["E29"], "phi1_mm": inp["E30"], "n2": inp["E31"], "phi2_mm": inp["E32"],
        "copriferro_mm": inp["E38"],
    }


def _oracle_semplificata(case: dict[str, Any], diametri: tuple[float, float, float]) -> dict[str, Any]:
    inp = case["inputs"]
    d1, d2, d3 = diametri
    return {
        "diametro_mm_1": d1, "sigma_fre_MPa_1": inp["E21"], "sigma_qpe_MPa_1": inp["E22"],
        "diametro_mm_2": d2, "sigma_fre_MPa_2": inp["E43"], "sigma_qpe_MPa_2": inp["E44"],
        "diametro_mm_3": d3, "sigma_fre_MPa_3": inp["E66"], "sigma_qpe_MPa_3": inp["E67"],
    }


@pytest.mark.parametrize("tool", (TOOL_LIMITAZIONE, TOOL_APERTURA, TOOL_SEMPLIFICATA), ids=lambda t: t.name)
def test_tool_dichiara_relazione(tool: Tool) -> None:
    assert tool.relazione is not None


@pytest.mark.parametrize("tool", (TOOL_LIMITAZIONE, TOOL_APERTURA, TOOL_SEMPLIFICATA), ids=lambda t: t.name)
def test_relazione_coerente_sullesempio(tool: Tool) -> None:
    assert_relazione_coerente(tool, tool.example)


@pytest.mark.golden
def test_relazione_coerente_sul_caso_golden_limitazione_tensioni() -> None:
    assert_relazione_coerente(TOOL_LIMITAZIONE, GOLDEN_LIMITAZIONE)


@pytest.mark.golden
def test_relazione_coerente_sul_caso_golden_apertura_fessure() -> None:
    assert_relazione_coerente(TOOL_APERTURA, GOLDEN_APERTURA)


@pytest.mark.golden
def test_relazione_coerente_sul_caso_golden_apertura_fessure_semplificata() -> None:
    assert_relazione_coerente(TOOL_SEMPLIFICATA, GOLDEN_SEMPLIFICATA)


@pytest.mark.oracle
@pytest.mark.parametrize("case", _fixture("ca_fessurazione_limitazione_tensioni_oracle.json"), ids=range(6))
def test_relazione_coerente_sui_casi_oracolo_limitazione_tensioni(case: dict[str, Any]) -> None:
    assert_relazione_coerente(TOOL_LIMITAZIONE, _oracle_limitazione(case))


@pytest.mark.oracle
@pytest.mark.parametrize("case", _fixture("ca_fessurazione_apertura_fessure_oracle.json"), ids=range(6))
def test_relazione_coerente_sui_casi_oracolo_apertura_fessure(case: dict[str, Any]) -> None:
    assert_relazione_coerente(TOOL_APERTURA, _oracle_apertura(case))


@pytest.mark.oracle
@pytest.mark.parametrize(
    ("case", "diametri"),
    list(zip(_fixture("ca_fessurazione_apertura_fessure_semp_oracle.json"), _DIAMETRI_ORACLE_SEMPLIFICATA, strict=True)),
    ids=range(6),
)
def test_relazione_coerente_sui_casi_oracolo_apertura_fessure_semplificata(case: dict[str, Any], diametri: tuple[float, float, float]) -> None:
    assert_relazione_coerente(TOOL_SEMPLIFICATA, _oracle_semplificata(case, diametri))


@pytest.mark.parametrize("tool", (TOOL_LIMITAZIONE, TOOL_APERTURA, TOOL_SEMPLIFICATA), ids=lambda t: t.name)
def test_ogni_highlight_e_spiegato(tool: Tool) -> None:
    assert_ogni_highlight_e_spiegato(tool, tool.example)


@pytest.mark.parametrize("tool", (TOOL_LIMITAZIONE, TOOL_APERTURA, TOOL_SEMPLIFICATA), ids=lambda t: t.name)
def test_step_count_within_the_8_to_30_target(tool: Tool) -> None:
    report = execute(tool, tool.example, con_relazione=True)
    totale = sum(len(t.passi) for t in report.relazione)
    assert 8 <= totale <= 30


@pytest.mark.parametrize("tool", (TOOL_LIMITAZIONE, TOOL_APERTURA, TOOL_SEMPLIFICATA), ids=lambda t: t.name)
def test_relazione_covers_every_check_the_tool_declares(tool: Tool) -> None:
    """Every `Check` of the tool's example run must appear as a `Passo` with a matching `esito`
    somewhere in the trace (docs/architecture-phase2.md §6: "every Check")."""
    report = execute(tool, tool.example, con_relazione=True)
    passi_di_verifica = [p for t in report.relazione for p in t.passi if p.esito]
    assert len(passi_di_verifica) == len(report.checks)
    for check in report.checks:
        atteso = "soddisfatta" if check.passed else "non soddisfatta"
        assert any(p.esito == atteso for p in passi_di_verifica), f"nessun Passo per il Check {check.name!r}"


def test_variazione_ramo_c4_1_10_spaziatura_fessure() -> None:
    """Interferro molto ampio: il ramo di spaziatura selezionato è §C4.1.10 anziché §C4.1.7
    (`spaziatura_fessure.ramo_spaziatura`)."""
    variazione = {**GOLDEN_APERTURA, "interferro_mm": 500}
    report = execute(TOOL_APERTURA, variazione, con_relazione=True)
    assert report.ok
    assert report.data.fessurazione.ramo == "C4.1.10"
    assert_relazione_coerente(TOOL_APERTURA, variazione)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo.startswith("Δs_m"))
    assert "C4.1.10" in passo.simbolo


def test_delta_sm_riporta_il_ramo_selezionato_nel_simbolo() -> None:
    """review finding MISSING_STEP: s_lim veniva stampato e mai più usato — il confronto
    interferro < s_lim che seleziona il ramo (§C4.1.7 vs §C4.1.10) esisteva solo nella `nota`, che
    `traccia_a_testo` non stampa mai. Il ramo selezionato deve comparire nel simbolo di Δs_m."""
    report = execute(TOOL_APERTURA, GOLDEN_APERTURA, con_relazione=True)
    assert report.data.fessurazione.ramo == "C4.1.7"
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo.startswith("Δs_m"))
    assert passo.simbolo != "Δs_m"
    assert "C4.1.7" in passo.simbolo


def test_variazione_classe_apertura_fessura_non_ordinaria() -> None:
    """Condizioni ambientali/sensibilità dell'armatura diverse dal default cambiano la classe
    w1/w2/w3 risolta da NTC2018 Tab. 4.1.IV (`classe_apertura_normativa`)."""
    variazione = {**GOLDEN_SEMPLIFICATA, "condizioni_ambientali": "aggressive", "sensibilita_armatura": "poco sensibile"}
    report = execute(TOOL_SEMPLIFICATA, variazione, con_relazione=True)
    assert report.ok
    assert report.data.sezioni[0].classe_fre != "w3"
    assert_relazione_coerente(TOOL_SEMPLIFICATA, variazione)


def test_variazione_check_fallito_limitazione_tensioni() -> None:
    """Una tensione di calcestruzzo eccessiva fa fallire il Check della sezione 1 in modalità
    standard: l'esito del Passo deve seguirlo."""
    variazione = {**GOLDEN_LIMITAZIONE, "sigma_c_rar_1_MPa": 1000.0}
    report = execute(TOOL_LIMITAZIONE, variazione, con_relazione=True)
    assert report.ok
    assert report.data.sezioni[0].verificato_c_rar is False
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "σ_c,rara" and p.esito)
    assert passo.esito == "non soddisfatta"
    assert_relazione_coerente(TOOL_LIMITAZIONE, variazione)
