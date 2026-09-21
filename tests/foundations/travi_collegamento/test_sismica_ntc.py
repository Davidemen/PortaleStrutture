"""Unit tests for `sismica_ntc` (SS/ST/S/α/amax)."""
import pytest

from strutture.foundations.travi_collegamento.sismica_ntc import sismica_ntc


@pytest.mark.unit
def test_sismica_ntc_golden_soil_b() -> None:
    result = sismica_ntc("B", "T1", 2.43, 0.151)
    assert result.ss == pytest.approx(1.2, rel=1e-4)
    assert result.st == pytest.approx(1.0)
    assert result.s == pytest.approx(1.2, rel=1e-4)
    assert result.alpha == pytest.approx(0.3)
    assert result.amax_g == pytest.approx(0.1812, rel=1e-4)


@pytest.mark.unit
def test_sismica_ntc_soil_a_alpha_nonzero() -> None:
    """NTC's α_A=0.2 (unlike EN1998's α_A=0) — Da verificare, spec bug note #2."""
    result = sismica_ntc("A", "T1", 2.43, 0.151)
    assert result.ss == pytest.approx(1.0)
    assert result.alpha == pytest.approx(0.2)


@pytest.mark.unit
@pytest.mark.parametrize("categoria,alpha_atteso", [("A", 0.2), ("B", 0.3), ("C", 0.4), ("D", 0.6)])
def test_sismica_ntc_alpha_table(categoria: str, alpha_atteso: float) -> None:
    result = sismica_ntc(categoria, "T1", 2.43, 0.151)
    assert result.alpha == pytest.approx(alpha_atteso)
