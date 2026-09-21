"""Step (spec calc steps 1-3): resolve provincia/regione/zona neve from a comune name.

Both `neve-carico-falda` and (in fixed mode) `neve-accumulo` key this lookup on the comune name
(`Comuni!D`), matching `Neve!H6/H7/H8`'s `VLOOKUP(comune, Comuni!D:J, ...)`. `neve-accumulo`'s
legacy mode instead reproduces `Neve accumulo!H8`'s Bug 2: `VLOOKUP(provincia, Comuni!D:J, 4, ...)`
looks the *provincia* string up inside the *comune* column.
"""
from strutture.shared.comuni import AmbiguousComuneError, Comune, KeyNotFound, lookup_comune


def resolve_comune(comune: str) -> Comune:
    """`Neve!H6/H7/H8`: exact VLOOKUP on the comune name."""
    return lookup_comune(comune)


def zona_from_provincia_bug(provincia: str) -> str:
    """`Neve accumulo!H8` in legacy mode (Bug 2): re-uses the *provincia* string (already resolved
    from the comune, as the sheet's own `H6` does) as the VLOOKUP key into the *comune* column —
    only coincidentally correct when the provincia's name equals a comune's name. Raises
    `KeyNotFound` (mapped to `CalcError` by the tool) otherwise, mirroring the sheet's `#N/A`.
    """
    try:
        return lookup_comune(provincia).zona_neve
    except (KeyNotFound, AmbiguousComuneError) as error:
        raise KeyNotFound(f"Bug di VLOOKUP su provincia (legacy): {provincia!r} non è un comune valido") from error
