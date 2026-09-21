import pytest

from strutture.loads.sisma.eta_verticale import eta_verticale


@pytest.mark.unit
def test_legacy_reproduces_sheet_reciprocal_bug():
    """Sisma!I45 = 1/I44 (mislabeled 'coefficiente dissipativo'), independent of ξ."""
    assert eta_verticale(5, 1.5, legacy_compat=True) == pytest.approx(1 / 1.5, rel=1e-9)
    assert eta_verticale(20, 1.5, legacy_compat=True) == pytest.approx(1 / 1.5, rel=1e-9)


@pytest.mark.unit
def test_fixed_uses_the_same_damping_formula_as_horizontal():
    from strutture.loads.sisma.smorzamento import smorzamento_eta

    assert eta_verticale(5, 1.5, legacy_compat=False) == pytest.approx(smorzamento_eta(5), rel=1e-9)
    assert eta_verticale(5, 1.5, legacy_compat=False) != pytest.approx(1 / 1.5, rel=1e-3)
