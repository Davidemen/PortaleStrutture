"""NTC2018 §7.2.5 — site amplification S and the α coefficient of the tie-force formula
(sheet `Travi collegamento NTC2018`, C8:C10/C27, `Tabelle!M118:P121`).

The sheet's own `SS` formulas (`Tabelle!N119:N121`) hardcode a cross-sheet reference to this
sheet's own C4/C5 (see spec "Suspected spreadsheet bugs" §1) but are otherwise the exact NTC2018
Tab. 3.2.IV formulas for categoria B/C/D, already reused via `shared.ntc_site_seismic`; this
sheet's own O-column clamps already match the NTC-standard bounds (no B-category 0.40 sheet clip),
so `fattore_amplificazione_ss` is always called here with `legacy_compat=False`.
"""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.ntc_site_seismic import fattore_amplificazione_ss, fattore_topografico_st
from strutture.shared.tables import exact_lookup

from .models import CategoriaSottosuoloTravi, CategoriaTopograficaTravi
from .tables import ALPHA_NTC


class SismicaNtcResult(BaseModel):
    """SS, ST, S, α, amax."""

    model_config = ConfigDict(frozen=True)

    ss: float = Field(description="Coefficiente di amplificazione stratigrafica SS", json_schema_extra={"unit": "-", "symbol": "S_S"}, gt=0)
    st: float = Field(description="Coefficiente di amplificazione topografica ST", json_schema_extra={"unit": "-", "symbol": "S_T"}, gt=0)
    s: float = Field(description="Coefficiente S = SS·ST", json_schema_extra={"unit": "-", "symbol": "S"}, gt=0)
    alpha: float = Field(description="Coefficiente α (Tab. C7.11.I)", json_schema_extra={"unit": "-", "symbol": "α"}, gt=0)
    amax_g: float = Field(description="Accelerazione orizzontale massima attesa al sito amax", json_schema_extra={"unit": "g", "symbol": "a_max"}, gt=0)


def sismica_ntc(
    categoria_sottosuolo: CategoriaSottosuoloTravi, categoria_topografica: CategoriaTopograficaTravi,
    f0: float, ag_g: float,
) -> SismicaNtcResult:
    """SS[C8], ST[C9], S[C10], α, amax[C27]."""
    ss = fattore_amplificazione_ss(categoria_sottosuolo, f0, ag_g, legacy_compat=False)
    st = fattore_topografico_st(categoria_topografica)
    s = ss * st
    alpha = exact_lookup(ALPHA_NTC, categoria_sottosuolo)
    return SismicaNtcResult(ss=ss, st=st, s=s, alpha=alpha, amax_g=ag_g * s)
