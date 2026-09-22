from decimal import Decimal

import pytest

from strutture.shared.dimensiona.griglia import MAX_GRADINI, GrigliaError, costruisci_griglia, indici_campionamento


def test_multipli_decimali_senza_drift():
    griglia = costruisci_griglia(0.1, 0.5, 0.05, intero=False)
    assert griglia == tuple(Decimal(v) for v in ("0.10", "0.15", "0.20", "0.25", "0.30", "0.35", "0.40", "0.45", "0.50"))


def test_campo_intero_solo_multipli_interi():
    griglia = costruisci_griglia(1, 6, 2, intero=True)
    assert griglia == (Decimal(2), Decimal(4), Decimal(6))


def test_passo_non_intero_su_campo_intero_e_422():
    with pytest.raises(GrigliaError, match="intero"):
        costruisci_griglia(1, 6, 1.5, intero=True)


def test_griglia_vuota():
    with pytest.raises(GrigliaError, match="Nessun multiplo"):
        costruisci_griglia(0.101, 0.104, 0.05, intero=False)


def test_da_maggiore_o_uguale_a():
    with pytest.raises(GrigliaError):
        costruisci_griglia(1.0, 1.0, 0.1, intero=False)


def test_troppi_gradini():
    with pytest.raises(GrigliaError, match="Troppi"):
        costruisci_griglia(0, MAX_GRADINI + 10, 1, intero=True)


def test_passo_non_positivo():
    with pytest.raises(GrigliaError, match="passo"):
        costruisci_griglia(0.1, 1.0, 0, intero=False)


def test_indici_campionamento_pochi_punti_su_griglia_piccola():
    assert indici_campionamento(3, 17) == (0, 1, 2)


def test_indici_campionamento_estremi_inclusi():
    indici = indici_campionamento(200, 17)
    assert indici[0] == 0
    assert indici[-1] == 199
    assert len(indici) <= 17
