"""Consistency check between a directly-entered fck and the Rck-derived value (sheet `1m` v2
delta #1: fck becomes a free input, decoupled from Rck, with no in-sheet cross-check — see
docs/specs/small-units.md, ca-taglio-non-armato-v2 'Suspected bugs'). Carried here as a warning
since the sheet accepts an inconsistent pair silently in both legacy_compat modes."""
from .tables import FCK_FROM_RCK_FACTOR, FCK_RCK_TOLLERANZA


def avviso_incoerenza_fck_rck(rck_MPa: float, fck_diretto_MPa: float) -> str | None:
    """None if fck_diretto is within tolerance of 0.83*Rck, else an Italian warning message."""
    atteso_MPa = FCK_FROM_RCK_FACTOR * rck_MPa
    scarto_relativo = abs(fck_diretto_MPa - atteso_MPa) / atteso_MPa
    if scarto_relativo <= FCK_RCK_TOLLERANZA:
        return None
    return (
        f"fck indicato ({fck_diretto_MPa:.2f} MPa) incoerente con Rck ({rck_MPa:.2f} MPa): "
        f"fck atteso da Rck (§11.2.10.1) = {atteso_MPa:.2f} MPa"
    )
