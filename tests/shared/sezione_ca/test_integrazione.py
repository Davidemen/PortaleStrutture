"""Strip integration — closed forms and invariants (`docs/architecture-phase4.md` §A verification
plan, the items that apply to the core engine)."""
import math
import time

import pytest

from strutture.shared.sezione_ca import forme, geometria
from strutture.shared.sezione_ca.integrazione import risultante_sezione
from strutture.shared.sezione_ca.leggi import EPS_CU2, eps_ud
from strutture.shared.sezione_ca.modelli import Barra, MaterialiSezione, Sezione
from strutture.shared.units import kn_to_n, knm_to_nmm

B, H = 300.0, 500.0


def _sezione_rettangolare(materiali: MaterialiSezione, barre: tuple[Barra, ...] = ()) -> Sezione:
    return Sezione(contorno=forme.rettangolo(B, H), barre=barre, materiali=materiali)


def _barre_4(diametro_mm: float = 16.0) -> tuple[Barra, ...]:
    return forme.fila_superiore(B, H, 30.0, 2, diametro_mm) + forme.fila_inferiore(B, H, 30.0, 2, diametro_mm)


@pytest.mark.parametrize("legge", ["parabola-rettangolo", "bilineare"])
def test_compressione_uniforme_pura_n_fcd_ac_piu_fyd_as(materiali_c25_b450c, legge) -> None:
    """N = fcd·Ac + fyd·As in compressione uniforme oltre il plateau — vale per entrambe le
    leggi del calcestruzzo (sul plateau danno lo stesso fcd)."""
    materiali = materiali_c25_b450c.model_copy(update={"legge_calcestruzzo": legge})
    barre = _barre_4()
    sezione = _sezione_rettangolare(materiali, barre)
    area_barre = sum(b.area_mm2 for b in barre)
    area_cls = B * H - area_barre
    atteso_N_kN = (
        materiali.calcestruzzo.fcd_MPa * area_cls + materiali.acciaio.fyd_MPa * area_barre
    ) / 1000.0
    r = risultante_sezione(sezione, -2.0 * EPS_CU2, 0.0, 0.0)
    assert r.n_kN == pytest.approx(atteso_N_kN, rel=1e-6)
    assert r.mx_kNm == pytest.approx(0.0, abs=1e-6)
    assert r.my_kNm == pytest.approx(0.0, abs=1e-6)


def test_trazione_pura_n_meno_fyd_as(materiali_c25_b450c) -> None:
    """N = -fyd·As in trazione pura (cls ignorato in trazione, acciaio plafonato a fyd)."""
    barre = _barre_4()
    sezione = _sezione_rettangolare(materiali_c25_b450c, barre)
    area_barre = sum(b.area_mm2 for b in barre)
    atteso_N_kN = -materiali_c25_b450c.acciaio.fyd_MPa * area_barre / 1000.0
    r = risultante_sezione(sezione, 0.02, 0.0, 0.0)
    assert r.n_kN == pytest.approx(atteso_N_kN, rel=1e-6)


def test_flessione_lineare_legge_bilineare_triangolo_piu_rettangolo(materiali_c25_b450c_bilineare) -> None:
    """Piano di deformazione lineare (κx ≠ 0) tale che il diagramma di sforzo sia un triangolo
    (0..εc3) sulla metà inferiore e un blocco costante (εc3..εcu3) sulla metà superiore: N e M si
    ricavano a mano con la statica elementare (area/baricentro di triangolo + rettangolo)."""
    fcd = materiali_c25_b450c_bilineare.calcestruzzo.fcd_MPa
    kx = -EPS_CU2 / H
    eps0 = kx * H / 2.0  # eps(y=-H/2) = 0, eps(y=+H/2) = -EPS_CU2 esattamente
    sezione = Sezione(contorno=forme.rettangolo(B, H), materiali=materiali_c25_b450c_bilineare)

    n_atteso_N = B * fcd * H * 0.75  # 1/2*fcd*(H/2)*B [triangolo] + fcd*(H/2)*B [rettangolo]
    m_atteso_Nmm = B * fcd * H ** 2 / 12.0  # ricavato a mano: ∫|σ(y)|·y dy, vedi docstring del task

    r = risultante_sezione(sezione, eps0, kx, 0.0)
    assert kn_to_n(r.n_kN) == pytest.approx(n_atteso_N, rel=1e-3)
    assert knm_to_nmm(r.mx_kNm) == pytest.approx(m_atteso_Nmm, rel=1e-3)
    assert r.my_kNm == pytest.approx(0.0, abs=1e-6)


def test_sezione_simmetrica_my_zero_per_asse_neutro_orizzontale(materiali_c25_b450c) -> None:
    barre = _barre_4()
    sezione = _sezione_rettangolare(materiali_c25_b450c, barre)
    r = risultante_sezione(sezione, -0.0015, -0.000006, 0.0)
    assert r.my_kNm == pytest.approx(0.0, abs=1e-6)


def test_rotazione_90_gradi_scambia_mx_my(materiali_c25_b450c) -> None:
    barre = forme.fila_superiore(B, H, 30.0, 3, 16.0)  # asimmetriche (solo lembo superiore)
    sezione = _sezione_rettangolare(materiali_c25_b450c, barre)
    eps0, kx, ky = -0.0015, -0.000004, 0.0000015
    originale = risultante_sezione(sezione, eps0, kx, ky)

    contorno_ruotato = geometria.ruota(sezione.contorno, math.pi / 2.0)
    barre_ruotate = tuple(
        Barra(x_mm=-b.y_mm, y_mm=b.x_mm, diametro_mm=b.diametro_mm) for b in barre
    )
    sezione_ruotata = Sezione(contorno=contorno_ruotato, barre=barre_ruotate, materiali=materiali_c25_b450c)
    ruotato = risultante_sezione(sezione_ruotata, eps0, -ky, kx)

    assert ruotato.n_kN == pytest.approx(originale.n_kN, rel=1e-6)
    assert ruotato.mx_kNm == pytest.approx(-originale.my_kNm, rel=1e-6, abs=1e-9)
    assert ruotato.my_kNm == pytest.approx(originale.mx_kNm, rel=1e-6, abs=1e-9)


def test_scala_k_scala_n_k2_e_m_k3(materiali_c25_b450c) -> None:
    barre = forme.fila_superiore(B, H, 30.0, 3, 16.0)
    sezione = _sezione_rettangolare(materiali_c25_b450c, barre)
    eps0, kx, ky = -0.0015, -0.000004, 0.0
    base = risultante_sezione(sezione, eps0, kx, ky)

    k = 2.0
    contorno_scalato = tuple((x * k, y * k) for x, y in sezione.contorno)
    barre_scalate = tuple(Barra(x_mm=b.x_mm * k, y_mm=b.y_mm * k, diametro_mm=b.diametro_mm * k) for b in barre)
    sezione_scalata = Sezione(contorno=contorno_scalato, barre=barre_scalate, materiali=materiali_c25_b450c)
    scalato = risultante_sezione(sezione_scalata, eps0, kx / k, ky / k)

    assert scalato.n_kN == pytest.approx(base.n_kN * k ** 2, rel=1e-3)
    assert scalato.mx_kNm == pytest.approx(base.mx_kNm * k ** 3, rel=1e-3)


def test_raffinamento_strisce_converge(materiali_c25_b450c) -> None:
    """Poligono curvo (cerchio 48 lati) con piano di deformazione obliquo: il risultato con poche
    strisce e con 200 strisce concorda entro l'1e-3 relativo."""
    sezione = Sezione(contorno=forme.cerchio(400.0, 48), materiali=materiali_c25_b450c)
    eps0, kx, ky = -0.0012, -0.000006, 0.000004
    grezzo = risultante_sezione(sezione, eps0, kx, ky, n_strip_max=50)
    fine = risultante_sezione(sezione, eps0, kx, ky, n_strip_max=200)
    assert grezzo.n_kN == pytest.approx(fine.n_kN, rel=1e-3)
    assert grezzo.mx_kNm == pytest.approx(fine.mx_kNm, rel=1e-3, abs=1e-6)
    assert grezzo.my_kNm == pytest.approx(fine.my_kNm, rel=1e-3, abs=1e-6)


def test_bara_bilineare_incrudimento_oltre_snervamento(materiali_c25_b450c) -> None:
    """Una barra sola in trazione oltre εyd con legge bilineare: N interno coerente con σ = k·fyd
    a εud (verifica indiretta della legge bilineare passata attraverso l'integrazione)."""
    materiali = materiali_c25_b450c.model_copy(update={"legge_acciaio": "bilineare"})
    barra = Barra(x_mm=0.0, y_mm=0.0, diametro_mm=16.0)
    sezione = Sezione(contorno=forme.rettangolo(B, H), barre=(barra,), materiali=materiali)
    k = materiali.acciaio.ftk_MPa / materiali.acciaio.fyk_MPa
    r = risultante_sezione(sezione, eps_ud(), 0.0, 0.0)
    atteso_N_kN = -k * materiali.acciaio.fyd_MPa * barra.area_mm2 / 1000.0
    assert r.n_kN == pytest.approx(atteso_N_kN, rel=1e-6)


def test_timing_singola_valutazione_rettangolo(materiali_c25_b450c) -> None:
    """Vincolo di prestazione: < 2 ms a valutazione (limite generoso nel test per evitare
    fragilità in CI, verificato manualmente < 2 ms in locale)."""
    barre = _barre_4()
    sezione = _sezione_rettangolare(materiali_c25_b450c, barre)
    inizio = time.perf_counter()
    for _ in range(20):
        risultante_sezione(sezione, -0.0015, -0.000004, 0.0000015)
    durata_media_s = (time.perf_counter() - inizio) / 20.0
    assert durata_media_s < 0.05
