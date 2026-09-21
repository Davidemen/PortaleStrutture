"""Unit tests for `riga_carico` (composes contact + stress + punching + crack + rebar for one
`carichi` row, spec steps 1-13)."""
import pytest

from strutture.foundations.pavimento_industriale.carico_row import CaricoRow
from strutture.foundations.pavimento_industriale.concentrati_riga import riga_carico

_RIGA_CENTRO = CaricoRow(caso="ruota motrice", posizione="centro", p_kN=15.5, impronta_a_mm=500, impronta_b_mm=100, gamma=1.5, psi1=0.9)
_COMMON = {"h_mm": 200.0, "l_mm": 776.901, "fcfd_MPa": 1.45982, "fctm_MPa": 2.60682, "mrd_Nmm_m": 15046.9, "d_mm": 170.0, "v1": 0.54, "fcd_MPa": 14.1667, "v_min_MPa": 0.494975}


@pytest.mark.unit
def test_riga_carico_matches_golden_case_centro() -> None:
    result = riga_carico(_RIGA_CENTRO, **_COMMON, legacy_compat=True)
    assert result.caso == "ruota motrice"
    assert result.posizione == "centro"
    assert result.sigma_c_max_MPa == pytest.approx(0.789861, rel=1e-5)
    assert result.tl_tensionale == pytest.approx(0.541068, rel=1e-4)
    assert result.tl_fessurazione == pytest.approx(0.218158, rel=1e-4)
    assert result.tl_armatura == pytest.approx(0.349956, rel=1e-4)
    assert result.tl_punzonamento_u0 == pytest.approx(0.0342657, rel=1e-4)
    assert result.tl_punzonamento_u1 == pytest.approx(0.0952414, rel=1e-4)


@pytest.mark.unit
def test_riga_carico_matches_golden_case_spigolo() -> None:
    riga = CaricoRow(caso="ruota motrice", posizione="spigolo", p_kN=15.5, impronta_a_mm=500, impronta_b_mm=100, gamma=1.5, psi1=0.9)
    result = riga_carico(riga, **_COMMON, legacy_compat=True)
    assert result.sigma_c_max_MPa == pytest.approx(1.02311, rel=1e-5)
    assert result.tl_tensionale == pytest.approx(0.70085, rel=1e-4)
    assert result.tl_punzonamento_u1 == pytest.approx(0.33742, rel=1e-4)


@pytest.mark.unit
def test_utilizzo_max_is_the_worst_of_all_ratios() -> None:
    result = riga_carico(_RIGA_CENTRO, **_COMMON, legacy_compat=True)
    assert result.utilizzo_max == pytest.approx(max(
        result.tl_tensionale, result.tl_fessurazione, result.tl_armatura,
        result.tl_punzonamento_u0, result.tl_punzonamento_u1,
    ))
