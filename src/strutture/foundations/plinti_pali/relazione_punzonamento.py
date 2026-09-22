"""Verified restatement (docs/architecture-phase2.md §6) of Tool-4's punching checks
(`taglio_punzonamento.py::punzonamento_colonna`/`punzonamento_palo`, EC2 §6.4), STANDARD mode only:
`α_cc`/`ν`/`k_max` as the tool's own inputs (never the sheet's fixed `α_cc=1`/`k_max=0,5`), the
eccentricity factor β applied (EC2 eq. 6.39, simplified interior-column form) and the corner-pile
control perimeter capped to the non-overlapping distance `a` (EC2 §6.4.2(5)).

`a` (`punzonamento_palo.a_mm`) is cited directly from the output rather than re-derived: it is the
minimum of up to 5 geometric bounds (`taglio_punzonamento._distanza_disponibile_mm`, task addition,
no sheet cell, no single EC2 formula) — the same allowance the architecture brief gives a table
lookup the notation grammar cannot express (mirrors `ca_travi.relazione_sle`'s σ_s,limite). `k`/`ρ`
are reused from the "Resistenza a taglio" Traccia (same pile-cap section, same values; in standard
mode `k=k_size(d_v)` is already capped at 2, so `taglio_punzonamento.punzonamento_palo`'s own
`k_eff = k_size(d_v) if k>2 else k` never takes its first branch)."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .input import PlintoSuPaliInput
from .models import PlintoSuPaliOutput
from .models_taglio import Punzonamento, PunzonamentoPalo, Taglio
from .relazione_comune import fcd_frammento, nu_vrd_max_frammento, valore_fck, valore_gamma_c
from .relazione_helpers import trova_riga
from .rows import RigaCarico

EC2_PUNZ_COLONNA = "EN 1992-1-1 §6.4.5(3)"
EC2_PUNZ_PALO = "EN 1992-1-1 §6.4.4(2)"


def traccia_punzonamento_colonna(inputs: PlintoSuPaliInput, output: PlintoSuPaliOutput, peso_kN: float) -> Traccia:
    """5 passi: β, perimetro u_0, taglio di punzonamento V_Ed, resistenza V_Rd,max, Check
    "Punzonamento al filo pilastro"."""
    n_tot_riga = next(r for r in output.inviluppo if r.grandezza == "n_totale_max")
    riga = trova_riga(output.righe, n_tot_riga.nodo, n_tot_riga.combo)
    nsd_kN = n_tot_riga.valore + peso_kN
    bx_mm, by_mm = inputs.bx_pilastro_m * 1000.0, inputs.by_pilastro_m * 1000.0
    punz = output.punzonamento
    passi = (
        _passo_beta(riga, nsd_kN, bx_mm, by_mm, punz),
        _passo_u0(bx_mm, by_mm, punz),
        _passo_ved(nsd_kN, punz),
        _passo_vrd_max(inputs, output, punz),
        _passo_check_colonna(punz),
    )
    return Traccia(titolo="Punzonamento al filo del pilastro", passi=passi)


def traccia_punzonamento_palo(inputs: PlintoSuPaliInput, output: PlintoSuPaliOutput) -> Traccia:
    """3 passi: perimetro di verifica u_p, resistenza V_Rd,c del palo, Check "Punzonamento del palo
    d'angolo"."""
    passi = (
        _passo_up(inputs, output.punzonamento_palo),
        _passo_vrdc_palo(inputs, output),
        _passo_check_palo(output),
    )
    return Traccia(titolo="Punzonamento al perimetro del palo d'angolo", passi=passi)


def _passo_beta(riga: RigaCarico, nsd_kN: float, bx_mm: float, by_mm: float, punz: Punzonamento) -> Passo:
    formula = "1 + 1.8 * sqrt((abs(M_y) / N_sd * 1000 / b_X)^2 + (abs(M_x) / N_sd * 1000 / b_Y)^2)"
    return Passo(
        simbolo="β", formula=formula,
        valori=(
            Valore(simbolo="M_y", valore=riga.my_finale_kNm, unita="kNm", descrizione=f"momento My finale in testa ai pali, combinazione {riga.combo}"),
            Valore(simbolo="N_sd", valore=nsd_kN, unita="kN", descrizione="carico assiale totale (colonna + peso proprio del plinto)"),
            Valore(simbolo="b_X", valore=bx_mm, unita="mm", descrizione="dimensione del pilastro lungo X"),
            Valore(simbolo="M_x", valore=riga.mx_finale_kNm, unita="kNm", descrizione="momento Mx finale in testa ai pali"),
            Valore(simbolo="b_Y", valore=by_mm, unita="mm", descrizione="dimensione del pilastro lungo Y"),
        ),
        risultato=punz.beta, unita="-", clausola="EN 1992-1-1 §6.4.3(3) eq. 6.39, semplificata",
        nota="Semplificazione a favore di sicurezza: le eccentricità sono divise per i lati del pilastro (b_X, b_Y) "
             "anziché per le dimensioni del perimetro di verifica (b_y, b_z ≈ lato + 4·d) dell'eq. 6.39: β risulta "
             "maggiore (registro: plinti-pali/beta-con-lati-del-pilastro).",
    )


def _passo_u0(bx_mm: float, by_mm: float, punz: Punzonamento) -> Passo:
    return Passo(
        simbolo="u_0", formula="2 * (b_X + b_Y)",
        valori=(
            Valore(simbolo="b_X", valore=bx_mm, unita="mm", descrizione="dimensione del pilastro lungo X"),
            Valore(simbolo="b_Y", valore=by_mm, unita="mm", descrizione="dimensione del pilastro lungo Y"),
        ),
        risultato=punz.u_mm, unita="mm", clausola="EN 1992-1-1 §6.4.2",
        nota="Perimetro di verifica al filo del pilastro rettangolare (distanza nulla dal filo).",
    )


def _passo_ved(nsd_kN: float, punz: Punzonamento) -> Passo:
    return Passo(
        simbolo="V_Ed", formula="β * N_sd",
        valori=(
            Valore(simbolo="β", valore=punz.beta, descrizione="fattore di eccentricità, calcolato sopra"),
            Valore(simbolo="N_sd", valore=nsd_kN, unita="kN"),
        ),
        risultato=punz.ved_kN, unita="kN", clausola="EN 1992-1-1 §6.4.3(1)",
        nota="Taglio di punzonamento sollecitante al filo del pilastro.",
    )


def _passo_vrd_max(inputs: PlintoSuPaliInput, output: PlintoSuPaliOutput, punz: Punzonamento) -> Passo:
    d_v = output.taglio.d_mm
    formula = f"k_max * {nu_vrd_max_frammento()} * {fcd_frammento()} * u_0 * d_v / 1000"
    return Passo(
        simbolo="V_Rd,max", formula=formula,
        valori=(
            Valore(simbolo="k_max", valore=inputs.coeff_vrd_max, descrizione="coefficiente di v_Rd,max: 0,4 (EN 1992-1-1/A1:2014) oppure 0,5 (EN 1992-1-1:2004 + Appendice Nazionale italiana)"),
            valore_fck(output.materiali.calcestruzzo.fck_MPa), valore_gamma_c(inputs.gamma_c),
            Valore(simbolo="u_0", valore=punz.u_mm, unita="mm", descrizione="perimetro di verifica al filo del pilastro, calcolato sopra"),
            Valore(simbolo="d_v", valore=d_v, unita="mm", descrizione="altezza utile, calcolata sopra (Resistenza a taglio)"),
        ),
        risultato=punz.vrd_max_kN, unita="kN", clausola=EC2_PUNZ_COLONNA,
        nota="Resistenza massima a punzonamento al filo del pilastro (schiacciamento delle bielle, nessuna armatura può innalzare questo limite).",
    )


def _passo_check_colonna(punz: Punzonamento) -> Passo:
    return Passo(
        simbolo="V_Ed/V_Rd,max", formula="V_Ed <= V_Rd,max",
        valori=(
            Valore(simbolo="V_Ed", valore=punz.ved_kN, unita="kN"),
            Valore(simbolo="V_Rd,max", valore=punz.vrd_max_kN, unita="kN"),
        ),
        risultato=punz.ved_kN, unita="kN", clausola=EC2_PUNZ_COLONNA,
        esito="soddisfatta" if punz.verificato else "non soddisfatta",
        nota="Verifica \"Punzonamento al filo pilastro\".",
    )


def _passo_up(inputs: PlintoSuPaliInput, palo: PunzonamentoPalo) -> Passo:
    return Passo(
        simbolo="u_p", formula="π * (φ_palo + 2 * a)",
        valori=(
            Valore(simbolo="π", valore=3.141592653589793),
            Valore(simbolo="φ_palo", valore=inputs.diametro_pila_mm, unita="mm", descrizione="diametro del palo"),
            Valore(simbolo="a", valore=palo.a_mm, unita="mm",
                   descrizione="distanza disponibile dal filo palo prima di bordo plinto o palo adiacente, EC2 §6.4.2(5) (≤2·d_v)"),
        ),
        risultato=palo.u_mm, unita="mm", clausola="EN 1992-1-1 §6.4.2",
        nota="Perimetro di verifica del palo d'angolo, limitato dall'interasse pali/bordo plinto quando è inferiore a 2·d_v.",
    )


def _passo_vrdc_palo(inputs: PlintoSuPaliInput, output: PlintoSuPaliOutput) -> Passo:
    taglio: Taglio = output.taglio
    palo = output.punzonamento_palo
    formula = (
        "max(0.18 / γ_c * k * (100 * min(ρ, 0.02) * f_ck)^(1/3), 0.035 * k^1.5 * sqrt(f_ck)) "
        "* (2 * d_v / a) * u_p * d_v / 1000"
    )
    return Passo(
        simbolo="V_Rd,c,palo", formula=formula,
        valori=(
            valore_gamma_c(inputs.gamma_c),
            Valore(simbolo="k", valore=taglio.k, descrizione="fattore dimensionale, riutilizzato dalla Resistenza a taglio sopra"),
            Valore(simbolo="ρ", valore=taglio.rho, descrizione="quota di armatura tesa disposta, riutilizzata dalla Resistenza a taglio sopra"),
            valore_fck(output.materiali.calcestruzzo.fck_MPa),
            Valore(simbolo="d_v", valore=taglio.d_mm, unita="mm", descrizione="altezza utile, calcolata sopra"),
            Valore(simbolo="a", valore=palo.a_mm, unita="mm", descrizione="distanza disponibile, calcolata sopra"),
            Valore(simbolo="u_p", valore=palo.u_mm, unita="mm", descrizione="perimetro di verifica del palo, calcolato sopra"),
        ),
        risultato=palo.vrd_c_kN, unita="kN", clausola=EC2_PUNZ_PALO,
        nota="Perimetro di verifica a distanza a < 2·d_v: la resistenza del calcestruzzo è incrementata di 2·d_v/a "
             "(EN 1992-1-1 §6.4.4(2), eq. 6.50).",
    )


def _passo_check_palo(output: PlintoSuPaliOutput) -> Passo:
    palo = output.punzonamento_palo
    return Passo(
        simbolo="N_max/V_Rd,c,palo", formula="N_max <= V_Rd,c,palo",
        valori=(
            Valore(simbolo="N_max", valore=output.n_max_pila_kN, unita="kN", descrizione="reazione di progetto sul palo, calcolata sopra"),
            Valore(simbolo="V_Rd,c,palo", valore=palo.vrd_c_kN, unita="kN"),
        ),
        risultato=output.n_max_pila_kN, unita="kN", clausola=EC2_PUNZ_PALO,
        esito="soddisfatta" if palo.verificato else "non soddisfatta",
        nota="Verifica \"Punzonamento del palo d'angolo\".",
    )
