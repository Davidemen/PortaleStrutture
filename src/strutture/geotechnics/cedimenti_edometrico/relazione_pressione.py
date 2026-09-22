"""Verified restatement (docs/architecture-phase2.md) of `carico.pressione_netta` (Step 2) — net
design pressure q' = q − γ·D, the pressure the oedometric increment is spread from. Standard mode
only (this module is never called with `legacy_compat=True`, see
`strutture.shared.tool._con_relazione`), so the water-table-aware branch of
`strutture.shared.soil_layers.effective_overburden` always applies, mirroring `carico.py` exactly
(`legacy=False` there is the same call this module restates).

NTC2018 §6.2.2 ("Verifiche della sicurezza e delle prestazioni") / Circolare 2019 C6.2.2 prescribe
WHICH checks must be performed (that SLE settlements are checked), not the net-pressure convention
printed here (a classical geotechnical definition, q minus the removed overburden γ·D): citing that
clause on this formula would dress an empirical convention as a code equation (review finding
WRONG_CLAUSE, same lesson `relazione_cedimento.py` applies to Δσ/ΔH) — this `Passo` carries no
`clausola` rather than a borrowed one.

The trace reads dimensional inputs (B, L, D, γ, Zw) through the package's own `ingresso.converti_in_si`
(the input model stores them in whichever `sistema_unita` the engineer chose, not always SI — an
intermediate not exposed by `EdometricoOutput`, so it is read straight from the package's own step
function, exactly as the architecture brief allows)."""
from strutture.shared.relazione import Passo, Traccia, Valore
from strutture.shared.soil_layers import GAMMA_WATER_KN_M3

from .ingresso import IngressoSI, converti_in_si
from .models import EdometricoInput
from .output import EdometricoOutput


def traccia_pressione(inputs: EdometricoInput, output: EdometricoOutput) -> Traccia:
    """1 passo: pressione netta di progetto q'."""
    si = converti_in_si(inputs)
    return Traccia(titolo="Pressione netta di progetto", passi=(_passo_q_prime(output, si),))


def _passo_q_prime(output: EdometricoOutput, si: IngressoSI) -> Passo:
    carico = output.carico
    falda_sopra_il_piano_di_posa = si.falda_m is not None and si.falda_m < si.d_m
    if falda_sopra_il_piano_di_posa:
        formula = f"q - (γ * Zw + (γ - {GAMMA_WATER_KN_M3:g}) * (D - Zw))"
        valori = (
            Valore(simbolo="q", valore=carico.q_kPa, unita="kPa", descrizione="pressione di contatto applicata"),
            Valore(simbolo="γ", valore=si.gamma_kN_m3, unita="kN/m³", descrizione="peso di volume del terreno"),
            Valore(simbolo="Zw", valore=si.falda_m, unita="m", descrizione="profondità della falda dal piano campagna"),
            Valore(simbolo="D", valore=si.d_m, unita="m", descrizione="profondità di infissione/sbancamento"),
        )
        nota = (
            "Falda al di sopra del piano di posa: il sovraccarico rimosso usa il peso di volume "
            "alleggerito γ−γw sotto falda (γw=9,80665 kN/m³)."
        )
    else:
        formula = "q - γ * D"
        valori = (
            Valore(simbolo="q", valore=carico.q_kPa, unita="kPa", descrizione="pressione di contatto applicata"),
            Valore(simbolo="γ", valore=si.gamma_kN_m3, unita="kN/m³", descrizione="peso di volume del terreno"),
            Valore(simbolo="D", valore=si.d_m, unita="m", descrizione="profondità di infissione/sbancamento"),
        )
        nota = "Terreno asciutto fino al piano di posa (o falda assente): il sovraccarico rimosso usa il peso di volume totale γ."
    return Passo(
        simbolo="q'", formula=formula, valori=valori,
        risultato=carico.q_prime_kPa, unita="kPa",
        nota=f"Pressione netta di progetto, al netto del sovraccarico rimosso dallo scavo/infissione (γ·D={carico.sovraccarico_rimosso_kPa:.4g} kPa). {nota}",
    )
