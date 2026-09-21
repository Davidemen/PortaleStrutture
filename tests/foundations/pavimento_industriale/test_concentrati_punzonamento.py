"""Unit tests for `punzonamento` (spec steps 7-10), including the u1 h-vs-d divergence
(architecture-batch2.md §7 `pavimento M33/N33`, docs/divergences/pavimento-industriale.md)."""
import pytest

from strutture.foundations.pavimento_industriale.concentrati_punzonamento import punzonamento

_ARGS = {"bx_mm": 500.0, "by_mm": 100.0, "d_mm": 170.0, "h_mm": 200.0, "v1": 0.54, "fcd_MPa": 14.1667, "v_min_MPa": 0.494975}


@pytest.mark.unit
def test_centro_matches_golden_case() -> None:
    result = punzonamento("centro", 23.25, **_ARGS, legacy_compat=True)
    assert result.v_ed_kN == pytest.approx(26.7375, rel=1e-5)
    assert result.u0_mm == pytest.approx(1200.0)
    assert result.v_rd_max_MPa == pytest.approx(3.825, rel=1e-5)
    assert result.v_ed0_MPa == pytest.approx(0.131066, rel=1e-5)
    assert result.u1_mm == pytest.approx(3336.28, rel=1e-5)
    assert result.v_ed1_MPa == pytest.approx(0.0471421, rel=1e-5)
    assert result.verifica_u0.passed and result.verifica_u1.passed


@pytest.mark.unit
def test_vrd_max_legacy_uses_ntc_05_coefficient() -> None:
    """legacy_compat=True must keep reproducing the sheet's NTC2018 §4.1.2.3.5.2 coefficient (0.5)."""
    result = punzonamento("centro", 23.25, **_ARGS, legacy_compat=True)
    assert result.v_rd_max_MPa == pytest.approx(0.5 * 0.54 * 14.1667, rel=1e-6)
    assert result.verifica_u0.clause == "NTC2018 §4.1.2.3.5.2"


@pytest.mark.unit
def test_vrd_max_fixed_uses_en_04_coefficient() -> None:
    """legacy_compat=False, `coeff_vrd_max` left at its default: the default is explicitly
    `V_RD_MAX_COEFF_A1_2014` (0.4, EN 1992-1-1/A1:2014 §6.4.5(3), the more conservative of the two
    disputed values -- docs/divergences/ec2-shared.md), not the sheet's NTC-derived 0.5."""
    result = punzonamento("centro", 23.25, **_ARGS, legacy_compat=False)
    assert result.v_rd_max_MPa == pytest.approx(0.4 * 0.54 * 14.1667, rel=1e-6)
    assert result.verifica_u0.clause == "EC2 §6.4.5(3)"


@pytest.mark.unit
def test_coeff_vrd_max_can_be_overridden_to_2004_na_it_value() -> None:
    """`coeff_vrd_max` is an explicit, named advanced input (`PavimentoIndustrialeInput`), not a
    silent default: 0.5 (EN 1992-1-1:2004 + Appendice Nazionale italiana 2013) is also selectable."""
    result = punzonamento("centro", 23.25, **_ARGS, legacy_compat=False, coeff_vrd_max=0.5)
    assert result.v_rd_max_MPa == pytest.approx(0.5 * 0.54 * 14.1667, rel=1e-6)
    assert result.verifica_u0.clause == "EC2 §6.4.5(3)"


@pytest.mark.unit
def test_coeff_vrd_max_04_vs_05_give_resistances_in_ratio_08_in_code_standard_mode() -> None:
    a1_2014 = punzonamento("centro", 23.25, **_ARGS, legacy_compat=False, coeff_vrd_max=0.4)
    na_it = punzonamento("centro", 23.25, **_ARGS, legacy_compat=False, coeff_vrd_max=0.5)
    assert a1_2014.v_rd_max_MPa == pytest.approx(na_it.v_rd_max_MPa * 0.8, rel=1e-9)


@pytest.mark.unit
def test_coeff_vrd_max_ignored_in_legacy_mode() -> None:
    """legacy_compat=True must keep reproducing the sheet's own NTC2018 0.5 coefficient regardless of
    `coeff_vrd_max`."""
    legacy_04 = punzonamento("centro", 23.25, **_ARGS, legacy_compat=True, coeff_vrd_max=0.4)
    legacy_05 = punzonamento("centro", 23.25, **_ARGS, legacy_compat=True, coeff_vrd_max=0.5)
    assert legacy_04.v_rd_max_MPa == pytest.approx(legacy_05.v_rd_max_MPa, rel=1e-12)
    assert legacy_04.v_rd_max_MPa == pytest.approx(0.5 * 0.54 * 14.1667, rel=1e-6)


@pytest.mark.unit
def test_centro_u1_is_identical_in_both_legacy_modes() -> None:
    """Only bordo/spigolo carry the h-vs-d bug; centro already uses d in the sheet."""
    legacy = punzonamento("centro", 23.25, **_ARGS, legacy_compat=True)
    fixed = punzonamento("centro", 23.25, **_ARGS, legacy_compat=False)
    assert legacy.u1_mm == pytest.approx(fixed.u1_mm)


@pytest.mark.unit
def test_bordo_legacy_reproduces_h_based_perimeter() -> None:
    result = punzonamento("bordo", 23.25, **_ARGS, legacy_compat=True)
    assert result.u1_mm == pytest.approx(1956.64, rel=1e-5)
    assert result.v_ed1_MPa == pytest.approx(0.097857, rel=1e-5)


@pytest.mark.unit
def test_spigolo_legacy_reproduces_h_based_perimeter() -> None:
    result = punzonamento("spigolo", 23.25, **_ARGS, legacy_compat=True)
    assert result.u1_mm == pytest.approx(1228.32, rel=1e-5)
    assert result.v_ed1_MPa == pytest.approx(0.167015, rel=1e-5)


@pytest.mark.unit
def test_bordo_fixed_uses_d_and_shrinks_u1() -> None:
    """Fix: u1 uses d (170mm) instead of h (200mm) -> smaller u1 -> higher (more conservative) vEd1."""
    legacy = punzonamento("bordo", 23.25, **_ARGS, legacy_compat=True)
    fixed = punzonamento("bordo", 23.25, **_ARGS, legacy_compat=False)
    assert fixed.u1_mm < legacy.u1_mm
    assert fixed.v_ed1_MPa > legacy.v_ed1_MPa


@pytest.mark.unit
def test_spigolo_fixed_uses_d_and_shrinks_u1() -> None:
    legacy = punzonamento("spigolo", 23.25, **_ARGS, legacy_compat=True)
    fixed = punzonamento("spigolo", 23.25, **_ARGS, legacy_compat=False)
    assert fixed.u1_mm < legacy.u1_mm
    assert fixed.v_ed1_MPa > legacy.v_ed1_MPa
