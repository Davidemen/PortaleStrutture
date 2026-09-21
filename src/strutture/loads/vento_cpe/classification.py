"""Step 2 (spec §4.2): building classification by slenderness, cell B10."""

SLENDER_THRESHOLD = 5.0  # Circ. C3.3.8.1: h/d>5 excluded from the rectangular-plan cpe table

EDIFICIO_TOZZO = "EDIFICIO TOZZO"
EDIFICIO_SNELLO = "EDIFICIO SNELLO"
EDIFICIO_SNELLO_DIR1 = "EDIFICIO SNELLO DIR 1"
EDIFICIO_SNELLO_DIR2 = "EDIFICIO SNELLO DIR 2"


def classify(hd_dir1: float, hd_dir2: float) -> str:
    """Squat/slender classification, matching sheet cell B10's nested IFs."""
    if hd_dir1 > SLENDER_THRESHOLD and hd_dir2 > SLENDER_THRESHOLD:
        return EDIFICIO_SNELLO
    if hd_dir1 <= SLENDER_THRESHOLD and hd_dir2 <= SLENDER_THRESHOLD:
        return EDIFICIO_TOZZO
    if hd_dir1 > SLENDER_THRESHOLD:
        return EDIFICIO_SNELLO_DIR1
    return EDIFICIO_SNELLO_DIR2
