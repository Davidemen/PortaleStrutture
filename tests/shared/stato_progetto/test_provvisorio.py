"""stato_provvisorio: §25.2, standard vs Excel mode, da_verificare counted separately."""
import pytest

from strutture.shared.stato_progetto.provvisorio import stato_provvisorio


def _voce(**over):
    base = {"da_confermare": 0, "approvato": 0, "respinto": 0,
            "ramo_nessuno": {"da_confermare": 0, "approvato": 0, "respinto": 0}, "da_verificare": 0}
    return {**base, **over}


@pytest.mark.unit
def test_no_register_entries_never_provvisorio():
    stato = stato_provvisorio(None, "standard")
    assert stato.provvisorio is False


@pytest.mark.unit
def test_standard_mode_da_confermare_makes_provvisorio():
    stato = stato_provvisorio(_voce(da_confermare=2), "standard")
    assert stato.provvisorio is True
    assert stato.correzioni.da_confermare == 2


@pytest.mark.unit
def test_standard_mode_respinto_makes_provvisorio_decision_21():
    stato = stato_provvisorio(_voce(respinto=1), "standard")
    assert stato.provvisorio is True
    assert stato.correzioni.respinto == 1


@pytest.mark.unit
def test_standard_mode_approvato_only_not_provvisorio():
    stato = stato_provvisorio(_voce(approvato=3), "standard")
    assert stato.provvisorio is False


@pytest.mark.unit
def test_excel_mode_only_ramo_nessuno_counts():
    # a standard-branch entry (not ramo_nessuno) does not make Excel mode provvisorio.
    voce = _voce(da_confermare=1)
    stato = stato_provvisorio(voce, "excel")
    assert stato.provvisorio is False
    assert stato.correzioni.da_confermare == 0


@pytest.mark.unit
def test_excel_mode_ramo_nessuno_da_confermare_makes_provvisorio():
    voce = _voce(da_confermare=1, ramo_nessuno={"da_confermare": 1, "approvato": 0, "respinto": 0})
    stato = stato_provvisorio(voce, "excel")
    assert stato.provvisorio is True


@pytest.mark.unit
def test_da_verificare_never_makes_provvisorio_but_is_counted():
    stato = stato_provvisorio(_voce(da_verificare=4), "standard")
    assert stato.provvisorio is False
    assert stato.correzioni.da_verificare == 4
