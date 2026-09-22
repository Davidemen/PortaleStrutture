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
    avvisi_nuovi: tuple[str, ...] = ()  # warnings not present at the base run (empty = none)


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
        if self.valutazioni >= self._max or time.monotonic() >= self._scadenza:
            self.esaurita = True
            return None
        self.valutazioni += 1
        return self._valuta(valore)


def interrotta(campioni: list[Campione], verso: Literal["auto", "minimo", "massimo"], valutazioni: int) -> Risultato:
    """§23.3 point 6: report the extreme admissible sample known SO FAR in the direction actually
    being searched (the best-known bracket, "minimo" -> smallest admissible valore, "massimo" ->
    largest), not the globally lowest-η one -- an interrupted search still owes the engineer the
    closest thing to an answer in the direction they asked for, not an unrelated sample that
    happens to look safest."""
    verso_finale: Verso = "minimo" if verso != "massimo" else "massimo"
    ammissibili = [c for c in campioni if c.esito == "ammissibile"]
    migliore = (
        min(ammissibili, key=lambda c: c.valore) if verso_finale == "minimo"
        else max(ammissibili, key=lambda c: c.valore)
    ) if ammissibili else None
    return Risultato(
        esito="interrotta", verso=verso_finale,
        valore=migliore.valore if migliore else None, affidabile=False,
        motivi=("Ricerca interrotta: limite di valutazioni o di tempo raggiunto",),
        campioni=tuple(campioni), valutazioni=valutazioni,
    )
