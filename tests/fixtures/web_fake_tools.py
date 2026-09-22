"""Two fake tools used only by `tests/web/`, exercising the generic web UI end to end."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.report import CalcError, Check, Report, success
from strutture.shared.tool import Tool


class SumInputs(BaseModel):
    model_config = ConfigDict(frozen=True)

    a: float = Field(description="Primo addendo", json_schema_extra={"unit": "kN"}, ge=0, le=100)
    b: float = Field(description="Secondo addendo", json_schema_extra={"unit": "kN"}, ge=0, le=100, default=10.0)
    legacy_compat: bool = False


class SumOutputs(BaseModel):
    model_config = ConfigDict(frozen=True)

    total: float


def _run_sum(inputs: SumInputs) -> Report[SumOutputs]:
    total = inputs.a + inputs.b
    checks = (Check(name="somma positiva", passed=total >= 0, clause="TEST §1"),)
    return success(SumOutputs(total=total), inputs, checks=checks)


SUM_TOOL = Tool(
    name="fake-sum",
    title="Somma di prova",
    group="Prova",
    norm="TEST §1",
    input_model=SumInputs,
    output_model=SumOutputs,
    run=_run_sum,
)


class FlagInputs(BaseModel):
    model_config = ConfigDict(frozen=True)

    mode: str = Field(description="Modalità", json_schema_extra={"unit": ""})
    legacy_compat: bool = False


class FlagOutputs(BaseModel):
    model_config = ConfigDict(frozen=True)

    mode: str


def _run_flag(inputs: FlagInputs) -> Report[FlagOutputs]:
    if inputs.mode == "boom":
        raise CalcError("modalità 'boom' non è valida per questo strumento")
    if inputs.mode == "crash":
        raise RuntimeError("bug simulato")
    return success(FlagOutputs(mode=inputs.mode), inputs)


FLAG_TOOL = Tool(
    name="fake-flag",
    title="Bandiera di prova",
    group="Prova",
    norm="TEST §2",
    input_model=FlagInputs,
    output_model=FlagOutputs,
    run=_run_flag,
)

class VerificaInputs(BaseModel):
    """A demand/capacity check monotone in `b` (§23/§24 API tests): larger `b` -> smaller η."""

    model_config = ConfigDict(frozen=True)

    domanda: float = Field(description="Domanda", json_schema_extra={"unit": "kN"}, gt=0)
    capacita: float = Field(description="Capacità", json_schema_extra={"unit": "kN"}, gt=0, le=1000)
    n_barre: int = Field(description="Numero di barre", json_schema_extra={"unit": ""}, ge=1, le=20, default=1)
    # Optional numeric field (`float | None`): pydantic gives it no top-level `type`, only an
    # `anyOf` with the numeric branch alongside `{"type": "null"}` -- exercises the "Dimensiona"
    # `_valida_campo`/`_valida_intervallo` `anyOf` resolution (§23.3 point 7).
    margine: float | None = Field(default=None, description="Margine opzionale", json_schema_extra={"unit": "kN"}, gt=0, le=50)
    legacy_compat: bool = False


class VerificaOutputs(BaseModel):
    model_config = ConfigDict(frozen=True)

    eta: float


def _run_verifica(inputs: VerificaInputs) -> Report[VerificaOutputs]:
    eta = inputs.domanda / inputs.capacita
    checks = (Check(name="Resistenza", passed=eta <= 1, clause="TEST §3", value=inputs.domanda, limit=inputs.capacita),)
    return success(VerificaOutputs(eta=eta), inputs, checks=checks)


VERIFICA_TOOL = Tool(
    name="fake-verifica",
    title="Verifica di prova",
    group="Prova",
    norm="TEST §3",
    input_model=VerificaInputs,
    output_model=VerificaOutputs,
    run=_run_verifica,
)

FAKE_TOOLS: dict[str, Tool] = {
    SUM_TOOL.name: SUM_TOOL, FLAG_TOOL.name: FLAG_TOOL, VERIFICA_TOOL.name: VERIFICA_TOOL,
}
