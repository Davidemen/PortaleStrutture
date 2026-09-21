"""probe / read_units / autodetect_base_url — docs/integrations/MIDAS.md §1."""
import httpx
import pytest

from strutture.integrations.midas import MidasClient, MidasError, probe, read_units
from strutture.integrations.midas.version import autodetect_base_url

from .conftest import load_fixture, make_transport

BASE_URL = "https://moa-engineers.midasit.com:443/gen"
FAKE_KEY = "FAKEKEY"


@pytest.mark.unit
def test_probe_returns_version_info() -> None:
    client = MidasClient(BASE_URL, FAKE_KEY, transport=make_transport({"/config/ver": load_fixture("midas_version.json")}))
    info = probe(client)
    assert info.product == "gen"
    assert info.name == "midas Gen NX"
    assert info.version == "1.6.6"


@pytest.mark.unit
def test_probe_detects_civil_from_name() -> None:
    client = MidasClient(
        BASE_URL, FAKE_KEY, transport=make_transport({"/config/ver": {"VER": {"NAME": "midas CIVIL NX", "VERSION": "1.0"}}})
    )
    assert probe(client).product == "civil"


@pytest.mark.unit
def test_probe_raises_bad_response_on_unexpected_shape() -> None:
    client = MidasClient(BASE_URL, FAKE_KEY, transport=make_transport({"/config/ver": {"unexpected": True}}))
    with pytest.raises(MidasError) as exc_info:
        probe(client)
    assert exc_info.value.kind == "bad_response"


@pytest.mark.unit
def test_read_units_returns_force_and_dist() -> None:
    client = MidasClient(BASE_URL, FAKE_KEY, transport=make_transport({"/db/UNIT": load_fixture("midas_unit.json")}))
    assert read_units(client) == ("KN", "M")


@pytest.mark.unit
def test_read_units_raises_bad_response_when_missing() -> None:
    client = MidasClient(BASE_URL, FAKE_KEY, transport=make_transport({"/db/UNIT": {"UNIT": {}}}))
    with pytest.raises(MidasError) as exc_info:
        read_units(client)
    assert exc_info.value.kind == "bad_response"


@pytest.mark.unit
def test_read_units_raises_bad_response_when_force_or_dist_is_blank() -> None:
    client = MidasClient(BASE_URL, FAKE_KEY, transport=make_transport({"/db/UNIT": {"UNIT": {"1": {"FORCE": "", "DIST": "M"}}}}))
    with pytest.raises(MidasError) as exc_info:
        read_units(client)
    assert exc_info.value.kind == "bad_response"


@pytest.mark.unit
def test_autodetect_tries_relays_until_one_answers() -> None:
    tried: list[str] = []

    def factory(base_url: str) -> MidasClient:
        tried.append(base_url)
        if "moa-engineers-kr" in base_url:
            return MidasClient(base_url, FAKE_KEY, transport=make_transport({"/config/ver": load_fixture("midas_version.json")}))
        return MidasClient(
            base_url,
            FAKE_KEY,
            transport=make_transport({"/config/ver": lambda r: httpx.Response(401, json={"message": "no"})}),
        )

    base_url, client, info = autodetect_base_url(factory, "gen")
    assert "moa-engineers-kr" in base_url
    assert info.name == "midas Gen NX"
    assert tried[-1] == base_url  # stopped once a relay answered
    assert probe(client).name == "midas Gen NX"


@pytest.mark.unit
def test_autodetect_raises_last_error_when_no_relay_answers() -> None:
    def factory(base_url: str) -> MidasClient:
        return MidasClient(base_url, FAKE_KEY, transport=make_transport({"/config/ver": lambda r: httpx.Response(401, json={})}))

    with pytest.raises(MidasError) as exc_info:
        autodetect_base_url(factory, "civil")
    assert exc_info.value.kind == "auth"
