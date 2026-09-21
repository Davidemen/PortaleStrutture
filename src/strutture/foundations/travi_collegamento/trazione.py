"""Axial tension check Nt,Rd > NEd (NTC C32/C33/C34, EN C30/C31/C32).

**Sheet bug** (both sheets, same pattern): `check_t` compares `Nt,Rd` against the *compression*
work ratio `T.L._c` (NTC `C33={=IF(C32>C31,...)}`, EN `C31={=IF(C30>C29,...)}`) instead of `NEd`
(`C28`/`C26`) — a copy-paste off-by-one-row error. Since `T.L._c` is a dimensionless ratio (~0-1)
and `Nt,Rd` is a force in kN, the sheet's check is nearly always "OK" regardless of the actual
tension demand. `legacy_compat=True` reproduces it; `legacy_compat=False` compares against NEd.
"""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.report import Check
from strutture.shared.units import N_PER_KN


class TrazioneResult(BaseModel):
    """Nt,Rd, verifica, tasso di lavoro."""

    model_config = ConfigDict(frozen=True)

    ntrd_kN: float = Field(description="Forza assiale resistente a trazione Nt,Rd", json_schema_extra={"unit": "kN", "symbol": "N_t,Rd"}, gt=0)
    verifica: Check
    tasso_lavoro: float = Field(
        description="Tasso di lavoro a trazione, azione di progetto su resistenza",
        json_schema_extra={"unit": "-", "symbol": "η_t", "highlight": True}, ge=0
    )


def trazione(
    as_mm2: float, fyd_MPa: float, ned_kN: float, tasso_lavoro_compressione: float, *, legacy_compat: bool = False,
) -> TrazioneResult:
    """Nt,Rd[C32/C30] = As·fyd/1000; verifica: Nt,Rd > NEd (fixed) vs Nt,Rd > T.L._c (sheet bug)."""
    ntrd_kN = as_mm2 * fyd_MPa / N_PER_KN
    termine_confronto = tasso_lavoro_compressione if legacy_compat else ned_kN
    return TrazioneResult(
        ntrd_kN=ntrd_kN,
        verifica=Check(
            name="Verifica a trazione", passed=ntrd_kN > termine_confronto, clause="NTC2018 §7.2.5",
            value=ned_kN, limit=ntrd_kN, unit="kN",
        ),
        tasso_lavoro=ned_kN / ntrd_kN,
    )
