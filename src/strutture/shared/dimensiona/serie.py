"""Studio di sensibilità (WORKBENCH_SPEC §24): how every check reacts to one input over a range,
evenly spaced, no rounding step — a study, not a search for one value."""
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from strutture.shared.tool import Tool

from .esecuzione import checks_di, esegui
from .sfruttamento import eta as eta_di
from .sfruttamento import impara_orientamenti

MAX_PUNTI = 41


@dataclass(frozen=True)
class VoceSerie:
    nome: str
    clausola: str
    eta: tuple[float | None, ...]
    esito: tuple[bool | None, ...]


@dataclass(frozen=True)
class Serie:
    valori: tuple[float, ...]
    verifiche: tuple[VoceSerie, ...]
    errori: tuple[dict[str, Any], ...]
    verifiche_solo_esito: tuple[str, ...]
    completa: bool


def punti_equispaziati(da: float, a: float, punti: int) -> tuple[float, ...]:
    if punti < 2:
        return (da,)
    passo = (a - da) / (punti - 1)
    return tuple(da + i * passo for i in range(punti))


def calcola_serie(
    tool: Tool, inputs: dict[str, Any], campo: str, da: float, a: float, punti: int, *, tempo_max_s: float = 10.0,
) -> Serie:
    valori = punti_equispaziati(da, a, punti)
    scadenza = time.monotonic() + tempo_max_s
    riporti: list[tuple[float, dict[str, Any]]] = []
    completa = True
    for valore in valori:
        if time.monotonic() >= scadenza:
            completa = False
            break
        riporti.append((valore, esegui(tool, inputs, campo, Decimal(str(valore)))))
    orientamenti = impara_orientamenti(tuple(checks_di(r) for _, r in riporti if r.get("ok")))
    verifiche = _serie_verifiche(riporti, orientamenti)
    errori = tuple(
        {"valore": v, "messaggio": "; ".join(r.get("errors", ())) or "Ingresso non valido"}
        for v, r in riporti if not r.get("ok")
    )
    # `orientamenti` (impara_orientamenti) only holds an entry for a check NAME once it has seen at
    # least one sample with a ratio: a check with NO ratio anywhere (no value/limit at all, ca-
    # pilastro/ca-trave's own outcome-only checks) never becomes a key there at all, so filtering
    # `orientamenti.items()` alone silently drops it from `verifiche_solo_esito`. `verifiche` (built
    # from every check NAME actually seen, `_serie_verifiche`'s own `nomi`) is the right universe.
    solo_esito = tuple(v.nome for v in verifiche if orientamenti.get(v.nome) is None)
    valori_calcolati = tuple(v for v, _ in riporti)
    return Serie(valori=valori_calcolati, verifiche=verifiche, errori=errori, verifiche_solo_esito=solo_esito, completa=completa)


def _serie_verifiche(riporti: list[tuple[float, dict[str, Any]]], orientamenti: dict) -> tuple[VoceSerie, ...]:
    nomi: dict[str, str] = {}
    for _, report in riporti:
        if report.get("ok"):
            for check in checks_di(report):
                nomi.setdefault(check.name, check.clause)
    voci = []
    for nome, clausola in nomi.items():
        orientamento = orientamenti.get(nome)
        eta_serie: list[float | None] = []
        esito_serie: list[bool | None] = []
        for _, report in riporti:
            check = _trova(report, nome)
            if check is None:
                eta_serie.append(None)
                esito_serie.append(None)
            else:
                eta_serie.append(eta_di(check, orientamento))
                esito_serie.append(check.passed)
        voci.append(VoceSerie(nome=nome, clausola=clausola, eta=tuple(eta_serie), esito=tuple(esito_serie)))
    return tuple(voci)


def _trova(report: dict[str, Any], nome: str):
    if not report.get("ok"):
        return None
    for check in checks_di(report):
        if check.name == nome:
            return check
    return None
