"""Instabilita flessionale/flesso-torsionale output models, split out of `results.py` (regola dura 12)."""
from pydantic import BaseModel, ConfigDict, Field


class InstabilitaFlessionale(BaseModel):
    """Instabilità per flessione semplice, §6.3.1."""

    model_config = ConfigDict(frozen=True)

    ncr_y_kN: float = Field(description="Carico critico euleriano Ncr,y (Y21)", json_schema_extra={"unit": "kN"})
    ncr_z_kN: float = Field(description="Carico critico euleriano Ncr,z (Y22)", json_schema_extra={"unit": "kN"})
    ncr_t_kN: float = Field(description="Carico critico torsionale Ncr,T (AV38)", json_schema_extra={"unit": "kN"})
    lambda_yy: float = Field(description="Snellezza adimensionale lambda_yy (W23)")
    lambda_zz: float = Field(description="Snellezza adimensionale lambda_zz (W24)")
    lambda_max: float = Field(description="MAX(lambda_yy, lambda_zz) (AI33)")
    phi_yy: float = Field(description="phi per la curva di instabilità yy (W27)")
    phi_zz: float = Field(description="phi per la curva di instabilità zz (W28)")
    chi_yy: float = Field(description="Fattore riduttivo chi_yy (W29)")
    chi_zz: float = Field(description="Fattore riduttivo chi_zz (W32)")


class InstabilitaTorsoFlessionale(BaseModel):
    """Instabilità flesso-torsionale (LTB), §6.3.2."""

    model_config = ConfigDict(frozen=True)

    mcr_Nmm: float = Field(description="Momento critico elastico Mcr (AI8)", json_schema_extra={"unit": "Nmm"})
    lambda_lt: float = Field(description="Snellezza adimensionale lambda_LT (S34/AI35)")
    phi_lt: float = Field(description="phi_LT (W36)")
    chi_lt: float = Field(description="Fattore riduttivo chi_LT (U37)")
    verifica_non_necessaria: bool = Field(description="LTB non necessaria per §6.3.2.2(4) (O59)")
