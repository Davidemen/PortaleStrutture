"""Punching-shear check for `pav-carichi-concentrati` (spec calculation steps 7-10; EC2 §6.4-style).
Divergence (architecture-batch2.md §7 `pavimento M33/N33`, spec bug 2): the sheet's 2d-offset control
perimeter `u1` uses the total thickness `h` for the edge/corner (`bordo`/`spigolo`) positions instead
of the effective depth `d` (already used correctly for `centro`) -- EC2 §6.4.2 always uses `d`. Using
`h` (200 mm) instead of `d` (170 mm) oversizes `u1` by ~18%, understating `vEd1` and non-conservatively
passing the check. `legacy_compat=True` reproduces the sheet; `False` uses `d` for every position.
Reuses `shared.ec2_shear.control_perimeter` for `u0` (all positions) and `centro`'s `u1` (both match
the standard rounded-rectangle formula exactly); `bordo`/`spigolo` keep the sheet's own reduced-
perimeter shape (not a column surrounded on all sides, so the generic formula does not apply)."""
import math

from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.ec2_shear import control_perimeter
from strutture.shared.ec2_shear.v_rd_max import V_RD_MAX_COEFF_A1_2014
from strutture.shared.report import Check

from .carico_row import PosizioneCarico
from .tables import BETA_PUNZONAMENTO

FACE_PERIMETER_DIST_MM = 0.0
CONTROL_PERIMETER_OFFSET_FACTOR = 2.0  # EC2 §6.4.2: u1 at distance 2d from the load face.
# spec step 8: VRd,max = 0.5*v1*fcd. This 0.5 is the sheet's own NTC2018 §4.1.2.3.5.2 value, NOT the
# EC2 §6.4.5(3) coefficient (an explicit user choice in the code-standard branch, `coeff_vrd_max` on
# `PavimentoIndustrialeInput`: 0.4 EN 1992-1-1/A1:2014 default, or 0.5 EN 1992-1-1:2004 + Appendice
# Nazionale italiana). Kept only under `legacy_compat=True` to reproduce the sheet
# (docs/divergences/pavimento-industriale.md).
VRD_MAX_COEFFICIENT_NTC = 0.5
VRD_MAX_CLAUSE_LEGACY = "NTC2018 §4.1.2.3.5.2"
VRD_MAX_CLAUSE_FIXED = "EC2 §6.4.5(3)"


class PunzonamentoResult(BaseModel):
    """`pav-carichi-concentrati` outputs L28/L29-N29, L30-N36 (punching shear at u0 and u1)."""

    model_config = ConfigDict(frozen=True)

    v_ed_kN: float = Field(description="Azione di taglio per punzonamento VEd = P_SLU*β", gt=0, json_schema_extra={"unit": "kN", "symbol": "V_Ed"})
    u0_mm: float = Field(description="Perimetro di verifica a filo pilastro/impronta u0", gt=0, json_schema_extra={"unit": "mm", "symbol": "u_0"})
    v_rd_max_MPa: float = Field(
        description="Tensione massima di punzonamento VRd,max = coeff*ν1*fcd (coeff=0.5 NTC2018 in "
        "modalità foglio, oppure il valore scelto in 'coeff_vrd_max' in modalità standard)",
        gt=0, json_schema_extra={"unit": "MPa", "symbol": "V_Rd,max"},
    )
    v_ed0_MPa: float = Field(description="Tensione di punzonamento a u0", gt=0, json_schema_extra={"unit": "MPa", "symbol": "v_Ed0"})
    verifica_u0: Check
    u1_mm: float = Field(description="Perimetro di verifica a distanza 2d u1", gt=0, json_schema_extra={"unit": "mm", "symbol": "u_1"})
    v_rd_c_MPa: float = Field(description="Resistenza a punzonamento del solo calcestruzzo VRd,c", gt=0, json_schema_extra={"unit": "MPa", "symbol": "V_Rd,c"})
    v_ed1_MPa: float = Field(description="Tensione di punzonamento a u1", gt=0, json_schema_extra={"unit": "MPa", "symbol": "v_Ed1"})
    verifica_u1: Check


def _u1_mm(posizione: PosizioneCarico, bx_mm: float, by_mm: float, depth_mm: float) -> float:
    if posizione == "centro":
        return control_perimeter("rett", bx_mm, by_mm, CONTROL_PERIMETER_OFFSET_FACTOR * depth_mm).u_mm
    lato_min, lato_max = min(bx_mm, by_mm), max(bx_mm, by_mm)
    if posizione == "bordo":
        return 2.0 * lato_min + lato_max + 2.0 * depth_mm * math.pi
    return lato_min + lato_max + depth_mm * math.pi  # spigolo


def punzonamento(
    posizione: PosizioneCarico, p_slu_kN: float, bx_mm: float, by_mm: float, d_mm: float, h_mm: float,
    v1: float, fcd_MPa: float, v_min_MPa: float, *, legacy_compat: bool = False,
    coeff_vrd_max: float = V_RD_MAX_COEFF_A1_2014,
) -> PunzonamentoResult:
    """spec steps 7-10."""
    v_ed_kn = p_slu_kN * BETA_PUNZONAMENTO[posizione]
    u0_mm = control_perimeter("rett", bx_mm, by_mm, FACE_PERIMETER_DIST_MM).u_mm
    vrd_max_coefficient = VRD_MAX_COEFFICIENT_NTC if legacy_compat else coeff_vrd_max
    v_rd_max_mpa = vrd_max_coefficient * v1 * fcd_MPa
    v_ed0_mpa = v_ed_kn * 1000.0 / (u0_mm * d_mm)
    # Only bordo/spigolo carry the h-vs-d bug (spec bug 2): centro already uses d in the sheet.
    depth_for_u1 = d_mm if posizione == "centro" else (h_mm if legacy_compat else d_mm)
    u1_mm = _u1_mm(posizione, bx_mm, by_mm, depth_for_u1)
    v_ed1_mpa = v_ed_kn * 1000.0 / (u1_mm * d_mm)
    return PunzonamentoResult(
        v_ed_kN=v_ed_kn, u0_mm=u0_mm, v_rd_max_MPa=v_rd_max_mpa, v_ed0_MPa=v_ed0_mpa,
        verifica_u0=Check(
            name="Punzonamento a u0", passed=v_ed0_mpa <= v_rd_max_mpa,
            clause=VRD_MAX_CLAUSE_LEGACY if legacy_compat else VRD_MAX_CLAUSE_FIXED,
            detail=f"vRd,max = {vrd_max_coefficient:g}·ν·fcd",
            value=v_ed0_mpa, limit=v_rd_max_mpa, unit="MPa",
        ),
        u1_mm=u1_mm, v_rd_c_MPa=v_min_MPa, v_ed1_MPa=v_ed1_mpa,
        verifica_u1=Check(name="Punzonamento a u1", passed=v_ed1_mpa <= v_min_MPa, clause="EC2 §6.4.4",
                           value=v_ed1_mpa, limit=v_min_MPa, unit="MPa"),
    )
