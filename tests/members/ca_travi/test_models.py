import pytest
from pydantic import ValidationError

from strutture.members.ca_travi.models import TraveRettangolareInput

BASE_KWARGS = {
    "b_mm": 600, "h_mm": 400, "tipo_acciaio": "RB500W", "tipo_cls": "C35/45", "copriferro_mm": 70,
    "n_ferri1": 5, "diametro_ferri1_mm": 20,
    "diametro_staffe1_mm": 12, "passo_staffe1_mm": 115,
    "ved_kN": 138, "med_slu_kNm": 318, "med_rara_kNm": 239, "med_qp_kNm": 200, "mrc_kNm": 350, "lt_m": 8,
}


@pytest.mark.unit
def test_defaults_reproduce_the_golden_shape():
    inputs = TraveRettangolareInput(**BASE_KWARGS)
    assert inputs.n_ferri2 == 0
    assert inputs.n_bracci_staffe1 == 2
    assert inputs.classe_duttilita == "CDB"
    assert inputs.condizioni_ambientali == "Ordinarie"
    assert inputs.combinazione == "Frequente"
    assert inputs.sensibilita_armatura == "Poco sensibile"
    assert inputs.classe_apertura_fessura == "w3"
    assert inputs.legacy_compat is False


@pytest.mark.unit
def test_copriferro_must_be_smaller_than_h():
    with pytest.raises(ValidationError):
        TraveRettangolareInput(**{**BASE_KWARGS, "copriferro_mm": 400})


@pytest.mark.unit
def test_second_bar_type_requires_positive_diameter_if_count_given():
    with pytest.raises(ValidationError):
        TraveRettangolareInput(**{**BASE_KWARGS, "n_ferri2": 2, "diametro_ferri2_mm": 0})


@pytest.mark.unit
def test_second_stirrup_type_requires_positive_diameter_if_bracci_given():
    with pytest.raises(ValidationError):
        TraveRettangolareInput(**{**BASE_KWARGS, "n_bracci_staffe2": 2, "diametro_staffe2_mm": 0})


@pytest.mark.unit
def test_invalid_concrete_class_rejected():
    with pytest.raises(ValidationError):
        TraveRettangolareInput(**{**BASE_KWARGS, "tipo_cls": "C99/99"})


@pytest.mark.unit
def test_invalid_classe_duttilita_rejected():
    with pytest.raises(ValidationError):
        TraveRettangolareInput(**{**BASE_KWARGS, "classe_duttilita": "CDX"})


@pytest.mark.unit
def test_negative_geometry_rejected():
    with pytest.raises(ValidationError):
        TraveRettangolareInput(**{**BASE_KWARGS, "b_mm": -600})
