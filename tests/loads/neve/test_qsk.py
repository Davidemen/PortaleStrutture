import pytest

from strutture.loads.neve.qsk import qsk1, qsk2, qsk_accumulo, qsk_falda


@pytest.mark.unit
def test_qsk1_exact_zonal_constants():
    assert qsk1("I (alpina)") == pytest.approx(1.5)
    assert qsk1("II") == pytest.approx(1.0)
    assert qsk1("III") == pytest.approx(0.6)


@pytest.mark.unit
def test_qsk2_altitude_formula():
    assert qsk2("I (alpina)", 0) == pytest.approx(1.39)
    assert qsk2("II", 481) == pytest.approx(0.85 * 2)


@pytest.mark.unit
def test_qsk_falda_branch_threshold():
    assert qsk_falda("II", 199.999) == pytest.approx(qsk1("II"))
    assert qsk_falda("II", 200) == pytest.approx(qsk1("II"))
    assert qsk_falda("II", 200.001) == pytest.approx(qsk2("II", 200.001))


@pytest.mark.unit
@pytest.mark.parametrize("zona", ["I (alpina)", "I (mediterranea)", "II", "III"])
def test_qsk_falda_boundary_at_200m_uses_constant_in_every_zone_ntc_3_4_2(zona):
    """NTC2018 §3.4.2: qsk1 (constant) applies for as <= 200 m, qsk2(as) only for as > 200 m.
    Code-standard mode (legacy_compat=False, default) must select qsk1 at exactly 200 m in every
    zone -- previously the branch test was `altitude_m < 200`, which took the qsk2 altitude
    formula at as=200 exactly and was non-conservative (e.g. zona II: 0.9970 vs the correct 1.00).
    """
    assert qsk_falda(zona, 200) == pytest.approx(qsk1(zona))
    assert qsk_falda(zona, 200.0001) == pytest.approx(qsk2(zona, 200.0001))


@pytest.mark.unit
def test_qsk_falda_legacy_mode_keeps_sheets_strict_less_than_200_boundary():
    """legacy_compat=True reproduces `Neve!H10`'s own `IF(as<200, qsk1, qsk2)` byte-for-byte, so
    as=200 m exactly still takes the qsk2 altitude formula there -- unlike code-standard mode.
    Keeps the oracle/golden fixtures (which use legacy_compat=True) green.
    """
    assert qsk_falda("II", 200, legacy_compat=True) == pytest.approx(qsk2("II", 200))
    assert qsk_falda("II", 199.999, legacy_compat=True) == pytest.approx(qsk1("II"))


@pytest.mark.unit
def test_qsk_falda_mediterranea_range_lookup_bug_only_in_legacy():
    """Bug 5 + `Tabelle!A3:A6`'s TRUE-lookup: legacy misresolves 'I (mediterranea)' to the
    'I (alpina)' row (confirmed against `tests/fixtures/neve_carico_falda_oracle.json` case 2,
    Milano/400m); fixed mode uses the zone's own coefficients.
    """
    fixed = qsk_falda("I (mediterranea)", 400, legacy_compat=False)
    legacy = qsk_falda("I (mediterranea)", 400, legacy_compat=True)
    assert fixed == pytest.approx(qsk2("I (mediterranea)", 400))
    assert legacy == pytest.approx(qsk2("I (alpina)", 400))
    assert fixed != pytest.approx(legacy)


@pytest.mark.unit
def test_qsk_accumulo_branch_inversion_bug_3():
    """Below 200m: fixed mode uses the constant (qsk1); legacy inverts to the altitude formula."""
    fixed = qsk_accumulo("II", 150, legacy_compat=False, neve_altitude_m=None)
    legacy = qsk_accumulo("II", 150, legacy_compat=True, neve_altitude_m=None)
    assert fixed == pytest.approx(qsk1("II"))
    assert legacy == pytest.approx(qsk2("II", 150))


@pytest.mark.unit
def test_qsk_accumulo_bug_1_cross_sheet_contamination():
    """Legacy mode's qsk2 branch uses `neve_altitude_m` (`Neve!H9`), not this sheet's own altitude,
    when supplied; falls back to its own altitude only if the caller doesn't supply it.
    """
    contaminated = qsk_accumulo("I (alpina)", 150, legacy_compat=True, neve_altitude_m=900)
    own_altitude_fallback = qsk_accumulo("I (alpina)", 150, legacy_compat=True, neve_altitude_m=None)
    assert contaminated == pytest.approx(qsk2("I (alpina)", 900))
    assert own_altitude_fallback == pytest.approx(qsk2("I (alpina)", 150))
    assert contaminated != pytest.approx(own_altitude_fallback)


@pytest.mark.unit
def test_qsk_accumulo_fixed_mode_ignores_neve_altitude_and_branch_bugs():
    fixed = qsk_accumulo("I (alpina)", 250, legacy_compat=False, neve_altitude_m=999)
    assert fixed == pytest.approx(qsk2("I (alpina)", 250))


@pytest.mark.unit
def test_qsk_accumulo_fixed_mode_boundary_at_200m_uses_constant():
    """Fixed mode delegates to `qsk_falda` (NTC2018 §3.4.2 boundary), so as=200 m exactly must
    also select qsk1 here, not just in `qsk_falda` directly."""
    fixed = qsk_accumulo("II", 200, legacy_compat=False, neve_altitude_m=None)
    assert fixed == pytest.approx(qsk1("II"))
