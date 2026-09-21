"""Step 2 (spec §4.2): building classification by slenderness, cell B10."""
from strutture.shared.divergences import legacy

SLENDER_THRESHOLD = 5.0  # Circ. C3.3.8.1: h/d>5 excluded from the rectangular-plan cpe table

# `legacy_compat=True` reproduces the sheet's own ALL-CAPS cell B10 string exactly (oracle
# fixtures store it verbatim); `legacy_compat=False` uses a readable sentence-case phrase instead
# (design review: "EDIFICIO TOZZO"-style strings must be sentence case) — a presentation-only
# divergence, no numeric value changes either way.
EDIFICIO_TOZZO_LEGACY = "EDIFICIO TOZZO"
EDIFICIO_SNELLO_LEGACY = "EDIFICIO SNELLO"
EDIFICIO_SNELLO_DIR1_LEGACY = "EDIFICIO SNELLO DIR 1"
EDIFICIO_SNELLO_DIR2_LEGACY = "EDIFICIO SNELLO DIR 2"

EDIFICIO_TOZZO = "Edificio tozzo"
EDIFICIO_SNELLO = "Edificio snello"
EDIFICIO_SNELLO_DIR1 = "Edificio snello, direzione 1"
EDIFICIO_SNELLO_DIR2 = "Edificio snello, direzione 2"


def classify(hd_dir1: float, hd_dir2: float, *, legacy_compat: bool = False) -> str:
    """Squat/slender classification, matching sheet cell B10's nested IFs."""
    maiuscolo = legacy("vento-cpe/etichetta-classificazione-maiuscolo", legacy_compat)
    if hd_dir1 > SLENDER_THRESHOLD and hd_dir2 > SLENDER_THRESHOLD:
        return EDIFICIO_SNELLO_LEGACY if maiuscolo else EDIFICIO_SNELLO
    if hd_dir1 <= SLENDER_THRESHOLD and hd_dir2 <= SLENDER_THRESHOLD:
        return EDIFICIO_TOZZO_LEGACY if maiuscolo else EDIFICIO_TOZZO
    # vento-cpe/etichetta-classificazione-edificio-snello-mista: same maiuscolo/frase rewrite as
    # above, no separate branch (register entry has ramo="nessuno").
    if hd_dir1 > SLENDER_THRESHOLD:
        return EDIFICIO_SNELLO_DIR1_LEGACY if maiuscolo else EDIFICIO_SNELLO_DIR1
    return EDIFICIO_SNELLO_DIR2_LEGACY if maiuscolo else EDIFICIO_SNELLO_DIR2
