"""Composed output model of the `muro-sostegno` tool (split out of `models.py`, regola dura 12 dei
moduli piccoli).
"""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.sketch import Sketch, campo_schizzo

from .models_armatura import ArmaturaFondazioneMonteResult, ArmaturaFondazioneValleResult, ArmaturaParamentoResult
from .models_capacita_portante import CapacitaPortanteFondazioneResult
from .models_geometria import GeometriaResult, ParametriSismiciResult
from .models_spinta import SpintaCombo
from .models_verifiche import PressioniCombo, RibaltamentoScorrimentoCombo


class MuroSostegnoOutput(BaseModel):
    """Composed output of the `muro-sostegno` tool: shared geometry + one row per combination for
    each of the three verification groups. `spinte`/`ribaltamento_scorrimento`/`pressioni_terreno`
    all carry 8 rows in the same order: STR_1, STR_2, GEO_1, GEO_2, EQU_1, EQU_2, SISMA_1, SISMA_2.
    """

    model_config = ConfigDict(frozen=True)

    geometria: GeometriaResult = Field(description="Geometria e pesi del muro/terreno, comuni a tutte le combinazioni")
    parametri_sismici: ParametriSismiciResult = Field(description="Coefficienti di amplificazione sismica")
    spinte: tuple[SpintaCombo, ...] = Field(description="Spinta attiva statica/sismica per combinazione")
    ribaltamento_scorrimento: tuple[RibaltamentoScorrimentoCombo, ...] = Field(description="Verifiche a ribaltamento e scorrimento per combinazione")
    pressioni_terreno: tuple[PressioniCombo, ...] = Field(
        description="Pressioni sul terreno ed eccentricità per combinazione",
        json_schema_extra={
            "chart": {
                "x": "nome", "y": ["p_valle_kPa", "p_monte_kPa"],
                "x_label": "Combinazione", "y_label": "Pressione sul terreno [kPa]",
            },
        },
    )
    capacita_portante_fondazione: CapacitaPortanteFondazioneResult | None = Field(
        default=None,
        description="Verifica di capacità portante del terreno di fondazione (calcolata solo se il blocco 'Terreno di fondazione' è compilato in modalità standard)",
    )
    armatura_paramento: ArmaturaParamentoResult = Field(description="Armatura verticale del paramento")
    armatura_fondazione_valle: ArmaturaFondazioneValleResult = Field(description="Armatura della fondazione di valle/mancia")
    armatura_fondazione_monte: ArmaturaFondazioneMonteResult = Field(description="Armatura della fondazione di monte/tacco")
    schizzo: Sketch | None = campo_schizzo()
