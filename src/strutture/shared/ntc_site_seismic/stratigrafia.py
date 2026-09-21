"""NTC 2018 Tab. 3.2.IV — Ss (amplificazione stratigrafica) e Cc (correzione periodo) by categoria sottosuolo."""
from strutture.shared.divergences import legacy
from strutture.shared.numeric import clamp

from .models import CategoriaSottosuolo

# Tabelle!E8 bug: the sheet clips Ss for categoria B to a lower bound of 0.40 instead of the
# NTC Tab. 3.2.IV value of 1.00 (categories C/D/E already use the correct bounds).
SS_CLIP_INFERIORE_CATEGORIA_B_SHEET = 0.40
SS_CLIP_INFERIORE_CATEGORIA_B_NTC = 1.00


def fattore_amplificazione_ss(
    categoria_sottosuolo: CategoriaSottosuolo, f0: float, ag_g: float, *, legacy_compat: bool = False
) -> float:
    """Ss, `Tabelle!D7:F11` col E (Tab. 3.2.IV)."""
    if categoria_sottosuolo == "A":
        return 1.0
    if categoria_sottosuolo == "B":
        low = (
            SS_CLIP_INFERIORE_CATEGORIA_B_SHEET
            if legacy("ntc-site-seismic/ss-categoria-b-limite-inferiore-basso", legacy_compat)
            else SS_CLIP_INFERIORE_CATEGORIA_B_NTC
        )
        return clamp(1.40 - 0.40 * f0 * ag_g, low, 1.20)
    if categoria_sottosuolo == "C":
        return clamp(1.70 - 0.60 * f0 * ag_g, 1.00, 1.50)
    if categoria_sottosuolo == "D":
        return clamp(2.40 - 1.50 * f0 * ag_g, 0.90, 1.80)
    if categoria_sottosuolo == "E":
        return clamp(2.00 - 1.10 * f0 * ag_g, 1.00, 1.60)
    raise ValueError(f"categoria sottosuolo sconosciuta: {categoria_sottosuolo!r}")


def coefficiente_correzione_cc(categoria_sottosuolo: CategoriaSottosuolo, tc_star_s: float) -> float:
    """Cc, `Tabelle!D7:F11` col F (Tab. 3.2.IV)."""
    if categoria_sottosuolo == "A":
        return 1.0
    if categoria_sottosuolo == "B":
        return 1.10 * tc_star_s**-0.20
    if categoria_sottosuolo == "C":
        return 1.05 * tc_star_s**-0.33
    if categoria_sottosuolo == "D":
        return 1.25 * tc_star_s**-0.50
    if categoria_sottosuolo == "E":
        return 1.15 * tc_star_s**-0.40
    raise ValueError(f"categoria sottosuolo sconosciuta: {categoria_sottosuolo!r}")
