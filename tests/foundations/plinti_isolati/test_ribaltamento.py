import pytest

from strutture.foundations.plinti_isolati.ribaltamento import LEGACY_NO_DEMAND_RATIO, mu_ribaltamento


@pytest.mark.golden
def test_mu_ribaltamento_golden() -> None:
    """docs/specs/fond-plinti-isolati.md golden case: mu_X = mu_Y = ">100"."""
    ribaltamento = mu_ribaltamento(2596.93, 4.0, 4.0, 1.42918, 40.9685, legacy_compat=True)
    assert ribaltamento.mu_x == LEGACY_NO_DEMAND_RATIO
    assert ribaltamento.mu_y == LEGACY_NO_DEMAND_RATIO


@pytest.mark.unit
def test_mu_ribaltamento_valore_reale_senza_legacy() -> None:
    ribaltamento = mu_ribaltamento(2596.93, 4.0, 4.0, 1.42918, 40.9685, legacy_compat=False)
    assert ribaltamento.mu_x is not None and ribaltamento.mu_x > LEGACY_NO_DEMAND_RATIO
    assert ribaltamento.mu_y is not None and ribaltamento.mu_y > LEGACY_NO_DEMAND_RATIO


@pytest.mark.unit
def test_mu_ribaltamento_senza_domanda() -> None:
    """Fix (AE/AH): Mrib=0 (no overturning demand) is `None`, not ">100"."""
    ribaltamento = mu_ribaltamento(2596.93, 4.0, 4.0, 0.0, 0.0, legacy_compat=False)
    assert ribaltamento.mu_x is None
    assert ribaltamento.mu_y is None
    ribaltamento_legacy = mu_ribaltamento(2596.93, 4.0, 4.0, 0.0, 0.0, legacy_compat=True)
    assert ribaltamento_legacy.mu_x == LEGACY_NO_DEMAND_RATIO


@pytest.mark.unit
def test_mu_ribaltamento_sotto_soglia() -> None:
    ribaltamento = mu_ribaltamento(10.0, 1.0, 1.0, 100.0, 100.0, legacy_compat=False)
    assert ribaltamento.mu_x < 1.0
    assert ribaltamento.mu_y < 1.0
