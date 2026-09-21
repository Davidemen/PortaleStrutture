"""kPa <-> kg/cm2 conversion at the `sistema_unita`/`legacy_compat` boundary (docs/architecture-batch2.md
§9-D1). The source sheet approximates 1 MPa = 10 kg/cm2 everywhere (`CHECKS!Q,R,W,Y,AA`: `10*N/mm2`);
the exact factor is 1 MPa = 1000/98.0665 = 10.1972 kg/cm2 (`shared.units.kpa_to_kgcm2`). Reproduce the
sheet's approximation under `legacy_compat=True`; use `shared.units` otherwise (divergence: see
docs/divergences/plinti-isolati.md)."""
from strutture.shared import units
from strutture.shared.divergences import legacy

LEGACY_MPA_TO_KGCM2 = 10.0  # sheet's approximation of 1 MPa in kg/cm2 (exact: ~10.1972).


def kpa_to_kgcm2(value_kpa: float, *, legacy_compat: bool) -> float:
    """Convert a pressure from kPa to kg/cm2, sheet-approximate or exact."""
    if legacy("plinti-isolati/fattore-mpa-kgcm2-approssimato", legacy_compat):
        return value_kpa / units.KPA_PER_MPA * LEGACY_MPA_TO_KGCM2
    return units.kpa_to_kgcm2(value_kpa)


def kgcm2_to_kpa(value_kgcm2: float, *, legacy_compat: bool) -> float:
    """Convert a pressure from kg/cm2 to kPa, sheet-approximate or exact (inverse of `kpa_to_kgcm2`)."""
    if legacy("plinti-isolati/fattore-mpa-kgcm2-approssimato", legacy_compat):
        return value_kgcm2 / LEGACY_MPA_TO_KGCM2 * units.KPA_PER_MPA
    return units.kgcm2_to_kpa(value_kgcm2)


def sigma_ammissibile_kpa(value: float, *, sistema_unita: str, legacy_compat: bool) -> float:
    """Boundary conversion of a `resistenze` row value to kPa (§9-D1: converted once, here)."""
    if sistema_unita == "tecnico" or legacy("plinti-isolati/fattore-mpa-kgcm2-approssimato", legacy_compat):
        return kgcm2_to_kpa(value, legacy_compat=legacy_compat)
    return value
