"""Strip integration of a strain plane over a `Sezione` (`docs/architecture-phase4.md` §A).

Strain plane: `ε(x, y) = ε0 + κx·y − κy·x`, same tension-positive sign convention as `leggi.py`.
Lines of constant `f(x, y) = κx·y − κy·x` are parallel to the neutral axis (`ε = 0` where
`f = -ε0`); strips of constant `f` are therefore **perpendicular to the neutral axis**, exactly
as the architecture specifies. Each strip's area/centroid come from exact polygon clipping
(`geometria.taglia_semipiano`, twice, cutting a band); the material law is Simpson-integrated
across the strip depth (samples at its two edges + midpoint) — exact along the strip's length
since strain does not vary there, refined across the (thin) strip thickness by `n_strip`.

Bars are point areas: steel stress minus the concrete stress that the bar's area displaces.

**Reported sign convention**: this module accumulates N, Mx, My internally in the tension-positive
convention (so a fully-compressed section sums to N_internal < 0), then negates the whole triple
once at the end — giving N > 0 for compression and M > 0 for tension at the bottom fibre (min y),
matching `docs/architecture-phase4.md` §A. Units: strains dimensionless, stresses MPa (N/mm²),
geometry mm — the module computes in N / N·mm and converts to kN / kNm only in the public result.
"""
from math import hypot

from strutture.shared.units import n_to_kn, nmm_to_knm

from .geometria import Poligono, area, area_e_centroide, taglia_semipiano
from .leggi import legge_acciaio, legge_calcestruzzo
from .modelli import Barra, Risultante, Sezione

N_STRIP_DEFAULT = 200
N_STRIP_INIZIALE = 25
TOLLERANZA_RELATIVA_DEFAULT = 1e-4


def epsilon(eps0: float, kx: float, ky: float, x_mm: float, y_mm: float) -> float:
    """ε(x, y) = ε0 + κx·y − κy·x."""
    return eps0 + kx * y_mm - ky * x_mm


def _fascia(poligono: Poligono, kx: float, ky: float, d_min: float, d_max: float) -> Poligono:
    """Sub-poligono dove `d_min <= κx·y − κy·x <= d_max` (taglio con due semipiani)."""
    tagliato = taglia_semipiano(poligono, -ky, kx, -d_max)
    return taglia_semipiano(tagliato, ky, -kx, d_min)


def _zona_compressa(contorno: Poligono, eps0: float, kx: float, ky: float) -> Poligono:
    """Sub-poligono dove ε(x, y) < 0 (compresso; il cls in trazione è ignorato)."""
    if kx == 0.0 and ky == 0.0:
        return contorno if eps0 < 0.0 else ()
    return taglia_semipiano(contorno, -ky, kx, eps0)


def _risultante_calcestruzzo(
    contorno: Poligono, legge_cls, eps0: float, kx: float, ky: float, n_strip: int,
) -> tuple[float, float, float]:
    """(N, Mx, My) interni del solo calcestruzzo."""
    zona = _zona_compressa(contorno, eps0, kx, ky)
    if len(zona) < 3 or area(zona) <= 0.0:
        return 0.0, 0.0, 0.0
    kappa = hypot(kx, ky)
    if kappa == 0.0:
        _, cx, cy = area_e_centroide(zona)
        forza = legge_cls(eps0) * area(zona)
        return forza, forza * cy, -forza * cx
    f_vals = [kx * y - ky * x for x, y in zona]
    f_min, f_max = min(f_vals), max(f_vals)
    if f_max <= f_min:
        _, cx, cy = area_e_centroide(zona)
        forza = legge_cls(eps0 + f_min) * area(zona)
        return forza, forza * cy, -forza * cx
    return _somma_strisce(zona, legge_cls, eps0, kx, ky, f_min, f_max, n_strip)


def _somma_strisce(
    zona: Poligono, legge_cls, eps0: float, kx: float, ky: float, f_min: float, f_max: float, n_strip: int,
) -> tuple[float, float, float]:
    passo = (f_max - f_min) / n_strip
    n_tot = mx_tot = my_tot = 0.0
    for i in range(n_strip):
        d_lo, d_hi = f_min + i * passo, f_min + (i + 1) * passo
        striscia = _fascia(zona, kx, ky, d_lo, d_hi)
        a_striscia = area(striscia)
        if a_striscia <= 0.0:
            continue
        _, cx, cy = area_e_centroide(striscia)
        sigma_media = (legge_cls(eps0 + d_lo) + 4.0 * legge_cls(eps0 + (d_lo + d_hi) / 2.0) + legge_cls(eps0 + d_hi)) / 6.0
        forza = sigma_media * a_striscia
        n_tot += forza
        mx_tot += forza * cy
        my_tot += -forza * cx
    return n_tot, mx_tot, my_tot


def _risultante_barre(
    barre: tuple[Barra, ...], legge_acc, legge_cls, eps0: float, kx: float, ky: float,
) -> tuple[float, float, float]:
    """(N, Mx, My) interni delle barre (tensione acciaio meno cls spostato)."""
    n_tot = mx_tot = my_tot = 0.0
    for barra in barre:
        eps = epsilon(eps0, kx, ky, barra.x_mm, barra.y_mm)
        forza = (legge_acc(eps) - legge_cls(eps)) * barra.area_mm2
        n_tot += forza
        mx_tot += forza * barra.y_mm
        my_tot += -forza * barra.x_mm
    return n_tot, mx_tot, my_tot


def _valuta(sezione: Sezione, eps0: float, kx: float, ky: float, n_strip: int) -> tuple[float, float, float]:
    legge_cls = legge_calcestruzzo(sezione.materiali)
    legge_acc = legge_acciaio(sezione.materiali)
    nc, mxc, myc = _risultante_calcestruzzo(sezione.contorno, legge_cls, eps0, kx, ky, n_strip)
    nb, mxb, myb = _risultante_barre(sezione.barre, legge_acc, legge_cls, eps0, kx, ky)
    return nc + nb, mxc + mxb, myc + myb


def _convergente(a: tuple[float, float, float], b: tuple[float, float, float], tolleranza: float) -> bool:
    return all(abs(x - y) <= tolleranza * max(1.0, abs(x), abs(y)) for x, y in zip(a, b, strict=True))


def risultante_sezione(
    sezione: Sezione,
    eps0: float,
    kx: float,
    ky: float,
    *,
    n_strip_max: int = N_STRIP_DEFAULT,
    tolleranza_relativa: float = TOLLERANZA_RELATIVA_DEFAULT,
) -> Risultante:
    """Integra il piano di deformazione ε0 + κx·y − κy·x su `sezione`, raffinando il numero di
    strisce (a partire da 25, raddoppiando) finché ΔN e ΔM relativi non scendono sotto
    `tolleranza_relativa` (o si raggiunge `n_strip_max`, default 200)."""
    n = min(N_STRIP_INIZIALE, n_strip_max)
    stato = _valuta(sezione, eps0, kx, ky, n)
    while n < n_strip_max:
        n_succ = min(n * 2, n_strip_max)
        stato_succ = _valuta(sezione, eps0, kx, ky, n_succ)
        convergenza = _convergente(stato, stato_succ, tolleranza_relativa)
        n, stato = n_succ, stato_succ
        if convergenza:
            break
    n_int, mx_int, my_int = stato
    return Risultante(
        n_kN=n_to_kn(-n_int), mx_kNm=nmm_to_knm(-mx_int), my_kNm=nmm_to_knm(-my_int), n_strisce=n,
    )
