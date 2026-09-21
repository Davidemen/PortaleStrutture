import pytest

from strutture.loads.neve.accumulo_mw import MW_MAX, MW_MIN, mu_w, mu_w_grezzo, rapporto_gamma_h_qsk
from strutture.loads.neve.models import AccumuloInput
from strutture.loads.neve.tool import run_accumulo

pytestmark = pytest.mark.unit


def test_rapporto_gamma_h_qsk():
    assert rapporto_gamma_h_qsk(2.0, 10.0, 1.5) == pytest.approx(13.333333, rel=1e-6)


def test_mu_w_grezzo_takes_the_smaller_of_geometry_and_gamma_ratio():
    assert mu_w_grezzo(1.0, 1.0, 10.0, 100.0) == pytest.approx(0.1)  # geometry term wins
    assert mu_w_grezzo(100.0, 100.0, 10.0, 0.5) == pytest.approx(0.5)  # gamma-ratio term wins


def test_mu_w_clamps_to_upper_bound_circ_c3_4_5_6():
    """Circ. 2019 §C3.4.5.6 / EN1991-1-3 §6.2(3): mu_w <= 4.0 — confirmed, not a placeholder."""
    assert mu_w(10.0) == pytest.approx(MW_MAX)


def test_mu_w_clamps_to_lower_bound_circ_c3_4_5_6():
    """Circ. 2019 §C3.4.5.6 / EN1991-1-3 §6.2(3): mu_w >= 0.8, the companion lower bound to
    MW_MAX. The sheet's own H36 formula applies both bounds unconditionally, so this must hold
    with no legacy_compat branching (see `mu_w`'s docstring)."""
    assert mu_w(0.1) == pytest.approx(MW_MIN)
    assert mu_w(0.0) == pytest.approx(MW_MIN)


def test_mu_w_passthrough_within_bounds():
    assert mu_w(2.5) == pytest.approx(2.5)


def test_run_accumulo_applies_lower_bound_in_code_standard_mode():
    """A narrow, tall geometry drives the raw mu_w below 0.8; `neve-accumulo` in code-standard
    mode (legacy_compat=False) must still clamp the reported mw at MW_MIN, per Circ. 2019
    §C3.4.5.6 — same as legacy mode, since the sheet's own formula already enforces this bound.
    """
    inputs = AccumuloInput(
        zona="II",
        as_m=100,
        topografia="Normale",
        ct=1.0,
        b1=0.1,
        b2=0.1,
        h=10.0,
        gamma=2.0,
        a=0.0,
        m1_input=0.5,
        msup=0.5,
        legacy_compat=False,
    )
    report = run_accumulo(inputs)
    assert report.ok
    assert report.data.mw == pytest.approx(MW_MIN)


def test_run_accumulo_applies_lower_bound_in_legacy_mode_too():
    inputs = AccumuloInput(
        zona="II",
        as_m=100,
        topografia="Normale",
        ct=1.0,
        b1=0.1,
        b2=0.1,
        h=10.0,
        gamma=2.0,
        a=0.0,
        m1_input=0.5,
        msup=0.5,
        legacy_compat=True,
    )
    report = run_accumulo(inputs)
    assert report.ok
    assert report.data.mw == pytest.approx(MW_MIN)
