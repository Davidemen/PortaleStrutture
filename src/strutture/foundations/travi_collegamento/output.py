"""Composed output model for `fond-trave-collegamento` — groups mirror the sheet sections
(architecture-batch2.md §1: sismica, azione, materiali, compressione, trazione, snellezza, minimi)."""
from pydantic import BaseModel, ConfigDict, Field

from .armatura_minima_en import ArmaturaMinimaEnResult
from .azione import AzioneResult
from .compressione import CompressioneResult
from .geometria_minima_en import GeometriaMinimaEnResult
from .materiali import MaterialiResult
from .minimi_ntc import MinimiNtcResult
from .sismica_en import SismicaEnResult
from .sismica_ntc import SismicaNtcResult
from .snellezza_en import SnellezzaEnResult
from .snellezza_ntc import SnellezzaNtcResult
from .staffe_minime_en import StaffeMinimeEnResult
from .trazione import TrazioneResult


class MinimiEnResult(BaseModel):
    """EN sheet's three minimum checks: armatura longitudinale, geometria di sezione, staffe."""

    model_config = ConfigDict(frozen=True)

    armatura_longitudinale: ArmaturaMinimaEnResult
    geometria: GeometriaMinimaEnResult
    staffe: StaffeMinimeEnResult


class TraviCollegamentoOutput(BaseModel):
    """Full result envelope for both `norma` branches; the branch not selected is absent (None)."""

    model_config = ConfigDict(frozen=True)

    sismica_ntc: SismicaNtcResult | None = Field(default=None, description="Amplificazione sismica (NTC2018)")
    sismica_en: SismicaEnResult | None = Field(default=None, description="Amplificazione sismica (EN1998)")
    azione: AzioneResult = Field(description="Forza assiale di progetto")
    materiali: MaterialiResult = Field(description="Materiali")
    compressione: CompressioneResult = Field(description="Verifica a compressione")
    trazione: TrazioneResult = Field(description="Verifica a trazione")
    snellezza_ntc: SnellezzaNtcResult | None = Field(default=None, description="Controllo della snellezza (NTC2018)")
    snellezza_en: SnellezzaEnResult | None = Field(default=None, description="Controllo della snellezza (EN1998)")
    minimi_ntc: MinimiNtcResult | None = Field(default=None, description="Staffe minime (NTC2018)")
    minimi_en: MinimiEnResult | None = Field(default=None, description="Limiti minimi di normativa (EN1998)")
