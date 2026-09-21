"""Spec steps 6-8, 10-12: concrete-only punching capacity at the governing perimeter found by the
scan, and the message driving whether shear reinforcement is required (spec C40)."""
from pydantic import BaseModel, ConfigDict

from strutture.shared.ec2_shear import v_rd_c as ec2_v_rd_c

from .perimeter_area import area_within_perimeter_mm2, perimeter_length_mm

GAMMA_C = 1.5

MESSAGGIO_NON_NECESSARIO = "Progetto delle armature verticali non necessario."
MESSAGGIO_NECESSARIO = "Verifica non soddisfatta: necessario il progetto delle armature verticali."


class GoverningCapacity(BaseModel):
    """Internal result of the governing-perimeter capacity check (spec steps 6-8, 10-12); assembled
    into `PerimetroCriticoOutput` together with the scan rows by `compose.py`."""

    model_config = ConfigDict(frozen=True)

    a_governante_mm: float
    ui_mm: float
    area_mm2: float
    ved_red_ui_kN: float
    v_rd_i_MPa: float
    v_ed_i_MPa: float
    rapporto: float
    armatura_necessaria: bool


def _ved_red_ui_kN(ved_kN: float, beta: float, pterreno_MPa: float, area_mm2: float, a_amanuale_mm2: float | None) -> float:
    """Sheet D36: reduced shear using MIN(A_a, A_amanuale) when a manual area override is given."""
    area_effettiva_mm2 = area_mm2 if a_amanuale_mm2 is None else min(area_mm2, a_amanuale_mm2)
    return ved_kN * beta - pterreno_MPa * area_effettiva_mm2 / 1000.0


def governing_capacity(
    ved_kN: float, beta: float, pterreno_MPa: float, lato_a_mm: float, lato_b_mm: float, diametro_mm: float,
    umanuale_mm: float | None, a_amanuale_mm2: float | None, a_governante_su_d: float, d_mm: float, k: float,
    rho: float, fck_MPa: float, *, legacy_compat: bool,
) -> GoverningCapacity:
    a_governante_mm = a_governante_su_d * d_mm
    ui_mm = perimeter_length_mm(lato_a_mm, lato_b_mm, diametro_mm, a_governante_mm, umanuale_mm)
    area_mm2 = area_within_perimeter_mm2(lato_a_mm, lato_b_mm, diametro_mm, a_governante_mm, legacy_compat=legacy_compat)
    ved_red_ui_kN = _ved_red_ui_kN(ved_kN, beta, pterreno_MPa, area_mm2, a_amanuale_mm2)
    v_rd_i_MPa = ec2_v_rd_c(k, rho, fck_MPa, 0.0, GAMMA_C, av_over_2d=2.0 * d_mm / a_governante_mm).v_rd_c_MPa
    v_ed_i_MPa = ved_red_ui_kN * 1000.0 / (ui_mm * d_mm)
    return GoverningCapacity(
        a_governante_mm=a_governante_mm, ui_mm=ui_mm, area_mm2=area_mm2, ved_red_ui_kN=ved_red_ui_kN,
        v_rd_i_MPa=v_rd_i_MPa, v_ed_i_MPa=v_ed_i_MPa, rapporto=v_ed_i_MPa / v_rd_i_MPa,
        armatura_necessaria=v_ed_i_MPa >= v_rd_i_MPa,
    )


def messaggio_esito(armatura_necessaria: bool) -> str:
    return MESSAGGIO_NECESSARIO if armatura_necessaria else MESSAGGIO_NON_NECESSARIO
