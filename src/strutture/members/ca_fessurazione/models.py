"""Pydantic I/O models for the three `ca_fessurazione` tools (NTC2018 §4.1.2.2.4/§4.1.2.2.5).

Inputs stay flat, ordered as in each sheet top to bottom; only outputs are nested (see
docs/BUILD_CONTRACT.md "Member tools"). The three repeated sections of `Limitazione delle
tensioni` and `Apertura delle fessure SEMP` are flattened to `_1`/`_2`/`_3` suffixed input
fields and reassembled into a `tuple[..., ...]` of per-section output rows.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from strutture.shared.durability_cover import CrackWidthClass, EnvironmentalCondition, ReinforcementSensitivity
from strutture.shared.materials.concrete import ConcreteClass
from strutture.shared.materials.rebar import ES_MPA

from .tables import ClasseFessurazione, DurataCarico, TipoBarre, TipoSollecitazione

# ---------------------------------------------------------------------------
# Tool 1: ca-sle-limitazione-tensioni
# ---------------------------------------------------------------------------


class LimitazioneTensioniInput(BaseModel):
    """`Limitazione delle tensioni` sheet inputs."""

    model_config = ConfigDict(frozen=True)

    rck_MPa: float = Field(description="Resistenza cubica caratteristica del calcestruzzo", gt=0, json_schema_extra={"unit": "MPa", "symbol": "R_ck", "group": "Materiali"})
    fyk_MPa: float = Field(default=450.0, description="Tensione caratteristica di snervamento dell'acciaio", gt=0, json_schema_extra={"unit": "MPa", "symbol": "f_yk", "group": "Materiali"})
    sigma_c_rar_1_MPa: float = Field(description="Tensione nel calcestruzzo, combinazione rara, sezione 1 (h=30cm, bordo)", ge=0, json_schema_extra={"unit": "MPa", "symbol": "σ_c,rara", "group": "Sollecitazioni di progetto"})
    sigma_c_qpe_1_MPa: float = Field(description="Tensione nel calcestruzzo, combinazione quasi permanente, sezione 1", ge=0, json_schema_extra={"unit": "MPa", "symbol": "σ_c,qp", "group": "Sollecitazioni di progetto"})
    sigma_s_rar_1_MPa: float = Field(description="Tensione nell'acciaio, combinazione rara, sezione 1", ge=0, json_schema_extra={"accepts": "trave.sigma_s_rara_MPa", "unit": "MPa", "symbol": "σ_s,rara", "group": "Sollecitazioni di progetto"})
    sigma_c_rar_2_MPa: float = Field(description="Tensione nel calcestruzzo, combinazione rara, sezione 2 (h=30cm, zona centrale)", ge=0, json_schema_extra={"unit": "MPa", "symbol": "σ_c,rara", "group": "Sollecitazioni di progetto"})
    sigma_c_qpe_2_MPa: float = Field(description="Tensione nel calcestruzzo, combinazione quasi permanente, sezione 2", ge=0, json_schema_extra={"unit": "MPa", "symbol": "σ_c,qp", "group": "Sollecitazioni di progetto"})
    sigma_s_rar_2_MPa: float = Field(description="Tensione nell'acciaio, combinazione rara, sezione 2", ge=0, json_schema_extra={"unit": "MPa", "symbol": "σ_s,rara", "group": "Sollecitazioni di progetto"})
    sigma_c_rar_3_MPa: float = Field(description="Tensione nel calcestruzzo, combinazione rara, sezione 3 (h=20cm)", ge=0, json_schema_extra={"unit": "MPa", "symbol": "σ_c,rara", "group": "Sollecitazioni di progetto"})
    sigma_c_qpe_3_MPa: float = Field(description="Tensione nel calcestruzzo, combinazione quasi permanente, sezione 3", ge=0, json_schema_extra={"unit": "MPa", "symbol": "σ_c,qp", "group": "Sollecitazioni di progetto"})
    sigma_s_rar_3_MPa: float = Field(description="Tensione nell'acciaio, combinazione rara, sezione 3", ge=0, json_schema_extra={"unit": "MPa", "symbol": "σ_s,rara", "group": "Sollecitazioni di progetto"})
    legacy_compat: bool = Field(
        default=False, description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"advanced": True, "group": "Avanzate"},
    )


class VerificaTensioneSezione(BaseModel):
    """One section's stress-limitation verification row."""

    model_config = ConfigDict(frozen=True)

    titolo: str = Field(description="Titolo della sezione")
    sottotitolo: str = Field(description="Sottotitolo della sezione (vuoto se non presente)")
    sigma_c_max_rar_MPa: float = Field(description="Tensione limite nel calcestruzzo, combinazione rara", json_schema_extra={"unit": "MPa", "symbol": "σ_c,rara,lim"})
    sigma_c_rar_MPa: float = Field(description="Tensione agente nel calcestruzzo, combinazione rara", json_schema_extra={"unit": "MPa", "symbol": "σ_c,rara"})
    utilizzo_c_rar: float = Field(description="Tasso di sfruttamento, calcestruzzo combinazione rara", json_schema_extra={"unit": "-", "symbol": "σ_c,rara/σ_c,rara,lim", "highlight": True})
    verificato_c_rar: bool = Field(description="Esito della verifica sul calcestruzzo, combinazione rara")
    sigma_c_max_qpe_MPa: float = Field(description="Tensione limite nel calcestruzzo, combinazione quasi permanente", json_schema_extra={"unit": "MPa", "symbol": "σ_c,qp,lim"})
    sigma_c_qpe_MPa: float = Field(description="Tensione agente nel calcestruzzo, combinazione quasi permanente", json_schema_extra={"unit": "MPa", "symbol": "σ_c,qp"})
    utilizzo_c_qpe: float = Field(description="Tasso di sfruttamento, calcestruzzo combinazione quasi permanente", json_schema_extra={"unit": "-"})
    verificato_c_qpe: bool = Field(description="Esito della verifica sul calcestruzzo, combinazione quasi permanente")
    sigma_s_max_rar_MPa: float = Field(description="Tensione limite nell'acciaio, combinazione rara", json_schema_extra={"unit": "MPa", "symbol": "σ_s,rara,lim"})
    sigma_s_rar_MPa: float = Field(description="Tensione agente nell'acciaio, combinazione rara", json_schema_extra={"unit": "MPa", "symbol": "σ_s,rara"})
    utilizzo_s_rar: float = Field(description="Tasso di sfruttamento, acciaio combinazione rara", json_schema_extra={"unit": "-"})
    verificato_s_rar: bool = Field(description="Esito della verifica sull'acciaio, combinazione rara")


class LimitazioneTensioniOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    fck_MPa: float = Field(description="Resistenza cilindrica caratteristica", json_schema_extra={"unit": "MPa", "symbol": "f_ck"})
    sezioni: tuple[VerificaTensioneSezione, VerificaTensioneSezione, VerificaTensioneSezione] = Field(
        description="Verifiche per le tre sezioni (h=30cm bordo, h=30cm zona centrale, h=20cm)"
    )


# ---------------------------------------------------------------------------
# Tool 2: ca-apertura-fessure
# ---------------------------------------------------------------------------


class AperturaFessureInput(BaseModel):
    """`Apertura delle fessure` sheet inputs.

    `E18`/`E19` (Ecm/fctm) are not exposed as inputs: the sheet sources them from a dead
    external link (`[1]MATERIALE CLS`); this tool derives them from `classe_calcestruzzo`
    (already an input, `E4`) via `strutture.shared.materials.concrete` instead — see
    docs/divergences/ca-fessurazione.md.
    """

    model_config = ConfigDict(frozen=True)

    classe_calcestruzzo: ConcreteClass = Field(description="Classe di resistenza del calcestruzzo", json_schema_extra={"group": "Materiali"})
    tipo_barre: TipoBarre = Field(description="Tipo di aderenza delle barre", json_schema_extra={"group": "Geometria della sezione"})
    tipo_sollecitazione: TipoSollecitazione = Field(description="Tipo di sollecitazione", json_schema_extra={"group": "Sollecitazioni di progetto"})
    durata_carico: DurataCarico = Field(description="Durata del carico", json_schema_extra={"group": "Sollecitazioni di progetto"})
    classe_fessurazione: ClasseFessurazione = Field(description="Classe di apertura di fessura limite", json_schema_extra={"group": "Combinazione"})
    interferro_mm: float = Field(gt=0, description="Spaziatura (interferro) fra le barre", json_schema_extra={"unit": "mm", "group": "Geometria della sezione"})
    sigma_s_MPa: float = Field(gt=0, description="Tensione nell'armatura tesa nella sezione fessurata", json_schema_extra={"unit": "MPa", "symbol": "σ_s", "group": "Sollecitazioni di progetto"})
    es_MPa: float = Field(default=ES_MPA, gt=0, description="Modulo elastico dell'acciaio", json_schema_extra={"unit": "MPa", "symbol": "E_s", "group": "Materiali", "advanced": True})
    h_mm: float = Field(gt=0, description="Altezza della sezione", json_schema_extra={"unit": "mm", "symbol": "h", "group": "Geometria della sezione"})
    x_mm: float = Field(gt=0, description="Profondità dell'asse neutro", json_schema_extra={"unit": "mm", "symbol": "x", "group": "Geometria della sezione"})
    b_mm: float = Field(gt=0, description="Larghezza della sezione", json_schema_extra={"unit": "mm", "symbol": "b", "group": "Geometria della sezione"})
    n1: int = Field(ge=1, description="Numero di barre, gruppo 1", json_schema_extra={"group": "Geometria della sezione"})
    phi1_mm: float = Field(gt=0, description="Diametro delle barre, gruppo 1", json_schema_extra={"unit": "mm", "symbol": "⌀_1", "group": "Geometria della sezione"})
    n2: int = Field(default=0, ge=0, description="Numero di barre, gruppo 2 (0 se assente)", json_schema_extra={"group": "Geometria della sezione"})
    phi2_mm: float = Field(default=0.0, ge=0, description="Diametro delle barre, gruppo 2", json_schema_extra={"unit": "mm", "symbol": "⌀_2", "group": "Geometria della sezione"})
    copriferro_mm: float = Field(gt=0, description="Copriferro dell'armatura", json_schema_extra={"unit": "mm", "symbol": "c", "group": "Geometria della sezione"})
    k3: float = Field(default=3.4, gt=0, description="Costante di spaziatura delle fessure", json_schema_extra={"symbol": "k_3", "group": "Parametri di calcolo", "advanced": True})
    k4: float = Field(default=0.425, gt=0, description="Costante di spaziatura delle fessure", json_schema_extra={"symbol": "k_4", "group": "Parametri di calcolo", "advanced": True})
    legacy_compat: bool = Field(
        default=False, description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"advanced": True, "group": "Avanzate"},
    )

    @model_validator(mode="after")
    def _geometria_coerente(self) -> "AperturaFessureInput":
        if self.x_mm >= self.h_mm:
            raise ValueError("la profondità dell'asse neutro x deve essere minore dell'altezza della sezione h")
        if self.h_mm <= self.phi1_mm / 2 + self.copriferro_mm:
            raise ValueError("l'altezza utile d = h - ø1/2 - c deve essere positiva")
        if (self.n2 == 0) != (self.phi2_mm == 0):
            raise ValueError("n2 e ø2 devono essere entrambi nulli o entrambi positivi")
        return self


class GeometriaFessurazioneOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    d_mm: float = Field(description="Altezza utile della sezione", json_schema_extra={"unit": "mm", "symbol": "d"})
    hc_eff_mm: float = Field(description="Altezza efficace di calcestruzzo teso", json_schema_extra={"unit": "mm", "symbol": "h_c,eff"})
    ac_eff_mm2: float = Field(description="Area efficace di calcestruzzo teso", json_schema_extra={"unit": "mm2", "symbol": "A_c,eff"})
    as_mm2: float = Field(description="Area di armatura tesa", json_schema_extra={"unit": "mm2", "symbol": "A_s"})
    phi_eq_mm: float = Field(description="Diametro equivalente delle barre", json_schema_extra={"unit": "mm", "symbol": "⌀_eq"})
    rho_eff: float = Field(description="Rapporto di armatura efficace", json_schema_extra={"unit": "-", "symbol": "ρ_eff"})


class MaterialeFessurazioneOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    ecm_MPa: float = Field(description="Modulo elastico secante del calcestruzzo", json_schema_extra={"unit": "MPa", "symbol": "E_cm"})
    fctm_MPa: float = Field(description="Resistenza media a trazione del calcestruzzo", json_schema_extra={"unit": "MPa", "symbol": "f_ctm"})
    alpha_e: float = Field(description="Rapporto di omogeneizzazione acciaio-calcestruzzo", json_schema_extra={"unit": "-", "symbol": "α_e"})


class CoefficientiFessurazioneOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    k1: float = Field(description="Coefficiente di aderenza", json_schema_extra={"unit": "-", "symbol": "k_1"})
    k2: float = Field(description="Coefficiente per tipo di sollecitazione", json_schema_extra={"unit": "-", "symbol": "k_2"})
    kt: float = Field(description="Coefficiente per durata del carico", json_schema_extra={"unit": "-", "symbol": "k_t"})


class RisultatoFessurazioneOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    slim_mm: float = Field(description="Spaziatura limite tra le barre", json_schema_extra={"unit": "mm", "symbol": "s_lim"})
    ramo: Literal["C4.1.7", "C4.1.10"] = Field(description="Ramo di calcolo selezionato per la distanza media tra le fessure")
    delta_sm_mm: float = Field(description="Distanza media tra le fessure", json_schema_extra={"unit": "mm", "symbol": "Δs_m"})
    epsilon_sm: float = Field(description="Deformazione media dell'armatura", json_schema_extra={"unit": "-", "symbol": "ε_sm"})
    wk_mm: float = Field(description="Ampiezza caratteristica delle fessure", json_schema_extra={"unit": "mm", "symbol": "w_k", "highlight": True})
    wlim_mm: float = Field(description="Ampiezza limite delle fessure", json_schema_extra={"unit": "mm", "symbol": "w_lim"})
    utilizzo: float = Field(description="Tasso di sfruttamento wk/wlim, arrotondato per eccesso a 2 decimali", json_schema_extra={"unit": "-", "symbol": "w_k/w_lim", "highlight": True})
    verificato: bool = Field(description="Esito della verifica di apertura delle fessure")


class AperturaFessureOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    geometria: GeometriaFessurazioneOutput
    materiale: MaterialeFessurazioneOutput
    coefficienti: CoefficientiFessurazioneOutput
    fessurazione: RisultatoFessurazioneOutput


# ---------------------------------------------------------------------------
# Tool 3: ca-apertura-fessure-semplificata
# ---------------------------------------------------------------------------


class AperturaFessureSempInput(BaseModel):
    """`Apertura delle fessure SEMP` sheet inputs.

    The sheet's σs,lim columns (`D21/43/66` for FRE, `D22/44/67` for QPE) are free-typed
    numbers with no backing formula ("presumably taken from EC2 Table 7.2N ... at a given bar
    diameter — not present in this sheet", spec §Tool 3). Here `diametro_mm_i` replaces them:
    the limits are derived from `strutture.shared.rebar_catalog.sigma_limit_by_diameter` (Tab.
    C4.1.II). Under `legacy_compat=True` the crack-width class is the sheet's hardcoded pair
    (w3 for FRE, w2 for QPE — the "condizioni ordinarie + armatura poco sensibile" row of Tab.
    4.1.IV); under `legacy_compat=False` `condizioni_ambientali`/`sensibilita_armatura` resolve
    the applicable class via `strutture.shared.durability_cover.crack_width_limit` — see
    docs/divergences/ca-fessurazione.md.
    """

    model_config = ConfigDict(frozen=True)

    condizioni_ambientali: EnvironmentalCondition = Field(
        default="ordinarie", description="Condizioni ambientali di esposizione", json_schema_extra={"group": "Combinazione"}
    )
    sensibilita_armatura: ReinforcementSensitivity = Field(
        default="poco sensibile", description="Sensibilità dell'armatura alla corrosione", json_schema_extra={"group": "Combinazione"}
    )
    diametro_mm_1: float = Field(gt=0, description="Diametro delle barre, sezione 1 (h=30cm, bordo)", json_schema_extra={"unit": "mm", "symbol": "⌀_1", "group": "Geometria della sezione"})
    sigma_fre_MPa_1: float = Field(ge=0, description="Tensione nell'acciaio, combinazione frequente, sezione 1", json_schema_extra={"unit": "MPa", "symbol": "σ_s,fre", "group": "Sollecitazioni di progetto"})
    sigma_qpe_MPa_1: float = Field(ge=0, description="Tensione nell'acciaio, combinazione quasi permanente, sezione 1", json_schema_extra={"unit": "MPa", "symbol": "σ_s,qp", "group": "Sollecitazioni di progetto"})
    diametro_mm_2: float = Field(gt=0, description="Diametro delle barre, sezione 2 (h=30cm, zona centrale)", json_schema_extra={"unit": "mm", "symbol": "⌀_2", "group": "Geometria della sezione"})
    sigma_fre_MPa_2: float = Field(ge=0, description="Tensione nell'acciaio, combinazione frequente, sezione 2", json_schema_extra={"unit": "MPa", "symbol": "σ_s,fre", "group": "Sollecitazioni di progetto"})
    sigma_qpe_MPa_2: float = Field(ge=0, description="Tensione nell'acciaio, combinazione quasi permanente, sezione 2", json_schema_extra={"unit": "MPa", "symbol": "σ_s,qp", "group": "Sollecitazioni di progetto"})
    diametro_mm_3: float = Field(gt=0, description="Diametro delle barre, sezione 3 (h=20cm)", json_schema_extra={"unit": "mm", "symbol": "⌀_3", "group": "Geometria della sezione"})
    sigma_fre_MPa_3: float = Field(ge=0, description="Tensione nell'acciaio, combinazione frequente, sezione 3", json_schema_extra={"unit": "MPa", "symbol": "σ_s,fre", "group": "Sollecitazioni di progetto"})
    sigma_qpe_MPa_3: float = Field(ge=0, description="Tensione nell'acciaio, combinazione quasi permanente, sezione 3", json_schema_extra={"unit": "MPa", "symbol": "σ_s,qp", "group": "Sollecitazioni di progetto"})
    legacy_compat: bool = Field(
        default=False, description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"advanced": True, "group": "Avanzate"},
    )


class VerificaSemplificataSezione(BaseModel):
    model_config = ConfigDict(frozen=True)

    titolo: str = Field(description="Titolo della sezione")
    sottotitolo: str = Field(description="Sottotitolo della sezione (vuoto se non presente)")
    diametro_mm: float = Field(description="Diametro delle barre", json_schema_extra={"unit": "mm", "symbol": "⌀"})
    classe_fre: CrackWidthClass = Field(description="Classe di apertura fessura applicata, combinazione frequente")
    sigma_lim_fre_MPa: float = Field(description="Tensione limite nell'acciaio, combinazione frequente", json_schema_extra={"unit": "MPa", "symbol": "σ_s,fre,lim"})
    sigma_fre_MPa: float = Field(description="Tensione agente nell'acciaio, combinazione frequente", json_schema_extra={"unit": "MPa", "symbol": "σ_s,fre"})
    utilizzo_fre: float = Field(description="Tasso di sfruttamento, combinazione frequente", json_schema_extra={"unit": "-", "symbol": "σ_s,fre/σ_s,fre,lim", "highlight": True})
    verificato_fre: bool = Field(description="Esito della verifica, combinazione frequente")
    classe_qpe: CrackWidthClass = Field(description="Classe di apertura fessura applicata, combinazione quasi permanente")
    sigma_lim_qpe_MPa: float = Field(description="Tensione limite nell'acciaio, combinazione quasi permanente", json_schema_extra={"unit": "MPa", "symbol": "σ_s,qp,lim"})
    sigma_qpe_MPa: float = Field(description="Tensione agente nell'acciaio, combinazione quasi permanente", json_schema_extra={"unit": "MPa", "symbol": "σ_s,qp"})
    utilizzo_qpe: float = Field(description="Tasso di sfruttamento, combinazione quasi permanente", json_schema_extra={"unit": "-"})
    verificato_qpe: bool = Field(description="Esito della verifica, combinazione quasi permanente")


class AperturaFessureSempOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    sezioni: tuple[VerificaSemplificataSezione, VerificaSemplificataSezione, VerificaSemplificataSezione] = Field(
        description="Verifiche per le tre sezioni (h=30cm bordo, h=30cm zona centrale, h=20cm)"
    )
