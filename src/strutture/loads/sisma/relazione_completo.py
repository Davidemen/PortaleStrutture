"""Verified restatement of `sisma-completo` (NTC2018 §3.2; docs/architecture-phase2.md §6, wave 3
adoption). `sisma-completo` computes nothing of its own — `completo.run_completo` chains the four
other tools' own `run_*` (vita di riferimento -> parametri di sito -> fattori di struttura ->
spettro) and nests their already-computed outputs unchanged. This relazione does exactly the same
with the four `relazione_*` functions: builds each one's own input model from `SismaCompletoInput`
(mirroring `completo.run_completo`'s own construction, so the two never drift apart) and calls it
against the matching nested output — no formula is duplicated or re-derived, avoiding the drift a
second, independent restatement of the same physics would risk.
"""
from strutture.shared.relazione import Traccia

from .models import SismaFattoriStrutturaInput, SismaParametriSitoInput, SismaSpettroInput, SismaVitaRiferimentoInput
from .models_completo import SismaCompletoInput, SismaCompletoOutput
from .relazione_fattori_struttura import relazione_fattori_struttura
from .relazione_parametri_sito import relazione_parametri_sito
from .relazione_spettro import relazione_spettro
from .relazione_vita_riferimento import relazione_vita_riferimento


def relazione_completo(inputs: SismaCompletoInput, output: SismaCompletoOutput) -> tuple[Traccia, ...]:
    """Concatena le Traccia delle 4 fasi (vita, sito, struttura, spettro), ciascuna già completa
    per conto proprio (8, 8, 8, 10 passi sul caso aureo: 34 in totale, oltre al budget 8-30 di un
    singolo tool — atteso per un tool che compone gli altri quattro per intero, si veda
    `tests/loads/sisma/test_relazione.py`)."""
    vita_input = SismaVitaRiferimentoInput(
        comune=inputs.comune, provincia=inputs.provincia, vn_anni=inputs.vn_anni,
        classe_uso=inputs.classe_uso, legacy_compat=inputs.legacy_compat,
    )
    sito_input = SismaParametriSitoInput(
        categoria_sottosuolo=inputs.categoria_sottosuolo, categoria_topografica=inputs.categoria_topografica,
        tc_star_s=inputs.tc_star_s, f0=inputs.f0, ag_g=inputs.ag_g, legacy_compat=inputs.legacy_compat,
    )
    struttura_input = SismaFattoriStrutturaInput(
        xi_pct=inputs.xi_pct, q0=inputs.q0, regolare_altezza=inputs.regolare_altezza,
        stato_limite=inputs.stato_limite, qv=inputs.qv, legacy_compat=inputs.legacy_compat,
    )
    spettro_input = SismaSpettroInput(
        s=output.parametri_sito.amplificazione.s, eta=output.fattori_struttura.eta, q=output.fattori_struttura.q,
        ag_g=inputs.ag_g, f0=inputs.f0, tb_s=output.parametri_sito.periodi.tb, tc_s=output.parametri_sito.periodi.tc,
        td_s=output.parametri_sito.periodi.td, stato_limite=inputs.stato_limite,
        t_start_s=inputs.t_start_s, t_end_s=inputs.t_end_s, step_s=inputs.step_s, legacy_compat=inputs.legacy_compat,
    )
    return (
        *relazione_vita_riferimento(vita_input, output.vita_riferimento),
        *relazione_parametri_sito(sito_input, output.parametri_sito),
        *relazione_fattori_struttura(struttura_input, output.fattori_struttura),
        *relazione_spettro(spettro_input, output.spettro),
    )
