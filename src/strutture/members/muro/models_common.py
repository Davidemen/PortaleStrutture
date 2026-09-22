"""Shared type used across the `muro-sostegno` result models (split out of `models.py`, regola
dura 12 dei moduli piccoli): the identifier of one of the 8 load combinations.
"""
from typing import Literal

NomeCombo = Literal["STR_1", "STR_2", "GEO_1", "GEO_2", "EQU_1", "EQU_2", "SISMA_1", "SISMA_2"]
