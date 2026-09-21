import pytest

from strutture.members.ca_fessurazione.models import AperturaFessureSempInput, LimitazioneTensioniInput
from strutture.members.ca_fessurazione.tool import TOOLS
from strutture.shared.tool import execute

pytestmark = pytest.mark.unit


def test_tools_are_registered_with_unique_names():
    names = [tool.name for tool in TOOLS]
    assert names == ["ca-sle-limitazione-tensioni", "ca-apertura-fessure", "ca-apertura-fessure-semplificata"]
    assert len(set(names)) == len(names)


def test_limitazione_tensioni_run_emits_one_check_per_row():
    tool = next(t for t in TOOLS if t.name == "ca-sle-limitazione-tensioni")
    report = tool.run(
        LimitazioneTensioniInput(
            rck_MPa=45,
            fyk_MPa=450,
            sigma_c_rar_1_MPa=4.5, sigma_c_qpe_1_MPa=4.5, sigma_s_rar_1_MPa=255.8,
            sigma_c_rar_2_MPa=10, sigma_c_qpe_2_MPa=5.3, sigma_s_rar_2_MPa=274,
            sigma_c_rar_3_MPa=6, sigma_c_qpe_3_MPa=6, sigma_s_rar_3_MPa=237,
            legacy_compat=True,
        )
    )
    assert report.ok
    assert len(report.checks) == 9  # 3 sections * 3 checks
    assert all(check.passed for check in report.checks)
    assert all(check.clause == "NTC2018 §4.1.2.2.5" for check in report.checks)


def test_execute_maps_calc_error_to_failed_report():
    """`ca-apertura-fessure-semplificata`'s CalcError (off-table diameter, legacy mode) is mapped
    to Report(ok=False) by the generic `strutture.shared.tool.execute`, not raised to the caller."""
    tool = next(t for t in TOOLS if t.name == "ca-apertura-fessure-semplificata")
    raw_inputs = {
        "diametro_mm_1": 15, "sigma_fre_MPa_1": 100, "sigma_qpe_MPa_1": 100,
        "diametro_mm_2": 16, "sigma_fre_MPa_2": 100, "sigma_qpe_MPa_2": 100,
        "diametro_mm_3": 16, "sigma_fre_MPa_3": 100, "sigma_qpe_MPa_3": 100,
        "legacy_compat": True,
    }
    report = execute(tool, raw_inputs)
    assert not report.ok
    assert report.errors
    assert "Tab. C4.1.II" in report.errors[0]


def test_execute_maps_validation_error_to_failed_report():
    tool = next(t for t in TOOLS if t.name == "ca-apertura-fessure-semplificata")
    report = execute(tool, {"diametro_mm_1": -1})
    assert not report.ok
    assert report.errors


def test_apertura_fessure_semp_input_model_matches_tool():
    tool = next(t for t in TOOLS if t.name == "ca-apertura-fessure-semplificata")
    assert tool.input_model is AperturaFessureSempInput
