"""Shared types for a search's grid samples (WORKBENCH_SPEC §23.3): the per-point verdict a `valuta`
callable returns, and the `Sessione` evaluation budget (max evaluations + wall clock, §23.3 point 6)."""
import time
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

CampioneEsito = Literal["ammissibile", "non_ammissibile", "errore"]
Verso = Literal["minimo", "massimo"]
EsitoRicerca = Literal["trovato", "estremo_sufficiente", "nessun_valore", "interrotta", "limite_validita"]


@dataclass(frozen=True)
class Campione:
    valore: Decimal
    esito: CampioneEsito
    eta_max: float | None = None
    messaggio: str = ""
    avviso_nuovo: str = ""  # a warning not present at the base run (empty = none)


Valuta = Callable[[Decimal], Campione]


@dataclass(frozen=True)
class Risultato:
    esito: EsitoRicerca
    verso: Verso
    valore: Decimal | None
    affidabile: bool
    motivi: tuple[str, ...]
    campioni: tuple[Campione, ...]
    valutazioni: int


def cat(campione: Campione) -> str:
    return {"ammissibile": "A", "non_ammissibile": "N", "errore": "E"}[campione.esito]


class Sessione:
    """Evaluation budget shared across sampling, bisection and confirmation."""

    def __init__(self, valuta: Valuta, max_valutazioni: int, scadenza: float) -> None:
        self._valuta, self._max, self._scadenza = valuta, max_valutazioni, scadenza
        self.valutazioni = 0
        self.esaurita = False

    def prova(self, valore: Decimal) -> Campione | None:
        if self.valutazioni >= self._max or time.monotonic() > self._scadenza:
            self.esaurita = True
            return None
        self.valutazioni += 1
        return self._valuta(valore)


def interrotta(campioni: list[Campione], verso: Literal["auto", "minimo", "massimo"], valutazioni: int) -> Risultato:
    migliore = min((c for c in campioni if c.esito == "ammissibile"), key=lambda c: c.eta_max or 0, default=None)
    return Risultato(
        esito="interrotta", verso="minimo" if verso != "massimo" else "massimo",
        valore=migliore.valore if migliore else None, affidabile=False,
        motivi=("Ricerca interrotta: limite di valutazioni o di tempo raggiunto",),
        campioni=tuple(campioni), valutazioni=valutazioni,
    )
