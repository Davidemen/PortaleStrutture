"""Verified restatement of the utilisation of the GOVERNING `azioni` row only, per
docs/architecture-phase2.md §6 ("the domain itself is a chart, not a trace"; "trace the GOVERNING
row only and say so in the Traccia title"). `M_Rd+`/`M_Rd-` at `N = N_Ed` are the section's exact
equilibrium solve (`shared.sezione_ca.domini.m_rd`, one bisection each — `compose.py`'s own
`riga_azione_esatta`, never the cheap domain interpolation used for the other rows): no closed
form to restate, so each bound is a bare-identifier lookup `Passo` per §6's lookup rule, with a
`nota` naming the resolution method. Identifiers use `,pos`/`,neg` (the grammar's subscript allows
letters/digits/`,`/`'`, not `+`/`-`, docs/architecture-phase2.md §2); `Passo.simbolo` (free text,
never parsed — the same trick `ca_travi/relazione_taglio.py` uses for "cotg θ") keeps the nicer
`M_Rd,x+`/`M_Rd,x-` for display. The utilisation `η` itself restates `rapporto.py` exactly, branch
for branch (`TipoPressoflessione`): uniaxial (NTC2018 §4.1.2.3.4.2, `shared.sezione_ca.verifica.
rapporto_uniassiale` — classic `|M_Ed|/|M_Rd|` when `[M_Rd-, M_Rd+]` straddles zero, else the
interval's centre/half-width form), biaxial (EN 1992-1-1 §5.8.9(4), exponent `a` interpolated on
`N_Ed/N_Rd`) and axial-only (EN 1992-1-1 §6.1(4) minimum eccentricity, per axis, the worse of the
two)."""
from itertools import pairwise

from strutture.shared.numeric import clamp
from strutture.shared.relazione import Passo, Traccia, Valore
from strutture.shared.sezione_ca.domini import intervallo_n
from strutture.shared.sezione_ca.domini import m_rd as m_rd_esatto
from strutture.shared.sezione_ca.modelli import Sezione
from strutture.shared.tables import interp_lookup

from .models_output import RigaAzione
from .rapporto import (
    ECCENTRICITA_MINIMA_ASSOLUTA_MM,
    FRAZIONE_ALTEZZA_ECCENTRICITA_MINIMA_MM,
    TABELLA_ESPONENTE_INTERAZIONE,
)

CLAUSOLA_UNIASSIALE = "NTC2018 §4.1.2.3.4.2"
CLAUSOLA_BIASSIALE = "EN 1992-1-1 §5.8.9(4)"
CLAUSOLA_ASSIALE = "EN 1992-1-1 §6.1(4)"
CLAUSOLA_MRD = "NTC2018 §4.1.2.3.4.2"


def traccia_governante(sezione: Sezione, governante: RigaAzione, h_x_mm: float, h_y_mm: float) -> Traccia:
    """Titolo che nomina la combinazione governante (§6); solo il ramo di `TipoPressoflessione`
    effettivamente selezionato è tracciato."""
    titolo = f"Verifica a pressoflessione — combinazione governante '{governante.nome}'"
    if governante.rapporto is None:
        return Traccia(titolo=titolo, passi=(_passo_fuori_dominio(sezione, governante),))
    if governante.tipo == "uniassiale x":
        passi = _passi_uniassiale(sezione, governante, "x")
    elif governante.tipo == "uniassiale y":
        passi = _passi_uniassiale(sezione, governante, "y")
    elif governante.tipo == "biassiale":
        n_rd_kN = intervallo_n(sezione)[1]
        passi = _passi_biassiale(sezione, governante, n_rd_kN)
    else:
        passi = _passi_assiale(sezione, governante, h_x_mm, h_y_mm)
    return Traccia(titolo=titolo, passi=passi)


def _passo_fuori_dominio(sezione: Sezione, governante: RigaAzione) -> Passo:
    """Il confronto della normativa è a doppio lato (N_min <= N_Ed <= N_max), non esprimibile come
    un unico confronto nella grammatica (docs/architecture-phase2.md §2: al più UN confronto per
    formula): si mostra il solo lato effettivamente violato."""
    n_min_kN, n_max_kN = intervallo_n(sezione)
    supera_compressione = governante.n_ed_kN > n_max_kN
    if supera_compressione:
        simbolo, valore = "N_max", n_max_kN
        formula, nota_limite = "N_Ed <= N_max", "compressione eccessiva: N_Ed supera l'estremo massimo del dominio."
    else:
        simbolo, valore = "N_min", n_min_kN
        formula, nota_limite = "N_Ed >= N_min", "trazione eccessiva: N_Ed è inferiore all'estremo minimo del dominio."
    return Passo(
        simbolo="η", formula=formula,
        valori=(
            Valore(simbolo="N_Ed", valore=governante.n_ed_kN, unita="kN", descrizione="sforzo normale della combinazione governante"),
            Valore(simbolo=simbolo, valore=valore, unita="kN", descrizione="estremo del dominio, calcolato sopra"),
        ),
        risultato=governante.n_ed_kN, unita="kN", clausola=CLAUSOLA_UNIASSIALE, esito="non soddisfatta",
        nota=f"N_Ed è fuori dal campo di resistenza assiale della sezione ({nota_limite}): nessun M_Rd è definito a questo N.",
    )


def _id_bound(asse: str, segno: str) -> str:
    """Identificatore grammar-legal per M_Rd,{asse}±: 'pos'/'neg' come sottoscritto (niente +/-)."""
    return f"M_Rd,{asse},{segno}"


def _etichetta_bound(asse: str, segno: str) -> str:
    return f"M_Rd,{asse}+" if segno == "pos" else f"M_Rd,{asse}-"


def _passo_mrd_bound(asse: str, segno: str, valore_kNm: float) -> Passo:
    identificatore = _id_bound(asse, segno)
    return Passo(
        simbolo=_etichetta_bound(asse, segno), formula=identificatore,
        valori=(Valore(simbolo=identificatore, valore=valore_kNm, unita="kNm", descrizione="risoluzione esatta dell'equilibrio della sezione (bisezione), non una formula chiusa"),),
        risultato=valore_kNm, unita="kNm", clausola=CLAUSOLA_MRD,
        nota="Letto sul dominio di resistenza N-M tracciato in alto (grafico), risolto esattamente alla combinazione governante.",
    )


def _passo_mrd_segno(simbolo_mrd: str, asse: str, m_ed_kNm: float, rd_pos: float, rd_neg: float) -> Passo:
    segno = "pos" if m_ed_kNm >= 0.0 else "neg"
    identificatore, valore = _id_bound(asse, segno), (rd_pos if segno == "pos" else rd_neg)
    # Il segno selezionato (quello di M_Ed,{asse}) va nel simbolo stampato, non solo nella nota
    # (`traccia_a_testo` non stampa mai `Passo.nota`, review finding MISSING_STEP): altrimenti
    # "M_Rd,x = M_Rd,x,pos" si legge come una legge incondizionata, non come l'esito del solo
    # ramo M_Ed,x ≥ 0.
    condizione = f"M_Ed,{asse} ≥ 0" if segno == "pos" else f"M_Ed,{asse} < 0"
    return Passo(
        simbolo=f"{simbolo_mrd}  ({condizione})", formula=identificatore,
        valori=(Valore(simbolo=identificatore, valore=valore, unita="kNm", descrizione="calcolato sopra"),),
        risultato=valore, unita="kNm",
        nota=f"Momento resistente nel verso di M_Ed,{asse} (segno di M_Ed,{asse}), fra i due estremi calcolati sopra.",
    )


def _rapporto_uniassiale_formula(simbolo_ed: str, asse: str, m_ed: float, rd_pos: float, rd_neg: float) -> tuple[str, tuple[Valore, ...], float]:
    """Restates `shared.sezione_ca.verifica.rapporto_uniassiale` exactly: the ordinary ray-from-
    origin ratio when `[rd_neg, rd_pos]` straddles zero, else distance-from-centre/half-width."""
    if rd_neg <= 0.0 <= rd_pos:
        segno = "pos" if m_ed >= 0.0 else "neg"
        scelto, valore_scelto = _id_bound(asse, segno), (rd_pos if segno == "pos" else rd_neg)
        formula = f"abs({simbolo_ed}) / abs({scelto})"
        valori = (
            Valore(simbolo=simbolo_ed, valore=m_ed, unita="kNm", descrizione="momento di progetto (o minimo) della combinazione governante"),
            Valore(simbolo=scelto, valore=valore_scelto, unita="kNm", descrizione="momento resistente nel verso di M_Ed, calcolato sopra"),
        )
        return formula, valori, abs(m_ed) / abs(valore_scelto)
    centro, semiampiezza = (rd_pos + rd_neg) / 2.0, (rd_pos - rd_neg) / 2.0
    formula = f"abs({simbolo_ed} - M_c,{asse}) / ΔM_{asse}"
    valori = (
        Valore(simbolo=simbolo_ed, valore=m_ed, unita="kNm", descrizione="momento di progetto (o minimo) della combinazione governante"),
        Valore(simbolo=f"M_c,{asse}", valore=centro, unita="kNm", descrizione="centro dell'intervallo [M_Rd-, M_Rd+], calcolato sopra"),
        Valore(simbolo=f"ΔM_{asse}", valore=semiampiezza, unita="kNm", descrizione="semiampiezza dell'intervallo [M_Rd-, M_Rd+]"),
    )
    return formula, valori, abs(m_ed - centro) / semiampiezza


def _passi_uniassiale(sezione: Sezione, governante: RigaAzione, asse: str) -> tuple[Passo, ...]:
    m_ed = governante.m_ed_x_kNm if asse == "x" else governante.m_ed_y_kNm
    rd_pos, rd_neg = m_rd_esatto(sezione, governante.n_ed_kN, asse)
    simbolo_ed, simbolo_mrd = f"M_Ed,{asse}", f"M_Rd,{asse}"
    formula, valori_extra, valore_rapporto = _rapporto_uniassiale_formula(simbolo_ed, asse, m_ed, rd_pos, rd_neg)
    soddisfatta = valore_rapporto <= 1.0
    return (
        _passo_mrd_bound(asse, "pos", rd_pos),
        _passo_mrd_bound(asse, "neg", rd_neg),
        _passo_mrd_segno(simbolo_mrd, asse, m_ed, rd_pos, rd_neg),
        Passo(
            simbolo="η", formula=f"({formula}) <= 1", valori=valori_extra, risultato=valore_rapporto, unita="-",
            clausola=CLAUSOLA_UNIASSIALE, esito="soddisfatta" if soddisfatta else "non soddisfatta",
            nota="Tasso di sfruttamento a pressoflessione retta.",
        ),
    )


def _passi_biassiale(sezione: Sezione, governante: RigaAzione, n_rd_kN: float) -> tuple[Passo, ...]:
    rd_x_pos, rd_x_neg = m_rd_esatto(sezione, governante.n_ed_kN, "x")
    rd_y_pos, rd_y_neg = m_rd_esatto(sezione, governante.n_ed_kN, "y")
    mx_rd = rd_x_pos if governante.m_ed_x_kNm >= 0.0 else rd_x_neg
    my_rd = rd_y_pos if governante.m_ed_y_kNm >= 0.0 else rd_y_neg
    a = _esponente_interazione(governante.n_ed_kN, n_rd_kN)
    valore_rapporto = (abs(governante.m_ed_x_kNm) / abs(mx_rd)) ** a + (abs(governante.m_ed_y_kNm) / abs(my_rd)) ** a
    soddisfatta = valore_rapporto <= 1.0
    return (
        _passo_mrd_bound("x", "pos", rd_x_pos), _passo_mrd_bound("x", "neg", rd_x_neg),
        _passo_mrd_segno("M_Rd,x", "x", governante.m_ed_x_kNm, rd_x_pos, rd_x_neg),
        _passo_mrd_bound("y", "pos", rd_y_pos), _passo_mrd_bound("y", "neg", rd_y_neg),
        _passo_mrd_segno("M_Rd,y", "y", governante.m_ed_y_kNm, rd_y_pos, rd_y_neg),
        _passo_esponente(governante.n_ed_kN, n_rd_kN, a),
        Passo(
            simbolo="η", formula="(abs(M_Ed,x) / abs(M_Rd,x))^a + (abs(M_Ed,y) / abs(M_Rd,y))^a <= 1",
            valori=(
                Valore(simbolo="M_Ed,x", valore=governante.m_ed_x_kNm, unita="kNm", descrizione="momento di progetto attorno a x"),
                Valore(simbolo="M_Rd,x", valore=mx_rd, unita="kNm", descrizione="momento resistente attorno a x, calcolato sopra"),
                Valore(simbolo="M_Ed,y", valore=governante.m_ed_y_kNm, unita="kNm", descrizione="momento di progetto attorno a y"),
                Valore(simbolo="M_Rd,y", valore=my_rd, unita="kNm", descrizione="momento resistente attorno a y, calcolato sopra"),
                Valore(simbolo="a", valore=a, descrizione="esponente di interazione, calcolato sopra"),
            ),
            risultato=valore_rapporto, unita="-", clausola=CLAUSOLA_BIASSIALE,
            esito="soddisfatta" if soddisfatta else "non soddisfatta",
            nota="Tasso di sfruttamento a pressoflessione deviata (formula di interazione).",
        ),
    )


def _esponente_interazione(n_ed_kN: float, n_rd_kN: float) -> float:
    rapporto_assiale = clamp(n_ed_kN / n_rd_kN, 0.1, 1.0) if n_rd_kN > 0.0 else 0.1
    return interp_lookup(TABELLA_ESPONENTE_INTERAZIONE, rapporto_assiale)


def _segmento_tabella(n_ed_kN: float, n_rd_kN: float) -> tuple[tuple[float, float], tuple[float, float]]:
    x = clamp(n_ed_kN / n_rd_kN, 0.1, 1.0) if n_rd_kN > 0.0 else 0.1
    for (x0, y0), (x1, y1) in pairwise(TABELLA_ESPONENTE_INTERAZIONE):
        if x0 <= x <= x1:
            return (x0, y0), (x1, y1)
    return TABELLA_ESPONENTE_INTERAZIONE[0], TABELLA_ESPONENTE_INTERAZIONE[1]


def _passo_esponente(n_ed_kN: float, n_rd_kN: float, a: float) -> Passo:
    (x1, a1), (x2, a2) = _segmento_tabella(n_ed_kN, n_rd_kN)
    # Il segmento di tabella selezionato va nel simbolo stampato, non solo nella nota
    # (`traccia_a_testo` non stampa mai `Passo.nota`, review finding MISSING_STEP): la formula
    # stampa solo i due nodi usati, non l'intera tabella (0,1; 1,0)—(0,7; 1,5)—(1,0; 2,0), quindi
    # senza il simbolo un lettore non può dire quale segmento fu scelto.
    return Passo(
        simbolo=f"a  (segmento [{x1:g}; {x2:g}])",
        formula=f"{a1:g} + ({a2:g} - {a1:g}) * (min(max(N_Ed / N_Rd, {x1:g}), {x2:g}) - {x1:g}) / ({x2:g} - {x1:g})",
        valori=(
            Valore(simbolo="N_Ed", valore=n_ed_kN, unita="kN", descrizione="sforzo normale della combinazione governante"),
            Valore(simbolo="N_Rd", valore=n_rd_kN, unita="kN", descrizione="estremo massimo del dominio (N_max), calcolato sopra"),
        ),
        risultato=a, unita="-", clausola=CLAUSOLA_BIASSIALE,
        nota=f"Esponente di interazione, interpolato linearmente sulla tabella (N_Ed/N_Rd, a): "
             f"(0,1; 1,0) — (0,7; 1,5) — (1,0; 2,0); segmento [{x1:g}; {x2:g}] selezionato.",
    )


def _passi_assiale(sezione: Sezione, governante: RigaAzione, h_x_mm: float, h_y_mm: float) -> tuple[Passo, ...]:
    rd_x_pos, rd_x_neg = m_rd_esatto(sezione, governante.n_ed_kN, "x")
    rd_y_pos, rd_y_neg = m_rd_esatto(sezione, governante.n_ed_kN, "y")
    e0_x = max(h_x_mm / FRAZIONE_ALTEZZA_ECCENTRICITA_MINIMA_MM, ECCENTRICITA_MINIMA_ASSOLUTA_MM)
    e0_y = max(h_y_mm / FRAZIONE_ALTEZZA_ECCENTRICITA_MINIMA_MM, ECCENTRICITA_MINIMA_ASSOLUTA_MM)
    m_min_x = governante.n_ed_kN * e0_x / 1000.0
    m_min_y = governante.n_ed_kN * e0_y / 1000.0
    formula_x, valori_x, rho_x = _rapporto_uniassiale_formula("M_min,x", "x", m_min_x, rd_x_pos, rd_x_neg)
    formula_y, valori_y, rho_y = _rapporto_uniassiale_formula("M_min,y", "y", m_min_y, rd_y_pos, rd_y_neg)
    valore_rapporto = max(rho_x, rho_y)
    soddisfatta = valore_rapporto <= 1.0
    return (
        _passo_eccentricita_minima("e_0,x", h_x_mm, e0_x, "x"),
        _passo_momento_minimo("M_min,x", governante.n_ed_kN, e0_x, m_min_x, "x"),
        _passo_mrd_bound("x", "pos", rd_x_pos), _passo_mrd_bound("x", "neg", rd_x_neg),
        Passo(simbolo="ρ_x", formula=formula_x, valori=valori_x, risultato=rho_x, unita="-", clausola=CLAUSOLA_ASSIALE, nota="Tasso di sfruttamento assiale, direzione x."),
        _passo_eccentricita_minima("e_0,y", h_y_mm, e0_y, "y"),
        _passo_momento_minimo("M_min,y", governante.n_ed_kN, e0_y, m_min_y, "y"),
        _passo_mrd_bound("y", "pos", rd_y_pos), _passo_mrd_bound("y", "neg", rd_y_neg),
        Passo(simbolo="ρ_y", formula=formula_y, valori=valori_y, risultato=rho_y, unita="-", clausola=CLAUSOLA_ASSIALE, nota="Tasso di sfruttamento assiale, direzione y."),
        Passo(
            simbolo="η", formula="max(ρ_x, ρ_y) <= 1",
            valori=(
                Valore(simbolo="ρ_x", valore=rho_x, descrizione="tasso di sfruttamento direzione x, calcolato sopra"),
                Valore(simbolo="ρ_y", valore=rho_y, descrizione="tasso di sfruttamento direzione y, calcolato sopra"),
            ),
            risultato=valore_rapporto, unita="-", clausola=CLAUSOLA_ASSIALE,
            esito="soddisfatta" if soddisfatta else "non soddisfatta",
            nota="Sforzo normale (quasi) centrato: verificato con l'eccentricità minima su entrambi gli assi, si prende il caso peggiore.",
        ),
    )


def _passo_eccentricita_minima(simbolo: str, dimensione_mm: float, e0_mm: float, nome_asse: str) -> Passo:
    return Passo(
        simbolo=simbolo, formula=f"max(h_{nome_asse} / {FRAZIONE_ALTEZZA_ECCENTRICITA_MINIMA_MM:g}, {ECCENTRICITA_MINIMA_ASSOLUTA_MM:g})",
        valori=(Valore(simbolo=f"h_{nome_asse}", valore=dimensione_mm, unita="mm", descrizione=f"ingombro della sezione lungo l'asse ortogonale a {nome_asse}"),),
        risultato=e0_mm, unita="mm", clausola=CLAUSOLA_ASSIALE, nota="Eccentricità minima.",
    )


def _passo_momento_minimo(simbolo: str, n_ed_kN: float, e0_mm: float, m_min_kNm: float, nome_asse: str) -> Passo:
    return Passo(
        simbolo=simbolo, formula=f"N_Ed * e_0,{nome_asse}", scala=1e-3,
        valori=(
            Valore(simbolo="N_Ed", valore=n_ed_kN, unita="kN", descrizione="sforzo normale della combinazione governante"),
            Valore(simbolo=f"e_0,{nome_asse}", valore=e0_mm, unita="mm", descrizione="eccentricità minima, calcolata sopra"),
        ),
        risultato=m_min_kNm, unita="kNm", clausola=CLAUSOLA_ASSIALE,
        nota="Momento minimo equivalente all'eccentricità minima.",
    )
