"""Verified restatement (docs/architecture-phase2.md §6, wave-3 adoption) of the ground snow load
q_sk (`qsk.py::qsk_falda`, NTC2018 §3.4.2 Tab. 3.4.I) and the exposure coefficient C_E
(`esposizione.py::coefficiente_esposizione`, NTC2018 §3.4.3 Tab. 3.4.I). Both `neve-carico-falda`
and `neve-accumulo` compute these two values with the SAME functions on their own site data
(`tool.py::run_carico_falda`/`run_accumulo`), so one `Traccia` builder is shared by both tools'
`relazione.py`. The calculation code is never touched.

`legacy_compat` is always False here (docs/architecture-phase2.md §1: `relazione` only ever
describes the code-standard branch), so `qsk.qsk_falda`'s own `_resolve_zona_row` reduces to the
identity on `zona` (`legacy(...)` is False) — the zonal table row below is looked up directly on
`zona`, without going through that private helper.
"""
from strutture.shared.relazione import Passo, Traccia, Valore
from strutture.shared.tables import exact_lookup

from .tables import QSK_BRANCH_THRESHOLD_M, ZONE_QSK1, ZONE_QSK2_PARAMS

CLAUSOLA_QSK = "NTC2018 §3.4.2 Tab. 3.4.I"
CLAUSOLA_CE = "NTC2018 §3.4.3 Tab. 3.4.I"
CLAUSOLA_CT = "NTC2018 §3.4.4"


def traccia_carico_al_suolo(
    *, zona: str, altitude_m: float, qsk_val: float, topografia: str, ce_val: float, ct_val: float, titolo: str
) -> Traccia:
    """3 passi: q_sk (costante o formula in quota, secondo la soglia di §3.4.2), C_E (lookup) e
    C_t (dato di ingresso, ripreso dalle formule del carico di progetto)."""
    return Traccia(
        titolo=titolo,
        passi=(_passo_qsk(zona, altitude_m, qsk_val), _passo_ce(topografia, ce_val), _passo_ct(ct_val)),
    )


def _passo_qsk(zona: str, altitude_m: float, qsk_val: float) -> Passo:
    if altitude_m <= QSK_BRANCH_THRESHOLD_M:
        valore_costante = exact_lookup(ZONE_QSK1, zona)
        return Passo(
            simbolo="q_sk",
            formula="q_sk,cost",
            valori=(
                Valore(
                    simbolo="q_sk,cost", valore=valore_costante, unita="kN/m²",
                    descrizione=f"valore costante della zona {zona}, Tab. 3.4.I",
                ),
            ),
            risultato=qsk_val, unita="kN/m²", clausola=CLAUSOLA_QSK,
            nota=f"Zona neve {zona}: fino a {QSK_BRANCH_THRESHOLD_M:g} m di quota il carico al suolo "
                 "è il valore costante tabellare.",
        )
    coeff, denom_m = exact_lookup(ZONE_QSK2_PARAMS, zona)
    return Passo(
        simbolo="q_sk",
        formula="C_qsk * (1 + (a_s / a_qsk)^2)",
        valori=(
            Valore(simbolo="C_qsk", valore=coeff, unita="kN/m²", descrizione=f"coefficiente della zona {zona}, Tab. 3.4.I"),
            Valore(simbolo="a_s", valore=altitude_m, unita="m", descrizione="altitudine del sito"),
            Valore(simbolo="a_qsk", valore=denom_m, unita="m", descrizione=f"quota di riferimento della zona {zona}, Tab. 3.4.I"),
        ),
        risultato=qsk_val, unita="kN/m²", clausola=CLAUSOLA_QSK,
        nota=f"Zona neve {zona}: sopra {QSK_BRANCH_THRESHOLD_M:g} m di quota il carico al suolo segue "
             "la formula in funzione dell'altitudine.",
    )


def _passo_ce(topografia: str, ce_val: float) -> Passo:
    return Passo(
        simbolo="C_E",
        formula="C_E",
        valori=(Valore(simbolo="C_E", valore=ce_val, descrizione=f"classe di esposizione «{topografia}»"),),
        risultato=ce_val, unita="-", clausola=CLAUSOLA_CE,
        nota="Valore da tabella in base alla classe di esposizione topografica del sito.",
    )


def _passo_ct(ct_val: float) -> Passo:
    return Passo(
        simbolo="C_t",
        formula="C_t",
        valori=(Valore(simbolo="C_t", valore=ct_val, descrizione="dato di ingresso, default 1"),),
        risultato=ct_val, unita="-", clausola=CLAUSOLA_CT,
        nota="Coefficiente termico: riduce il carico neve per coperture ad alta dispersione termica.",
    )
