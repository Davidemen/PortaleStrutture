"""Step: the single check on the envelope (docs/BUILD_CONTRACT.md "Batch 2": "checks on the envelope
only"), evaluated on the governing row. `N_Ed` outside the section's resistance domain (`rapporto`
undefined, see `capacita.py`/`interpolazione.py`) is reported as a FAILED check with an explicit
Italian detail explaining why — never a crash, never a silently clamped ratio."""
from strutture.shared.report import Check

from .models_output import RigaAzione

CLAUSOLA_PRESSOFLESSIONE = "NTC2018 §4.1.2.3.4.2"


def _dettaglio(governante: RigaAzione) -> str:
    if governante.rapporto is None:
        return (
            f"Combinazione governante '{governante.nome}': N_Ed = {governante.n_ed_kN:.1f} kN è fuori dal "
            "campo di resistenza assiale della sezione (compressione o trazione eccessiva)."
        )
    return f"Combinazione governante '{governante.nome}'."


def check_pressoflessione(governante: RigaAzione) -> Check:
    return Check(
        name="Verifica a pressoflessione", passed=governante.dentro, clause=CLAUSOLA_PRESSOFLESSIONE,
        detail=_dettaglio(governante), value=governante.rapporto, limit=1.0, unit="-",
    )
