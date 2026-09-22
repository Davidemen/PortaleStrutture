"""Wires `execute()` and `sfruttamento.py` into the pure search algorithm (`ricerca.py`, `serie.py`):
the only module in `shared/dimensiona/` that runs a tool. WORKBENCH_SPEC §23.3 point 2, §23.4."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from strutture.shared.report import Check
from strutture.shared.tool import Tool, execute

from .campioni import Campione
from .griglia import indici_campionamento
from .sfruttamento import Esito, Orientamento, impara_orientamenti, valuta_esito

N_CAMPIONI = 17


@dataclass(frozen=True)
class Valutazione:
    """One tool run at a trial value: the raw envelope plus its `Esito` (`None` when the run itself
    failed — a validity-range `errore` — or when `obiettivo`/`obiettivo_su_minimi` are not known yet)."""

    report: dict[str, Any]
    esito: Esito | None


def valutazioni_iniziali(
    tool: Tool, inputs: dict[str, Any], campo: str, griglia: tuple[Decimal, ...],
) -> dict[Decimal, dict[str, Any]]:
    """Runs the tool once at each of the initial sampling points (§23.3 point 2), before orientation
    is known. Cached by value so `valuta` (below) never re-executes these same grid points."""
    indici = indici_campionamento(len(griglia), N_CAMPIONI)
    return {griglia[i]: esegui(tool, inputs, campo, griglia[i]) for i in indici}


def impara_da_riporti(riporti: dict[Decimal, dict[str, Any]]) -> dict[str, Orientamento | None]:
    checks = tuple(checks_di(r) for r in riporti.values() if r.get("ok"))
    return impara_orientamenti(checks)


def checks_di(report: dict[str, Any]) -> tuple[Check, ...]:
    return tuple(Check(**c) for c in report.get("checks", ()))


def esegui(tool: Tool, inputs: dict[str, Any], campo: str, valore: Decimal) -> dict[str, Any]:
    return execute(tool, {**inputs, campo: float(valore)}).model_dump(mode="json")


def costruisci_valuta(
    tool: Tool, inputs: dict[str, Any], campo: str, cache_iniziale: dict[Decimal, dict[str, Any]],
    orientamenti: dict[str, Orientamento | None], obiettivo: float, obiettivo_su_minimi: bool,
    avvisi_base: tuple[str, ...],
):
    """The `Campione`-producing callable `ricerca.cerca` drives. Cache hits from the initial
    sampling are reused (same executions, not run twice); anything else is a real tool run."""
    cache: dict[Decimal, dict[str, Any]] = dict(cache_iniziale)

    def valuta(valore: Decimal) -> Campione:
        report = cache.get(valore)
        if report is None:
            report = esegui(tool, inputs, campo, valore)
            cache[valore] = report
        return _campione_da_report(valore, report, orientamenti, obiettivo, obiettivo_su_minimi, avvisi_base)

    return valuta, cache


def _campione_da_report(
    valore: Decimal, report: dict[str, Any], orientamenti: dict[str, Orientamento | None],
    obiettivo: float, obiettivo_su_minimi: bool, avvisi_base: tuple[str, ...],
) -> Campione:
    if not report.get("ok"):
        messaggio = "; ".join(report.get("errors", ())) or "Ingresso non valido"
        return Campione(valore=valore, esito="errore", messaggio=messaggio)
    esito = valuta_esito(checks_di(report), orientamenti, obiettivo, obiettivo_su_minimi)
    nuovi = tuple(w for w in report.get("warnings", ()) if w not in avvisi_base)
    return Campione(
        valore=valore, esito="ammissibile" if esito.ammissibile else "non_ammissibile",
        eta_max=esito.eta_max, avvisi_nuovi=nuovi,
    )


def esito_alla_risposta(
    valore: Decimal | None, tool: Tool, inputs: dict[str, Any], campo: str, cache: dict[Decimal, dict[str, Any]],
    orientamenti: dict[str, Orientamento | None], obiettivo: float, obiettivo_su_minimi: bool,
) -> tuple[dict[str, Any] | None, Esito | None]:
    """The full report at the found value, plus its `Esito` (governing check, `verifiche_*` lists)
    — recomputed here rather than threaded through `Campione`, which stays a thin, generic type."""
    if valore is None:
        return None, None
    report = cache.get(valore) or esegui(tool, inputs, campo, valore)
    if not report.get("ok"):
        return report, None
    return report, valuta_esito(checks_di(report), orientamenti, obiettivo, obiettivo_su_minimi)
