"""Input model for `fond-plinto-isolato` (docs/specs/fond-plinti-isolati.md, both tools combined into
one composed workflow). Fields follow the sheet's top-to-bottom order; tables per
docs/architecture-batch2.md §2."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from strutture.shared.footing_pressure import Metodo
from strutture.shared.load_table import ReactionRow, reazioni_table_field, validate_unique_nodo_combo
from strutture.shared.materials.concrete import ConcreteClass
from strutture.shared.materials.rebar import RebarGrade

from .rows import ResistenzaRow, resistenze_table_field, validate_unique_famiglia

SistemaUnita = Literal["SI", "tecnico"]


class PlintoIsolatoInput(BaseModel):
    """`Plinti isolati.xlsx` — isolated footing checked against a table of support reactions."""

    model_config = ConfigDict(frozen=True)

    metodo_pressioni: Metodo = Field(
        default="esatto", description="Metodo di calcolo della pressione di contatto biassiale",
        json_schema_extra={"group": "Metodo", "condition": {"field": "legacy_compat", "equals": [False]}},
    )
    sistema_unita: SistemaUnita = Field(
        default="SI", description="Sistema di unità per la resistenza del terreno",
        json_schema_extra={"group": "Metodo", "unit_selector": "sistema_unita", "advanced": True},
    )

    ax_m: float = Field(description="Dimensione in pianta del plinto lungo X", gt=0, le=20,
                         json_schema_extra={"unit": "m", "symbol": "A_X", "group": "Geometria"})
    by_m: float = Field(description="Dimensione in pianta del plinto lungo Y", gt=0, le=20,
                         json_schema_extra={"unit": "m", "symbol": "B_Y", "group": "Geometria"})
    h_plinto_m: float = Field(description="Altezza del plinto", gt=0, le=5,
                               json_schema_extra={"unit": "m", "symbol": "H", "group": "Geometria"})
    h_interro_m: float = Field(description="Profondità di ricoprimento del terreno sopra il plinto", ge=0, le=10,
                                json_schema_extra={"unit": "m", "symbol": "h", "group": "Geometria"})
    a_pedestal_m: float = Field(default=0.0, description="Dimensione in pianta del bicchiere/pilastrino lungo X", ge=0, le=10,
                                 json_schema_extra={"unit": "m", "symbol": "a_X", "group": "Geometria"})
    b_pedestal_m: float = Field(default=0.0, description="Dimensione in pianta del bicchiere/pilastrino lungo Y", ge=0, le=10,
                                 json_schema_extra={"unit": "m", "symbol": "a_Y", "group": "Geometria"})
    h_pedestal_sopra_m: float = Field(default=0.0, description="Altezza del bicchiere sopra il piano campagna", ge=0, le=10,
                                       json_schema_extra={"unit": "m", "symbol": "s_sup", "group": "Geometria"})
    h_pedestal_sotto_m: float = Field(default=0.0, description="Altezza del bicchiere sotto il piano campagna", ge=0, le=10,
                                       json_schema_extra={"unit": "m", "symbol": "s_inf", "group": "Geometria"})
    offset_leva_m: float = Field(default=0.05, description="Offset aggiuntivo al braccio di leva (rialzo/mensola)", ge=0, le=2,
                                  json_schema_extra={"unit": "m", "symbol": "s", "group": "Geometria", "advanced": True})
    ex_m: float = Field(default=0.0, description="Eccentricità di carico applicata lungo X", ge=-10, le=10,
                         json_schema_extra={"unit": "m", "symbol": "e_X", "group": "Geometria", "advanced": True})
    ey_m: float = Field(default=0.0, description="Eccentricità di carico applicata lungo Y", ge=-10, le=10,
                         json_schema_extra={"unit": "m", "symbol": "e_Y", "group": "Geometria", "advanced": True})

    gamma_terreno_kNm3: float = Field(default=20.0, description="Peso di volume del terreno", gt=0, le=30,
                                       json_schema_extra={"unit": "kN/m3", "symbol": "γ", "group": "Terreno"})
    phi_terreno_deg: float = Field(default=30.0, description="Angolo di attrito del terreno", gt=0, lt=90,
                                    json_schema_extra={"unit": "°", "symbol": "φ", "group": "Terreno"})
    resistenze: tuple[ResistenzaRow, ...] = resistenze_table_field()

    classe_calcestruzzo: ConcreteClass = Field(default="C25/30", description="Classe di resistenza del calcestruzzo",
                                                json_schema_extra={"group": "Materiali"})
    grado_acciaio: RebarGrade = Field(default="B450C", description="Classe di resistenza dell'armatura",
                                       json_schema_extra={"group": "Materiali"})
    gamma_s: float = Field(default=1.15, description="Coefficiente parziale dell'acciaio γs", gt=1, le=1.5,
                            json_schema_extra={"unit": "-", "symbol": "γ_s", "group": "Materiali", "advanced": True})
    copriferro_cm: float = Field(description="Copriferro netto", gt=0, le=30,
                                  json_schema_extra={"unit": "cm", "symbol": "c", "group": "Armatura"})
    passo_armatura_cm: float = Field(description="Passo di posa dell'armatura di progetto", gt=0, le=50,
                                      json_schema_extra={"unit": "cm", "symbol": "s_ferri", "group": "Armatura"})
    diametro_manuale_x_mm: float = Field(default=12.0, description="Diametro minimo imposto per l'armatura X", gt=0, le=40,
                                          json_schema_extra={"unit": "mm", "symbol": "Φ_X,man", "group": "Armatura", "advanced": True})
    diametro_manuale_y_mm: float = Field(default=12.0, description="Diametro minimo imposto per l'armatura Y", gt=0, le=40,
                                          json_schema_extra={"unit": "mm", "symbol": "Φ_Y,man", "group": "Armatura", "advanced": True})

    reazioni: tuple[ReactionRow, ...] = reazioni_table_field()

    legacy_compat: bool = Field(default=False, description="Riproduci il foglio Excel originale (errori inclusi)",
                                 json_schema_extra={"group": "Avanzate", "advanced": True})

    @model_validator(mode="after")
    def _valida(self) -> "PlintoIsolatoInput":
        validate_unique_nodo_combo(self.reazioni)
        validate_unique_famiglia(self.resistenze)
        famiglie_reazioni = {row.famiglia for row in self.reazioni}
        if None in famiglie_reazioni:
            raise ValueError("ogni riga della tabella reazioni deve specificare una famiglia")
        famiglie_resistenze = {row.famiglia for row in self.resistenze}
        mancanti = famiglie_reazioni - famiglie_resistenze
        if mancanti:
            raise ValueError(f"manca la resistenza di progetto del terreno per le famiglie: {sorted(mancanti)}")
        return self


# `table_field()` (shared.tabular) carries no `group` hint; every input needs one
# (docs/BUILD_CONTRACT.md "Batch 2"). Patched here rather than in the shared module.
for _campo, _gruppo in (("resistenze", "Terreno"), ("reazioni", "Reazioni")):
    _field_info = PlintoIsolatoInput.model_fields[_campo]
    _field_info.json_schema_extra = {**(_field_info.json_schema_extra or {}), "group": _gruppo}
PlintoIsolatoInput.model_rebuild(force=True)
