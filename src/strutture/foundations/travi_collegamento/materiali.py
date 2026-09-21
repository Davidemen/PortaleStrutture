"""Section + material properties common to both sheets (NTC C15/C16/C19/C20/C21, EN C13/C14/C17/C18/C19)."""
import math

from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.materials.concrete import ConcreteClass, fcd, fck
from strutture.shared.materials.rebar import RebarGrade, fyd, rebar_properties


class MaterialiResult(BaseModel):
    """Ac, As, fck, fcd, fyd."""

    model_config = ConfigDict(frozen=True)

    ac_mm2: float = Field(description="Area sezione di calcestruzzo Ac", json_schema_extra={"unit": "mm2", "symbol": "A_c"}, gt=0)
    as_mm2: float = Field(description="Area barre longitudinali As", json_schema_extra={"unit": "mm2", "symbol": "A_s"}, gt=0)
    fck_MPa: float = Field(description="Resistenza caratteristica cilindrica fck", json_schema_extra={"unit": "MPa", "symbol": "f_ck"}, gt=0)
    fcd_MPa: float = Field(description="Tensione di progetto a compressione fcd", json_schema_extra={"unit": "MPa", "symbol": "f_cd"}, gt=0)
    fyk_MPa: float = Field(description="Tensione caratteristica di snervamento fyk", json_schema_extra={"unit": "MPa", "symbol": "f_yk"}, gt=0)
    fyd_MPa: float = Field(description="Tensione di snervamento di progetto fyd", json_schema_extra={"unit": "MPa", "symbol": "f_yd"}, gt=0)


def materiali(
    b_mm: float, h_mm: float, phi_mm: float, n_barre: int,
    classe_calcestruzzo: ConcreteClass, classe_acciaio: RebarGrade, *, legacy_compat: bool = False,
) -> MaterialiResult:
    """Ac[C15/C13], As[C16/C14], fck[C19/C17], fcd[C20/C18], fyd[C21/C19]."""
    ac_mm2 = b_mm * h_mm
    as_mm2 = math.pi * phi_mm**2 / 4.0 * n_barre
    fck_mpa = fck(classe_calcestruzzo, legacy_compat=legacy_compat)
    fyk_mpa = rebar_properties(classe_acciaio).fyk_MPa
    return MaterialiResult(
        ac_mm2=ac_mm2, as_mm2=as_mm2, fck_MPa=fck_mpa,
        fcd_MPa=fcd(fck_mpa), fyk_MPa=fyk_mpa, fyd_MPa=fyd(fyk_mpa),
    )
