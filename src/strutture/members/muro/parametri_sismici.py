"""Soil amplification S = Ss·ST (muro-sostegno rows 17-20). Reuses `strutture.shared.ntc_site_seismic`
(the single implementation of NTC2018 Tab. 3.2.IV/3.2.V) instead of re-deriving Ss/ST — the sheet's
"Tratto A" freezes Ss as a manual input while "Tratto B" computes it live from the category; the
tool always computes it live, driven by the `categoria_sottosuolo`/`categoria_topografica` inputs
(see docs/specs/muro-sostegno.md "Tratto A vs B" and docs/divergences/muro-sostegno.md).
"""
from strutture.shared.ntc_site_seismic import (
    CategoriaSottosuolo,
    CategoriaTopografica,
    fattore_amplificazione_ss,
    fattore_topografico_st,
)

from .models import ParametriSismiciResult


def parametri_sismici(categoria_sottosuolo: CategoriaSottosuolo, categoria_topografica: CategoriaTopografica, f0: float, ag_g: float) -> ParametriSismiciResult:
    ss = fattore_amplificazione_ss(categoria_sottosuolo, f0, ag_g)
    st = fattore_topografico_st(categoria_topografica)
    return ParametriSismiciResult(ss=ss, st=st, s=ss * st)
