"""Composition-level tests for the `ca-mensola-tozza` Tool: registration, divergences end-to-end,
boundary branches."""
import pytest

from strutture.members.ca_mensole.models import MensolaTozzaInput
from strutture.members.ca_mensole.tool import TOOLS, run
from strutture.shared.report import CalcError

_BASE = {
    "a_mm": 177, "h_mm": 450, "b_mm": 800, "c_mm": 50, "ped_kN": 136, "hed_kN": 0,
    "acciaio": "B450C", "calcestruzzo": "C32/40",
    "n_hor": 8, "phi_hor_mm": 12, "n_incl": 0, "phi_incl_mm": 0, "angolo_incl_deg": 0,
    "n_staffe": 3, "phi_staffe_mm": 12, "staffe_verticali": "NO",
}


@pytest.mark.unit
def test_tool_registered_once() -> None:
    assert len(TOOLS) == 1
    tool = TOOLS[0]
    assert tool.name == "ca-mensola-tozza"
    assert tool.input_model is MensolaTozzaInput


@pytest.mark.unit
def test_run_success_produces_all_groups_and_checks() -> None:
    report = run(MensolaTozzaInput(**_BASE, legacy_compat=True))
    assert report.ok
    assert report.data.materiali is not None
    assert report.data.geometria is not None
    assert report.data.armature is not None
    assert report.data.capacita is not None
    assert len(report.checks) == 3


@pytest.mark.unit
def test_run_fcd_divergence_end_to_end() -> None:
    """legacy_compat toggles the fck fill-down bug through the whole tool, changing PRC."""
    legacy = run(MensolaTozzaInput(**_BASE, legacy_compat=True))
    fixed = run(MensolaTozzaInput(**_BASE, legacy_compat=False))
    assert legacy.data.materiali.fcd_MPa != pytest.approx(fixed.data.materiali.fcd_MPa)
    assert legacy.data.capacita.prc_kN != pytest.approx(fixed.data.capacita.prc_kN)


@pytest.mark.unit
def test_run_feb22k_legacy_raises_calc_error() -> None:
    inputs = MensolaTozzaInput(**{**_BASE, "acciaio": "FeB22k"}, legacy_compat=True)
    with pytest.raises(CalcError):
        run(inputs)


@pytest.mark.unit
def test_run_feb22k_code_standard_succeeds() -> None:
    inputs = MensolaTozzaInput(**{**_BASE, "acciaio": "FeB22k"}, legacy_compat=False)
    report = run(inputs)
    assert report.ok


@pytest.mark.unit
def test_run_as_lnk_boundary_a_equals_half_h() -> None:
    """a == 0.5h takes the long-span branch (strict `<` in the sheet's IF, spec §4 step 11)."""
    report = run(MensolaTozzaInput(**{**_BASE, "a_mm": 225.0, "h_mm": 450.0}, legacy_compat=True))
    expected = 0.5 * _BASE["ped_kN"] * 1000 / report.data.materiali.fyd_MPa
    assert report.data.armature.as_lnk_min_mm2 == pytest.approx(expected, rel=1e-9)
