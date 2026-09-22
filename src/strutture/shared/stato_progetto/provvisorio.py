"""§25.2: an element is "provvisorio" when its tool has unapproved register entries in the branch
that its mode actually runs. `RESPINTO_RENDE_PROVVISORIO` records the owner's decision 21 (2026-09-22):
a rejected entry still counts, because standard mode keeps applying it until an agent adapts the code."""
from dataclasses import dataclass
from typing import Literal

RESPINTO_RENDE_PROVVISORIO = True
Modalita = Literal["standard", "excel"]


@dataclass(frozen=True)
class Correzioni:
    da_confermare: int
    respinto: int
    ramo_nessuno: int
    da_verificare: int


@dataclass(frozen=True)
class StatoProvvisorio:
    provvisorio: bool
    correzioni: Correzioni


def stato_provvisorio(voce_riepilogo: dict | None, modalita: Modalita) -> StatoProvvisorio:
    """`voce_riepilogo` is one value of `riepilogo_per_strumento(...)` (or `None`: no register entry
    at all for the tool, so it is never provvisorio)."""
    if voce_riepilogo is None:
        return StatoProvvisorio(False, Correzioni(0, 0, 0, 0))
    # `voce_riepilogo`'s `da_confermare`/`ramo_nessuno` here must already exclude `tipo ==
    # "da_verificare"` entries -- a dubbio never counts as a correction (§25.2). The caller passes
    # `riepilogo_per_strumento(...)`'s own `correzioni`/`correzioni_ramo_nessuno` sub-dicts for
    # exactly this reason: this function's own flat shape/tests stay unchanged either way.
    ramo_nessuno = voce_riepilogo["ramo_nessuno"]
    correzioni = Correzioni(
        da_confermare=voce_riepilogo["da_confermare"] if modalita == "standard" else ramo_nessuno["da_confermare"],
        respinto=voce_riepilogo["respinto"] if modalita == "standard" else ramo_nessuno["respinto"],
        ramo_nessuno=ramo_nessuno["approvato"] + ramo_nessuno["da_confermare"] + ramo_nessuno["respinto"],
        da_verificare=voce_riepilogo["da_verificare"],
    )
    provvisorio = correzioni.da_confermare > 0 or (RESPINTO_RENDE_PROVVISORIO and correzioni.respinto > 0)
    return StatoProvvisorio(provvisorio, correzioni)
