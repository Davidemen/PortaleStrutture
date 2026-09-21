import pytest
from pydantic import ValidationError

from strutture.loads.vento.models import VentoPressioneInput

BASE = {"altitudine_m": 120, "periodo_ritorno_anni": 50, "categoria_esposizione": "II", "ct": 1, "altezza_edificio_m": 60}


@pytest.mark.unit
def test_accetta_comune_senza_zona():
    inputs = VentoPressioneInput(comune="Milano", **BASE)
    assert inputs.comune == "Milano"
    assert inputs.zona is None


@pytest.mark.unit
def test_accetta_zona_senza_comune():
    inputs = VentoPressioneInput(zona=3, **BASE)
    assert inputs.zona == 3
    assert inputs.comune is None


@pytest.mark.unit
def test_rifiuta_ne_comune_ne_zona():
    with pytest.raises(ValidationError, match="esattamente uno"):
        VentoPressioneInput(**BASE)


@pytest.mark.unit
def test_rifiuta_comune_vuoto_ne_zona():
    with pytest.raises(ValidationError, match="esattamente uno"):
        VentoPressioneInput(comune="   ", **BASE)


@pytest.mark.unit
def test_rifiuta_sia_comune_che_zona():
    with pytest.raises(ValidationError, match="esattamente uno"):
        VentoPressioneInput(comune="Milano", zona=3, **BASE)


@pytest.mark.unit
def test_rifiuta_zona_fuori_da_1_9():
    with pytest.raises(ValidationError):
        VentoPressioneInput(zona=10, **BASE)


@pytest.mark.unit
def test_rifiuta_periodo_ritorno_non_maggiore_di_1():
    with pytest.raises(ValidationError):
        VentoPressioneInput(zona=1, **{**BASE, "periodo_ritorno_anni": 1})


@pytest.mark.unit
def test_rifiuta_altezza_edificio_non_positiva():
    with pytest.raises(ValidationError):
        VentoPressioneInput(zona=1, **{**BASE, "altezza_edificio_m": 0})


@pytest.mark.unit
def test_rifiuta_categoria_esposizione_non_valida():
    with pytest.raises(ValidationError):
        VentoPressioneInput(zona=1, **{**BASE, "categoria_esposizione": "VI"})


@pytest.mark.unit
def test_rifiuta_n_sezioni_non_positivo():
    with pytest.raises(ValidationError):
        VentoPressioneInput(zona=1, **{**BASE, "n_sezioni": 0})


@pytest.mark.unit
def test_input_e_immutabile():
    inputs = VentoPressioneInput(zona=1, **BASE)
    with pytest.raises(ValidationError):
        inputs.zona = 5
