"""Comparison of one tool run in its two modes: code-standard (default) vs Excel (`legacy_compat`).

Pure functions over two already-serialised `Report` dicts: which output leaves differ, by how much,
which checks change outcome, and which register entries are responsible — an entry is responsible
for a path when one of its `uscite` equals the path or is a prefix of it (row indices stripped:
`righe[3].eta` is covered by `righe.eta` and by `righe`)."""
import math
import re
from collections.abc import Iterator
from typing import Any

from strutture.shared.divergences.models import Divergence

MAX_DIFFERENZE = 200  # a many-rows table can differ in thousands of cells: the list is capped, the total is not
REL_TOL = 1e-9
ABS_TOL = 1e-12
_IGNORED_KEYS = frozenset({"schizzo"})  # sketch geometry follows the numbers; it is not a result
_ROW_INDEX = re.compile(r"\[\d+\]")
_MISSING = object()


def confronta(standard: dict[str, Any], excel: dict[str, Any], tool_name: str,
              register: tuple[Divergence, ...]) -> dict[str, Any]:
    """Differences between the two runs. `confrontabile` is False when either run has no data."""
    data_standard, data_excel = standard.get("data"), excel.get("data")
    confrontabile = isinstance(data_standard, dict) and isinstance(data_excel, dict)
    uscite = _uscite_per_divergenza(tool_name, register)
    tutte = list(_differenze(data_standard, data_excel, "")) if confrontabile else []
    differenze = [{**d, "divergenze": _responsabili(d["percorso"], uscite)} for d in tutte[:MAX_DIFFERENZE]]
    coinvolte = sorted({i for d in tutte for i in _responsabili(d["percorso"], uscite)})
    return {
        "confrontabile": confrontabile,
        "differenze": differenze,
        "totale_differenze": len(tutte),
        "verifiche": _verifiche(standard.get("checks") or [], excel.get("checks") or []),
        "divergenze_coinvolte": coinvolte,
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
        if a is None or b is None or a["passed"] != b["passed"] or not _uguali(a["value"], b["value"]):
            cambiate.append({"nome": nome, "standard": a, "excel": b})
    return cambiate


def _esito(check: dict[str, Any] | None) -> dict[str, Any] | None:
    return None if check is None else {"passed": check.get("passed"), "value": check.get("value")}
