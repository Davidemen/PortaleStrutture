"""Output model for `fond-plinto-su-pali` (docs/architecture-batch2.md §2: `righe` paged, `inviluppo`
per governing quantity, `governante` expanded, checks on the envelope only)."""
from pydantic import BaseModel, ConfigDict, Field

from .inviluppo import InviluppoRiga
from .materiali import Materiali
from .models_flessione import Flessione
from .models_puntoni_tiranti import PuntoniTiranti
from .models_taglio import CapacitaPalo, Punzonamento, PunzonamentoPalo, Taglio
from .rows import RigaCarico


class PlintoSuPaliOutput(BaseModel):
    """Full strut-and-tie verification of one pile cap against every row of the `reazioni` table."""

    model_config = ConfigDict(frozen=True)

    materiali: Materiali = Field(description="Proprietà dei materiali")
    righe: tuple[RigaCarico, ...] = Field(
        description="Reazione assiale di ogni palo per ogni combinazione di carico",
        json_schema_extra={"rows_page": 200, "chart": {"x": "combo", "y": ["n_max_pila_kN", "n_min_pila_kN"],
                                                         "y_label": "Reazione assiale sul palo [kN]"}},
    )
    inviluppo: tuple[InviluppoRiga, ...] = Field(description="Valore e combinazione governante per grandezza")
    governante: RigaCarico = Field(description="Combinazione governante per la reazione massima sul palo")
    flessione: Flessione = Field(description="Progetto a flessione della soletta del plinto")
    puntoni_tiranti: PuntoniTiranti = Field(description="Verifica a puntoni e tiranti (EC2 §6.5)")
    taglio: Taglio = Field(description="Verifica a taglio (EC2 §6.2.2)")
    punzonamento: Punzonamento = Field(description="Verifica a punzonamento al filo pilastro (EC2 §6.4.5)")
    punzonamento_palo: PunzonamentoPalo = Field(description="Verifica a punzonamento del palo d'angolo (EC2 §6.4.2)")
    capacita_compressione: CapacitaPalo = Field(description="Verifica della capacità portante del palo a compressione")
    capacita_trazione: CapacitaPalo | None = Field(
        description="Verifica della capacità portante del palo a trazione (solo se un palo risulta teso)",
    )

    n_max_pila_kN: float = Field(
        description="Reazione assiale massima di progetto sul palo, peso proprio incluso", ge=0,
        json_schema_extra={"unit": "kN", "symbol": "N_max", "highlight": True},
    )
    utilizzo_puntoni_tiranti: float = Field(
        description="Utilizzo governante tra puntone e tiranti", ge=0,
        json_schema_extra={"unit": "-", "symbol": "η_st", "highlight": True},
    )
    utilizzo_taglio_punzonamento: float = Field(
        description="Utilizzo governante tra taglio e punzonamento", ge=0,
        json_schema_extra={"unit": "-", "symbol": "η_v", "highlight": True},
    )
