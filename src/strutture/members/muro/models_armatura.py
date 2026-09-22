"""Tool 4/5/6 (armatura-paramento, armatura-fondazione-valle, armatura-fondazione-monte) result
models of the `muro-sostegno` tool (split out of `models.py`, regola dura 12 dei moduli piccoli).
"""
from pydantic import BaseModel, ConfigDict, Field

from .models_common import NomeCombo


class ArmaturaParamentoCombo(BaseModel):
    """One row of Muro!C143:H150 (stem base bending per combination)."""

    model_config = ConfigDict(frozen=True)

    nome: NomeCombo = Field(description="Identificativo della combinazione")
    zq_m: float = Field(description="Braccio di leva di SH.q rispetto alla base del paramento", json_schema_extra={"unit": "m"})
    zterr_m: float = Field(description="Braccio di leva di SH.terr rispetto alla base del paramento", json_schema_extra={"unit": "m"})
    m_ed_kNm: float = Field(description="Momento flettente di calcolo alla base del paramento MEd", json_schema_extra={"unit": "kNm"})
    as_nec_cm2_m: float = Field(description="Area di armatura necessaria As.nec (può essere negativa: MEd favorevole, nessuna armatura a trazione richiesta su questa combinazione)", json_schema_extra={"unit": "cm2/m"})


class ArmaturaParamentoResult(BaseModel):
    """Composed result of Tool 4 (rows 133-151): governing combination + bar callout."""

    model_config = ConfigDict(frozen=True)

    combinazioni: tuple[ArmaturaParamentoCombo, ...] = Field(description="Momento e As.nec per combinazione (8 righe, ordine ALL_COMBOS)")
    as_nec_cm2_m: float = Field(description="Area di armatura necessaria governante, massimo tra le combinazioni", ge=0, json_schema_extra={"unit": "cm2/m", "symbol": "A_s,nec"})
    as_min_cm2_m: float = Field(default=0.0, description="Armatura minima NTC2018 §4.1.6.1.1, max(0,26·fctm/fyk; 0,0013)·b·d per metro", ge=0, json_schema_extra={"unit": "cm2/m", "symbol": "A_s,min"})
    as_progetto_cm2_m: float = Field(default=0.0, description="Area di progetto per la scelta delle barre: max(As,nec; As,min) (in modalità Excel: As,nec)", ge=0, json_schema_extra={"unit": "cm2/m", "symbol": "A_s,prog"})
    combo_governante: NomeCombo = Field(description="Combinazione che governa il dimensionamento")
    diametro_mm: float = Field(description="Diametro della barra scelto", gt=0, json_schema_extra={"unit": "mm"})
    passo_m: float = Field(description="Passo delle armature", gt=0, json_schema_extra={"unit": "m"})
    callout: str = Field(description="Sigla di armatura, es. '1φ8/20'")


class ArmaturaFondazioneValleCombo(BaseModel):
    """One row of Muro!C161:K168 (toe/mancia cantilever bending per combination)."""

    model_config = ConfigDict(frozen=True)

    nome: NomeCombo = Field(description="Identificativo della combinazione")
    p_star_kPa: float = Field(description="Pressione sul terreno all'incastro della mensola di valle p*", json_schema_extra={"unit": "kPa"})
    m_ed_p1_kNm: float = Field(description="Momento del blocco di pressione rettangolare/triangolare inferiore MEd.p.1", json_schema_extra={"unit": "kNm"})
    m_ed_p2_kNm: float = Field(description="Momento del cuneo di pressione residuo MEd.p.2", json_schema_extra={"unit": "kNm"})
    m_ed_fond_kNm: float = Field(description="Momento del peso proprio della mensola di valle MEd.fond", json_schema_extra={"unit": "kNm"})
    m_ed_tot_kNm: float = Field(description="Momento flettente totale all'incastro MEd.tot", json_schema_extra={"unit": "kNm"})
    as_nec_cm2_m: float = Field(description="Area di armatura necessaria As.nec (può essere negativa: MEd favorevole, nessuna armatura a trazione richiesta su questa combinazione)", json_schema_extra={"unit": "cm2/m"})


class ArmaturaFondazioneValleResult(BaseModel):
    """Composed result of Tool 5 (rows 154-169): governing combination + bar callout."""

    model_config = ConfigDict(frozen=True)

    combinazioni: tuple[ArmaturaFondazioneValleCombo, ...] = Field(description="Momento e As.nec per combinazione (8 righe, ordine ALL_COMBOS)")
    as_nec_cm2_m: float = Field(description="Area di armatura necessaria governante, massimo tra le combinazioni", ge=0, json_schema_extra={"unit": "cm2/m", "symbol": "A_s,nec"})
    as_min_cm2_m: float = Field(default=0.0, description="Armatura minima NTC2018 §4.1.6.1.1, max(0,26·fctm/fyk; 0,0013)·b·d per metro", ge=0, json_schema_extra={"unit": "cm2/m", "symbol": "A_s,min"})
    as_progetto_cm2_m: float = Field(default=0.0, description="Area di progetto per la scelta delle barre: max(As,nec; As,min) (in modalità Excel: As,nec)", ge=0, json_schema_extra={"unit": "cm2/m", "symbol": "A_s,prog"})
    combo_governante: NomeCombo = Field(description="Combinazione che governa il dimensionamento")
    diametro_mm: float = Field(description="Diametro della barra scelto", gt=0, json_schema_extra={"unit": "mm"})
    passo_m: float = Field(description="Passo delle armature", gt=0, json_schema_extra={"unit": "m"})
    callout: str = Field(description="Sigla di armatura, es. '1φ4/20'")


class ArmaturaFondazioneMonteCombo(BaseModel):
    """One row of Muro!C179:M186 (heel/tacco cantilever bending per combination)."""

    model_config = ConfigDict(frozen=True)

    nome: NomeCombo = Field(description="Identificativo della combinazione")
    p_star_star_kPa: float = Field(description="Pressione sul terreno all'incastro della mensola di monte p**", json_schema_extra={"unit": "kPa"})
    m_ed_p_kNm: float = Field(description="Momento del diagramma di pressione sotto la mensola di monte MEd.p", json_schema_extra={"unit": "kNm"})
    m_ed_terr_kNm: float = Field(description="Momento del peso del cuneo di terreno a tergo MEd.terr", json_schema_extra={"unit": "kNm"})
    m_ed_sv_kNm: float = Field(description="Momento della componente verticale della spinta MEd.SV", json_schema_extra={"unit": "kNm"})
    m_ed_fond_kNm: float = Field(description="Momento del peso proprio della mensola di monte MEd.fond", json_schema_extra={"unit": "kNm"})
    m_ed_tot_kNm: float = Field(description="Momento flettente totale all'incastro MEd.tot", json_schema_extra={"unit": "kNm"})
    as_nec_cm2_m: float = Field(description="Area di armatura necessaria As.nec (può essere negativa: MEd favorevole, nessuna armatura a trazione richiesta su questa combinazione)", json_schema_extra={"unit": "cm2/m"})


class ArmaturaFondazioneMonteResult(BaseModel):
    """Composed result of Tool 6 (rows 172-187): governing combination + bar callout."""

    model_config = ConfigDict(frozen=True)

    combinazioni: tuple[ArmaturaFondazioneMonteCombo, ...] = Field(description="Momento e As.nec per combinazione (8 righe, ordine ALL_COMBOS)")
    as_nec_cm2_m: float = Field(description="Area di armatura necessaria governante, massimo tra le combinazioni", ge=0, json_schema_extra={"unit": "cm2/m", "symbol": "A_s,nec"})
    as_min_cm2_m: float = Field(default=0.0, description="Armatura minima NTC2018 §4.1.6.1.1, max(0,26·fctm/fyk; 0,0013)·b·d per metro", ge=0, json_schema_extra={"unit": "cm2/m", "symbol": "A_s,min"})
    as_progetto_cm2_m: float = Field(default=0.0, description="Area di progetto per la scelta delle barre: max(As,nec; As,min) (in modalità Excel: As,nec)", ge=0, json_schema_extra={"unit": "cm2/m", "symbol": "A_s,prog"})
    combo_governante: NomeCombo = Field(description="Combinazione che governa il dimensionamento")
    diametro_mm: float = Field(description="Diametro della barra scelto", gt=0, json_schema_extra={"unit": "mm"})
    passo_m: float = Field(description="Passo delle armature", gt=0, json_schema_extra={"unit": "m"})
    callout: str = Field(description="Sigla di armatura, es. '1φ10/20'")
