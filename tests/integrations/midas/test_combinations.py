"""read_combinations — the six LCOM-* endpoints, docs/integrations/MIDAS.md §1/§3.

Assumption (not verified against a live instance, see docs/VERIFICA_MIDAS.md): a classification with
no combinations answers 200 with an empty object, not a 404 — every fixture below supplies all six
endpoints for that reason."""
import pytest

from strutture.integrations.midas import MidasClient, read_combinations

from .conftest import load_fixture, make_transport

BASE_URL = "https://moa-engineers.midasit.com:443/gen"
FAKE_KEY = "FAKEKEY"

_EMPTY_ENDPOINTS = {
    "/db/LCOM-CONC": {"LCOM-CONC": {}},
    "/db/LCOM-STEEL": {"LCOM-STEEL": {}},
    "/db/LCOM-SRC": {"LCOM-SRC": {}},
    "/db/LCOM-STLCOMP": {"LCOM-STLCOMP": {}},
    "/db/LCOM-SEISMIC": {"LCOM-SEISMIC": {}},
}


@pytest.mark.unit
def test_reads_general_combinations_with_cb_suffix() -> None:
    routes = {"/db/LCOM-GEN": load_fixture("midas_lcom_gen.json"), **_EMPTY_ENDPOINTS}
    client = MidasClient(BASE_URL, FAKE_KEY, transport=make_transport(routes))
    combos = read_combinations(client)
    slu1 = next(c for c in combos if c.name == "SLU1")
    assert slu1.table_name == "SLU1(CB)"
    assert slu1.classification == "GEN"
    assert slu1.active == "ACTIVE"
    assert slu1.n_terms == 2


@pytest.mark.unit
def test_empty_classifications_contribute_nothing() -> None:
    routes = {"/db/LCOM-GEN": load_fixture("midas_lcom_gen.json"), **_EMPTY_ENDPOINTS}
    client = MidasClient(BASE_URL, FAKE_KEY, transport=make_transport(routes))
    combos = read_combinations(client)
    assert len(combos) == 2  # only the two general combinations from the fixture


@pytest.mark.unit
def test_classification_specific_suffixes() -> None:
    routes = {
        "/db/LCOM-GEN": {"LCOM-GEN": {}},
        "/db/LCOM-CONC": {"LCOM-CONC": {"1": {"NAME": "SLU_C1", "ACTIVE": "STRENGTH", "DESC": "", "vCOMB": []}}},
        "/db/LCOM-STEEL": {"LCOM-STEEL": {"1": {"NAME": "SLU_S1", "ACTIVE": "SERVICE", "DESC": "", "vCOMB": []}}},
        "/db/LCOM-SRC": {"LCOM-SRC": {}},
        "/db/LCOM-STLCOMP": {"LCOM-STLCOMP": {}},
        "/db/LCOM-SEISMIC": {"LCOM-SEISMIC": {}},
    }
    client = MidasClient(BASE_URL, FAKE_KEY, transport=make_transport(routes))
    combos = read_combinations(client)
    by_name = {c.name: c for c in combos}
    assert by_name["SLU_C1"].table_name == "SLU_C1(CBC)"
    assert by_name["SLU_S1"].table_name == "SLU_S1(CBS)"
