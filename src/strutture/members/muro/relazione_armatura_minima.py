"""Verified restatement (docs/architecture-phase2.md) of `armatura_minima.py`: the three steps that
close each reinforcement section — A_s,min (NTC2018 §4.1.6.1.1), the design area the bars are
chosen for, and the check that the bars laid out cover the minimum. Shared by the stem, toe and
heel traces (`suffisso` keeps the symbols distinct within one report)."""
from strutture.shared.materials.concrete import concrete_properties
from strutture.shared.materials.rebar import rebar_properties
from strutture.shared.relazione import Passo, Valore

from .armatura_minima import LARGHEZZA_STRISCIA_MM, RAPPORTO_FCTM_FYK, RAPPORTO_MINIMO_ASSOLUTO, area_disposta_cm2_m
from .models import MuroSostegnoInput

CLAUSE_ARMATURA_MINIMA = "NTC2018 §4.1.6.1.1 / EN 1992-1-1 §9.2.1.1"


def passi_armatura_minima(inputs: MuroSostegnoInput, risultato, *, d_m: float, suffisso: str) -> tuple[Passo, Passo, Passo]:
    fctm = concrete_properties(inputs.tipo_cls).fctm_MPa
    fyk = rebar_properties(inputs.grado_acciaio).fyk_MPa
    disposta = area_disposta_cm2_m(diametro_mm=risultato.diametro_mm, passo_m=risultato.passo_m)
    minimo = Passo(
        simbolo=f"A_s,min ({suffisso})",
        formula=f"max({RAPPORTO_FCTM_FYK} * f_ctm / f_yk, {RAPPORTO_MINIMO_ASSOLUTO}) * b * d * 1000 / 100",
        valori=(
            Valore(simbolo="f_ctm", valore=fctm, unita="MPa", descrizione=f"resistenza media a trazione del calcestruzzo {inputs.tipo_cls}"),
            Valore(simbolo="f_yk", valore=fyk, unita="MPa", descrizione="tensione caratteristica di snervamento dell'acciaio"),
            Valore(simbolo="b", valore=LARGHEZZA_STRISCIA_MM, unita="mm", descrizione="larghezza della striscia di calcolo, 1 m di muro"),
            Valore(simbolo="d", valore=d_m, unita="m", descrizione="altezza utile, derivata sopra"),
        ),
        risultato=risultato.as_min_cm2_m, unita="cm2/m", clausola=CLAUSE_ARMATURA_MINIMA,
        nota="Armatura minima per metro di muro; il foglio non la considerava (registro: muro-sostegno/armatura-senza-minimo-normativo).",
    )
    progetto = Passo(
        simbolo=f"A_s,prog ({suffisso})", formula="max(A_s,nec, A_s,min)",
        valori=(
            Valore(simbolo="A_s,nec", valore=max(0.0, risultato.as_nec_cm2_m), unita="cm2/m", descrizione="area necessaria a flessione, governante fra le combinazioni (non negativa)"),
            Valore(simbolo="A_s,min", valore=risultato.as_min_cm2_m, unita="cm2/m", descrizione="armatura minima, derivata sopra"),
        ),
        risultato=risultato.as_progetto_cm2_m, unita="cm2/m", clausola=CLAUSE_ARMATURA_MINIMA,
        nota=f"Area per la scelta delle barre: {risultato.callout}.",
    )
    verifica = Passo(
        simbolo=f"A_s,disp ({suffisso})", formula="π * φ^2 / 4 / s / 100 >= A_s,min",
        valori=(
            Valore(simbolo="π", valore=3.141592653589793),
            Valore(simbolo="φ", valore=risultato.diametro_mm, unita="mm", descrizione="diametro della barra scelta"),
            Valore(simbolo="s", valore=risultato.passo_m, unita="m", descrizione="passo delle barre"),
            Valore(simbolo="A_s,min", valore=risultato.as_min_cm2_m, unita="cm2/m"),
        ),
        risultato=disposta, unita="cm2/m", clausola=CLAUSE_ARMATURA_MINIMA,
        esito="soddisfatta" if disposta + 1e-9 >= risultato.as_min_cm2_m else "non soddisfatta",
    )
    return minimo, progetto, verifica
