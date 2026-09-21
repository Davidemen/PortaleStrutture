"""Output model for `fond-plinto-isolato` (docs/architecture-batch2.md §2: `righe` paged, `inviluppo`
per quantity x famiglia, `governante` expanded, checks on the envelope only)."""
from pydantic import BaseModel, ConfigDict, Field

from .inviluppo import Eccentricita, InviluppoRiga
from .materiali import Materiali
from .models_flessione import Flessione
from .models_sle import Sle
from .riga_verifica import RigaVerifica


class PlintoIsolatoOutput(BaseModel):
    """Full verification of one footing type against every row of the `reazioni` table."""

    model_config = ConfigDict(frozen=True)

    materiali: Materiali = Field(description="Proprietà dei materiali")
    righe: tuple[RigaVerifica, ...] = Field(
        description="Verifica di ogni combinazione della tabella reazioni",
        json_schema_extra={"rows_page": 200, "chart": {"x": "combo", "y": ["sigma_max_kpa"],
                                                         "y_label": "Pressione di contatto [kPa]"}},
    )
    inviluppo: tuple[InviluppoRiga, ...] = Field(description="Valore e combinazione governante per grandezza e famiglia")
    eccentricita: Eccentricita = Field(description="Inviluppo delle eccentricità su tutte le combinazioni")
    governante: RigaVerifica = Field(description="Combinazione governante per la pressione di contatto massima")
    flessione: Flessione = Field(description="Progetto a flessione del plinto al filo pilastro")
    sle: Sle = Field(description="Verifiche di esercizio (tensioni in calcestruzzo e acciaio)")

    sigma_max_governante_kpa: float = Field(
        description="Pressione di contatto massima governante, su tutte le famiglie", ge=0,
        json_schema_extra={"unit": "kPa", "symbol": "σ_max", "highlight": True},
    )
    mu_scorrimento_minimo: float | None = Field(
        description="Coefficiente di sicurezza allo scorrimento minimo, su tutte le famiglie",
        json_schema_extra={"unit": "-", "symbol": "μ_scorr", "highlight": True},
    )
    mu_ribaltamento_minimo: float | None = Field(
        description="Coefficiente di sicurezza al ribaltamento minimo, su tutte le famiglie e direzioni",
        json_schema_extra={"unit": "-", "symbol": "μ_rib", "highlight": True},
    )
