"""Step: cracked-section neutral axis + elastic stresses for the SLS checks (docs/specs/
fond-plinti-isolati.md Tool-2 steps 14-15, `INPUT!X7,X8,X16:X23,AB22:AB23`).

Reuses `shared.section_geometry.cracked_neutral_axis` (n=15 homogenisation) for the neutral-axis
depth. Pure formulas only: whichever depth (gross H or effective d) the caller passes in is used
verbatim as both the neutral-axis input and the lever-arm base. The sheet plugs the *gross* plinth
height H where EC2 §7.2/§7.3 want the effective depth d = H - copriferro - phi/2 (CRITICAL, review
finding: this understated the SLS stresses by up to +26.6% concrete / +16.5% steel on a realistic
footing); `sle.py` is the composing module that decides which one to pass — `legacy_compat=True`
passes H (sheet reproduction), `legacy_compat=False` passes the effective depth (same margin
`flessione._as_required_cm2` already uses for the ULS steel area). See
docs/divergences/plinti-isolati.md."""
from strutture.shared.section_geometry import cracked_neutral_axis

NMM_PER_KNM = 1.0e6


def profondita_asse_neutro_mm(larghezza_mm: float, altezza_mm: float, as_prov_mm2: float) -> float:
    """Neutral-axis depth xi of the cracked section (n=15), width `larghezza_mm`, singly reinforced."""
    return cracked_neutral_axis(b_mm=larghezza_mm, d_mm=altezza_mm, d2_mm=0.0, as_mm2=as_prov_mm2,
                                 as2_mm2=0.0).x_mm


def sigma_calcestruzzo_MPa(m_kNm: float, larghezza_mm: float, xi_mm: float, altezza_mm: float) -> float:
    """sigma_c = 2*M / (b*xi*(H - xi/3)), M in kN*m -> N*mm via NMM_PER_KNM."""
    braccio_mm = altezza_mm - xi_mm / 3.0
    return 2.0 * m_kNm * NMM_PER_KNM / (larghezza_mm * xi_mm * braccio_mm)


def sigma_acciaio_MPa(m_kNm: float, as_prov_mm2: float, xi_mm: float, altezza_mm: float) -> float:
    """sigma_s = M / (As,prov*(H - xi/3)), M in kN*m -> N*mm via NMM_PER_KNM."""
    braccio_mm = altezza_mm - xi_mm / 3.0
    return m_kNm * NMM_PER_KNM / (as_prov_mm2 * braccio_mm)
