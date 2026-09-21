"""Pydantic I/O models for the ca-taglio-non-armato tool (NTC2018 §4.1.2.3.5.1).

Covers both workbook sheets with the same flat input model (docs/architecture-batch2.md §4):
`Foglio1` (v1, bw=generic width, Asl given directly) and `1m` (v2, per-metre strip, fck given
directly instead of derived from Rck, Asl given as N°/Ø instead of a scalar area).
"""
from pydantic import BaseModel, ConfigDict, Field, model_validator

from strutture.shared.sketch import Sketch, campo_schizzo


class TaglioNonArmatoInput(BaseModel):
    """Flat inputs, ordered as in sheet `Foglio1` (v1) / `1m` (v2) of Taglio non armato NTC2018.xlsx."""

    model_config = ConfigDict(frozen=True)

    rck_MPa: float = Field(description="Resistenza cubica caratteristica del calcestruzzo", gt=0, json_schema_extra={"unit": "MPa", "symbol": "R_ck", "group": "Materiali"})
    fck_MPa: float | None = Field(
        default=None, gt=0,
        description="Resistenza cilindrica caratteristica, se nota direttamente (vuoto = 0.83*Rck, foglio v1); se indicata, deve essere coerente con Rck (foglio v2)",
        json_schema_extra={"unit": "MPa", "symbol": "f_ck", "group": "Materiali"},
    )
    gamma_c: float = Field(
        default=1.5, gt=0, description="Coefficiente parziale di sicurezza del calcestruzzo",
        json_schema_extra={"symbol": "γ_c", "group": "Avanzate", "advanced": True},
    )
    h_mm: float = Field(description="Altezza della sezione", gt=0, json_schema_extra={"unit": "mm", "symbol": "h", "group": "Geometria della sezione"})
    c_mm: float = Field(description="Copriferro, misurato all'asse delle barre", ge=0, json_schema_extra={"unit": "mm", "symbol": "c", "group": "Geometria della sezione"})
    bw_mm: float = Field(description="Larghezza minima della sezione (tipicamente 1000 mm per verifiche a striscia di 1 m)", gt=0, json_schema_extra={"unit": "mm", "symbol": "b_w", "group": "Geometria della sezione"})
    asl_mm2: float | None = Field(
        default=None, ge=0,
        description="Area di armatura longitudinale tesa, se nota direttamente (in alternativa a N° e diametro delle barre, foglio v1)",
        json_schema_extra={"unit": "mm2", "symbol": "A_sl", "group": "Geometria della sezione"},
    )
    n_barre: int | None = Field(
        default=None, gt=0, description="Numero di barre longitudinali tese (in alternativa ad Asl, foglio v2)",
        json_schema_extra={"symbol": "N°", "group": "Geometria della sezione"},
    )
    diametro_barre_mm: float | None = Field(
        default=None, gt=0, description="Diametro delle barre longitudinali tese (in alternativa ad Asl, foglio v2)",
        json_schema_extra={"unit": "mm", "symbol": "⌀", "group": "Geometria della sezione"},
    )
    ned_kN: float = Field(description="Azione assiale nella sezione, positiva se di compressione", json_schema_extra={"unit": "kN", "symbol": "N_Ed", "group": "Sollecitazioni di progetto"})
    legacy_compat: bool = Field(
        default=False, description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"advanced": True, "group": "Avanzate"},
    )

    @model_validator(mode="after")
    def _valida_armatura_longitudinale(self) -> "TaglioNonArmatoInput":
        ha_area_diretta = self.asl_mm2 is not None
        ha_barre = self.n_barre is not None and self.diametro_barre_mm is not None
        if ha_area_diretta and (self.n_barre is not None or self.diametro_barre_mm is not None):
            raise ValueError("indicare Asl direttamente oppure N° e diametro delle barre, non entrambi")
        if not ha_area_diretta and not ha_barre:
            raise ValueError("indicare Asl direttamente oppure N° e diametro delle barre")
        return self


class MaterialiOutput(BaseModel):
    """Resistenze di calcolo del calcestruzzo."""

    model_config = ConfigDict(frozen=True)

    fck_MPa: float = Field(description="Resistenza cilindrica caratteristica", json_schema_extra={"unit": "MPa", "symbol": "f_ck"})
    fcd_MPa: float = Field(description="Resistenza di calcolo a compressione", json_schema_extra={"unit": "MPa", "symbol": "f_cd"})


class GeometriaOutput(BaseModel):
    """Geometria utile della sezione."""

    model_config = ConfigDict(frozen=True)

    d_mm: float = Field(description="Altezza utile della sezione", json_schema_extra={"unit": "mm", "symbol": "d"})
    asl_mm2: float = Field(description="Area di armatura longitudinale tesa, effettiva", json_schema_extra={"unit": "mm2", "symbol": "A_sl"})


class TaglioOutput(BaseModel):
    """Termini della formula di resistenza a taglio senza armatura trasversale."""

    model_config = ConfigDict(frozen=True)

    sigma_cp_MPa: float = Field(description="Tensione media di compressione nella sezione", json_schema_extra={"unit": "MPa", "symbol": "σ_cp"})
    k: float = Field(description="Fattore di scala per l'effetto dimensionale", json_schema_extra={"unit": "-", "symbol": "k"})
    vmin_MPa: float = Field(description="Resistenza a taglio minima", json_schema_extra={"unit": "MPa", "symbol": "v_min"})
    rho_l: float = Field(description="Rapporto geometrico di armatura longitudinale tesa", json_schema_extra={"unit": "-", "symbol": "ρ_l"})
    vrd1_kN: float = Field(description="Resistenza a taglio, termine con armatura longitudinale", json_schema_extra={"unit": "kN", "symbol": "V_Rd,1"})
    vrd2_kN: float = Field(description="Resistenza a taglio, termine minimo", json_schema_extra={"unit": "kN", "symbol": "V_Rd,2"})
    vrd_kN: float = Field(description="Resistenza a taglio di calcolo", json_schema_extra={"unit": "kN", "symbol": "V_Rd", "highlight": True})


class TaglioNonArmatoOutput(BaseModel):
    """Full result set for the taglio-non-armato tool."""

    model_config = ConfigDict(frozen=True)

    materiali: MaterialiOutput
    geometria: GeometriaOutput
    taglio: TaglioOutput
    schizzo: Sketch | None = campo_schizzo()
