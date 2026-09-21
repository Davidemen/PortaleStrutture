"""Utilisation ratio `verifica()` — uniaxial shortcut and biaxial direction search."""
import math

import pytest

from strutture.shared.sezione_ca import forme
from strutture.shared.sezione_ca.domini import m_rd
from strutture.shared.sezione_ca.modelli import Barra, Sezione
from strutture.shared.sezione_ca.verifica import verifica

B, H = 300.0, 500.0


def _barre_4(diametro_mm: float = 16.0) -> tuple[Barra, ...]:
    return forme.fila_superiore(B, H, 30.0, 2, diametro_mm) + forme.fila_inferiore(B, H, 30.0, 2, diametro_mm)


def test_scorciatoia_uniassiale_coincide_con_m_rd(materiali_c25_b450c) -> None:
    sezione = Sezione(contorno=forme.rettangolo(B, H), barre=_barre_4(), materiali=materiali_c25_b450c)
    n_ed_kN = 300.0
    mrd_pos, mrd_neg = m_rd(sezione, n_ed_kN, "x")

    a_meta = verifica(sezione, n_ed_kN, mrd_pos / 2.0, 0.0)
    assert a_meta.rapporto == pytest.approx(0.5, rel=1e-9)
    assert a_meta.dentro
    assert a_meta.m_rd_direzione == pytest.approx(mrd_pos, rel=1e-9)

    negativo = verifica(sezione, n_ed_kN, mrd_neg / 2.0, 0.0)
    assert negativo.rapporto == pytest.approx(0.5, rel=1e-9)
    assert negativo.m_rd_direzione == pytest.approx(mrd_neg, rel=1e-9)

    sull_asse_y = verifica(sezione, n_ed_kN, 0.0, 40.0)
    mrd_y_pos, _ = m_rd(sezione, n_ed_kN, "y")
    assert sull_asse_y.rapporto == pytest.approx(40.0 / mrd_y_pos, rel=1e-9)


def test_appena_fuori_dal_dominio_uniassiale(materiali_c25_b450c) -> None:
    sezione = Sezione(contorno=forme.rettangolo(B, H), barre=_barre_4(), materiali=materiali_c25_b450c)
    n_ed_kN = 300.0
    mrd_pos, _ = m_rd(sezione, n_ed_kN, "x")
    fuori = verifica(sezione, n_ed_kN, mrd_pos * 1.2, 0.0)
    assert not fuori.dentro
    assert fuori.rapporto > 1.0


def test_biassiale_quadrato_4_barre_direzioni_0_e_45(materiali_c25_b450c) -> None:
    """Sezione quadrata + 4 barre d'angolo: a N costante, il rapporto per un carico allineato
    all'asse x è coerente con `m_rd`, e per un carico lungo la diagonale (Mx_Ed = My_Ed) il
    momento resistente nella direzione (`m_rd_direzione`) è lo stesso qualunque sia il verso preso
    lungo la diagonale, per simmetria della sezione."""
    lato, copriferro_mm = 400.0, 40.0
    semiluce = lato / 2.0 - copriferro_mm
    barre = tuple(
        Barra(x_mm=sx * semiluce, y_mm=sy * semiluce, diametro_mm=20.0) for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)
    )
    sezione = Sezione(contorno=forme.rettangolo(lato, lato), barre=barre, materiali=materiali_c25_b450c)
    n_ed_kN = 500.0

    mrd_x, _ = m_rd(sezione, n_ed_kN, "x")
    sull_asse = verifica(sezione, n_ed_kN, mrd_x * 0.6, 0.0)
    assert sull_asse.rapporto == pytest.approx(0.6, rel=1e-6)

    diagonale_1 = verifica(sezione, n_ed_kN, 50.0, 50.0)
    diagonale_2 = verifica(sezione, n_ed_kN, -50.0, -50.0)
    assert diagonale_1.m_rd_direzione == pytest.approx(diagonale_2.m_rd_direzione, rel=1e-3)
    assert diagonale_1.rapporto == pytest.approx(diagonale_2.rapporto, rel=1e-3)


def test_dentro_al_dominio_per_carico_piccolo(materiali_c25_b450c) -> None:
    sezione = Sezione(contorno=forme.rettangolo(B, H), barre=_barre_4(), materiali=materiali_c25_b450c)
    esito = verifica(sezione, 100.0, 5.0, 5.0)
    assert esito.dentro
    assert esito.rapporto < 1.0
    assert math.isfinite(esito.rapporto)


def test_n_ed_fuori_dal_dominio_non_solleva_ma_dentro_false(materiali_c25_b450c) -> None:
    """MEDIO — `N_Ed` fuori da `[N_min, N_max]` non è un errore di calcolo (la sezione non
    "esplode"): è semplicemente una combinazione non verificata, come previsto per una tabella di
    più righe (Fase 4 parte B). `verifica()` deve restituire `dentro=False` e un `rapporto` non
    finito (nessun `M_Rd` è definito fuori dal range di `N`), invece di sollevare `CalcError` e
    interrompere l'elaborazione dell'intera tabella."""
    sezione = Sezione(contorno=forme.rettangolo(B, H), barre=_barre_4(), materiali=materiali_c25_b450c)
    fuori_per_trazione = verifica(sezione, -1.0e7, 5.0, 0.0)
    assert not fuori_per_trazione.dentro
    assert fuori_per_trazione.rapporto == math.inf

    fuori_per_compressione = verifica(sezione, 1.0e7, 0.0, 5.0)
    assert not fuori_per_compressione.dentro
    assert fuori_per_compressione.rapporto == math.inf

    fuori_biassiale = verifica(sezione, 1.0e7, 5.0, 5.0)
    assert not fuori_biassiale.dentro
    assert fuori_biassiale.rapporto == math.inf
