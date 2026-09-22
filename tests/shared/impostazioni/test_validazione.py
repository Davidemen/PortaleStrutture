"""valida_eccezioni: unknown tool/field, non-numeric field, fractional exception on an integer field."""
import pytest
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.impostazioni.modelli import Impostazioni, PassoCampo
from strutture.shared.impostazioni.validazione import valida_eccezioni, valida_passi_per_tipo
from strutture.shared.tool import Tool


class _Input(BaseModel):
    model_config = ConfigDict(frozen=True)

    n_barre: int = Field(gt=0, json_schema_extra={"symbol": "N°", "group": "g"})
    h_mm: float = Field(gt=0, json_schema_extra={"unit": "mm", "symbol": "h", "group": "g"})
    copriferro_cm: float = Field(gt=0, json_schema_extra={"unit": "cm", "symbol": "c", "group": "g"})
    scelta: str = Field(json_schema_extra={"group": "g"})


class _Output(BaseModel):
    model_config = ConfigDict(frozen=True)

    ok: bool = True


def _tool() -> Tool:
    return Tool(name="prova", title="Prova", group="g", norm="n", input_model=_Input, output_model=_Output, run=lambda i: None)


@pytest.mark.unit
def test_unknown_tool():
    errori = valida_eccezioni((PassoCampo(strumento="boh", campo="h_mm", passo=1.0),), {"prova": _tool()})
    assert errori == ("Strumento sconosciuto: boh",)


@pytest.mark.unit
def test_unknown_or_non_numeric_field():
    tools = {"prova": _tool()}
    assert "prova.mai_esistito" in valida_eccezioni((PassoCampo(strumento="prova", campo="mai_esistito", passo=1.0),), tools)[0]


@pytest.mark.unit
def test_fractional_exception_on_integer_field_rejected():
    errori = valida_eccezioni((PassoCampo(strumento="prova", campo="n_barre", passo=1.5),), {"prova": _tool()})
    assert errori == ("Il passo deve essere intero per prova.n_barre",)


@pytest.mark.unit
def test_valid_exception_accepted():
    assert valida_eccezioni((PassoCampo(strumento="prova", campo="h_mm", passo=2.0),), {"prova": _tool()}) == ()


@pytest.mark.unit
def test_none_passo_always_accepted():
    assert valida_eccezioni((PassoCampo(strumento="prova", campo="n_barre", passo=None),), {"prova": _tool()}) == ()


@pytest.mark.unit
def test_no_type_steps_is_always_valid():
    assert valida_passi_per_tipo(Impostazioni(), {"prova": _tool()}) == ()


@pytest.mark.unit
def test_type_step_that_does_not_survive_conversion_is_rejected_by_field():
    impostazioni = Impostazioni(passi_per_tipo={"copriferro": 1.2345})
    errori = valida_passi_per_tipo(impostazioni, {"prova": _tool()})
    assert len(errori) == 1
    assert "prova.copriferro_cm" in errori[0]


@pytest.mark.unit
def test_type_step_that_converts_cleanly_is_accepted():
    assert valida_passi_per_tipo(Impostazioni(passi_per_tipo={"copriferro": 5.0}), {"prova": _tool()}) == ()


@pytest.mark.unit
def test_field_exception_shields_it_from_the_type_step_conflict():
    impostazioni = Impostazioni(
        passi_per_tipo={"copriferro": 1.2345},
        passi_per_campo=(PassoCampo(strumento="prova", campo="copriferro_cm", passo=2.0),),
    )
    assert valida_passi_per_tipo(impostazioni, {"prova": _tool()}) == ()
