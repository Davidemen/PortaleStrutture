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

FAKE_TOOLS: dict[str, Tool] = {SUM_TOOL.name: SUM_TOOL, FLAG_TOOL.name: FLAG_TOOL}
