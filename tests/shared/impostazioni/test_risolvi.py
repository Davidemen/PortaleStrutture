"""passo_proposto: precedence campo > tipo > intero > none; None exception masks the type step;
cm/mm conversion of a copriferro step; unresolvable conversion raises."""
import pytest

from strutture.shared.impostazioni.modelli import Impostazioni, PassoCampo
from strutture.shared.impostazioni.risolvi import passo_proposto


@pytest.mark.unit
def test_exception_wins_over_type_step():
    impostazioni = Impostazioni(
        passi_per_tipo={"lunghezza_mm": 5.0},
        passi_per_campo=(PassoCampo(strumento="t", campo="h_mm", passo=2.0),),
    )
    risultato = passo_proposto(impostazioni, "t", "h_mm", {"unit": "mm"}, "lunghezza_mm")
    assert risultato.passo == 2.0
    assert risultato.origine == "campo"


@pytest.mark.unit
def test_none_exception_masks_type_step():
    impostazioni = Impostazioni(
        passi_per_tipo={"lunghezza_mm": 5.0},
        passi_per_campo=(PassoCampo(strumento="t", campo="h_mm", passo=None),),
    )
    risultato = passo_proposto(impostazioni, "t", "h_mm", {"unit": "mm"}, "lunghezza_mm")
    assert risultato.passo is None
    assert risultato.origine == "campo"


@pytest.mark.unit
def test_type_step_used_when_no_exception():
    impostazioni = Impostazioni(passi_per_tipo={"lunghezza_mm": 5.0})
    risultato = passo_proposto(impostazioni, "t", "h_mm", {"unit": "mm"}, "lunghezza_mm")
    assert risultato == (5.0, "tipo", "lunghezza_mm")


@pytest.mark.unit
def test_integer_field_defaults_to_one():
    risultato = passo_proposto(Impostazioni(), "t", "n", {}, "intero")
    assert risultato == (1.0, "intero", "intero")


@pytest.mark.unit
def test_no_type_no_step_gives_none():
    risultato = passo_proposto(Impostazioni(), "t", "ag_g", {"unit": "g"}, None)
    assert risultato == (None, None, None)


@pytest.mark.unit
def test_copriferro_step_converted_from_mm_to_cm():
    impostazioni = Impostazioni(passi_per_tipo={"copriferro": 5.0})
    risultato = passo_proposto(impostazioni, "t", "copriferro_cm", {"unit": "cm"}, "copriferro")
    assert risultato.passo == pytest.approx(0.5)
    assert risultato.origine == "tipo"


@pytest.mark.unit
def test_conversion_that_does_not_survive_4_decimals_raises():
    # 1,2345 mm (4 decimals, a valid type step) -> 0,12345 cm (5 decimals): refused, not silently rounded.
    impostazioni = Impostazioni(passi_per_tipo={"copriferro": 1.2345})
    with pytest.raises(ValueError, match="non è esprimibile"):
        passo_proposto(impostazioni, "t", "copriferro_cm", {"unit": "cm"}, "copriferro")
