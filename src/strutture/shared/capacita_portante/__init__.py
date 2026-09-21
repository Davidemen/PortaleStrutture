"""EN 1997-1 Annex D bearing capacity (rigid rectangular/strip footing), NTC 2018 §6.4.2.1
approccio 2 (A1+M1+R3) verification. Pure functions, no I/O, no `Tool` registered here — consumed
by `fond-plinto-isolato` and `muro-sostegno` (docs/architecture-phase4.md §C).

Public API:
- `fattori`: Nq/Nc/Nγ, shape, load-inclination and base-inclination factors.
- `area_efficace` / `area_efficace_nastriforme`: Meyerhof effective area (rectangular / strip).
- `carico_limite_drenato` / `carico_limite_non_drenato`: q_lim with every factor reported.
- `verifica_drenata` / `verifica_non_drenata`: NTC 2018 §6.4.2.1 R_d vs N_Ed check.
"""
from .area_efficace import area_efficace, area_efficace_nastriforme
from .carico_limite import carico_limite_drenato, carico_limite_non_drenato
from .models import (
    AreaEfficace,
    CaricoLimiteResult,
    Condizione,
    Direzione,
    FattoriForma,
    FattoriInclinazioneBase,
    FattoriInclinazioneCarico,
    FattoriPortanza,
    VerificaCapacitaPortante,
)
from .verifica import verifica_drenata, verifica_non_drenata

__all__ = [
    "AreaEfficace",
    "CaricoLimiteResult",
    "Condizione",
    "Direzione",
    "FattoriForma",
    "FattoriInclinazioneBase",
    "FattoriInclinazioneCarico",
    "FattoriPortanza",
    "VerificaCapacitaPortante",
    "area_efficace",
    "area_efficace_nastriforme",
    "carico_limite_drenato",
    "carico_limite_non_drenato",
    "verifica_drenata",
    "verifica_non_drenata",
]
