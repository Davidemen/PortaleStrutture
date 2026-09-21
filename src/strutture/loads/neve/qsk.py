"""Step (spec §3.4.2 / calc steps 4, `Neve!H10` & `Neve accumulo!H10`): ground snow load qsk."""
from strutture.shared.tables import exact_lookup

from .tables import (
    QSK_BRANCH_THRESHOLD_M,
    ZONA_TABELLE_KEY_TO_CANONICAL,
    ZONA_TABELLE_KEYS_LEGACY,
    ZONE_QSK1,
    ZONE_QSK2_PARAMS,
)


def _resolve_zona_row(zona: str, *, legacy_compat: bool) -> str:
    """Row of `Tabelle!A3:C6` actually selected for `zona`.

    Fixed mode: exact match on the normalized zona string (as designed).
    Legacy mode reproduces the sheet's `VLOOKUP(zona, Tabelle!A3:C6, ..., TRUE)` — an approximate
    (range) match, not exact — combined with Bug 5's stray paren on `Tabelle!A4`'s "I (mediterranea))":
    our normalized "I (mediterranea)" sorts *before* that typo'd key, so the nearest-lower match is
    the previous row, "I (alpina)", silently reusing its coefficients. Confirmed against the
    LibreOffice oracle (`tests/fixtures/neve_carico_falda_oracle.json`, case 2, Milano/400m).
    """
    if not legacy_compat:
        return zona
    candidates = [key for key in ZONA_TABELLE_KEYS_LEGACY if key <= zona]
    matched_key = candidates[-1] if candidates else ZONA_TABELLE_KEYS_LEGACY[0]
    return ZONA_TABELLE_KEY_TO_CANONICAL[matched_key]


def qsk1(zona: str) -> float:
    """Constant zonal value, `Tabelle!B3:B6`."""
    return exact_lookup(ZONE_QSK1, zona)


def qsk2(zona: str, altitude_m: float) -> float:
    """Altitude-dependent zonal formula, `Tabelle!C3:C6`."""
    coeff, denom_m = exact_lookup(ZONE_QSK2_PARAMS, zona)
    return coeff * (1 + (altitude_m / denom_m) ** 2)


def qsk_falda(zona: str, altitude_m: float, *, legacy_compat: bool = False) -> float:
    """`Neve!H10`: NTC2018 §3.4.2 — qsk1 (constant) applies for as <= 200 m, qsk2(as) (altitude
    formula) applies for as > 200 m; the zona-row selection quirk above still applies in legacy
    mode.

    Fixed mode applies the clause's boundary literally (`<=`/`>`), so as=200 m exactly takes the
    constant. Legacy mode reproduces `Neve!H10`'s own `IF(as<200, qsk1, qsk2)` formula
    byte-for-byte, which is strict on both sides, so as=200 m exactly falls through to the qsk2
    altitude formula instead — non-conservative in every zone at that single point (previously
    undetected boundary bug, distinct from `Neve accumulo!H10`'s Bug 3 branch inversion; see
    `docs/divergences/neve.md`).
    """
    row = _resolve_zona_row(zona, legacy_compat=legacy_compat)
    if legacy_compat:
        if altitude_m < QSK_BRANCH_THRESHOLD_M:
            return qsk1(row)
        return qsk2(row, altitude_m)
    if altitude_m <= QSK_BRANCH_THRESHOLD_M:
        return qsk1(row)
    return qsk2(row, altitude_m)


def qsk_accumulo(zona: str, altitude_m: float, *, legacy_compat: bool, neve_altitude_m: float | None) -> float:
    """`Neve accumulo!H10`.

    Fixed mode: same branch order as `qsk_falda`, using this tool's own altitude.
    Legacy mode reproduces two further compounded sheet bugs on top of the row-selection quirk
    above: the `<200` branch is inverted (Bug 3, `docs/specs/neve.md` §7.3) *and*, whenever the
    qsk2 formula fires, `Tabelle!C3:C6` hardcodes `Neve!$H$9` regardless of caller (Bug 1, §7.1) —
    so the altitude actually used is the *other* sheet's `as`, not this sheet's own, unless the
    caller supplies `neve_altitude_m`.
    """
    if not legacy_compat:
        return qsk_falda(zona, altitude_m)
    row = _resolve_zona_row(zona, legacy_compat=True)
    if altitude_m < QSK_BRANCH_THRESHOLD_M:
        contaminated_altitude_m = altitude_m if neve_altitude_m is None else neve_altitude_m
        return qsk2(row, contaminated_altitude_m)
    return qsk1(row)
