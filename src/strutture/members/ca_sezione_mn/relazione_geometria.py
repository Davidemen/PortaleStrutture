"""Verified restatement of `ca-sezione-dominio-mn`'s materials (`sezione_builder.py`, NTC2018
§4.1.2.1.1.1), section-geometry summary (`geometria_riepilogo.py`) and axial-capacity extremes
(`shared.sezione_ca.domini.intervallo_n`) steps of docs/architecture-phase2.md §6 wave 2/3.

`A_c` has a closed form ONLY for the two shapes an engineer would size by hand (rectangle, b·h;
circle, π·D²/4): every other `forma` (T/L, wall, free polygon) integrates the contour vertices
(`shared.sezione_ca.geometria.area`, the shoelace formula) — no single formula to restate, so it
is a bare-identifier lookup `Passo` for those shapes, per §6's lookup rule. `A_s` is always the sum
of the individual bar areas (table or parametric layout): also a bare-identifier `Passo`, for the
same reason. `N_max`/`N_min` are the domain's angle-independent extremes
(`stati_ultimi.py`'s own docstring: "N = fcd·(Ac−As) + fyd·As exactly" / "N = -fyd·As exactly" —
concrete net of the steel it displaces, steel at full design strength): NOT exposed by
`SezioneMnOutput` (the domain point clouds are a chart, not this trace, per §6), so they are
recomputed here from the tool's own `sezione_builder.costruisci_sezione` and
`shared.sezione_ca.domini.intervallo_n`, exactly as the architecture brief allows for a value the
output does not expose."""
import math

from strutture.shared.materials.concrete import ALPHA_CC, GAMMA_C
from strutture.shared.materials.rebar import GAMMA_S
from strutture.shared.relazione import Passo, Traccia, Valore
from strutture.shared.sezione_ca.domini import intervallo_n
from strutture.shared.sezione_ca.modelli import MaterialiSezione, Sezione

from .models_input import SezioneMnInput
from .models_output import GeometriaOutput

CLAUSOLA_MATERIALI = "NTC2018 §4.1.2.1.1.1"
CLAUSOLA_DOMINIO = "NTC2018 §4.1.2.3.4.2"


def traccia_materiali(inputs: SezioneMnInput, materiali: MaterialiSezione) -> Traccia:
    """4 passi: f_ck (lookup), f_cd, f_yk (lookup), f_yd."""
    cls, acc = materiali.calcestruzzo, materiali.acciaio
    return Traccia(
        titolo="Materiali",
        passi=(
            _passo_lookup("f_ck", cls.fck_MPa, "MPa", f"NTC2018 Tab. 4.1.I per la classe {inputs.classe_calcestruzzo}"),
            _passo_fcd(cls.fck_MPa, cls.fcd_MPa),
            _passo_lookup("f_yk", acc.fyk_MPa, "MPa", f"NTC2018 Tab. 11.3.Ia per il grado {inputs.grado_acciaio}"),
            _passo_fyd(acc.fyk_MPa, acc.fyd_MPa),
        ),
    )


def _passo_lookup(simbolo: str, valore: float, unita: str, fonte: str) -> Passo:
    return Passo(
        simbolo=simbolo, formula=simbolo,
        valori=(Valore(simbolo=simbolo, valore=valore, unita=unita, descrizione=fonte),),
        risultato=valore, unita=unita, nota=f"Lettura tabellare: {fonte}.",
    )


def _passo_fcd(fck_MPa: float, fcd_MPa: float) -> Passo:
    return Passo(
        simbolo="f_cd", formula=f"{ALPHA_CC:g} * f_ck / γ_c",
        valori=(
            Valore(simbolo="f_ck", valore=fck_MPa, unita="MPa", descrizione="resistenza cilindrica caratteristica, calcolata sopra"),
            Valore(simbolo="γ_c", valore=GAMMA_C, descrizione="coefficiente parziale del calcestruzzo, Tab. 4.1.V"),
        ),
        risultato=fcd_MPa, unita="MPa", clausola=CLAUSOLA_MATERIALI, nota="Resistenza di calcolo a compressione del calcestruzzo.",
    )


def _passo_fyd(fyk_MPa: float, fyd_MPa: float) -> Passo:
    return Passo(
        simbolo="f_yd", formula="f_yk / γ_s",
        valori=(
            Valore(simbolo="f_yk", valore=fyk_MPa, unita="MPa", descrizione="tensione caratteristica di snervamento, calcolata sopra"),
            Valore(simbolo="γ_s", valore=GAMMA_S, descrizione="coefficiente parziale dell'acciaio, Tab. 4.1.V"),
        ),
        risultato=fyd_MPa, unita="MPa", clausola=CLAUSOLA_MATERIALI, nota="Tensione di calcolo di snervamento dell'acciaio.",
    )


def traccia_geometria(inputs: SezioneMnInput, geometria: GeometriaOutput) -> Traccia:
    """3 passi: A_c (formula chiusa solo per rettangolo/cerchio), A_s (somma delle barre), ρ."""
    return Traccia(
        titolo="Geometria della sezione",
        passi=(_passo_ac(inputs, geometria.ac_mm2), _passo_as(geometria.as_mm2, geometria.n_barre), _passo_rho(geometria)),
    )


def _passo_ac(inputs: SezioneMnInput, ac_mm2: float) -> Passo:
    if inputs.forma == "rettangolare" and inputs.b_mm is not None and inputs.h_mm is not None:
        return Passo(
            simbolo="A_c", formula="b * h",
            valori=(
                Valore(simbolo="b", valore=inputs.b_mm, unita="mm", descrizione="base della sezione rettangolare"),
                Valore(simbolo="h", valore=inputs.h_mm, unita="mm", descrizione="altezza della sezione rettangolare"),
            ),
            risultato=ac_mm2, unita="mm2", nota="Area lorda di calcestruzzo, sezione rettangolare.",
        )
    if inputs.forma == "circolare" and inputs.diametro_mm is not None:
        return Passo(
            simbolo="A_c", formula="π/4 * D^2",
            valori=(
                Valore(simbolo="D", valore=inputs.diametro_mm, unita="mm", descrizione="diametro della sezione circolare"),
                Valore(simbolo="π", valore=math.pi, descrizione="pi greco"),
            ),
            risultato=ac_mm2, unita="mm2", nota="Area lorda di calcestruzzo, sezione circolare.",
        )
    return Passo(
        simbolo="A_c", formula="A_c",
        valori=(Valore(simbolo="A_c", valore=ac_mm2, unita="mm2", descrizione=f"area del poligono di contorno, forma '{inputs.forma}'"),),
        risultato=ac_mm2, unita="mm2",
        nota="Area lorda di calcestruzzo: integrale del poligono di contorno (formula del "
             "capoverso, non un'espressione chiusa in funzione di poche dimensioni per questa forma).",
    )


def _passo_as(as_mm2: float, n_barre: int) -> Passo:
    return Passo(
        simbolo="A_s", formula="A_s",
        valori=(Valore(simbolo="A_s", valore=as_mm2, unita="mm2", descrizione=f"somma delle aree delle {n_barre} barre d'armatura presenti"),),
        risultato=as_mm2, unita="mm2", nota="Area totale dell'armatura longitudinale, somma delle singole barre (tabella o layout parametrico).",
    )


def _passo_rho(geometria: GeometriaOutput) -> Passo:
    return Passo(
        simbolo="ρ", formula="A_s / A_c",
        valori=(
            Valore(simbolo="A_s", valore=geometria.as_mm2, unita="mm2", descrizione="armatura longitudinale, calcolata sopra"),
            Valore(simbolo="A_c", valore=geometria.ac_mm2, unita="mm2", descrizione="area lorda di calcestruzzo, calcolata sopra"),
        ),
        risultato=geometria.rho, unita="-", nota="Rapporto geometrico di armatura.",
    )


def traccia_dominio_assiale(materiali: MaterialiSezione, geometria: GeometriaOutput, sezione: Sezione) -> Traccia:
    """2 passi: N_max, N_min — estremi assiali del dominio di resistenza (angolo-indipendenti)."""
    n_min_kN, n_max_kN = intervallo_n(sezione)
    return Traccia(
        titolo="Estremi assiali del dominio di resistenza",
        passi=(_passo_n_max(materiali, geometria, n_max_kN), _passo_n_min(materiali, geometria, n_min_kN)),
    )


def _passo_n_max(materiali: MaterialiSezione, geometria: GeometriaOutput, n_max_kN: float) -> Passo:
    return Passo(
        simbolo="N_max", formula="f_cd * (A_c - A_s) + f_yd * A_s",
        valori=(
            Valore(simbolo="f_cd", valore=materiali.calcestruzzo.fcd_MPa, unita="MPa", descrizione="resistenza di calcolo del calcestruzzo, calcolata sopra"),
            Valore(simbolo="A_c", valore=geometria.ac_mm2, unita="mm2", descrizione="area lorda, calcolata sopra"),
            Valore(simbolo="A_s", valore=geometria.as_mm2, unita="mm2", descrizione="armatura longitudinale, calcolata sopra"),
            Valore(simbolo="f_yd", valore=materiali.acciaio.fyd_MPa, unita="MPa", descrizione="tensione di calcolo di snervamento, calcolata sopra"),
        ),
        risultato=n_max_kN, unita="kN", scala=1e-3, clausola=CLAUSOLA_DOMINIO,
        nota="Compressione centrata pura: calcestruzzo sull'area netta (al lordo dell'armatura) a f_cd, armatura interamente snervata in compressione.",
    )


def _passo_n_min(materiali: MaterialiSezione, geometria: GeometriaOutput, n_min_kN: float) -> Passo:
    return Passo(
        simbolo="N_min", formula="-f_yd * A_s",
        valori=(
            Valore(simbolo="f_yd", valore=materiali.acciaio.fyd_MPa, unita="MPa", descrizione="tensione di calcolo di snervamento, calcolata sopra"),
            Valore(simbolo="A_s", valore=geometria.as_mm2, unita="mm2", descrizione="armatura longitudinale, calcolata sopra"),
        ),
        risultato=n_min_kN, unita="kN", scala=1e-3, clausola=CLAUSOLA_DOMINIO,
        nota="Trazione centrata pura: calcestruzzo reagente trascurato, armatura interamente snervata in trazione.",
    )
