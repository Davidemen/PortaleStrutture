"""Shear resistance (column-check!G26, G36 — EN1993-1-1 §6.2.6(2)).

New divergence (found by direct cell-formula inspection): the pass/fail checks `J26`/`J36`
actually compare each capacity against the *other* axis's demand — `J26` ("web" check) tests
`G26 > J23` (Vz,sd, the wings' shear) instead of `J22` (Vy,sd, the web's own shear), and `J36`
("wing" check) tests `G36 > J22` instead of `J23`. The adjacent ratio-text cells `K26`/`K36` (same
rows) use the *correct*, non-swapped reference, and the spec's own §3 output table documents the
intended (non-swapped) pairing — both corroborate that the boolean checks are the outlier, not the
messages. Fixed behaviour compares each capacity against its own axis's demand; legacy reproduces
the swap. See docs/divergences/acciaio-colonna-ec3.md.
"""
import math

from strutture.shared.divergences import legacy
from strutture.shared.report import Check
from strutture.shared.units import n_to_kn

from .results import Taglio


def vpl_rd_kN(av_mm2: float, fyd_MPa: float) -> float:
    """column-check!G26/G36 — Vpl,Rd = Av*fyd/sqrt(3)."""
    return n_to_kn(av_mm2 * fyd_MPa / math.sqrt(3.0))


def costruisci_taglio(
    *, av_z_mm2: float, av_y_mm2: float, fyd_MPa: float, vy_sd_kN: float, vz_sd_kN: float, legacy_compat: bool
) -> Taglio:
    vpl_anima = vpl_rd_kN(av_z_mm2, fyd_MPa)
    vpl_ali = vpl_rd_kN(av_y_mm2, fyd_MPa)
    domanda_anima, domanda_ali = (
        (vz_sd_kN, vy_sd_kN) if legacy("acciaio-colonna-ec3/verifica-taglio-assi-scambiati", legacy_compat)
        else (vy_sd_kN, vz_sd_kN)
    )
    return Taglio(
        vpl_rd_anima_kN=vpl_anima,
        vpl_rd_ali_kN=vpl_ali,
        verifica_anima=Check(
            name="Vpl,Rd anima", passed=vpl_anima > domanda_anima,
            detail=f"Vpl,Rd={vpl_anima:.3f} kN > V={domanda_anima:.3f} kN",
            clause="EN1993-1-1 §6.2.6(2)", value=domanda_anima, limit=vpl_anima, unit="kN",
        ),
        verifica_ali=Check(
            name="Vpl,Rd ali", passed=vpl_ali > domanda_ali,
            detail=f"Vpl,Rd={vpl_ali:.3f} kN > V={domanda_ali:.3f} kN",
            clause="EN1993-1-1 §6.2.6(2)", value=domanda_ali, limit=vpl_ali, unit="kN",
        ),
    )
