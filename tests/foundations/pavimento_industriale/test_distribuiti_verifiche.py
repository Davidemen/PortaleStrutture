"""Unit tests for `verifiche_distribuito` (spec steps 6-12), including the fcfk/fcfd divergence
(architecture-batch2.md §7 `pavimento G22`, docs/divergences/pavimento-industriale.md)."""
import pytest

from strutture.foundations.pavimento_industriale.distribuiti_verifiche import verifiche_distribuito

_ARGS = {
    "m_slu_sup_Nmm_m": 7758.68, "m_slu_inf_Nmm_m": 7435.78,
    "m_sle_freq_sup_Nmm_m": 4655.21, "m_sle_freq_inf_Nmm_m": 4461.47,
    "w_mm3_m": 6.66667e6, "fcfk_MPa": 2.18973, "fcfd_MPa": 1.45982, "fctm_MPa": 2.60682, "mrd_Nmm_m": 15046.9,
}


@pytest.mark.unit
def test_legacy_reproduces_sheets_inconsistent_denominators() -> None:
    """legacy_compat=True: sup divides by fcfk (characteristic), inf by fcfd (design) -- the sheet bug."""
    result = verifiche_distribuito(**_ARGS, legacy_compat=True)
    assert result.verifica_tensionale_sup.limit == pytest.approx(2.18973, rel=1e-5)
    assert result.verifica_tensionale_inf.limit == pytest.approx(1.45982, rel=1e-5)
    assert result.verifica_tensionale_sup.value / result.verifica_tensionale_sup.limit == pytest.approx(0.531482, rel=1e-4)
    assert result.verifica_tensionale_inf.value / result.verifica_tensionale_inf.limit == pytest.approx(0.764045, rel=1e-4)


@pytest.mark.unit
def test_fixed_uses_fcfd_for_both_sup_and_inf() -> None:
    """legacy_compat=False (fix, docs/divergences/pavimento-industriale.md): both sup and inf use fcfd."""
    result = verifiche_distribuito(**_ARGS, legacy_compat=False)
    assert result.verifica_tensionale_sup.limit == pytest.approx(1.45982, rel=1e-5)
    assert result.verifica_tensionale_inf.limit == pytest.approx(1.45982, rel=1e-5)


@pytest.mark.unit
def test_crack_and_rebar_checks_match_golden_case() -> None:
    result = verifiche_distribuito(**_ARGS, legacy_compat=True)
    assert result.sigma_c_t_sup_MPa == pytest.approx(0.698281, rel=1e-5)
    assert result.verifica_fessurazione_sup.value / result.verifica_fessurazione_sup.limit == pytest.approx(0.32144, rel=1e-4)
    assert result.verifica_fessurazione_inf.value / result.verifica_fessurazione_inf.limit == pytest.approx(0.308063, rel=1e-4)
    assert result.verifica_armatura_sup.value / result.verifica_armatura_sup.limit == pytest.approx(0.515634, rel=1e-4)
    assert result.verifica_armatura_inf.value / result.verifica_armatura_inf.limit == pytest.approx(0.494175, rel=1e-4)
    assert all(check.passed for check in (
        result.verifica_tensionale_sup, result.verifica_tensionale_inf,
        result.verifica_fessurazione_sup, result.verifica_fessurazione_inf,
        result.verifica_armatura_sup, result.verifica_armatura_inf,
    ))


@pytest.mark.unit
def test_tl_massimo_is_worst_of_all_ratios() -> None:
    result = verifiche_distribuito(**_ARGS, legacy_compat=True)
    assert result.tl_massimo == pytest.approx(0.764045, rel=1e-4)


@pytest.mark.unit
def test_fixed_stress_check_fails_when_sheet_bug_would_pass() -> None:
    """Boundary case built to demonstrate the numeric impact of the fix: a sup stress between fcfd
    and fcfk passes under legacy_compat=True (checked against the higher fcfk) but fails once the
    fix applies fcfd to both."""
    args = {**_ARGS, "m_slu_sup_Nmm_m": 7758.68 * 1.4}  # push sigma_sup between fcfd and fcfk
    legacy = verifiche_distribuito(**args, legacy_compat=True)
    fixed = verifiche_distribuito(**args, legacy_compat=False)
    assert legacy.verifica_tensionale_sup.passed is True
    assert fixed.verifica_tensionale_sup.passed is False
