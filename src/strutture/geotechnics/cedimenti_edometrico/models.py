"""Input model for `geo-cedimento-edometrico` (docs/specs/geo-cedimenti-edometrico.md).

Flat scalar fields use unit-neutral names (`b`, `l`, `gamma`, `q`, ...); `sistema_unita` selects
between SI (m, kN/m³, kPa) and the sheet's own units (cm, kg/m³, kg/cm²) via the `unit_options`
hint, converted once at the boundary in `ingresso.py` (docs/architecture-batch2.md §9-D1). The
`strati` soil-layer table is always SI (`shared.soil_layers.SoilLayer` is a frozen shared row model
with fixed field units — reused as-is, not re-implemented).
"""
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.fields import FieldInfo

from strutture.shared.soil_layers import SoilLayer, strati_table_field
from strutture.shared.soil_layers import validate as validate_strati

SistemaUnita = Literal["SI", "tecnico"]
MetodoTensioni = Literal["newmark", "approssimato"]

_MAX_PUNTI_GRIGLIA = 20_000  # difesa contro un Δz troppo fine rispetto a z_max (§ perf. batch2)


def _with_hints(field: FieldInfo, **extra: Any) -> FieldInfo:
    """Merge extra `json_schema_extra` keys into a `FieldInfo` built by a shared table-field factory
    (the factory takes no `group`/`symbol`; this stays local to this package, no edit to `shared/`).
    Pydantic v2 rebuilds the schema from `FieldInfo._attributes_set`, not the live slot, when the
    model class merges an annotation with a bare `Field(...)` value — both must be updated."""
    merged = {**(field.json_schema_extra or {}), **extra}
    field.json_schema_extra = merged
    field._attributes_set["json_schema_extra"] = merged
    return field


class EdometricoInput(BaseModel):
    """`Edometrico` — cedimento edometrico di una fondazione rettangolare (B×L) su terreno
    stratificato, per il metodo edometrico (Terzaghi)."""

    model_config = ConfigDict(frozen=True, json_schema_extra={"unit_selector": "sistema_unita"})

    sistema_unita: SistemaUnita = Field(
        default="SI", description="Sistema di unità di misura degli ingressi dimensionali",
        json_schema_extra={"group": "Generale"},
    )

    b: float = Field(
        description="Larghezza della fondazione B", gt=0, le=5000,
        json_schema_extra={"symbol": "B", "group": "Geometria", "unit_options": {"SI": "m", "tecnico": "cm"}},
    )
    l: float = Field(
        description="Lunghezza della fondazione L", gt=0, le=5000,
        json_schema_extra={"symbol": "L", "group": "Geometria", "unit_options": {"SI": "m", "tecnico": "cm"}},
    )
    d: float = Field(
        default=0.0,
        description=(
            "Profondità di infissione/sbancamento D: riduce la pressione netta di q'=q−γ·D "
            "(cella non etichettata nel foglio originale, sempre in metri anche in modalità tecnico — "
            "dedotto dal fattore ×0.0001 della formula, vedi spec §7.3, da verificare)"
        ),
        ge=0, le=200,
        json_schema_extra={"symbol": "D", "group": "Carico", "unit": "m"},
    )
    gamma: float = Field(
        description="Peso di volume del terreno γ", gt=0, le=3000,
        json_schema_extra={"symbol": "γ", "group": "Carico", "unit_options": {"SI": "kN/m³", "tecnico": "kg/m³"}},
    )
    q: float = Field(
        description="Pressione di contatto applicata q", gt=0, le=2000,
        json_schema_extra={"symbol": "q", "group": "Carico", "unit_options": {"SI": "kPa", "tecnico": "kg/cm²"}},
    )
    falda: float | None = Field(
        default=None,
        description=(
            "Profondità della falda dal piano campagna: assente = terreno asciutto (peso di volume "
            "totale γ per l'intero profilo). Sotto falda si applica il peso di volume alleggerito "
            "γ−γw sia a σ'v0 sia al sovraccarico rimosso D·γ (docs/architecture-batch2.md §7, "
            "review HIGH: nel foglio originale la falda era sempre assunta al piano di posa, "
            "ignorando D — comportamento riprodotto solo in modalità legacy)"
        ),
        ge=0, le=100_000,
        json_schema_extra={"symbol": "Zw", "group": "Carico", "advanced": True, "unit_options": {"SI": "m", "tecnico": "cm"}},
    )

    strati: tuple[SoilLayer, ...] = _with_hints(
        strati_table_field(description="Stratigrafia del terreno (profondità e modulo edometrico Eed)"),
        group="Stratigrafia",
    )

    metodo_tensioni: MetodoTensioni = Field(
        default="newmark",
        description="Metodo di calcolo dell'incremento di tensione Δσv,q indotto dal carico in profondità",
        json_schema_extra={"group": "Metodo"},
    )
    z_crit_input: float | None = Field(
        default=None,
        description=(
            "Profondità critica Z,crit manuale: in modalità standard sovrascrive il calcolo automatico "
            "(criterio Δσv,q=0.1·Δσ'v); in modalità legacy riproduce la cella libera del foglio "
            "(assente = taglio disattivato, come il valore di default 10000 cm del foglio originale)"
        ),
        gt=0, le=100_000,
        json_schema_extra={"symbol": "Z_crit", "group": "Metodo", "advanced": True, "unit_options": {"SI": "m", "tecnico": "cm"}},
    )
    dz: float = Field(
        default=0.1, description="Passo di discretizzazione della profondità Δz", gt=0, le=1000,
        json_schema_extra={"symbol": "Δz", "group": "Metodo", "advanced": True, "unit_options": {"SI": "m", "tecnico": "cm"}},
    )
    z_max: float = Field(
        default=50.0, description="Profondità massima di integrazione", gt=0, le=100_000,
        json_schema_extra={"symbol": "z_max", "group": "Metodo", "advanced": True, "unit_options": {"SI": "m", "tecnico": "cm"}},
    )

    legacy_compat: bool = Field(
        default=False, description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"group": "Avanzate", "advanced": True},
    )

    @model_validator(mode="after")
    def _stratigrafia_valida(self) -> "EdometricoInput":
        validate_strati(self.strati)
        return self

    @model_validator(mode="after")
    def _griglia_non_eccessiva(self) -> "EdometricoInput":
        punti = self.z_max / self.dz
        if punti > _MAX_PUNTI_GRIGLIA:
            raise ValueError(f"il rapporto z_max/Δz ({punti:.0f} punti) supera il limite di {_MAX_PUNTI_GRIGLIA}")
        return self
