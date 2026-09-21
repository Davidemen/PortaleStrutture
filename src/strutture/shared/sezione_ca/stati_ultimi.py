"""Ultimate-state strain planes for the pivot method (`docs/architecture-phase4.md` §A): for a
neutral-axis angle `theta_rad`, sweep the classic three-pivot diagram (pivot A/B/C) from pure
tension to pure compression with a single monotonic parameter `t in [0, 1]`.

**Geometry.** The bending direction is `u = (-sin(theta), cos(theta))`; every point's position
along it is `p(x, y) = y*cos(theta) - x*sin(theta)`, so `eps0 + kx*y - ky*x = eps0 + kappa*p` when
`kx = kappa*cos(theta)`, `ky = kappa*sin(theta)`. `p_min`/`p_max` are the concrete outline's
extremes along that direction: `p_max` is always the compression-side extreme fibre, `p_min` the
tension side (this module's own choice of sign, independent of any input curvature sign).

**Pivot points** — the strain profile is described by its two extreme-fibre values `(eps_bot @
p_min, eps_top @ p_max)`, piecewise-linear in `t` across 4 vertices:
1. `t=0` — pure tension: `eps_bot = eps_top = eps_ud` (uniform, steel at its ultimate design
   strain everywhere, concrete ignored in tension) -> `N = -fyd*As` exactly.
2. pivot A -> pivot B transition: "pivot A" holds the strain AT THE MOST-TENSIONED BAR (not the
   concrete edge `p_min`) fixed at `eps_ud`, while `eps_top` sweeps `eps_ud -> -eps_cu` (`eps_cu`
   from the selected concrete law). Let `p_a` be that bar's projection and
   `a = (p_a - p_min) / (p_max - p_min)` its fraction of `h` from the tension edge (`a = 0`, i.e.
   pivot at `p_min`, for an unreinforced outline). Solving `eps(p_a) = eps_bot*(1-a) + eps_top*a =
   eps_ud` for `eps_bot` (the value the LINE through `p_min`/`p_max` must have at `p_min` to meet
   that condition) gives `eps_bot = (eps_ud + eps_cu*a) / (1 - a)`; at `a=0` this is `eps_ud`,
   recovering the old (unreinforced-outline) anchor.
3. pivot B -> pivot C transition: `eps_top = -eps_cu` (fixed, "pivot B": rotation about the
   compression edge held at the concrete ultimate strain), `eps_bot` sweeps down to the value that
   makes the point at `p_c = p_min + (eps_c/eps_cu)*h` ("point C", `eps_c/eps_cu` from the TENSION
   edge, equivalently `1 - eps_c/eps_cu` from the compressed edge) read exactly `-eps_c`. Writing
   `s = eps_c/eps_cu` and `eps(p_c) = eps_bot*(1-s) + eps_top*s = -eps_c` with `eps_top = -eps_cu`:
   `eps_bot*(1-s) = -eps_c - (-eps_cu)*s = -eps_c + eps_cu*s = -eps_c + eps_c = 0` (since
   `eps_cu*s = eps_cu*(eps_c/eps_cu) = eps_c` identically) -> `eps_bot = 0` EXACTLY, for any
   `eps_c`/`eps_cu` pair: the B/C transition is geometrically the state where the neutral axis
   sits exactly on the tension edge (`x = h`), independent of the concrete law's numbers.
4. `t=1` — pure compression: `eps_bot = eps_top = -eps_c` (uniform, concrete on its plateau
   everywhere) -> `N = fcd*Ac + fyd*As` exactly ("pivot C": for `t` between steps 3 and 4, point C
   stays fixed at `-eps_c` while `eps_top` sweeps `-eps_cu -> -eps_c`, ending in this uniform
   state).

`(eps_c, eps_cu)` are `(EPS_C2, EPS_CU2)` for the parabola-rectangle law and `(EPS_C3, EPS_CU3)`
for the bilinear law (NTC2018 §4.1.2.1.2.1 Fig. 4.1.2.1.2.1b), selected from
`sezione.materiali.legge_calcestruzzo`.

For the elastic-perfectly-plastic steel law (`leggi.sigma_acciaio_elastico_perfettamente_plastico`,
"unlimited strain") `eps_ud` is not a real ductility limit: the law already plateaus at `fyd` well
before `eps_ud`, so step-2 states with `eps(p_a) = eps_ud` give the same `N`/`M` as any other
already-yielded value would — the domain is, for that law, effectively governed by the concrete
pivots B/C alone (as the architecture states); using `eps_ud` as the fixed value is still correct
and harmless because BOTH `leggi.py` laws clamp `|eps| <= eps_ud` internally.
"""
from math import cos, sin

from strutture.shared.numeric import clamp

from .integrazione import risultante_sezione
from .leggi import EPS_C2, EPS_C3, EPS_CU2, EPS_CU3, EPS_UK_B450C, eps_ud
from .modelli import Risultante, Sezione

N_REGIONI_PIVOT = 3  # trazione pura -> A/B -> B/C -> compressione pura: 3 tratti lineari in t.
_FRAZIONE_A_MAX = 1.0 - 1e-9  # guardia numerica: evita la divisione per zero se la barra è sul lembo compresso.


def _proiezione(x_mm: float, y_mm: float, theta_rad: float) -> float:
    """`p(x, y) = y*cos(theta) - x*sin(theta)`, coordinata lungo la direzione di flessione."""
    return y_mm * cos(theta_rad) - x_mm * sin(theta_rad)


def _estremi_proiezione(sezione: Sezione, theta_rad: float) -> tuple[float, float]:
    """`(p_min, p_max)` del contorno in cls lungo `theta_rad` (lembo teso, lembo compresso)."""
    proiezioni = [_proiezione(x, y, theta_rad) for x, y in sezione.contorno]
    return min(proiezioni), max(proiezioni)


def _proiezione_barra_piu_tesa(sezione: Sezione, theta_rad: float, p_min: float) -> float:
    """Proiezione della barra più tesa lungo `theta_rad` (ancora del pivot A); `p_min` (lembo cls)
    se la sezione non ha armatura."""
    if not sezione.barre:
        return p_min
    return min(_proiezione(b.x_mm, b.y_mm, theta_rad) for b in sezione.barre)


def _deformazioni_pivot_calcestruzzo(legge_calcestruzzo: str) -> tuple[float, float]:
    """`(eps_c, eps_cu)` della legge cls selezionata: parabola-rettangolo -> `(EPS_C2, EPS_CU2)`,
    bilineare -> `(EPS_C3, EPS_CU3)` (NTC2018 §4.1.2.1.2.1 Fig. 4.1.2.1.2.1b)."""
    if legge_calcestruzzo == "bilineare":
        return EPS_C3, EPS_CU3
    return EPS_C2, EPS_CU2


def _vertici_pivot(
    sezione: Sezione, theta_rad: float, eps_uk_mm_per_mm: float,
) -> tuple[tuple[float, float], ...]:
    """4 vertici `(eps_bot, eps_top)` che delimitano le 3 regioni A/B/C (derivazione nel modulo)."""
    eud = eps_ud(eps_uk_mm_per_mm)
    eps_c, eps_cu = _deformazioni_pivot_calcestruzzo(sezione.materiali.legge_calcestruzzo)
    p_min, p_max = _estremi_proiezione(sezione, theta_rad)
    p_a = _proiezione_barra_piu_tesa(sezione, theta_rad, p_min)
    a = clamp((p_a - p_min) / (p_max - p_min), 0.0, _FRAZIONE_A_MAX)
    eps_bot_ab = (eud + eps_cu * a) / (1.0 - a)
    return ((eud, eud), (eps_bot_ab, -eps_cu), (0.0, -eps_cu), (-eps_c, -eps_c))


def _profilo_deformazioni(
    sezione: Sezione, theta_rad: float, t: float, eps_uk_mm_per_mm: float,
) -> tuple[float, float]:
    """`(eps_bot, eps_top)` per il parametro monotono `t in [0, 1]` (interpolazione lineare a
    tratti sui 4 vertici pivot)."""
    t = clamp(t, 0.0, 1.0)
    vertici = _vertici_pivot(sezione, theta_rad, eps_uk_mm_per_mm)
    posizione = t * N_REGIONI_PIVOT
    indice = min(int(posizione), N_REGIONI_PIVOT - 1)
    frazione = posizione - indice
    eps_bot0, eps_top0 = vertici[indice]
    eps_bot1, eps_top1 = vertici[indice + 1]
    return (
        eps_bot0 + (eps_bot1 - eps_bot0) * frazione,
        eps_top0 + (eps_top1 - eps_top0) * frazione,
    )


def stato_pivot(
    sezione: Sezione, theta_rad: float, t: float, eps_uk_mm_per_mm: float = EPS_UK_B450C,
) -> tuple[float, float, float]:
    """`(eps0, kx, ky)` del piano di deformazione pivot per l'angolo `theta_rad` e il parametro
    monotono `t in [0, 1]` (0 = trazione pura, 1 = compressione pura)."""
    eps_bot, eps_top = _profilo_deformazioni(sezione, theta_rad, t, eps_uk_mm_per_mm)
    p_min, p_max = _estremi_proiezione(sezione, theta_rad)
    kappa = (eps_top - eps_bot) / (p_max - p_min)
    kx, ky = kappa * cos(theta_rad), kappa * sin(theta_rad)
    eps0 = eps_bot - kappa * p_min
    return eps0, kx, ky


def risultante_pivot(
    sezione: Sezione, theta_rad: float, t: float, eps_uk_mm_per_mm: float = EPS_UK_B450C,
) -> Risultante:
    """`(N, Mx, My)` dello stato pivot `(theta_rad, t)`, via l'integrazione della Parte 1."""
    eps0, kx, ky = stato_pivot(sezione, theta_rad, t, eps_uk_mm_per_mm)
    return risultante_sezione(sezione, eps0, kx, ky)

