"""Validation of `passi_per_campo`/`passi_per_tipo` that needs the tool registry (§26.2/§26.3): pure,
given the tools."""
from collections.abc import Mapping

from strutture.shared.tool import Tool

from .campi import campi_numerici
from .modelli import Impostazioni, PassoCampo
from .risolvi import passo_proposto
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


def valida_passi_per_tipo(impostazioni: Impostazioni, tools: Mapping[str, Tool]) -> tuple[str, ...]:
    """§26.3: un passo per tipo deve convertirsi nell'unità di OGNI campo di quel tipo mantenendo al
    massimo 4 decimali (`risolvi._converti`); altrimenti va respinto al salvataggio, con il campo
    nominato, non solo scoperto più tardi da GET .../passi. Un campo con la propria eccezione
    (`passi_per_campo`) non è toccato dal passo per tipo, quindi non genera conflitto qui."""
    if not impostazioni.passi_per_tipo:
        return ()
    errori: list[str] = []
    for tool in tools.values():
        for nome, schema_campo in campi_numerici(tool):
            tipo = tipo_dato(nome, schema_campo)
            if tipo is None or tipo not in impostazioni.passi_per_tipo:
                continue
            try:
                passo_proposto(impostazioni, tool.name, nome, schema_campo, tipo)
            except ValueError as errore:
                errori.append(str(errore))
    return tuple(errori)
