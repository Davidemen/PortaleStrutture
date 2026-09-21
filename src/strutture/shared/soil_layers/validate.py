"""Cross-row validation for a `strati` table: ascending, contiguous, non-overlapping layers.

Call from the consuming tool's `model_validator(mode="after")`; raises `ValueError` (pydantic
attaches it at the table field) naming the 1-based rows, per the contract's Italian convention."""
from .models import SoilLayer


def validate(layers: tuple[SoilLayer, ...]) -> None:
    """Raise `ValueError` unless `layers` form one contiguous, strictly ascending stratigraphy:
    `layers[0].z_top_m == 0` and `layers[i].z_bot_m == layers[i+1].z_top_m` for every i."""
    if not layers:
        raise ValueError("la stratigrafia deve avere almeno uno strato")
    if layers[0].z_top_m != 0:
        raise ValueError(f"riga 1: il primo strato deve partire da 0 m, non da {layers[0].z_top_m} m")
    for index in range(len(layers) - 1):
        current, following = layers[index], layers[index + 1]
        if current.z_bot_m != following.z_top_m:
            raise ValueError(
                f"riga {index + 1} e riga {index + 2}: la stratigrafia non è contigua "
                f"({current.z_bot_m} m != {following.z_top_m} m)"
            )
