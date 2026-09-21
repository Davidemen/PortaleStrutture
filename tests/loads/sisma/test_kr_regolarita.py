import pytest

from strutture.loads.sisma.kr_regolarita import kr_regolare_altezza


@pytest.mark.unit
@pytest.mark.parametrize("regolare_altezza,expected", [("SI", 1.0), ("si", 1.0), ("NO", 0.8), ("no", 0.8)])
def test_kr(regolare_altezza: str, expected: float):
    assert kr_regolare_altezza(regolare_altezza) == pytest.approx(expected)
