import pytest

from strutture.members.ca_fessurazione.coefficienti_fessurazione import (
    k1_per_tipo_barre,
    k2_per_sollecitazione,
    kt_per_durata_carico,
    wlim_mm_per_classe,
)
from strutture.shared.tables import KeyNotFound

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(("tipo_barre", "atteso"), [("barre aderenza migliorata", 0.8), ("barre lisce", 1.6)])
def test_k1(tipo_barre, atteso):
    assert k1_per_tipo_barre(tipo_barre) == pytest.approx(atteso, rel=1e-9)


@pytest.mark.parametrize(("tipo_sollecitazione", "atteso"), [("caso di flessione", 0.5), ("caso di trazione semplice", 1.0)])
def test_k2(tipo_sollecitazione, atteso):
    assert k2_per_sollecitazione(tipo_sollecitazione) == pytest.approx(atteso, rel=1e-9)


def test_k2_dropped_branch_is_not_a_valid_key():
    """Divergence: 'caso di trazione eccentrica' (dead #DIV/0! branch, W7) is not ported."""
    with pytest.raises(KeyNotFound):
        k2_per_sollecitazione("caso di trazione eccentrica (o per singole parti di sezione)")  # type: ignore[arg-type]


@pytest.mark.parametrize(("durata_carico", "atteso"), [("breve durata", 0.6), ("lunga durata", 0.4)])
def test_kt(durata_carico, atteso):
    assert kt_per_durata_carico(durata_carico) == pytest.approx(atteso, rel=1e-9)


@pytest.mark.parametrize(
    ("classe_fessurazione", "atteso"),
    [("w1 (0.20 mm)", 0.2), ("w2 (0.30 mm)", 0.3), ("w3 (0.40 mm)", 0.4)],
)
def test_wlim(classe_fessurazione, atteso):
    assert wlim_mm_per_classe(classe_fessurazione) == pytest.approx(atteso, rel=1e-9)
