"""Flessione/Taglio/TaglioInstabilita output models, split out of `results.py` (regola dura 12)."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.report import Check


class Flessione(BaseModel):
    """Resistenza a flessione, §6.2.5, con riduzione per taglio elevato §6.2.8."""

    model_config = ConfigDict(frozen=True)

    fy_ridotta_y_MPa: float = Field(description="fy' per MRd,y, ridotta se il taglio è elevato (G31)", json_schema_extra={"unit": "MPa"})
    fy_ridotta_z_MPa: float = Field(description="fy' per MRd,z, ridotta se il taglio è elevato (G41)", json_schema_extra={"unit": "MPa"})
    mrd_y_kNm: float = Field(description="Momento resistente, asse forte", json_schema_extra={"unit": "kNm", "symbol": "M_Rd,y"})
    mrd_z_kNm: float = Field(description="Momento resistente, asse debole", json_schema_extra={"unit": "kNm", "symbol": "M_Rd,z"})
    verifica_y: Check
    verifica_z: Check


class Taglio(BaseModel):
    """Resistenza a taglio, §6.2.6."""

    model_config = ConfigDict(frozen=True)

    vpl_rd_anima_kN: float = Field(description="Resistenza a taglio dell'anima", json_schema_extra={"unit": "kN", "symbol": "V_pl,Rd"})
    vpl_rd_ali_kN: float = Field(description="Resistenza a taglio delle ali", json_schema_extra={"unit": "kN", "symbol": "V_pl,Rd"})
    verifica_anima: Check
    verifica_ali: Check


class TaglioInstabilita(BaseModel):
    """Instabilità per taglio dell'anima, §6.2.6(6)/EN1993-1-5 §5."""

    model_config = ConfigDict(frozen=True)

    hw_t: float = Field(description="Snellezza dell'anima hw/tw (AC27)")
    limite_72_eps_eta: float = Field(description="Limite 72*epsilon*eta (AD27)")
    richiede_verifica: bool = Field(description="hw/tw > limite -> verifica richiesta (K32)")
    cw: float = Field(description="Coefficiente di imbozzamento cw (C67)")
    vb_rd_kN: float = Field(description="Resistenza a taglio per instabilità dell'anima", json_schema_extra={"unit": "kN", "symbol": "V_b,Rd"})
    verifica: Check
