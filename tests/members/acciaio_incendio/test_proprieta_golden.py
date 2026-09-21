"""Golden test: spec §"Golden test case" cached values, θ=550°C (interpolated between the
500/600°C Table 3.1 rows)."""
import pytest

from strutture.members.acciaio_incendio.proprieta_models import ProprietaTemperaturaInput
from strutture.members.acciaio_incendio.proprieta_tool import run

pytestmark = pytest.mark.golden


def test_theta_550_matches_cached_sheet_values():
    inputs = ProprietaTemperaturaInput(fyk_MPa=355.0, ea_20_MPa=210000.0, theta_C=550.0)
    report = run(inputs)
    assert report.ok
    data = report.data
    assert data.ky_theta == pytest.approx(0.625, rel=1e-6)
    assert data.kp_theta == pytest.approx(0.27, rel=1e-6)
    assert data.kE_theta == pytest.approx(0.455, rel=1e-6)
    assert data.fy_theta_MPa == pytest.approx(221.875, rel=1e-6)
    assert data.fp_theta_MPa == pytest.approx(95.85, rel=1e-6)
    assert data.ea_theta_MPa == pytest.approx(95550.0, rel=1e-6)


@pytest.mark.parametrize(
    ("theta_C", "ky", "kp", "kE", "fy", "fp", "ea"),
    [
        (600.0, 0.470, 0.18, 0.310, 166.85, 63.9, 65100.0),
        (700.0, 0.230, 0.075, 0.130, 81.65, 26.625, 27300.0),
    ],
)
def test_other_spec_cases(theta_C, ky, kp, kE, fy, fp, ea):
    report = run(ProprietaTemperaturaInput(fyk_MPa=355.0, ea_20_MPa=210000.0, theta_C=theta_C))
    assert report.ok
    data = report.data
    assert data.ky_theta == pytest.approx(ky, rel=1e-6)
    assert data.kp_theta == pytest.approx(kp, rel=1e-6)
    assert data.kE_theta == pytest.approx(kE, rel=1e-6)
    assert data.fy_theta_MPa == pytest.approx(fy, rel=1e-6)
    assert data.fp_theta_MPa == pytest.approx(fp, rel=1e-6)
    assert data.ea_theta_MPa == pytest.approx(ea, rel=1e-6)
