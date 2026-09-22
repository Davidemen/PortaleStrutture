"""propaga/cicli: §25.1 propagation, order independence, termination on cycles, depth cap."""
import itertools

import pytest

from strutture.shared.stato_progetto.cicli import cicli_componenti
from strutture.shared.stato_progetto.propagazione import PROFONDITA_MAX_ORIGINI, Arco, OwnState, cicli, propaga


def _catena(*ids: str) -> dict[str, tuple[Arco, ...]]:
    """consumatore -> [fornitore]: ids[0] consumes ids[1], ids[1] consumes ids[2], ..."""
    archi: dict[str, tuple[Arco, ...]] = {}
    for consumatore, fornitore in itertools.pairwise(ids):
        archi[consumatore] = (Arco(fornitore, "strumento", "chiave"),)
    return archi


def _stato_di(marcati: frozenset[str], provvisori: frozenset[str] = frozenset(), excel: frozenset[str] = frozenset()):
    def stato_proprio(elemento_id: str) -> OwnState:
        return OwnState(
            da_ricalcolare=elemento_id in marcati, messaggio=f"motivo di {elemento_id}",
            provvisorio=elemento_id in provvisori, excel=elemento_id in excel,
        )
    return stato_proprio


@pytest.mark.unit
def test_chain_a_changed_marks_b_and_c():
    archi = _catena("C", "B", "A")  # C uses B uses A
    stato_proprio = _stato_di(marcati=frozenset({"B"}))  # B's own state already reflects A's change
    stato_b = propaga("B", archi, stato_proprio, frozenset())
    stato_c = propaga("C", archi, stato_proprio, frozenset())
    assert stato_b.da_ricalcolare_per_origine is False  # B is marked on its OWN state, not via propagation
    assert stato_c.da_ricalcolare_per_origine is True
    assert stato_c.motivi_ricalcolo[0].elemento_id == "B"


@pytest.mark.unit
def test_two_marked_nodes_on_the_same_branch_group_into_one_motivo_at_the_direct_provider():
    """§25.1: one motivo per DIRECT provider, not one per marked node reached -- "Apri l'origine"
    opens the direct one; the message is the farthest-upstream own reason on that branch."""
    archi = _catena("D", "C", "B", "A")  # D uses C uses B uses A
    stato_proprio = _stato_di(marcati=frozenset({"B", "C"}))  # both B and C already reflect A's change
    stato_d = propaga("D", archi, stato_proprio, frozenset())
    assert len(stato_d.motivi_ricalcolo) == 1
    motivo = stato_d.motivi_ricalcolo[0]
    assert motivo.elemento_id == "C"  # D's DIRECT provider, not the farther B
    assert motivo.messaggio == "motivo di B"  # the farthest-upstream reason found on this branch


@pytest.mark.unit
def test_two_direct_providers_each_get_their_own_motivo():
    archi = {"C": (Arco("A", "s", "k"), Arco("B", "s", "k"))}
    stato_proprio = _stato_di(marcati=frozenset({"A", "B"}))
    stato_c = propaga("C", archi, stato_proprio, frozenset())
    assert {m.elemento_id for m in stato_c.motivi_ricalcolo} == {"A", "B"}


@pytest.mark.unit
def test_provvisorio_or_excel_provider_marks_provvisorio_origine_only():
    archi = _catena("C", "B", "A")
    stato_proprio = _stato_di(marcati=frozenset(), provvisori=frozenset({"A"}))
    stato_c = propaga("C", archi, stato_proprio, frozenset())
    assert stato_c.provvisorio_origine is True
    assert stato_c.da_ricalcolare_per_origine is False


@pytest.mark.unit
def test_provvisorio_names_the_real_upstream_node_not_just_the_direct_provider():
    """Found in review: C's DIRECT provider is B (now approved, `provvisorio=False`), but A --
    further upstream on the same branch -- is still provisional. The motivo must say A is the real
    cause, not silently attribute it to B just because B is nearest."""
    archi = _catena("C", "B", "A")
    stato_proprio = _stato_di(marcati=frozenset(), provvisori=frozenset({"A"}))
    stato_c = propaga("C", archi, stato_proprio, frozenset())
    motivo = stato_c.motivi_provvisorio[0]
    assert motivo["elemento_id"] == "B"  # "Apri l'origine" still opens the DIRECT provider
    assert motivo["causa_elemento_id"] == "A"  # but the real cause is named too
    assert motivo["causa_strumento"] == "strumento"


@pytest.mark.unit
def test_provvisorio_omits_upstream_fields_when_the_direct_provider_is_the_real_cause():
    archi = _catena("C", "B", "A")
    stato_proprio = _stato_di(marcati=frozenset(), provvisori=frozenset({"B"}))
    stato_c = propaga("C", archi, stato_proprio, frozenset())
    motivo = stato_c.motivi_provvisorio[0]
    assert "causa_elemento_id" not in motivo


@pytest.mark.unit
def test_items_without_elemento_id_never_propagate():
    # an empty adjacency for a node simply gives no propagation.
    stato = propaga("X", {}, _stato_di(frozenset()), frozenset())
    assert stato.da_ricalcolare_per_origine is False
    assert stato.provvisorio_origine is False


@pytest.mark.unit
def test_self_edge_terminates_and_is_flagged():
    archi = {"X": (Arco("X", "s", "k"),)}
    ids_ciclo = cicli(archi)
    assert "X" in ids_ciclo
    stato = propaga("X", archi, _stato_di(frozenset()), ids_ciclo)
    assert any(m.causa == "ciclo_origini" for m in stato.motivi_ricalcolo)


@pytest.mark.unit
def test_two_cycle_terminates_and_flags_both_members():
    archi = {"A": (Arco("B", "s", "k"),), "B": (Arco("A", "s", "k"),)}
    ids_ciclo = cicli(archi)
    assert ids_ciclo == frozenset({"A", "B"})
    for elemento_id in ("A", "B"):
        stato = propaga(elemento_id, archi, _stato_di(frozenset()), ids_ciclo)
        assert any(m.causa == "ciclo_origini" for m in stato.motivi_ricalcolo)


@pytest.mark.unit
def test_five_cycle_terminates_and_flags_every_member():
    ids = ["A", "B", "C", "D", "E"]
    archi = {ids[i]: (Arco(ids[(i + 1) % 5], "s", "k"),) for i in range(5)}
    ids_ciclo = cicli(archi)
    assert ids_ciclo == frozenset(ids)
    for elemento_id in ids:
        stato = propaga(elemento_id, archi, _stato_di(frozenset()), ids_ciclo)
        assert any(m.causa == "ciclo_origini" for m in stato.motivi_ricalcolo)


@pytest.mark.unit
def test_chain_longer_than_depth_cap_gives_controllo_rinviato():
    ids = [f"E{i}" for i in range(PROFONDITA_MAX_ORIGINI + 3)]
    archi = _catena(*ids)
    stato = propaga(ids[0], archi, _stato_di(frozenset()), frozenset())
    assert any(m.causa == "controllo_rinviato" for m in stato.motivi_ricalcolo)


@pytest.mark.unit
def test_chain_of_exactly_the_depth_cap_is_not_rinviato():
    """Off-by-one found in review: a chain of EXACTLY `PROFONDITA_MAX_ORIGINI` hops from the direct
    provider ends right at the cap with nothing left to visit -- must NOT be `controllo_rinviato`."""
    ids = [f"E{i}" for i in range(PROFONDITA_MAX_ORIGINI + 1)]  # E0 -> E1 -> ... -> E10 (10 hops)
    archi = _catena(*ids)
    stato = propaga(ids[0], archi, _stato_di(frozenset()), frozenset())
    assert not any(m.causa == "controllo_rinviato" for m in stato.motivi_ricalcolo)


@pytest.mark.unit
def test_cicli_componenti_counts_distinct_cycles_not_members():
    """§25.1/§25.3: one 3-node cycle is ONE component, however many elements sit in it."""
    archi = {"A": (Arco("B", "s", "k"),), "B": (Arco("C", "s", "k"),), "C": (Arco("A", "s", "k"),)}
    componenti = cicli_componenti(archi)
    assert len(componenti) == 1
    percorso = componenti[0]
    assert percorso[0] == percorso[-1]  # closes back on itself
    assert set(percorso[:-1]) == {"A", "B", "C"}


@pytest.mark.unit
def test_cicli_componenti_counts_two_separate_cycles_as_two():
    archi = {
        "A": (Arco("B", "s", "k"),), "B": (Arco("A", "s", "k"),),
        "X": (Arco("Y", "s", "k"),), "Y": (Arco("X", "s", "k"),),
    }
    assert len(cicli_componenti(archi)) == 2


@pytest.mark.unit
def test_same_result_for_every_permutation_of_traversal_order():
    # order independence: BFS from the same node gives the same verdict regardless of dict insertion
    # order of the adjacency (Python dicts preserve insertion order, so build it two different ways).
    archi_1 = {"C": (Arco("B", "s", "k"), Arco("D", "s", "k")), "B": (Arco("A", "s", "k"),)}
    archi_2 = {"B": (Arco("A", "s", "k"),), "C": (Arco("D", "s", "k"), Arco("B", "s", "k"))}
    stato_proprio = _stato_di(marcati=frozenset({"B"}))
    r1 = propaga("C", archi_1, stato_proprio, frozenset())
    r2 = propaga("C", archi_2, stato_proprio, frozenset())
    assert r1.da_ricalcolare_per_origine == r2.da_ricalcolare_per_origine
    assert {m.elemento_id for m in r1.motivi_ricalcolo} == {m.elemento_id for m in r2.motivi_ricalcolo}
