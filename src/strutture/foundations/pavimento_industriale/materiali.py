"""Concrete/steel properties for `pav-fondazione-materiali` (spec calculation steps 1-9): reuses
`shared.materials.concrete`/`shared.materials.rebar` for the NTC2018 chain (Rck, fck, fcm, Ecm, fyk,
fyd) and adds the CNR-DT211/2014-specific flexural tensile strength chain (fctm from **Rck**, not
fck, then fcfm/fcfk/fcfd) that has no shared equivalent."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.materials.concrete import fcd as concrete_fcd
from strutture.shared.materials.concrete import fck as concrete_fck
from strutture.shared.materials.concrete import rck as concrete_rck
from strutture.shared.materials.concrete.resistenze import ecm as concrete_ecm
from strutture.shared.materials.concrete.resistenze import fcm as concrete_fcm
from strutture.shared.materials.rebar import rebar_properties

# `Materiali!A2:A10` dropdown -- this sheet's concrete-class subset (9 of the 12 NTC2018 classes).
ClasseCalcestruzzoPavimento = Literal[
    "C20/25", "C25/30", "C28/35", "C30/37", "C32/40", "C35/45", "C40/50", "C45/55", "C50/60",
]

FCTM_RCK_COEFFICIENT = 0.27  # CNR-DT211/2014 fit (spec step 4): fctm = 0.27*Rck^(2/3), not EC2's 0.30*fck^(2/3).
FCTM_EXPONENT = 2.0 / 3.0
FCFM_OVER_FCTM = 1.2  # spec step 5.
FCFK_OVER_FCFM = 0.7  # spec step 6.


class MaterialiResult(BaseModel):
    """`pav-fondazione-materiali` outputs C5/C6/C8-C14/C19/C21 (concrete/steel strengths)."""

    model_config = ConfigDict(frozen=True)

    rck_MPa: float = Field(description="Resistenza cubica caratteristica Rck", gt=0, json_schema_extra={"unit": "MPa", "symbol": "R_ck"})
    fck_MPa: float = Field(description="Resistenza cilindrica caratteristica fck", gt=0, json_schema_extra={"unit": "MPa", "symbol": "f_ck"})
    fcd_MPa: float = Field(description="Resistenza di calcolo a compressione fcd", gt=0, json_schema_extra={"unit": "MPa", "symbol": "f_cd"})
    fcm_MPa: float = Field(description="Resistenza cilindrica media fcm", gt=0, json_schema_extra={"unit": "MPa", "symbol": "f_cm"})
    fctm_MPa: float = Field(description="Resistenza media a trazione fctm (CNR-DT211, da Rck)", gt=0, json_schema_extra={"unit": "MPa", "symbol": "f_ctm"})
    fcfm_MPa: float = Field(description="Resistenza media a trazione per flessione fcfm", gt=0, json_schema_extra={"unit": "MPa", "symbol": "f_cfm"})
    fcfk_MPa: float = Field(description="Resistenza caratteristica a trazione per flessione fcfk", gt=0, json_schema_extra={"unit": "MPa", "symbol": "f_cfk"})
    fcfd_MPa: float = Field(description="Resistenza di calcolo a trazione per flessione fcfd", gt=0, json_schema_extra={"unit": "MPa", "symbol": "f_cfd"})
    ecm_MPa: float = Field(description="Modulo elastico secante del calcestruzzo Ecm", gt=0, json_schema_extra={"unit": "MPa", "symbol": "E_cm"})
    fyk_MPa: float = Field(description="Tensione caratteristica di snervamento dell'acciaio fyk", gt=0, json_schema_extra={"unit": "MPa", "symbol": "f_yk"})
    fyd_MPa: float = Field(description="Tensione di calcolo di snervamento dell'acciaio fyd", gt=0, json_schema_extra={"unit": "MPa", "symbol": "f_yd"})


def materiali(
    classe_calcestruzzo: ClasseCalcestruzzoPavimento,
    gamma_c: float,
    gamma_s: float,
) -> MaterialiResult:
    """`pav-fondazione-materiali` steps 1-9 (acciaio is always B450C, `Materiali!E2:F2`).

    No `legacy_compat` branch here: unlike the batch-1 sheets (`docs/divergences/materials.md`),
    `Materiali!C2:C10` already stores the NTC2018 Tab. 4.1.I literal fck directly (e.g. 25 for
    C25/30, not a `0.83*Rck` fill-down), so `concrete_fck(..., legacy_compat=False)` reproduces
    both this sheet and the code-standard value.
    """
    rck_mpa = concrete_rck(classe_calcestruzzo)
    fck_mpa = concrete_fck(classe_calcestruzzo, legacy_compat=False)
    fcd_mpa = concrete_fcd(fck_mpa, gamma_c=gamma_c)
    fcm_mpa = concrete_fcm(fck_mpa)
    ecm_mpa = concrete_ecm(fcm_mpa)
    fctm_mpa = FCTM_RCK_COEFFICIENT * rck_mpa**FCTM_EXPONENT
    fcfm_mpa = FCFM_OVER_FCTM * fctm_mpa
    fcfk_mpa = FCFK_OVER_FCFM * fcfm_mpa
    fcfd_mpa = fcfk_mpa / gamma_c
    acciaio = rebar_properties("B450C", gamma_s=gamma_s)
    return MaterialiResult(
        rck_MPa=rck_mpa, fck_MPa=fck_mpa, fcd_MPa=fcd_mpa, fcm_MPa=fcm_mpa,
        fctm_MPa=fctm_mpa, fcfm_MPa=fcfm_mpa, fcfk_MPa=fcfk_mpa, fcfd_MPa=fcfd_mpa,
        ecm_MPa=ecm_mpa, fyk_MPa=acciaio.fyk_MPa, fyd_MPa=acciaio.fyd_MPa,
    )
