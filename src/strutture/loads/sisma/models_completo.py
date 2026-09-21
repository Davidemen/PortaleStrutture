"""I/O models for the composed `sisma-completo` tool.

One flat input form chains the four existing tools (vita di riferimento -> parametri di sito ->
fattori di struttura -> spettro); the output nests each tool's own (already-defined) output model
unchanged, so nothing here reimplements a formula or redeclares a result field.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.ntc_site_seismic import CategoriaSottosuolo, CategoriaTopografica, ClasseUso, StatoLimite

from .models import (
    SismaFattoriStrutturaOutput,
    SismaParametriSitoOutput,
    SismaSpettroOutput,
    SismaVitaRiferimentoOutput,
)


class SismaCompletoInput(BaseModel):
    """Sisma!I4, I7:I8, I25, I28:I30, I26:I27, I37, I39:I40, I44 (Tools 1-6 merged into one form).

    Field order follows the sheet top-to-bottom flow: vita di riferimento, stato limite, parametri
    di sito, fattori di struttura, then the optional comune lookup and spectrum sampling.
    """

    model_config = ConfigDict(frozen=True)

    comune: str | None = Field(
        default=None,
        description="Comune di ubicazione dell'opera, per l'inquadramento del sito",
        min_length=1,
        json_schema_extra={"widget": "comune", "group": "Sito"},
    )
    provincia: str | None = Field(
        default=None, description="Provincia, se serve a distinguere comuni omonimi",
        json_schema_extra={"group": "Sito"},
    )
    categoria_sottosuolo: CategoriaSottosuolo = Field(description="Categoria di sottosuolo", json_schema_extra={"group": "Sito"})
    categoria_topografica: CategoriaTopografica = Field(description="Categoria topografica", json_schema_extra={"group": "Sito"})
    vn_anni: float = Field(
        description="Vita nominale della costruzione", gt=0,
        json_schema_extra={"unit": "anni", "symbol": "V_N", "group": "Vita nominale e classe d'uso"},
    )
    classe_uso: ClasseUso = Field(
        description="Classe d'uso della costruzione", json_schema_extra={"group": "Vita nominale e classe d'uso"}
    )
    stato_limite: StatoLimite = Field(description="Stato limite considerato", json_schema_extra={"group": "Stato limite"})
    ag_g: float = Field(
        description="Accelerazione orizzontale massima al sito", gt=0,
        json_schema_extra={"unit": "g", "symbol": "a_g", "group": "Pericolosità di base"},
    )
    f0: float = Field(
        description="Fattore di amplificazione massima dello spettro", gt=0,
        json_schema_extra={"unit": "-", "symbol": "F_0", "group": "Pericolosità di base"},
    )
    tc_star_s: float = Field(
        description="Periodo di inizio del tratto a velocità costante", gt=0,
        json_schema_extra={"unit": "s", "symbol": "T*_C", "group": "Pericolosità di base"},
    )
    q0: float = Field(
        description="Fattore di struttura massimo, dipende dalla tipologia strutturale", gt=0,
        json_schema_extra={"unit": "-", "symbol": "q_0", "group": "Struttura"},
    )
    regolare_altezza: Literal["SI", "NO"] = Field(
        description="La struttura è regolare in altezza?", json_schema_extra={"group": "Struttura"}
    )
    qv: float = Field(
        description="Fattore di struttura per la componente verticale", gt=0,
        json_schema_extra={"unit": "-", "symbol": "q_v", "group": "Struttura"},
    )
    xi_pct: float = Field(
        description="Smorzamento viscoso equivalente", gt=0,
        json_schema_extra={"unit": "%", "symbol": "ξ", "group": "Struttura", "advanced": True},
    )
    t_start_s: float = Field(
        default=0.0, description="Periodo iniziale del campionamento dello spettro", ge=0,
        json_schema_extra={"unit": "s", "symbol": "T_min", "group": "Campionamento dello spettro", "advanced": True},
    )
    t_end_s: float = Field(
        default=4.0, description="Periodo finale del campionamento dello spettro", gt=0,
        json_schema_extra={"unit": "s", "symbol": "T_max", "group": "Campionamento dello spettro", "advanced": True},
    )
    step_s: float = Field(
        default=0.05, description="Passo di campionamento dello spettro", gt=0,
        json_schema_extra={"unit": "s", "symbol": "ΔT", "group": "Campionamento dello spettro", "advanced": True},
    )
    legacy_compat: bool = Field(
        default=False,
        description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"group": "Avanzate", "advanced": True},
    )


class SismaCompletoOutput(BaseModel):
    """All four intermediate groups plus the spectrum, so the user reads one result instead of
    copying S/eta/q/TB/TC/TD by hand between tools."""

    model_config = ConfigDict(frozen=True)

    vita_riferimento: SismaVitaRiferimentoOutput = Field(description="Vita di riferimento e periodi di ritorno")
    parametri_sito: SismaParametriSitoOutput = Field(description="Parametri di sito e amplificazione")
    fattori_struttura: SismaFattoriStrutturaOutput = Field(description="Fattori di struttura")
    spettro: SismaSpettroOutput = Field(description="Spettro di risposta")
