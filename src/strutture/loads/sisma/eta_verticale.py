"""NTC 2018 §7.3.3.2 — fattore di correzione per smorzamento della componente verticale η,v.

Sisma!I45 (labelled "coefficiente dissipativo delle costruzioni") is actually computed as `=1/I44`,
i.e. the reciprocal of q,v — not a damping-correction factor at all, and not a function of ξ. This
is the sheet's dead/mislabeled cell noted in `docs/specs/sisma.md` §7 item 2. See
`docs/divergences/sisma.md`.
"""
from strutture.shared.divergences import legacy

from .smorzamento import smorzamento_eta


def eta_verticale(xi_pct: float, qv: float, *, legacy_compat: bool) -> float:
    """η,v: legacy mode reproduces Sisma!I45 = 1/q,v. Fixed mode uses the same η(ξ) formula as the
    horizontal component (Sisma!I38) — NTC2018 assumes ξ=5% for both components unless stated
    otherwise, so η,v is the same viscous-damping correction, not q,v's reciprocal."""
    if legacy("sisma/eta-verticale-reciproco-di-qv", legacy_compat):
        return 1.0 / qv
    return smorzamento_eta(xi_pct)
