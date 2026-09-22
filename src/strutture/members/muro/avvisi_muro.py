"""Warnings that are not tied to the optional bearing-capacity block, plus the mapping from
warning text to the input field it is about — split out of `tool.py`, regola dura 12 dei moduli
piccoli.
"""
from .capacita_portante_muro import (
    AVVISO_CAPACITA_PORTANTE,
    AVVISO_CAPACITA_PORTANTE_SISMICA,
    AVVISO_TERRENO_IGNORATO_LEGACY,
)
from .models import MuroSostegnoInput

AVVISO_SCORRIMENTO_NON_DRENATA = (
    "Verifica a scorrimento: con il terreno di fondazione in condizione non drenata la resistenza sul piano di "
    "posa (adesione c_u) non è modellata; il calcolo usa l'angolo di attrito del rinterro."
)


def avvisi_scorrimento(inputs: MuroSostegnoInput) -> tuple[str, ...]:
    if inputs.legacy_compat or inputs.terreno_condizione != "non_drenata":
        return ()
    return (AVVISO_SCORRIMENTO_NON_DRENATA,)


_CAMPO_PER_AVVISO = {
    AVVISO_CAPACITA_PORTANTE: "terreno_condizione",
    AVVISO_CAPACITA_PORTANTE_SISMICA: "terreno_condizione",
    AVVISO_TERRENO_IGNORATO_LEGACY: "legacy_compat",
    AVVISO_SCORRIMENTO_NON_DRENATA: "terreno_condizione",
}


def campi_degli_avvisi(avvisi: tuple[str, ...]) -> dict[str, str]:
    """The input field each warning is about (the UI jumps to it on click)."""
    campi = {}
    for avviso in avvisi:
        if avviso in _CAMPO_PER_AVVISO:
            campi[avviso] = _CAMPO_PER_AVVISO[avviso]
        elif avviso.startswith("Profondità di posa D="):
            campi[avviso] = "terreno_profondita_posa_m"
    return campi
