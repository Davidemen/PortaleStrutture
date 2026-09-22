"""valida_eccezioni: unknown tool/field, non-numeric field, fractional exception on an integer field."""
import pytest
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.impostazioni.modelli import PassoCampo
from strutture.shared.impostazioni.validazione import valida_eccezioni
from strutture.shared.tool import Tool


class _Input(BaseModel):
    model_config = ConfigDict(frozen=True)

    n_barre: int = Field(gt=0, json_schema_extra={"symbol": "N°", "group": "g"})
    h_mm: float = Field(gt=0, json_schema_extra={"unit": "mm", "symbol": "h", "group": "g"})
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
