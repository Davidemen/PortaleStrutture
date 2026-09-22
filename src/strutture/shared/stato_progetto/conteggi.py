"""§25.3: aggregate counts for the project head, from the per-element `stato` payload the route builds."""
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Conteggi:
    elementi: int
    verificati: int
    non_verificati: int
    dati_modificati: int
    da_ricalcolare: int
    provvisori: int
    provvisori_per_origine: int
    controllo_rinviato: int
    cicli_origini: int


def conta(
    stati_elementi: Iterable[str], voci_stato: Iterable[Mapping[str, Any]], numero_cicli: int = 0,
) -> Conteggi:
    """`stati_elementi`: each element's own `StatoElemento` ("verificato"/...). `voci_stato`: the
    matching `{da_ricalcolare, motivi, provvisorio, provvisorio_origine}` payloads, same order.
    `numero_cicli`: distinct cycles (§25.1: `propagazione.cicli_componenti()`'s own count), NOT the
    number of elements that sit in one -- a single 3-element cycle must show "1 ciclo", not 3."""
    stati = list(stati_elementi)
    voci = list(voci_stato)
    return Conteggi(
        elementi=len(voci),
        verificati=sum(1 for s in stati if s == "verificato"),
        non_verificati=sum(1 for s in stati if s == "non_verificato"),
        dati_modificati=sum(1 for s in stati if s == "dati_modificati"),
        da_ricalcolare=sum(1 for v in voci if v["da_ricalcolare"]),
        provvisori=sum(1 for v in voci if v["provvisorio"]),
        provvisori_per_origine=sum(1 for v in voci if v["provvisorio_origine"]),
        controllo_rinviato=sum(1 for v in voci if _con_causa(v, "controllo_rinviato")),
        cicli_origini=numero_cicli,
    )


def _con_causa(voce: Mapping[str, Any], causa: str) -> bool:
    return any(m["causa"] == causa for m in voce["motivi"])
