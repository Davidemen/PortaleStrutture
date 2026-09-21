"""Normalization unit tests: case/accent folding for comune/provincia matching."""
import pytest

from strutture.shared.comuni.normalize import normalize_name

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("Milano", "milano"),
        ("MILANO", "MiLaNo"),
        ("Città Sant'Angelo", "citta sant'angelo"),
        ("Cirò Marina", "ciro marina"),
        ("  Bergamo  ", "Bergamo"),
        ("Petronà", "PETRONA"),
    ],
)
def test_equivalent_spellings_normalize_equal(a, b):
    assert normalize_name(a) == normalize_name(b)


def test_different_names_normalize_different():
    assert normalize_name("Milano") != normalize_name("Torino")


def test_rejects_non_string():
    with pytest.raises(TypeError):
        normalize_name(123)  # type: ignore[arg-type]
