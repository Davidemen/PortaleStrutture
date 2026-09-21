"""Oracle test: `acciaio-proprieta-temperatura` vs LibreOffice recalculation of fuoco-materiali's
four θ sheets (tests/fixtures/gen_acciaio_incendio_proprieta.py). Each sheet's empty override is a
free golden case (docs/BUILD_CONTRACT.md §"Member tools")."""
import json
from pathlib import Path

import pytest

from strutture.members.acciaio_incendio.proprieta_models import ProprietaTemperaturaInput
from strutture.members.acciaio_incendio.proprieta_tool import run

pytestmark = pytest.mark.oracle

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "acciaio_incendio_proprieta_oracle.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", FIXTURE, ids=lambda c: c["sheet"])
def test_matches_libreoffice_recalculation(case):
    outputs = case["outputs"]
    inputs = ProprietaTemperaturaInput(
        fyk_MPa=float(outputs["C20"]),
        ea_20_MPa=float(outputs["C21"]),
        theta_C=float(outputs["C22"]),
        legacy_compat=True,
    )
    report = run(inputs)

    assert report.ok
    assert report.data.fp_theta_MPa == pytest.approx(outputs["C23"])
    assert report.data.fy_theta_MPa == pytest.approx(outputs["C24"])
    assert report.data.ea_theta_MPa == pytest.approx(outputs["C25"])
