"""Pivot strain planes — closed-form endpoints and monotonicity (`docs/architecture-phase4.md`
§A verification plan item 1)."""
from itertools import pairwise

import pytest

from strutture.shared.sezione_ca import forme
from strutture.shared.sezione_ca.integrazione import epsilon
from strutture.shared.sezione_ca.leggi import EPS_C2, EPS_C3, EPS_UK_B450C, eps_ud
from strutture.shared.sezione_ca.modelli import Barra, MaterialiSezione, Sezione
from strutture.shared.sezione_ca.stati_ultimi import risultante_pivot, stato_pivot

B, H = 300.0, 500.0


def _barre_4(diametro_mm: float = 16.0) -> tuple[Barra, ...]:
    return forme.fila_superiore(B, H, 30.0, 2, diametro_mm) + forme.fila_inferiore(B, H, 30.0, 2, diametro_mm)


def _sezione(materiali: MaterialiSezione, barre: tuple[Barra, ...] = ()) -> Sezione:
    return Sezione(contorno=forme.rettangolo(B, H), barre=barre, materiali=materiali)


@pytest.mark.parametrize("theta_rad", [0.0, 0.7, 1.9, 3.4])
def test_t_zero_e_trazione_pura_n_meno_fyd_as(materiali_c25_b450c, theta_rad) -> None:
    """`t=0` (qualsiasi `theta_rad`): stato uniforme a `eps_ud`, `N = -fyd*As` esatto — invariante
    di primo principio (§A item 1), indipendente dall'angolo perché lo stato è uniforme (kappa=0)."""
    barre = _barre_4()
    sezione = _sezione(materiali_c25_b450c, barre)
    area_barre = sum(b.area_mm2 for b in barre)
    atteso_N_kN = -materiali_c25_b450c.acciaio.fyd_MPa * area_barre / 1000.0
    r = risultante_pivot(sezione, theta_rad, 0.0)
    assert r.n_kN == pytest.approx(atteso_N_kN, rel=1e-6)
    assert r.mx_kNm == pytest.approx(0.0, abs=1e-6)
    assert r.my_kNm == pytest.approx(0.0, abs=1e-6)


@pytest.mark.parametrize("theta_rad", [0.0, 0.7, 1.9, 3.4])
def test_t_uno_e_compressione_pura_n_fcd_ac_piu_fyd_as(materiali_c25_b450c, theta_rad) -> None:
    """`t=1`: stato uniforme a `-eps_c2`, `N = fcd*Ac + fyd*As` esatto (pivot C, non `eps_cu2`)."""
    barre = _barre_4()
    sezione = _sezione(materiali_c25_b450c, barre)
    area_barre = sum(b.area_mm2 for b in barre)
    area_cls = B * H - area_barre
    atteso_N_kN = (
        materiali_c25_b450c.calcestruzzo.fcd_MPa * area_cls + materiali_c25_b450c.acciaio.fyd_MPa * area_barre
    ) / 1000.0
    r = risultante_pivot(sezione, theta_rad, 1.0)
    assert r.n_kN == pytest.approx(atteso_N_kN, rel=1e-6)
    assert r.mx_kNm == pytest.approx(0.0, abs=1e-6)
    assert r.my_kNm == pytest.approx(0.0, abs=1e-6)


def test_n_monotono_crescente_da_trazione_a_compressione(materiali_c25_b450c) -> None:
    """`N(t)` è monotona non decrescente lungo l'unico parametro `t` (trazione -> compressione),
    come richiesto dall'architettura (`stati_ultimi.py`, "single monotonic parameter")."""
    barre = _barre_4()
    sezione = _sezione(materiali_c25_b450c, barre)
    valori_n = [risultante_pivot(sezione, 0.3, i / 40.0).n_kN for i in range(41)]
    assert all(b >= a - 1e-6 for a, b in pairwise(valori_n))


def test_stato_pivot_clampa_t_fuori_da_0_1(materiali_c25_b450c) -> None:
    """`t` fuori da `[0, 1]` viene clampato (robustezza numerica per la bisezione di `domini.py`)."""
    sezione = _sezione(materiali_c25_b450c)
    assert stato_pivot(sezione, 0.0, -0.5) == stato_pivot(sezione, 0.0, 0.0)
    assert stato_pivot(sezione, 0.0, 1.5) == stato_pivot(sezione, 0.0, 1.0)


def test_transizione_b_c_ha_deformazione_nulla_al_lembo_teso(materiali_c25_b450c) -> None:
    """CRITICO — punto C classico: sta a `s = eps_c2/eps_cu2` (= 4/7) dal lembo TESO (equivalente
    a `1 - eps_c2/eps_cu2` = 3/7 dal lembo compresso). Alla transizione B/C (`t = 2/3`, terzo
    vertice su 4, regione 3 su 3) il profilo è lineare fra `(p_max, -eps_cu2)` (pivot B) e
    `(p_min, eps_bot)`, e deve valere `-eps_c2` esattamente a `p_c = p_min + s*h`:
    `eps_bot*(1-s) + eps_top*s = -eps_c2` con `eps_top = -eps_cu2` e
    `eps_cu2*s = eps_cu2*(eps_c2/eps_cu2) = eps_c2` identicamente, quindi
    `eps_bot*(1-s) = -eps_c2 - (-eps_cu2)*s = -eps_c2 + eps_c2 = 0` -> `eps_bot = 0` ESATTO
    (per qualunque coppia eps_c/eps_cu, non solo 2/3.5). La versione attuale usa invece
    `r = 1 - eps_c2/eps_cu2` come frazione dal lembo TESO (errore di lato), dando
    `eps_bot = (eps_cu2*r - eps_c2)/(1-r) = -0.000875` invece di `0.0`."""
    sezione = _sezione(materiali_c25_b450c)
    t_transizione_bc = 2.0 / 3.0  # 3° vertice su 4 (N_REGIONI_PIVOT = 3): fine del ramo pivot B.
    eps0, kx, ky = stato_pivot(sezione, 0.0, t_transizione_bc)
    eps_al_lembo_teso = epsilon(eps0, kx, ky, 0.0, -H / 2.0)
    assert eps_al_lembo_teso == pytest.approx(0.0, abs=1e-9)


def test_pivot_a_ancorato_alla_barra_piu_tesa_non_al_lembo_cls(materiali_c25_b450c) -> None:
    """MEDIO — pivot A è la deformazione ultima della barra più tesa (`docs/architecture-phase4.md`
    §A: "pivot A (acciaio a εud)"), non del lembo teso del contorno in cls. Con un copriferro di
    40 mm su una sezione di 500 mm, la barra sta a `y = -(H/2 - 40)` mentre il lembo cls sta a
    `y = -H/2`: se il pivot fosse (erroneamente) ancorato al lembo cls, la barra non
    raggiungerebbe mai `eud`. Alla transizione A/B (`t = 1/3`, 2° vertice su 4) la deformazione
    ALLA BARRA deve invece valere esattamente `eud = 0.9*eps_uk`."""
    copriferro_mm = 40.0
    barra = Barra(x_mm=0.0, y_mm=-(H / 2.0 - copriferro_mm), diametro_mm=16.0)
    sezione = _sezione(materiali_c25_b450c, (barra,))
    t_transizione_ab = 1.0 / 3.0  # 2° vertice su 4: fine del ramo pivot A.
    eps0, kx, ky = stato_pivot(sezione, 0.0, t_transizione_ab)
    eps_alla_barra = epsilon(eps0, kx, ky, barra.x_mm, barra.y_mm)
    assert eps_alla_barra == pytest.approx(eps_ud(EPS_UK_B450C), rel=1e-9)


def test_compressione_pura_usa_eps_c3_per_la_legge_bilineare(materiali_c25_b450c_bilineare) -> None:
    """ALTO — con la legge bilineare (NTC2018 Fig. 4.1.2.1.2.1b) lo stato di compressione pura
    (`t = 1`) deve saturare a `-eps_c3` (= -0.00175), non a `-eps_c2` (= -0.002) della
    parabola-rettangolo: sono due leggi diverse con un plateau diverso, e il barometro pivot deve
    seguire quella selezionata da `materiali.legge_calcestruzzo`."""
    sezione = _sezione(materiali_c25_b450c_bilineare)
    eps0, kx, ky = stato_pivot(sezione, 0.0, 1.0)
    assert (kx, ky) == (0.0, 0.0)
    assert eps0 == pytest.approx(-EPS_C3, rel=1e-9)
    assert eps0 != pytest.approx(-EPS_C2, rel=1e-3)
