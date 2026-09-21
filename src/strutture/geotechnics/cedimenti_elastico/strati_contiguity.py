"""Cross-row contiguity check for the ground-surface `strati` table shared by
`TimoshenkoGoodierInput` and `NewmarkInput`.

Unlike `shared.soil_layers.validate` (used by `cedimenti_edometrico`, whose table is already
anchored at the foundation base), this package's `strati` is measured from the GROUND surface and
may legitimately start above `z=0` -- `ground_to_base.shift_to_base` clamps that leading span to 0
once the foundation embedment `D` swallows it (see that module's docstring), so a leading gap is
not an error here.

Fixes the silent double-counting / silent-zero bug in `shared.soil_layers.weighted_modulus` and
`layer_at`, which both assume the table is already contiguous and ascending and do not detect an
inconsistent one themselves: two overlapping rows are silently summed twice (overstated stiffness,
understated settlement); a gap strictly between two rows contributes a false zero in the numerator
while the full depth stays in the denominator (also an overstated stiffness)."""
from strutture.shared.soil_layers import SoilLayer


def validate_ground_strati(layers: tuple[SoilLayer, ...]) -> None:
    """Raise `ValueError` if two consecutive rows overlap or leave a gap between them. A leading
    gap before `layers[0].z_top_m` is allowed (normal ground-surface input, see module docstring)."""
    for index in range(len(layers) - 1):
        current, following = layers[index], layers[index + 1]
        if current.z_bot_m != following.z_top_m:
            raise ValueError(
                f"riga {index + 1} e riga {index + 2}: la stratigrafia non è contigua "
                f"({current.z_bot_m} m != {following.z_top_m} m)"
            )
