"""§25.1 propagation along the usage chain and §25.2's "provvisorio per origine" (owner's decision 22:
"da ricalcolare" and "provvisorio" propagate). Pure: the route builds the graph and a callable for the
own state of one element (so this is tested without the web layer)."""
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal

PROFONDITA_MAX_ORIGINI = 10


@dataclass(frozen=True)
class Arco:
    elemento_id: str  # the provider this edge points to
    strumento: str
    chiave: str


@dataclass(frozen=True)
class MotivoOrigine:
    elemento_id: str
    strumento: str
    causa: Literal["origine_da_ricalcolare", "controllo_rinviato", "ciclo_origini"]
    messaggio: str = ""


@dataclass(frozen=True)
class OwnState:
    da_ricalcolare: bool
    messaggio: str  # own reason, used as the propagated "farthest-upstream" message
    provvisorio: bool
    excel: bool


@dataclass(frozen=True)
class StatoPropagato:
    da_ricalcolare_per_origine: bool
    motivi_ricalcolo: tuple[MotivoOrigine, ...]
    provvisorio_origine: bool
    motivi_provvisorio: tuple[dict, ...]


def propaga(
    elemento_id: str,
    archi: Mapping[str, tuple[Arco, ...]],
    stato_proprio: Callable[[str], OwnState],
    ids_in_ciclo: frozenset[str],
) -> StatoPropagato:
    """Breadth-first from `elemento_id` along provider edges, with a visited set (terminates on any
    cycle) and a depth cap (`PROFONDITA_MAX_ORIGINI`, not itself a marker)."""
    visitati = {elemento_id}
    coda: list[tuple[Arco, int]] = [(arco, 1) for arco in archi.get(elemento_id, ())]
    motivi_ricalcolo: list[MotivoOrigine] = []
    motivi_provvisorio: list[dict] = []
    rinviato = False
    while coda:
        arco, profondita = coda.pop(0)
        if arco.elemento_id in visitati:
            continue
        visitati.add(arco.elemento_id)
        if profondita > PROFONDITA_MAX_ORIGINI:
            rinviato = True
            continue
        proprio = stato_proprio(arco.elemento_id)
        if proprio.da_ricalcolare:
            motivi_ricalcolo.append(MotivoOrigine(arco.elemento_id, arco.strumento, "origine_da_ricalcolare", proprio.messaggio))
        if proprio.provvisorio:
            motivi_provvisorio.append({"elemento_id": arco.elemento_id, "strumento": arco.strumento, "causa": "origine_provvisoria"})
        elif proprio.excel:
            motivi_provvisorio.append({"elemento_id": arco.elemento_id, "strumento": arco.strumento, "causa": "origine_excel"})
        for prossimo in archi.get(arco.elemento_id, ()):
            if prossimo.elemento_id not in visitati:
                coda.append((prossimo, profondita + 1))
    if rinviato:
        motivi_ricalcolo.append(MotivoOrigine("", "", "controllo_rinviato", "Catena di origini più lunga di 10 passaggi: controllo interrotto"))
    if elemento_id in ids_in_ciclo:
        motivi_ricalcolo.append(MotivoOrigine("", "", "ciclo_origini", "Le origini formano un ciclo"))
    return StatoPropagato(
        da_ricalcolare_per_origine=any(m.causa == "origine_da_ricalcolare" for m in motivi_ricalcolo),
        motivi_ricalcolo=tuple(motivi_ricalcolo),
        provvisorio_origine=bool(motivi_provvisorio),
        motivi_provvisorio=tuple(motivi_provvisorio),
    )


def cicli(archi: Mapping[str, tuple[Arco, ...]]) -> frozenset[str]:
    """Ids belonging to a strongly connected component with more than one node, or a self-edge
    (Tarjan, iterative — recursion would blow the stack on a real project graph)."""
    grafo: dict[str, tuple[str, ...]] = {
        nodo: tuple(a.elemento_id for a in archi.get(nodo, ())) for nodo in _tutti_i_nodi(archi)
    }
    componenti = _tarjan(grafo)
    return frozenset(
        nodo for componente in componenti for nodo in componente
        if len(componente) > 1 or grafo.get(next(iter(componente)), ()).count(next(iter(componente))) > 0
    )


def _tutti_i_nodi(archi: Mapping[str, tuple[Arco, ...]]) -> frozenset[str]:
    nodi = set(archi.keys())
    for lista in archi.values():
        nodi.update(a.elemento_id for a in lista)
    return frozenset(nodi)


def _tarjan(grafo: Mapping[str, tuple[str, ...]]) -> tuple[frozenset[str], ...]:
    """Iterative Tarjan's SCC algorithm: order-independent over `sorted(grafo)`, no recursion."""
    index_di: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    nella_pila: set[str] = set()
    pila: list[str] = []
    componenti: list[frozenset[str]] = []
    contatore = [0]

    for radice in sorted(grafo):
        if radice in index_di:
            continue
        lavoro: list[tuple[str, int]] = [(radice, 0)]
        while lavoro:
            nodo, indice_vicino = lavoro[-1]
            if indice_vicino == 0:
                index_di[nodo] = lowlink[nodo] = contatore[0]
                contatore[0] += 1
                pila.append(nodo)
                nella_pila.add(nodo)
            vicini = grafo.get(nodo, ())
            if indice_vicino < len(vicini):
                lavoro[-1] = (nodo, indice_vicino + 1)
                vicino = vicini[indice_vicino]
                if vicino not in index_di:
                    lavoro.append((vicino, 0))
                elif vicino in nella_pila:
                    lowlink[nodo] = min(lowlink[nodo], index_di[vicino])
            else:
                lavoro.pop()
                if lavoro:
                    genitore = lavoro[-1][0]
                    lowlink[genitore] = min(lowlink[genitore], lowlink[nodo])
                if lowlink[nodo] == index_di[nodo]:
                    componente = []
                    while True:
                        cima = pila.pop()
                        nella_pila.discard(cima)
                        componente.append(cima)
                        if cima == nodo:
                            break
                    componenti.append(frozenset(componente))
    return tuple(componenti)
