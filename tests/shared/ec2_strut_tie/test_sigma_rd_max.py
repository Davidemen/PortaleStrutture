"""§6.5.4(4) node stress limits CCC/CCT/CTT. EN default coefficients k1=1.0, k2=0.85, k3=0.75.
Note: docs/specs/fond-plinti-pali.md's own node formulas use different (sheet-specific) coefficients
(1.18/0.85, 1.0, 0.88) — see docs/divergences/ec2-shared.md, kept only inside `plinti_pali`."""
import pytest

from strutture.shared.ec2_strut_tie import sigma_rd_max


@pytest.mark.parametrize(
    ("nodo", "k_expected"),
    [("CCC", 1.0), ("CCT", 0.85), ("CTT", 0.75)],
)
def test_node_coefficients_match_en_defaults(nodo, k_expected):
    fck, gamma_c = 30.0, 1.5
    result = sigma_rd_max(fck, nodo, gamma_c)
    nu_prime = 1.0 - fck / 250.0
    fcd = fck / gamma_c
    assert result.sigma_rd_max_MPa == pytest.approx(k_expected * nu_prime * fcd)
    assert result.nu_prime == pytest.approx(nu_prime)
    assert result.fcd_MPa == pytest.approx(fcd)


def test_national_annex_coefficients_are_overridable():
    default = sigma_rd_max(30.0, "CCT", 1.5)
    custom = sigma_rd_max(30.0, "CCT", 1.5, k2=1.0)
    assert custom.sigma_rd_max_MPa == pytest.approx(default.sigma_rd_max_MPa / 0.85)


def test_unknown_node_raises():
    with pytest.raises(ValueError, match="nodo"):
        sigma_rd_max(30.0, "XYZ", 1.5)  # type: ignore[arg-type]


def test_invalid_gamma_c_raises():
    with pytest.raises(ValueError):
        sigma_rd_max(30.0, "CCC", 0.0)
