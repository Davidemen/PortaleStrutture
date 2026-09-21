import pytest

from strutture.foundations.plinti_isolati.riga_verifica import riga_verifica
from strutture.shared.load_table import ReactionRow
from strutture.shared.report import CalcError


def _riga(**overrides) -> ReactionRow:
    base = {"nodo": 1832, "combo": "ULS1", "famiglia": "SLU_STR", "fx_kN": 0.131665, "fy_kN": 5.37205,
            "fz_kN": 220.927, "mx_kNm": -36.4022, "my_kNm": 1.31727, "mz_kNm": -0.0608972}
    return ReactionRow(**{**base, **overrides})


@pytest.mark.golden
def test_riga_verifica_golden() -> None:
    """Full composition against docs/specs/fond-plinti-isolati.md golden case (ULS1, node 1832)."""
    riga = riga_verifica(_riga(), 4.0, 4.0, 0.8, 4.5, 0.0, 0.0, 0.0, 0.0, 0.05, 0.0, 0.0, 20.0, 30.0,
                          metodo_pressioni="sovrapposizione", legacy_compat=True)
    assert riga.n_kN == pytest.approx(2596.93, rel=1e-5)
    assert riga.myy_kNm == pytest.approx(1.42918, rel=1e-5)
    assert riga.mxx_kNm == pytest.approx(40.9685, rel=1e-5)
    assert riga.compressed_ratio == pytest.approx(1.0)
    assert riga.mu_ribaltamento_x == 100.0
    assert riga.mu_ribaltamento_y == 100.0
    assert riga.mu_scorrimento == 100.0


@pytest.mark.unit
def test_riga_verifica_famiglia_obbligatoria() -> None:
    with pytest.raises(CalcError):
        riga_verifica(_riga(famiglia=None), 4.0, 4.0, 0.8, 4.5, 0.0, 0.0, 0.0, 0.0, 0.05, 0.0, 0.0, 20.0, 30.0,
                       metodo_pressioni="esatto", legacy_compat=False)


@pytest.mark.unit
def test_riga_verifica_geometria_incompatibile_solleva_calc_error() -> None:
    """A resultant genuinely outside the footing footprint is a domain error, not a crash, and the
    message names the offending combo/node."""
    with pytest.raises(CalcError, match="ULS1"):
        riga_verifica(_riga(mx_kNm=-100000.0), 4.0, 4.0, 0.8, 4.5, 0.0, 0.0, 0.0, 0.0, 0.05, 0.0, 0.0, 20.0, 30.0,
                       metodo_pressioni="esatto", legacy_compat=False)
