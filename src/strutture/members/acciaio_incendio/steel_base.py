"""resistenza!D4:D5 — nominal fy/fu at 20°C by grade (EN10025 nominal values, duplicated here
independently of `acciaio-colonne-ec3/materiali.txt` per the spec's §6 note).

`legacy_compat=True` reproduces resistenza!D5's bug (docs/divergences/acciaio_incendio.md):
`=IF(D2="s235",360,IF(D3="s275",430,510))` tests `D3` (=210000, the elastic modulus) instead of
`D2` (the grade). `D3` is never `"s275"`, so that branch is always false and S275 silently gets
S355's fu=510 instead of 430.
"""
from strutture.shared.tables import exact_lookup

from .models import GradoAcciaioIncendio, MaterialeBase

# grado -> (fy(20°C), fu(20°C) corretto), MPa — resistenza!D4/D5, code-standard mode.
BASE_TABLE_MPA: tuple[tuple[GradoAcciaioIncendio, tuple[float, float]], ...] = (
    ("S235", (235.0, 360.0)),
    ("S275", (275.0, 430.0)),
    ("S355", (355.0, 510.0)),
)


def materiale_base(grado: GradoAcciaioIncendio, *, legacy_compat: bool = False) -> MaterialeBase:
    """fy(20°C)/fu(20°C) for `grado`. `legacy_compat=True` reproduces the D5 fu bug for S275."""
    fy_20, fu_20 = exact_lookup(BASE_TABLE_MPA, grado)
    if legacy_compat and grado != "S235":
        fu_20 = 510.0  # sheet's dead 2nd IF branch never fires -> always falls through to 510.
    return MaterialeBase(fy_20_MPa=fy_20, fu_20_MPa=fu_20)
