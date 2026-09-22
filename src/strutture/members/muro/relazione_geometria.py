"""Verified restatement (docs/architecture-phase2.md) of `geometria.py` (the simple, non-composite
terms only: H, B and the backfill-wedge area/centroid a_terr/x_terr/z_terr — plain sums a reader
can check by eye) and `mononobe_okabe.coefficienti_sismici` (kh/kv/θ, NTC2018 §7.11.6.2.1). The
wall's OWN area/centroid (a_muro/x_muro/z_muro, `GeometriaResult`) is a composite of three
sub-areas (footing rectangle + stem rectangle + stem taper) and is cited directly wherever it is
needed (`relazione_spinta.py`) rather than restated here: EN1997-1 Annex D's table-lookup
precedent of `ca_travi.relazione_sle` applies equally to a multi-term composite geometry formula
that would not fit this Traccia's scope.

kh/kv/θ are shown once, for SISMA_1 (segno_kv=+1): SISMA_2 uses the identical kh with kv=-0.5·kh
(sign flip only, see `nota`) — `relazione_spinta.py`'s own Traccia re-derives kv/θ for whichever of
the two actually governs (segno included, review finding MISSING_STEP: a bare citation of this
Traccia's SISMA_1-only kv/θ was silently wrong whenever SISMA_2 governed)."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import MuroSostegnoInput, MuroSostegnoOutput
from .relazione_comune import trova_spinta


def traccia_geometria(inputs: MuroSostegnoInput, output: MuroSostegnoOutput) -> Traccia:
    """8 passi: H, B, S, coefficienti sismici kh/kv/θ (SISMA_1), area/baricentro del cuneo di
    terreno a tergo (a_terr, x_terr, z_terr)."""
    return Traccia(
        titolo="Geometria e parametri sismici",
        passi=(
            _passo_h(inputs, output), _passo_b(inputs, output), _passo_s(output),
            _passo_kh(inputs, output), _passo_kv(inputs, output), _passo_theta(inputs, output),
            _passo_a_terr(inputs, output), _passo_x_terr(inputs, output), _passo_z_terr(inputs, output),
        ),
    )


def _passo_h(inputs: MuroSostegnoInput, output: MuroSostegnoOutput) -> Passo:
    return Passo(
        simbolo="H", formula="h_muro + s_fond",
        valori=(
            Valore(simbolo="h_muro", valore=inputs.h_muro_m, unita="m", descrizione="altezza del muro fuori terra"),
            Valore(simbolo="s_fond", valore=inputs.s_fond_m, unita="m", descrizione="spessore della fondazione"),
        ),
        risultato=output.geometria.h_muro_tot_m, unita="m",
        nota="Altezza totale del muro (fusto + fondazione), usata da spinta, momenti e bracci di leva.",
    )


def _passo_b(inputs: MuroSostegnoInput, output: MuroSostegnoOutput) -> Passo:
    return Passo(
        simbolo="B", formula="b_valle + s_base + b_monte",
        valori=(
            Valore(simbolo="b_valle", valore=inputs.b_valle_m, unita="m", descrizione="larghezza della fondazione lato valle (mancia)"),
            Valore(simbolo="s_base", valore=inputs.s_base_m, unita="m", descrizione="spessore del muro alla base"),
            Valore(simbolo="b_monte", valore=inputs.b_monte_m, unita="m", descrizione="larghezza della fondazione lato monte (tacco)"),
        ),
        risultato=output.geometria.b_fond_m, unita="m",
        nota="Larghezza totale della fondazione.",
    )


def _passo_s(output: MuroSostegnoOutput) -> Passo:
    sismici = output.parametri_sismici
    return Passo(
        simbolo="S", formula="S_S * S_T",
        valori=(
            Valore(simbolo="S_S", valore=sismici.ss, descrizione="coefficiente di amplificazione stratigrafica, NTC2018 Tab. 3.2.IV, funzione di categoria sottosuolo/F0/ag"),
            Valore(simbolo="S_T", valore=sismici.st, descrizione="coefficiente di amplificazione topografica, NTC2018 Tab. 3.2.V, funzione di categoria topografica"),
        ),
        risultato=sismici.s, unita="-", clausola="NTC2018 §3.2.3.2.1",
        nota="Coefficiente che tiene conto della categoria di sottosuolo e della topografia.",
    )


def _passo_kh(inputs: MuroSostegnoInput, output: MuroSostegnoOutput) -> Passo:
    sisma1 = trova_spinta(output, "SISMA_1")
    return Passo(
        simbolo="k_h", formula="S * a_g * β_m",
        valori=(
            Valore(simbolo="S", valore=output.parametri_sismici.s, descrizione="coefficiente di amplificazione del suolo, derivato sopra"),
            Valore(simbolo="a_g", valore=inputs.ag_g, unita="g", descrizione="accelerazione orizzontale massima al sito"),
            Valore(simbolo="β_m", valore=inputs.beta_m, descrizione="fattore di riduzione dell'accelerazione massima attesa al sito"),
        ),
        risultato=sisma1.kh, unita="-", clausola="NTC2018 §7.11.6.2.1",
        nota="Coefficiente sismico orizzontale, uguale per SISMA_1 e SISMA_2.",
    )


def _passo_kv(inputs: MuroSostegnoInput, output: MuroSostegnoOutput) -> Passo:
    sisma1 = trova_spinta(output, "SISMA_1")
    return Passo(
        simbolo="k_v", formula="0.5 * k_h",
        valori=(Valore(simbolo="k_h", valore=sisma1.kh, descrizione="coefficiente sismico orizzontale, derivato sopra"),),
        risultato=sisma1.kv, unita="-", clausola="NTC2018 §7.11.6.2.1",
        nota="Per SISMA_1 (mostrato qui); SISMA_2 usa lo stesso k_h con k_v = −0.5·k_h.",
    )


def _passo_theta(inputs: MuroSostegnoInput, output: MuroSostegnoOutput) -> Passo:
    sisma1 = trova_spinta(output, "SISMA_1")
    return Passo(
        simbolo="θ", formula="atan(k_h / (1 + k_v))",
        valori=(
            Valore(simbolo="k_h", valore=sisma1.kh, descrizione="coefficiente sismico orizzontale, derivato sopra"),
            Valore(simbolo="k_v", valore=sisma1.kv, descrizione="coefficiente sismico verticale, derivato sopra"),
        ),
        risultato=sisma1.theta_rad, unita="rad", clausola="NTC2018 §7.11.6.2.1",
        nota="Angolo che entra nel coefficiente di spinta attiva sismica di Mononobe-Okabe.",
    )


def _passo_a_terr(inputs: MuroSostegnoInput, output: MuroSostegnoOutput) -> Passo:
    return Passo(
        simbolo="A_terr", formula="b_monte * h_muro",
        valori=(
            Valore(simbolo="b_monte", valore=inputs.b_monte_m, unita="m"),
            Valore(simbolo="h_muro", valore=inputs.h_muro_m, unita="m"),
        ),
        risultato=output.geometria.a_terr_m2, unita="m2",
        nota="Area della sezione trasversale del cuneo di terreno a tergo del muro.",
    )


def _passo_x_terr(inputs: MuroSostegnoInput, output: MuroSostegnoOutput) -> Passo:
    return Passo(
        simbolo="x_terr", formula="b_valle + s_base + b_monte / 2",
        valori=(
            Valore(simbolo="b_valle", valore=inputs.b_valle_m, unita="m"),
            Valore(simbolo="s_base", valore=inputs.s_base_m, unita="m"),
            Valore(simbolo="b_monte", valore=inputs.b_monte_m, unita="m"),
        ),
        risultato=output.geometria.x_terr_m, unita="m",
        nota="Baricentro del cuneo di terreno dal polo di ribaltamento (punta valle).",
    )


def _passo_z_terr(inputs: MuroSostegnoInput, output: MuroSostegnoOutput) -> Passo:
    return Passo(
        simbolo="z_terr", formula="s_fond + h_muro / 2",
        valori=(
            Valore(simbolo="s_fond", valore=inputs.s_fond_m, unita="m"),
            Valore(simbolo="h_muro", valore=inputs.h_muro_m, unita="m"),
        ),
        risultato=output.geometria.z_terr_m, unita="m",
        nota="Baricentro del cuneo di terreno dalla base della fondazione (braccio verticale per l'inerzia sismica).",
    )
