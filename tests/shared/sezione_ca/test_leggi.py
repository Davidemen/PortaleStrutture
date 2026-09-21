"""Constitutive laws — NTC 2018 §4.1.2.1.2.1 closed forms."""
import pytest

from strutture.shared.sezione_ca import leggi

FCD = 14.166666666666666  # C25/30: 0.85*25/1.5
FYD = 391.30434782608694  # B450C: 450/1.15
ES = 210000.0


def test_calcestruzzo_parabola_zero_in_trazione() -> None:
    assert leggi.sigma_calcestruzzo_parabola_rettangolo(0.0001, FCD) == 0.0


def test_calcestruzzo_parabola_al_picco() -> None:
    assert leggi.sigma_calcestruzzo_parabola_rettangolo(-leggi.EPS_C2, FCD) == pytest.approx(-FCD)


def test_calcestruzzo_parabola_a_meta_picco() -> None:
    """A ε = εc2/2: σ = -fcd*(1-(1-0.5)^2) = -0.75*fcd (formula NTC applicata a mano)."""
    atteso = -FCD * 0.75
    assert leggi.sigma_calcestruzzo_parabola_rettangolo(-leggi.EPS_C2 / 2.0, FCD) == pytest.approx(atteso)


def test_calcestruzzo_parabola_sul_plateau() -> None:
    assert leggi.sigma_calcestruzzo_parabola_rettangolo(-leggi.EPS_CU2, FCD) == pytest.approx(-FCD)


def test_calcestruzzo_bilineare_zero_in_trazione() -> None:
    assert leggi.sigma_calcestruzzo_bilineare(0.001, FCD) == 0.0


def test_calcestruzzo_bilineare_rampa_lineare() -> None:
    """A ε = εc3/2: σ = -fcd/2 (rampa lineare)."""
    assert leggi.sigma_calcestruzzo_bilineare(-leggi.EPS_C3 / 2.0, FCD) == pytest.approx(-FCD / 2.0)


def test_calcestruzzo_bilineare_plateau() -> None:
    assert leggi.sigma_calcestruzzo_bilineare(-leggi.EPS_C3, FCD) == pytest.approx(-FCD)
    assert leggi.sigma_calcestruzzo_bilineare(-leggi.EPS_CU3, FCD) == pytest.approx(-FCD)


def test_eps_ud_default_b450c() -> None:
    assert leggi.eps_ud() == pytest.approx(0.9 * 0.075)


def test_acciaio_elastico_in_campo_elastico() -> None:
    eps = 0.001
    assert leggi.sigma_acciaio_elastico_perfettamente_plastico(eps, FYD, ES) == pytest.approx(ES * eps)


def test_acciaio_elastico_plafona_in_trazione_e_compressione() -> None:
    assert leggi.sigma_acciaio_elastico_perfettamente_plastico(0.05, FYD, ES) == pytest.approx(FYD)
    assert leggi.sigma_acciaio_elastico_perfettamente_plastico(-0.05, FYD, ES) == pytest.approx(-FYD)


def test_acciaio_bilineare_in_campo_elastico_uguale_a_epp() -> None:
    eps = 0.001
    assert leggi.sigma_acciaio_bilineare(eps, FYD, ES, k_incrudimento=1.2) == pytest.approx(ES * eps)


def test_acciaio_bilineare_a_eps_ud_raggiunge_k_fyd() -> None:
    k = 1.2
    eud = leggi.eps_ud()
    assert leggi.sigma_acciaio_bilineare(eud, FYD, ES, k_incrudimento=k) == pytest.approx(k * FYD, rel=1e-9)
    assert leggi.sigma_acciaio_bilineare(-eud, FYD, ES, k_incrudimento=k) == pytest.approx(-k * FYD, rel=1e-9)


def test_acciaio_bilineare_oltre_eps_ud_resta_su_k_fyd() -> None:
    k = 1.2
    eud = leggi.eps_ud()
    assert leggi.sigma_acciaio_bilineare(eud * 2.0, FYD, ES, k_incrudimento=k) == pytest.approx(k * FYD, rel=1e-9)


def test_dispatch_leggi_da_materiali(materiali_c25_b450c, materiali_c25_b450c_bilineare) -> None:
    cls_parabola = leggi.legge_calcestruzzo(materiali_c25_b450c)
    cls_bilineare = leggi.legge_calcestruzzo(materiali_c25_b450c_bilineare)
    assert cls_parabola(-leggi.EPS_C2) == pytest.approx(cls_bilineare(-leggi.EPS_C3))
    acciaio = leggi.legge_acciaio(materiali_c25_b450c)
    assert acciaio(0.001) == pytest.approx(materiali_c25_b450c.acciaio.es_MPa * 0.001)
