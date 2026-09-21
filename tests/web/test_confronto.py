"""Pure comparison of two Report payloads (code-standard vs Excel mode): which outputs differ, by how
much, and which register entries are responsible (via their `uscite` paths)."""
import pytest

from strutture.shared.divergences.models import Divergence
from strutture.web.confronto import MAX_DIFFERENZE, confronta

pytestmark = pytest.mark.unit


def _report(data: dict, checks: list[dict] | None = None, ok: bool = True) -> dict:
    return {"ok": ok, "data": data, "checks": checks or [], "warnings": [], "errors": [], "inputs_echo": {}}


def _div(id_: str, uscite: tuple[str, ...], strumenti: tuple[str, ...] = ("demo-tool",)) -> Divergence:
    return Divergence(
        id=id_, titolo=f"Titolo di {id_}", tipo="errore_foglio", strumenti=strumenti,
        foglio="il foglio fa X", corretto="il codice fa Y", uscite=uscite,
    )


def test_identical_outputs_have_no_differences() -> None:
    result = confronta(_report({"a": 1.0, "g": {"b": 2.0}}), _report({"a": 1.0, "g": {"b": 2.0}}), "demo-tool", ())
    assert result["differenze"] == []
    assert result["totale_differenze"] == 0
    assert result["verifiche"] == []


def test_numeric_leaf_difference_reports_delta_and_relative_delta() -> None:
    result = confronta(_report({"g": {"mrd_kNm": 110.0}}), _report({"g": {"mrd_kNm": 100.0}}), "demo-tool", ())
    assert result["differenze"] == [
        {"percorso": "g.mrd_kNm", "standard": 110.0, "excel": 100.0, "delta": 10.0, "delta_rel": 0.1, "divergenze": []}
    ]


def test_relative_delta_is_none_when_the_excel_value_is_zero() -> None:
    (diff,) = confronta(_report({"x": 0.5}), _report({"x": 0.0}), "demo-tool", ())["differenze"]
    assert diff["delta"] == 0.5 and diff["delta_rel"] is None


def test_float_noise_is_not_a_difference() -> None:
    result = confronta(_report({"x": 0.1 + 0.2}), _report({"x": 0.3}), "demo-tool", ())
    assert result["differenze"] == []


def test_non_numeric_and_null_differences_carry_no_delta() -> None:
    result = confronta(_report({"classe": "TOZZO", "k": None}), _report({"classe": "SNELLO", "k": 2.0}), "demo-tool", ())
    assert result["differenze"] == [
        {"percorso": "classe", "standard": "TOZZO", "excel": "SNELLO", "delta": None, "delta_rel": None, "divergenze": []},
        {"percorso": "k", "standard": None, "excel": 2.0, "delta": None, "delta_rel": None, "divergenze": []},
    ]


def test_bool_is_compared_as_a_flag_not_as_a_number() -> None:
    (diff,) = confronta(_report({"ok": True}), _report({"ok": False}), "demo-tool", ())["differenze"]
    assert diff["delta"] is None


def test_rows_are_indexed_and_the_sketch_subtree_is_ignored() -> None:
    standard = _report({"righe": [{"eta": 0.5}, {"eta": 0.9}], "schizzo": {"viste": [1, 2, 3]}})
    excel = _report({"righe": [{"eta": 0.5}, {"eta": 0.7}], "schizzo": {"viste": []}})
    result = confronta(standard, excel, "demo-tool", ())
    assert [d["percorso"] for d in result["differenze"]] == ["righe[1].eta"]


def test_rows_of_different_length_report_the_missing_rows() -> None:
    result = confronta(_report({"righe": [{"eta": 0.5}]}), _report({"righe": [{"eta": 0.5}, {"eta": 0.7}]}), "demo-tool", ())
    assert result["differenze"] == [
        {"percorso": "righe[1].eta", "standard": None, "excel": 0.7, "delta": None, "delta_rel": None, "divergenze": []}
    ]


def test_responsible_divergences_come_from_uscite_with_row_indices_stripped() -> None:
    register = (
        _div("demo/rows", ("righe.eta",)),
        _div("demo/group", ("g",)),                       # a prefix covers everything underneath
        _div("demo/other-tool", ("righe.eta",), strumenti=("altro-tool",)),
        _div("demo/unrelated", ("zzz",)),
    )
    standard = _report({"righe": [{"eta": 0.9}], "g": {"b": 2.0}})
    excel = _report({"righe": [{"eta": 0.7}], "g": {"b": 3.0}})
    result = confronta(standard, excel, "demo-tool", register)
    by_path = {d["percorso"]: d["divergenze"] for d in result["differenze"]}
    assert by_path == {"righe[0].eta": ["demo/rows"], "g.b": ["demo/group"]}
    assert result["divergenze_coinvolte"] == ["demo/group", "demo/rows"]


def test_check_outcomes_that_change_are_listed_by_name() -> None:
    standard = _report({}, checks=[{"name": "Flessione", "passed": False, "value": 1.2}, {"name": "Taglio", "passed": True, "value": 0.4}])
    excel = _report({}, checks=[{"name": "Flessione", "passed": True, "value": 0.9}, {"name": "Taglio", "passed": True, "value": 0.4}])
    result = confronta(standard, excel, "demo-tool", ())
    assert result["verifiche"] == [
        {"nome": "Flessione", "standard": {"passed": False, "value": 1.2}, "excel": {"passed": True, "value": 0.9},
         "cambia_esito": True}
    ]


def test_a_check_whose_value_moves_but_not_its_outcome_is_flagged_as_such() -> None:
    standard = _report({}, checks=[{"name": "Scorrimento", "passed": True, "value": 1.26}])
    excel = _report({}, checks=[{"name": "Scorrimento", "passed": True, "value": 1.18}])
    (verifica,) = confronta(standard, excel, "demo-tool", ())["verifiche"]
    assert verifica["cambia_esito"] is False


def test_a_check_present_in_one_mode_only_is_listed() -> None:
    result = confronta(_report({}, checks=[{"name": "Nuova", "passed": True, "value": 0.1}]), _report({}), "demo-tool", ())
    assert result["verifiche"] == [
        {"nome": "Nuova", "standard": {"passed": True, "value": 0.1}, "excel": None, "cambia_esito": True}
    ]


def test_the_list_is_capped_but_the_total_is_always_reported() -> None:
    n = MAX_DIFFERENZE + 25
    standard = _report({"righe": [{"eta": float(i)} for i in range(n)]})
    excel = _report({"righe": [{"eta": float(i) + 1.0} for i in range(n)]})
    result = confronta(standard, excel, "demo-tool", ())
    assert len(result["differenze"]) == MAX_DIFFERENZE
    assert result["totale_differenze"] == n


def test_a_failed_run_in_one_mode_compares_nothing_but_says_so() -> None:
    result = confronta(_report({"a": 1.0}), _report(None, ok=False), "demo-tool", ())  # type: ignore[arg-type]
    assert result["differenze"] == [] and result["totale_differenze"] == 0
    assert result["confrontabile"] is False


def test_a_key_absent_in_one_mode_and_null_in_the_other_is_not_a_difference() -> None:
    assert confronta(_report({"a": 1.0, "k": None}), _report({"a": 1.0}), "demo-tool", ())["differenze"] == []


# --- attribution by switching ONE correction to Excel behaviour at a time ---------------------------

def _esegui_demo() -> dict:
    """A fake standard-mode run whose outputs depend on two linked corrections."""
    from strutture.shared.divergences.marker import legacy

    a = 1.0 + (10.0 if legacy("demo/a", False) else 0.0)
    b = 2.0 + (20.0 if legacy("demo/b", False) else 0.0)
    if legacy("demo/rotta", False):
        raise ValueError("stato incoerente con una sola correzione attiva")
    return _report({"a": a, "g": {"b": b}, "somma": a + b})


def test_single_correction_runs_attribute_each_path_to_the_corrections_that_move_it() -> None:
    from strutture.web.confronto import attribuisci_per_singola_correzione

    esito = attribuisci_per_singola_correzione(_esegui_demo, _esegui_demo(), ("demo/a", "demo/b"))
    assert esito.per_percorso == {"a": ("demo/a",), "g.b": ("demo/b",), "somma": ("demo/a", "demo/b")}
    assert esito.valutate == 2 and esito.completa is True and esito.non_valutabili == ()


def test_a_correction_that_cannot_run_alone_is_reported_not_raised() -> None:
    from strutture.web.confronto import attribuisci_per_singola_correzione

    esito = attribuisci_per_singola_correzione(_esegui_demo, _esegui_demo(), ("demo/rotta", "demo/a"))
    assert esito.per_percorso == {"a": ("demo/a",), "somma": ("demo/a",)}
    assert esito.non_valutabili == ("demo/rotta",) and esito.completa is True


def test_the_time_budget_stops_the_runs_and_says_so() -> None:
    from strutture.web.confronto import attribuisci_per_singola_correzione

    ticks = iter([0.0, 0.0, 5.0, 5.0, 5.0])
    esito = attribuisci_per_singola_correzione(
        _esegui_demo, _esegui_demo(), ("demo/a", "demo/b"), budget_s=3.0, orologio=lambda: next(ticks),
    )
    assert esito.valutate == 1 and esito.completa is False
    assert esito.per_percorso == {"a": ("demo/a",), "somma": ("demo/a",)}


def test_confronta_merges_run_based_and_register_based_attribution() -> None:
    from strutture.web.confronto import Attribuzione

    register = (_div("demo/statica", ("a",)),)
    attribuzione = Attribuzione(per_percorso={"a": ("demo/a",), "righe[0].eta": ("demo/b",)}, valutate=2, completa=True, non_valutabili=())
    standard = _report({"a": 1.0, "righe": [{"eta": 0.5}]})
    excel = _report({"a": 9.0, "righe": [{"eta": 0.7}]})
    result = confronta(standard, excel, "demo-tool", register, attribuzione)
    by_path = {d["percorso"]: d["divergenze"] for d in result["differenze"]}
    assert by_path == {"a": ["demo/a", "demo/statica"], "righe[0].eta": ["demo/b"]}
    assert result["divergenze_coinvolte"] == ["demo/a", "demo/b", "demo/statica"]
    assert result["attribuzione"] == {"correzioni_valutate": 2, "completa": True, "non_valutabili": []}


def test_without_run_based_attribution_the_block_says_none_was_done() -> None:
    result = confronta(_report({"a": 1.0}), _report({"a": 2.0}), "demo-tool", ())
    assert result["attribuzione"] == {"correzioni_valutate": 0, "completa": True, "non_valutabili": []}


def test_an_output_that_merely_echoes_the_mode_flag_is_not_a_difference() -> None:
    result = confronta(_report({"regole": {"legacy_compat": False, "k": 1.0}}), _report({"regole": {"legacy_compat": True, "k": 1.0}}), "demo-tool", ())
    assert result["differenze"] == []
