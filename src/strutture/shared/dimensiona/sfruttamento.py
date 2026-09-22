"""Reads a utilisation ratio from a `Check` and learns, per check NAME, whether it is a
demand/capacity check ("diretto": passed ⇔ value/limit ≤ 1) or a minimum/capacity-over-demand check
("inverso": passed ⇔ value/limit ≥ 1). WORKBENCH_SPEC §23.2. No contract change: `Check.value`/
`Check.limit` are read as they are, `detail` is never parsed."""
from dataclasses import dataclass
from typing import Literal

from strutture.shared.report import Check

Orientamento = Literal["diretto", "inverso"]


def rapporto(check: Check) -> float | None:
    """value/limit when both are set, finite, `limit != 0` and same sign; `None` otherwise (no ratio)."""
    if check.value is None or check.limit is None or check.limit == 0:
        return None
    if (check.value < 0) != (check.limit < 0):
        return None
    return check.value / check.limit


def impara_orientamenti(campioni_checks: tuple[tuple[Check, ...], ...]) -> dict[str, Orientamento | None]:
    """One pass over the initial samples (§23.3 point 2): per check name, the orientation that holds
    on every sample where the check has a ratio. `None` = outcome-only for the rest of this search
    (no ratio anywhere, contradictory samples, or every ratio sits exactly on 1)."""
    per_nome: dict[str, list[tuple[float, bool]]] = {}
    for checks in campioni_checks:
        for check in checks:
            r = rapporto(check)
            if r is not None:
                per_nome.setdefault(check.name, []).append((r, check.passed))
    return {nome: _orientamento(coppie) for nome, coppie in per_nome.items()}


def _orientamento(coppie: list[tuple[float, bool]]) -> Orientamento | None:
    if all(r == 1 for r, _ in coppie):
        return None
    diretto = all(passed == (r <= 1) for r, passed in coppie)
    inverso = all(passed == (r >= 1) for r, passed in coppie)
    if diretto and not inverso:
        return "diretto"
    if inverso and not diretto:
        return "inverso"
    return None


def eta(check: Check, orientamento: Orientamento | None) -> float | None:
    """η in the search's terms: r for "diretto", 1/r for "inverso"; `None` for outcome-only checks
    or a sample where this check has no ratio at all."""
    r = rapporto(check)
    if r is None or orientamento is None:
        return None
    return r if orientamento == "diretto" else 1 / r


@dataclass(frozen=True)
class Esito:
    """One sample's verdict against `obiettivo` (WORKBENCH_SPEC §23.2's `obiettivo_su_verifiche_minimo`)."""

    ammissibile: bool
    eta_max: float | None
    governante: tuple[str, float] | None
    incoerenze: tuple[str, ...]
    solo_esito: tuple[str, ...]
    senza_obiettivo: tuple[str, ...]


def valuta_esito(
    checks: tuple[Check, ...], orientamenti: dict[str, Orientamento | None],
    obiettivo: float, obiettivo_su_minimi: bool,
) -> Esito:
    """Admissible: `report.ok` (checked by the caller) AND every check passed AND every check whose
    target applies has η ≤ `obiettivo`. Target applies to every "diretto" check; to "inverso" checks
    only when `obiettivo_su_minimi` is true (else they count as pass/fail only, §23.2)."""
    incoerenze: list[str] = []
    solo_esito: list[str] = []
    senza_obiettivo: list[str] = []
    etas: list[tuple[str, float]] = []
    obiettivo_rispettato = True
    for check in checks:
        orientamento = orientamenti.get(check.name)
        r = rapporto(check)
        if orientamento is None:
            solo_esito.append(check.name)
            continue
        if r is not None and check.passed != (r <= 1 if orientamento == "diretto" else r >= 1):
            incoerenze.append(check.name)
        valore_eta = eta(check, orientamento)
        if valore_eta is None:
            continue
        etas.append((check.name, valore_eta))
        applica = orientamento == "diretto" or obiettivo_su_minimi
        if not applica:
            senza_obiettivo.append(check.name)
        elif valore_eta > obiettivo:
            obiettivo_rispettato = False
    governante = max(etas, key=lambda coppia: coppia[1]) if etas else None
    ammissibile = all(c.passed for c in checks) and obiettivo_rispettato
    return Esito(
        ammissibile=ammissibile, eta_max=governante[1] if governante else None, governante=governante,
        incoerenze=tuple(incoerenze), solo_esito=tuple(solo_esito), senza_obiettivo=tuple(senza_obiettivo),
    )
