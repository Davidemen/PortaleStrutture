"""`validate`: ascending, contiguous, starts at 0 — cross-row rules for a `strati` table."""
import pytest

from strutture.shared.soil_layers import SoilLayer, validate

CONTIGUOUS = (
    SoilLayer(z_top_m=0.0, z_bot_m=1.0, modulo_MPa=10.0),
    SoilLayer(z_top_m=1.0, z_bot_m=2.5, modulo_MPa=12.0),
    SoilLayer(z_top_m=2.5, z_bot_m=5.0, modulo_MPa=15.0),
)


@pytest.mark.unit
def test_accepts_contiguous_stratigraphy() -> None:
    validate(CONTIGUOUS)  # does not raise


@pytest.mark.unit
def test_rejects_empty_table() -> None:
    with pytest.raises(ValueError, match="almeno uno strato"):
        validate(())


@pytest.mark.unit
def test_rejects_first_layer_not_starting_at_zero() -> None:
    layers = (SoilLayer(z_top_m=0.5, z_bot_m=2.0, modulo_MPa=10.0),)
    with pytest.raises(ValueError, match="riga 1"):
        validate(layers)


@pytest.mark.unit
def test_rejects_gap_between_layers() -> None:
    layers = (
        SoilLayer(z_top_m=0.0, z_bot_m=1.0, modulo_MPa=10.0),
        SoilLayer(z_top_m=1.5, z_bot_m=3.0, modulo_MPa=12.0),
    )
    with pytest.raises(ValueError, match="riga 1 e riga 2"):
        validate(layers)


@pytest.mark.unit
def test_rejects_overlap_between_layers() -> None:
    layers = (
        SoilLayer(z_top_m=0.0, z_bot_m=2.0, modulo_MPa=10.0),
        SoilLayer(z_top_m=1.5, z_bot_m=3.0, modulo_MPa=12.0),
    )
    with pytest.raises(ValueError, match="non è contigua"):
        validate(layers)
