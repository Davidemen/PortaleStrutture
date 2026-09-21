"""Pydantic I/O models for the ca-punzonamento tool (EN 1992-1-1 §6.4). Inputs flat, ordered as in
sheet `Shotblast_225N` top to bottom; outputs nested per docs/architecture-batch2.md §1."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from strutture.shared.divergences import legacy
from strutture.shared.ec2_shear.v_rd_max import V_RD_MAX_COEFF_A1_2014
from strutture.shared.sketch import Sketch, campo_schizzo

from .tables import PHI_STAFFA_LEGACY_TYPO_MM, PHI_STAFFA_OPTIONS_MM, PosizionePilastro

COEFF_VRD_MAX_DESCRIPTION = (
    "Coefficiente di vRd,max = c·ν·fcd: 0,4 (EN 1992-1-1/A1:2014, consigliato) oppure 0,5 "
    "(EN 1992-1-1:2004 con Appendice Nazionale italiana)"
)


class PunzonamentoInput(BaseModel):
    """Flat inputs, ordered as in sheet `Shotblast_225N` (D2:D58)."""

    model_config = ConfigDict(frozen=True)

    ved_kN: float = Field(gt=0, description="Taglio di progetto (SLU+SLV) al pilastro", json_schema_extra={"unit": "kN", "symbol": "V_Ed", "group": "Azioni"})
    pterreno_MPa: float = Field(ge=0, description="Pressione del terreno da FEM, sottratta al taglio", json_schema_extra={"unit": "MPa", "symbol": "p", "group": "Azioni"})
    lato_a_mm: float = Field(ge=0, description="Lato 1 del pilastro (0 = pilastro circolare, vedi diametro)", json_schema_extra={"unit": "mm", "symbol": "a", "group": "Geometria"})
    lato_b_mm: float = Field(ge=0, description="Lato 2 del pilastro", json_schema_extra={"unit": "mm", "symbol": "b", "group": "Geometria"})
    h_mm: float = Field(gt=0, description="Spessore del solaio/platea", json_schema_extra={"unit": "mm", "symbol": "H", "group": "Geometria"})
    diametro_mm: float = Field(ge=0, description="Diametro del pilastro/palo circolare", json_schema_extra={"unit": "mm", "symbol": "D", "group": "Geometria", "condition": {"field": "lato_a_mm", "equals": [0]}})
    fck_MPa: float = Field(gt=0, description="Resistenza cilindrica caratteristica del calcestruzzo", json_schema_extra={"unit": "MPa", "symbol": "f_ck", "group": "Materiali"})
    copriferro_mm: float = Field(gt=0, description="Copriferro", json_schema_extra={"unit": "mm", "symbol": "c", "group": "Geometria"})
    posizione: PosizionePilastro = Field(description="Posizione del pilastro (regola il fattore di eccentricità β)", json_schema_extra={"symbol": "β", "group": "Azioni"})
    umanuale_mm: float | None = Field(default=None, ge=0, description="Perimetro di verifica impostato manualmente (vuoto = nessun limite)", json_schema_extra={"unit": "mm", "symbol": "u_man", "group": "Avanzate", "advanced": True})
    a_amanuale_mm2: float | None = Field(default=None, ge=0, description="Area entro il perimetro di verifica impostata manualmente (vuoto = nessun limite)", json_schema_extra={"unit": "mm2", "symbol": "A_a,man", "group": "Avanzate", "advanced": True})
    px_mm: float = Field(gt=0, description="Passo delle armature tese in direzione x", json_schema_extra={"unit": "mm", "symbol": "p_x", "group": "Armatura tesa"})
    py_mm: float = Field(gt=0, description="Passo delle armature tese in direzione y", json_schema_extra={"unit": "mm", "symbol": "p_y", "group": "Armatura tesa"})
    phix_mm: float = Field(gt=0, description="Diametro delle armature tese in direzione x", json_schema_extra={"unit": "mm", "symbol": "φ_x", "group": "Armatura tesa"})
    phiy_mm: float = Field(gt=0, description="Diametro delle armature tese in direzione y", json_schema_extra={"unit": "mm", "symbol": "φ_y", "group": "Armatura tesa"})
    paddx_mm: float = Field(default=0, ge=0, description="Passo delle armature aggiuntive tese in direzione x (0 = nessuna)", json_schema_extra={"unit": "mm", "symbol": "p_ax", "group": "Armatura tesa", "advanced": True})
    paddy_mm: float = Field(default=0, ge=0, description="Passo delle armature aggiuntive tese in direzione y (0 = nessuna)", json_schema_extra={"unit": "mm", "symbol": "p_ay", "group": "Armatura tesa", "advanced": True})
    phiaddx_mm: float = Field(default=0, ge=0, description="Diametro delle armature aggiuntive tese in direzione x", json_schema_extra={"unit": "mm", "symbol": "φ_ax", "group": "Armatura tesa", "advanced": True})
    phiaddy_mm: float = Field(default=0, ge=0, description="Diametro delle armature aggiuntive tese in direzione y", json_schema_extra={"unit": "mm", "symbol": "φ_ay", "group": "Armatura tesa", "advanced": True})
    a1eff_mm: float = Field(gt=0, description="Distanza effettiva della prima fila di cuciture dal filo del pilastro", json_schema_extra={"unit": "mm", "symbol": "a_1,eff", "group": "Armatura a taglio"})
    bu_mm: float = Field(gt=0, description="Distanza dell'ultima fila di cuciture dal perimetro u0,out", json_schema_extra={"unit": "mm", "symbol": "b_u", "group": "Armatura a taglio"})
    st_mm: float = Field(gt=0, description="Passo tangenziale tra le cuciture di una stessa fila", json_schema_extra={"unit": "mm", "symbol": "s_t", "group": "Armatura a taglio"})
    phi_staffa_mm: float = Field(description="Diametro delle cuciture verticali", json_schema_extra={"unit": "mm", "symbol": "φ_w", "group": "Armatura a taglio"})
    n_staffe: int = Field(gt=0, description="Numero effettivo di cuciture per fila circonferenziale", json_schema_extra={"symbol": "n", "group": "Armatura a taglio"})
    coeff_vrd_max: Literal[0.4, 0.5] = Field(
        default=V_RD_MAX_COEFF_A1_2014, description=COEFF_VRD_MAX_DESCRIPTION,
        json_schema_extra={"symbol": "c", "group": "Avanzate", "advanced": True},
    )
    legacy_compat: bool = Field(default=False, description="Riproduci il foglio Excel originale (errori inclusi)", json_schema_extra={"group": "Avanzate", "advanced": True})

    @model_validator(mode="after")
    def _valida_geometria_e_diametro_staffa(self) -> "PunzonamentoInput":
        if self.lato_a_mm == 0 and self.diametro_mm <= 0:
            raise ValueError("pilastro circolare (lato_a_mm=0): indicare il diametro")
        if self.lato_a_mm > 0 and self.lato_b_mm <= 0:
            raise ValueError("pilastro rettangolare: lato_b_mm deve essere positivo")
        allowed = (
            (*PHI_STAFFA_OPTIONS_MM, PHI_STAFFA_LEGACY_TYPO_MM)
            if legacy("ca-punzonamento/diametro-staffa-28-probabile-refuso", self.legacy_compat)
            else PHI_STAFFA_OPTIONS_MM
        )
        if self.phi_staffa_mm not in allowed:
            raise ValueError(f"diametro cuciture non commerciale: {self.phi_staffa_mm} mm (ammessi: {allowed})")
        return self


class GeometriaOutput(BaseModel):
    """Altezza utile e perimetro di verifica al filo del pilastro (spec steps 1-2)."""

    model_config = ConfigDict(frozen=True)

    dx_mm: float = Field(description="Altezza utile in direzione x", json_schema_extra={"unit": "mm", "symbol": "d_x"})
    dy_mm: float = Field(description="Altezza utile in direzione y", json_schema_extra={"unit": "mm", "symbol": "d_y"})
    d_mm: float = Field(description="Altezza utile media", json_schema_extra={"unit": "mm", "symbol": "d"})
    u0_mm: float = Field(description="Perimetro di verifica al filo del pilastro", json_schema_extra={"unit": "mm", "symbol": "u_0"})


class FacciaPilastroOutput(BaseModel):
    """Verifica al filo del pilastro, tensione massima semplificata (spec steps 3-4)."""

    model_config = ConfigDict(frozen=True)

    v_rd_max_MPa: float = Field(description="Tensione massima di punzonamento al perimetro u0", json_schema_extra={"unit": "MPa", "symbol": "v_Rd,max"})
    ved_red_0_kN: float = Field(description="Taglio ridotto della quota di carico scaricata direttamente sul terreno", json_schema_extra={"unit": "kN", "symbol": "V_Ed,red,0"})
    v_ed_0_MPa: float = Field(description="Tensione di punzonamento al perimetro u0", json_schema_extra={"unit": "MPa", "symbol": "v_Ed,0"})


class RigaPerimetro(BaseModel):
    """One sample of the control-perimeter scan (spec step 5, fill-down table AO2:AX152)."""

    model_config = ConfigDict(frozen=True)

    a_su_d: float = Field(description="Rapporto a/d del campione", json_schema_extra={"symbol": "a/d", "unit": "-"})
    a_mm: float = Field(description="Distanza del perimetro dal filo del pilastro", json_schema_extra={"unit": "mm", "symbol": "a"})
    ui_mm: float = Field(description="Lunghezza del perimetro di verifica", json_schema_extra={"unit": "mm", "symbol": "u_i"})
    area_mm2: float = Field(description="Area entro il perimetro di verifica", json_schema_extra={"unit": "mm2", "symbol": "A_a"})
    ved_red_kN: float = Field(description="Taglio ridotto della quota di carico scaricata sul terreno entro l'area", json_schema_extra={"unit": "kN", "symbol": "V_Ed,red"})
    v_rd_i_MPa: float = Field(description="Resistenza a punzonamento del solo calcestruzzo al campione", json_schema_extra={"unit": "MPa", "symbol": "v_Rd,i"})
    v_ed_i_MPa: float = Field(description="Tensione di punzonamento al campione", json_schema_extra={"unit": "MPa", "symbol": "v_Ed,i"})
    rapporto: float = Field(description="Rapporto v_Ed,i / v_Rd,i, massimizzato dalla scansione", json_schema_extra={"symbol": "v_Ed,i/v_Rd,i", "unit": "-"})


class PerimetroCriticoOutput(BaseModel):
    """Scansione del perimetro critico e verifica a punzonamento senza armatura (spec steps 5-12)."""

    model_config = ConfigDict(frozen=True)

    righe: tuple[RigaPerimetro, ...] = Field(
        description="Scansione di a/d in [0.5, 2.0]",
        json_schema_extra={"chart": {"x": "a_su_d", "y": ["v_ed_i_MPa", "v_rd_i_MPa"], "x_label": "a/d", "y_label": "Tensione [MPa]", "guides": [{"field": "a_governante_su_d", "label": "a/d governante"}]}},
    )
    a_governante_su_d: float = Field(description="Rapporto a/d del perimetro governante", json_schema_extra={"symbol": "(a/d)*", "unit": "-"})
    a_governante_mm: float = Field(description="Distanza del perimetro governante dal filo del pilastro", json_schema_extra={"unit": "mm", "symbol": "a"})
    ui_mm: float = Field(description="Lunghezza del perimetro governante", json_schema_extra={"unit": "mm", "symbol": "u_i"})
    area_mm2: float = Field(description="Area entro il perimetro governante", json_schema_extra={"unit": "mm2", "symbol": "A_a"})
    rho: float = Field(description="Percentuale geometrica di armatura tesa (media geometrica x/y, capped 2%)", json_schema_extra={"symbol": "ρ_l", "unit": "-"})
    k: float = Field(description="Fattore di scala (effetto dimensionale)", json_schema_extra={"symbol": "k", "unit": "-"})
    ved_red_ui_kN: float = Field(description="Taglio ridotto al perimetro governante", json_schema_extra={"unit": "kN", "symbol": "V_Ed,red,ui"})
    v_rd_i_MPa: float = Field(description="Resistenza a punzonamento del solo calcestruzzo al perimetro governante", json_schema_extra={"unit": "MPa", "symbol": "v_Rd,i"})
    v_ed_i_MPa: float = Field(description="Tensione di punzonamento al perimetro governante", json_schema_extra={"unit": "MPa", "symbol": "v_Ed,i"})
    rapporto: float = Field(description="Rapporto v_Ed,i / v_Rd,i al perimetro governante", json_schema_extra={"symbol": "v_Ed,i/v_Rd,i", "unit": "-", "highlight": True})
    armatura_necessaria: bool = Field(description="Esito: è necessario il progetto delle armature a punzonamento")


class ArmaturaOutput(BaseModel):
    """Progetto delle armature verticali a punzonamento (spec steps 13-23), presente solo quando
    `armatura_necessaria` è vero in modalità codice; sempre presente in modalità foglio (bug #5)."""

    model_config = ConfigDict(frozen=True)

    u0_out_mm: float = Field(description="Perimetro oltre il quale non serve armatura a taglio", json_schema_extra={"unit": "mm", "symbol": "u_0,out"})
    k_d_primo_mm: float = Field(description="Distanza da u0,out oltre i lati rettilinei del pilastro", json_schema_extra={"unit": "mm", "symbol": "k'd"})
    sr_max_mm: float = Field(description="Passo massimo radiale tra le file di cuciture", json_schema_extra={"unit": "mm", "symbol": "s_r,max"})
    a1_min_mm: float = Field(description="Distanza minima della prima fila dal filo del pilastro", json_schema_extra={"unit": "mm", "symbol": "a_1,min"})
    a1_max_mm: float = Field(description="Distanza massima della prima fila dal filo del pilastro", json_schema_extra={"unit": "mm", "symbol": "a_1,max"})
    au_mm: float = Field(description="Distanza dell'ultima fila dal filo del pilastro", json_schema_extra={"unit": "mm", "symbol": "a_u"})
    au_meno_a1_mm: float = Field(description="Distanza tra la prima e l'ultima fila", json_schema_extra={"unit": "mm", "symbol": "a_u-a_1"})
    n_file: int = Field(description="Numero di file radiali di cuciture", json_schema_extra={"symbol": "n_file"})
    sr_mm: float = Field(description="Interasse effettivo tra le file", json_schema_extra={"unit": "mm", "symbol": "s_r"})
    asw_min_mm2: float = Field(description="Area minima di ogni cucitura verticale (EC2 §9.4.3(2))", json_schema_extra={"unit": "mm2", "symbol": "A_sw,min"})
    v_rd_cs_min_kN: float = Field(description="Taglio minimo richiesto lato acciaio al perimetro governante", json_schema_extra={"unit": "kN", "symbol": "V'_Rd,cs,min"})
    fywd_ef_MPa: float = Field(description="Tensione di calcolo efficace delle cuciture (EC2 eq. 6.52)", json_schema_extra={"unit": "MPa", "symbol": "f_ywd,ef"})
    area_staffa_mm2: float = Field(description="Area di una cucitura verticale", json_schema_extra={"unit": "mm2", "symbol": "A_sw,1"})
    v_rd_cs1_kN: float = Field(description="Taglio resistente di una cucitura su una fila circonferenziale", json_schema_extra={"unit": "kN", "symbol": "V_Rd,cs(1)"})
    n_f_richiesto: int = Field(description="Numero di cuciture per fila richiesto dall'area minima", json_schema_extra={"symbol": "n(f)"})
    n_effettivo: int = Field(description="Numero di cuciture per fila effettivamente poste", json_schema_extra={"symbol": "n"})
    v_rd_c_primo_kN: float = Field(description="Contributo del calcestruzzo alla resistenza complessiva", json_schema_extra={"unit": "kN", "symbol": "V'_Rd,c"})
    v_rd_s_kN: float = Field(description="Contributo delle cuciture alla resistenza complessiva", json_schema_extra={"unit": "kN", "symbol": "V_Rd,s"})
    v_rrd_kN: float = Field(description="Resistenza complessiva con armatura a taglio", json_schema_extra={"unit": "kN", "symbol": "V_Rrd"})
    ved_su_vrd: float = Field(description="Tasso di sfruttamento finale V_Ed·β / V_Rrd", json_schema_extra={"symbol": "V_Ed/V_Rd", "unit": "-", "highlight": True})


class PunzonamentoOutput(BaseModel):
    """Full result set for the ca-punzonamento tool."""

    model_config = ConfigDict(frozen=True)

    geometria: GeometriaOutput
    faccia_pilastro: FacciaPilastroOutput
    perimetro_critico: PerimetroCriticoOutput
    messaggio: str = Field(description="Esito sintetico (cella C40 del foglio)")
    armatura: ArmaturaOutput | None = Field(default=None, description="Progetto armature a taglio, presente solo se necessario")
    schizzo: Sketch | None = campo_schizzo()
