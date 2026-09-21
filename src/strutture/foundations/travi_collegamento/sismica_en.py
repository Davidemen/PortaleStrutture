"""EN1998-1 §3.2.2.2 spectrum-type selection + EN1998-5 §5.4.1.2 site/α table (sheet
`Travi colleg. EN 1998-1 e 5`, C7:C8/C25, `Tabelle!M131:P134`).

EN1998-1 §3.2.2.2(2)P: when the governing earthquake has Ms **not greater than 5.5**, the Type 2
spectrum (higher S) applies; Type 1 applies for Ms > 5.5.

**Sheet bug**: only the sheet's *label* is wrong — `C7={=IF(C6<=5.5,"TIPO1","TIPO2")}` inverts
the norm's rule (it should read `"TIPO2"` when `Ms<=5.5`). The sheet's `C8` column selection
(`{=VLOOKUP(C5,Tabelle!M131:O134,IF(C6<=5.5,3,2),FALSE)}` — column 3/O = "S Tipo 2" when
`Ms<=5.5`, column 2/N = "S Tipo 1" when `Ms>5.5`) is *independently* EN-correct: it already
matches the norm's threshold, regardless of what `C7` calls it. So the S value is identical under
both flags; only the reported `tipo_spettro` label differs. `legacy_compat=True` reproduces the
sheet's mislabeled `C7`; `legacy_compat=False` reports the EN1998-1 §3.2.2.2(2)P-correct label.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.divergences import legacy
from strutture.shared.tables import exact_lookup

from .models import CategoriaSottosuoloTravi
from .tables import EN1998_SOIL_TABLE

TipoSpettro = Literal["TIPO1", "TIPO2"]
MS_SOGLIA_TIPO_SPETTRO = 5.5  # EN1998-1 §3.2.2.2(2)P — Ms <= 5.5 -> spettro Tipo 2, altrimenti Tipo 1.


class SismicaEnResult(BaseModel):
    """Tipo spettro, S, α, amax."""

    model_config = ConfigDict(frozen=True)

    tipo_spettro: TipoSpettro = Field(description="Tipologia di spettro (Ms ≤ 5.5 → Tipo 2, EN1998-1 §3.2.2.2(2)P)")
    s: float = Field(description="Coefficiente S", json_schema_extra={"unit": "-", "symbol": "S"}, gt=0)
    alpha: float = Field(description="Coefficiente α (EN1998-5 §5.4.1.2)", json_schema_extra={"unit": "-", "symbol": "α"}, ge=0)
    amax_g: float = Field(description="Accelerazione orizzontale massima attesa al sito amax", json_schema_extra={"unit": "g", "symbol": "a_max"}, gt=0)


def sismica_en(categoria_sottosuolo: CategoriaSottosuoloTravi, ms: float, ag_g: float, *, legacy_compat: bool = False) -> SismicaEnResult:
    """TIPO[C7], S[C8], α, amax[C25]."""
    tipo_spettro_corretto: TipoSpettro = "TIPO2" if ms <= MS_SOGLIA_TIPO_SPETTRO else "TIPO1"
    tipo_spettro_sheet: TipoSpettro = "TIPO1" if ms <= MS_SOGLIA_TIPO_SPETTRO else "TIPO2"  # sheet's inverted C7
    tipo_spettro = (
        tipo_spettro_sheet
        if legacy("fond-travi-collegamento/etichetta-tipo-spettro-en-invertita", legacy_compat)
        else tipo_spettro_corretto
    )
    s_tipo1, s_tipo2, alpha = exact_lookup(EN1998_SOIL_TABLE, categoria_sottosuolo)
    # Sheet's C8 column pick is independently EN-correct (matches tipo_spettro_corretto) in both
    # modes — only the reported label (C7) differs between legacy and fixed.
    s = s_tipo2 if tipo_spettro_corretto == "TIPO2" else s_tipo1
    return SismicaEnResult(tipo_spettro=tipo_spettro, s=s, alpha=alpha, amax_g=ag_g * s)
