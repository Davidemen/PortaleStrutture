"""Composed output model for `fond-pavimento-industriale` (architecture-batch2.md §1: materiali,
sottofondo, distribuiti, concentrati, giunti)."""
from pydantic import BaseModel, ConfigDict, Field

from .armatura import ArmaturaResult
from .concentrati import ConcentratiResult
from .distribuiti_carico import CaricoDistribuitoResult
from .distribuiti_momenti import MomentiDistribuitoResult
from .distribuiti_verifiche import VerificheDistribuitoResult
from .giunti import GiuntiResult
from .materiali import MaterialiResult
from .sottofondo import SottofondoResult


class DistribuitiResult(BaseModel):
    """`pav-carichi-distribuiti`: combined loads, moments, stress/crack/reinforcement checks."""

    model_config = ConfigDict(frozen=True)

    carico: CaricoDistribuitoResult
    momenti: MomentiDistribuitoResult
    verifiche: VerificheDistribuitoResult


class PavimentoIndustrialeOutput(BaseModel):
    """Full result envelope: `pav-fondazione-materiali` + `pav-carichi-distribuiti` +
    `pav-carichi-concentrati` + `pav-giunti`, composed into one report."""

    model_config = ConfigDict(frozen=True)

    materiali: MaterialiResult = Field(description="Proprietà di calcestruzzo e acciaio")
    sottofondo: SottofondoResult = Field(description="Sottofondo Winkler e rigidezza della piastra")
    armatura: ArmaturaResult = Field(description="Rete elettrosaldata: area e momento resistente")
    distribuiti: DistribuitiResult = Field(description="Verifica per carico uniformemente distribuito")
    concentrati: ConcentratiResult = Field(description="Verifica per carichi concentrati (righe + inviluppo)")
    giunti: GiuntiResult = Field(description="Prescrizioni geometriche sui giunti")
