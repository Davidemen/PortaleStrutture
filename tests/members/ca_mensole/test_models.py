"""Validation tests for `MensolaTozzaInput` (boundary/enum/dropdown-allowlist checks)."""
import pytest
from pydantic import ValidationError

from strutture.members.ca_mensole.models import MensolaTozzaInput

_BASE = {
    "a_mm": 177, "h_mm": 450, "b_mm": 800, "c_mm": 50, "ped_kN": 136, "hed_kN": 0,
    "acciaio": "B450C", "calcestruzzo": "C32/40",
    "n_hor": 8, "phi_hor_mm": 12, "n_incl": 0, "phi_incl_mm": 0, "angolo_incl_deg": 0,
    "n_staffe": 3, "phi_staffe_mm": 12, "staffe_verticali": "NO",
}


@pytest.mark.unit
def test_valid_input_accepted() -> None:
    MensolaTozzaInput(**_BASE)


@pytest.mark.unit
def test_cover_greater_than_height_rejected() -> None:
    with pytest.raises(ValidationError):
        MensolaTozzaInput(**{**_BASE, "c_mm": 500})


@pytest.mark.unit
def test_cover_equal_height_rejected() -> None:
    with pytest.raises(ValidationError):
        MensolaTozzaInput(**{**_BASE, "c_mm": 450})


@pytest.mark.unit
def test_b500c_not_allowed_dropdown_allowlist_fix() -> None:
    """Divergence: B500C exists in Tabelle!M45:P49 but is excluded from H14's dropdown
    (BU16:BU20) - the allowlist is enforced here too."""
    with pytest.raises(ValidationError):
        MensolaTozzaInput(**{**_BASE, "acciaio": "B500C"})


@pytest.mark.unit
def test_invalid_concrete_class_rejected() -> None:
    with pytest.raises(ValidationError):
        MensolaTozzaInput(**{**_BASE, "calcestruzzo": "C10/15"})


@pytest.mark.unit
def test_negative_load_rejected() -> None:
    with pytest.raises(ValidationError):
        MensolaTozzaInput(**{**_BASE, "ped_kN": -10})


@pytest.mark.unit
def test_incline_angle_out_of_range_rejected() -> None:
    with pytest.raises(ValidationError):
        MensolaTozzaInput(**{**_BASE, "angolo_incl_deg": 120})


@pytest.mark.unit
def test_invalid_staffe_verticali_enum_rejected() -> None:
    with pytest.raises(ValidationError):
        MensolaTozzaInput(**{**_BASE, "staffe_verticali": "MAYBE"})
