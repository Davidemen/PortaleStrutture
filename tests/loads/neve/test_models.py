import re

import pytest
from pydantic import ValidationError

from strutture.loads.neve.models import AccumuloInput, CaricoFaldaInput

_FALDA_KWARGS = {
    "as_m": 250,
    "topografia": "Normale",
    "tipo_copertura": "Copertura ad una falda",
    "a": 0,
    "parapetto": "NO",
    "a1": 0,
    "parapetto1": "NO",
    "a2": 0,
    "parapetto2": "NO",
}

_ACCUMULO_KWARGS = {"as_m": 249, "topografia": "Normale", "b1": 10, "b2": 10, "h": 5, "a": 0, "m1_input": 0.8, "msup": 0.45}

_UNA_FALDA_MINIMAL = {
    "as_m": 250,
    "topografia": "Normale",
    "tipo_copertura": "Copertura ad una falda",
    "a": 0,
    "parapetto": "NO",
}

_DUE_FALDE_MINIMAL = {
    "as_m": 250,
    "topografia": "Normale",
    "tipo_copertura": "Copertura a due falde",
    "a1": 35,
    "parapetto1": "NO",
    "a2": 50,
    "parapetto2": "NO",
}


@pytest.mark.unit
def test_comune_and_zona_are_mutually_exclusive():
    with pytest.raises(ValidationError):
        CaricoFaldaInput(comune="Mapello", zona="I (alpina)", **_FALDA_KWARGS)


@pytest.mark.unit
def test_comune_or_zona_is_required():
    with pytest.raises(ValidationError):
        CaricoFaldaInput(**_FALDA_KWARGS)


@pytest.mark.unit
def test_zona_alone_is_accepted():
    inputs = CaricoFaldaInput(zona="II", **_FALDA_KWARGS)
    assert inputs.zona == "II"
    assert inputs.comune is None


@pytest.mark.unit
def test_invalid_topografia_enum_rejected():
    with pytest.raises(ValidationError):
        CaricoFaldaInput(comune="Mapello", **{**_FALDA_KWARGS, "topografia": "Esposta"})


@pytest.mark.unit
def test_negative_altitude_rejected():
    with pytest.raises(ValidationError):
        CaricoFaldaInput(comune="Mapello", **{**_FALDA_KWARGS, "as_m": -1})


@pytest.mark.unit
def test_pitch_angle_out_of_range_rejected():
    with pytest.raises(ValidationError):
        CaricoFaldaInput(comune="Mapello", **{**_FALDA_KWARGS, "a": 91})


@pytest.mark.unit
def test_accumulo_widths_must_be_positive():
    with pytest.raises(ValidationError):
        AccumuloInput(comune="Bergamo", **{**_ACCUMULO_KWARGS, "b1": 0})


@pytest.mark.unit
def test_accumulo_comune_and_zona_mutually_exclusive():
    with pytest.raises(ValidationError):
        AccumuloInput(comune="Bergamo", zona="II", **_ACCUMULO_KWARGS)


@pytest.mark.unit
def test_una_falda_accepts_only_its_own_fields():
    """A user selecting "una falda" must not be forced to also fill the two-pitch fields."""
    inputs = CaricoFaldaInput(zona="II", **_UNA_FALDA_MINIMAL)
    assert inputs.a == 0
    assert inputs.parapetto == "NO"
    assert inputs.a1 is None and inputs.parapetto1 is None
    assert inputs.a2 is None and inputs.parapetto2 is None


@pytest.mark.unit
def test_due_falde_accepts_only_its_own_fields():
    """A user selecting "due falde" must not be forced to also fill the one-pitch fields."""
    inputs = CaricoFaldaInput(zona="II", **_DUE_FALDE_MINIMAL)
    assert inputs.a1 == 35 and inputs.parapetto1 == "NO"
    assert inputs.a2 == 50 and inputs.parapetto2 == "NO"
    assert inputs.a is None and inputs.parapetto is None


@pytest.mark.unit
def test_una_falda_missing_a_raises_italian_message_naming_the_field():
    kwargs = {key: value for key, value in _UNA_FALDA_MINIMAL.items() if key != "a"}
    with pytest.raises(ValidationError) as exc_info:
        CaricoFaldaInput(zona="II", **kwargs)
    message = str(exc_info.value)
    assert re.search(r"campo obbligatorio mancante per tipo_copertura='Copertura ad una falda': a\b", message)


@pytest.mark.unit
def test_due_falde_missing_multiple_fields_names_all_of_them():
    kwargs = {key: value for key, value in _DUE_FALDE_MINIMAL.items() if key not in ("a1", "a2")}
    with pytest.raises(ValidationError) as exc_info:
        CaricoFaldaInput(zona="II", **kwargs)
    message = str(exc_info.value)
    assert "campi obbligatori mancanti" in message
    assert "a1" in message and "a2" in message


@pytest.mark.unit
def test_una_falda_extra_due_falde_fields_are_accepted_not_required():
    """Supplying the other roof type's fields too (e.g. copy-pasted from a previous run) must
    not raise -- they are simply unused/ignored by `run_carico_falda` for this tipo_copertura."""
    inputs = CaricoFaldaInput(zona="II", **_UNA_FALDA_MINIMAL, a1=10, parapetto1="SI", a2=20, parapetto2="NO")
    assert inputs.a1 == 10
