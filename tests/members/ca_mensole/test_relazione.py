"""`relazione.py` (docs/architecture-phase2.md §6, wave 2/3 adoption) for `ca-mensola-tozza`: the
harness on the tool's example, on the golden case of `test_golden.py` (identical numeric inputs
to the example — `docs/specs/ca-mensole.md` §8 — with `legacy_compat` dropped, since `relazione`
only ever describes standard mode) and on every oracle case of
`test_oracle_ca_mensola_tozza.py` (`tests/fixtures/ca_mensola_tozza_oracle.json`, run here in
STANDARD mode: the fixture's own `legacy_compat=True` FeB22k-#N/A case succeeds instead, since
standard mode uses the shared union rebar table), plus 3 variations that switch branches: the
long-span `A_s,lnk,min` branch, the `staffe_verticali='SI'` amplification coefficient, and a
failing ULS check."""
import json
from pathlib import Path
from typing import Any

import pytest

from strutture.members.ca_mensole.tool import TOOLS
from strutture.shared.tool import execute
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOL = TOOLS[0]

_ORACLE_FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "ca_mensola_tozza_oracle.json").read_text())

# Golden case (test_golden.py) WITHOUT legacy_compat=True — identical to `TOOL.example`, kept
# separate so the golden fixture stays traceable to its own source test.
GOLDEN_KWARGS = {
    "a_mm": 177, "h_mm": 450, "b_mm": 800, "c_mm": 50, "ped_kN": 136, "hed_kN": 0,
    "acciaio": "B450C", "calcestruzzo": "C32/40",
    "n_hor": 8, "phi_hor_mm": 12, "n_incl": 0, "phi_incl_mm": 0, "angolo_incl_deg": 0,
    "n_staffe": 3, "phi_staffe_mm": 12, "staffe_verticali": "NO",
}


def _oracle_raw_inputs(case: dict[str, Any]) -> dict[str, Any]:
    cells = case["inputs"]
    return {
        "a_mm": cells["H5"], "h_mm": cells["H6"], "b_mm": cells["H7"], "c_mm": cells["H8"],
        "ped_kN": cells["H9"], "hed_kN": cells["H10"],
        "acciaio": cells["H14"], "calcestruzzo": cells["H15"],
        "n_hor": cells["H16"], "phi_hor_mm": cells["H17"], "n_incl": cells["H18"], "phi_incl_mm": cells["H19"],
        "angolo_incl_deg": cells["H22"], "n_staffe": cells["H24"], "phi_staffe_mm": cells["H25"],
        "staffe_verticali": cells["H29"],
    }


def test_tool_declares_relazione() -> None:
    assert TOOL.relazione is not None


def test_relazione_coerente_sullesempio() -> None:
    assert_relazione_coerente(TOOL, TOOL.example)


@pytest.mark.golden
def test_relazione_coerente_sul_caso_golden() -> None:
    assert_relazione_coerente(TOOL, GOLDEN_KWARGS)


@pytest.mark.oracle
@pytest.mark.parametrize("case", _ORACLE_FIXTURE, ids=range(len(_ORACLE_FIXTURE)))
def test_relazione_coerente_sui_casi_oracolo(case: dict[str, Any]) -> None:
    assert_relazione_coerente(TOOL, _oracle_raw_inputs(case))


def test_ogni_highlight_e_spiegato() -> None:
    assert_ogni_highlight_e_spiegato(TOOL, TOOL.example)


def test_step_count_within_the_8_to_30_target() -> None:
    report = execute(TOOL, TOOL.example, con_relazione=True)
    totale = sum(len(t.passi) for t in report.relazione)
    assert 8 <= totale <= 30


def test_relazione_covers_every_check_the_tool_declares() -> None:
    report = execute(TOOL, TOOL.example, con_relazione=True)
    assert len(report.checks) == 3
    passi_di_verifica = [p for t in report.relazione for p in t.passi if p.esito]
    assert len(passi_di_verifica) == len(report.checks)
    for check in report.checks:
        atteso = "soddisfatta" if check.passed else "non soddisfatta"
        assert any(p.esito == atteso for p in passi_di_verifica), f"nessun Passo per il Check {check.name!r}"


def test_variazione_ramo_campata_lunga_as_lnk_min() -> None:
    """a >= 0,5h: il ramo di A_s,lnk,min diventa 0,5·PEd/fyd anziché 0,25·A_s,hor."""
    variazione = {**TOOL.example, "a_mm": 300}
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    assert variazione["a_mm"] >= 0.5 * variazione["h_mm"]
    assert_relazione_coerente(TOOL, variazione)


def test_variazione_staffe_verticali_presenti() -> None:
    """staffe_verticali='SI': il coefficiente c passa da 1,0 a 1,5 nella capacità del puntone."""
    variazione = {**TOOL.example, "staffe_verticali": "SI"}
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    assert report.data.capacita.c_coeff == pytest.approx(1.5)
    assert_relazione_coerente(TOOL, variazione)


def test_variazione_check_fallito_uls() -> None:
    """Un carico verticale eccessivo fa fallire il Check ULS (PR <= PEd) in modalità standard."""
    variazione = {**TOOL.example, "ped_kN": 2000.0}
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    by_name = {c.name: c.passed for c in report.checks}
    assert by_name["Verifica PR > PEd"] is False
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "P_Ed < P_R")
    assert passo.esito == "non soddisfatta"
    assert_relazione_coerente(TOOL, variazione)


def test_coefficiente_staffe_non_si_chiama_c_come_il_copriferro() -> None:
    """review finding MISLEADING: 'c' indica sia il copriferro (Geometria, d=h-c) sia il
    coefficiente adimensionale che amplifica P_Rc — nella stessa Sviluppo dei calcoli. Il
    coefficiente deve avere un simbolo distinto (es. k_staffe)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passi = [p for t in report.relazione for p in t.passi]
    assert not any(p.simbolo == "c" for p in passi), "il simbolo nudo 'c' e' ambiguo (copriferro vs coefficiente)"
    passo_copriferro = next(p for p in passi if p.simbolo == "d")
    assert any(v.simbolo == "c" for v in passo_copriferro.valori)  # il copriferro resta 'c' in d=h-c
    passo_coeff = next(p for p in passi if p.simbolo.startswith("k_staffe"))
    assert "staffe verticali" in passo_coeff.simbolo.lower() or "staffe verticali" in passo_coeff.formula.lower()


def test_p_rc_e_il_coefficiente_staffe_citano_formula_empirica_non_ec3() -> None:
    """review finding WRONG_CLAUSE: `capacita.py` marca STRUT_EFFECTIVENESS_COEFF e
    STAFFE_VERTICALI_C con clausola '?' (provenienza sconosciuta); il passo P_Rc e il passo del
    coefficiente non possono citare 'NTC2018 §4.1.6.1.3 / EN 1992-1-1 §6.5', che per il puntone
    dà σ_Rd,max=0,6·ν'·f_cd, non questa formula, e non prevede alcun bonus del 50% per staffe."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passi = [p for t in report.relazione for p in t.passi]
    passo_prc = next(p for p in passi if p.simbolo == "P_Rc")
    passo_coeff = next(p for p in passi if p.simbolo.startswith("k_staffe"))
    for passo in (passo_prc, passo_coeff):
        assert "EN 1992-1-1 §6.5" not in passo.clausola
        assert "empirica" in passo.clausola.lower()


def test_variazione_armatura_inclinata_angolo_non_nullo() -> None:
    """Ferri inclinati presenti a 45°: verifica che `sin(α)` nella formula di ΔP_R usi i gradi
    (α ha unità '°' fra i Valore del passo) e non i radianti — l'esempio e il caso golden hanno
    sempre angolo_incl_deg=0, che non distinguerebbe i due rami."""
    variazione = {**TOOL.example, "n_incl": 4, "phi_incl_mm": 14, "angolo_incl_deg": 45}
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    assert report.data.capacita.dpr_kN > 0
    assert_relazione_coerente(TOOL, variazione)
