"""Golden tests: legacy_compat=True concrete_properties vs the sheets' cached values.

Fixture source: build/data/ca-fessurazione/materiale-cls.csv (ca-fessurazione!MATERIALE CLS),
except C35/45 which is overridden with the fill-down bug cached in
build/cellmaps/ca-travi/tabelle.txt row 38 (ca-travi/ca-mensole/ca-pilastri!Tabelle) — see
docs/divergences/materials.md."""
import json
from pathlib import Path

import pytest

from strutture.shared.materials.concrete import concrete_properties

pytestmark = pytest.mark.golden

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "materials_concrete_legacy_oracle.json").read_text())


@pytest.mark.parametrize("row", FIXTURE, ids=lambda r: r["classe"])
def test_concrete_legacy_matches_sheet_cache(row):
    result = concrete_properties(row["classe"], legacy_compat=True)
    assert result.rck_MPa == pytest.approx(row["rck_MPa"], rel=1e-6)
    assert result.fck_MPa == pytest.approx(row["fck_MPa"], rel=1e-6)
    assert result.fcm_MPa == pytest.approx(row["fcm_MPa"], rel=1e-6)
    assert result.ecm_MPa == pytest.approx(row["ecm_MPa"], rel=1e-4)
    assert result.fctm_MPa == pytest.approx(row["fctm_MPa"], rel=1e-4)
    if row["fctk_MPa"] is not None:
        assert result.fctk_MPa == pytest.approx(row["fctk_MPa"], rel=1e-6)
    if row["fcd_MPa"] is not None:
        assert result.fcd_MPa == pytest.approx(row["fcd_MPa"], rel=1e-6)
    if row["fctd_MPa"] is not None:
        assert result.fctd_MPa == pytest.approx(row["fctd_MPa"], rel=1e-6)
