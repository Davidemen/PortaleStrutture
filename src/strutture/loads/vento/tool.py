"""Tool registration: vento-pressione. NTC2018 §3.3 / Circ. NTC2019 C3.3.2."""
from strutture.shared.report import Report, success
from strutture.shared.tool import Tool

from .comune_zona import risolvi_zona
from .costanti import ALTITUDE_WARNING_THRESHOLD_M, MAX_SEZIONI_SENZA_AVVISO
from .esposizione import coefficiente_esposizione
from .models import VentoPressioneInput, VentoPressioneOutput
from .periodo_ritorno import coefficiente_periodo_ritorno, velocita_riferimento
from .pressione_cinetica import pressione_cinetica_riferimento
from .profilo import profilo_pressione
from .tables import categoria_parametri, zona_parametri
from .vref import velocita_riferimento_suolo


def _warnings(inputs: VentoPressioneInput) -> tuple[str, ...]:
    warnings: tuple[str, ...] = ()
    if inputs.legacy_compat and inputs.altitudine_m > ALTITUDE_WARNING_THRESHOLD_M:
        # In legacy_compat il foglio si limita ad avvisare (Vento!L8): oltre questa soglia, in modalità
        # standard (legacy_compat=False) il calcolo di ca solleva invece un CalcError (§3.3.2, vref.py).
        messaggio = (
            f"Altitudine > {ALTITUDE_WARNING_THRESHOLD_M:.0f} m: sono necessarie analisi approfondite "
            "comprovate da apposita documentazione (§3.3.1)."
        )
        warnings = (*warnings, messaggio)
    if inputs.n_sezioni > MAX_SEZIONI_SENZA_AVVISO:
        messaggio = (
            f"Numero di sezioni del profilo > {MAX_SEZIONI_SENZA_AVVISO}: risoluzione superiore a quella "
            "del foglio originale (Tabelle!N1)."
        )
        warnings = (*warnings, messaggio)
    return warnings


def run(inputs: VentoPressioneInput) -> Report[VentoPressioneOutput]:
    zona, comune = risolvi_zona(inputs.zona, inputs.comune, inputs.provincia, inputs.legacy_compat)
    vb0, a0, ka, ks = zona_parametri(zona)
    kr, z0, zmin = categoria_parametri(inputs.categoria_esposizione)

    vref, ca = velocita_riferimento_suolo(vb0, ka, ks, a0, inputs.altitudine_m, inputs.legacy_compat)
    a_r = coefficiente_periodo_ritorno(inputs.periodo_ritorno_anni)
    vr = velocita_riferimento(vref, inputs.periodo_ritorno_anni, inputs.legacy_compat)
    qb = pressione_cinetica_riferimento(vr)
    ce_h = coefficiente_esposizione(inputs.altezza_edificio_m, kr, z0, zmin, inputs.ct)
    profilo = profilo_pressione(inputs.altezza_edificio_m, inputs.n_sezioni, qb, kr, z0, zmin, inputs.ct)

    data = VentoPressioneOutput(
        regione=comune.regione if comune else None,
        provincia=comune.provincia if comune else None,
        zona=zona,
        vb0=vb0,
        a0=a0,
        ka=ka,
        ks=ks,
        ca=ca,
        vref=vref,
        a_r=a_r,
        vr=vr,
        kr=kr,
        z0=z0,
        zmin=zmin,
        qb=qb,
        ce_h=ce_h,
        p_h_kNm2=qb * ce_h,
        profilo=profilo,
    )
    return success(data, inputs, warnings=_warnings(inputs))


TOOLS = (
    Tool(
        name="vento-pressione",
        title="Pressione del vento",
        group="Carichi / Vento",
        norm="NTC2018 §3.3 / Circ. NTC2019 C3.3.2",
        input_model=VentoPressioneInput,
        output_model=VentoPressioneOutput,
        run=run,
        example={
            "comune": "Milano",
            "altitudine_m": 120,
            "periodo_ritorno_anni": 50,
            "categoria_esposizione": "II",
            "ct": 1,
            "altezza_edificio_m": 60,
            "n_sezioni": 1000,
        },
        summary="Calcola la velocità e la pressione cinetica di riferimento del vento e il coefficiente di esposizione, restituendo il profilo di pressione lungo l'altezza dell'edificio.",
    ),
)
