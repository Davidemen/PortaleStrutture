"""Aspect-ratio and depth-ratio factors feeding `shared.soil_stress.steinbrenner_is`
(`docs/specs/geo-cedimenti-elastico.md` Tool 2, steps 1-5: `IS = I1 + (1-2μ)/(1-μ)·I2`, evaluated
once for the centre point (`b = 2H/B`) and once for the edge midpoint (`b = H/B`)).

Fixes the sheet's edge-midpoint bug: `P15` feeds `steinbrenner_is(a, b_bordo, mu)` straight into
the `ΔH bordo` formula, i.e. the classical Bowles CORNER-settlement factor of the whole B×L
rectangle, not the edge-MIDPOINT factor the output claims (`docs/architecture-batch2.md` §7 lists
no such entry — found independently). The true edge-midpoint factor superposes two B×(L/2)
sub-rectangles sharing the edge: `IS_bordo = 2·steinbrenner_is(a/2, b_bordo, mu)` (Bowles,
"Foundation Analysis and Design", `B'` stays the full `B` for both halves). `legacy_compat=True`
reproduces the sheet's single-rectangle corner factor."""
from strutture.shared.soil_stress import steinbrenner_is

_EDGE_MIDPOINT_SUB_RECTANGLES = 2  # two B x (L/2) sub-rectangles sharing the edge


def aspect_ratio(b_m: float, l_m: float) -> float:
    """`a = L/B` (sheet's `F6`), reused for both the centre and the edge-midpoint factor."""
    return l_m / b_m


def depth_ratio_centro(h_m: float, b_m: float) -> float:
    """`b_centro = 2H/B` (sheet's `N12`)."""
    return 2 * h_m / b_m


def depth_ratio_bordo(h_m: float, b_m: float) -> float:
    """`b_bordo = H/B` (sheet's `P12`)."""
    return h_m / b_m


def influence_factors(a: float, b_centro: float, b_bordo: float, mu: float, *, legacy_compat: bool = False) -> tuple[float, float]:
    """`(IS_centro, IS_bordo)` (sheet's `N15`, `P15`). `IS_centro` is unaffected by the bordo bug.
    `IS_bordo` uses the sheet's single-rectangle corner factor when `legacy_compat=True`, else the
    true edge-midpoint factor from 2-sub-rectangle superposition."""
    is_centro = steinbrenner_is(a, b_centro, mu)
    if legacy_compat:
        is_bordo = steinbrenner_is(a, b_bordo, mu)
    else:
        is_bordo = _EDGE_MIDPOINT_SUB_RECTANGLES * steinbrenner_is(a / 2, b_bordo, mu)
    return is_centro, is_bordo
