"""Verified restatement (docs/architecture-phase2.md) of `taglio_puntoni.py` (σ_cp, a_c, EC2 §6.2.3),
`taglio_theta.py` (cotθ, EC2 §6.2.3), `taglio_resistenza.py` (V_Rd,c/V_Rd,s, EC2 §6.2.3 / NTC2018
§4.1.2.1.3.2) and `gerarchia.py` (capacity-design shear demand, NTC2018 §7.4.4.2.1). `z` (leva
interna, `geometria.leva_interna`) is not exposed by `TaglioResult`, so it is read straight from the
package's own step function, the way the architecture brief allows for a value the calling `Traccia`
does not itself need to re-derive elsewhere. The stirrup inclination is a package constant α=90°
(no input for it, unlike `ca_travi`'s `alpha_staffe_deg`), so cotα=1/tan(90°)≈0 and sin(90°)=1 are
dropped from the restated formulas — their true (floating-point, not exactly zero/one) contribution
is orders of magnitude below the harness's own numeric tolerance — noted in `V_Rd,c`'s `nota`.

`ν1` (the strut-efficiency factor shared by cotθ and V_Rd,c) is a fixed 0.5 for NTC2018/NTC2008 and
`0.6·(1-f_ck/250)` for EC2 (EC2 §6.2.2(6), already reflected in `RegoleResult.nu1`): its formula is
folded into a described `Valore` reused by both formulas rather than promoted to its own `Passo`
(docs/architecture-phase2.md lesson: "a coefficient... gets a step OR a named Valore with a
descrizione"), keeping this package's per-tool step count inside the 10-30 target."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .geometria import leva_interna
from .gerarchia import CAPACITY_DESIGN_HINGES, GAMMA_RD
from .models import Norma, PilastroCircolareInput, PilastroOutput, PilastroRettangolareInput
from .taglio_puntoni import STRUT_COEFFICIENT_LOW_THRESHOLD, STRUT_COEFFICIENT_MID, STRUT_COEFFICIENT_MID_THRESHOLD
from .taglio_theta import COT_THETA_MAX, COT_THETA_MIN

PilastroInput = PilastroRettangolareInput | PilastroCircolareInput
PI_GRECO = 3.141592653589793
MM_PER_M = 1000.0  # strutture.shared.units.mm_to_m
_CLAUSOLA_TAGLIO = "NTC2018 §4.1.2.1.3.2 / EC2 §6.2.3"


def _valore_nu1(output: PilastroOutput) -> Valore:
    norma: Norma = output.regole.norma
    descrizione = (
        "ν1 = 0,6·(1-f_ck/250), EC2 §6.2.2(6) — dai materiali calcolati sopra"
        if norma == "EC2"
        else "coefficiente ν1, valore fisso NTC2018/NTC2008 (non dalla formula EC2 §6.2.2(6))"
    )
    return Valore(simbolo="ν1", valore=output.regole.nu1, descrizione=descrizione)


def traccia_taglio(
    inputs: PilastroInput, output: PilastroOutput, *,
    larghezza_mm: float, larghezza_simbolo: str, larghezza_descrizione: str,
    altezza_mm: float, altezza_simbolo: str, altezza_descrizione: str,
) -> Traccia:
    """8 passi: A_sw, σ_cp, a_c, z, cotgθ, V_Rcd, V_Rd,s, Check "Resistenza a taglio".

    Review finding (MISLEADING): il codice fissa SEMPRE `z = leva_interna(L_2, c)` (braccio di leva
    lungo la dimensione L_2) e `larghezza = L_1` in `vrdc`/`cot_theta` (`tool_rettangolare.py::
    _taglio`), qualunque sia la direzione in cui agisce l'unico V_Ed in input — non "la dimensione
    che il chiamante passa" come prima di questa correzione, quando entrambi gli usi condividevano
    lo stesso `larghezza_mm` (bug: per una sezione non quadrata z veniva calcolato su L_1 invece che
    su L_2). `altezza_mm`/`altezza_simbolo` (usati SOLO da z) e `larghezza_mm`/`larghezza_simbolo`
    (usati da cotgθ/V_Rcd/V_Rd,s) sono ora passati separatamente: L_2/L_1 per la sezione
    rettangolare, `l_eq` per entrambi nella circolare (un'unica dimensione equivalente)."""
    materiali = output.materiali
    passo_asw = _passo_asw(inputs)
    passo_sigma_cp = _passo_sigma_cp(inputs, output)
    passo_ac = _passo_ac(output, passo_sigma_cp.risultato, materiali.fcd_MPa)
    passo_z = _passo_z(altezza_mm, altezza_simbolo, altezza_descrizione, inputs.c_mm)
    passo_cotgtheta = _passo_cotgtheta(inputs, output, larghezza_mm, larghezza_simbolo, passo_asw.risultato, passo_ac.risultato)
    passo_vrdc = _passo_vrdc(output, larghezza_mm, larghezza_simbolo, passo_z.risultato, passo_ac.risultato, passo_cotgtheta.risultato)
    passo_vrds = _passo_vrds(inputs, output, passo_z.risultato, passo_asw.risultato, passo_cotgtheta.risultato)
    passo_check = _passo_check_taglio(inputs, output, passo_vrdc.risultato, passo_vrds.risultato)
    passi = (passo_asw, passo_sigma_cp, passo_ac, passo_z, passo_cotgtheta, passo_vrdc, passo_vrds, passo_check)
    titolo = "Resistenza a taglio"
    if altezza_simbolo != larghezza_simbolo:
        titolo += f" — V_Ed assunto flettente attorno all'asse con leva {altezza_simbolo} (anima {larghezza_simbolo})"
    return Traccia(titolo=titolo, passi=passi)


def traccia_gerarchia(inputs: PilastroInput, output: PilastroOutput) -> Traccia:
    """1 passo (Check "Gerarchia delle resistenze a taglio", NTC2018 §7.4.4.2.1): γ_Rd è un valore
    normativo a sé, mai una cifra nuda nella formula, come V_Ed,max in `ca_travi.relazione_taglio`."""
    taglio = output.taglio
    soddisfatta = taglio.vrd_kN > taglio.domanda_capacity_design_kN
    passo = Passo(
        simbolo="V_Ed,DC", formula=f"γ_Rd * {CAPACITY_DESIGN_HINGES:g} * M_Rd / (H / {MM_PER_M:g}) <= V_Rd",
        valori=(
            Valore(simbolo="γ_Rd", valore=GAMMA_RD, descrizione="fattore di sovraresistenza NTC2018 §7.4.4.2.1 per CD \"B\" (1,30 per CD \"A\")"),
            Valore(simbolo="M_Rd", valore=inputs.mrd_kNm, unita="kNm", descrizione="momento resistente della sezione, dato di ingresso"),
            Valore(simbolo="H", valore=inputs.h_mm, unita="mm", descrizione="altezza netta del pilastro"),
            Valore(simbolo="V_Rd", valore=taglio.vrd_kN, unita="kN", descrizione="resistenza a taglio, calcolata sopra"),
        ),
        risultato=taglio.domanda_capacity_design_kN, unita="kN", clausola="NTC2018 §7.4.4.2.1",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Taglio di calcolo da gerarchia delle resistenze: momenti resistenti a entrambe le estremità del "
             "pilastro, sull'intera altezza netta (nessuna somma con il taglio dei carichi gravitazionali, "
             "assente in questo tool).",
    )
    return Traccia(titolo="Gerarchia delle resistenze a taglio", passi=(passo,))


def _passo_asw(inputs: PilastroInput) -> Passo:
    asw_mm2 = 2.0 * PI_GRECO * inputs.diametro_staffe_mm**2 / 4.0
    return Passo(
        simbolo="A_sw", formula="2 * π * φ_sw^2 / 4",
        valori=(
            Valore(simbolo="π", valore=PI_GRECO),
            Valore(simbolo="φ_sw", valore=inputs.diametro_staffe_mm, unita="mm", descrizione="diametro delle staffe (2 bracci)"),
        ),
        risultato=asw_mm2, unita="mm2", nota="Area delle staffe presenti (sezione, 2 bracci).",
    )


def _passo_sigma_cp(inputs: PilastroInput, output: PilastroOutput) -> Passo:
    return Passo(
        simbolo="σ_cp", formula=f"N_Ed * {MM_PER_M:g} / A_c",
        valori=(
            Valore(simbolo="N_Ed", valore=inputs.ned_kN, unita="kN"),
            Valore(simbolo="A_c", valore=output.geometria.ac_mm2, unita="mm2"),
        ),
        risultato=output.taglio.sigma_cp_MPa, unita="MPa", clausola="EC2 §6.2.3",
        nota="Tensione media di compressione nella sezione.",
    )


def _passo_ac(output: PilastroOutput, sigma_cp_MPa: float, fcd_MPa: float) -> Passo:
    """3 rami residui del selettore (il ramo di trazione è morto nel dominio di questo tool, N_Ed>0
    sempre — vedi `taglio_puntoni.py`): il ramo scelto qui sotto è quello effettivamente attivo per
    questo calcolo.

    Review finding (MISLEADING): la clausola EC2 §6.2.3 è un selettore a rami (1 in trazione;
    1+σ_cp/f_cd sotto 0,25·f_cd; 1,25 fisso fino a 0,5·f_cd; 2,5·(1-σ_cp/f_cd) oltre), ma §5
    dell'architettura stampa solo formula/sostituzione/risultato: senza la condizione di validità
    resa visibile, un lettore che applica la formula stampata fuori dal suo intervallo ottiene un
    coefficiente sbagliato (fino a 2× non conservativo). La condizione è quindi parte del simbolo
    stampato (line 1), non solo della `nota` (invisibile in stampa)."""
    costante_ramo_medio = f"{STRUT_COEFFICIENT_MID:g}"
    if sigma_cp_MPa < STRUT_COEFFICIENT_LOW_THRESHOLD * fcd_MPa:
        formula = "1 + σ_cp / f_cd"
        condizione, nota_ramo = "σ_cp/f_cd < 0,25", "Ramo basso (σ_cp < 0,25·f_cd)."
    elif sigma_cp_MPa < STRUT_COEFFICIENT_MID_THRESHOLD * fcd_MPa:
        formula = costante_ramo_medio
        condizione, nota_ramo = "0,25 <= σ_cp/f_cd < 0,5", "Ramo intermedio, costante (0,25·f_cd <= σ_cp < 0,5·f_cd)."
    else:
        formula = "2.5 * (1 - σ_cp / f_cd)"
        condizione, nota_ramo = "σ_cp/f_cd >= 0,5", "Ramo alto (σ_cp >= 0,5·f_cd)."
    valori = (
        ()
        if formula == costante_ramo_medio
        else (
            Valore(simbolo="σ_cp", valore=sigma_cp_MPa, unita="MPa", descrizione="tensione media di compressione, calcolata sopra"),
            Valore(simbolo="f_cd", valore=fcd_MPa, unita="MPa"),
        )
    )
    return Passo(
        simbolo=f"a_c ({condizione})", formula=formula, valori=valori,
        risultato=output.taglio.ac, unita="-", clausola="EC2 §6.2.3",
        nota=f"Coefficiente maggiorativo per la resistenza dei puntoni compressi. {nota_ramo}",
    )


def _passo_z(altezza_mm: float, altezza_simbolo: str, altezza_descrizione: str, c_mm: float) -> Passo:
    """Braccio di leva interno, SEMPRE sulla dimensione L_2 per la sezione rettangolare
    (`tool_rettangolare.py::_taglio`: `leva_interna(inputs.l2_mm, c)`), mai su L_1: prima della
    correzione (review finding MISLEADING) il passo usava lo stesso identificatore generico
    'dimensione' per L_1 e L_2, e riceveva sempre L_1 — sbagliato per una sezione non quadrata."""
    return Passo(
        simbolo="z", formula=f"0.9 * ({altezza_simbolo} - c)",
        valori=(
            Valore(simbolo=altezza_simbolo, valore=altezza_mm, unita="mm", descrizione=altezza_descrizione),
            Valore(simbolo="c", valore=c_mm, unita="mm", descrizione="copriferro"),
        ),
        risultato=leva_interna(altezza_mm, c_mm), unita="mm", clausola="EC2 §6.2.3",
        nota="Braccio di leva interno.",
    )


def _passo_cotgtheta(
    inputs: PilastroInput, output: PilastroOutput, larghezza_mm: float, larghezza_simbolo: str, asw_mm2: float, ac: float,
) -> Passo:
    taglio, materiali = output.taglio, output.materiali
    sin2theta = f"(A_sw * f_yd) / ({larghezza_simbolo} * s * (a_c * ν1 * f_cd))"
    return Passo(
        simbolo="cotgθ",
        formula=f"min(max(sqrt((1 - {sin2theta}) / ({sin2theta})), {COT_THETA_MIN:g}), {COT_THETA_MAX:g})",
        valori=(
            Valore(simbolo="A_sw", valore=asw_mm2, unita="mm2", descrizione="area delle staffe, calcolata sopra"),
            Valore(simbolo="f_yd", valore=materiali.fyd_MPa, unita="MPa"),
            Valore(simbolo=larghezza_simbolo, valore=larghezza_mm, unita="mm"),
            Valore(simbolo="s", valore=inputs.passo_staffe_mm, unita="mm", descrizione="passo delle staffe"),
            Valore(simbolo="a_c", valore=ac, descrizione="coefficiente maggiorativo, calcolato sopra"),
            _valore_nu1(output),
            Valore(simbolo="f_cd", valore=materiali.fcd_MPa, unita="MPa"),
        ),
        risultato=taglio.cot_theta, unita="-", clausola="EC2 §6.2.3",
        nota=f"Cotangente dell'inclinazione dei puntoni di calcestruzzo, limitata all'intervallo [{COT_THETA_MIN:g}; {COT_THETA_MAX:g}].",
    )


def _passo_vrdc(output: PilastroOutput, larghezza_mm: float, larghezza_simbolo: str, z_mm: float, ac: float, cotgtheta: float) -> Passo:
    """Review finding (MISLEADING): rinominato da 'V_Rd,c' a 'V_Rcd' — 'V_Rd,c' in EC2 §6.2.2 è la
    resistenza a taglio di un elemento SENZA armatura trasversale (lo stesso simbolo usato, con
    quel significato, da `plinti_pali.relazione_taglio`), non la resistenza di schiacciamento dei
    puntoni (EC2 §6.2.3 la chiama V_Rd,max, NTC2018 §4.1.2.1.3.2 la chiama V_Rcd)."""
    taglio, materiali = output.taglio, output.materiali
    return Passo(
        simbolo="V_Rcd", formula=f"z * {larghezza_simbolo} * a_c * ν1 * f_cd * cotgθ / (1 + cotgθ^2)",
        valori=(
            Valore(simbolo="z", valore=z_mm, unita="mm", descrizione="leva interna, calcolata sopra"),
            Valore(simbolo=larghezza_simbolo, valore=larghezza_mm, unita="mm"),
            Valore(simbolo="a_c", valore=ac, descrizione="calcolato sopra"),
            _valore_nu1(output),
            Valore(simbolo="f_cd", valore=materiali.fcd_MPa, unita="MPa"),
            Valore(simbolo="cotgθ", valore=cotgtheta, descrizione="calcolata sopra"),
        ),
        risultato=taglio.vrdc_kN, unita="kN", scala=1e-3, clausola=_CLAUSOLA_TAGLIO,
        nota="Resistenza a taglio lato calcestruzzo (compressione dei puntoni, V_Rd,max in EC2 §6.2.3); "
             "le staffe sono verticali (α=90°), quindi il termine cotg α (nullo) non compare.",
    )


def _passo_vrds(inputs: PilastroInput, output: PilastroOutput, z_mm: float, asw_mm2: float, cotgtheta: float) -> Passo:
    taglio, materiali = output.taglio, output.materiali
    return Passo(
        simbolo="V_Rd,s", formula="z * (A_sw / s) * f_yd * cotgθ",
        valori=(
            Valore(simbolo="z", valore=z_mm, unita="mm", descrizione="leva interna, calcolata sopra"),
            Valore(simbolo="A_sw", valore=asw_mm2, unita="mm2", descrizione="area delle staffe, calcolata sopra"),
            Valore(simbolo="s", valore=inputs.passo_staffe_mm, unita="mm", descrizione="passo delle staffe"),
            Valore(simbolo="f_yd", valore=materiali.fyd_MPa, unita="MPa"),
            Valore(simbolo="cotgθ", valore=cotgtheta, descrizione="calcolata sopra"),
        ),
        risultato=taglio.vrds_kN, unita="kN", scala=1e-3, clausola=_CLAUSOLA_TAGLIO,
        nota="Resistenza a taglio lato armatura (snervamento delle staffe); staffe verticali (α=90°), quindi "
             "sin α=1 non compare.",
    )


def _passo_check_taglio(inputs: PilastroInput, output: PilastroOutput, vrdc_kN: float, vrds_kN: float) -> Passo:
    taglio = output.taglio
    soddisfatta = taglio.vrd_kN > inputs.ved_kN
    return Passo(
        simbolo="V_Rd", formula="min(V_Rcd, V_Rd,s) >= V_Ed",
        valori=(
            Valore(simbolo="V_Rcd", valore=vrdc_kN, unita="kN"),
            Valore(simbolo="V_Rd,s", valore=vrds_kN, unita="kN"),
            Valore(simbolo="V_Ed", valore=inputs.ved_kN, unita="kN", descrizione="taglio di calcolo agente"),
        ),
        risultato=taglio.vrd_kN, unita="kN", clausola=_CLAUSOLA_TAGLIO,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Resistenza a taglio di progetto, minimo fra lato calcestruzzo e lato armatura.",
    )
