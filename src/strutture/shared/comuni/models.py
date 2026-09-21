"""Frozen data model for one row of the merged Comuni database."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ZonaSismica = Literal[1, 2, 3, 4]
ZonaVento = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9]
ZonaNeve = Literal["I (alpina)", "I (mediterranea)", "II", "III"]


class Comune(BaseModel):
    """One municipality, merged per architecture.md §3 conflict C3 (Regione/Istat/Comune/Sismica/Vento
    from the sisma-vento snapshot; Provincia/Neve from the newer neve snapshot).
    """

    model_config = ConfigDict(frozen=True)

    regione: str = Field(description="Regione amministrativa", min_length=1)
    provincia: str = Field(description="Provincia amministrativa", min_length=1)
    istat: str = Field(description="Codice Istat del comune (stringa, zeri iniziali preservati)", min_length=1)
    comune: str = Field(description="Nome del comune", min_length=1)
    zona_sismica: ZonaSismica = Field(description="Zona sismica NTC18 (1..4, 1 = più severa)")
    zona_vento: ZonaVento = Field(description="Zona vento NTC18 (1..9)")
    zona_neve: ZonaNeve = Field(description="Zona neve NTC18")
