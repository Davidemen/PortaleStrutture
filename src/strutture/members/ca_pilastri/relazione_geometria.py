"""Verified restatement (docs/architecture-phase2.md) of `geometria.py` (`sezione_rettangolare`/
`sezione_circolare`, `eccentricita_minima`): concrete area A_c, steel area A_s and the governing
design moment M_Ed (envelope of the applied moment and the minimum-eccentricity moment). `A_c` and
`A_s` are reused by later Tracce (armatura, compressione, snellezza) exactly as computed here — d
and z's own promotion in `ca_travi` is mirrored by giving these their own steps rather than folding
them into a later formula."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .geometria import MIN_ECCENTRICITY_MM, MIN_ECCENTRICITY_RATIO
from .models import PilastroCircolareInput, PilastroOutput, PilastroRettangolareInput

MM_PER_M = 1000.0  # strutture.shared.units.mm_to_m


def traccia_geometria_rettangolare(inputs: PilastroRettangolareInput, output: PilastroOutput) -> Traccia:
    """4 passi: A_c, A_s, e_min, M_Ed (calcolo)."""
    geometria = output.geometria
    passo_ac = Passo(
        simbolo="A_c", formula="L_1 * L_2",
        valori=(
            Valore(simbolo="L_1", valore=inputs.l1_mm, unita="mm", descrizione="lato 1 del pilastro (base)"),
            Valore(simbolo="L_2", valore=inputs.l2_mm, unita="mm", descrizione="lato 2 del pilastro (altezza)"),
        ),
        risultato=geometria.ac_mm2, unita="mm2", nota="Area della sezione di calcestruzzo.",
    )
    passo_as = _passo_as(inputs, output)
    l_max = max(inputs.l1_mm, inputs.l2_mm)
    passo_med = _passo_med(inputs, output, dimensione_max_mm=l_max, dimensione_descrizione="dimensione maggiore della sezione, max(L_1, L_2)")
    return Traccia(titolo="Geometria della sezione", passi=(passo_ac, passo_as, passo_med))


def traccia_geometria_circolare(inputs: PilastroCircolareInput, output: PilastroOutput) -> Traccia:
    """5 passi: A_c, A_s, l_eq (lato equivalente), e_min, M_Ed (calcolo)."""
    geometria = output.geometria
    passo_ac = Passo(
        simbolo="A_c", formula="π * D^2 / 4",
        valori=(
            Valore(simbolo="π", valore=3.141592653589793),
            Valore(simbolo="D", valore=inputs.d_mm, unita="mm", descrizione="diametro del pilastro"),
        ),
        risultato=geometria.ac_mm2, unita="mm2", nota="Area della sezione di calcestruzzo.",
    )
    passo_as = _passo_as(inputs, output)
    passo_leq = Passo(
        simbolo="l_eq", formula="sqrt(A_c)",
        valori=(Valore(simbolo="A_c", valore=geometria.ac_mm2, unita="mm2"),),
        risultato=geometria.lato_equivalente_mm, unita="mm",
        nota="Lato del quadrato equivalente all'area della sezione circolare: sostituisce L_1/L_2 nelle "
             "formule di leva interna, taglio e confinamento (docs/specs/ca-pilastri.md).",
    )
    passo_med = _passo_med(inputs, output, dimensione_max_mm=inputs.d_mm, dimensione_descrizione="diametro del pilastro")
    return Traccia(titolo="Geometria della sezione", passi=(passo_ac, passo_as, passo_leq, passo_med))


def _passo_as(inputs: PilastroRettangolareInput | PilastroCircolareInput, output: PilastroOutput) -> Passo:
    """`φ` (not the grammar-illegal UI symbol `⌀`, docs/architecture-phase2.md §2) stands for the
    longitudinal bar diameter, `diametro_ferri_mm` in input — mirrors `ca_travi.relazione_geometria`."""
    return Passo(
        simbolo="A_s", formula="n_ferri * π * φ^2 / 4",
        valori=(
            Valore(simbolo="n_ferri", valore=float(inputs.n_ferri), descrizione="numero totale di ferri longitudinali"),
            Valore(simbolo="π", valore=3.141592653589793),
            Valore(simbolo="φ", valore=inputs.diametro_ferri_mm, unita="mm", descrizione="diametro dei ferri longitudinali (⌀ in input)"),
        ),
        risultato=output.geometria.as_mm2, unita="mm2", nota="Area di armatura longitudinale presente.",
    )


def _passo_med(
    inputs: PilastroRettangolareInput | PilastroCircolareInput, output: PilastroOutput, *,
    dimensione_max_mm: float, dimensione_descrizione: str,
) -> Passo:
    geometria = output.geometria
    e_min_mm = max(MIN_ECCENTRICITY_MM, MIN_ECCENTRICITY_RATIO * dimensione_max_mm)
    return Passo(
        simbolo="M_Ed", formula=f"max(N_Ed * e_min / {MM_PER_M:g}, M_Ed,appl)",
        valori=(
            Valore(simbolo="N_Ed", valore=inputs.ned_kN, unita="kN", descrizione="azione assiale di calcolo"),
            Valore(
                simbolo="e_min", valore=e_min_mm, unita="mm",
                descrizione=f"eccentricità minima, max(20 mm; 5% × {dimensione_descrizione})",
            ),
            Valore(simbolo="M_Ed,appl", valore=inputs.med_kNm, unita="kNm", descrizione="momento flettente di calcolo agente, dato di ingresso"),
        ),
        risultato=geometria.med_calc_kNm, unita="kNm",
        nota="Momento di calcolo: il maggiore fra il momento agente e quello indotto dall'eccentricità minima "
             "(imperfezioni geometriche/accidentali).",
    )
