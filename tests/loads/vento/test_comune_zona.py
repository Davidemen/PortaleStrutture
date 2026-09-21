import pytest

from strutture.loads.vento.comune_zona import risolvi_zona
from strutture.shared.report import CalcError


@pytest.mark.unit
def test_zona_data_direttamente_ignora_comune():
    zona, comune = risolvi_zona(zona=9, comune=None, provincia=None, legacy_compat=False)
    assert zona == 9
    assert comune is None


@pytest.mark.unit
def test_zona_data_direttamente_bypassa_anche_in_legacy():
    zona, comune = risolvi_zona(zona=5, comune=None, provincia=None, legacy_compat=True)
    assert zona == 5
    assert comune is None


@pytest.mark.unit
def test_zona_da_comune_fixed_usa_il_campo_zona_vento():
    zona, comune = risolvi_zona(zona=None, comune="Corsico", provincia=None, legacy_compat=False)
    assert zona == 1
    assert comune is not None and comune.comune == "Corsico" and comune.provincia == "Milano"


@pytest.mark.unit
def test_zona_da_comune_legacy_bug_coincidenza_provincia_capoluogo():
    """Corsico's provincia (Milano) happens to be the name of another comune, so the buggy
    VLOOKUP(H5, Comuni!D:J,...) still finds a row and (since zona vento is uniform per provincia
    in this dataset) returns the same numeric zone as the fixed lookup -- spec §7/§8.
    """
    zona, comune = risolvi_zona(zona=None, comune="Corsico", provincia=None, legacy_compat=True)
    assert zona == 1
    assert comune.comune == "Corsico"


@pytest.mark.unit
def test_zona_da_comune_legacy_bug_fallisce_senza_capoluogo_omonimo():
    """Agrate Brianza's provincia is 'Monza e Brianza', not the name of any comune, so the legacy
    VLOOKUP(H5,...) has nothing to match against (mirrors Excel's #N/A) -- spec §7.
    """
    with pytest.raises(CalcError, match="Monza e Brianza"):
        risolvi_zona(zona=None, comune="Agrate Brianza", provincia=None, legacy_compat=True)


@pytest.mark.unit
def test_zona_da_comune_fixed_funziona_dove_il_legacy_fallisce():
    zona, comune = risolvi_zona(zona=None, comune="Agrate Brianza", provincia=None, legacy_compat=False)
    assert zona == 1
    assert comune.comune == "Agrate Brianza"


@pytest.mark.unit
def test_comune_non_trovato_solleva_calc_error():
    with pytest.raises(CalcError, match="non trovato"):
        risolvi_zona(zona=None, comune="Nonesistente Assoluto", provincia=None, legacy_compat=False)


@pytest.mark.unit
def test_comune_omonimo_senza_provincia_solleva_calc_error():
    with pytest.raises(CalcError, match="omonimo"):
        risolvi_zona(zona=None, comune="Castro", provincia=None, legacy_compat=False)


@pytest.mark.unit
def test_comune_omonimo_disambiguato_da_provincia():
    zona, comune = risolvi_zona(zona=None, comune="Castro", provincia="Lecce", legacy_compat=False)
    assert comune.provincia == "Lecce"
    assert zona == comune.zona_vento


@pytest.mark.unit
def test_comune_vuoto_senza_zona_solleva_calc_error():
    with pytest.raises(CalcError):
        risolvi_zona(zona=None, comune=None, provincia=None, legacy_compat=False)
