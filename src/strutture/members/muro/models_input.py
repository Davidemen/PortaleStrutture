"""Input model of the `muro-sostegno` tool (split out of `models.py`, regola dura 12 dei moduli
piccoli). Inputs stay FLAT, ordered as in the sheet (rows 4-39).
"""
from pydantic import BaseModel, ConfigDict, Field, model_validator

from strutture.shared.capacita_portante import Condizione
from strutture.shared.materials.concrete import ConcreteClass
from strutture.shared.materials.rebar import RebarGrade
from strutture.shared.ntc_site_seismic import CategoriaSottosuolo, CategoriaTopografica


class MuroSostegnoInput(BaseModel):
    """Muro!I4:I38 (shared geometry/soil/seismic block feeding all combinations)."""

    model_config = ConfigDict(frozen=True)

    # --- Sito ---------------------------------------------------------------------------------
    ag_g: float = Field(description="Accelerazione orizzontale massima al sito", gt=0, lt=1, json_schema_extra={"accepts": "sito.ag_g", "unit": "g", "symbol": "a_g", "group": "Sito"})
    f0: float = Field(description="Fattore massimo di amplificazione dello spettro in accelerazione orizzontale", gt=0, json_schema_extra={"accepts": "sito.f0", "unit": "-", "symbol": "F_0", "group": "Sito"})
    categoria_sottosuolo: CategoriaSottosuolo = Field(description="Categoria di sottosuolo (governa il coefficiente Ss, Tab. 3.2.IV)", json_schema_extra={"accepts": "sito.categoria_sottosuolo", "group": "Sito"})
    categoria_topografica: CategoriaTopografica = Field(description="Categoria topografica (governa il coefficiente ST, Tab. 3.2.V)", json_schema_extra={"accepts": "sito.categoria_topografica", "group": "Sito"})
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
