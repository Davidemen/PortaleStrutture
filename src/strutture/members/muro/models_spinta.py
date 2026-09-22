"""Tool 1 (spinta-terra-statica-sismica) result model of the `muro-sostegno` tool (split out of
`models.py`, regola dura 12 dei moduli piccoli).
"""
from pydantic import BaseModel, ConfigDict, Field

from .models_common import NomeCombo


class SpintaCombo(BaseModel):
    """One row of Muro!D45:AA50 (static) or D80:AA81 (seismic)."""

    model_config = ConfigDict(frozen=True)

    nome: NomeCombo = Field(description="Identificativo della combinazione")
    sismica: bool = Field(description="True per le combinazioni sismiche SISMA.1/SISMA.2")
    gamma_g_muro: float = Field(description="Coefficiente parziale sul peso proprio del muro γG,muro", gt=0, json_schema_extra={"unit": "-"})
    gamma_phi_terr: float = Field(description="Coefficiente parziale sull'angolo di attrito del terreno γφ,terr", gt=0, json_schema_extra={"unit": "-"})
    gamma_g_terr: float = Field(description="Coefficiente parziale sul peso del terreno γG,terr", gt=0, json_schema_extra={"unit": "-"})
    gamma_q: float = Field(description="Coefficiente parziale sul sovraccarico variabile γQ", ge=0, json_schema_extra={"unit": "-"})
    phi_d_rad: float = Field(description="Angolo di attrito interno di progetto φd", json_schema_extra={"unit": "rad"})
    delta_d_rad: float = Field(description="Angolo di attrito terreno-muro di progetto δd", json_schema_extra={"unit": "rad"})
    w_muro_kN: float = Field(description="Peso proprio del muro Wmuro", gt=0, json_schema_extra={"unit": "kN"})
    m_muro_kNm: float = Field(description="Momento di Wmuro rispetto al polo di ribaltamento", json_schema_extra={"unit": "kNm"})
    w_terr_kN: float = Field(description="Peso del cuneo di terreno a tergo Wterr", ge=0, json_schema_extra={"unit": "kN"})
    m_terr_kNm: float = Field(description="Momento di Wterr rispetto al polo di ribaltamento", json_schema_extra={"unit": "kNm"})
    ka: float = Field(description="Coefficiente di spinta attiva (Coulomb statico, Mononobe-Okabe sismico)", gt=0, json_schema_extra={"unit": "-", "symbol": "K_a"})
    kh: float | None = Field(default=None, description="Coefficiente sismico orizzontale kh (solo combinazioni sismiche)", json_schema_extra={"unit": "-"})
    kv: float | None = Field(default=None, description="Coefficiente sismico verticale kv = ±0.5·kh (solo combinazioni sismiche)", json_schema_extra={"unit": "-"})
    theta_rad: float | None = Field(default=None, description="Angolo θ = atan(kh/(1+kv)) (solo combinazioni sismiche)", json_schema_extra={"unit": "rad"})
