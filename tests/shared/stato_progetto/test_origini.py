"""stato_origini: §25.1 own-state rule."""
import pytest

from strutture.shared.stato_progetto.origini import stato_origini


def _item(**over):
    base = {"chiave": "sito.ag_g", "strumento": "sisma-parametri-sito", "percorso": "risultati.ag_g",
             "ingresso": False, "valore": 0.15, "elemento_id": "prov-1"}
    return {**base, **over}


@pytest.mark.unit
def test_unchanged_value_not_marked():
    stato = stato_origini((_item(),), lambda eid: object(), lambda f, p, i: 0.15)
    assert stato.da_ricalcolare is False
    assert stato.motivi == ()


@pytest.mark.unit
def test_changed_value_marks_valore_cambiato():
    stato = stato_origini((_item(),), lambda eid: object(), lambda f, p, i: 0.18)
    assert stato.da_ricalcolare is True
    assert stato.motivi[0].causa == "valore_cambiato"
    assert stato.motivi[0].valore_attuale == 0.18


@pytest.mark.unit
def test_relative_tolerance_ignores_numeric_noise():
    stato = stato_origini((_item(valore=1.0),), lambda eid: object(), lambda f, p, i: 1.0 + 1e-12)
    assert stato.da_ricalcolare is False


@pytest.mark.unit
def test_deleted_provider_marks_origine_eliminata():
    stato = stato_origini((_item(),), lambda eid: None, lambda f, p, i: 0.15)
    assert stato.motivi[0].causa == "origine_eliminata"


@pytest.mark.unit
def test_failing_provider_marks_origine_non_calcolabile():
    def esplode(f, p, i):
        raise ValueError("boom")

    stato = stato_origini((_item(),), lambda eid: object(), esplode)
    assert stato.motivi[0].causa == "origine_non_calcolabile"


@pytest.mark.unit
def test_item_without_elemento_id_never_marks():
    stato = stato_origini((_item(elemento_id=None),), lambda eid: object(), lambda f, p, i: 999)
    assert stato.da_ricalcolare is False
    assert stato.motivi == ()


@pytest.mark.unit
def test_enum_value_changed_is_string_compared():
    stato = stato_origini((_item(valore="A"),), lambda eid: object(), lambda f, p, i: "B")
    assert stato.motivi[0].causa == "valore_cambiato"


@pytest.mark.unit
def test_limite_ricalcoli_gives_controllo_rinviato_not_marked():
    from strutture.shared.stato_progetto.origini import LimiteRicalcoliRaggiunto

    def esaurito(f, p, i):
        raise LimiteRicalcoliRaggiunto()

    stato = stato_origini((_item(), _item(chiave="altra.chiave")), lambda eid: object(), esaurito)
    assert stato.da_ricalcolare is False
    assert all(m.causa == "controllo_rinviato" for m in stato.motivi)


@pytest.mark.unit
def test_same_revision_but_changed_output_still_marks():
    # the rule never looks at `revisione`: a code fix or a register change at a fixed revision must
    # still be caught (§25.1).
    stato = stato_origini((_item(),), lambda eid: object(), lambda f, p, i: 0.20)
    assert stato.da_ricalcolare is True


@pytest.mark.unit
def test_malformed_saved_item_is_non_calcolabile_never_a_crash():
    """A saved `provenienza.collegamenti` entry missing `chiave`/`strumento` (external, stored
    data) must never raise KeyError -- read defensively, report "non calcolabile" like any other
    provider failure."""
    item = {"elemento_id": "prov-1", "percorso": "risultati.ag_g", "valore": 0.15}
    stato = stato_origini((item,), lambda eid: object(), lambda f, p, i: 0.18)
    assert stato.motivi[0].causa == "valore_cambiato"
    assert stato.motivi[0].chiave == ""
    assert stato.motivi[0].strumento == ""


@pytest.mark.unit
def test_missing_percorso_is_non_calcolabile():
    stato = stato_origini((_item(percorso=None),), lambda eid: object(), lambda f, p, i: 0.15)
    assert stato.motivi[0].causa == "origine_non_calcolabile"


@pytest.mark.unit
def test_vanished_output_path_is_non_calcolabile_not_valore_cambiato():
    """The provider ran fine but its own output shape changed, so nothing lives at `percorso`
    anymore (`None`): a missing value, not "changed to None"."""
    stato = stato_origini((_item(),), lambda eid: object(), lambda f, p, i: None)
    assert stato.motivi[0].causa == "origine_non_calcolabile"


@pytest.mark.unit
def test_message_uses_italian_decimal_comma():
    stato = stato_origini((_item(valore=0.15),), lambda eid: object(), lambda f, p, i: 0.18)
    assert stato.motivi[0].messaggio == "sito.ag_g: 0,15 → 0,18"
