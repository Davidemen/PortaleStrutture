import pytest

from strutture.loads.sisma.validazione_sito import valida_parametri_sito
from strutture.shared.report import CalcError


@pytest.mark.unit
def test_valid_inputs_do_not_raise():
    valida_parametri_sito(0.098, 2.436, 0.272)


@pytest.mark.unit
@pytest.mark.parametrize(
    "ag_g,f0,tc_star_s",
    [
        (0.0, 2.436, 0.272),  # ag too low
        (1.5, 2.436, 0.272),  # ag too high
        (0.098, 0.5, 0.272),  # F0 too low
        (0.098, 6.0, 0.272),  # F0 too high
        (0.098, 2.436, 0.0),  # T*C too low
        (0.098, 2.436, 3.0),  # T*C too high
    ],
)
def test_out_of_range_raises_calc_error_with_italian_message(ag_g: float, f0: float, tc_star_s: float):
    with pytest.raises(CalcError):
        valida_parametri_sito(ag_g, f0, tc_star_s)
