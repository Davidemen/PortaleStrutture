"""Step: envelope-level check for the optional bearing-capacity block (docs/architecture-phase4.md
§C): a single check on the overall governing row (worst N_Ed/R_d across every family and row),
emitted only when the "Terreno" block produced results (`capacita_portante.governante` set)."""
from strutture.shared.report import Check

from .capacita_portante import CapacitaPortanteOutput

CLAUSOLA = "NTC2018 §6.4.2.1, EN 1997-1 Annesso D"
NOME_CHECK = "Capacità portante (NTC2018 §6.4.2.1, EN 1997-1 Annesso D)"


def checks_capacita_portante(output: CapacitaPortanteOutput) -> tuple[Check, ...]:
    """`()` when the block was not filled (or ignored in legacy mode); one `Check` on the governing
    row otherwise."""
    riga = output.governante
    if riga is None:
        return ()
    return (Check(
        name=NOME_CHECK, passed=riga.ratio <= 1.0, clause=CLAUSOLA,
        detail=f"{riga.combo} ({riga.famiglia})", value=riga.n_ed_kn, limit=riga.r_d_kn, unit="kN",
    ),)
