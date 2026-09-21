"""Fixed-behaviour tests (legacy_compat=False): D5 fu bug fix, default exposure times, warning,
and boundary/validation cases (docs/divergences/acciaio_incendio.md)."""
import pytest
from pydantic import ValidationError

from strutture.members.acciaio_incendio.models import DEFAULT_TEMPI_MIN, ResistenzaIncendioInput
from strutture.members.acciaio_incendio.tool import NO_THERMAL_LAG_WARNING, run
from strutture.shared.report import CalcError


def test_default_tempi_min_matches_sheet_fill_down():
    assert DEFAULT_TEMPI_MIN == tuple(float(t) for t in range(5, 121, 5))
    assert len(DEFAULT_TEMPI_MIN) == 24


def test_s275_fu_bug_fixed_in_code_standard_mode():
    """docs/divergences/acciaio_incendio.md — sheet's D5 always returns 510 for S275; fixed = 430."""
    legacy = run(ResistenzaIncendioInput(grado="S275", tempi_min=(5.0,), legacy_compat=True))
    fixed = run(ResistenzaIncendioInput(grado="S275", tempi_min=(5.0,), legacy_compat=False))
    assert legacy.data.materiale.fu_20_MPa == pytest.approx(510.0)
    assert fixed.data.materiale.fu_20_MPa == pytest.approx(430.0)


def test_s235_and_s355_unaffected_by_the_bug():
    for grado in ("S235", "S355"):
        legacy = run(ResistenzaIncendioInput(grado=grado, tempi_min=(5.0,), legacy_compat=True))
        fixed = run(ResistenzaIncendioInput(grado=grado, tempi_min=(5.0,), legacy_compat=False))
        assert legacy.data.materiale.fu_20_MPa == pytest.approx(fixed.data.materiale.fu_20_MPa)


def test_no_thermal_lag_warning_is_always_emitted():
    report = run(ResistenzaIncendioInput(grado="S355", tempi_min=(5.0,)))
    assert NO_THERMAL_LAG_WARNING in report.warnings


def test_reduced_values_never_exceed_the_20c_reference():
    report = run(ResistenzaIncendioInput(grado="S355", tempi_min=(60.0,)))
    riga = report.data.righe[0]
    materiale = report.data.materiale
    assert riga.fy_theta_MPa < materiale.fy_20_MPa
    assert riga.fu_theta_MPa < materiale.fu_20_MPa
    assert riga.e_theta_MPa < 210000.0


def test_unknown_grade_rejected_by_validation():
    with pytest.raises(ValidationError):
        ResistenzaIncendioInput(grado="S460", tempi_min=(5.0,))


def test_empty_tempi_min_rejected_by_validation():
    with pytest.raises(ValidationError):
        ResistenzaIncendioInput(grado="S355", tempi_min=())


def test_time_beyond_table_range_raises_calc_error():
    with pytest.raises(CalcError):
        run(ResistenzaIncendioInput(grado="S355", tempi_min=(400.0,)))
