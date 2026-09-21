"""Golden test: spec §3 cached values (resistenza!D4/D5, row t=5min = B9:H9), legacy_compat=True."""
import pytest

from strutture.members.acciaio_incendio.models import ResistenzaIncendioInput
from strutture.members.acciaio_incendio.tool import run

pytestmark = pytest.mark.golden


def test_default_grade_row_t5_matches_cached_sheet_values():
    inputs = ResistenzaIncendioInput(grado="S355", tempi_min=(5.0,), legacy_compat=True)
    report = run(inputs)
    assert report.ok
    assert report.data.materiale.fy_20_MPa == pytest.approx(355.0)
    assert report.data.materiale.fu_20_MPa == pytest.approx(510.0)
    riga = report.data.righe[0]
    assert riga.theta_C == pytest.approx(576.41, rel=1e-5)
    assert riga.ky_theta == pytest.approx(0.543128, rel=1e-5)
    assert riga.kE_theta == pytest.approx(0.378410, rel=1e-5)
    assert riga.fu_theta_MPa == pytest.approx(276.995, rel=1e-5)
    assert riga.fy_theta_MPa == pytest.approx(192.810, rel=1e-5)
    assert riga.e_theta_MPa == pytest.approx(79466.0, rel=1e-4)
