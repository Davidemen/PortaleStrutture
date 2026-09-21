import math

import pytest

from strutture.foundations.plinti_isolati.scorrimento import (
    GAMMA_R_SCORRIMENTO,
    LEGACY_NO_DEMAND_RATIO,
    mu_scorrimento,
)


@pytest.mark.golden
def test_mu_scorrimento_golden() -> None:
    """docs/specs/fond-plinti-isolati.md golden case: mu_sl = ">100" (S=5.37366, N=2596.93, phi=30deg)."""
    mu = mu_scorrimento(2596.93, 0.131665, 5.37205, 30.0, legacy_compat=True)
    assert mu == LEGACY_NO_DEMAND_RATIO


@pytest.mark.unit
def test_mu_scorrimento_valore_reale_senza_legacy() -> None:
    """Fix (AM): non-legacy mode never caps the ratio, even when it exceeds 100."""
    mu = mu_scorrimento(2596.93, 0.131665, 5.37205, 30.0, legacy_compat=False)
    assert mu is not None
    assert mu > LEGACY_NO_DEMAND_RATIO


@pytest.mark.unit
def test_mu_scorrimento_senza_domanda() -> None:
    """Fix (AM): S=0 (no shear demand) is `None`, not the misleading ">100" text."""
    assert mu_scorrimento(2596.93, 0.0, 0.0, 30.0, legacy_compat=False) is None
    assert mu_scorrimento(2596.93, 0.0, 0.0, 30.0, legacy_compat=True) == LEGACY_NO_DEMAND_RATIO


@pytest.mark.unit
def test_mu_scorrimento_sotto_soglia() -> None:
    mu = mu_scorrimento(10.0, 0.0, 50.0, 30.0, legacy_compat=False)
    assert mu is not None
    assert mu < 1.0


@pytest.mark.unit
def test_mu_scorrimento_gamma_r_non_legacy() -> None:
    """Fix (CRITICAL): non-legacy mode divides the resistance by gammaR=1.1 (NTC2018 Tab. 6.4.I,
    Approccio 2, R3), so a raw ratio of exactly 1.0 must FAIL, not PASS."""
    n_kN, phi_deg, s_kN = 100.0, 45.0, 100.0 * math.tan(math.radians(45.0))  # raw ratio = 1.0
    mu_legacy = mu_scorrimento(n_kN, s_kN, 0.0, phi_deg, legacy_compat=True)
    mu_fisso = mu_scorrimento(n_kN, s_kN, 0.0, phi_deg, legacy_compat=False)
    assert mu_legacy == pytest.approx(1.0)
    assert mu_fisso == pytest.approx(1.0 / GAMMA_R_SCORRIMENTO)
    assert mu_fisso < 1.0
