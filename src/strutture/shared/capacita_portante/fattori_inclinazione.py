"""iq, iγ, ic — EN 1997-1 Annex D.2 (drained) / D.3 (undrained) load-inclination factors.

Drained (Annex D.2):
    mB = (2 + B'/L') / (1 + B'/L')            H parallel to B'
    mL = (2 + L'/B') / (1 + L'/B')            H parallel to L'
    mθ = mL·cos²θ + mB·sin²θ                  H at angle θ to the L' axis
    iq = [1 - H / (V + A'·c'·cotφ')]^m
    iγ = [1 - H / (V + A'·c'·cotφ')]^(m+1)
    ic = iq - (1 - iq) / (Nc·tanφ')            φ' > 0

Undrained (Annex D.3):
    ic = 0.5·(1 + sqrt(1 - H/(A'·cu)))
requires H <= A'·cu (the base cannot transmit more shear than the undrained strength offers),
otherwise no equilibrium exists -> `CalcError`.
"""
import math

from strutture.shared.report import CalcError

from .models import Direzione, FattoriInclinazioneCarico


def esponente_m(b_eff_m: float, l_eff_m: float, *, direzione: Direzione = "B", theta_deg: float = 0.0) -> float:
    """m exponent (Annex D.2) for a footing B' x L' (B' <= L') and horizontal load H acting
    along B' (`direzione="B"`), along L' (`direzione="L"`), or at `theta_deg` to the L' axis
    (`direzione="theta"`). A strip footing is `l_eff_m = math.inf`."""
    if b_eff_m <= 0 or l_eff_m <= 0:
        raise ValueError(f"b_eff_m e l_eff_m devono essere > 0, ricevuti {b_eff_m}, {l_eff_m}")
    m_b = 2.0 if math.isinf(l_eff_m) else (2.0 + b_eff_m / l_eff_m) / (1.0 + b_eff_m / l_eff_m)
    m_l = 1.0 if math.isinf(l_eff_m) else (2.0 + l_eff_m / b_eff_m) / (1.0 + l_eff_m / b_eff_m)
    if direzione == "B":
        return m_b
    if direzione == "L":
        return m_l
    theta_rad = math.radians(theta_deg)
    return m_l * math.cos(theta_rad) ** 2 + m_b * math.sin(theta_rad) ** 2


def fattori_inclinazione_carico(
    h_kn: float, v_kn: float, a_eff_m2: float, c_kpa: float, phi_deg: float, nc: float, m: float,
) -> FattoriInclinazioneCarico:
    """Drained iq, iγ, ic (φ' > 0). `h_kn`, `v_kn` >= 0; `h_kn` is the horizontal resultant."""
    if phi_deg <= 0.0:
        raise ValueError("fattori_inclinazione_carico richiede phi_deg > 0 (usare la formula non drenata per phi_deg=0)")
    if h_kn < 0 or v_kn < 0:
        raise ValueError(f"h_kn e v_kn devono essere >= 0, ricevuti {h_kn}, {v_kn}")
    phi_rad = math.radians(phi_deg)
    denom = v_kn + a_eff_m2 * c_kpa / math.tan(phi_rad)
    if denom <= 0 or h_kn >= denom:
        raise CalcError(
            f"Il carico orizzontale H={h_kn:.4g} kN eccede l'aderenza e l'attrito disponibili alla base "
            f"(V + A'·c'·cotφ' = {denom:.4g} kN): equilibrio non verificabile.")
    base = 1.0 - h_kn / denom
    iq = base**m
    igamma = base ** (m + 1.0)
    # Annex D.4's c' term cannot subtract more resistance than it adds; for large H the raw
    # expression can go negative (MEDIUM finding) — clamp at 0 rather than let a pydantic
    # ValidationError escape this physics function (docs/BUILD_CONTRACT.md).
    ic = max(iq - (1.0 - iq) / (nc * math.tan(phi_rad)), 0.0)
    return FattoriInclinazioneCarico(m=m, iq=iq, igamma=igamma, ic=ic)


def fattori_inclinazione_carico_non_drenata(h_kn: float, a_eff_m2: float, cu_kpa: float) -> float:
    """Undrained ic = 0.5·(1 + sqrt(1 - H/(A'·cu))). Raises CalcError if H > A'·cu."""
    if h_kn < 0:
        raise ValueError(f"h_kn deve essere >= 0, ricevuto {h_kn}")
    resistenza_disponibile = a_eff_m2 * cu_kpa
    if h_kn > resistenza_disponibile:
        raise CalcError(
            f"Il carico orizzontale H={h_kn:.4g} kN supera la resistenza al taglio non drenata disponibile "
            f"A'·cu={resistenza_disponibile:.4g} kN: equilibrio non verificabile.")
    return 0.5 * (1.0 + math.sqrt(1.0 - h_kn / resistenza_disponibile))
