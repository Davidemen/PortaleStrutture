"""Step: sliding safety factor (docs/specs/fond-plinti-isolati.md Tool-1 step 12, `CHECKS!AJ:AM`).

Fix 1 (docs/architecture-batch2.md §7 `plinti-isolati AM`): the sheet returns the text ">100" both
when the ratio genuinely exceeds 100 and when there is no shear demand (S=0, IFERROR branch) —
undistinguishable from a safe result. Here S=0 reports `None` (no demand, `senza_domanda`),
`legacy_compat=True` keeps the sheet's `100.0` stand-in so oracle numbers still match.

Fix 2 (CRITICAL, review finding): the sheet (and this module, before the fix) compared the raw
ratio N*tan(phi')/S against 1.0 and stamped the result "NTC2018 §6.4.3.1" — but NTC2018 Tab. 6.4.I
(Approccio 2, A1+M1+R3) requires the *resistance* Rd = N*tan(delta)/gammaR with gammaR=1.1 (gammaphi'=1
under M1, the whole reduction sits in gammaR), so a combination with 1.0 <= ratio < 1.1 is a real
FAIL, not a PASS: `legacy_compat=False` now divides by `GAMMA_R_SCORRIMENTO`; `legacy_compat=True`
keeps the un-reduced ratio (sheet behaviour, `docs/divergences/plinti-isolati.md`). The interface
friction angle is still assumed equal to phi_terreno_deg (delta = phi'); exposing a separate delta
input for smooth/pre-cast bases is deferred (no shared module or input field for it yet -- see
divergence doc)."""
import math

from strutture.shared.divergences import legacy

LEGACY_NO_DEMAND_RATIO = 100.0  # sheet's IFERROR(...,100) stand-in when S=0 (division by zero).
GAMMA_R_SCORRIMENTO = 1.1  # NTC2018 Tab. 6.4.I, Approccio 2 (A1+M1+R3) - scorrimento su piano di posa.


def mu_scorrimento(n_kN: float, vx_kN: float, vy_kN: float, phi_terreno_deg: float, *,
                    legacy_compat: bool) -> float | None:
    """N*tan(phi)/(gammaR*S), S = sqrt(vx^2+vy^2), gammaR=1 (legacy) or 1.1 (fix, NTC2018 R3).
    `None` when S=0 (no shear demand); `legacy_compat=True` instead reproduces the sheet's
    IFERROR/">100" text as the numeric stand-in `100.0`."""
    s_kN = math.hypot(vx_kN, vy_kN)
    if s_kN == 0:
        return (LEGACY_NO_DEMAND_RATIO
                if legacy("plinti-isolati/scorrimento-taglio-zero-valore-fittizio", legacy_compat)
                else None)
    gamma_r = (1.0 if legacy("plinti-isolati/scorrimento-senza-fattore-parziale-gammar", legacy_compat)
               else GAMMA_R_SCORRIMENTO)
    ratio = n_kN * math.tan(math.radians(phi_terreno_deg)) / (gamma_r * s_kN)
    if (legacy("plinti-isolati/scorrimento-taglio-zero-valore-fittizio", legacy_compat)
            and ratio > LEGACY_NO_DEMAND_RATIO):
        return LEGACY_NO_DEMAND_RATIO
    return ratio
