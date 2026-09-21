"""Validation tests for `EdometricoInput`."""
import pytest
from pydantic import ValidationError

from strutture.geotechnics.cedimenti_edometrico.models import EdometricoInput

_STRATI = [
    {"z_top_m": 0.0, "z_bot_m": 3.7, "modulo_MPa": 5.5},
    {"z_top_m": 3.7, "z_bot_m": 4.7, "modulo_MPa": 7.0},
]

_BASE = {"sistema_unita": "SI", "b": 3.5, "l": 5.0, "gamma": 18.0, "q": 50.0, "strati": _STRATI}


@pytest.mark.unit
def test_valid_input_accepted() -> None:
    EdometricoInput(**_BASE)


@pytest.mark.unit
def test_model_is_frozen() -> None:
    inputs = EdometricoInput(**_BASE)
    with pytest.raises(ValidationError):
        inputs.b = 4.0  # type: ignore[misc]


@pytest.mark.unit
def test_layers_must_start_at_zero() -> None:
    strati = [{"z_top_m": 1.0, "z_bot_m": 3.7, "modulo_MPa": 5.5}]
    with pytest.raises(ValidationError, match="deve partire da 0"):
        EdometricoInput(**{**_BASE, "strati": strati})


@pytest.mark.unit
def test_layers_must_be_contiguous() -> None:
    strati = [
        {"z_top_m": 0.0, "z_bot_m": 3.0, "modulo_MPa": 5.5},
        {"z_top_m": 3.5, "z_bot_m": 5.0, "modulo_MPa": 7.0},
    ]
    with pytest.raises(ValidationError, match="non è contigua"):
        EdometricoInput(**{**_BASE, "strati": strati})


@pytest.mark.unit
def test_negative_width_rejected() -> None:
    with pytest.raises(ValidationError):
        EdometricoInput(**{**_BASE, "b": -1.0})


@pytest.mark.unit
def test_invalid_sistema_unita_rejected() -> None:
    with pytest.raises(ValidationError):
        EdometricoInput(**{**_BASE, "sistema_unita": "imperiale"})


@pytest.mark.unit
def test_invalid_metodo_tensioni_rejected() -> None:
    with pytest.raises(ValidationError):
        EdometricoInput(**{**_BASE, "metodo_tensioni": "boussinesq"})


@pytest.mark.unit
def test_griglia_troppo_fine_rejected() -> None:
    with pytest.raises(ValidationError, match="20000"):
        EdometricoInput(**{**_BASE, "dz": 0.001, "z_max": 100.0})


@pytest.mark.unit
def test_empty_strati_rejected() -> None:
    with pytest.raises(ValidationError):
        EdometricoInput(**{**_BASE, "strati": []})


@pytest.mark.unit
def test_falda_defaults_to_none_dry_site() -> None:
    assert EdometricoInput(**_BASE).falda is None


@pytest.mark.unit
def test_falda_accepts_a_non_negative_depth() -> None:
    assert EdometricoInput(**{**_BASE, "falda": 2.5}).falda == pytest.approx(2.5)


@pytest.mark.unit
def test_negative_falda_rejected() -> None:
    with pytest.raises(ValidationError):
        EdometricoInput(**{**_BASE, "falda": -1.0})
