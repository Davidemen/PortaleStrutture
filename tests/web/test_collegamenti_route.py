"""GET /api/tools/collegamenti: the link registry the UI's "Usa in…" is built from."""
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_collegamenti_lists_keys_with_both_ends_and_per_tool_summaries(client: TestClient) -> None:
    from strutture.web.app import create_app

    real = TestClient(create_app())  # the packaged tools: the fake ones of `client` declare no links
    body = real.get("/api/tools/collegamenti").json()
    ag = body["chiavi"]["sito.ag_g"]
    assert {"strumento": "sisma-parametri-sito", "percorso": "ag_g", "ingresso": True} in ag["fornitori"]
    assert {"strumento": "muro-sostegno", "campo": "ag_g"} in ag["consumatori"]
    sito = body["per_strumento"]["sisma-parametri-sito"]
    assert "sito.ag_g" in sito["fornisce"]
    assert set(sito["usa_in"]) >= {"muro-sostegno", "fond-trave-collegamento"}
    muro = body["per_strumento"]["muro-sostegno"]
    assert muro["accetta"]["ag_g"] == "sito.ag_g"


def test_collegamenti_of_tools_without_links_is_empty(client: TestClient) -> None:
    body = client.get("/api/tools/collegamenti").json()
    assert body["chiavi"] == {}
    assert body["per_strumento"] == {
        "fake-sum": {"fornisce": [], "accetta": {}, "usa_in": []},
        "fake-flag": {"fornisce": [], "accetta": {}, "usa_in": []},
        "fake-verifica": {"fornisce": [], "accetta": {}, "usa_in": []},
    }
