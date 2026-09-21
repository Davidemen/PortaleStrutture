"""read_reactions: header-name parsing, suffix stripping, unit conversion, chunking and truncation
— docs/integrations/MIDAS.md §1, §2 rule 4, §3 reactions.py, §6."""
import json

import httpx
import pytest

from strutture.integrations.midas import MidasClient, MidasError, read_reactions
from strutture.integrations.midas.reactions import CHUNK_SIZE, MAX_CHUNKS
from strutture.shared.load_table import MAX_REAZIONI_ROWS

from .conftest import load_fixture, make_transport

BASE_URL = "https://moa-engineers.midasit.com:443/gen"
FAKE_KEY = "FAKEKEY"
_STANDARD_HEAD = ["Index", "Node", "Load", "FX", "FY", "FZ", "MX", "MY", "MZ"]


def _client(routes: dict) -> MidasClient:
    return MidasClient(BASE_URL, FAKE_KEY, transport=make_transport(routes))


@pytest.mark.unit
def test_reads_the_documented_fixture_shape() -> None:
    client = _client({"/post/table": load_fixture("midas_reactions.json")})
    rows, warnings = read_reactions(client, combinazioni=(("SLU1(CB)", "SLU_STR"), ("SLE1(CB)", "SLE_RARA")))
    assert warnings == ()
    assert len(rows) == 2
    row = next(r for r in rows if r.combo == "SLU1")
    assert row.nodo == 12
    assert row.famiglia == "SLU_STR"
    assert row.fz_kN == pytest.approx(847.1593)


@pytest.mark.unit
def test_header_parsing_tolerates_shuffled_and_extra_columns() -> None:
    table = {
        "HEAD": ["MZ", "Node", "Extra", "FY", "Load", "MX", "FZ", "FX", "MY", "Index"],
        "DATA": [["3.0", "12", "ignored-extra-value", "0", "SLU1", "0", "800", "0", "0", "1"]],
        "FORCE": "KN",
        "DIST": "M",
    }
    client = _client({"/post/table": {"SS_Table": table}})
    rows, _ = read_reactions(client, combinazioni=(("SLU1(CB)", None),))
    row = rows[0]
    assert row.nodo == 12
    assert row.combo == "SLU1"
    assert row.fz_kN == pytest.approx(800.0)
    assert row.mz_kNm == pytest.approx(3.0)


@pytest.mark.unit
def test_missing_table_key_raises_bad_response() -> None:
    client = _client({"/post/table": {"NOT_SS_Table": {}}})
    with pytest.raises(MidasError) as exc_info:
        read_reactions(client, combinazioni=(("SLU1(CB)", None),))
    assert exc_info.value.kind == "bad_response"


@pytest.mark.unit
def test_missing_data_key_raises_bad_response() -> None:
    table = {"HEAD": _STANDARD_HEAD}  # no "DATA"
    client = _client({"/post/table": {"SS_Table": table}})
    with pytest.raises(MidasError) as exc_info:
        read_reactions(client, combinazioni=(("SLU1(CB)", None),))
    assert exc_info.value.kind == "bad_response"


@pytest.mark.unit
def test_missing_required_header_raises_bad_response() -> None:
    table = {"HEAD": ["Index", "Node", "Load", "FX", "FY", "FZ", "MX", "MY"], "DATA": [], "FORCE": "KN", "DIST": "M"}
    client = _client({"/post/table": {"SS_Table": table}})
    with pytest.raises(MidasError) as exc_info:
        read_reactions(client, combinazioni=(("SLU1(CB)", None),))
    assert exc_info.value.kind == "bad_response"


@pytest.mark.unit
def test_suffix_stripping_slu1_cb_to_slu1() -> None:
    table = {
        "HEAD": _STANDARD_HEAD,
        "DATA": [["1", "12", "SLU1(CB)", "0", "0", "100", "0", "0", "0"]],
        "FORCE": "KN",
        "DIST": "M",
    }
    client = _client({"/post/table": {"SS_Table": table}})
    rows, _ = read_reactions(client, combinazioni=(("SLU1(CB)", "SLU_STR"),))
    assert rows[0].combo == "SLU1"
    assert rows[0].famiglia == "SLU_STR"


@pytest.mark.unit
def test_unit_conversion_from_n_and_mm() -> None:
    table = {
        "HEAD": _STANDARD_HEAD,
        "DATA": [["1", "12", "SLU1", "1000", "0", "500000", "0", "0", "2000000"]],
        "FORCE": "N",
        "DIST": "MM",
    }
    client = _client({"/post/table": {"SS_Table": table}})
    rows, _ = read_reactions(client, combinazioni=(("SLU1(CB)", "SLU_STR"),))
    row = rows[0]
    assert row.fx_kN == pytest.approx(1.0)
    assert row.fz_kN == pytest.approx(500.0)
    assert row.mz_kNm == pytest.approx(2.0)


@pytest.mark.unit
def test_falls_back_to_model_units_when_table_does_not_echo_them() -> None:
    table = {"HEAD": _STANDARD_HEAD, "DATA": [["1", "12", "SLU1", "1000", "0", "0", "0", "0", "0"]]}
    routes = {"/post/table": {"SS_Table": table}, "/db/UNIT": {"UNIT": {"1": {"FORCE": "N", "DIST": "MM"}}}}
    client = _client(routes)
    rows, _ = read_reactions(client, combinazioni=(("SLU1(CB)", None),))
    assert rows[0].fx_kN == pytest.approx(1.0)


@pytest.mark.unit
def test_unknown_response_unit_raises_bad_response() -> None:
    table = {"HEAD": _STANDARD_HEAD, "DATA": [["1", "12", "SLU1", "0", "0", "0", "0", "0", "0"]], "FORCE": "STONES", "DIST": "M"}
    client = _client({"/post/table": {"SS_Table": table}})
    with pytest.raises(MidasError) as exc_info:
        read_reactions(client, combinazioni=(("SLU1(CB)", None),))
    assert exc_info.value.kind == "bad_response"


@pytest.mark.unit
def test_chunks_requests_over_50_combinations() -> None:
    call_sizes: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        argument = json.loads(request.content)["Argument"]
        names = argument["LOAD_CASE_NAMES"]
        call_sizes.append(len(names))
        data = [["1", "12", name, "0", "0", "10", "0", "0", "0"] for name in names]
        return httpx.Response(200, json={"SS_Table": {"HEAD": _STANDARD_HEAD, "DATA": data, "FORCE": "KN", "DIST": "M"}})

    client = MidasClient(BASE_URL, FAKE_KEY, transport=httpx.MockTransport(handler))
    combinazioni = tuple((f"C{i}(CB)", None) for i in range(120))
    rows, warnings = read_reactions(client, combinazioni=combinazioni)
    assert call_sizes == [50, 50, 20]
    assert len(rows) == 120
    assert warnings == ()


@pytest.mark.unit
def test_rejects_more_than_max_chunks_worth_of_combinations_before_any_request() -> None:
    """HIGH 2 (security review): a request that would need more than `MAX_CHUNKS` round trips to
    MIDAS must be rejected up front, not looped over for minutes."""

    def never_called(request: httpx.Request) -> httpx.Response:
        raise AssertionError("must reject before making any request")

    client = MidasClient(BASE_URL, FAKE_KEY, transport=httpx.MockTransport(never_called))
    combinazioni = tuple((f"C{i}(CB)", None) for i in range(CHUNK_SIZE * MAX_CHUNKS + 1))
    with pytest.raises(MidasError) as exc_info:
        read_reactions(client, combinazioni=combinazioni)
    assert exc_info.value.kind == "forbidden_url"
    assert exc_info.value.status_code == 400


@pytest.mark.unit
def test_accepts_exactly_max_chunks_worth_of_combinations() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"SS_Table": {"HEAD": _STANDARD_HEAD, "DATA": [], "FORCE": "KN", "DIST": "M"}})

    client = MidasClient(BASE_URL, FAKE_KEY, transport=httpx.MockTransport(handler))
    combinazioni = tuple((f"C{i}(CB)", None) for i in range(CHUNK_SIZE * MAX_CHUNKS))
    rows, warnings = read_reactions(client, combinazioni=combinazioni)
    assert rows == ()
    assert warnings == ()


@pytest.mark.unit
def test_truncation_warning_at_max_reazioni_rows() -> None:
    n_rows = MAX_REAZIONI_ROWS + 10

    def handler(request: httpx.Request) -> httpx.Response:
        if not request.url.path.endswith("/post/table"):
            return httpx.Response(404, json={"message": "unexpected"})
        data = [[str(i), "12", "C1", "1.0", "0", "0", "0", "0", "0"] for i in range(n_rows)]
        return httpx.Response(200, json={"SS_Table": {"HEAD": _STANDARD_HEAD, "DATA": data, "FORCE": "KN", "DIST": "M"}})

    client = MidasClient(BASE_URL, FAKE_KEY, transport=httpx.MockTransport(handler))
    rows, warnings = read_reactions(client, combinazioni=(("C1(CB)", None),))
    assert len(rows) == MAX_REAZIONI_ROWS
    assert len(warnings) == 1
    assert str(MAX_REAZIONI_ROWS) in warnings[0]
