"""Pydantic I/O models for `neve-carico-falda` and `neve-accumulo` (NTC2018 §3.4 / Circ. §C3.4.5.6)."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from strutture.shared.sketch import Sketch, campo_schizzo

Topografia = Literal["Battuta dai venti", "Normale", "Riparata"]
SiNo = Literal["SI", "NO"]
Zona = Literal["I (alpina)", "I (mediterranea)", "II", "III"]
TipoCopertura = Literal["Copertura ad una falda", "Copertura a due falde"]


class _LocationInput(BaseModel):
    """Comune or zona directly — exactly one must be given (see `strutture.loads.neve.location`)."""

    model_config = ConfigDict(frozen=True)

    comune: str | None = Field(
        default=None,
        description="Comune di ubicazione dell'opera",
        json_schema_extra={"widget": "comune", "group": "Sito"},
    )
    zona: Zona | None = Field(
        default=None,
        description="Zona neve, se nota, in alternativa al comune",
        json_schema_extra={"group": "Sito"},
    )

    @model_validator(mode="after")
    def _exactly_one_location(self) -> "_LocationInput":
        if (self.comune is None) == (self.zona is None):
            raise ValueError("specificare esattamente uno tra comune e zona")
        return self


_CAMPI_UNA_FALDA: tuple[str, ...] = ("a", "parapetto")
_CAMPI_DUE_FALDE: tuple[str, ...] = ("a1", "parapetto1", "a2", "parapetto2")


class CaricoFaldaInput(_LocationInput):
    """`Neve` sheet inputs. `a`/`parapetto` are required only for `tipo_copertura="Copertura ad
    una falda"`; `a1`/`parapetto1`/`a2`/`parapetto2` only for `"Copertura a due falde"` (see
    `_richiede_campi_del_tipo_copertura`). Supplying the other roof type's fields too is
    harmless — in `legacy_compat=True` mode the sheet always computes both blocks when the data
    is present (oracle fixtures supply all six fields)."""

    as_m: float = Field(
        description="Altitudine sul livello del mare del sito",
        ge=0,
        json_schema_extra={"unit": "m", "symbol": "a_s", "group": "Sito"},
    )
    topografia: Topografia = Field(description="Esposizione topografica del sito", json_schema_extra={"group": "Sito"})
    ct: float = Field(
        default=1.0,
        gt=0,
        description="Coefficiente termico, riduce il carico per coperture ad alta dispersione termica",
        json_schema_extra={"unit": "-", "symbol": "C_t", "group": "Sito", "advanced": True},
    )
    tipo_copertura: TipoCopertura = Field(
        description="Tipo di copertura, decide quali campi geometrici servono",
        json_schema_extra={"group": "Geometria della copertura"},
    )
    a: float | None = Field(
        default=None,
        description="Angolo della falda",
        ge=0,
        le=90,
        json_schema_extra={
            "unit": "°",
            "symbol": "α",
            "group": "Geometria della copertura",
            "condition": {"field": "tipo_copertura", "equals": ["Copertura ad una falda"]},
        },
    )
    parapetto: SiNo | None = Field(
        default=None,
        description="Presenza di barriera al bordo inferiore della falda",
        json_schema_extra={
            "group": "Geometria della copertura",
            "condition": {"field": "tipo_copertura", "equals": ["Copertura ad una falda"]},
        },
    )
    a1: float | None = Field(
        default=None,
        description="Angolo della falda 1",
        ge=0,
        le=90,
        json_schema_extra={
            "unit": "°",
            "symbol": "α_1",
            "group": "Geometria della copertura",
            "condition": {"field": "tipo_copertura", "equals": ["Copertura a due falde"]},
        },
    )
    parapetto1: SiNo | None = Field(
        default=None,
        description="Presenza di barriera al bordo della falda 1",
        json_schema_extra={
            "group": "Geometria della copertura",
            "condition": {"field": "tipo_copertura", "equals": ["Copertura a due falde"]},
        },
    )
    a2: float | None = Field(
        default=None,
        description="Angolo della falda 2",
        ge=0,
        le=90,
        json_schema_extra={
            "unit": "°",
            "symbol": "α_2",
            "group": "Geometria della copertura",
            "condition": {"field": "tipo_copertura", "equals": ["Copertura a due falde"]},
        },
    )
    parapetto2: SiNo | None = Field(
        default=None,
        description="Presenza di barriera al bordo della falda 2",
        json_schema_extra={
            "group": "Geometria della copertura",
            "condition": {"field": "tipo_copertura", "equals": ["Copertura a due falde"]},
        },
    )
    legacy_compat: bool = Field(
        default=False,
        description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"group": "Avanzate", "advanced": True},
    )

    @model_validator(mode="after")
    def _richiede_campi_del_tipo_copertura(self) -> "CaricoFaldaInput":
        """Only the fields relevant to the selected `tipo_copertura` are required; the other
        roof type's fields, if supplied, are simply ignored by `run_carico_falda` unless the
        caller also supplied the required subset (see `tool.run_carico_falda`)."""
        campi_richiesti = _CAMPI_UNA_FALDA if self.tipo_copertura == "Copertura ad una falda" else _CAMPI_DUE_FALDE
        mancanti = [nome for nome in campi_richiesti if getattr(self, nome) is None]
        if mancanti:
            etichetta = "campo obbligatorio mancante" if len(mancanti) == 1 else "campi obbligatori mancanti"
            raise ValueError(f"{etichetta} per tipo_copertura={self.tipo_copertura!r}: {', '.join(mancanti)}")
        return self


class CaricoFaldaOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    provincia: str | None = Field(default=None, description="Provincia del comune")
    regione: str | None = Field(default=None, description="Regione del comune")
    zona: Zona = Field(description="Zona neve")
    qsk: float = Field(description="Carico neve al suolo", json_schema_extra={"unit": "kN/m²", "symbol": "q_sk"})
    ce: float = Field(description="Coefficiente di esposizione", json_schema_extra={"unit": "-", "symbol": "C_E"})
    mu: float | None = Field(
        default=None, description="Coefficiente di forma della copertura a una falda",
        json_schema_extra={"unit": "-", "symbol": "μ_1"},
    )
    qs: float | None = Field(
        default=None, description="Carico neve di progetto sulla copertura a una falda",
        json_schema_extra={"unit": "kN/m²", "symbol": "q_s", "highlight": True},
    )
    mu1: float | None = Field(
        default=None, description="Coefficiente di forma della falda 1",
        json_schema_extra={"unit": "-", "symbol": "μ_1"},
    )
    qs1: float | None = Field(
        default=None, description="Carico neve di progetto sulla falda 1",
        json_schema_extra={"unit": "kN/m²", "symbol": "q_s1", "highlight": True},
    )
    mu2: float | None = Field(
        default=None, description="Coefficiente di forma della falda 2",
        json_schema_extra={"unit": "-", "symbol": "μ_2"},
    )
    qs2: float | None = Field(
        default=None, description="Carico neve di progetto sulla falda 2",
        json_schema_extra={"unit": "kN/m²", "symbol": "q_s2", "highlight": True},
    )
    schizzo: Sketch | None = campo_schizzo()


class AccumuloInput(_LocationInput):
    """`Neve accumulo` sheet inputs."""

    as_m: float = Field(
        description="Altitudine sul livello del mare del sito",
        ge=0,
        json_schema_extra={"unit": "m", "symbol": "a_s", "group": "Sito"},
    )
    topografia: Topografia = Field(description="Esposizione topografica del sito", json_schema_extra={"group": "Sito"})
    ct: float = Field(
        default=1.0,
        gt=0,
        description="Coefficiente termico, riduce il carico per coperture ad alta dispersione termica",
        json_schema_extra={"unit": "-", "symbol": "C_t", "group": "Sito", "advanced": True},
    )
    b1: float = Field(
        gt=0, description="Larghezza della costruzione più alta",
        json_schema_extra={"unit": "m", "symbol": "b_1", "group": "Geometria"},
    )
    b2: float = Field(
        gt=0, description="Larghezza della costruzione più bassa",
        json_schema_extra={"unit": "m", "symbol": "b_2", "group": "Geometria"},
    )
    h: float = Field(
        gt=0, description="Dislivello tra le due coperture",
        json_schema_extra={"unit": "m", "symbol": "h", "group": "Geometria"},
    )
    a: float = Field(
        description="Angolo della falda della costruzione più alta",
        ge=0, le=90,
        json_schema_extra={"unit": "°", "symbol": "α", "group": "Geometria"},
    )
    gamma: float = Field(
        default=2.0, gt=0, description="Peso specifico della neve",
        json_schema_extra={"unit": "kN/m³", "symbol": "γ", "group": "Proprietà della neve"},
    )
    m1_input: float = Field(
        ge=0, description="Coefficiente di forma imposto per il bordo lontano dalla costruzione più alta",
        json_schema_extra={"unit": "-", "symbol": "μ_1,imp", "group": "Coefficienti di forma"},
    )
    msup: float = Field(
        ge=0, description="Coefficiente di forma della falda superiore",
        json_schema_extra={"unit": "-", "symbol": "μ_sup", "group": "Coefficienti di forma"},
    )
    neve_sheet_as_m: float | None = Field(
        default=None,
        description="Altitudine usata dal foglio «Neve» del calcolo originale, solo per riprodurne "
        "un errore di collegamento tra fogli in modalità Excel",
        ge=0,
        json_schema_extra={"unit": "m", "group": "Avanzate", "advanced": True},
    )
    legacy_compat: bool = Field(
        default=False,
        description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"group": "Avanzate", "advanced": True},
    )


class AccumuloOutput(BaseModel):
    model_config = ConfigDict(frozen=True)

    zona: Zona = Field(description="Macrozona neve")
    qsk: float = Field(description="Carico neve al suolo", json_schema_extra={"unit": "kN/m²"})
    ce: float = Field(description="Coefficiente di esposizione")
    ls: float = Field(description="Lunghezza della zona di accumulo", json_schema_extra={"unit": "m"})
    mw: float = Field(description="Coefficiente di forma da ridistribuzione del vento")
    ms: float = Field(description="Coefficiente di forma da scivolamento")
    m2: float = Field(description="Coefficiente di forma totale al muro")
    m1_final: float = Field(description="Coefficiente di forma di progetto, bordo lontano")
    m2_final: float = Field(description="Coefficiente di forma di progetto, al muro")
    ls_final: float = Field(description="Lunghezza di progetto della zona di accumulo", json_schema_extra={"unit": "m"})
    qs1_final: float = Field(
        description="Carico neve di progetto, bordo lontano (qsk·CE·Ct·m1_final)",
        json_schema_extra={"unit": "kN/m²", "highlight": True},
    )
    qs2_final: float = Field(
        description="Carico neve di progetto, al muro (qsk·CE·Ct·m2_final)",
        json_schema_extra={"unit": "kN/m²", "highlight": True},
    )
    schizzo: Sketch | None = campo_schizzo()
