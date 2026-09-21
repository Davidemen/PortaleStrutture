"""Step (spec §4.1-2): province/region lookup and wind-zone determination, incl. the §7 legacy bug."""
from strutture.shared.comuni import AmbiguousComuneError, Comune, load_comuni, lookup_comune
from strutture.shared.divergences import legacy
from strutture.shared.report import CalcError
from strutture.shared.tables import KeyNotFound, exact_lookup


def _resolve_comune(comune: str, provincia: str | None) -> Comune:
    if not comune or not comune.strip():
        raise CalcError("Specificare un comune o una zona vento.")
    try:
        return lookup_comune(comune, provincia)
    except AmbiguousComuneError as error:
        raise CalcError(f"Comune '{comune}' omonimo in più province: specificare la provincia.") from error
    except KeyNotFound as error:
        raise CalcError(f"Comune '{comune}' non trovato nell'anagrafica comuni.") from error


def _zona_da_provincia_legacy(provincia: str) -> int:
    """Reproduce Vento!H7 = VLOOKUP(H5, Comuni!D:J, 3, FALSE): keyed on the *provincia* name against
    the *Comune* name column (spec §7 bug), instead of on the comune actually chosen by the user.
    Fails (like Excel's #N/A) whenever no comune shares the exact name of its own province.
    """
    tabella_comuni = tuple((c.comune, c.zona_vento) for c in load_comuni())
    try:
        return exact_lookup(tabella_comuni, provincia)
    except KeyNotFound as error:
        raise CalcError(
            f"Zona vento non determinabile: nessun comune chiamato come la provincia '{provincia}' "
            "(bug storico del foglio: Vento!H7 cerca il nome della provincia nella colonna Comune)."
        ) from error


def risolvi_zona(
    zona: int | None, comune: str | None, provincia: str | None, legacy_compat: bool
) -> tuple[int, Comune | None]:
    """Zona vento (1-9) and the resolved Comune (None when `zona` was given directly, spec §2 extension)."""
    if zona is not None:
        return zona, None
    resolved = _resolve_comune(comune or "", provincia)
    if legacy("vento/zona-lookup-su-provincia-invece-che-comune", legacy_compat):
        return _zona_da_provincia_legacy(resolved.provincia), resolved
    return resolved.zona_vento, resolved
