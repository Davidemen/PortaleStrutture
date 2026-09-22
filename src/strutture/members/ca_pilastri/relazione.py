"""Verified restatement of the `ca-pilastro-rettangolare` / `ca-pilastro-circolare` formulas for
"Sviluppo dei calcoli" (docs/architecture-phase2.md §6, wave 2 adoption). Pure functions of each
tool's own validated inputs and already-computed output; the calculation code of this package is
never touched — see each `relazione_*.py` module's own docstring for which package module it
restates and which intermediate (not exposed by `PilastroOutput`) it reads straight from the
package's own step functions.

Both tools share ~80% of their trace (materials, armatura, pressoflessione, compressione, taglio,
gerarchia, confinamento) — the same split `tool_rettangolare.py`/`tool_circolare.py` already use for
the calculation itself — and differ only where the section shape does: geometry (A_c/A_s/l_eq),
which dimension feeds the shear/confinement "larghezza", and the radius of gyration formula for
snellezza. `relazione` only ever runs with `legacy_compat=False` (`strutture.shared.tool.
_con_relazione`), so it restates the code-standard branch of each `RuleSet` (`regole.py`) for
whichever `norma` the caller selected — NTC2018 or EC2 (NTC2008 has no code-standard branch,
`regole.resolve`, and therefore no trace: `execute(..., con_relazione=True)` never reaches a
`relazione` call for it, since the run itself fails with `CalcError` first)."""
from strutture.shared.relazione import Traccia

from .models import PilastroCircolareInput, PilastroOutput, PilastroRettangolareInput
from .relazione_armatura import traccia_limiti_armatura
from .relazione_dettagli import traccia_confinamento, traccia_dettagli_circolare, traccia_dettagli_rettangolare
from .relazione_flessione_compressione import traccia_compressione, traccia_pressoflessione
from .relazione_geometria import traccia_geometria_circolare, traccia_geometria_rettangolare
from .relazione_materiali import traccia_materiali
from .relazione_snellezza import traccia_snellezza_circolare, traccia_snellezza_rettangolare
from .relazione_taglio import traccia_gerarchia, traccia_taglio


def relazione_rettangolare(inputs: PilastroRettangolareInput, output: PilastroOutput) -> tuple[Traccia, ...]:
    dimensione_min_mm = min(inputs.l1_mm, inputs.l2_mm)
    return (
        traccia_materiali(inputs, output),
        traccia_geometria_rettangolare(inputs, output),
        traccia_limiti_armatura(inputs, output),
        traccia_pressoflessione(inputs, output),
        traccia_compressione(inputs, output),
        traccia_taglio(
            inputs, output,
            larghezza_mm=inputs.l1_mm, larghezza_simbolo="L_1", larghezza_descrizione="lato 1 del pilastro (base)",
            altezza_mm=inputs.l2_mm, altezza_simbolo="L_2", altezza_descrizione="lato 2 del pilastro (altezza)",
        ),
        traccia_gerarchia(inputs, output),
        traccia_confinamento(inputs, output, dimensione_confinata_mm=dimensione_min_mm),
        traccia_dettagli_rettangolare(inputs, output),
        traccia_snellezza_rettangolare(inputs, output),
    )


def relazione_circolare(inputs: PilastroCircolareInput, output: PilastroOutput) -> tuple[Traccia, ...]:
    lato_equivalente_mm = output.geometria.lato_equivalente_mm
    return (
        traccia_materiali(inputs, output),
        traccia_geometria_circolare(inputs, output),
        traccia_limiti_armatura(inputs, output),
        traccia_pressoflessione(inputs, output),
        traccia_compressione(inputs, output),
        traccia_taglio(
            inputs, output,
            larghezza_mm=lato_equivalente_mm, larghezza_simbolo="l_eq", larghezza_descrizione="lato del quadrato equivalente",
            altezza_mm=lato_equivalente_mm, altezza_simbolo="l_eq", altezza_descrizione="lato del quadrato equivalente",
        ),
        traccia_gerarchia(inputs, output),
        traccia_confinamento(inputs, output, dimensione_confinata_mm=lato_equivalente_mm),
        traccia_dettagli_circolare(inputs, output),
        traccia_snellezza_circolare(inputs, output),
    )
