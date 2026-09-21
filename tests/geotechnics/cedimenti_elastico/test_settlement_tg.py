import pytest

from strutture.geotechnics.cedimenti_elastico.settlement_tg import deltah_bordo_mm, deltah_centro_mm

Q_KPA = 0.92 * 98.0665
B_M = 1.0
ES_MPA = 138.8 * 0.0980665
IS_CENTRO, IS_BORDO = 0.505131, 0.451165
IF_CENTRO, IF_BORDO = 0.65, 0.78


@pytest.mark.golden
def test_legacy_matches_the_timoshenko_goodier_3_golden_case():
    assert deltah_centro_mm(Q_KPA, B_M, 0.35, ES_MPA, IS_CENTRO, IF_CENTRO, legacy_compat=True) == pytest.approx(2.82917, rel=1e-4)
    assert deltah_bordo_mm(Q_KPA, B_M, 0.35, ES_MPA, IS_BORDO, IF_BORDO, legacy_compat=True) == pytest.approx(1.51615, rel=1e-4)


@pytest.mark.unit
def test_code_standard_uses_1_minus_mu_squared():
    legacy = deltah_centro_mm(Q_KPA, B_M, 0.35, ES_MPA, IS_CENTRO, IF_CENTRO, legacy_compat=True)
    fixed = deltah_centro_mm(Q_KPA, B_M, 0.35, ES_MPA, IS_CENTRO, IF_CENTRO, legacy_compat=False)
    # (1-mu)=0.65 vs (1-mu^2)=0.8775 -> the fixed settlement is larger by that exact ratio.
    assert fixed == pytest.approx(legacy * (1 - 0.35**2) / (1 - 0.35), rel=1e-9)
    assert fixed > legacy
