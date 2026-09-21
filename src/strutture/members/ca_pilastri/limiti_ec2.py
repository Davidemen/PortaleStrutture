"""EC2-only rules (EN 1992-1-1:2005 with the Italian National Annex): shear ν1 reduction factor
(§6.2.2(6)), slenderness limit (§5.8.3.1(1)) with its A/B/C coefficients — docs/specs/ca-pilastri-ec2.md.
Kept out of the norm-agnostic step modules per architecture-batch2.md §3 ("small per-norm modules").
"""
import math

from strutture.shared.materials.concrete import fck
from strutture.shared.units import kn_to_n

from .models import ClsClasse
from .snellezza import coefficiente_c as _coefficiente_c_nota3

LAMBDA_LIM_COEFFICIENT_EC2 = 20.0  # EC2 §5.8.3.1(1): λlim = 20*A*B*C/√n
A_DEFAULT = 0.7  # nota 1: coefficiente A per rapporto di viscosità efficace φef non noto
NU1_BASE = 0.6  # EC2 §6.2.2(6): ν1 = 0.6*(1-fck/250)
NU1_FCK_DIVISOR_MPA = 250.0


def nu1(cls: ClsClasse, *, legacy_compat: bool) -> float:
    """CX28: ν1 = 0.6·(1-fck/250); `fck` follows the same `legacy_compat` fill-down as `fcd`
    (Tabelle!M34:Q41 col. 3, the same lookup the sheet's own ν1 formula reads from)."""
    fck_MPa = fck(cls, legacy_compat=legacy_compat)
    return NU1_BASE * (1.0 - fck_MPa / NU1_FCK_DIVISOR_MPA)


def omega_meccanico(fyd_MPa: float, as_mm2: float, fcd_MPa: float, ac_mm2: float) -> float:
    """CX49 (rapporto meccanico di armatura): ω = fyd·As/(fcd·Ac)."""
    return fyd_MPa * as_mm2 / (fcd_MPa * ac_mm2)


def coefficiente_a(phi_ef: float | None, *, a_fisso: float | None) -> float:
    """A (EC2 §5.8.3.1(1), nota 1): `a_fisso` reproduces the sheet's hardcoded 0.7 when given
    (legacy); otherwise `A = 1/(1+0.2*phi_ef)` when φef is known, else the same 0.7 default."""
    if a_fisso is not None:
        return a_fisso
    if phi_ef is None:
        return A_DEFAULT
    return 1.0 / (1.0 + 0.2 * phi_ef)


def coefficiente_c(rm: float | None, *, c_fisso: float | None) -> float:
    """C (EC2 §5.8.3.1(1), nota 3): `c_fisso` reproduces the sheet's hardcoded 0.7 when given
    (legacy); otherwise `C = 1.7 - rm` when rm is known, else `C = 0.7` (nota 3: "if rm is not
    known, C=0.7 may be used") — same rule as the NTC2018 code-standard branch, see
    `snellezza.coefficiente_c`."""
    return c_fisso if c_fisso is not None else _coefficiente_c_nota3(rm)


def lambda_limite(ned_kN: float, ac_mm2: float, fcd_MPa: float, omega: float, *, a: float, c: float) -> float:
    """λlim = 20·A·B·C/√n, B = √(1+2ω), n = Ned(N)/(Ac·fcd) — this EC2 formula already includes
    the ×1000 kN→N conversion in the sheet itself (no legacy bug to reproduce here)."""
    b = math.sqrt(1.0 + 2.0 * omega)
    n = kn_to_n(ned_kN) / (ac_mm2 * fcd_MPa)
    return LAMBDA_LIM_COEFFICIENT_EC2 * a * b * c / math.sqrt(n)
