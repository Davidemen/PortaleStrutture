"""Step (spec §4.4): altitude-corrected reference velocity, Vento!H12, §3.3.1 / §3.3.2."""
from strutture.shared.report import CalcError

MAX_ALTITUDINE_FORMULA_M = 1500.0  # §3.3.2: oltre, la norma richiede una valutazione specifica del sito


def coefficiente_altitudine(ks: float, a0: float, altitudine_m: float) -> float:
    """ca (§3.3.2, Tab. 3.3.I NTC2018): 1 per as<=a0; 1+ks*(as/a0-1) per a0<as<=1500 m.

    Oltre 1500 m la norma non fornisce una formula e richiede una valutazione specifica del sito:
    CalcError invece di estrapolare silenziosamente (a differenza della forma NTC2008 superata,
    riprodotta solo in legacy_compat=True).
    """
    if altitudine_m <= a0:
        return 1.0
    if altitudine_m > MAX_ALTITUDINE_FORMULA_M:
        raise CalcError(
            f"Altitudine {altitudine_m:.0f} m oltre {MAX_ALTITUDINE_FORMULA_M:.0f} m: la norma "
            "richiede una valutazione specifica del sito (§3.3.2)."
        )
    return 1.0 + ks * (altitudine_m / a0 - 1.0)


def velocita_riferimento_suolo(
    vb0: float, ka: float, ks: float, a0: float, altitudine_m: float, legacy_compat: bool
) -> tuple[float, float]:
    """vref [m/s] e il coefficiente di altitudine ca [-] applicato (Vento!H12), tali che
    vref == vb0*ca sempre, per costruzione.

    legacy_compat=True riproduce la forma NTC2008 superata `vb = vb0 + ka*(as-a0)` (Vento!H12,
    nessun limite di quota, spec §7). legacy_compat=False applica `vb = vb0*ca` per §3.3.2/Tab. 3.3.I.
    """
    if legacy_compat:
        vref = vb0 + ka * (altitudine_m - a0) if altitudine_m > a0 else vb0
        return vref, vref / vb0
    ca = coefficiente_altitudine(ks, a0, altitudine_m)
    return vb0 * ca, ca
