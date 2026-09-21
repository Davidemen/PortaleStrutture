"""Grade lookup and partial-factor resolution (column-check!H11:H15; Materiali!H19:J23).

Known bug (docs/architecture.md §6, `acciaio column-check H12/H13`): the sheet's gammaM0/gammaM1
are free user inputs hardcoded to 1, disconnected from `Materiali!E4:E5`=1.05. Fixed behaviour
takes the EC3 defaults from `structural_steel.partial_factors()`, still overridable (with a
warning if the override differs from the standard value).

Also fixes `H15` (fuk divided by gammaM0 instead of gammaM2, docs/architecture.md §6 `acciaio H15`)
— that value is not read by any other formula in the sheet, so the fix has no effect on any check.
"""
from strutture.shared.materials.structural_steel import partial_factors
from strutture.shared.tables import exact_lookup

from .models import GradoAcciaioColonna
from .results import Materiali
from .tables import TABELLA_ACCIAIO_MPA


def _risolvi_gamma(valore_utente: float | None, standard: float, *, legacy_compat: bool) -> tuple[float, str | None]:
    """(gamma risolto, warning). Sheet default is 1 in legacy mode; EC3 default otherwise."""
    if legacy_compat:
        return (valore_utente if valore_utente is not None else 1.0), None
    if valore_utente is None:
        return standard, None
    if valore_utente != standard:
        return valore_utente, f"gamma sovrascritto manualmente a {valore_utente} (valore normativo EC3: {standard})"
    return valore_utente, None


def risolvi_materiale(
    grado: GradoAcciaioColonna,
    gamma_m0_input: float | None,
    gamma_m1_input: float | None,
    *,
    legacy_compat: bool,
) -> tuple[Materiali, tuple[str, ...]]:
    """Materiali (fyd/fud pre-divided as in the sheet's H14/H15) + any override warnings."""
    fyk_mpa, fuk_mpa = exact_lookup(TABELLA_ACCIAIO_MPA, grado)
    standard = partial_factors()
    gamma_m0, warning_m0 = _risolvi_gamma(gamma_m0_input, standard.gamma_m0, legacy_compat=legacy_compat)
    gamma_m1, warning_m1 = _risolvi_gamma(gamma_m1_input, standard.gamma_m1, legacy_compat=legacy_compat)
    fyd_mpa = fyk_mpa / gamma_m0
    fud_mpa = fuk_mpa / (gamma_m0 if legacy_compat else standard.gamma_m2)
    warnings = tuple(w for w in (warning_m0, warning_m1) if w is not None)
    materiali = Materiali(
        grado=grado,
        fyk_MPa=fyk_mpa,
        fuk_MPa=fuk_mpa,
        fyd_MPa=fyd_mpa,
        fud_MPa=fud_mpa,
        gamma_m0=gamma_m0,
        gamma_m1=gamma_m1,
        gamma_m2=standard.gamma_m2,
    )
    return materiali, warnings
