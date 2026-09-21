"""read_supports — /db/cons + /db/node, docs/integrations/MIDAS.md §1/§3."""
import pytest

from strutture.integrations.midas import MidasClient, read_supports

from .conftest import load_fixture, make_transport

BASE_URL = "https://moa-engineers.midasit.com:443/gen"
FAKE_KEY = "FAKEKEY"


@pytest.mark.unit
def test_reads_constrained_nodes_with_coordinates() -> None:
    routes = {"/db/cons": load_fixture("midas_cons.json"), "/db/node": load_fixture("midas_node.json")}
    client = MidasClient(BASE_URL, FAKE_KEY, transport=make_transport(routes))
    supports = read_supports(client)
    assert {s.nodo for s in supports} == {12, 13}
    node13 = next(s for s in supports if s.nodo == 13)
    assert node13.x_m == pytest.approx(4.0)
    assert node13.vincoli == "111111"


@pytest.mark.unit
def test_a_constrained_node_missing_coordinates_is_skipped() -> None:
    routes = {
        "/db/cons": {"CONS": {"12": {"CONSTRAINT": "111111"}, "99": {"CONSTRAINT": "111111"}}},
        "/db/node": {"NODE": {"12": {"X": 0.0, "Y": 0.0, "Z": 0.0}}},
    }
    client = MidasClient(BASE_URL, FAKE_KEY, transport=make_transport(routes))
    supports = read_supports(client)
    assert {s.nodo for s in supports} == {12}
