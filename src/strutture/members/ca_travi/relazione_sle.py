"""Verified restatement (docs/architecture-phase2.md) of `sle_tensioni.py` (Tool 4, NTC2018
§4.1.2.2.5, sezione parzializzata n=15) and `fessurazione.py` (Tool 5, NTC2018 §4.1.2.2.4 +
Circolare 7/2019 C4.1.2.2.4.5). `x` (profondità dell'asse neutro della sezione parzializzata) is
derived once and reused by every stress `Check` that follows it, mirroring how an engineer writes
the calculation by hand. `σ_s,limite` (Tab. C4.1.II) is a table lookup, not a formula the
notation grammar can restate (docs/architecture-phase2.md §2 is a whitelist of arithmetic
operators and functions, no table interpolation): it is cited directly from `FessurazioneOutput`,
the way the architecture brief allows for any value the trace does not itself derive.

The optional last step (`Check` "Classe di apertura fessura conforme a Tab. 4.1.IV") compares two
Literal strings (`w1`/`w2`/`w3`), which the notation grammar cannot express directly (identifiers
evaluate to numbers): both classes are encoded through `_CODICE_CLASSE` (w1=1, w2=2, w3=3, in
Tab. 4.1.IV's own more-restrictive-to-less-restrictive order) and compared as a `"="` equality —
documented in the step's `nota`.
"""
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import ClasseAperturaFessura, TraveRettangolareInput, TraveRettangolareOutput
from .sle_tensioni import COEFF_SIGMA_C_QUASI_PERMANENTE, COEFF_SIGMA_C_RARA, COEFF_SIGMA_S, HOMOGENISATION_N

KNM_A_NMM = 1_000_000.0  # sle_tensioni.MEDIA_A_STADIO_II_FATTORE
# NTC2018 Tab. 4.1.IV limits di apertura fessura per classe (mm) — review finding (MISLEADING): usati
# al posto dei codici interi 1/2/3 così la formula stampata mostra le etichette w1/w2/w3 e il w_k
# limite in mm, non un confronto di codici opachi.
_WK_LIMITE_MM: dict[ClasseAperturaFessura, float] = {"w1": 0.2, "w2": 0.3, "w3": 0.4}


def traccia_sle(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Traccia:
    """5 o 6 passi: asse neutro parzializzato, 3 Check di tensione, il diametro massimo che
    alimenta la tabella C4.1.II, Check di fessurazione, ed eventualmente il Check di conformità
    della classe di apertura fessura scelta (assente quando la normativa richiede una verifica a
    decompressione anziché un limite di apertura, Tab. 4.1.IV)."""
    passi = (
        _passo_x(inputs, output), _passo_sigma_c_rara(inputs, output), _passo_sigma_s_rara(inputs, output),
        _passo_sigma_c_qp(inputs, output), _passo_diametro_max(inputs, output), _passo_fessurazione(inputs, output),
    )
    classe_normativa = output.fessurazione.classe_normativa
    if classe_normativa is not None:
        passi = (*passi, _passo_classe_conforme(inputs, classe_normativa))
    return Traccia(titolo="Stato limite di esercizio", passi=passi)


def _valori_base(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> tuple[Valore, Valore, Valore]:
    return (
        Valore(simbolo="b", valore=inputs.b_mm, unita="mm", descrizione="base della trave"),
        Valore(simbolo="d", valore=output.flessione.d_mm, unita="mm", descrizione="altezza utile"),
        Valore(simbolo="x", valore=output.sle_tensioni.x_mm, unita="mm", descrizione="profondità dell'asse neutro parzializzato, calcolata sopra"),
    )


def _passo_x(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    return Passo(
        simbolo="x",
        formula="(-n * A_s + sqrt((n * A_s)^2 + 2 * b * n * A_s * d)) / b",
        valori=(
            Valore(simbolo="n", valore=HOMOGENISATION_N, descrizione="coefficiente di omogeneizzazione acciaio-calcestruzzo, n=Es/Ec"),
            Valore(simbolo="A_s", valore=output.armatura.as_o_mm2, unita="mm²", descrizione="armatura tesa presente"),
            Valore(simbolo="b", valore=inputs.b_mm, unita="mm"),
            Valore(simbolo="d", valore=output.flessione.d_mm, unita="mm"),
        ),
        risultato=output.sle_tensioni.x_mm, unita="mm", clausola="NTC2018 §4.1.2.2.5",
        nota="Profondità dell'asse neutro della sezione parzializzata (stadio II), sezione semplicemente armata.",
    )


def _passo_sigma_c_rara(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    sle, fck_MPa = output.sle_tensioni, output.materiali.calcestruzzo.fck_MPa
    soddisfatta = sle.sigma_c_rara_MPa <= sle.limite_sigma_c_rara_MPa
    return Passo(
        simbolo="σ_c,rara",
        formula=f"2 * M_Ed,rara * {KNM_A_NMM:g} / (b * x * (d - x/3)) <= {COEFF_SIGMA_C_RARA:g} * f_ck",
        valori=(
            Valore(simbolo="M_Ed,rara", valore=inputs.med_rara_kNm, unita="kNm", descrizione="momento flettente di esercizio, combinazione rara"),
            *_valori_base(inputs, output),
            Valore(simbolo="f_ck", valore=fck_MPa, unita="MPa"),
        ),
        risultato=sle.sigma_c_rara_MPa, unita="MPa", clausola="NTC2018 §4.1.2.2.5",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Tensione di compressione nel calcestruzzo, combinazione rara.",
    )


def _passo_sigma_s_rara(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    sle = output.sle_tensioni
    fyk_MPa = output.materiali.acciaio.fyk_MPa
    soddisfatta = sle.sigma_s_rara_MPa <= sle.limite_sigma_s_MPa
    return Passo(
        simbolo="σ_s,rara",
        formula=f"M_Ed,rara * {KNM_A_NMM:g} / (A_s * (d - x/3)) <= {COEFF_SIGMA_S:g} * f_yk",
        valori=(
            Valore(simbolo="M_Ed,rara", valore=inputs.med_rara_kNm, unita="kNm"),
            Valore(simbolo="A_s", valore=output.armatura.as_o_mm2, unita="mm²"),
            Valore(simbolo="d", valore=output.flessione.d_mm, unita="mm"),
            Valore(simbolo="x", valore=sle.x_mm, unita="mm"),
            Valore(simbolo="f_yk", valore=fyk_MPa, unita="MPa"),
        ),
        risultato=sle.sigma_s_rara_MPa, unita="MPa", clausola="NTC2018 §4.1.2.2.5",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Tensione di trazione nell'acciaio, combinazione rara.",
    )


def _passo_sigma_c_qp(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    sle, fck_MPa = output.sle_tensioni, output.materiali.calcestruzzo.fck_MPa
    soddisfatta = sle.sigma_c_qp_MPa <= sle.limite_sigma_c_qp_MPa
    return Passo(
        simbolo="σ_c,qp",
        formula=f"2 * M_Ed,qp * {KNM_A_NMM:g} / (b * x * (d - x/3)) <= {COEFF_SIGMA_C_QUASI_PERMANENTE:g} * f_ck",
        valori=(
            Valore(simbolo="M_Ed,qp", valore=inputs.med_qp_kNm, unita="kNm", descrizione="momento flettente di esercizio, combinazione quasi permanente"),
            *_valori_base(inputs, output),
            Valore(simbolo="f_ck", valore=fck_MPa, unita="MPa"),
        ),
        risultato=sle.sigma_c_qp_MPa, unita="MPa", clausola="NTC2018 §4.1.2.2.5",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Tensione di compressione nel calcestruzzo, combinazione quasi permanente.",
    )


def _passo_diametro_max(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    """Review finding (MISSING_STEP): σ_s,limite (Tab. C4.1.II, lettura tabellare, non una formula
    — vedi docstring del modulo) compariva dal nulla; questo passo mostra il diametro massimo delle
    barre tese, uno dei due parametri d'ingresso della tabella insieme alla classe di apertura
    fessura scelta/richiesta (passo successivo)."""
    return Passo(
        simbolo="⌀_max", formula="max(φ_1, φ_2)",
        valori=(
            Valore(simbolo="φ_1", valore=inputs.diametro_ferri1_mm, unita="mm", descrizione="diametro dei ferri tesi, primo strato"),
            Valore(simbolo="φ_2", valore=inputs.diametro_ferri2_mm, unita="mm", descrizione="diametro dei ferri tesi, secondo strato (0 se assente)"),
        ),
        risultato=output.fessurazione.diametro_max_mm, unita="mm",
        nota="Diametro massimo delle barre tese, parametro d'ingresso (con la classe di apertura "
             "fessura) della tabella C4.1.II (Circolare 7/2019) da cui si legge σ_s,limite.",
    )


def _passo_fessurazione(inputs: TraveRettangolareInput, output: TraveRettangolareOutput) -> Passo:
    sle, fessurazione = output.sle_tensioni, output.fessurazione
    frequente = inputs.combinazione == "Frequente"
    simbolo_sigma = "σ_s,rara" if frequente else "σ_s,qp"
    valore_sigma = sle.sigma_s_rara_MPa if frequente else sle.sigma_s_qp_MPa
    soddisfatta = sle.sigma_s_combinazione_MPa <= fessurazione.sigma_limite_MPa
    return Passo(
        simbolo="σ_s",
        formula=f"{simbolo_sigma} <= σ_s,limite",
        valori=(
            Valore(simbolo=simbolo_sigma, valore=valore_sigma, unita="MPa", descrizione="tensione nell'acciaio per la combinazione scelta, calcolata sopra"),
            Valore(simbolo="σ_s,limite", valore=fessurazione.sigma_limite_MPa, unita="MPa", descrizione="limite tabellare NTC2018 Tab. C4.1.II per il diametro massimo delle barre tese"),
        ),
        risultato=sle.sigma_s_combinazione_MPa, unita="MPa", clausola="NTC2018 §4.1.2.2.4 / Circolare 7/2019 C4.1.2.2.4.5",
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota="Controllo indiretto dell'ampiezza di fessura, senza calcolo diretto di w.",
    )


def _passo_classe_conforme(inputs: TraveRettangolareInput, classe_normativa: ClasseAperturaFessura) -> Passo:
    """Formula/identifiers use the class LABELS themselves (`w1`/`w2`/`w3`, grammar-legal
    identifiers) rather than opaque integer codes, and the compared VALUE is the actual w_k limit
    in mm (NTC2018 Tab. 4.1.IV), not an internal code — review finding (MISLEADING): the printed
    row used to read "3 = 3", never showing which class was meant nor its w_k limit."""
    scelta, normativa = inputs.classe_apertura_fessura, classe_normativa
    wk_scelta_mm, wk_normativa_mm = _WK_LIMITE_MM[scelta], _WK_LIMITE_MM[normativa]
    valori = {
        scelta: Valore(simbolo=scelta, valore=wk_scelta_mm, unita="mm", descrizione="classe scelta, limite w_k"),
        normativa: Valore(simbolo=normativa, valore=wk_normativa_mm, unita="mm", descrizione="classe richiesta dalla normativa, limite w_k"),
    }
    return Passo(
        simbolo="classe apertura fessura",
        formula=f"{scelta} = {normativa}",
        valori=tuple(valori.values()),
        risultato=wk_scelta_mm, unita="mm", clausola="NTC2018 Tab. 4.1.IV",
        esito="soddisfatta" if scelta == normativa else "non soddisfatta",
        nota="La classe di apertura di fessura scelta deve coincidere con quella richiesta dalla normativa per esposizione, combinazione e sensibilità dell'armatura.",
    )
