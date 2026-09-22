"""Impostazioni model: factory values, limits, decimal rules (WORKBENCH_SPEC.md §26.2)."""
import pytest
from pydantic import ValidationError

from strutture.shared.impostazioni.modelli import FABBRICA, MAX_ECCEZIONI, Impostazioni, PassoCampo


@pytest.mark.unit
def test_fabbrica_values():
    assert FABBRICA.obiettivo_sfruttamento == 1.0
    assert FABBRICA.obiettivo_su_verifiche_minimo is False
    assert all(passo is None for passo in FABBRICA.passi_per_tipo.values())
    assert FABBRICA.passi_per_campo == ()


@pytest.mark.unit
def test_obiettivo_deve_essere_positivo_e_al_massimo_1():
    with pytest.raises(ValidationError):
        Impostazioni(obiettivo_sfruttamento=0)
    with pytest.raises(ValidationError):
        Impostazioni(obiettivo_sfruttamento=1.01)
    Impostazioni(obiettivo_sfruttamento=1.0)


@pytest.mark.unit
def test_obiettivo_al_massimo_2_decimali():
    with pytest.raises(ValidationError):
        Impostazioni(obiettivo_sfruttamento=0.905)
    Impostazioni(obiettivo_sfruttamento=0.90)


@pytest.mark.unit
def test_passo_per_tipo_limiti():
    with pytest.raises(ValidationError):
        Impostazioni(passi_per_tipo={"lunghezza_mm": 0})
    with pytest.raises(ValidationError):
        Impostazioni(passi_per_tipo={"lunghezza_mm": 1001})
    with pytest.raises(ValidationError):
        Impostazioni(passi_per_tipo={"lunghezza_mm": 1.23456})
    Impostazioni(passi_per_tipo={"lunghezza_mm": 2.0})


@pytest.mark.unit
def test_passo_intero_deve_essere_intero():
    with pytest.raises(ValidationError):
        Impostazioni(passi_per_tipo={"intero": 1.5})
    Impostazioni(passi_per_tipo={"intero": 1.0})


@pytest.mark.unit
def test_passo_campo_al_massimo_4_decimali():
    with pytest.raises(ValidationError):
        PassoCampo(strumento="x", campo="y", passo=1.23456)
    PassoCampo(strumento="x", campo="y", passo=1.2345)


@pytest.mark.unit
def test_passo_campo_none_e_valido():
    PassoCampo(strumento="x", campo="y", passo=None)


@pytest.mark.unit
def test_eccezioni_duplicate_rifiutate():
    with pytest.raises(ValidationError):
        Impostazioni(passi_per_campo=(
            PassoCampo(strumento="a", campo="b", passo=1.0),
            PassoCampo(strumento="a", campo="b", passo=2.0),
        ))


@pytest.mark.unit
def test_massimo_eccezioni():
    eccezioni = tuple(PassoCampo(strumento="a", campo=f"c{i}", passo=1.0) for i in range(MAX_ECCEZIONI))
    Impostazioni(passi_per_campo=eccezioni)
    with pytest.raises(ValidationError):
        Impostazioni(passi_per_campo=(*eccezioni, PassoCampo(strumento="a", campo="oltre", passo=1.0)))


@pytest.mark.unit
def test_extra_forbid():
    with pytest.raises(ValidationError):
        Impostazioni(campo_sconosciuto=1)
