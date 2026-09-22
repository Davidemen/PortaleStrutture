"""Pydantic I/O models for the `ca-mensola-tozza` tool (RC short corbel, strut-and-tie).

Inputs stay FLAT, ordered as in the sheet `Mensola tozza` (rows H5-H29). Outputs are nested per
calculation group: `materiali` (Z5-Z9), `geometria` (H11/H13), `armature` (H20/H21/H23),
`capacita` (H28/H30-H33). The 3-way verdict text (`C34`) and the stirrup note (`A36`) become
`Check`s in the `Report.checks` tuple (see `docs/BUILD_CONTRACT.md` "Member tools").
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from strutture.shared.sketch import Sketch, campo_schizzo

# Mensola tozza!BU5:BU12 — local dropdown source for H15 (8 entries, mirrors Tabelle!M34:M41).
ClasseCalcestruzzoMensola = Literal[
    "C20/25", "C25/30", "C28/35", "C32/40", "C35/45", "C40/50", "C45/55", "C50/60",
]
# Mensola tozza!BU16:BU20 — local dropdown source for H14. `B500C` exists in `Tabelle!M45:P49` but
# is not in this list (spec §5/§7); `FeB22k` *is* in this list despite being absent from that same
# `Tabelle` range (see divergence in `materiali.py` and `docs/divergences/ca-mensole.md`).
GradoAcciaioMensola = Literal["B450C", "FeB22k", "FeB32k", "FeB38k", "FeB44k"]
SiNo = Literal["SI", "NO"]


class MensolaTozzaInput(BaseModel):
    """`Mensola tozza!H5:H29` (spec §2)."""

    model_config = ConfigDict(frozen=True)

    a_mm: float = Field(description="Distanza del carico dal filo del pilastro", gt=0, json_schema_extra={"unit": "mm", "symbol": "a", "group": "Geometria della sezione"})
    h_mm: float = Field(description="Altezza della mensola", gt=0, json_schema_extra={"unit": "mm", "symbol": "h", "group": "Geometria della sezione"})
    b_mm: float = Field(description="Larghezza della mensola", gt=0, json_schema_extra={"unit": "mm", "symbol": "b", "group": "Geometria della sezione"})
    c_mm: float = Field(description="Copriferro, misurato all'asse delle barre", gt=0, json_schema_extra={"unit": "mm", "symbol": "c", "group": "Geometria della sezione"})
    ped_kN: float = Field(description="Carico verticale di progetto", gt=0, json_schema_extra={"unit": "kN", "symbol": "P_Ed", "group": "Sollecitazioni di progetto"})
    hed_kN: float = Field(default=0.0, description="Carico orizzontale di progetto", ge=0, json_schema_extra={"unit": "kN", "symbol": "H_Ed", "group": "Sollecitazioni di progetto"})
    acciaio: GradoAcciaioMensola = Field(description="Tipo di acciaio per l'armatura", json_schema_extra={"group": "Materiali"})
    calcestruzzo: ClasseCalcestruzzoMensola = Field(description="Tipo di calcestruzzo", json_schema_extra={"group": "Materiali"})
    n_hor: int = Field(description="Numero di ferri orizzontali (tiranti)", ge=0, json_schema_extra={"group": "Geometria della sezione"})
    phi_hor_mm: float = Field(description="Diametro dei ferri orizzontali", gt=0, json_schema_extra={"unit": "mm", "symbol": "⌀_hor", "group": "Geometria della sezione"})
    n_incl: int = Field(default=0, description="Numero di ferri inclinati", ge=0, json_schema_extra={"group": "Geometria della sezione"})
    phi_incl_mm: float = Field(default=0.0, description="Diametro dei ferri inclinati", ge=0, json_schema_extra={"unit": "mm", "symbol": "⌀_incl", "group": "Geometria della sezione"})
    angolo_incl_deg: float = Field(default=0.0, description="Inclinazione dell'armatura inclinata", ge=0, le=90, json_schema_extra={"unit": "°", "symbol": "α", "group": "Geometria della sezione"})
    n_staffe: int = Field(default=0, description="Numero di staffe orizzontali", ge=0, json_schema_extra={"group": "Geometria della sezione"})
    phi_staffe_mm: float = Field(default=0.0, description="Diametro delle staffe orizzontali", ge=0, json_schema_extra={"unit": "mm", "symbol": "⌀_sw", "group": "Geometria della sezione"})
    staffe_verticali: SiNo = Field(default="NO", description="Sono presenti staffe verticali?", json_schema_extra={"group": "Geometria della sezione"})
    legacy_compat: bool = Field(
        default=False, description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"advanced": True, "group": "Avanzate"},
    )

    @model_validator(mode="after")
    def _altezza_utile_positiva(self) -> "MensolaTozzaInput":
        if self.c_mm >= self.h_mm:
            raise ValueError(f"copriferro c={self.c_mm} deve essere minore dell'altezza h={self.h_mm}")
        return self


# --- materiali (Z5-Z9) --------------------------------------------------------------------------


class MaterialiResult(BaseModel):
    """`Mensola tozza!Z5:Z9` (`Z7`=ftk is dead, spec §7, omitted here)."""

    model_config = ConfigDict(frozen=True)

    gamma_s: float = Field(description="Coefficiente parziale dell'acciaio", json_schema_extra={"unit": "-", "symbol": "γ_s"})
    gamma_c: float = Field(description="Coefficiente parziale del calcestruzzo", json_schema_extra={"unit": "-", "symbol": "γ_c"})
    fyd_MPa: float = Field(description="Resistenza di calcolo a snervamento dell'acciaio", json_schema_extra={"unit": "MPa", "symbol": "f_yd"})
    fcd_MPa: float = Field(description="Resistenza di calcolo a compressione del calcestruzzo", json_schema_extra={"unit": "MPa", "symbol": "f_cd"})


# --- geometria (H11, H13) -----------------------------------------------------------------------


class GeometriaResult(BaseModel):
    """`Mensola tozza!H11,H13` (`H12`=z is dead, spec §7, omitted here)."""

    model_config = ConfigDict(frozen=True)

    d_mm: float = Field(description="Altezza utile della sezione", json_schema_extra={"unit": "mm", "symbol": "d"})
    l_mm: float = Field(description="Braccio di taglio equivalente", json_schema_extra={"unit": "mm", "symbol": "l"})


# --- armature (H20, H21, H23) --------------------------------------------------------------------


class ArmatureResult(BaseModel):
    """`Mensola tozza!H20,H21,H23`."""

    model_config = ConfigDict(frozen=True)

    as_hor_mm2: float = Field(description="Area di armatura orizzontale (tiranti)", json_schema_extra={"unit": "mm²", "symbol": "A_s,hor"})
    as_incl_mm2: float = Field(description="Area di armatura inclinata", json_schema_extra={"unit": "mm²", "symbol": "A_s,incl"})
    as_lnk_min_mm2: float = Field(description="Area minima di staffe/tiranti orizzontali richiesta", json_schema_extra={"unit": "mm²", "symbol": "A_s,lnk,min"})


# --- capacita (H28, H30-H33) ---------------------------------------------------------------------


class CapacitaResult(BaseModel):
    """`Mensola tozza!H28,H30,H31,H32,H33` (`H30` reimplemented as a plain number, spec §7)."""

    model_config = ConfigDict(frozen=True)

    c_coeff: float = Field(description="Coefficiente di amplificazione per presenza di staffe verticali", json_schema_extra={"unit": "-", "symbol": "c"})
    prs_kN: float = Field(description="Capacità lato acciaio (tirante)", json_schema_extra={"unit": "kN", "symbol": "P_Rs"})
    prc_kN: float = Field(description="Capacità lato calcestruzzo (puntone)", json_schema_extra={"unit": "kN", "symbol": "P_Rc"})
    dpr_kN: float = Field(description="Contributo dell'armatura inclinata", json_schema_extra={"unit": "kN", "symbol": "ΔP_R"})
    pr_kN: float = Field(description="Capacità portante globale della mensola, min(P_Rs + 0,8·ΔP_R; P_Rc) (modalità Excel: senza il limite del puntone)", json_schema_extra={"unit": "kN", "symbol": "P_R", "highlight": True})


class MensolaTozzaOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    materiali: MaterialiResult
    geometria: GeometriaResult
    armature: ArmatureResult
    capacita: CapacitaResult
    schizzo: Sketch | None = campo_schizzo()
