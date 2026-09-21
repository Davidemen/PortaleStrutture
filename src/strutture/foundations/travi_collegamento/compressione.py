"""Axial compression check Nc,Rd > NEd (NTC C29/C30/C31, EN C27/C28/C29)."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.report import Check
from strutture.shared.units import N_PER_KN


class CompressioneResult(BaseModel):
    """Nc,Rd, verifica, tasso di lavoro."""

    model_config = ConfigDict(frozen=True)

    ncrd_kN: float = Field(description="Forza assiale resistente a compressione Nc,Rd", json_schema_extra={"unit": "kN", "symbol": "N_c,Rd"}, gt=0)
    verifica: Check
    tasso_lavoro: float = Field(
        description="Tasso di lavoro a compressione, azione di progetto su resistenza",
        json_schema_extra={"unit": "-", "symbol": "η_c", "highlight": True}, ge=0
    )


def compressione(ac_mm2: float, fcd_MPa: float, ned_kN: float) -> CompressioneResult:
    """Nc,Rd[C29/C27] = Ac·fcd/1000 (mm²·MPa = N); verifica: Nc,Rd > NEd."""
    ncrd_kN = ac_mm2 * fcd_MPa / N_PER_KN
    return CompressioneResult(
        ncrd_kN=ncrd_kN,
        verifica=Check(
            name="Verifica a compressione", passed=ncrd_kN > ned_kN, clause="NTC2018 §7.2.5",
            value=ned_kN, limit=ncrd_kN, unit="kN",
        ),
        tasso_lavoro=ned_kN / ncrd_kN,
    )
