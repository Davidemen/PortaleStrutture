import pytest

from strutture.geotechnics.cedimenti_elastico.models_tg import TimoshenkoGoodierInput
from strutture.geotechnics.cedimenti_elastico.tool_timoshenko_goodier import run_timoshenko_goodier

# Elastico_Timoshenko_Goodier_3: rows 3-4 are dead zero-thickness placeholder rows in the sheet's
# fixed 5-row table; SoilLayer forbids zero-thickness rows (its own per-row validator), so two
# 1-nanometre padding rows stand in for them -- negligible (~1e-9 relative) numerically, but they
# occupy row-position 3 and 4 so the legacy "first 4 rows" bug still excludes the real deep layer,
# exactly like the sheet's own dead rows do (see `weighted_es.py` and
# `docs/divergences/geo-cedimenti-elastico.md`).
STRATI = [
    {"z_top_m": 0.0, "z_bot_m": 2.10, "modulo_MPa": 180 * 0.0980665},
    {"z_top_m": 2.10, "z_bot_m": 5.00, "modulo_MPa": 140 * 0.0980665},
    {"z_top_m": 5.00, "z_bot_m": 5.00 + 1e-9, "modulo_MPa": 140 * 0.0980665},
    {"z_top_m": 5.00 + 1e-9, "z_bot_m": 5.00 + 2e-9, "modulo_MPa": 280 * 0.0980665},
    {"z_top_m": 5.00 + 2e-9, "z_bot_m": 120.0, "modulo_MPa": 280 * 0.0980665},
]


@pytest.mark.golden
def test_golden_case():
    inputs = TimoshenkoGoodierInput(b=1.0, l=1.0, d=0.5, mu=0.35, q=0.92 * 98.0665, strati=STRATI, if_centro=0.65, if_bordo=0.78, legacy_compat=True)
    report = run_timoshenko_goodier(inputs)
    assert report.ok, report.errors
    data = report.data
    assert data.modulo.es_MPa == pytest.approx(138.8 * 0.0980665, rel=1e-6)
    assert data.fattori.is_centro == pytest.approx(0.505131, rel=1e-6)
    assert data.fattori.is_bordo == pytest.approx(0.451165, rel=1e-6)
    assert data.cedimento.delta_h_centro_mm == pytest.approx(2.82917, rel=1e-4)
    assert data.cedimento.delta_h_bordo_mm == pytest.approx(1.51615, rel=1e-4)


@pytest.mark.unit
def test_sistema_tecnico_matches_si():
    si = TimoshenkoGoodierInput(sistema_unita="SI", b=1.0, l=1.0, d=0.5, mu=0.35, q=0.92 * 98.0665, strati=STRATI, if_centro=0.65, if_bordo=0.78, legacy_compat=True)
    tecnico = TimoshenkoGoodierInput(sistema_unita="tecnico", b=100.0, l=100.0, d=50.0, mu=0.35, q=0.92, strati=STRATI, if_centro=0.65, if_bordo=0.78, legacy_compat=True)
    r_si, r_tecnico = run_timoshenko_goodier(si), run_timoshenko_goodier(tecnico)
    assert r_si.data.cedimento.delta_h_centro_mm == pytest.approx(r_tecnico.data.cedimento.delta_h_centro_mm, rel=1e-9)
