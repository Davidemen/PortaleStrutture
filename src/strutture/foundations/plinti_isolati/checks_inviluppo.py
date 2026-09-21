"""Step: envelope-level checks — bearing (vs the per-famiglia design resistance), sliding and
overturning (docs/architecture-batch2.md §2: "checks are emitted on the envelope only"). Compressed
-base ratio is reported in `righe`/`inviluppo` but not checked here: the sheet defines no numeric
pass/fail threshold for it (docs/specs/fond-plinti-isolati.md §"PASS/FAIL" note, "Da verificare").

Fix 1 (MEDIUM, review finding): the bearing check only compares sigma_max against a user-entered
`sigma_ammissibile` (allowable stress) — no qlim/Meyerhof effective-area/gammaR=2.3 bearing-capacity
calculation exists in this package (no shared bearing-capacity module to reuse either), so it must
not carry the NTC2018 §6.4.2.1 limit-state clause: `BEARING_CLAUSE` replaces it with an honest label
in both modes (a text-only change, no numeric divergence to record).

Fix 2 (HIGH, review finding gamma_azioni.py): overturning is an EQU-type verification (NTC2018
Tab. 2.6.I requires gammaG1=0.9 on the stabilising self-weight); `azioni_base`'s N already applies
gammaW=1.35 for `SLU_STR` (`gamma_azioni.GAMMA_STR`), inflating Mstab by 50% relative to the code
value, so a `SLU_STR` overturning check would be non-conservative. `legacy_compat=False` restricts
the overturning check to the families whose gammaW is the correct EQU-type value (`SLU_EQU`: 0.9;
`SLV_EQU`: 1.0, correct per NTC2018 §2.5.3 seismic combos - see gamma_azioni.py); `legacy_compat=True`
keeps emitting it for every family (sheet behaviour)."""
from strutture.shared.load_table import Famiglia
from strutture.shared.report import Check

from .inviluppo import InviluppoRiga
from .legacy_units import sigma_ammissibile_kpa
from .rows import ResistenzaRow

SAFETY_RATIO_LIMIT = 1.0
BEARING_CLAUSE = "Confronto con la resistenza ammissibile (non è una verifica NTC2018 §6.4.2.1 completa)"
OVERTURNING_CLAUSE = "NTC2018 §6.4.3.1"
EQU_FAMIGLIE: tuple[Famiglia, ...] = ("SLU_EQU", "SLV_EQU")  # gammaW corretto per l'azione stabilizzante (EQU).


def checks_inviluppo(inviluppo: tuple[InviluppoRiga, ...], resistenze: tuple[ResistenzaRow, ...], *,
                      sistema_unita: str, legacy_compat: bool) -> tuple[Check, ...]:
    """Bearing, sliding and overturning (X/Y) checks, one per `famiglia` present in the envelope."""
    resistenza_per_famiglia: dict[Famiglia, float] = {
        row.famiglia: sigma_ammissibile_kpa(row.sigma_ammissibile, sistema_unita=sistema_unita, legacy_compat=legacy_compat)
        for row in resistenze
    }
    result: tuple[Check, ...] = ()
    for riga in inviluppo:
        if riga.famiglia is None:
            continue
        if riga.grandezza == "pressione_max_kpa":
            limite = resistenza_per_famiglia.get(riga.famiglia)
            if limite is None:
                continue
            result = (*result, Check(
                name=f"Portanza ({riga.famiglia})", passed=riga.valore <= limite, clause=BEARING_CLAUSE,
                detail=riga.combo, value=riga.valore, limit=limite, unit="kPa"))
        elif riga.grandezza == "scorrimento_min":
            result = (*result, _check_sicurezza(f"Scorrimento ({riga.famiglia})", riga, OVERTURNING_CLAUSE))
        elif riga.grandezza in ("ribaltamento_x_min", "ribaltamento_y_min"):
            if not legacy_compat and riga.famiglia not in EQU_FAMIGLIE:
                continue
            direzione = "X" if riga.grandezza == "ribaltamento_x_min" else "Y"
            result = (*result, _check_sicurezza(f"Ribaltamento {direzione} ({riga.famiglia})", riga, OVERTURNING_CLAUSE))
    return result


def _check_sicurezza(name: str, riga: InviluppoRiga, clause: str) -> Check:
    return Check(name=name, passed=riga.valore >= SAFETY_RATIO_LIMIT, clause=clause, detail=riga.combo,
                 value=riga.valore, limit=SAFETY_RATIO_LIMIT, unit="-")
