"""Step: envelope-level check for the optional bearing-capacity block (docs/architecture-phase4.md
§C): a single check on the overall governing row (worst N_Ed/R_d across every family and row),
emitted only when the "Terreno" block produced results (`capacita_portante.governante` set)."""
from strutture.shared.report import Check

from .capacita_portante import FAMIGLIE_SISMICHE, CapacitaPortanteOutput

CLAUSOLA = "NTC2018 §6.4.2.1, EN 1997-1 Annesso D"
NOME_CHECK = "Capacità portante (NTC2018 §6.4.2.1, EN 1997-1 Annesso D)"
# MEDIUM finding: le righe SLV_* sono calcolate con la formula STATICA dell'Annesso D sotto un
# gamma_R statico (`capacita_portante_riga.py` chiama sempre `sismico=False`, nessuna riduzione
# inerziale Paolucci-Pecker) — quando una di queste righe governa, il Check deve citarlo (clausola
# sismica) ed esporre l'esito come da confermare, non come un ordinario passato/non passato di
# §6.4.2.1 (il codice stesso dichiara la formula incompleta, l'esito non può presentarsi come
# definitivo).
CLAUSOLA_SISMICA = "NTC2018 §7.11.5.3.1 (formula statica dell'Annesso D, riduzione inerziale del terreno non implementata)"


def checks_capacita_portante(output: CapacitaPortanteOutput) -> tuple[Check, ...]:
    """`()` when the block was not filled (or ignored in legacy mode); one `Check` on the governing
    row otherwise."""
    riga = output.governante
    if riga is None:
        return ()
    sismica = riga.famiglia in FAMIGLIE_SISMICHE
    detail = f"{riga.combo} ({riga.famiglia})"
    if sismica:
        detail += " — esito da confermare: coefficienti sismici (Paolucci-Pecker) non applicati"
    return (Check(
        name=NOME_CHECK, passed=riga.ratio <= 1.0, clause=CLAUSOLA_SISMICA if sismica else CLAUSOLA,
        detail=detail, value=riga.n_ed_kn, limit=riga.r_d_kn, unit="kN",
    ),)
