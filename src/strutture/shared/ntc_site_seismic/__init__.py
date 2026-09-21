"""Single implementation of the NTC 2018 hazard/site chain (§2.4.3, §3.2), shared by every tool
that needs Cu/VR/TR/Ss/Cc/ST/S/TB/TC/TD (today duplicated across `sisma` and `muro-sostegno`).
Pure functions + frozen result models only; no `Tool` is registered here."""
from .amplificazione import amplificazione
from .classe_uso import coefficiente_uso
from .models import (
    AmplificazioneResult,
    CategoriaSottosuolo,
    CategoriaTopografica,
    ClasseUso,
    PeriodiRitornoResult,
    PeriodiSpettroResult,
    StatoLimite,
    VitaRiferimentoResult,
)
from .periodi_spettro import periodi_spettro
from .periodo_ritorno import periodi_ritorno, periodo_ritorno
from .stratigrafia import coefficiente_correzione_cc, fattore_amplificazione_ss
from .topografia import fattore_topografico_st
from .vita_riferimento import vita_riferimento

__all__ = [
    "AmplificazioneResult",
    "CategoriaSottosuolo",
    "CategoriaTopografica",
    "ClasseUso",
    "PeriodiRitornoResult",
    "PeriodiSpettroResult",
    "StatoLimite",
    "VitaRiferimentoResult",
    "amplificazione",
    "coefficiente_correzione_cc",
    "coefficiente_uso",
    "fattore_amplificazione_ss",
    "fattore_topografico_st",
    "periodi_ritorno",
    "periodi_spettro",
    "periodo_ritorno",
    "vita_riferimento",
]
