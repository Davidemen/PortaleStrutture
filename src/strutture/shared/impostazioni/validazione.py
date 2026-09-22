"""Validation of `passi_per_campo` that needs the tool registry (§26.2): pure, given the tools."""
from collections.abc import Mapping

from strutture.shared.tool import Tool

from .campi import campi_numerici
from .modelli import PassoCampo
from .tipi_dato import tipo_dato


def valida_eccezioni(eccezioni: tuple[PassoCampo, ...], tools: Mapping[str, Tool]) -> tuple[str, ...]:
    """Every Italian error message for `eccezioni` against the current tool registry (empty = valid)."""
    errori: list[str] = []
    for eccezione in eccezioni:
        errori.extend(_valida_una(eccezione, tools))
    return tuple(errori)


def _valida_una(eccezione: PassoCampo, tools: Mapping[str, Tool]) -> tuple[str, ...]:
    tool = tools.get(eccezione.strumento)
    if tool is None:
        return (f"Strumento sconosciuto: {eccezione.strumento}",)
    campi = dict(campi_numerici(tool))
    schema_campo = campi.get(eccezione.campo)
    if schema_campo is None:
        return (f"Campo non numerico o inesistente: {eccezione.strumento}.{eccezione.campo}",)
    if eccezione.passo is None:
        return ()
    if tipo_dato(eccezione.campo, schema_campo) == "intero" and eccezione.passo != int(eccezione.passo):
        return (f"Il passo deve essere intero per {eccezione.strumento}.{eccezione.campo}",)
    return ()
