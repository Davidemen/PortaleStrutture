"""Tool registration: neve-carico-falda (NTC2018 §3.4) and neve-accumulo (Circ. §C3.4.5.6)."""
import logging

from strutture.shared.comuni import AmbiguousComuneError, KeyNotFound
from strutture.shared.divergences import legacy
from strutture.shared.report import CalcError, Report, success
from strutture.shared.tool import Tool

from .accumulo_ls import lunghezza_accumulo
from .accumulo_m1 import m1_finale
from .accumulo_ms import mu_s
from .accumulo_mw import mu_w, mu_w_grezzo, rapporto_gamma_h_qsk
from .esposizione import coefficiente_esposizione
from .forma_falda import coefficiente_forma
from .location import resolve_comune, zona_from_provincia_bug
from .models import AccumuloInput, AccumuloOutput, CaricoFaldaInput, CaricoFaldaOutput
from .qsk import qsk_accumulo, qsk_falda
from .schizzo import disegna_accumulo as disegna_schizzo_accumulo
from .schizzo import disegna_carico_falda as disegna_schizzo_falda

logger = logging.getLogger(__name__)


def _location_error(comune: str, error: Exception) -> CalcError:
    return CalcError(f"Comune {comune!r} non trovato o ambiguo: {error}")


def run_carico_falda(inputs: CaricoFaldaInput) -> Report[CaricoFaldaOutput]:
    provincia: str | None = None
    regione: str | None = None
    zona = inputs.zona
    if inputs.comune is not None:
        try:
            comune = resolve_comune(inputs.comune)
        except (KeyNotFound, AmbiguousComuneError) as error:
            raise _location_error(inputs.comune, error) from error
        provincia, regione, zona = comune.provincia, comune.regione, comune.zona_neve

    qsk = qsk_falda(zona, inputs.as_m, legacy_compat=inputs.legacy_compat)
    ce = coefficiente_esposizione(inputs.topografia)

    mu = qs = None
    if inputs.a is not None and inputs.parapetto is not None:
        mu = coefficiente_forma(inputs.a, inputs.parapetto == "SI", legacy_compat=inputs.legacy_compat)
        qs = qsk * ce * inputs.ct * mu

    mu1 = qs1 = mu2 = qs2 = None
    if None not in (inputs.a1, inputs.parapetto1, inputs.a2, inputs.parapetto2):
        mu1 = coefficiente_forma(inputs.a1, inputs.parapetto1 == "SI", legacy_compat=inputs.legacy_compat)
        mu2 = coefficiente_forma(inputs.a2, inputs.parapetto2 == "SI", legacy_compat=inputs.legacy_compat)
        qs1 = qsk * ce * inputs.ct * mu1
        qs2 = qsk * ce * inputs.ct * mu2

    tipo_copertura_ignorato = legacy("neve/tipo-copertura-non-filtra-output", inputs.legacy_compat)
    show_una_falda = tipo_copertura_ignorato or inputs.tipo_copertura == "Copertura ad una falda"
    show_due_falde = tipo_copertura_ignorato or inputs.tipo_copertura == "Copertura a due falde"

    campi = {
        "provincia": provincia,
        "regione": regione,
        "zona": zona,
        "qsk": qsk,
        "ce": ce,
        "mu": mu if show_una_falda else None,
        "qs": qs if show_una_falda else None,
        "mu1": mu1 if show_due_falde else None,
        "qs1": qs1 if show_due_falde else None,
        "mu2": mu2 if show_due_falde else None,
        "qs2": qs2 if show_due_falde else None,
    }
    try:
        schizzo = disegna_schizzo_falda(inputs, CaricoFaldaOutput(**campi))
    except Exception:
        logger.exception("errore nel disegno dello schizzo per neve-carico-falda")
        schizzo = None
    data = CaricoFaldaOutput(**campi, schizzo=schizzo)
    return success(data, inputs)


def _resolve_accumulo_zona(inputs: AccumuloInput) -> str:
    """`Neve accumulo!H8`: comune lookup (fixed) or Bug 2's provincia-keyed lookup (legacy)."""
    if inputs.comune is None:
        return inputs.zona
    try:
        comune = resolve_comune(inputs.comune)
    except (KeyNotFound, AmbiguousComuneError) as error:
        raise _location_error(inputs.comune, error) from error
    if not legacy("neve/zona-lookup-su-provincia-invece-che-comune", inputs.legacy_compat):
        return comune.zona_neve
    try:
        return zona_from_provincia_bug(comune.provincia)
    except KeyNotFound as error:
        raise CalcError(str(error)) from error


def run_accumulo(inputs: AccumuloInput) -> Report[AccumuloOutput]:
    zona = _resolve_accumulo_zona(inputs)
    qsk = qsk_accumulo(
        zona, inputs.as_m, legacy_compat=inputs.legacy_compat, neve_altitude_m=inputs.neve_sheet_as_m
    )
    ce = coefficiente_esposizione(inputs.topografia)

    ls = lunghezza_accumulo(inputs.h)
    gamma_h_over_qsk = rapporto_gamma_h_qsk(inputs.gamma, inputs.h, qsk)
    mw_raw = mu_w_grezzo(inputs.b1, inputs.b2, inputs.h, gamma_h_over_qsk)
    mw = mu_w(mw_raw)
    ms = mu_s(inputs.a, inputs.msup)
    m2 = ms + mw
    m1_final = m1_finale(inputs.b2, ls, mw, inputs.m1_input, legacy_compat=inputs.legacy_compat)

    campi = {
        "zona": zona,
        "qsk": qsk,
        "ce": ce,
        "ls": ls,
        "mw": mw,
        "ms": ms,
        "m2": m2,
        "m1_final": m1_final,
        "m2_final": m2,
        "ls_final": ls,
        "qs1_final": qsk * ce * inputs.ct * m1_final,
        "qs2_final": qsk * ce * inputs.ct * m2,
    }
    try:
        schizzo = disegna_schizzo_accumulo(inputs, AccumuloOutput(**campi))
    except Exception:
        logger.exception("errore nel disegno dello schizzo per neve-accumulo")
        schizzo = None
    data = AccumuloOutput(**campi, schizzo=schizzo)
    return success(data, inputs)


TOOLS = (
    Tool(
        name="neve-carico-falda",
        title="Carico neve su copertura (una/due falde)",
        group="Carichi / Neve",
        norm="NTC2018 §3.4",
        input_model=CaricoFaldaInput,
        output_model=CaricoFaldaOutput,
        run=run_carico_falda,
        summary="Calcola il carico neve di progetto su una copertura a una o due falde.",
        example={
            "comune": "Mapello",
            "as_m": 250,
            "topografia": "Normale",
            "ct": 1,
            "tipo_copertura": "Copertura ad una falda",
            "a": 0,
            "parapetto": "NO",
            "a1": 35,
            "parapetto1": "NO",
            "a2": 50,
            "parapetto2": "NO",
        },
    ),
    Tool(
        name="neve-accumulo",
        title="Accumulo neve su coperture adiacenti a costruzioni più alte",
        group="Carichi / Neve",
        norm="Circ. NTC2018 §C3.4.5.6",
        input_model=AccumuloInput,
        output_model=AccumuloOutput,
        run=run_accumulo,
        summary="Calcola l'accumulo di neve sulla copertura più bassa addossata a un edificio più alto.",
        example={
            "comune": "Bergamo",
            "as_m": 249,
            "topografia": "Normale",
            "ct": 1,
            "b1": 43.15,
            "b2": 36.2,
            "h": 10,
            "gamma": 2,
            "a": 0,
            "m1_input": 0.8,
            "msup": 0.45,
        },
    ),
)
