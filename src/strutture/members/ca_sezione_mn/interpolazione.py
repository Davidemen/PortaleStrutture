"""Step: read the resistant moment off an already-traced M-N domain instead of asking the engine to
re-solve it for every row of the `azioni` table.

`shared.sezione_ca.domini.m_rd` is exact but costs one bisection per call (~12 ms measured on a
representative test section, both directions ~24 ms); with up to 500 rows on 2 axes that is ~12-24 s
on its own — well over the 5 s/500-row budget (docs/BUILD_CONTRACT.md "Batch 2"). Instead the domain
is traced ONCE per axis (`dominio_nm`, already needed for the chart output) and every row just
interpolates on it; `compose.py` then re-resolves ONLY the governing row exactly
(`capacita.riga_azione_esatta`), since that is the one number the pass/fail check depends on
(finding ALTO: linear interpolation on the default `n_punti=72` trace can under-estimate `M_Rd` by
several percent near a pivot-domain kink — `compose.py` traces at a higher `n_punti` for that
reason too, see `N_PUNTI_DOMINIO`).

This is deliberately conservative, not merely "close enough": `docs/architecture-phase4.md` §A's own
verification plan asserts the domain is convex, so the straight chord between two points already ON
the boundary lies INSIDE the true domain — linear interpolation can only under-estimate the resistant
moment, never over-estimate it. [A] assumption, see the tool's final report."""
from itertools import pairwise

from strutture.shared.numeric import lerp
from strutture.shared.sezione_ca.domini import PuntoDominio


def _rami(dominio: tuple[PuntoDominio, ...]) -> tuple[tuple[PuntoDominio, ...], tuple[PuntoDominio, ...]]:
    """`(ramo_positivo, ramo_negativo)`, entrambi con `n_kN` crescente: `dominio_nm` costruisce la
    curva chiusa come due rami (l'angolo dell'asse neutro e il suo opposto, vedi `domini.py`), il
    primo già con N crescente, il secondo con N decrescente (va invertito)."""
    meta = len(dominio) // 2
    return dominio[:meta], tuple(reversed(dominio[meta:]))


def _interpola_ramo(ramo: tuple[PuntoDominio, ...], n_ed_kN: float) -> float | None:
    if not ramo[0].n_kN <= n_ed_kN <= ramo[-1].n_kN:
        return None
    for a, b in pairwise(ramo):
        if a.n_kN <= n_ed_kN <= b.n_kN:
            return a.m_kNm if b.n_kN == a.n_kN else lerp(n_ed_kN, a.n_kN, a.m_kNm, b.n_kN, b.m_kNm)
    return ramo[-1].m_kNm


def m_rd_da_dominio(dominio: tuple[PuntoDominio, ...], n_ed_kN: float) -> tuple[float, float] | None:
    """`(M_Rd+, M_Rd-)` a `N = n_ed_kN`, per interpolazione lineare sui punti già tracciati del
    dominio; `None` se `n_ed_kN` è fuori dal campo di validità del dominio (stessa convenzione di
    `shared.sezione_ca.verifica.verifica`)."""
    positivo, negativo = _rami(dominio)
    m_pos = _interpola_ramo(positivo, n_ed_kN)
    m_neg = _interpola_ramo(negativo, n_ed_kN)
    if m_pos is None or m_neg is None:
        return None
    return m_pos, m_neg
