"""Section title/subtitle pairs shared by `ca-sle-limitazione-tensioni` and
`ca-apertura-fessure-semplificata`: both iterate the same three sections, and the SEMP sheet
literally cross-references `Limitazione delle tensioni`!B11/B19/B27 (title) and !B12/B20/B28
(subtitle) for these labels (see spec Tool 3 "Outputs" and "Suspected bugs").

`B12` and `B28` are blank cells in the source sheet; the SEMP sheet's `=+'Limitazione delle
tensioni'!B12` (and `!B28`) formulas render Excel's blank-cell coercion to `0` instead of an
empty string. Fixed here as `""` — see `docs/divergences/ca-fessurazione.md`.
"""

SEZIONI: tuple[tuple[str, str], ...] = (
    ("Sezione h = 30 cm", ""),  # 'Limitazione delle tensioni' B11/B12
    ("Sezione h = 30 cm", "Zona centrale"),  # B19/B20
    ("Sezione h = 20 cm", ""),  # B27/B28
)
