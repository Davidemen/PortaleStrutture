"""Composed output model for `geo-cedimento-edometrico` (docs/architecture-batch2.md §1
`geotechnics/cedimenti_edometrico`: `carico`, `profondita_critica`, `righe` [chart], `cedimento`
[highlight])."""
from pydantic import BaseModel, ConfigDict, Field

from .carico import CaricoResult
from .cedimento import CedimentoResult
from .profondita_critica import ProfonditaCriticaResult
from .righe import RigaResult

_CHART_RIGHE = {
    "x": "z_m",
    "y": ["delta_sigma_kPa", "cumulativo_cm"],
    "x_label": "z [m]",
    "y_label": "Δσv,q [kPa] / cedimento cumulato [cm]",
    "guides": [{"field": "profondita_critica.z_crit_utilizzato_m", "label": "Z,crit"}],
}


class EdometricoOutput(BaseModel):
    """Full result envelope: applied/net pressure, critical depth, the per-slice profile (with
    `chart`) and the total settlement."""

    model_config = ConfigDict(frozen=True)

    carico: CaricoResult = Field(description="Pressione applicata e netta di progetto")
    profondita_critica: ProfonditaCriticaResult = Field(description="Profondità critica (criterio Δσv,q = 0.1·Δσ'v)")
    righe: tuple[RigaResult, ...] = Field(
        description="Profilo tensione-cedimento per fetta di profondità",
        json_schema_extra={"chart": _CHART_RIGHE},
    )
    cedimento: CedimentoResult = Field(description="Cedimento edometrico totale")
