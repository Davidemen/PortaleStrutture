import pytest
from pydantic import ValidationError

from strutture.geotechnics.cedimenti_elastico.models_tg import TimoshenkoGoodierInput
from strutture.geotechnics.cedimenti_elastico.tool_timoshenko_goodier import run_timoshenko_goodier
from strutture.shared.report import CalcError

STRATI_6_LAYERS = [{"z_top_m": float(i), "z_bot_m": float(i + 1), "modulo_MPa": 10.0 + i} for i in range(6)]


@pytest.mark.unit
def test_overlapping_strati_are_rejected():
    # rows overlap on [1,2]: shared.soil_layers.weighted_modulus would otherwise silently double
    # count that band (the bug this validator closes).
    strati = [{"z_top_m": 0.0, "z_bot_m": 2.0, "modulo_MPa": 10.0}, {"z_top_m": 1.0, "z_bot_m": 5.0, "modulo_MPa": 100.0}]
    with pytest.raises(ValidationError, match="non è contigua"):
        TimoshenkoGoodierInput(b=1.0, l=1.0, d=0.0, mu=0.3, q=100.0, strati=strati, h_significativo=5.0, if_centro=1.0, if_bordo=1.0)


@pytest.mark.unit
def test_gapped_strati_are_rejected():
    strati = [{"z_top_m": 0.0, "z_bot_m": 1.0, "modulo_MPa": 10.0}, {"z_top_m": 2.0, "z_bot_m": 5.0, "modulo_MPa": 100.0}]
    with pytest.raises(ValidationError, match="non è contigua"):
        TimoshenkoGoodierInput(b=1.0, l=1.0, d=0.0, mu=0.3, q=100.0, strati=strati, h_significativo=5.0, if_centro=1.0, if_bordo=1.0)


@pytest.mark.unit
def test_ground_surface_strati_may_start_above_zero():
    # legitimate: the leading gap is swallowed by the foundation embedment D once shift_to_base
    # runs (docs/architecture-batch2.md / ground_to_base.py), so this must NOT be rejected.
    strati = [{"z_top_m": 0.80, "z_bot_m": 4.80, "modulo_MPa": 5.5}, {"z_top_m": 4.80, "z_bot_m": 120.0, "modulo_MPa": 7.0}]
    inputs = TimoshenkoGoodierInput(b=1.0, l=1.0, d=1.10, mu=0.3, q=100.0, strati=strati, h_significativo=5.0, if_centro=1.0, if_bordo=1.0)
    assert run_timoshenko_goodier(inputs).ok


@pytest.mark.unit
def test_h_significativo_defaults_to_five_times_b():
    inputs = TimoshenkoGoodierInput(b=1.0, l=1.0, d=0.0, mu=0.3, q=100.0, strati=STRATI_6_LAYERS, if_centro=1.0, if_bordo=1.0)
    report = run_timoshenko_goodier(inputs)
    assert report.ok, report.errors
    assert report.data.geometria.b_centro == pytest.approx(2 * 5.0 / 1.0)


@pytest.mark.unit
def test_code_standard_uses_any_number_of_layers_legacy_hardwires_to_four():
    inputs = TimoshenkoGoodierInput(b=1.0, l=1.0, d=0.0, mu=0.3, q=100.0, strati=STRATI_6_LAYERS, h_significativo=6.0, if_centro=1.0, if_bordo=1.0, legacy_compat=False)
    fixed = run_timoshenko_goodier(inputs)
    legacy = run_timoshenko_goodier(inputs.model_copy(update={"legacy_compat": True}))
    assert fixed.ok and legacy.ok
    assert fixed.data.modulo.es_MPa == pytest.approx((10 + 11 + 12 + 13 + 14 + 15) / 6)
    assert legacy.data.modulo.es_MPa == pytest.approx((10 + 11 + 12 + 13) / 6)
    assert fixed.data.cedimento.delta_h_centro_mm < legacy.data.cedimento.delta_h_centro_mm  # bigger Es -> smaller settlement


@pytest.mark.unit
def test_code_standard_raises_when_stratigraphy_stops_short_of_h():
    inputs = TimoshenkoGoodierInput(
        b=1.0, l=1.0, d=0.0, mu=0.3, q=100.0, strati=[{"z_top_m": 0.0, "z_bot_m": 2.0, "modulo_MPa": 10.0}],
        h_significativo=6.0, if_centro=1.0, if_bordo=1.0, legacy_compat=False,
    )
    with pytest.raises(CalcError, match="stratigrafia"):
        run_timoshenko_goodier(inputs)


@pytest.mark.unit
def test_legacy_uses_1_minus_mu_code_standard_uses_1_minus_mu_squared():
    # h_significativo=4.0 -> both modes weight exactly the first 4 layers, so Es is identical and
    # the only difference between the two reports is the (1-mu) vs (1-mu^2) term.
    inputs = TimoshenkoGoodierInput(b=1.0, l=1.0, d=0.0, mu=0.35, q=100.0, strati=STRATI_6_LAYERS, h_significativo=4.0, if_centro=1.0, if_bordo=1.0, legacy_compat=True)
    legacy = run_timoshenko_goodier(inputs)
    fixed = run_timoshenko_goodier(inputs.model_copy(update={"legacy_compat": False}))
    ratio = fixed.data.cedimento.delta_h_centro_mm / legacy.data.cedimento.delta_h_centro_mm
    assert ratio == pytest.approx((1 - 0.35**2) / (1 - 0.35), rel=1e-9)


@pytest.mark.unit
def test_code_standard_bordo_settlement_uses_edge_midpoint_superposition():
    # Square footing, H=4B, mu=0.35: h_significativo=4.0 keeps Es identical between the two modes
    # (both weight exactly the first 4 layers), isolating the (1-mu) vs (1-mu^2) term and the
    # IS_bordo fix. Legacy reuses the sheet's single-rectangle corner IS_bordo; code-standard uses
    # the true edge-midpoint IS_bordo (2 sub-rectangles), which is larger.
    inputs = TimoshenkoGoodierInput(b=1.0, l=1.0, d=0.0, mu=0.35, q=100.0, strati=STRATI_6_LAYERS, h_significativo=4.0, if_centro=1.0, if_bordo=1.0, legacy_compat=True)
    legacy = run_timoshenko_goodier(inputs)
    fixed = run_timoshenko_goodier(inputs.model_copy(update={"legacy_compat": False}))
    assert legacy.ok and fixed.ok
    assert legacy.data.modulo.es_MPa == fixed.data.modulo.es_MPa
    assert fixed.data.fattori.is_bordo > legacy.data.fattori.is_bordo
    mu_term_ratio = (1 - 0.35**2) / (1 - 0.35)
    is_bordo_ratio = fixed.data.fattori.is_bordo / legacy.data.fattori.is_bordo
    assert fixed.data.cedimento.delta_h_bordo_mm == pytest.approx(legacy.data.cedimento.delta_h_bordo_mm * mu_term_ratio * is_bordo_ratio, rel=1e-9)


@pytest.mark.unit
def test_h_override_is_unit_converted():
    si = TimoshenkoGoodierInput(sistema_unita="SI", b=1.0, l=1.0, d=0.0, mu=0.3, q=100.0, strati=STRATI_6_LAYERS, h_significativo=3.0, if_centro=1.0, if_bordo=1.0)
    tecnico = TimoshenkoGoodierInput(sistema_unita="tecnico", b=100.0, l=100.0, d=0.0, mu=0.3, q=100.0 / 98.0665, strati=STRATI_6_LAYERS, h_significativo=300.0, if_centro=1.0, if_bordo=1.0)
    r_si, r_tecnico = run_timoshenko_goodier(si), run_timoshenko_goodier(tecnico)
    assert r_si.data.modulo.es_MPa == pytest.approx(r_tecnico.data.modulo.es_MPa, rel=1e-9)
