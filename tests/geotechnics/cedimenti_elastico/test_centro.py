import pytest

from strutture.geotechnics.cedimenti_elastico.centro import centro_settlement
from strutture.geotechnics.cedimenti_elastico.integrate import total_settlement_m
from strutture.shared.soil_layers import SoilLayer

CENTRO_LAYERS = (
    SoilLayer(z_top_m=0.0, z_bot_m=3.70, modulo_MPa=5.5),
    SoilLayer(z_top_m=3.70, z_bot_m=4.70, modulo_MPa=7.0),
    SoilLayer(z_top_m=4.70, z_bot_m=5.50, modulo_MPa=9.0),
    SoilLayer(z_top_m=5.50, z_bot_m=31.50, modulo_MPa=7.0),
    SoilLayer(z_top_m=31.50, z_bot_m=118.90, modulo_MPa=7.0),
)
Q_KPA = 0.5 * 98.0665


@pytest.mark.golden
def test_legacy_reproduces_the_two_hardcoded_depths():
    main, qa = centro_settlement(Q_KPA, 3.5, 5.0, CENTRO_LAYERS, z_max_m=1.0, dz_m=0.1, legacy_compat=True)
    assert len(main) == 90  # z=0.1..9.0m, ignores z_max_m/dz_m
    assert len(qa) == 81  # z=0.1..8.1m... rows 7..87 minus the missing last row -> 81? see centro.py
    assert total_settlement_m(main) * 100 == pytest.approx(3.0768, abs=2e-4)
    assert total_settlement_m(qa) * 100 == pytest.approx(3.0122, abs=2e-4)


@pytest.mark.unit
def test_code_standard_uses_one_common_grid_for_both_paths():
    main, qa = centro_settlement(Q_KPA, 3.5, 5.0, CENTRO_LAYERS, z_max_m=5.0, dz_m=0.5, legacy_compat=False)
    assert [s.z_m for s in main] == [s.z_m for s in qa]
    assert len(main) == 10
