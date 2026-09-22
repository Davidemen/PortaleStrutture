"""Pydantic I/O models for the `muro-sostegno` tool (cantilever retaining wall, per metre run).

Inputs stay FLAT, ordered as in the sheet (rows 4-39). Outputs are nested per calculation group:
`geometria` (shared geometry/weights), `parametri_sismici` (Ss/ST/S), `spinte` (Tool 1 — active
thrust per combination), `ribaltamento_scorrimento` (Tool 2), `pressioni_terreno` (Tool 3).

Extension point for the reinforcement-design agent: append new nested result models below
`PressioniCombo` (e.g. `ArmaturaParamentoResult`, `ArmaturaFondazioneValleResult`,
`ArmaturaFondazioneMonteResult`) and new optional fields on `MuroSostegnoOutput` — see the
`# --- reinforcement design (appended by a later agent) ---` marker at the bottom of this file.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from strutture.shared.capacita_portante import Condizione
from strutture.shared.materials.concrete import ConcreteClass
from strutture.shared.materials.rebar import RebarGrade
from strutture.shared.ntc_site_seismic import CategoriaSottosuolo, CategoriaTopografica
from strutture.shared.report import Check
from strutture.shared.sketch import Sketch, campo_schizzo

NomeCombo = Literal["STR_1", "STR_2", "GEO_1", "GEO_2", "EQU_1", "EQU_2", "SISMA_1", "SISMA_2"]


class MuroSostegnoInput(BaseModel):
    """Muro!I4:I38 (shared geometry/soil/seismic block feeding all combinations)."""

    model_config = ConfigDict(frozen=True)

    # --- Sito ---------------------------------------------------------------------------------
    ag_g: float = Field(description="Accelerazione orizzontale massima al sito", gt=0, lt=1, json_schema_extra={"unit": "g", "symbol": "a_g", "group": "Sito"})
    f0: float = Field(description="Fattore massimo di amplificazione dello spettro in accelerazione orizzontale", gt=0, json_schema_extra={"unit": "-", "symbol": "F_0", "group": "Sito"})
    categoria_sottosuolo: CategoriaSottosuolo = Field(description="Categoria di sottosuolo (governa il coefficiente Ss, Tab. 3.2.IV)", json_schema_extra={"group": "Sito"})
    categoria_topografica: CategoriaTopografica = Field(description="Categoria topografica (governa il coefficiente ST, Tab. 3.2.V)", json_schema_extra={"group": "Sito"})
    beta_m: float = Field(description="Fattore di riduzione dell'accelerazione massima attesa al sito", gt=0, le=1, json_schema_extra={"unit": "-", "symbol": "β_m", "group": "Sito"})
    gamma_e: float = Field(
        default=1.0,
        description="Fattore moltiplicativo sulla spinta sismica (raramente diverso da 1)",
        gt=0,
        json_schema_extra={"unit": "-", "symbol": "γ_E", "group": "Sito", "advanced": True},
    )

    # --- Geometria ------------------------------------------------------------------------------
    beta_deg: float = Field(description="Angolo di inclinazione del pendio a tergo del muro", ge=0, lt=45, json_schema_extra={"unit": "°", "symbol": "β", "group": "Geometria"})
    psi_deg: float = Field(description="Angolo di inclinazione del paramento interno (90° = verticale)", gt=0, lt=180, json_schema_extra={"unit": "°", "symbol": "ψ", "group": "Geometria"})
    omega_deg: float = Field(description="Angolo di inclinazione della base di fondazione", ge=-30, le=30, json_schema_extra={"unit": "°", "symbol": "ω", "group": "Geometria"})
    s_base_m: float = Field(description="Spessore del muro alla base", gt=0, json_schema_extra={"unit": "m", "symbol": "s_base", "group": "Geometria"})
    s_top_m: float = Field(description="Spessore del muro in sommità", gt=0, json_schema_extra={"unit": "m", "symbol": "s_top", "group": "Geometria"})
    s_fond_m: float = Field(description="Spessore della fondazione", gt=0, json_schema_extra={"unit": "m", "symbol": "s_fond", "group": "Geometria"})
    h_muro_m: float = Field(description="Altezza del muro fuori terra", gt=0, json_schema_extra={"unit": "m", "symbol": "h_muro", "group": "Geometria"})
    b_valle_m: float = Field(description="Larghezza della fondazione lato valle (mancia)", gt=0, json_schema_extra={"unit": "m", "symbol": "B_valle", "group": "Geometria"})
    b_monte_m: float = Field(description="Larghezza della fondazione lato monte (tacco)", gt=0, json_schema_extra={"unit": "m", "symbol": "B_monte", "group": "Geometria"})

    # --- Materiali ------------------------------------------------------------------------------
    gamma_terr_sat_kN_m3: float = Field(description="Peso di volume del terreno saturo", gt=0, json_schema_extra={"unit": "kN/m3", "symbol": "γ_terr", "group": "Materiali"})
    gamma_terr_secco_kN_m3: float = Field(description="Peso di volume del terreno secco", gt=0, json_schema_extra={"unit": "kN/m3", "symbol": "γ'_terr", "group": "Materiali"})
    phi_deg: float = Field(description="Angolo di attrito interno del terreno", gt=0, lt=45, json_schema_extra={"unit": "°", "symbol": "φ", "group": "Materiali"})
    delta_deg: float = Field(description="Angolo di attrito terreno-muro", ge=0, lt=45, json_schema_extra={"unit": "°", "symbol": "δ", "group": "Materiali"})
    gamma_cls_kN_m3: float = Field(description="Peso di volume del calcestruzzo", gt=0, json_schema_extra={"unit": "kN/m3", "symbol": "γ_cls", "group": "Materiali"})
    grado_acciaio: RebarGrade = Field(description="Grado dell'acciaio da armatura (governa fyk/fyd, NTC2018 §11.3.2)", json_schema_extra={"group": "Materiali"})
    tipo_cls: ConcreteClass = Field(
        default="C25/30",
        description="Classe di resistenza del calcestruzzo (governa fctm per l'armatura minima, NTC2018 §4.1.6.1.1)",
        json_schema_extra={"group": "Materiali"},
    )

    # --- Azioni ---------------------------------------------------------------------------------
    q_kN_m2: float = Field(description="Sovraccarico variabile a tergo del muro", ge=0, json_schema_extra={"unit": "kN/m2", "symbol": "q", "group": "Azioni"})

    # --- Armatura -------------------------------------------------------------------------------
    copertura_paramento_m: float = Field(description="Copriferro asse barre verticali del paramento", gt=0, json_schema_extra={"unit": "m", "symbol": "c_muro", "group": "Armatura"})
    passo_arm_paramento_m: float = Field(description="Passo delle armature verticali del paramento", gt=0, json_schema_extra={"unit": "m", "symbol": "s_muro", "group": "Armatura"})
    copertura_fondazione_m: float = Field(description="Copriferro asse barre trasversali della fondazione (comune a valle e monte)", gt=0, json_schema_extra={"unit": "m", "symbol": "c_fond", "group": "Armatura"})
    passo_arm_fondazione_m: float = Field(description="Passo delle armature della fondazione (comune a valle e monte)", gt=0, json_schema_extra={"unit": "m", "symbol": "s_fond", "group": "Armatura"})

    # --- Terreno di fondazione (facoltativo, docs/architecture-phase4.md §C "Integration") -----
    terreno_condizione: Condizione | None = Field(
        default=None,
        description="Condizione del terreno di fondazione per la verifica di capacità portante: se non selezionata, la verifica non viene calcolata (compilare l'intero blocco per attivarla)",
        json_schema_extra={"group": "Terreno di fondazione"},
    )
    terreno_phi_k_deg: float | None = Field(
        default=None, gt=0, lt=45,
        description="Angolo di attrito interno caratteristico del terreno di fondazione φ'k (condizione drenata)",
        json_schema_extra={"unit": "°", "symbol": "φ'_k", "group": "Terreno di fondazione", "condition": {"field": "terreno_condizione", "equals": ["drenata"]}},
    )
    terreno_c_k_kpa: float | None = Field(
        default=None, ge=0,
        description="Coesione efficace caratteristica del terreno di fondazione c'k (condizione drenata)",
        json_schema_extra={"unit": "kPa", "symbol": "c'_k", "group": "Terreno di fondazione", "condition": {"field": "terreno_condizione", "equals": ["drenata"]}},
    )
    terreno_cu_k_kpa: float | None = Field(
        default=None, gt=0,
        description="Resistenza al taglio non drenata caratteristica del terreno di fondazione cu,k (condizione non drenata)",
        json_schema_extra={"unit": "kPa", "symbol": "c_u,k", "group": "Terreno di fondazione", "condition": {"field": "terreno_condizione", "equals": ["non_drenata"]}},
    )
    terreno_gamma_kn_m3: float | None = Field(
        default=None, gt=0,
        description="Peso di volume del terreno di fondazione γ",
        json_schema_extra={"unit": "kN/m3", "symbol": "γ_fond", "group": "Terreno di fondazione", "condition": {"field": "terreno_condizione", "equals": ["drenata", "non_drenata"]}},
    )
    terreno_profondita_posa_m: float | None = Field(
        default=None, ge=0,
        description="Approfondimento del piano di posa della fondazione D, misurato dal piano campagna "
                    "a VALLE (lato mancia, non il piano campagna a monte/tacco: un valore riferito al "
                    "monte sovrastima il sovraccarico q' e la capacità portante, vedi l'avviso se D "
                    "supera l'altezza fuori terra del muro h_muro)",
        json_schema_extra={"unit": "m", "symbol": "D", "group": "Terreno di fondazione", "condition": {"field": "terreno_condizione", "equals": ["drenata", "non_drenata"]}},
    )
    terreno_profondita_falda_m: float | None = Field(
        default=None, ge=0,
        description="Profondità della falda dal piano di campagna, stesso riferimento di D (facoltativa: se assente si assume falda assente)",
        json_schema_extra={"unit": "m", "symbol": "z_w", "group": "Terreno di fondazione", "condition": {"field": "terreno_condizione", "equals": ["drenata", "non_drenata"]}},
    )

    # --- Avanzate ---------------------------------------------------------------------------------
    legacy_compat: bool = Field(default=False, description="Riproduci il foglio Excel originale (errori inclusi)", json_schema_extra={"group": "Avanzate", "advanced": True})

    @model_validator(mode="after")
    def _terreno_fondazione_coerente(self) -> "MuroSostegnoInput":
        """Cross-field validation of the optional 'Terreno di fondazione' block: when a
        `terreno_condizione` is selected, the fields the chosen condition needs must be present.

        HIGH finding: a block filled in the OPPOSITE direction (phi'k/c'k/gamma/D valorized but
        `terreno_condizione` left unset) used to be skipped in silence (both branches returned
        immediately on `terreno_condizione is None`): `capacita_portante_fondazione` came back
        `None` with only the generic "non calcolata da questo strumento" warning, and the engineer
        believed the check had run. Rejected explicitly here instead."""
        campi_blocco_valorizzati = [
            nome for nome, valore in (
                ("terreno_phi_k_deg", self.terreno_phi_k_deg), ("terreno_c_k_kpa", self.terreno_c_k_kpa),
                ("terreno_cu_k_kpa", self.terreno_cu_k_kpa), ("terreno_gamma_kn_m3", self.terreno_gamma_kn_m3),
                ("terreno_profondita_posa_m", self.terreno_profondita_posa_m),
                ("terreno_profondita_falda_m", self.terreno_profondita_falda_m),
            ) if valore is not None
        ]
        if self.terreno_condizione is None:
            if campi_blocco_valorizzati:
                raise ValueError(
                    "blocco 'Terreno di fondazione': selezionare la condizione di drenaggio "
                    "(terreno_condizione) per attivare la verifica di capacità portante, oppure "
                    f"svuotare i campi {', '.join(campi_blocco_valorizzati)}"
                )
            return self
        mancanti = [
            nome for nome, valore in (
                ("terreno_gamma_kn_m3", self.terreno_gamma_kn_m3),
                ("terreno_profondita_posa_m", self.terreno_profondita_posa_m),
            ) if valore is None
        ]
        if self.terreno_condizione == "drenata":
            mancanti += [n for n, v in (("terreno_phi_k_deg", self.terreno_phi_k_deg), ("terreno_c_k_kpa", self.terreno_c_k_kpa)) if v is None]
        else:
            mancanti += [n for n, v in (("terreno_cu_k_kpa", self.terreno_cu_k_kpa),) if v is None]
        if mancanti:
            raise ValueError(
                f"blocco 'Terreno di fondazione': con condizione='{self.terreno_condizione}' sono obbligatori i campi {', '.join(mancanti)}"
            )
        return self


# --- geometria / parametri sismici (comuni a tutte le combinazioni) ----------------------------


class GeometriaResult(BaseModel):
    """Muro!I30, I33:I35, I11:I12, I39."""

    model_config = ConfigDict(frozen=True)

    h_muro_tot_m: float = Field(description="Altezza totale del muro (fusto + fondazione)", gt=0, json_schema_extra={"unit": "m", "symbol": "H"})
    b_fond_m: float = Field(description="Larghezza totale della fondazione", gt=0, json_schema_extra={"unit": "m", "symbol": "B"})
    a_muro_m2: float = Field(description="Area della sezione trasversale del muro (fusto + fondazione)", gt=0, json_schema_extra={"unit": "m2"})
    x_muro_m: float = Field(description="Baricentro del muro dal polo di ribaltamento (punta valle)", gt=0, json_schema_extra={"unit": "m"})
    z_muro_m: float = Field(description="Baricentro del muro dalla base della fondazione (braccio verticale per l'inerzia sismica)", gt=0, json_schema_extra={"unit": "m"})
    a_terr_m2: float = Field(description="Area della sezione trasversale del cuneo di terreno a tergo", ge=0, json_schema_extra={"unit": "m2"})
    x_terr_m: float = Field(description="Baricentro del terreno dal polo di ribaltamento", gt=0, json_schema_extra={"unit": "m"})
    z_terr_m: float = Field(description="Baricentro del cuneo di terreno dalla base della fondazione (braccio verticale per l'inerzia sismica)", gt=0, json_schema_extra={"unit": "m"})
    x_sv_m: float = Field(description="Baricentro del sovraccarico dal polo di ribaltamento", gt=0, json_schema_extra={"unit": "m"})


class ParametriSismiciResult(BaseModel):
    """Muro!I18:I20 (Ss/ST/S, sempre calcolati dalla categoria di sottosuolo/topografica)."""

    model_config = ConfigDict(frozen=True)

    ss: float = Field(description="Coefficiente di amplificazione stratigrafica", gt=0, json_schema_extra={"unit": "-", "symbol": "S_S"})
    st: float = Field(description="Coefficiente di amplificazione topografica", gt=0, json_schema_extra={"unit": "-", "symbol": "S_T"})
    s: float = Field(description="Coefficiente che tiene conto della categoria di sottosuolo, S = Ss·ST", gt=0, json_schema_extra={"unit": "-", "symbol": "S"})


# --- Tool 1: spinta-terra-statica-sismica -------------------------------------------------------


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


# --- Tool 2: verifica-ribaltamento-scorrimento --------------------------------------------------


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


# --- Tool 3: verifica-pressioni-terreno ----------------------------------------------------------


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


# --- Capacità portante del terreno di fondazione (facoltativa) ----------------------------------


class CapacitaPortanteCombo(BaseModel):
    """One row of the bearing-capacity check on the strip footing (docs/architecture-phase4.md §C
    "Integration"): q_lim/R_d computed by `strutture.shared.capacita_portante` on the base nastriforme
    (per metro, L'->infinito, fattori di forma=1), with B'=B-2e from this combination's
    `pressioni_terreno.eccentricita_m` and H/V from its `ribaltamento_scorrimento` resultants.
    Present only when the optional 'Terreno di fondazione' block is filled (legacy_compat=False)."""

    model_config = ConfigDict(frozen=True)

    nome: NomeCombo = Field(description="Identificativo della combinazione")
    q_lim_kPa: float = Field(description="Pressione limite di capacità portante", ge=0, json_schema_extra={"unit": "kPa", "symbol": "q_lim"})
    r_d_kN: float = Field(description="Resistenza di progetto, per metro di sviluppo del muro", ge=0, json_schema_extra={"unit": "kN", "symbol": "R_d"})
    rapporto: float = Field(description="Grado di sfruttamento del terreno di fondazione", ge=0, json_schema_extra={"unit": "-", "symbol": "N_Ed/R_d"})


class CapacitaPortanteFondazioneResult(BaseModel):
    """Composed result: q_lim/R_d/rapporto per combinazione + la combinazione governante."""

    model_config = ConfigDict(frozen=True)

    combinazioni: tuple[CapacitaPortanteCombo, ...] = Field(
        description="q_lim, R_d e grado di sfruttamento per combinazione (STR_1, STR_2, SISMA_1, SISMA_2: "
                    "le uniche coerenti con i parametri caratteristici del terreno non ridotti e il γR usati "
                    "qui; GEO_1/GEO_2/EQU_1/EQU_2 userebbero uno schema Approccio/γR diverso, non implementato)")
    combo_governante: NomeCombo = Field(description="Combinazione con il grado di sfruttamento N_Ed/R_d maggiore")
    rapporto_governante: float = Field(
        description="Grado di sfruttamento governante N_Ed/R_d", ge=0,
        json_schema_extra={"unit": "-", "symbol": "N_Ed/R_d", "highlight": True},
    )
    verifica: Check = Field(description="Esito della verifica di capacità portante sulla combinazione governante (N_Ed ≤ R_d)")


# --- Tool 4: armatura-paramento ------------------------------------------------------------------


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


# --- Tool 5: armatura-fondazione-valle --------------------------------------------------------------


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


# --- Tool 6: armatura-fondazione-monte --------------------------------------------------------------


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


class MuroSostegnoOutput(BaseModel):
    """Composed output of the `muro-sostegno` tool: shared geometry + one row per combination for
    each of the three verification groups. `spinte`/`ribaltamento_scorrimento`/`pressioni_terreno`
    all carry 8 rows in the same order: STR_1, STR_2, GEO_1, GEO_2, EQU_1, EQU_2, SISMA_1, SISMA_2.
    """

    model_config = ConfigDict(frozen=True)

    geometria: GeometriaResult = Field(description="Geometria e pesi del muro/terreno, comuni a tutte le combinazioni")
    parametri_sismici: ParametriSismiciResult = Field(description="Coefficienti di amplificazione sismica")
    spinte: tuple[SpintaCombo, ...] = Field(description="Spinta attiva statica/sismica per combinazione")
    ribaltamento_scorrimento: tuple[RibaltamentoScorrimentoCombo, ...] = Field(description="Verifiche a ribaltamento e scorrimento per combinazione")
    pressioni_terreno: tuple[PressioniCombo, ...] = Field(
        description="Pressioni sul terreno ed eccentricità per combinazione",
        json_schema_extra={
            "chart": {
                "x": "nome", "y": ["p_valle_kPa", "p_monte_kPa"],
                "x_label": "Combinazione", "y_label": "Pressione sul terreno [kPa]",
            },
        },
    )
    capacita_portante_fondazione: CapacitaPortanteFondazioneResult | None = Field(
        default=None,
        description="Verifica di capacità portante del terreno di fondazione (calcolata solo se il blocco 'Terreno di fondazione' è compilato in modalità standard)",
    )
    armatura_paramento: ArmaturaParamentoResult = Field(description="Armatura verticale del paramento")
    armatura_fondazione_valle: ArmaturaFondazioneValleResult = Field(description="Armatura della fondazione di valle/mancia")
    armatura_fondazione_monte: ArmaturaFondazioneMonteResult = Field(description="Armatura della fondazione di monte/tacco")
    schizzo: Sketch | None = campo_schizzo()
