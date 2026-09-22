"""Tool 2 (verifica-ribaltamento-scorrimento) and Tool 3 (verifica-pressioni-terreno) result
models of the `muro-sostegno` tool (split out of `models.py`, regola dura 12 dei moduli piccoli).
"""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.report import Check

from .models_common import NomeCombo


class RibaltamentoScorrimentoCombo(BaseModel):
    """One row of Muro!B54:S61 (static) or B85:S88 (seismic)."""

    model_config = ConfigDict(frozen=True)

    nome: NomeCombo = Field(description="Identificativo della combinazione")
    phi_scorrimento_rad: float = Field(default=0.0, description="Angolo di attrito di progetto usato per la resistenza allo scorrimento sul piano di posa: del terreno di fondazione (blocco compilato, condizione drenata) oppure del rinterro", json_schema_extra={"unit": "rad", "symbol": "φ_d,base"})
    dq_kN_m2: float = Field(description="Sovraccarico di progetto Dq = q·γQ", ge=0, json_schema_extra={"unit": "kN/m2"})
    sh_q_kN: float = Field(description="Componente orizzontale della spinta dovuta al sovraccarico", ge=0, json_schema_extra={"unit": "kN"})
    sh_terr_kN: float = Field(description="Componente orizzontale della spinta del terreno", ge=0, json_schema_extra={"unit": "kN"})
    sv_q_kN: float = Field(description="Componente verticale della spinta dovuta al sovraccarico", json_schema_extra={"unit": "kN"})
    sv_terr_kN: float = Field(description="Componente verticale della spinta del terreno", json_schema_extra={"unit": "kN"})
    braccio_terr_m: float = Field(description="Braccio di leva di SH.terr rispetto alla base (H/3 statico, H/2 sismico)", gt=0, json_schema_extra={"unit": "m"})
    fh_kN: float = Field(default=0.0, description="Forza d'inerzia orizzontale del muro+terreno kh·(Wmuro+Wterr) (solo SISMA, legacy_compat=False)", ge=0, json_schema_extra={"unit": "kN"})
    m_fh_kNm: float = Field(default=0.0, description="Momento ribaltante della forza d'inerzia Fh (solo SISMA, legacy_compat=False)", ge=0, json_schema_extra={"unit": "kNm"})
    m_rib_kNm: float = Field(description="Momento ribaltante MRIB", ge=0, json_schema_extra={"unit": "kNm"})
    m_stab_kNm: float = Field(description="Momento stabilizzante MSTAB", json_schema_extra={"unit": "kNm"})
    n_tot_kN: float = Field(description="Risultante verticale totale Ntot", json_schema_extra={"unit": "kN"})
    r_tot_kN: float = Field(description="Risultante orizzontale totale Rtot", ge=0, json_schema_extra={"unit": "kN"})
    or_ribaltamento: float = Field(description="Fattore di sicurezza a ribaltamento, momento stabilizzante su momento ribaltante", json_schema_extra={"unit": "-", "symbol": "OR", "highlight": True})
    os_scorrimento: float = Field(description="Fattore di sicurezza a scorrimento", json_schema_extra={"unit": "-", "symbol": "OS", "highlight": True})
    verifica_ribaltamento: Check = Field(description="Esito della verifica a ribaltamento (OR ≥ 1)")
    verifica_scorrimento: Check = Field(description="Esito della verifica a scorrimento (OS ≥ 1)")


class PressioniCombo(BaseModel):
    """One row of Muro!B65:S72 (static) or B92:S95 (seismic)."""

    model_config = ConfigDict(frozen=True)

    nome: NomeCombo = Field(description="Identificativo della combinazione")
    e_muro_m: float = Field(description="Eccentricità del peso del muro rispetto al centro della fondazione", json_schema_extra={"unit": "m"})
    e_terr_m: float = Field(description="Eccentricità del peso del terreno rispetto al centro della fondazione", json_schema_extra={"unit": "m"})
    e_sv_m: float = Field(description="Eccentricità della spinta verticale totale rispetto al centro della fondazione", json_schema_extra={"unit": "m"})
    m_tot_kNm: float = Field(description="Momento totale rispetto al centro della fondazione", json_schema_extra={"unit": "kNm"})
    n_tot_kN: float = Field(description="Risultante verticale totale", json_schema_extra={"unit": "kN"})
    eccentricita_m: float = Field(description="Eccentricità della risultante, e = Mtot/Ntot", json_schema_extra={"unit": "m", "symbol": "e"})
    entro_nocciolo: bool = Field(description="True se |e| ≤ B/6 (sezione interamente compressa)")
    b_star_m: float = Field(description="Larghezza efficace (0 se |e| ≤ B/6)", ge=0, json_schema_extra={"unit": "m", "symbol": "B*"})
    p_valle_kPa: float = Field(description="Pressione sul terreno lato valle", ge=0, json_schema_extra={"unit": "kPa", "symbol": "p_valle"})
    p_monte_kPa: float = Field(description="Pressione sul terreno lato monte", ge=0, json_schema_extra={"unit": "kPa", "symbol": "p_monte"})
