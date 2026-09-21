"""Design axial tie force NEd = amax·Nsd·α (NTC2018 §7.2.5 C24/C28, EN1998 C22/C26)."""
from pydantic import BaseModel, ConfigDict, Field


class AzioneResult(BaseModel):
    """Nsd, NEd."""

    model_config = ConfigDict(frozen=True)

    nsd_kN: float = Field(description="Valore medio delle forze verticali agenti sugli elementi collegati Nsd", json_schema_extra={"unit": "kN", "symbol": "N_sd"}, ge=0)
    ned_kN: float = Field(description="Forza assiale di progetto NEd", json_schema_extra={"unit": "kN", "symbol": "N_Ed"}, ge=0)


def azione(n1_kN: float, n2_kN: float, amax_g: float, alpha: float) -> AzioneResult:
    """Nsd[C24/C22] = (N1+N2)/2; NEd[C28/C26] = amax·Nsd·α."""
    nsd_kN = (n1_kN + n2_kN) / 2.0
    return AzioneResult(nsd_kN=nsd_kN, ned_kN=amax_g * nsd_kN * alpha)
