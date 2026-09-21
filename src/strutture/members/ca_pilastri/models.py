"""Pydantic I/O models for `ca-pilastri`: pilastro-rettangolare and pilastro-circolare (RC columns
in CD "B", NTC2018 + Circolare 7/2019). Inputs stay FLAT, ordered as in the sheet. Outputs are
nested per calculation group.

MRd is a user-supplied input in both tools: the sheet does not compute an M-N interaction domain,
it only checks a caller-supplied MRd against demand (see docs/specs/ca-pilastri.md §1 and
docs/architecture.md §7 decision D1 — a future `ca/dominio-mn` tool would produce this MRd).
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.report import Check

AcciaioGrado = Literal["B450C", "FeB22k", "FeB32k", "FeB38k", "FeB44k"]  # Tabelle!$DA$7:$DA$11
ClsClasse = Literal["C20/25", "C25/30", "C28/35", "C32/40", "C35/45", "C40/50", "C45/55", "C50/60"]  # Tabelle!$CX$7:$CX$14
Norma = Literal["NTC2018", "EC2", "NTC2008"]  # architecture-batch2.md §3 / §9-D3

_MRD_DESCRIPTION = (
    "Momento resistente della sezione, fornito come dato esterno (ad esempio da un dominio di "
    "interazione M-N calcolato a parte)"
)
_L0_DESCRIPTION = (
    "Lunghezza libera di inflessione per la verifica di snellezza; se omessa si assume pari "
    "all'altezza netta del pilastro"
)
_RM_DESCRIPTION = (
    "Rapporto tra i momenti flettenti alle estremità del pilastro (rm = M01/M02); lasciare vuoto "
    "se non noto, per elementi non controventati, o quando i momenti del primo ordine derivano "
    "prevalentemente da imperfezioni o da un carico trasversale (in questi casi si assume rm=1, "
    "singola curvatura, da cui C=0.7)"
)
_NORMA_DESCRIPTION = (
    "Normativa di riferimento: NTC2018 (+ Circolare 7/2019), EC2 (UNI EN 1992-1-1:2005 con "
    "Allegato Nazionale italiano, α_cc=0.85) o NTC2008 (disponibile solo come riproduzione del "
    "foglio Excel originale, legacy_compat=True)"
)
_PHI_EF_DESCRIPTION = (
    "Coefficiente di viscosità efficace φef (EC2 §5.8.4), usato per il coefficiente A della "
    "snellezza limite (EC2 §5.8.3.1(1), nota 1); se omesso si assume A=0.7"
)


class PilastroRettangolareInput(BaseModel):
    """`Pilastri rettangolari!H5:H24`."""

    model_config = ConfigDict(frozen=True)

    norma: Norma = Field(default="NTC2018", description=_NORMA_DESCRIPTION, json_schema_extra={"group": "Normativa"})
    l1_mm: float = Field(description="Lato 1 del pilastro (base)", gt=0, json_schema_extra={"unit": "mm", "symbol": "L_1", "group": "Geometria della sezione"})
    l2_mm: float = Field(description="Lato 2 del pilastro (altezza)", gt=0, json_schema_extra={"unit": "mm", "symbol": "L_2", "group": "Geometria della sezione"})
    h_mm: float = Field(description="Altezza netta del pilastro", gt=0, json_schema_extra={"unit": "mm", "symbol": "H", "group": "Geometria della sezione"})
    acciaio: AcciaioGrado = Field(description="Tipo di acciaio per l'armatura", json_schema_extra={"group": "Materiali"})
    cls: ClsClasse = Field(description="Tipo di calcestruzzo", json_schema_extra={"group": "Materiali"})
    ned_kN: float = Field(description="Azione assiale di calcolo (pilastro semplicemente compresso)", gt=0, json_schema_extra={"unit": "kN", "symbol": "N_Ed", "group": "Sollecitazioni di progetto"})
    ved_kN: float = Field(description="Taglio di calcolo agente", ge=0, json_schema_extra={"unit": "kN", "symbol": "V_Ed", "group": "Sollecitazioni di progetto"})
    med_kNm: float = Field(description="Momento flettente di calcolo agente", ge=0, json_schema_extra={"unit": "kNm", "symbol": "M_Ed", "group": "Sollecitazioni di progetto"})
    c_mm: float = Field(description="Copriferro, misurato all'asse delle barre", gt=0, json_schema_extra={"unit": "mm", "symbol": "c", "group": "Geometria della sezione"})
    n_ferri: int = Field(description="Numero totale di ferri longitudinali verticali", ge=4, json_schema_extra={"unit": "-", "group": "Geometria della sezione"})
    diametro_ferri_mm: float = Field(description="Diametro dei ferri longitudinali verticali", gt=0, json_schema_extra={"unit": "mm", "symbol": "⌀", "group": "Geometria della sezione"})
    diametro_staffe_mm: float = Field(description="Diametro delle staffe", gt=0, json_schema_extra={"unit": "mm", "symbol": "⌀_sw", "group": "Geometria della sezione"})
    passo_staffe_mm: float = Field(description="Passo delle staffe", gt=0, json_schema_extra={"unit": "mm", "symbol": "s", "group": "Geometria della sezione"})
    mrd_kNm: float = Field(description=_MRD_DESCRIPTION, gt=0, json_schema_extra={"unit": "kNm", "symbol": "M_Rd", "group": "Sollecitazioni di progetto"})
    n_ferri_l1: int = Field(
        description="Numero di ferri lungo il lato corto (solo per la disposizione grafica dei ferri, non influenza alcuna verifica)",
        ge=2, json_schema_extra={"unit": "-", "group": "Geometria della sezione", "advanced": True},
    )
    l0_mm: float | None = Field(default=None, description=_L0_DESCRIPTION, gt=0, json_schema_extra={"unit": "mm", "symbol": "l_0", "group": "Geometria della sezione", "advanced": True})
    rm: float | None = Field(default=None, description=_RM_DESCRIPTION, ge=-1, le=1, json_schema_extra={"unit": "-", "symbol": "r_m", "group": "Parametri di calcolo", "advanced": True})
    phi_ef: float | None = Field(
        default=None, description=_PHI_EF_DESCRIPTION, ge=0,
        json_schema_extra={"unit": "-", "symbol": "φ_ef", "group": "Parametri di calcolo", "advanced": True, "condition": {"field": "norma", "equals": ["EC2"]}},
    )
    legacy_compat: bool = Field(
        default=False, description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"advanced": True, "group": "Avanzate"},
    )


class PilastroCircolareInput(BaseModel):
    """`Pilastri circolari!H5:H24`."""

    model_config = ConfigDict(frozen=True)

    norma: Norma = Field(default="NTC2018", description=_NORMA_DESCRIPTION, json_schema_extra={"group": "Normativa"})
    d_mm: float = Field(description="Diametro del pilastro", gt=0, json_schema_extra={"unit": "mm", "symbol": "D", "group": "Geometria della sezione"})
    h_mm: float = Field(description="Altezza netta del pilastro", gt=0, json_schema_extra={"unit": "mm", "symbol": "H", "group": "Geometria della sezione"})
    acciaio: AcciaioGrado = Field(description="Tipo di acciaio per l'armatura", json_schema_extra={"group": "Materiali"})
    cls: ClsClasse = Field(description="Tipo di calcestruzzo", json_schema_extra={"group": "Materiali"})
    ned_kN: float = Field(description="Azione assiale di calcolo (pilastro semplicemente compresso)", gt=0, json_schema_extra={"unit": "kN", "symbol": "N_Ed", "group": "Sollecitazioni di progetto"})
    ved_kN: float = Field(description="Taglio di calcolo agente", ge=0, json_schema_extra={"unit": "kN", "symbol": "V_Ed", "group": "Sollecitazioni di progetto"})
    med_kNm: float = Field(description="Momento flettente di calcolo agente", ge=0, json_schema_extra={"unit": "kNm", "symbol": "M_Ed", "group": "Sollecitazioni di progetto"})
    c_mm: float = Field(description="Copriferro, misurato all'asse delle barre", gt=0, json_schema_extra={"unit": "mm", "symbol": "c", "group": "Geometria della sezione"})
    n_ferri: int = Field(description="Numero totale di ferri longitudinali verticali", ge=4, json_schema_extra={"unit": "-", "group": "Geometria della sezione"})
    diametro_ferri_mm: float = Field(description="Diametro dei ferri longitudinali verticali", gt=0, json_schema_extra={"unit": "mm", "symbol": "⌀", "group": "Geometria della sezione"})
    diametro_staffe_mm: float = Field(description="Diametro delle staffe", gt=0, json_schema_extra={"unit": "mm", "symbol": "⌀_sw", "group": "Geometria della sezione"})
    passo_staffe_mm: float = Field(description="Passo delle staffe", gt=0, json_schema_extra={"unit": "mm", "symbol": "s", "group": "Geometria della sezione"})
    mrd_kNm: float = Field(description=_MRD_DESCRIPTION, gt=0, json_schema_extra={"unit": "kNm", "symbol": "M_Rd", "group": "Sollecitazioni di progetto"})
    l0_mm: float | None = Field(default=None, description=_L0_DESCRIPTION, gt=0, json_schema_extra={"unit": "mm", "symbol": "l_0", "group": "Geometria della sezione", "advanced": True})
    rm: float | None = Field(default=None, description=_RM_DESCRIPTION, ge=-1, le=1, json_schema_extra={"unit": "-", "symbol": "r_m", "group": "Parametri di calcolo", "advanced": True})
    phi_ef: float | None = Field(
        default=None, description=_PHI_EF_DESCRIPTION, ge=0,
        json_schema_extra={"unit": "-", "symbol": "φ_ef", "group": "Parametri di calcolo", "advanced": True, "condition": {"field": "norma", "equals": ["EC2"]}},
    )
    legacy_compat: bool = Field(
        default=False, description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"advanced": True, "group": "Avanzate"},
    )


class MaterialiResult(BaseModel):
    """`Z7:Z9` — proprietà di calcolo dei materiali."""

    model_config = ConfigDict(frozen=True)

    fyd_MPa: float = Field(description="Tensione di calcolo di snervamento dell'acciaio", gt=0, json_schema_extra={"unit": "MPa", "symbol": "f_yd"})
    fcd_MPa: float = Field(description="Resistenza di calcolo a compressione del calcestruzzo", gt=0, json_schema_extra={"unit": "MPa", "symbol": "f_cd"})
    ftk_non_usato_MPa: float = Field(
        description="Tensione caratteristica di rottura dell'acciaio (valore informativo, non impiegato nei calcoli seguenti)",
        gt=0, json_schema_extra={"unit": "MPa", "symbol": "f_tk"},
    )


class GeometriaResult(BaseModel):
    """`H18:H23` (+ `CX17:CX18` per la sezione circolare)."""

    model_config = ConfigDict(frozen=True)

    ac_mm2: float = Field(description="Area della sezione di calcestruzzo", gt=0, json_schema_extra={"unit": "mm2", "symbol": "A_c"})
    as_mm2: float = Field(description="Area di armatura longitudinale", gt=0, json_schema_extra={"unit": "mm2", "symbol": "A_s"})
    rs: float = Field(description="Rapporto geometrico di armatura", gt=0, json_schema_extra={"unit": "-", "symbol": "ρ_s"})
    e_min_mm: float = Field(description="Eccentricità minima", gt=0, json_schema_extra={"unit": "mm", "symbol": "e_min"})
    med_ecc_kNm: float = Field(description="Momento dovuto all'eccentricità minima", ge=0, json_schema_extra={"unit": "kNm", "symbol": "M_Ed,ecc"})
    med_calc_kNm: float = Field(description="Momento di calcolo (massimo fra momento agente e momento da eccentricità minima)", ge=0, json_schema_extra={"unit": "kNm", "symbol": "M_Ed"})
    lato_equivalente_mm: float | None = Field(
        default=None,
        description="Lato del quadrato equivalente alla sezione circolare, usato al posto dei lati L1/L2 nelle formule di taglio e confinamento",
        json_schema_extra={"unit": "mm"},
    )


class ArmaturaMinimaResult(BaseModel):
    """`CX25:DA27` — inviluppo di armatura minima (NTC2018 §7.4.6.2.1 / EC8 5.4.3.2.2)."""

    model_config = ConfigDict(frozen=True)

    as_min_mm2: float = Field(description="Area minima di armatura longitudinale", ge=0, json_schema_extra={"unit": "mm2", "symbol": "A_s,min"})
    rs_min: float = Field(description="Rapporto geometrico minimo di armatura", ge=0, json_schema_extra={"unit": "-", "symbol": "ρ_s,min"})


class TaglioResult(BaseModel):
    """`CX29:Z17`, `Y20` — resistenza a taglio e domanda da gerarchia delle resistenze."""

    model_config = ConfigDict(frozen=True)

    sigma_cp_MPa: float = Field(description="Tensione media di compressione", json_schema_extra={"unit": "MPa", "symbol": "σ_cp"})
    ac: float = Field(description="Coefficiente maggiorativo per la resistenza dei puntoni compressi", gt=0, json_schema_extra={"unit": "-", "symbol": "a_c"})
    cot_theta: float = Field(description="Cotangente dell'inclinazione dei puntoni di calcestruzzo", ge=1, le=2.5, json_schema_extra={"unit": "-", "symbol": "cotg θ"})
    vrdc_kN: float = Field(description="Taglio resistente lato calcestruzzo", gt=0, json_schema_extra={"unit": "kN", "symbol": "V_Rd,c"})
    vrds_kN: float = Field(description="Taglio resistente lato armatura trasversale", gt=0, json_schema_extra={"unit": "kN", "symbol": "V_Rd,s"})
    vrd_kN: float = Field(description="Taglio resistente (minimo fra lato calcestruzzo e lato armatura)", gt=0, json_schema_extra={"unit": "kN", "symbol": "V_Rd", "highlight": True})
    domanda_capacity_design_kN: float = Field(description="Taglio di calcolo da gerarchia delle resistenze, derivato dal momento resistente", gt=0, json_schema_extra={"unit": "kN", "symbol": "V_Ed,DC"})


class FlessioneResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    mrd_kNm: float = Field(description="Momento resistente (dato di ingresso)", gt=0, json_schema_extra={"unit": "kNm", "symbol": "M_Rd"})
    med_kNm: float = Field(description="Momento di calcolo", ge=0, json_schema_extra={"unit": "kNm", "symbol": "M_Ed"})
    tasso_sfruttamento_pct: float = Field(description="Tasso di sfruttamento a flessione MEd/MRd", ge=0, json_schema_extra={"unit": "%", "symbol": "M_Ed/M_Rd", "highlight": True})


class CompressioneResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    nrcd_kN: float = Field(description="Resistenza a compressione della sola sezione di calcestruzzo", gt=0, json_schema_extra={"unit": "kN", "symbol": "N_Rcd"})
    tasso_sfruttamento_pct: float = Field(description="Tasso di sfruttamento a compressione Ned/NRcd", ge=0, json_schema_extra={"unit": "%", "symbol": "N_Ed/N_Rcd", "highlight": True})


class ConfinamentoResult(BaseModel):
    """`Z24:Z25` — zona critica (confinata), NTC2018 §7.4.6.2.2."""

    model_config = ConfigDict(frozen=True)

    hcr_mm: float = Field(description="Altezza della zona critica confinata", gt=0, json_schema_extra={"unit": "mm", "symbol": "h_cr"})
    passo_max_confinato_mm: float = Field(description="Passo massimo delle staffe nella zona critica", gt=0, json_schema_extra={"unit": "mm"})


class SnellezzaResult(BaseModel):
    """`J53:J57` (rett.) / `J60:J64` (circ.) — verifica di snellezza."""

    model_config = ConfigDict(frozen=True)

    lambda_lim: float = Field(description="Snellezza limite", gt=0, json_schema_extra={"unit": "-", "symbol": "λ_lim"})
    i_mm: float = Field(description="Raggio d'inerzia della sezione", gt=0, json_schema_extra={"unit": "mm", "symbol": "i"})
    l0_mm: float = Field(description="Lunghezza libera di inflessione impiegata", gt=0, json_schema_extra={"unit": "mm", "symbol": "l_0"})
    lambda_: float = Field(description="Snellezza del pilastro", gt=0, json_schema_extra={"unit": "-", "symbol": "λ"})


class DettagliResult(BaseModel):
    """Righe di dettaglio costruttivo (NTC2018 §7.4.6.2.2 / EC8 5.4.3.2.2)."""

    model_config = ConfigDict(frozen=True)

    diametro_long_min_mm: float = Field(description="Diametro minimo delle barre longitudinali", gt=0, json_schema_extra={"unit": "mm"})
    interasse_long_max_mm: float = Field(description="Interasse massimo ammesso tra le barre longitudinali", gt=0, json_schema_extra={"unit": "mm"})
    interasse_long_calcolato_mm: float = Field(description="Interasse calcolato tra le barre longitudinali", gt=0, json_schema_extra={"unit": "mm"})
    as_long_min_mm2: float = Field(description="Area minima di armatura longitudinale", ge=0, json_schema_extra={"unit": "mm2", "symbol": "A_s,min"})
    diametro_staffe_min_mm: float = Field(description="Diametro minimo delle staffe", gt=0, json_schema_extra={"unit": "mm"})
    interasse_staffe_max_mm: float = Field(description="Interasse massimo ammesso tra le staffe, fuori dalla zona critica", gt=0, json_schema_extra={"unit": "mm"})


class RegoleResult(BaseModel):
    """Eco del set di regole normative applicato (architecture-batch2.md §3), utile a distinguere
    a colpo d'occhio quali coefficienti sono stati usati per `norma`/`legacy_compat`."""

    model_config = ConfigDict(frozen=True)

    norma: Norma = Field(description="Normativa applicata")
    legacy_compat: bool = Field(description="Modalità riproduzione foglio Excel")
    a_snellezza: float = Field(description="Coefficiente A per la snellezza limite (EC2 §5.8.3.1(1); NTC2018 non lo usa esplicitamente)", json_schema_extra={"unit": "-", "symbol": "A"})
    c_snellezza: float = Field(description="Coefficiente C (o 1.7-rm) per la snellezza limite", json_schema_extra={"unit": "-", "symbol": "C"})
    omega_meccanico: float | None = Field(default=None, description="Rapporto meccanico di armatura ω = fyd·As/(fcd·Ac), solo EC2", json_schema_extra={"unit": "-", "symbol": "ω"})
    nu1: float = Field(description="Coefficiente riduttivo ν1 per la resistenza a taglio lato calcestruzzo (EC2 §6.2.2(6); NTC2018 usa 0.5 fisso)", json_schema_extra={"unit": "-", "symbol": "ν_1"})


class PilastroOutput(BaseModel):
    """Shape shared by both tools: `pilastro-rettangolare` and `pilastro-circolare`."""

    model_config = ConfigDict(frozen=True)

    materiali: MaterialiResult
    geometria: GeometriaResult
    armatura_minima: ArmaturaMinimaResult
    taglio: TaglioResult
    flessione: FlessioneResult
    compressione: CompressioneResult
    confinamento: ConfinamentoResult
    snellezza: SnellezzaResult
    dettagli: DettagliResult
    regole: RegoleResult


__all__ = [
    "AcciaioGrado",
    "ArmaturaMinimaResult",
    "Check",
    "ClsClasse",
    "CompressioneResult",
    "ConfinamentoResult",
    "DettagliResult",
    "FlessioneResult",
    "GeometriaResult",
    "MaterialiResult",
    "Norma",
    "PilastroCircolareInput",
    "PilastroOutput",
    "PilastroRettangolareInput",
    "RegoleResult",
    "SnellezzaResult",
    "TaglioResult",
]
