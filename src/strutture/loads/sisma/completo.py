"""Composed step for `sisma-completo`: chains the four existing `sisma` tools (vita di riferimento
-> parametri di sito -> fattori di struttura -> spettro) so the user fills one form instead of
copying S/eta/q/TB/TC/TD by hand between tools.

Reuses each tool's own `run_*` composition from `tool.py` (imported lazily to break the import
cycle: `tool.py` needs `run_completo` to register the tool, this module needs `tool.py`'s `run_*`
functions to avoid re-composing the same steps) — no formula or sequencing logic is duplicated.
"""
from strutture.shared.report import Report, success

from .models import (
    SismaFattoriStrutturaInput,
    SismaParametriSitoInput,
    SismaSpettroInput,
    SismaVitaRiferimentoInput,
)
from .models_completo import SismaCompletoInput, SismaCompletoOutput


def run_completo(inputs: SismaCompletoInput) -> Report[SismaCompletoOutput]:
    from .tool import run_fattori_struttura, run_parametri_sito, run_spettro, run_vita_riferimento

    vita = run_vita_riferimento(
        SismaVitaRiferimentoInput(
            comune=inputs.comune,
            provincia=inputs.provincia,
            vn_anni=inputs.vn_anni,
            classe_uso=inputs.classe_uso,
            legacy_compat=inputs.legacy_compat,
        )
    ).data

    parametri_sito = run_parametri_sito(
        SismaParametriSitoInput(
            categoria_sottosuolo=inputs.categoria_sottosuolo,
            categoria_topografica=inputs.categoria_topografica,
            tc_star_s=inputs.tc_star_s,
            f0=inputs.f0,
            ag_g=inputs.ag_g,
            legacy_compat=inputs.legacy_compat,
        )
    ).data

    fattori_struttura = run_fattori_struttura(
        SismaFattoriStrutturaInput(
            xi_pct=inputs.xi_pct,
            q0=inputs.q0,
            regolare_altezza=inputs.regolare_altezza,
            stato_limite=inputs.stato_limite,
            qv=inputs.qv,
            legacy_compat=inputs.legacy_compat,
        )
    ).data

    spettro = run_spettro(
        SismaSpettroInput(
            s=parametri_sito.amplificazione.s,
            eta=fattori_struttura.eta,
            q=fattori_struttura.q,
            ag_g=inputs.ag_g,
            f0=inputs.f0,
            tb_s=parametri_sito.periodi.tb,
            tc_s=parametri_sito.periodi.tc,
            td_s=parametri_sito.periodi.td,
            stato_limite=inputs.stato_limite,
            t_start_s=inputs.t_start_s,
            t_end_s=inputs.t_end_s,
            step_s=inputs.step_s,
            legacy_compat=inputs.legacy_compat,
        )
    ).data

    data = SismaCompletoOutput(
        vita_riferimento=vita,
        parametri_sito=parametri_sito,
        fattori_struttura=fattori_struttura,
        spettro=spettro,
    )
    return success(data, inputs)
