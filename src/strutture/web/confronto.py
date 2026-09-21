"""Comparison of one tool run in its two modes: code-standard (default) vs Excel (`legacy_compat`).

Functions over already-serialised `Report` dicts: which output leaves differ, by how much, which
checks change outcome, and which register entries are responsible. Two sources of responsibility,
merged: the register's own `uscite` (an entry covers a path when one of its `uscite` equals it or
is a prefix of it, row indices stripped: `righe[3].eta` is covered by `righe.eta` and by `righe`),
and — exact for the CURRENT inputs — `attribuisci_per_singola_correzione`: the tool is re-run in
standard mode with ONE correction at a time switched to the spreadsheet's behaviour
(`shared.divergences.marker.solo`); every output that moves is that correction's doing."""
import math
import re
import time
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from typing import Any

from strutture.shared.divergences.marker import solo
from strutture.shared.divergences.models import Divergence

MAX_DIFFERENZE = 200  # a many-rows table can differ in thousands of cells: the list is capped, the total is not
REL_TOL = 1e-9
ABS_TOL = 1e-12
# not results: sketch geometry follows the numbers, and `legacy_compat` is the mode flag echoed back
_IGNORED_KEYS = frozenset({"schizzo", "legacy_compat"})
_ROW_INDEX = re.compile(r"\[\d+\]")
_MISSING = object()
BUDGET_ATTRIBUZIONE_S = 3.0  # total time allowed for the one-correction-at-a-time runs of one request


@dataclass(frozen=True)
class Attribuzione:
    """Outcome of the one-correction-at-a-time runs: exact paths (row indices kept) -> ids."""

    per_percorso: dict[str, tuple[str, ...]]
    valutate: int
    completa: bool  # False when the time budget ran out before every correction was tried
    non_valutabili: tuple[str, ...]  # corrections that cannot run on their own (the run failed)


NESSUNA_ATTRIBUZIONE = Attribuzione(per_percorso={}, valutate=0, completa=True, non_valutabili=())


def attribuisci_per_singola_correzione(
    esegui: Callable[[], dict[str, Any]], standard: dict[str, Any], ids: Iterable[str], *,
    budget_s: float = BUDGET_ATTRIBUZIONE_S, orologio: Callable[[], float] = time.monotonic,
) -> Attribuzione:
    """Re-run `esegui` (the tool in STANDARD mode, returning a serialised Report) once per id with
    only that correction switched to the spreadsheet's behaviour; every output leaf that moves away
    from `standard` is attributed to it. A run that fails is reported, never raised: some
    corrections only make sense together (a unit conversion and its inverse)."""
    per_percorso: dict[str, tuple[str, ...]] = {}
    non_valutabili: list[str] = []
    valutate = 0
    inizio = orologio()
    ordinati = sorted(ids)
    for divergence_id in ordinati:
        if orologio() - inizio > budget_s:
            break
        valutate += 1
        try:
            with solo((divergence_id,)):
                esito = esegui()
        except Exception:  # noqa: BLE001 - an inconsistent single-correction state is expected, not a bug
            non_valutabili.append(divergence_id)
            continue
        if not isinstance(esito.get("data"), dict):
            non_valutabili.append(divergence_id)
            continue
        for differenza in _differenze(standard.get("data"), esito["data"], ""):
            percorso = differenza["percorso"]
            per_percorso = {**per_percorso, percorso: (*per_percorso.get(percorso, ()), divergence_id)}
    return Attribuzione(per_percorso, valutate, valutate == len(ordinati), tuple(non_valutabili))


def confronta(standard: dict[str, Any], excel: dict[str, Any], tool_name: str, register: tuple[Divergence, ...],
              attribuzione: Attribuzione = NESSUNA_ATTRIBUZIONE) -> dict[str, Any]:
    """Differences between the two runs. `confrontabile` is False when either run has no data."""
    data_standard, data_excel = standard.get("data"), excel.get("data")
    confrontabile = isinstance(data_standard, dict) and isinstance(data_excel, dict)
    uscite = _uscite_per_divergenza(tool_name, register)

    def responsabili(percorso: str) -> list[str]:
        return sorted({*_responsabili(percorso, uscite), *attribuzione.per_percorso.get(percorso, ())})

    tutte = list(_differenze(data_standard, data_excel, "")) if confrontabile else []
    return {
        "confrontabile": confrontabile,
        "differenze": [{**d, "divergenze": responsabili(d["percorso"])} for d in tutte[:MAX_DIFFERENZE]],
        "totale_differenze": len(tutte),
        "verifiche": _verifiche(standard.get("checks") or [], excel.get("checks") or []),
        "divergenze_coinvolte": sorted({i for d in tutte for i in responsabili(d["percorso"])}),
        "attribuzione": {
            "correzioni_valutate": attribuzione.valutate,
            "completa": attribuzione.completa,
            "non_valutabili": list(attribuzione.non_valutabili),
        },
    }


def _differenze(standard: Any, excel: Any, percorso: str) -> Iterator[dict[str, Any]]:
    if isinstance(standard, dict) or isinstance(excel, dict):
        yield from _differenze_dict(standard if isinstance(standard, dict) else {}, excel if isinstance(excel, dict) else {}, percorso)
    elif isinstance(standard, list) or isinstance(excel, list):
        yield from _differenze_lista(standard if isinstance(standard, list) else [], excel if isinstance(excel, list) else [], percorso)
    else:
        # a key absent in one mode is the same as an explicit null there
        a, b = (None if standard is _MISSING else standard), (None if excel is _MISSING else excel)
        if not _uguali(a, b):
            yield _foglia(percorso, a, b)


def _differenze_dict(standard: dict[str, Any], excel: dict[str, Any], percorso: str) -> Iterator[dict[str, Any]]:
    for chiave in dict.fromkeys((*standard, *excel)):  # union, first-seen order
        if chiave in _IGNORED_KEYS:
            continue
        figlio = f"{percorso}.{chiave}" if percorso else chiave
        yield from _differenze(standard.get(chiave, _MISSING), excel.get(chiave, _MISSING), figlio)


def _differenze_lista(standard: list[Any], excel: list[Any], percorso: str) -> Iterator[dict[str, Any]]:
    for indice in range(max(len(standard), len(excel))):
        a = standard[indice] if indice < len(standard) else _MISSING
        b = excel[indice] if indice < len(excel) else _MISSING
        yield from _differenze(a, b, f"{percorso}[{indice}]")


def _numero(valore: Any) -> bool:
    return isinstance(valore, (int, float)) and not isinstance(valore, bool)


def _uguali(a: Any, b: Any) -> bool:
    if _numero(a) and _numero(b):
        return math.isclose(a, b, rel_tol=REL_TOL, abs_tol=ABS_TOL)
    return a is b or a == b


def _foglia(percorso: str, standard: Any, excel: Any) -> dict[str, Any]:
    entrambi_numeri = _numero(standard) and _numero(excel)
    delta = standard - excel if entrambi_numeri else None
    delta_rel = delta / abs(excel) if entrambi_numeri and excel != 0 else None
    return {
        "percorso": percorso,
        "standard": standard,
        "excel": excel,
        "delta": delta,
        "delta_rel": delta_rel,
    }


def _uscite_per_divergenza(tool_name: str, register: tuple[Divergence, ...]) -> dict[str, tuple[str, ...]]:
    return {d.id: d.uscite for d in register if tool_name in d.strumenti and d.uscite}


def _responsabili(percorso: str, uscite: dict[str, tuple[str, ...]]) -> list[str]:
    piano = _ROW_INDEX.sub("", percorso)
    return sorted(
        divergenza for divergenza, percorsi in uscite.items()
        if any(piano == u or piano.startswith(f"{u}.") for u in percorsi)
    )


def _verifiche(standard: list[dict[str, Any]], excel: list[dict[str, Any]]) -> list[dict[str, Any]]:
    per_nome_standard = {c.get("name"): c for c in standard}
    per_nome_excel = {c.get("name"): c for c in excel}
    cambiate = []
    for nome in dict.fromkeys((*per_nome_standard, *per_nome_excel)):
        a, b = _esito(per_nome_standard.get(nome)), _esito(per_nome_excel.get(nome))
        cambia_esito = a is None or b is None or a["passed"] != b["passed"]
        if cambia_esito or not _uguali(a["value"], b["value"]):
            # `cambia_esito`: the verdict itself differs (or the check exists in one mode only) — a
            # check whose utilisation merely moves is listed too, but it is a different kind of news
            cambiate.append({"nome": nome, "standard": a, "excel": b, "cambia_esito": cambia_esito})
    return cambiate


def _esito(check: dict[str, Any] | None) -> dict[str, Any] | None:
    return None if check is None else {"passed": check.get("passed"), "value": check.get("value")}
