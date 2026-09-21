"""Fixed-behaviour tests for `acciaio-proprieta-temperatura`: legacy_compat has no numeric effect
(docs/divergences/acciaio_incendio_proprieta.md), boundary/validation cases, and monotonic
sanity checks."""
import pytest
from pydantic import ValidationError

from strutture.members.acciaio_incendio.proprieta_models import ProprietaTemperaturaInput
from strutture.members.acciaio_incendio.proprieta_tool import run
from strutture.shared.tables import KeyNotFound


def test_legacy_compat_has_no_effect_on_the_result():
    legacy = run(ProprietaTemperaturaInput(fyk_MPa=355.0, ea_20_MPa=210000.0, theta_C=550.0, legacy_compat=True))
    fixed = run(ProprietaTemperaturaInput(fyk_MPa=355.0, ea_20_MPa=210000.0, theta_C=550.0, legacy_compat=False))
    assert legacy.data == fixed.data


def test_theta_at_table_boundaries_is_accepted():
    lower = run(ProprietaTemperaturaInput(fyk_MPa=355.0, ea_20_MPa=210000.0, theta_C=20.0))
    upper = run(ProprietaTemperaturaInput(fyk_MPa=355.0, ea_20_MPa=210000.0, theta_C=1200.0))
    assert lower.ok and upper.ok
    assert lower.data.ky_theta == pytest.approx(1.0)
    assert upper.data.ky_theta == pytest.approx(0.0)


def test_theta_outside_20_1200_rejected_by_validation():
    with pytest.raises(ValidationError):
        ProprietaTemperaturaInput(fyk_MPa=355.0, ea_20_MPa=210000.0, theta_C=10.0)
    with pytest.raises(ValidationError):
        ProprietaTemperaturaInput(fyk_MPa=355.0, ea_20_MPa=210000.0, theta_C=1300.0)


def test_non_positive_fyk_or_ea_rejected_by_validation():
    with pytest.raises(ValidationError):
        ProprietaTemperaturaInput(fyk_MPa=0.0, ea_20_MPa=210000.0, theta_C=550.0)
    with pytest.raises(ValidationError):
        ProprietaTemperaturaInput(fyk_MPa=355.0, ea_20_MPa=-1.0, theta_C=550.0)


def test_reduced_values_never_exceed_the_20c_reference():
    report = run(ProprietaTemperaturaInput(fyk_MPa=355.0, ea_20_MPa=210000.0, theta_C=600.0))
    data = report.data
    assert data.fy_theta_MPa < 355.0
    assert data.fp_theta_MPa < 355.0
    assert data.ea_theta_MPa < 210000.0


def test_fp_theta_never_exceeds_fy_theta():
    """kp,θ <= ky,θ for every node of Table 3.1, so fp,θ = fyk*kp,θ <= fy,θ = fyk*ky,θ."""
    for theta_C in (20.0, 300.0, 550.0, 800.0, 1200.0):
        report = run(ProprietaTemperaturaInput(fyk_MPa=355.0, ea_20_MPa=210000.0, theta_C=theta_C))
        assert report.data.fp_theta_MPa <= report.data.fy_theta_MPa + 1e-9


def test_shared_table_still_raises_outside_its_own_range_regression_guard():
    """Belt-and-braces: even if the pydantic bound were loosened, the shared module itself still
    refuses out-of-range θ (KeyNotFound), it never silently extrapolates."""
    from strutture.shared.fire_reduction import reduction_factors

    with pytest.raises(KeyNotFound):
        reduction_factors(1300.0)
