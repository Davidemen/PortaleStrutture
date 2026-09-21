"""Golden tests: legacy_compat=True steel_properties vs acciaio-colonne-ec3!Materiali!H19:J23
(single value per grade, thickness never read — see docs/divergences/materials.md)."""
import json
from pathlib import Path

import pytest

from strutture.shared.materials.structural_steel import steel_properties

pytestmark = pytest.mark.golden

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "materials_structural_steel_oracle.json").read_text())


@pytest.mark.parametrize("row", FIXTURE, ids=lambda r: r["grado"])
@pytest.mark.parametrize("t_mm", [10.0, 79.0])
def test_legacy_ignores_thickness(row, t_mm):
    result = steel_properties(row["grado"], t_mm, legacy_compat=True)
    assert result.fyk_MPa == pytest.approx(row["fyk_MPa"])
    assert result.fuk_MPa == pytest.approx(row["fuk_MPa"])
