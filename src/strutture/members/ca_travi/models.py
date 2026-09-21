"""Pydantic models for the composed tool `ca-trave-rettangolare` (rectangular RC beam,
design + verification). See docs/specs/ca-travi.md and `tool.py` for the composition order.

To add a new output group: add the new FLAT input fields to `TraveRettangolareInput` at the
position matching their row on the 'Travi sez. rettangolare' sheet (never append at the end),
add a new frozen `<Gruppo>Output` model below, and add the matching nested field to
`TraveRettangolareOutput`. Never edit or remove the fields already defined here.

SLS groups (`SleTensioniOutput`/Tool 4, `FessurazioneOutput`/Tool 5) were added in a second pass
following exactly this recipe; see `sle_tensioni.py`/`fessurazione.py` and `tool.py`.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from strutture.shared.materials.concrete import ConcreteClass, ConcreteProperties
from strutture.shared.materials.rebar import RebarGrade, RebarProperties
from strutture.shared.sketch import Sketch, campo_schizzo

ClasseDuttilita = Literal["CDA", "CDB"]

# Sheet 'Travi sez. rettangolare' Y50/Y51/Y52/Z54 dropdowns (Tool 4/5, NTC2018 §4.1.2.2.4/.5).
CondizioniAmbientali = Literal["Ordinarie", "Aggressive", "Molto aggressive"]
Combinazione = Literal["Frequente", "Quasi permanente"]
SensibilitaArmatura = Literal["Poco sensibile", "Sensibile"]
ClasseAperturaFessura = Literal["w1", "w2", "w3"]


class TraveRettangolareInput(BaseModel):
    """Flat inputs, ordered as the rows of sheet 'Travi sez. rettangolare' (H6 ... K80)."""

    model_config = ConfigDict(frozen=True)

    b_mm: float = Field(description="Base della trave", json_schema_extra={"unit": "mm", "symbol": "b", "group": "Geometria della sezione"}, gt=0)
    h_mm: float = Field(description="Altezza netta della trave", json_schema_extra={"unit": "mm", "symbol": "h", "group": "Geometria della sezione"}, gt=0)
    tipo_acciaio: RebarGrade = Field(description="Tipo di acciaio da armatura", json_schema_extra={"group": "Materiali"})
    tipo_cls: ConcreteClass = Field(description="Tipo di calcestruzzo", json_schema_extra={"group": "Materiali"})
    copriferro_mm: float = Field(description="Copriferro, misurato all'asse delle barre", json_schema_extra={"unit": "mm", "symbol": "c", "group": "Geometria della sezione"}, gt=0)
    n_ferri1: int = Field(description="Numero di ferri tesi, primo strato", ge=1, le=50, json_schema_extra={"group": "Geometria della sezione"})
    diametro_ferri1_mm: float = Field(description="Diametro dei ferri tesi, primo strato", json_schema_extra={"unit": "mm", "symbol": "⌀_1", "group": "Geometria della sezione"}, gt=0)
    n_ferri2: int = Field(default=0, description="Numero di ferri tesi, secondo strato (0 se assente)", ge=0, le=50, json_schema_extra={"group": "Geometria della sezione"})
    diametro_ferri2_mm: float = Field(
        default=0.0, description="Diametro dei ferri tesi, secondo strato", json_schema_extra={"unit": "mm", "symbol": "⌀_2", "group": "Geometria della sezione"}, ge=0
    )
    diametro_staffe1_mm: float = Field(description="Diametro delle staffe, primo tratto", json_schema_extra={"unit": "mm", "symbol": "⌀_sw,1", "group": "Geometria della sezione"}, gt=0)
    passo_staffe1_mm: float = Field(description="Passo delle staffe, primo tratto", json_schema_extra={"unit": "mm", "symbol": "s_1", "group": "Geometria della sezione"}, gt=0)
    n_bracci_staffe1: int = Field(default=2, description="Numero di bracci delle staffe, primo tratto", gt=0, le=12, json_schema_extra={"group": "Geometria della sezione"})
    diametro_staffe2_mm: float = Field(
        default=0.0, description="Diametro delle staffe, secondo tratto (0 se assente)", json_schema_extra={"unit": "mm", "symbol": "⌀_sw,2", "group": "Geometria della sezione"}, ge=0
    )
    n_bracci_staffe2: int = Field(default=0, description="Numero di bracci delle staffe, secondo tratto", ge=0, le=12, json_schema_extra={"group": "Geometria della sezione"})
    alpha_staffe_deg: float = Field(
        default=90.0,
        description="Inclinazione delle staffe rispetto all'asse della trave",
        json_schema_extra={"unit": "°", "symbol": "α", "group": "Geometria della sezione", "advanced": True},
        gt=0,
        le=90,
    )
    ved_kN: float = Field(description="Taglio di calcolo allo SLU", json_schema_extra={"unit": "kN", "symbol": "V_Ed", "group": "Sollecitazioni di progetto"}, ge=0)
    med_slu_kNm: float = Field(description="Momento flettente di calcolo allo SLU", json_schema_extra={"unit": "kNm", "symbol": "M_Ed", "group": "Sollecitazioni di progetto"}, gt=0)
    med_rara_kNm: float = Field(
        description="Momento flettente di esercizio, combinazione rara", json_schema_extra={"unit": "kNm", "symbol": "M_Ed,rara", "group": "Sollecitazioni di progetto"}, gt=0
    )
    med_qp_kNm: float = Field(
        description="Momento flettente di esercizio, combinazione quasi permanente",
        json_schema_extra={"unit": "kNm", "symbol": "M_Ed,qp", "group": "Sollecitazioni di progetto"},
        gt=0,
    )
    condizioni_ambientali: CondizioniAmbientali = Field(
        default="Ordinarie", description="Condizioni ambientali (aggressività dell'esposizione)",
        json_schema_extra={"group": "Combinazione"},
    )
    combinazione: Combinazione = Field(
        default="Frequente", description="Combinazione di carico per la verifica di fessurazione",
        json_schema_extra={"group": "Combinazione"},
    )
    sensibilita_armatura: SensibilitaArmatura = Field(
        default="Poco sensibile", description="Sensibilità dell'armatura alla corrosione",
        json_schema_extra={"group": "Combinazione"},
    )
    classe_apertura_fessura: ClasseAperturaFessura = Field(
        default="w3", description="Classe di apertura di fessura ammessa",
        json_schema_extra={"group": "Combinazione"},
    )
    classe_duttilita: ClasseDuttilita = Field(
        default="CDB", description="Classe di duttilità della struttura",
        json_schema_extra={"group": "Parametri di calcolo"},
    )
    mrc_kNm: float = Field(description="Momento resistente del pilastro convergente nel nodo", json_schema_extra={"unit": "kNm", "symbol": "M_Rc", "group": "Sollecitazioni di progetto"}, gt=0)
    lt_m: float = Field(description="Luce della trave", json_schema_extra={"unit": "m", "symbol": "L_t", "group": "Geometria della sezione"}, gt=0)
    v_gravita_kN: float = Field(
        default=0.0, ge=0,
        description="Taglio dovuto ai carichi gravitazionali della combinazione sismica, trave considerata "
                    "appoggiata agli estremi: si somma al taglio di gerarchia delle resistenze (NTC2018 §7.4.4.1.1)",
        json_schema_extra={"unit": "kN", "symbol": "V_g", "group": "Sollecitazioni di progetto"},
    )
    legacy_compat: bool = Field(
        default=False, description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"advanced": True, "group": "Avanzate"},
    )

    @model_validator(mode="after")
    def _check_copriferro(self) -> "TraveRettangolareInput":
        if self.copriferro_mm >= self.h_mm:
            raise ValueError("il copriferro deve essere minore dell'altezza della sezione")
        return self

    @model_validator(mode="after")
    def _check_ferri_tipo2(self) -> "TraveRettangolareInput":
        if self.n_ferri2 > 0 and self.diametro_ferri2_mm <= 0:
            raise ValueError("il diametro dei ferri tipo 2 deve essere positivo se n_ferri2 > 0")
        return self

    @model_validator(mode="after")
    def _check_staffe_tipo2(self) -> "TraveRettangolareInput":
        if self.n_bracci_staffe2 > 0 and self.diametro_staffe2_mm <= 0:
            raise ValueError("il diametro delle staffe tipo 2 deve essere positivo se n_bracci_staffe2 > 0")
        return self


class MaterialiOutput(BaseModel):
    """Proprietà dei materiali (Tool 0), risolte tramite `strutture.shared.materials`."""

    model_config = ConfigDict(frozen=True)

    calcestruzzo: ConcreteProperties = Field(description="Proprietà meccaniche del calcestruzzo")
    acciaio: RebarProperties = Field(description="Proprietà meccaniche dell'acciaio da armatura")


class ArmaturaLimitiOutput(BaseModel):
    """Limiti di armatura longitudinale/trasversale (Tool 1), NTC2018 §4.1.6.1.1."""

    model_config = ConfigDict(frozen=True)

    z_mm: float = Field(description="Braccio di leva interno", json_schema_extra={"unit": "mm", "symbol": "z"})
    as_o_mm2: float = Field(description="Area di armatura tesa presente", json_schema_extra={"unit": "mm²", "symbol": "A_s"})
    as_min_mm2: float = Field(description="Area minima di armatura tesa", json_schema_extra={"unit": "mm²", "symbol": "A_s,min"})
    as_max_mm2: float = Field(description="Area massima di armatura tesa", json_schema_extra={"unit": "mm²", "symbol": "A_s,max"})
    asw_per_m_mm2: float = Field(description="Area di staffe per metro presente", json_schema_extra={"unit": "mm²/m", "symbol": "A_sw"})
    ast_min_per_m_mm2: float = Field(description="Area minima di staffe per metro", json_schema_extra={"unit": "mm²/m", "symbol": "A_sw,min"})
    passo_max_staffe_mm: float = Field(description="Passo massimo ammesso delle staffe", json_schema_extra={"unit": "mm"})
    as_comp_mm2: float = Field(
        description="Area di armatura compressa presente, dal secondo strato di ferri riusato come "
        "armatura compressa per la verifica sismica",
        json_schema_extra={"unit": "mm²", "symbol": "A_s'"},
    )
    rho_tesa: float = Field(description="Percentuale geometrica di armatura tesa", json_schema_extra={"unit": "-", "symbol": "ρ"})
    rho_min_sismico: float = Field(description="Percentuale minima di armatura tesa sismica", json_schema_extra={"unit": "-", "symbol": "ρ_min"})
    rho_max_sismico: float = Field(description="Percentuale massima di armatura tesa sismica", json_schema_extra={"unit": "-", "symbol": "ρ_max"})
    as_comp_min_sismico_mm2: float = Field(
        description="Area minima di armatura compressa sismica",
        json_schema_extra={"unit": "mm²", "symbol": "A_s',min"},
    )


class FlessioneOutput(BaseModel):
    """Verifica a flessione SLU (Tool 2), NTC2018 §4.1.2.3.4.2, blocco di tensioni rettangolare."""

    model_config = ConfigDict(frozen=True)

    d_mm: float = Field(description="Altezza utile della sezione", json_schema_extra={"unit": "mm", "symbol": "d"})
    y_mm: float = Field(description="Profondità dell'asse neutro nel blocco di tensioni", json_schema_extra={"unit": "mm", "symbol": "y"})
    mrd_kNm: float = Field(description="Momento resistente", json_schema_extra={"unit": "kNm", "symbol": "M_Rd", "highlight": True})
    tasso_sfruttamento: float = Field(description="Tasso di sfruttamento a flessione MEd/MRd", json_schema_extra={"unit": "-", "symbol": "M_Ed/M_Rd", "highlight": True})
    eps_s_permille: float = Field(description="Deformazione dell'acciaio teso, per compatibilità delle deformazioni", json_schema_extra={"unit": "‰", "symbol": "ε_s"})
    acciaio_snervato: bool = Field(description="L'acciaio teso è snervato alla crisi della sezione")


class TaglioOutput(BaseModel):
    """Verifica a taglio SLU (Tool 3), NTC2018 §4.1.2.3.5.2, traliccio a inclinazione variabile."""

    model_config = ConfigDict(frozen=True)

    cotg_theta: float = Field(description="Cotangente dell'inclinazione dei puntoni di calcestruzzo", json_schema_extra={"unit": "-", "symbol": "cotg θ"})
    vrdc_kN: float = Field(description="Resistenza a taglio lato calcestruzzo", json_schema_extra={"unit": "kN", "symbol": "V_Rcd"})
    vrds_kN: float = Field(description="Resistenza a taglio lato armatura", json_schema_extra={"unit": "kN", "symbol": "V_Rsd"})
    vrd_kN: float = Field(description="Resistenza a taglio di progetto (minimo fra lato calcestruzzo e lato armatura)", json_schema_extra={"unit": "kN", "symbol": "V_Rd", "highlight": True})


class SleTensioniOutput(BaseModel):
    """Verifica delle tensioni in esercizio (Tool 4), NTC2018 §4.1.2.2.5, sezione parzializzata
    n=15 (`strutture.shared.section_geometry.cracked_neutral_axis`)."""

    model_config = ConfigDict(frozen=True)

    x_mm: float = Field(description="Profondità dell'asse neutro della sezione parzializzata", json_schema_extra={"unit": "mm", "symbol": "x"})
    sigma_c_rara_MPa: float = Field(
        description="Tensione di compressione nel calcestruzzo, combinazione rara", json_schema_extra={"unit": "MPa", "symbol": "σ_c,rara"}
    )
    sigma_s_rara_MPa: float = Field(
        description="Tensione di trazione nell'acciaio, combinazione rara", json_schema_extra={"unit": "MPa", "symbol": "σ_s,rara"}
    )
    sigma_c_qp_MPa: float = Field(
        description="Tensione di compressione nel calcestruzzo, combinazione quasi permanente",
        json_schema_extra={"unit": "MPa", "symbol": "σ_c,qp"},
    )
    sigma_s_qp_MPa: float = Field(
        description="Tensione di trazione nell'acciaio, combinazione quasi permanente", json_schema_extra={"unit": "MPa", "symbol": "σ_s,qp"}
    )
    sigma_s_combinazione_MPa: float = Field(
        description="Tensione nell'acciaio per la combinazione scelta, usata dalla verifica a fessurazione",
        json_schema_extra={"unit": "MPa", "symbol": "σ_s"},
    )
    limite_sigma_c_rara_MPa: float = Field(
        description="Limite di tensione nel calcestruzzo, combinazione rara", json_schema_extra={"unit": "MPa", "symbol": "σ_c,rara,lim"}
    )
    limite_sigma_c_qp_MPa: float = Field(
        description="Limite di tensione nel calcestruzzo, combinazione quasi permanente",
        json_schema_extra={"unit": "MPa", "symbol": "σ_c,qp,lim"},
    )
    limite_sigma_s_MPa: float = Field(
        description="Limite di tensione nell'acciaio", json_schema_extra={"unit": "MPa", "symbol": "σ_s,lim"}
    )


class FessurazioneOutput(BaseModel):
    """Controllo indiretto dell'ampiezza di fessura (Tool 5), NTC2018 §4.1.2.2.4 + Circolare
    7/2019 C4.1.2.2.4.5 Tab. C4.1.II/III (`strutture.shared.rebar_catalog`)."""

    model_config = ConfigDict(frozen=True)

    diametro_max_mm: float = Field(description="Diametro massimo delle barre tese", json_schema_extra={"unit": "mm", "symbol": "⌀_max"})
    sigma_limite_MPa: float = Field(
        description="Tensione limite nell'acciaio per la classe di apertura scelta", json_schema_extra={"unit": "MPa", "symbol": "σ_s,limite"}
    )
    classe_normativa: ClasseAperturaFessura | None = Field(
        description="Classe di apertura di fessura richiesta dalla normativa per l'esposizione, la "
        "combinazione e la sensibilità dell'armatura scelte (assente se è richiesta una verifica a "
        "decompressione anziché un limite di apertura)"
    )


class CapacityDesignOutput(BaseModel):
    """Dettagli costruttivi capacity design CD"A"/CD"B" (Tool 6), NTC2018 §7.4.4.1/§7.4.6."""

    model_config = ConfigDict(frozen=True)

    lunghezza_critica_mm: float = Field(description="Lunghezza della zona critica", json_schema_extra={"unit": "mm", "symbol": "L_cr"})
    passo_max_zona_critica_mm: float = Field(
        description="Passo massimo delle staffe in zona critica", json_schema_extra={"unit": "mm"}
    )
    lunghezza_ancoraggio_mm: float = Field(
        description="Lunghezza minima di ancoraggio del gancio della staffa", json_schema_extra={"unit": "mm"}
    )
    ved_max_kN: float = Field(description="Taglio massimo da gerarchia delle resistenze (capacity design)", json_schema_extra={"unit": "kN", "symbol": "V_Ed,max"})


class TraveRettangolareOutput(BaseModel):
    """Output nidificato del tool composito: un gruppo per step-group del foglio."""

    model_config = ConfigDict(frozen=True)

    materiali: MaterialiOutput
    armatura: ArmaturaLimitiOutput
    flessione: FlessioneOutput
    taglio: TaglioOutput
    sle_tensioni: SleTensioniOutput
    fessurazione: FessurazioneOutput
    dettagli_costruttivi: CapacityDesignOutput
    schizzo: Sketch | None = campo_schizzo()
