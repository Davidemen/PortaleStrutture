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
    messaggi_ciclo: Mapping[str, str] | None = None,
) -> StatoPropagato:
    """§25.1: one motivo per DIRECT provider (`archi[elemento_id]`), not one per every marked node
    reached anywhere in its subtree -- "Apri l'origine" opens the DIRECT provider, so that is the
    identity every motivo must carry. The message is the farthest-upstream own reason found along
    that direct provider's own branch (breadth-first within the branch, with its own visited set
    and the shared depth cap `PROFONDITA_MAX_ORIGINI`)."""
    motivi_ricalcolo: list[MotivoOrigine] = []
    motivi_provvisorio: list[dict] = []
    rinviato = False
    for diretto in archi.get(elemento_id, ()):
        raggiunto, branch_rinviato = _esplora_ramo(elemento_id, diretto, archi)
        rinviato = rinviato or branch_rinviato
        piu_lontano = None  # (profondita, OwnState) of the deepest own reason found on this branch
        provvisorio_visto = None  # (causa, nodo_id, strumento) of the node ACTUALLY responsible --
        # never assumed to be `diretto` itself: `diretto`'s own corrections can be approved while a
        # node further upstream on the same branch is the real (still unapproved/excel) cause.
        for nodo_id, profondita, strumento in raggiunto:
            proprio = stato_proprio(nodo_id)
            if proprio.da_ricalcolare and (piu_lontano is None or profondita > piu_lontano[0]):
                piu_lontano = (profondita, proprio)
            if provvisorio_visto is None:
                if proprio.provvisorio:
                    provvisorio_visto = ("origine_provvisoria", nodo_id, strumento)
                elif proprio.excel:
                    provvisorio_visto = ("origine_excel", nodo_id, strumento)
        if piu_lontano is not None:
            motivi_ricalcolo.append(
                MotivoOrigine(diretto.elemento_id, diretto.strumento, "origine_da_ricalcolare", piu_lontano[1].messaggio)
            )
        if provvisorio_visto is not None:
            causa, nodo_reale_id, nodo_reale_strumento = provvisorio_visto
            voce = {"elemento_id": diretto.elemento_id, "strumento": diretto.strumento, "causa": causa}
            # Only surface "a monte" fields when the real cause is NOT the direct provider itself --
            # keeps the payload/message identical to before for the (common) direct-cause case.
            if nodo_reale_id != diretto.elemento_id:
                voce["causa_elemento_id"] = nodo_reale_id
                voce["causa_strumento"] = nodo_reale_strumento
            motivi_provvisorio.append(voce)
    if rinviato:
        motivi_ricalcolo.append(MotivoOrigine("", "", "controllo_rinviato", "Catena di origini più lunga di 10 passaggi: controllo interrotto"))
    if elemento_id in ids_in_ciclo:
        # §25.1: name the actual cycle path ("<sigla> → … → <sigla>"), not just that one exists --
        # `messaggi_ciclo` is precomputed by the caller (`web/routes/progetti_stato.py`, which has
        # the tool siglas `propaga` itself never sees) from `cicli.cicli_componenti()`.
        messaggio = (messaggi_ciclo or {}).get(elemento_id, "Le origini formano un ciclo")
        motivi_ricalcolo.append(MotivoOrigine("", "", "ciclo_origini", messaggio))
    return StatoPropagato(
        da_ricalcolare_per_origine=any(m.causa == "origine_da_ricalcolare" for m in motivi_ricalcolo),
        motivi_ricalcolo=tuple(motivi_ricalcolo),
        provvisorio_origine=bool(motivi_provvisorio),
        motivi_provvisorio=tuple(motivi_provvisorio),
    )


def _esplora_ramo(
    radice: str, diretto: Arco, archi: Mapping[str, tuple[Arco, ...]],
) -> tuple[list[tuple[str, int, str]], bool]:
    """Breadth-first from one direct provider, own visited set (bounds a cycle local to this
    branch) starting at `{radice, diretto.elemento_id}`. Returns `(nodo_id, profondita, strumento)`
    for every node reached (itself included, `profondita=1`, `strumento` from the edge that reached
    it) plus whether the depth cap was hit -- `strumento` lets the caller name the ACTUAL node
    responsible for a "provvisorio"/excel state when it is not `diretto` itself."""
    visitati = {radice, diretto.elemento_id}
    raggiunto = [(diretto.elemento_id, 1, diretto.strumento)]
    coda: list[tuple[Arco, int]] = [(diretto, 1)]
    rinviato = False
    while coda:
        arco, profondita = coda.pop(0)
        if profondita > PROFONDITA_MAX_ORIGINI:
            # A node exactly AT the cap with no further providers is a genuine dead end, not a
            # cutoff -- only flag "rinviato" when there really is more beyond the cap left unvisited
            # (off-by-one found in review: a chain of EXACTLY 11 archi was marked rinviato even
            # though the last node had nothing left to explore).
            if archi.get(arco.elemento_id, ()):
                rinviato = True
            continue
        for prossimo in archi.get(arco.elemento_id, ()):
            if prossimo.elemento_id not in visitati:
                visitati.add(prossimo.elemento_id)
                raggiunto.append((prossimo.elemento_id, profondita + 1, prossimo.strumento))
                coda.append((prossimo, profondita + 1))
    return raggiunto, rinviato


# `cicli`/`cicli_componenti` moved to `stato_progetto/cicli.py` (rule 12: this module was 202
# lines). Re-exported here since `web/routes/progetti_stato.py` and every existing test import
# them from `propagazione` -- avoids touching every caller for a pure house-move.
from strutture.shared.stato_progetto.cicli import cicli, cicli_componenti  # noqa: F401
