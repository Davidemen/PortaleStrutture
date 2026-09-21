import pytest

from strutture.geotechnics.cedimenti_elastico.integrate import total_settlement_m
from strutture.geotechnics.cedimenti_elastico.punto import punto_settlement
from strutture.shared.report import CalcError
from strutture.shared.soil_layers import SoilLayer

PUNTO_LAYERS = (
    SoilLayer(z_top_m=0.0, z_bot_m=15.0, modulo_MPa=9.80665),
    SoilLayer(z_top_m=15.0, z_bot_m=120.0, modulo_MPa=17.65197),
)
Q_KPA = 0.8 * 98.0665


@pytest.mark.golden
def test_legacy_symmetric_point_matches_the_500_golden_case():
    o_slices, o_prime_slices = punto_settlement(Q_KPA, 40.0, 40.0, 20.0, 20.0, PUNTO_LAYERS, z_max_m=1.0, dz_m=0.1, legacy_compat=True)
    assert len(o_slices) == 80  # z=0.1..8.0m -- see punto.py's LEGACY_Z_MAX_M note
    assert total_settlement_m(o_slices) * 100 == pytest.approx(6.33092, rel=1e-6)
    assert total_settlement_m(o_prime_slices) * 100 == pytest.approx(1.59762, abs=1e-5)


@pytest.mark.unit
def test_legacy_and_fixed_stress_formulas_agree_for_a_symmetric_point():
    # Same assertion as before the mid-depth-quadrature fix (docs/architecture-batch2.md §7
    # integrate.py), but now compared point-wise (not through total_settlement_m): legacy_compat
    # evaluates sigma at the slice bottom while code-standard evaluates it at the slice mid-depth,
    # so the two quadratures no longer agree bit-for-bit even when the underlying stress formulas
    # do (the "same-side pairing" bug is only invisible at a symmetric point).
    from strutture.geotechnics.cedimenti_elastico.punto import _legacy_point_sigma
    from strutture.shared.soil_stress import under_point

    z_m = 3.0
    legacy_sigma = _legacy_point_sigma(Q_KPA, 20.0, 20.0, 40.0, 40.0, z_m)
    fixed_sigma = under_point(Q_KPA, 40.0, 40.0, 20.0, 20.0, z_m).total
    assert legacy_sigma == pytest.approx(fixed_sigma, rel=1e-9)


@pytest.mark.unit
def test_legacy_and_fixed_disagree_for_an_asymmetric_point():
    """spec: 'Re-derive/test this pairing against an asymmetric point before trusting it' -- the
    sheet's same-side pairing ("Ofga"=(e1,e1'), "Ocde"=(e2',e2)) is only numerically invisible at
    the symmetric point of both golden cases."""
    legacy_o, _ = punto_settlement(Q_KPA, 40.0, 40.0, 10.0, 30.0, PUNTO_LAYERS, z_max_m=8.0, dz_m=0.1, legacy_compat=True)
    fixed_o, _ = punto_settlement(Q_KPA, 40.0, 40.0, 10.0, 30.0, PUNTO_LAYERS, z_max_m=8.0, dz_m=0.1, legacy_compat=False)
    legacy_total, fixed_total = total_settlement_m(legacy_o), total_settlement_m(fixed_o)
    assert legacy_total != pytest.approx(fixed_total, rel=1e-4)


@pytest.mark.unit
def test_legacy_rejects_a_point_outside_the_comparison_rectangle():
    with pytest.raises(CalcError):
        punto_settlement(Q_KPA, 40.0, 40.0, 50.0, 20.0, PUNTO_LAYERS, z_max_m=1.0, dz_m=0.1, legacy_compat=True)


@pytest.mark.unit
def test_fixed_supports_a_point_outside_the_footing():
    o_slices, _ = punto_settlement(Q_KPA, 40.0, 40.0, 50.0, 20.0, PUNTO_LAYERS, z_max_m=8.0, dz_m=0.1, legacy_compat=False)
    assert total_settlement_m(o_slices) > 0
