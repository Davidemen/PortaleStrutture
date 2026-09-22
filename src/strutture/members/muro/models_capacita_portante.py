"""Optional bearing-capacity ('Terreno di fondazione') result models of the `muro-sostegno` tool
(split out of `models.py`, regola dura 12 dei moduli piccoli).
"""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.report import Check

from .models_common import NomeCombo


class CapacitaPortanteCombo(BaseModel):
    """One row of the bearing-capacity check on the strip footing (docs/architecture-phase4.md §C
    "Integration"): q_lim/R_d computed by `strutture.shared.capacita_portante` on the base nastriforme
    (per metro, L'->infinito, fattori di forma=1), with B'=B-2e from this combination's
    `pressioni_terreno.eccentricita_m` and H/V from its `ribaltamento_scorrimento` resultants.
    Present only when the optional 'Terreno di fondazione' block is filled (legacy_compat=False)."""

    model_config = ConfigDict(frozen=True)

    nome: NomeCombo = Field(description="Identificativo della combinazione")
    q_lim_kPa: float = Field(description="Pressione limite di capacità portante", ge=0, json_schema_extra={"unit": "kPa", "symbol": "q_lim"})
    r_d_kN: float = Field(description="Resistenza di progetto, per metro di sviluppo del muro", ge=0, json_schema_extra={"unit": "kN", "symbol": "R_d"})
    rapporto: float = Field(description="Grado di sfruttamento del terreno di fondazione", ge=0, json_schema_extra={"unit": "-", "symbol": "N_Ed/R_d"})


class CapacitaPortanteFondazioneResult(BaseModel):
    """Composed result: q_lim/R_d/rapporto per combinazione + la combinazione governante."""

    model_config = ConfigDict(frozen=True)

    combinazioni: tuple[CapacitaPortanteCombo, ...] = Field(
        description="q_lim, R_d e grado di sfruttamento per combinazione (STR_1, STR_2, SISMA_1, SISMA_2: "
                    "le uniche coerenti con i parametri caratteristici del terreno non ridotti e il γR usati "
                    "qui; GEO_1/GEO_2/EQU_1/EQU_2 userebbero uno schema Approccio/γR diverso, non implementato)")
    combo_governante: NomeCombo = Field(description="Combinazione con il grado di sfruttamento N_Ed/R_d maggiore")
    rapporto_governante: float = Field(
        description="Grado di sfruttamento governante N_Ed/R_d", ge=0,
        json_schema_extra={"unit": "-", "symbol": "N_Ed/R_d", "highlight": True},
    )
    verifica: Check = Field(description="Esito della verifica di capacità portante sulla combinazione governante (N_Ed ≤ R_d)")
