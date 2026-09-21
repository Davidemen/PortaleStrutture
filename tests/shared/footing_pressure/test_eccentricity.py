import pytest

from strutture.shared.footing_pressure.eccentricity import eccentricities, in_kern_biaxial, in_kern_uniaxial

pytestmark = pytest.mark.unit


def test_eccentricities_convention_my_gives_ex_mx_gives_ey():
    # docs/specs/fond-plinti-isolati.md steps 6-8: MYY -> eccX, MXX -> eccY.
    ex_m, ey_m = eccentricities(n_kn=100.0, mx_knm=50.0, my_knm=20.0)
    assert ex_m == pytest.approx(0.2)
    assert ey_m == pytest.approx(0.5)


def test_eccentricities_rejects_non_positive_n():
    with pytest.raises(ValueError):
        eccentricities(n_kn=0.0, mx_knm=1.0, my_knm=1.0)
    with pytest.raises(ValueError):
        eccentricities(n_kn=-10.0, mx_knm=1.0, my_knm=1.0)


@pytest.mark.parametrize(("e", "l_m", "expected"), [(0.0, 6.0, True), (1.0, 6.0, True), (1.0 + 1e-9, 6.0, False),
                                                     (-1.0, 6.0, True), (2.0, 6.0, False)])
def test_in_kern_uniaxial_threshold_at_l_over_6(e, l_m, expected):
    assert in_kern_uniaxial(e, l_m) is expected


def test_in_kern_biaxial_diamond_shape():
    bx, by = 6.0, 4.0  # kern half-widths: bx/6=1.0, by/6=0.667
    assert in_kern_biaxial(0.0, 0.0, bx, by) is True
    assert in_kern_biaxial(1.0, 0.0, bx, by) is True  # exactly on the X vertex of the diamond
    assert in_kern_biaxial(0.0, 2.0 / 3.0, bx, by) is True  # exactly on the Y vertex
    assert in_kern_biaxial(0.5, 1.0 / 3.0, bx, by) is True  # halfway: 0.5/1 + (1/3)/(2/3) = 1
    assert in_kern_biaxial(0.6, 1.0 / 3.0, bx, by) is False
    assert in_kern_biaxial(-0.5, -1.0 / 3.0, bx, by) is True  # symmetric in sign
