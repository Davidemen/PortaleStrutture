"""Spec steps 13-18: radial layout of the shear-reinforcement perimeters (EC2§9.4.3, fig. 6.22),
computed via the concrete-term already exposed by `shared.ec2_shear.v_rd_c` (no av_over_2d, no vmin
enhancement — the same `CRd,c*k*(100*rho*fck)^(1/3)` term the sheet calls out at cell D25/D26)."""
import math

from strutture.shared.ec2_shear import v_rd_c as ec2_v_rd_c
from strutture.shared.report import CalcError

SR_MAX_FACTOR = 0.75  # EC2§9.4.3(1) fig. 9.10 — max radial spacing sr,max = 0.75d
A1_MIN_FACTOR = 0.3  # EC2§9.4.3(1) — min distance of the 1st perimeter from the column face
A1_MAX_FACTOR = 0.5  # EC2§9.4.3(1) — max distance of the 1st perimeter from the column face
BU_ST_MAX_FACTOR = 1.5  # EC2§9.4.3(1) — max distance of the last row from u0,out / tangential spacing
GAMMA_C = 1.5


def u0_out_mm(ved_kN: float, beta: float, k: float, rho: float, fck_MPa: float, d_mm: float) -> float:
    """Perimeter beyond which no shear reinforcement is required (EC2§6.4.5(4))."""
    concrete_term_MPa = ec2_v_rd_c(k, rho, fck_MPa, 0.0, GAMMA_C).concrete_term_MPa
    return ved_kN * beta * 1000.0 / (concrete_term_MPa * d_mm)


def k_d_primo_mm(u0_out_mm_: float, lato_a_mm: float, lato_b_mm: float) -> float:
    """Radius beyond the column's straight sides, to reach u0,out."""
    return (u0_out_mm_ - 2.0 * (lato_a_mm + lato_b_mm)) / (2.0 * math.pi)


def radial_limits_mm(d_mm: float) -> tuple[float, float, float]:
    """(sr_max, a1_min, a1_max), all mm."""
    return SR_MAX_FACTOR * d_mm, A1_MIN_FACTOR * d_mm, A1_MAX_FACTOR * d_mm


def bu_st_limit_mm(d_mm: float) -> float:
    return BU_ST_MAX_FACTOR * d_mm


def perimeter_rows(k_d_primo_mm_: float, bu_mm: float, a1eff_mm: float, sr_max_mm: float) -> tuple[float, float, int, float]:
    """(au, au-a1, n_file, sr): distance to the last row, distance between 1st and last row, number of
    radial rows (Excel CEILING(x,1)+1 — `math.ceil` also rounds negative arguments toward +infinity,
    matching the sheet), effective spacing."""
    au_mm = k_d_primo_mm_ - bu_mm
    au_meno_a1_mm = au_mm - a1eff_mm
    n_file = math.ceil(au_meno_a1_mm / sr_max_mm) + 1
    if n_file == 1:
        raise CalcError(
            "layout delle cuciture non calcolabile: la distanza disponibile tra la prima e "
            "l'ultima fila (au-a1,eff) restituisce una sola fila, per cui l'interasse radiale "
            "sr non è definito"
        )
    sr_mm = au_meno_a1_mm / (n_file - 1)
    return au_mm, au_meno_a1_mm, n_file, sr_mm
