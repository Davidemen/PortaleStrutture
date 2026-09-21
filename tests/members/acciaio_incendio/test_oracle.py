"""Oracle test: legacy_compat=True vs LibreOffice recalculation of resistenza!D4/D5/B9:H9/B32:H32
(tests/fixtures/gen_acciaio_incendio.py), across every grade / case (incl. the D5 fu bug on S275)."""
import json
from pathlib import Path

import pytest

from strutture.members.acciaio_incendio.models import ResistenzaIncendioInput
from strutture.members.acciaio_incendio.tool import run

pytestmark = pytest.mark.oracle

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "acciaio_incendio_resistenza_oracle.json").read_text())


@pytest.mark.parametrize("case", FIXTURE, ids=lambda c: f"{c['inputs']['D2']}_{c['inputs']['D3']}")
def test_matches_libreoffice_recalculation(case):
    grado = case["inputs"]["D2"].upper()
    e_20_MPa = float(case["inputs"]["D3"])
    outputs = case["outputs"]

    inputs = ResistenzaIncendioInput(grado=grado, e_20_MPa=e_20_MPa, tempi_min=(5.0, 120.0), legacy_compat=True)
    report = run(inputs)

    assert report.ok
    assert report.data.materiale.fy_20_MPa == pytest.approx(outputs["D4"])
    assert report.data.materiale.fu_20_MPa == pytest.approx(outputs["D5"])

    row_t5, row_t120 = report.data.righe
    assert row_t5.theta_C == pytest.approx(outputs["C9"])
    assert row_t5.ky_theta == pytest.approx(outputs["D9"])
    assert row_t5.kE_theta == pytest.approx(outputs["E9"])
    assert row_t5.fu_theta_MPa == pytest.approx(outputs["F9"])
    assert row_t5.fy_theta_MPa == pytest.approx(outputs["G9"])
    assert row_t5.e_theta_MPa == pytest.approx(outputs["H9"])

    assert row_t120.theta_C == pytest.approx(outputs["C32"])
    assert row_t120.ky_theta == pytest.approx(outputs["D32"])
    assert row_t120.kE_theta == pytest.approx(outputs["E32"])
    assert row_t120.fu_theta_MPa == pytest.approx(outputs["F32"])
    assert row_t120.fy_theta_MPa == pytest.approx(outputs["G32"])
    assert row_t120.e_theta_MPa == pytest.approx(outputs["H32"])
