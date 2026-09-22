"""Composed tool: pilastro-rettangolare — verifica di pilastro in c.a. rettangolare/quadrato in
CD "B" (NTC2018 + Circolare 7/2019, EC2 or NTC2008 per `inputs.norma`). `run` only composes the
step modules; norm-specific parameters come from `regole.resolve` (architecture-batch2.md §3).

I passi di calcolo veri e propri vivono in `esecuzione_rettangolare.py` e `dettagli_rettangolare.py`
(estratti per la regola dura 12 di CLAUDE.md, moduli/funzioni piccoli). `_dettagli` resta importabile
da qui (usato da tests/members/ca_pilastri/test_fixed_behaviour.py) e `disegna_schizzo` resta una
chiamata diretta in questo modulo così i test possono fare il monkeypatch dell'attributo di modulo."""
import logging

from strutture.shared.report import Report, success

from .dettagli_rettangolare import _dettagli  # noqa: F401 — re-esportata per i test
from .esecuzione_rettangolare import calcola_nucleo_rettangolare
from .materiali import proprieta_materiali
from .models import PilastroOutput, PilastroRettangolareInput
from .regole import resolve
from .schizzo import disegna_rettangolare as disegna_schizzo

logger = logging.getLogger(__name__)


def run_pilastro_rettangolare(inputs: PilastroRettangolareInput) -> Report[PilastroOutput]:
    rules = resolve(inputs.norma, inputs.legacy_compat)
    materiali = proprieta_materiali(inputs.acciaio, inputs.cls, legacy_compat=inputs.legacy_compat)
    nucleo = calcola_nucleo_rettangolare(inputs, rules, materiali)

    try:
        schizzo = disegna_schizzo(inputs)
    except Exception:
        logger.exception("errore nel disegno dello schizzo per pilastro-rettangolare")
        schizzo = None

    output = PilastroOutput(
        materiali=materiali, geometria=nucleo.geometria, armatura_minima=nucleo.armatura_minima,
        taglio=nucleo.taglio, flessione=nucleo.flessione, compressione=nucleo.compressione,
        confinamento=nucleo.confinamento, snellezza=nucleo.snellezza, dettagli=nucleo.dettagli,
        regole=nucleo.regole, schizzo=schizzo,
    )
    return success(output, inputs, checks=nucleo.checks)
