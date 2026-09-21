"""Bending resistance with high-shear reduction (column-check!G31/G41, D33/D43 — EN1993-1-1 §6.2.5/6.2.8).

New divergence (found by direct cell-formula inspection, not previously listed in
docs/architecture.md §6): `D33` (MRd,y only — `D43`/MRd,z does not) divides the already-gammaM0
-embedded `fy'` (G31, itself `fyd = fyk/gammaM0`, reduced for shear) by `H12` (gammaM0) a *second*
time — a double application of gammaM0, invisible while gammaM0=1 (the sheet's own bugged default,
see `materiale.py`) but wrong as soon as gammaM0 is corrected to 1.05. The sheet's own `AD35`
(used everywhere else, e.g. the Annex A interaction and the simplified checks) does not
double-divide, and neither does `D43` — confirming `D33` alone is the outlier. Fixed behaviour
drops the extra division; legacy reproduces it. See docs/divergences/acciaio-colonna-ec3.md.

Fixed divergence (docs/divergences/acciaio-colonna-ec3.md): the high-shear trigger for `MRd,y`
compares `Vz,sd` (wings) against the *web* capacity `Vpl,Rd,web`, while the reduction factor itself
uses `Vy,sd`/`Vpl,Rd,web` (mirrored for `MRd,z`) — the same trigger/reduction axis swap already
fixed for `J26`/`J36` in `taglio.py`. EN1993-1-1 §6.2.8(2)-(3) requires the SAME VEd and Vpl,Rd in
both the trigger and rho = (2*VEd/Vpl,Rd - 1)^2. Fixed mode uses one shear per axis; legacy
reproduces the swap.
"""
from strutture.shared.report import Check

from .results import Flessione


def fy_ridotta_MPa(taglio_condizione_kN: float, taglio_riduzione_kN: float, vpl_rd_kN: float, fyd_MPa: float) -> float:
    """column-check!G31/G41 — fy' unreduced if the trigger shear < 0.5*Vpl,Rd, else EC3 §6.2.8(3)."""
    if taglio_condizione_kN < 0.5 * vpl_rd_kN:
        return fyd_MPa
    return (1.0 - (2.0 * taglio_riduzione_kN / vpl_rd_kN - 1.0) ** 2) * fyd_MPa


def mrd_y_kNm(classe_num: int, wel_y_mm3: float, wpl_y_mm3: float, fy_ridotta_MPa: float, gamma_m0: float, *, legacy_compat: bool) -> float:
    """column-check!D33 — MRd,y = W*fy'/gammaM0; legacy reproduces the extra /gammaM0 (see module docstring)."""
    modulo = wpl_y_mm3 if classe_num < 3 else wel_y_mm3
    valore = modulo * fy_ridotta_MPa / 1_000_000.0
    return valore / gamma_m0 if legacy_compat else valore


def mrd_z_kNm(classe_num: int, wel_z_mm3: float, wpl_z_mm3: float, fy_ridotta_MPa: float) -> float:
    """column-check!D43 — MRd,z = W*fy' (no extra division, unlike D33 — see module docstring)."""
    modulo = wpl_z_mm3 if classe_num < 3 else wel_z_mm3
    return modulo * fy_ridotta_MPa / 1_000_000.0


def costruisci_flessione(
    *,
    classe_num: int,
    wel_y_mm3: float,
    wpl_y_mm3: float,
    wel_z_mm3: float,
    wpl_z_mm3: float,
    fyd_MPa: float,
    gamma_m0: float,
    vy_sd_kN: float,
    vz_sd_kN: float,
    vpl_rd_anima_kN: float,
    vpl_rd_ali_kN: float,
    my_sd_kNm: float,
    mz_sd_kNm: float,
    legacy_compat: bool,
) -> Flessione:
    if legacy_compat:
        fy_y = fy_ridotta_MPa(vz_sd_kN, vy_sd_kN, vpl_rd_anima_kN, fyd_MPa)
        fy_z = fy_ridotta_MPa(vy_sd_kN, vz_sd_kN, vpl_rd_ali_kN, fyd_MPa)
    else:
        fy_y = fy_ridotta_MPa(vy_sd_kN, vy_sd_kN, vpl_rd_anima_kN, fyd_MPa)
        fy_z = fy_ridotta_MPa(vz_sd_kN, vz_sd_kN, vpl_rd_ali_kN, fyd_MPa)
    mrd_y = mrd_y_kNm(classe_num, wel_y_mm3, wpl_y_mm3, fy_y, gamma_m0, legacy_compat=legacy_compat)
    mrd_z = mrd_z_kNm(classe_num, wel_z_mm3, wpl_z_mm3, fy_z)
    return Flessione(
        fy_ridotta_y_MPa=fy_y,
        fy_ridotta_z_MPa=fy_z,
        mrd_y_kNm=mrd_y,
        mrd_z_kNm=mrd_z,
        verifica_y=Check(
            name="MRd,y", passed=mrd_y > my_sd_kNm, detail=f"MRd,y={mrd_y:.3f} kNm > My,sd={my_sd_kNm:.3f} kNm",
            clause="EN1993-1-1 §6.2.5", value=my_sd_kNm, limit=mrd_y, unit="kNm",
        ),
        verifica_z=Check(
            name="MRd,z", passed=mrd_z > mz_sd_kNm, detail=f"MRd,z={mrd_z:.3f} kNm > Mz,sd={mz_sd_kNm:.3f} kNm",
            clause="EN1993-1-1 §6.2.5", value=mz_sd_kNm, limit=mrd_z, unit="kNm",
        ),
    )
