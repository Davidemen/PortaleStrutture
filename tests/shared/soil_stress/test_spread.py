"""`spread_2to1` against the oedometric sheet's own computed column H
(`build/data/geo-cedimenti/edometrico.csv`)."""
import csv
from pathlib import Path

import pytest

from strutture.shared.soil_stress import spread_2to1
from strutture.shared.units import cm_to_m, kgcm2_to_kpa

FIXTURE = Path(__file__).parent.parent.parent / "fixtures" / "soil_stress_spread_overburden_edometrico.csv"


def _rows() -> list[dict[str, str]]:
    with FIXTURE.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.golden
@pytest.mark.parametrize("row", _rows(), ids=lambda row: f"z={row['z_cm']}cm")
def test_matches_edometrico_column_h(row: dict[str, str]) -> None:
    q_kpa = kgcm2_to_kpa(float(row["q_kgcm2"]))
    b_m, l_m, z_m = cm_to_m(float(row["b_cm"])), cm_to_m(float(row["l_cm"])), cm_to_m(float(row["z_cm"]))
    expected = kgcm2_to_kpa(float(row["dsigma_v_q_kgcm2"]))
    assert spread_2to1(q_kpa, b_m, l_m, z_m) == pytest.approx(expected, rel=1e-6)


@pytest.mark.unit
def test_at_surface_equals_applied_pressure() -> None:
    assert spread_2to1(150.0, 3.0, 4.0, 0.0) == pytest.approx(150.0)


@pytest.mark.unit
def test_rejects_negative_depth() -> None:
    with pytest.raises(ValueError, match="z_m"):
        spread_2to1(100.0, 1.0, 1.0, -0.1)
