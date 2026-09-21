"""Pydantic I/O models for the vento-pressione tool (NTC2018 §3.3 / Circ. NTC2019 C3.3.2)."""
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

CategoriaEsposizione = Literal["I", "II", "III", "IV", "V"]
ZonaVento = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9]


class VentoPressioneInput(BaseModel):
    """Input per il calcolo della pressione del vento, NTC2018 §3.3. La zona vento può essere data
    direttamente (`zona`) oppure risolta da un `comune` (mutuamente esclusivi).
    """

    model_config = ConfigDict(frozen=True)

    comune: str | None = Field(
        default=None,
        description="Comune di ubicazione dell'opera, per la determinazione della zona vento",
        json_schema_extra={"widget": "comune", "group": "Sito"},
    )
    provincia: str | None = Field(
        default=None, description="Provincia, se serve a distinguere comuni omonimi",
        json_schema_extra={"group": "Sito"},
    )
    zona: ZonaVento | None = Field(
        default=None, description="Zona vento, se nota, in alternativa al comune",
        json_schema_extra={"group": "Sito"},
    )
    altitudine_m: float = Field(
        description="Altitudine sul livello del mare del sito", ge=0,
        json_schema_extra={"unit": "m", "symbol": "a_s", "group": "Sito"},
    )
    categoria_esposizione: CategoriaEsposizione = Field(
        description="Categoria di esposizione del sito", json_schema_extra={"group": "Sito"}
    )
    ct: float = Field(
        default=1.0, gt=0, description="Coefficiente di topografia",
        json_schema_extra={"unit": "-", "symbol": "c_t", "group": "Sito", "advanced": True},
    )
    altezza_edificio_m: float = Field(
        description="Altezza massima dell'edificio", gt=0,
        json_schema_extra={"unit": "m", "symbol": "H", "group": "Geometria"},
    )
    periodo_ritorno_anni: float = Field(
        description="Periodo di ritorno dell'azione del vento", gt=1,
        json_schema_extra={"unit": "anni", "symbol": "T_R", "group": "Azione di progetto"},
    )
    n_sezioni: int = Field(
        default=10, ge=1, description="Numero di sezioni del profilo di pressione lungo l'altezza",
        json_schema_extra={"unit": "-", "group": "Campionamento", "advanced": True},
    )
    legacy_compat: bool = Field(
        default=False,
        description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"group": "Avanzate", "advanced": True},
    )

    @model_validator(mode="after")
    def _comune_xor_zona(self) -> Self:
        comune_dato = bool(self.comune and self.comune.strip())
        zona_data = self.zona is not None
        if comune_dato == zona_data:
            raise ValueError("specificare esattamente uno tra `comune` e `zona`")
        return self


class ProfiloRiga(BaseModel):
    """Una quota del profilo di pressione: z, ce(z) e p(z) (Tabelle!L/O/P, generalizzato)."""

    model_config = ConfigDict(frozen=True)

    z_m: float = Field(description="Quota sul terreno", json_schema_extra={"unit": "m", "symbol": "z"})
    ce: float = Field(description="Coefficiente di esposizione alla quota z", json_schema_extra={"unit": "-", "symbol": "c_e(z)"})
    p_kNm2: float = Field(
        description="Pressione del vento alla quota z (coefficiente di forma unitario)",
        json_schema_extra={"unit": "kN/m²", "symbol": "p(z)"},
    )


class VentoPressioneOutput(BaseModel):
    """Risultati del calcolo della pressione del vento (Vento!H5:H45, Tabelle!K4:Q1004 generalizzato)."""

    model_config = ConfigDict(frozen=True)

    regione: str | None = Field(default=None, description="Regione del comune")
    provincia: str | None = Field(default=None, description="Provincia del comune")
    zona: int = Field(description="Zona vento", json_schema_extra={"unit": "-"})
    vb0: float = Field(description="Velocità base di riferimento", json_schema_extra={"unit": "m/s", "symbol": "v_b,0"})
    a0: float = Field(description="Altitudine di riferimento della zona", json_schema_extra={"unit": "m", "symbol": "a_0"})
    ka: float = Field(
        description="Coefficiente di altitudine secondo la NTC2008, superato",
        json_schema_extra={"unit": "1/s", "symbol": "k_a", "legacy_only": True},
    )
    ks: float = Field(
        description="Coefficiente di zona per il calcolo del coefficiente di altitudine",
        json_schema_extra={"unit": "-", "symbol": "k_s"},
    )
    ca: float = Field(
        description="Coefficiente di altitudine applicato",
        json_schema_extra={"unit": "-", "symbol": "c_a"},
    )
    vref: float = Field(
        description="Velocità di riferimento al suolo per un periodo di ritorno di 50 anni",
        json_schema_extra={"unit": "m/s", "symbol": "v_b"},
    )
    a_r: float = Field(
        description="Coefficiente di correzione per il periodo di ritorno applicato",
        json_schema_extra={"unit": "-", "symbol": "c_r"},
    )
    vr: float = Field(
        description="Velocità di riferimento per il periodo di ritorno di progetto",
        json_schema_extra={"unit": "m/s", "symbol": "v_r", "highlight": True},
    )
    kr: float = Field(description="Fattore di terreno legato all'esposizione", json_schema_extra={"unit": "-", "symbol": "k_r"})
    z0: float = Field(description="Lunghezza di rugosità del terreno", json_schema_extra={"unit": "m", "symbol": "z_0"})
    zmin: float = Field(description="Quota minima del profilo di pressione", json_schema_extra={"unit": "m", "symbol": "z_min"})
    qb: float = Field(description="Pressione cinetica di riferimento", json_schema_extra={"unit": "kN/m²", "symbol": "q_b"})
    ce_h: float = Field(
        description="Coefficiente di esposizione alla quota dell'edificio",
        json_schema_extra={"unit": "-", "symbol": "c_e(H)", "highlight": True},
    )
    p_h_kNm2: float = Field(
        description="Pressione del vento alla quota dell'edificio (coefficiente di forma unitario)",
        json_schema_extra={"unit": "kN/m²", "symbol": "p(H)", "highlight": True},
    )
    profilo: tuple[ProfiloRiga, ...] = Field(
        description="Profilo di pressione lungo l'altezza dell'edificio",
        json_schema_extra={
            "chart": {"x": "z_m", "y": ["p_kNm2"], "x_label": "z [m]", "y_label": "p [kN/m²]"}
        },
    )
