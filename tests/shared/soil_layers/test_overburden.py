"""`effective_overburden`: buoyant σ'v0 increase, matching the oedometric sheet's column I
(`build/data/geo-cedimenti/edometrico.csv`, γ=1800 kg/mc, water table at the reference level)."""
import csv
from pathlib import Path

import pytest

from strutture.shared.soil_layers import effective_overburden
from strutture.shared.units import cm_to_m, kgcm2_to_kpa

FIXTURE = Path(__file__).parent.parent.parent / "fixtures" / "soil_stress_spread_overburden_edometrico.csv"
GAMMA_KGM3_TO_KNM3 = 9.80665 / 1000  # kg/m3 * g[m/s2] / 1000 = kN/m3, mirrors units.KPA_PER_KGCM2's g


def _rows() -> list[dict[str, str]]:
    with FIXTURE.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.golden
@pytest.mark.parametrize("row", _rows(), ids=lambda row: f"z={row['z_cm']}cm")
def test_matches_edometrico_column_i(row: dict[str, str]) -> None:
    gamma_kn_m3 = float(row["gamma_kgm3"]) * GAMMA_KGM3_TO_KNM3
    z_m = cm_to_m(float(row["z_cm"]))
    expected_kpa = kgcm2_to_kpa(float(row["dsigma_v_eff_kgcm2"]))
    assert effective_overburden(gamma_kn_m3, z_m, water_table_m=0.0) == pytest.approx(expected_kpa, rel=1e-6, abs=1e-6)


@pytest.mark.unit
def test_above_water_table_uses_total_unit_weight() -> None:
    assert effective_overburden(18.0, 2.0, water_table_m=5.0) == pytest.approx(36.0)


@pytest.mark.unit
def test_below_water_table_uses_buoyant_unit_weight() -> None:
    gamma, gamma_w, wt = 18.0, 9.80665, 3.0
    expected = gamma * wt + (gamma - gamma_w) * (5.0 - wt)
    assert effective_overburden(gamma, 5.0, water_table_m=wt) == pytest.approx(expected)


@pytest.mark.unit
def test_continuous_at_the_water_table() -> None:
    gamma, wt = 18.0, 3.0
    just_above = effective_overburden(gamma, wt - 1e-9, water_table_m=wt)
    at_wt = effective_overburden(gamma, wt, water_table_m=wt)
    assert just_above == pytest.approx(at_wt, rel=1e-6)


@pytest.mark.unit
def test_rejects_negative_depth() -> None:
    with pytest.raises(ValueError, match="z_m"):
        effective_overburden(18.0, -1.0)


@pytest.mark.unit
def test_rejects_negative_water_table() -> None:
    with pytest.raises(ValueError, match="water_table_m"):
        effective_overburden(18.0, 1.0, water_table_m=-0.5)
