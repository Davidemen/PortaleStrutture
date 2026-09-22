"""Verified restatement (docs/architecture-phase2.md) of `flessione.py` (bending utilisation against
the user-supplied M_Rd, no M-N interaction domain — `models.py` module docstring) and
`compressione.py` (pure concrete axial capacity, NTC2018 §4.1.2.1.2).

Both highlighted outputs (`FlessioneResult.tasso_sfruttamento_pct`, `CompressioneResult.
tasso_sfruttamento_pct`) are rounded to 2 decimal places by `flessione.tasso_sfruttamento_pct`
(`round(domanda/capacita*100.0, 2)`) — `round` is not in the notation grammar's function whitelist
(docs/architecture-phase2.md §2), so the displayed percentage cannot be re-derived algebraically
inside the harness's 1e-6 tolerance from the unrounded ratio. It is therefore cited directly as a
single named `Valore` ("tasso", already computed above from the demand/capacity shown in the
preceding steps), the same way `ca_travi.relazione_sle` cites a table lookup the grammar cannot
restate — the comparison itself (`tasso <= 100`) is still fully verified by the harness."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import PilastroCircolareInput, PilastroOutput, PilastroRettangolareInput

PilastroInput = PilastroRettangolareInput | PilastroCircolareInput


def traccia_pressoflessione(inputs: PilastroInput, output: PilastroOutput) -> Traccia:
    """2 passi: η = M_Ed/M_Rd (con la sostituzione reale e la provenienza di M_Rd dichiarata) e il
    Check "Resistenza a pressoflessione" in percentuale (Check "Resistenza a pressoflessione"). M_Rd
    è un dato di ingresso (non esiste un dominio di interazione M-N nel foglio, vedi `models.py`);
    M_Ed è già stato derivato nella Traccia "Geometria della sezione".

    Review finding (MISLEADING): il solo passo percentuale, con `tasso` citato come `Valore` opaco
    (necessario perché `tasso_sfruttamento_pct` arrotonda a 2 cifre decimali, non ricostruibile
    algebricamente entro la tolleranza dell'harness — vedi il docstring del modulo), non mostrava
    MAI la sostituzione reale M_Ed/M_Rd né dichiarava M_Rd come dato di ingresso in questa Traccia:
    il passo η qui sotto copre entrambi i difetti."""
    flessione = output.flessione
    passo_eta = Passo(
        simbolo="η", formula="M_Ed / M_Rd",
        valori=(
            Valore(simbolo="M_Ed", valore=flessione.med_kNm, unita="kNm", descrizione="momento di calcolo, derivato nella Traccia \"Geometria della sezione\""),
            Valore(simbolo="M_Rd", valore=flessione.mrd_kNm, unita="kNm", descrizione="momento resistente della sezione, dato di ingresso (nessun dominio M-N nel foglio)"),
        ),
        risultato=flessione.med_kNm / flessione.mrd_kNm, unita="-", clausola="NTC2018 §4.1.2.1.2",
        nota="Rapporto di utilizzo a pressoflessione.",
    )
    tasso = flessione.tasso_sfruttamento_pct
    soddisfatta = tasso <= 100.0
    passo_check = Passo(
        simbolo="M_Ed/M_Rd", formula="tasso <= 100",
        valori=(
            Valore(simbolo="tasso", valore=tasso, unita="%",
                   descrizione="η (passo sopra) × 100, arrotondato a 2 cifre decimali"),
        ),
        risultato=tasso, unita="%", clausola="NTC2018 §4.1.2.1.2",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Tasso di sfruttamento a pressoflessione, stessa quantità di η sopra espressa in percentuale.",
    )
    return Traccia(titolo="Resistenza a pressoflessione", passi=(passo_eta, passo_check))


def traccia_compressione(inputs: PilastroInput, output: PilastroOutput) -> Traccia:
    """3 passi: N_Rcd (resistenza a compressione della sola sezione di calcestruzzo), η_N =
    N_Ed/N_Rcd (sostituzione reale, review finding MISLEADING — stesso difetto della
    pressoflessione, vedi `traccia_pressoflessione`) e N_Ed/N_Rcd (Check "Resistenza a
    compressione") in percentuale."""
    compressione = output.compressione
    passo_nrcd = Passo(
        simbolo="N_Rcd", formula="A_c * f_cd", scala=1e-3,
        valori=(
            Valore(simbolo="A_c", valore=output.geometria.ac_mm2, unita="mm2"),
            Valore(simbolo="f_cd", valore=output.materiali.fcd_MPa, unita="MPa"),
        ),
        risultato=compressione.nrcd_kN, unita="kN", clausola="NTC2018 §4.1.2.1.2",
        nota="Resistenza a compressione della sola sezione di calcestruzzo (nessun contributo dell'armatura).",
    )
    passo_eta = Passo(
        simbolo="η_N", formula="N_Ed / N_Rcd",
        valori=(
            Valore(simbolo="N_Ed", valore=inputs.ned_kN, unita="kN", descrizione="azione assiale di calcolo, dato di ingresso"),
            Valore(simbolo="N_Rcd", valore=compressione.nrcd_kN, unita="kN", descrizione="resistenza a compressione, calcolata sopra"),
        ),
        risultato=inputs.ned_kN / compressione.nrcd_kN, unita="-", clausola="NTC2018 §4.1.2.1.2",
        nota="Rapporto di utilizzo a compressione semplice.",
    )
    tasso = compressione.tasso_sfruttamento_pct
    soddisfatta = tasso <= 100.0
    passo_check = Passo(
        simbolo="N_Ed/N_Rcd", formula="tasso <= 100",
        valori=(
            Valore(simbolo="tasso", valore=tasso, unita="%",
                   descrizione="η_N (passo sopra) × 100, arrotondato a 2 cifre decimali"),
        ),
        risultato=tasso, unita="%", clausola="NTC2018 §4.1.2.1.2",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Tasso di sfruttamento a compressione semplice, stessa quantità di η_N sopra espressa in percentuale.",
    )
    return Traccia(titolo="Resistenza a compressione", passi=(passo_nrcd, passo_eta, passo_check))
