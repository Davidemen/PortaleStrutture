import pytest
from pydantic import ValidationError

from strutture.members.ca_fessurazione.models import AperturaFessureInput

pytestmark = pytest.mark.unit

_BASE = {
    "classe_calcestruzzo": "C28/35",
    "tipo_barre": "barre aderenza migliorata",
    "tipo_sollecitazione": "caso di flessione",
    "durata_carico": "lunga durata",
    "classe_fessurazione": "w3 (0.40 mm)",
    "interferro_mm": 200,
    "sigma_s_MPa": 286,
    "h_mm": 250,
    "x_mm": 75.84,
    "b_mm": 1000,
    "n1": 5,
    "phi1_mm": 20,
    "copriferro_mm": 35,
}


def test_valid_input_accepted():
    AperturaFessureInput(**_BASE)


def test_x_must_be_less_than_h():
    with pytest.raises(ValidationError, match="asse neutro"):
        AperturaFessureInput(**{**_BASE, "x_mm": 250})


def test_effective_depth_must_be_positive():
    with pytest.raises(ValidationError, match="altezza utile"):
        AperturaFessureInput(**{**_BASE, "h_mm": 40, "x_mm": 10})


@pytest.mark.parametrize("overrides", [{"n2": 2, "phi2_mm": 0}, {"n2": 0, "phi2_mm": 12}])
def test_second_bar_group_requires_both_fields(overrides):
    with pytest.raises(ValidationError, match="n2 e ø2"):
        AperturaFessureInput(**{**_BASE, **overrides})


def test_second_bar_group_both_zero_or_both_positive_are_valid():
    AperturaFessureInput(**{**_BASE, "n2": 0, "phi2_mm": 0})
    AperturaFessureInput(**{**_BASE, "n2": 2, "phi2_mm": 12})


def test_dropped_load_case_enum_value_rejected():
    with pytest.raises(ValidationError):
        AperturaFessureInput(**{**_BASE, "tipo_sollecitazione": "caso di trazione eccentrica (o per singole parti di sezione)"})


def test_sheet_typo_spelling_rejected_in_favour_of_corrected_literal():
    """We use the corrected 'caso di trazione semplice' spelling; the sheet's own dropdown
    literal has a typo ('smplice') that oracle tests feed straight into the workbook cell."""
    with pytest.raises(ValidationError):
        AperturaFessureInput(**{**_BASE, "tipo_sollecitazione": "caso di trazione smplice"})
