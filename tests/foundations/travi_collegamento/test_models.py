"""Validation tests for `TraviCollegamentoInput` (required-per-norma fields, boundary checks)."""
import pytest
from pydantic import ValidationError

from strutture.foundations.travi_collegamento.models import TraviCollegamentoInput

_BASE_NTC = {
    "norma": "NTC2018", "ag_g": 0.151, "f0": 2.43, "categoria_sottosuolo": "B", "categoria_topografica": "T1",
    "b_mm": 400, "h_mm": 400, "phi_mm": 16, "n_barre": 6, "classe_calcestruzzo": "C25/30", "classe_acciaio": "B450C",
    "n1_kN": 2000, "n2_kN": 2500, "l_mm": 5000, "beta": 1, "phi_staffa_mm": 10, "n_bracci": 2, "cf_mm": 40, "p_mm": 125,
}

_BASE_EN = {
    "norma": "EN1998", "ag_g": 0.151, "categoria_sottosuolo": "B", "ms": 5.6,
    "b_mm": 400, "h_mm": 450, "phi_mm": 16, "n_barre": 8, "classe_calcestruzzo": "C25/30", "classe_acciaio": "B450C",
    "n1_kN": 2000, "n2_kN": 2500, "l_mm": 5000, "beta": 1, "n_piani": 3,
    "phi_staffa_mm": 10, "n_bracci": 2, "alpha_staffa_deg": 90, "cf_mm": 40, "p_mm": 200,
}


@pytest.mark.unit
def test_valid_ntc_input_accepted() -> None:
    TraviCollegamentoInput(**_BASE_NTC)


@pytest.mark.unit
def test_valid_en_input_accepted() -> None:
    TraviCollegamentoInput(**_BASE_EN)


@pytest.mark.unit
def test_ntc_requires_f0() -> None:
    with pytest.raises(ValidationError):
        TraviCollegamentoInput(**{**_BASE_NTC, "f0": None})


@pytest.mark.unit
def test_ntc_requires_categoria_topografica() -> None:
    with pytest.raises(ValidationError):
        TraviCollegamentoInput(**{**_BASE_NTC, "categoria_topografica": None})


@pytest.mark.unit
def test_en_requires_ms() -> None:
    with pytest.raises(ValidationError):
        TraviCollegamentoInput(**{**_BASE_EN, "ms": None})


@pytest.mark.unit
def test_invalid_categoria_sottosuolo_rejected() -> None:
    with pytest.raises(ValidationError):
        TraviCollegamentoInput(**{**_BASE_NTC, "categoria_sottosuolo": "E"})


@pytest.mark.unit
def test_negative_section_rejected() -> None:
    with pytest.raises(ValidationError):
        TraviCollegamentoInput(**{**_BASE_NTC, "b_mm": -10})


@pytest.mark.unit
def test_invalid_concrete_class_rejected() -> None:
    with pytest.raises(ValidationError):
        TraviCollegamentoInput(**{**_BASE_NTC, "classe_calcestruzzo": "C10/15"})


@pytest.mark.unit
def test_model_is_frozen() -> None:
    inputs = TraviCollegamentoInput(**_BASE_NTC)
    with pytest.raises(ValidationError):
        inputs.b_mm = 500  # type: ignore[misc]
