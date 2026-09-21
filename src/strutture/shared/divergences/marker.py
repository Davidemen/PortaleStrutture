"""Code marker linking a legacy branch to its register entry.

    if legacy("ca-pilastri/lambda-lim-unita", legacy_compat):
        ... spreadsheet behaviour ...
    else:
        ... code-standard behaviour ...

It returns the flag unchanged; its value is the greppable, testable link: a test collects every
string literal passed to `legacy(` and compares it with the register in both directions."""


def legacy(divergence_id: str, legacy_compat: bool) -> bool:
    """True when the spreadsheet behaviour of `divergence_id` must be reproduced."""
    return legacy_compat
