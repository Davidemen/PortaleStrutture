"""Composed tool: pilastro-circolare — verifica di pilastro in c.a. circolare in CD "B" (NTC2018 +
Circolare 7/2019, EC2 or NTC2008 per `inputs.norma`). Shares ~80% of its step modules with
`tool_rettangolare`; the shear/confinement formulas use the equivalent-square side (√Ac) in place
of L1/L2 (docs/specs/ca-pilastri.md). Norm-specific parameters come from `regole.resolve`.

I passi di calcolo veri e propri vivono in `esecuzione_circolare.py` e `dettagli_circolare.py`
(estratti per la regola dura 12 di CLAUDE.md, moduli/funzioni piccoli). `disegna_schizzo` resta una
chiamata diretta in questo modulo così i test possono fare il monkeypatch dell'attributo di modulo
(tests/members/ca_pilastri/test_schizzo.py)."""
import logging

from strutture.shared.report import Report, success

from .esecuzione_circolare import calcola_nucleo_circolare
from .materiali import proprieta_materiali
from .models import PilastroCircolareInput, PilastroOutput
from .regole import resolve
from .schizzo import disegna_circolare as disegna_schizzo

logger = logging.getLogger(__name__)


def run_pilastro_circolare(inputs: PilastroCircolareInput) -> Report[PilastroOutput]:
    rules = resolve(inputs.norma, inputs.legacy_compat)
    materiali = proprieta_materiali(inputs.acciaio, inputs.cls, legacy_compat=inputs.legacy_compat)
    nucleo = calcola_nucleo_circolare(inputs, rules, materiali)

    try:
        schizzo = disegna_schizzo(inputs)
    except Exception:
        logger.exception("errore nel disegno dello schizzo per pilastro-circolare")
        schizzo = None

    output = PilastroOutput(
        materiali=materiali, geometria=nucleo.geometria, armatura_minima=nucleo.armatura_minima,
        taglio=nucleo.taglio, flessione=nucleo.flessione, compressione=nucleo.compressione,
        confinamento=nucleo.confinamento, snellezza=nucleo.snellezza, dettagli=nucleo.dettagli,
        regole=nucleo.regole, schizzo=schizzo,
    )
    return success(output, inputs, checks=nucleo.checks)
