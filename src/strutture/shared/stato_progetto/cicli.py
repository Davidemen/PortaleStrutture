"""Cycle detection over the "Usa in..." graph (WORKBENCH_SPEC §25.1), split out of
`propagazione.py` (rule 12: modules stay <= 150 lines). Pure: takes the same `archi` mapping
`propagazione.propaga`/`web/routes/progetti_stato.py` already build, no web/storage dependency."""
from collections.abc import Mapping

from strutture.shared.stato_progetto.propagazione import Arco


def cicli_componenti(archi: Mapping[str, tuple[Arco, ...]]) -> tuple[tuple[str, ...], ...]:
    """One entry per DISTINCT cycle (strongly connected component with more than one node, or a
    self-edge -- Tarjan, iterative, recursion would blow the stack on a real project graph), not
    one per element inside it (§25.1/§25.3: `conteggi.conta`'s `numero_cicli` needs the count of
    entries here, never `sum(len(c) for c in ...)`). Each entry is an ORDERED path of ids walking
    edges from an arbitrary (deterministic: lexicographically smallest) start node back to itself,
    so a caller can render "<sigla> → … → <sigla>" (§25.1)."""
    grafo: dict[str, tuple[str, ...]] = {
        nodo: tuple(a.elemento_id for a in archi.get(nodo, ())) for nodo in _tutti_i_nodi(archi)
    }
    percorsi: list[tuple[str, ...]] = []
    for componente in _tarjan(grafo):
        if len(componente) > 1:
            percorsi.append(_percorso_ciclo(componente, grafo))
        else:
            solo = next(iter(componente))
            if solo in grafo.get(solo, ()):
                percorsi.append((solo, solo))
    return tuple(percorsi)


def _percorso_ciclo(componente: frozenset[str], grafo: Mapping[str, tuple[str, ...]]) -> tuple[str, ...]:
    """Walks edges inside `componente` from its smallest id back to itself -- every node in a
    strongly connected component has a path back to every other, so this never gets stuck."""
    inizio = min(componente)
    percorso = [inizio]
    visitati = {inizio}
    corrente = inizio
    while True:
        successivo = next(v for v in grafo.get(corrente, ()) if v in componente and (v == inizio or v not in visitati))
        percorso.append(successivo)
        if successivo == inizio:
            return tuple(percorso)
        visitati.add(successivo)
        corrente = successivo


def cicli(archi: Mapping[str, tuple[Arco, ...]]) -> frozenset[str]:
    """Ids belonging to any cycle (union of every `cicli_componenti()` path, closing node dropped)."""
    return frozenset(nodo for percorso in cicli_componenti(archi) for nodo in percorso[:-1])


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
