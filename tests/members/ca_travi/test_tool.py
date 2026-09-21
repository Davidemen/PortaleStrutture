import pytest

from strutture.members.ca_travi.models import TraveRettangolareInput
from strutture.members.ca_travi.tool import TOOLS, run
from strutture.shared.report import CalcError
from strutture.shared.tool import execute

BASE_KWARGS = {
    "b_mm": 600, "h_mm": 400, "tipo_acciaio": "RB500W", "tipo_cls": "C35/45", "copriferro_mm": 70,
    "n_ferri1": 5, "diametro_ferri1_mm": 20,
    "diametro_staffe1_mm": 12, "passo_staffe1_mm": 115,
    "ved_kN": 138, "med_slu_kNm": 318, "med_rara_kNm": 239, "med_qp_kNm": 200, "mrc_kNm": 350, "lt_m": 8,
}


@pytest.mark.unit
def test_tool_is_registered_with_expected_name_and_models():
    assert len(TOOLS) == 1
    tool = TOOLS[0]
    assert tool.name == "ca-trave-rettangolare"
    assert tool.input_model is TraveRettangolareInput


@pytest.mark.unit
def test_execute_validates_raw_dict_inputs_end_to_end():
    tool = TOOLS[0]
    report = execute(tool, {**BASE_KWARGS, "legacy_compat": True})
    assert report.ok
    assert report.data.flessione.mrd_kNm == pytest.approx(207.01, rel=1e-4)


@pytest.mark.unit
def test_execute_reports_validation_errors_without_raising():
    tool = TOOLS[0]
    report = execute(tool, {**BASE_KWARGS, "b_mm": -1})
    assert not report.ok
    assert report.errors


@pytest.mark.unit
def test_over_reinforced_shear_raises_calc_error_via_run():
    inputs = TraveRettangolareInput(
        **{**BASE_KWARGS, "diametro_staffe1_mm": 20, "passo_staffe1_mm": 50, "n_bracci_staffe1": 4}
    )
    with pytest.raises(CalcError):
        run(inputs)


@pytest.mark.unit
def test_run_no_longer_warns_about_unused_lt():
    """HIGH finding fixed: `lt_m` is now used by the capacity-design shear formula in
    `legacy_compat=False`, so the old inert-input warning no longer applies."""
    report = run(TraveRettangolareInput(**BASE_KWARGS))
    assert not any("Lt" in w for w in report.warnings)


@pytest.mark.unit
def test_run_reports_all_checks_including_sls_and_seismic_ductility():
    # 4 armatura + 3 seismic-ductility (rho_min/rho_max/As' sismici) + 4 flessione/taglio/capacity
    # (incl. new "Duttilità sezione") + 4 SLS stress checks + 1 crack-width-class conformity check
    # (BASE_KWARGS defaults land on a matching classe_normativa, so it is emitted).
    report = run(TraveRettangolareInput(legacy_compat=True, **BASE_KWARGS))
    assert len(report.checks) == 16
    assert all(c.clause.startswith("NTC2018") for c in report.checks)


@pytest.mark.unit
def test_run_fixed_mode_capacity_design_shear_uses_lt_and_returns_a_force():
    """HIGH finding fixed: NTC2018 §7.4.4.1.1 VEd = (Mi,d+Mj,d)/Lt; the legacy value (a bare
    moment) must differ from the fixed value once Lt is applied."""
    legacy = run(TraveRettangolareInput(legacy_compat=True, **BASE_KWARGS)).data
    fixed = run(TraveRettangolareInput(legacy_compat=False, **BASE_KWARGS)).data
    assert fixed.dettagli_costruttivi.ved_max_kN != pytest.approx(legacy.dettagli_costruttivi.ved_max_kN)
    # fixed mode's own MRb differs slightly from legacy's (upstream fcd legacy_compat drift, not
    # a ca-travi bug), so recompute the expectation from fixed's own MRb/MRc rather than legacy's.
    fattore = min(1.0, BASE_KWARGS["mrc_kNm"] / fixed.flessione.mrd_kNm)
    expected = 2.0 * fixed.flessione.mrd_kNm * fattore / BASE_KWARGS["lt_m"]
    assert fixed.dettagli_costruttivi.ved_max_kN == pytest.approx(expected, rel=1e-6)


@pytest.mark.unit
def test_check_names_are_readable_italian_phrases_not_python_keys():
    """Design review (P0): `Check(name=...)` must be a readable Italian phrase, never a raw
    snake_case Python key, so no check name may contain an underscore."""
    tool = TOOLS[0]
    report = execute(tool, tool.example)
    assert report.ok, report.errors
    assert report.checks
    for check in report.checks:
        assert "_" not in check.name, check.name


@pytest.mark.unit
def test_classe_duttilita_cda_changes_lunghezza_critica_and_gamma_rd():
    cdb = run(TraveRettangolareInput(classe_duttilita="CDB", **BASE_KWARGS)).data
    cda = run(TraveRettangolareInput(classe_duttilita="CDA", **BASE_KWARGS)).data
    assert cda.dettagli_costruttivi.lunghezza_critica_mm == pytest.approx(1.5 * cdb.dettagli_costruttivi.lunghezza_critica_mm)
    assert cda.dettagli_costruttivi.ved_max_kN > cdb.dettagli_costruttivi.ved_max_kN


def test_capacity_design_shear_includes_the_gravity_term_and_warns_when_it_is_missing():
    """NTC2018 §7.4.4.1.1: V_Ed = γ_Rd·ΣM_Rd/L_t + V_g. With V_g left at 0 the check is incomplete
    (non-conservative): the tool says so; with V_g given, the demand grows by exactly V_g."""
    from strutture.members.ca_travi.tool import TOOLS
    from strutture.shared.tool import execute

    tool = TOOLS[0]
    base = {k: v for k, v in tool.example.items() if k != "legacy_compat"}
    senza = execute(tool, base)
    con = execute(tool, {**base, "v_gravita_kN": 40.0})
    assert senza.ok and con.ok
    assert con.data.dettagli_costruttivi.ved_max_kN == pytest.approx(senza.data.dettagli_costruttivi.ved_max_kN + 40.0)
    avviso = "carichi gravitazionali"
    assert any(avviso in w for w in senza.warnings)
    assert not any(avviso in w for w in con.warnings)
