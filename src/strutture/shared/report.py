"""Result envelope shared by every tool: success flag, data, code checks, warnings, errors."""
from typing import Any

from pydantic import BaseModel, ConfigDict

from .relazione.modelli import Traccia


class Check(BaseModel):
    """One pass/fail verification against a code clause."""

    model_config = ConfigDict(frozen=True)

    name: str
    passed: bool
    detail: str = ""
    clause: str = ""
    value: float | None = None  # demand, in `unit`; with `limit` it drives the UI utilisation bar
    limit: float | None = None  # capacity / admissible value, in `unit`
    unit: str = ""


class ErrorDetail(BaseModel):
    """One validation error with its location, e.g. ("reazioni", 17, "fz_kN") = table, 0-based row, column."""

    model_config = ConfigDict(frozen=True)

    loc: tuple[str | int, ...]
    message: str


class Report[T](BaseModel):
    model_config = ConfigDict(frozen=True)

    ok: bool
    data: T | None = None
    checks: tuple[Check, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    error_details: tuple[ErrorDetail, ...] = ()  # same errors, machine-locatable (form fields, table cells)
    inputs_echo: dict[str, Any] = {}
    relazione: tuple[Traccia, ...] = ()  # "Sviluppo dei calcoli", built only when asked (execute(..., con_relazione=True))


class CalcError(ValueError):
    """Domain error with a user-facing message (input outside the method's validity range, etc.)."""


def success[T](data: T, inputs: BaseModel, checks: tuple[Check, ...] = (), warnings: tuple[str, ...] = ()) -> Report[T]:
    return Report(ok=True, data=data, checks=checks, warnings=warnings, inputs_echo=inputs.model_dump(mode="json"))


def failure(
    errors: tuple[str, ...],
    inputs_echo: dict[str, Any] | None = None,
    details: tuple[ErrorDetail, ...] = (),
) -> Report[Any]:
    return Report(ok=False, errors=errors, error_details=details, inputs_echo=inputs_echo or {})
