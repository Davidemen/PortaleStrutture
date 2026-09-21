"""Golden tests: rebar_properties vs the union roster cached in ca-travi/ca-mensole/ca-pilastri!
Tabelle (merge C1, docs/architecture.md §3)."""
import json
from pathlib import Path

import pytest

from strutture.shared.materials.rebar import rebar_properties

pytestmark = pytest.mark.golden

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "materials_rebar_oracle.json").read_text())


@pytest.mark.parametrize("row", FIXTURE, ids=lambda r: r["grado"])
def test_rebar_matches_sheet_cache(row):
    result = rebar_properties(row["grado"])
    assert result.fyk_MPa == pytest.approx(row["fyk_MPa"])
    assert result.ftk_MPa == pytest.approx(row["ftk_MPa"])
    if row["sigma_amm_MPa"] is None:
        assert result.sigma_amm_MPa is None
    else:
        assert result.sigma_amm_MPa == pytest.approx(row["sigma_amm_MPa"])
    assert result.legacy_grade is row["legacy_grade"]
