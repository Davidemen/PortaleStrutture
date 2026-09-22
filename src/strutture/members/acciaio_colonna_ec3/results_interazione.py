"""Interazione N-My-Mz output models, split out of `results.py` (regola dura 12)."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.report import Check


class Interazione(BaseModel):
    """Interazione N-My-Mz, Annex A, eq. 6.61/6.62."""

    model_config = ConfigDict(frozen=True)

    cmy: float = Field(description="Fattore di momento uniforme equivalente Cmy (AM64)")
    cmz: float = Field(description="Fattore di momento uniforme equivalente Cmz (AM65)")
    cm_lt: float = Field(description="Fattore CmLT (AM66)")
    kyy: float = Field(description="Fattore di interazione kyy (X42)")
    kyz: float = Field(description="Fattore di interazione kyz (X43)")
    kzy: float = Field(description="Fattore di interazione kzy (X44)")
    kzz: float = Field(description="Fattore di interazione kzz (X45)")
    utilizzo_yy: float = Field(description="Rapporto di utilizzo dell'interazione N-My-Mz, asse forte", json_schema_extra={"unit": "-", "symbol": "N_Ed/N_Rd + ΣM_Ed/M_Rd (yy)", "highlight": True})
    utilizzo_zz: float = Field(description="Rapporto di utilizzo dell'interazione N-My-Mz, asse debole", json_schema_extra={"unit": "-", "symbol": "N_Ed/N_Rd + ΣM_Ed/M_Rd (zz)", "highlight": True})
    verifica_yy: Check
    verifica_zz: Check


class InterazioneSemplificata(BaseModel):
    """Verifiche semplificate di riscontro (fallback), non da Annex A."""

    model_config = ConfigDict(frozen=True)

    n_ratio: float = Field(description="n = Nsd/Npl (H46)")
    mn_rd_y_kNm: float = Field(description="Momento resistente ridotto per la presenza di sforzo normale, asse forte", json_schema_extra={"unit": "kNm", "symbol": "M_N,Rd,y"})
    mn_rd_z_kNm: float = Field(description="Momento resistente ridotto per la presenza di sforzo normale, asse debole", json_schema_extra={"unit": "kNm", "symbol": "M_N,Rd,z"})
    verifica_yy: Check
    verifica_zz: Check
    v54: float = Field(description="Somma dei rapporti di utilizzo lineari (V54)")
    verifica_lineare: Check
    i56: float = Field(description="Interazione a potenza (I56)")
    verifica_potenza: Check
