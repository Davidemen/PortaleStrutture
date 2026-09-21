"""Spec step 5: exhaustive scan of the governing control-perimeter distance a/d in [0.5, 2.0]
(sheet fill-down AO2:AX152), replaced by `shared.ec2_shear.scan_governing`. Not provably monotonic for
every input (docs/specs/ca-punzonamento.md §7.6, e.g. `pterreno>0`), so the full scan is always run."""
from strutture.shared.ec2_shear import GoverningScan, scan_governing
from strutture.shared.ec2_shear import v_rd_c as ec2_v_rd_c

from .models import RigaPerimetro
from .perimeter_area import area_within_perimeter_mm2, perimeter_length_mm
from .tables import SCAN_A_SU_D_MAX, SCAN_A_SU_D_MIN, SCAN_A_SU_D_STEP

GAMMA_C = 1.5


def _samples() -> tuple[float, ...]:
    """Same sample set `scan_governing` iterates internally, kept in sync so `righe` and the
    governing search agree on every x/a value evaluated."""
    n = round((SCAN_A_SU_D_MAX - SCAN_A_SU_D_MIN) / SCAN_A_SU_D_STEP) + 1
    return tuple(SCAN_A_SU_D_MIN + i * SCAN_A_SU_D_STEP for i in range(n))


def _row_at(
    x: float, ved_kN: float, beta: float, pterreno_MPa: float, lato_a_mm: float, lato_b_mm: float,
    diametro_mm: float, umanuale_mm: float | None, d_mm: float, k: float, rho: float, fck_MPa: float,
    *, legacy_compat: bool,
) -> RigaPerimetro:
    a_mm = x * d_mm
    ui_mm = perimeter_length_mm(lato_a_mm, lato_b_mm, diametro_mm, a_mm, umanuale_mm)
    area_mm2 = area_within_perimeter_mm2(lato_a_mm, lato_b_mm, diametro_mm, a_mm, legacy_compat=legacy_compat)
    ved_red_kN = ved_kN * beta - pterreno_MPa * area_mm2 / 1000.0
    v_rd_i_MPa = ec2_v_rd_c(k, rho, fck_MPa, 0.0, GAMMA_C, av_over_2d=2.0 * d_mm / a_mm).v_rd_c_MPa
    v_ed_i_MPa = ved_red_kN * 1000.0 / (ui_mm * d_mm)
    return RigaPerimetro(
        a_su_d=x, a_mm=a_mm, ui_mm=ui_mm, area_mm2=area_mm2, ved_red_kN=ved_red_kN,
        v_rd_i_MPa=v_rd_i_MPa, v_ed_i_MPa=v_ed_i_MPa, rapporto=v_ed_i_MPa / v_rd_i_MPa,
    )


def scan_perimetro(
    ved_kN: float, beta: float, pterreno_MPa: float, lato_a_mm: float, lato_b_mm: float,
    diametro_mm: float, umanuale_mm: float | None, d_mm: float, k: float, rho: float, fck_MPa: float,
    *, legacy_compat: bool,
) -> tuple[tuple[RigaPerimetro, ...], GoverningScan]:
    """Returns (righe, governing) where `governing.x` is the winning a/d and `governing.index` its
    0-based position in `righe`."""
    def row(x: float) -> RigaPerimetro:
        return _row_at(
            x, ved_kN, beta, pterreno_MPa, lato_a_mm, lato_b_mm, diametro_mm, umanuale_mm, d_mm, k,
            rho, fck_MPa, legacy_compat=legacy_compat,
        )

    righe = tuple(row(x) for x in _samples())
    governing = scan_governing(lambda x: row(x).rapporto, SCAN_A_SU_D_MIN, SCAN_A_SU_D_MAX, SCAN_A_SU_D_STEP)
    return righe, governing
