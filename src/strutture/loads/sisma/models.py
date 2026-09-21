"""Pydantic I/O models for the `sisma` tool package (NTC 2018 §3.2).

Site-hazard results (Cu/VR/TR, Ss/Cc/ST/S, TB/TC/TD) reuse the frozen result models from
`strutture.shared.ntc_site_seismic` directly — this package is a thin wrapper, not a
reimplementation, so there is no reason to redeclare their fields.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.ntc_site_seismic import (
    AmplificazioneResult,
    CategoriaSottosuolo,
    CategoriaTopografica,
    ClasseUso,
    PeriodiRitornoResult,
    PeriodiSpettroResult,
    StatoLimite,
    VitaRiferimentoResult,
)

# --- comune enrichment -------------------------------------------------------------------------


class ComuneInfo(BaseModel):
    """Sisma!I5/I6 plus zona sismica (spec Tool 1, extended with the merged comuni-db field)."""

    model_config = ConfigDict(frozen=True)

    provincia: str = Field(description="Provincia del comune")
    regione: str = Field(description="Regione del comune")
    zona_sismica: int = Field(description="Zona sismica del comune (1 = più severa)", ge=1, le=4, json_schema_extra={"unit": "-"})


# --- Tool: sisma-vita-riferimento --------------------------------------------------------------


class SismaVitaRiferimentoInput(BaseModel):
    """Sisma!I4, I7:I8 (spec Tools 1+2)."""

    model_config = ConfigDict(frozen=True)

    comune: str | None = Field(
        default=None,
        description="Comune di ubicazione dell'opera, per l'inquadramento del sito",
        min_length=1,
        json_schema_extra={"widget": "comune", "group": "Sito"},
    )
    provincia: str | None = Field(
        default=None,
        description="Provincia, se serve a distinguere comuni omonimi",
        json_schema_extra={"group": "Sito"},
    )
    vn_anni: float = Field(
        description="Vita nominale della costruzione",
        gt=0,
        json_schema_extra={"unit": "anni", "symbol": "V_N", "group": "Vita nominale e classe d'uso"},
    )
    classe_uso: ClasseUso = Field(
        description="Classe d'uso della costruzione",
        json_schema_extra={"group": "Vita nominale e classe d'uso"},
    )
    legacy_compat: bool = Field(
        default=False,
        description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"group": "Avanzate", "advanced": True},
    )


class SismaVitaRiferimentoOutput(BaseModel):
    """Sisma!I5:I6, I9:I10, D13:D16/E13:E16."""

    model_config = ConfigDict(frozen=True)

    comune_info: ComuneInfo | None = Field(default=None, description="Provincia/regione/zona sismica del comune")
    vita: VitaRiferimentoResult = Field(description="Coefficiente d'uso Cu e vita di riferimento VR")
    periodi_ritorno: PeriodiRitornoResult = Field(description="Periodi di ritorno TR per i 4 stati limite")


# --- Tool: sisma-parametri-sito -----------------------------------------------------------------


class SismaParametriSitoInput(BaseModel):
    """Sisma!I26:I30 (spec Tools 3+5)."""

    model_config = ConfigDict(frozen=True)

    categoria_sottosuolo: CategoriaSottosuolo = Field(description="Categoria di sottosuolo", json_schema_extra={"group": "Sito"})
    categoria_topografica: CategoriaTopografica = Field(description="Categoria topografica", json_schema_extra={"group": "Sito"})
    ag_g: float = Field(
        description="Accelerazione orizzontale massima al sito",
        gt=0,
        json_schema_extra={"unit": "g", "symbol": "a_g", "group": "Pericolosità di base"},
    )
    f0: float = Field(
        description="Fattore di amplificazione massima dello spettro",
        gt=0,
        json_schema_extra={"unit": "-", "symbol": "F_0", "group": "Pericolosità di base"},
    )
    tc_star_s: float = Field(
        description="Periodo di inizio del tratto a velocità costante",
        gt=0,
        json_schema_extra={"unit": "s", "symbol": "T*_C", "group": "Pericolosità di base"},
    )
    legacy_compat: bool = Field(
        default=False,
        description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"group": "Avanzate", "advanced": True},
    )


class SismaParametriSitoOutput(BaseModel):
    """Sisma!I31:I34, I48:I50."""

    model_config = ConfigDict(frozen=True)

    amplificazione: AmplificazioneResult = Field(description="Coefficienti di amplificazione stratigrafica/topografica")
    periodi: PeriodiSpettroResult = Field(description="Periodi caratteristici TB, TC, TD dello spettro")


# --- Tool: sisma-fattori-struttura --------------------------------------------------------------


class SismaFattoriStrutturaInput(BaseModel):
    """Sisma!I25, I37, I39:I40, I44 (spec Tool 4)."""

    model_config = ConfigDict(frozen=True)

    stato_limite: StatoLimite = Field(description="Stato limite considerato", json_schema_extra={"group": "Stato limite"})
    q0: float = Field(
        description="Fattore di struttura massimo, dipende dalla tipologia strutturale",
        gt=0,
        json_schema_extra={"unit": "-", "symbol": "q_0", "group": "Struttura"},
    )
    regolare_altezza: Literal["SI", "NO"] = Field(
        description="La struttura è regolare in altezza?", json_schema_extra={"group": "Struttura"}
    )
    qv: float = Field(
        description="Fattore di struttura per la componente verticale",
        gt=0,
        json_schema_extra={"unit": "-", "symbol": "q_v", "group": "Struttura"},
    )
    xi_pct: float = Field(
        description="Smorzamento viscoso equivalente",
        gt=0,
        json_schema_extra={"unit": "%", "symbol": "ξ", "group": "Smorzamento", "advanced": True},
    )
    legacy_compat: bool = Field(
        default=False,
        description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"group": "Avanzate", "advanced": True},
    )


class SismaFattoriStrutturaOutput(BaseModel):
    """Sisma!I38, I41, I44:I45."""

    model_config = ConfigDict(frozen=True)

    eta: float = Field(
        description="Correzione per smorzamento, componente orizzontale",
        gt=0,
        json_schema_extra={"unit": "-", "symbol": "η", "highlight": True},
    )
    q: float = Field(
        description="Fattore di struttura, componente orizzontale",
        gt=0,
        json_schema_extra={"unit": "-", "symbol": "q", "highlight": True},
    )
    eta_vert: float = Field(
        description="Correzione per smorzamento, componente verticale",
        gt=0,
        json_schema_extra={"unit": "-", "symbol": "η_v"},
    )
    q_vert: float = Field(
        description="Fattore di struttura, componente verticale",
        gt=0,
        json_schema_extra={"unit": "-", "symbol": "q_v", "highlight": True},
    )


# --- Tool: sisma-spettro -------------------------------------------------------------------------


class SismaSpettroInput(BaseModel):
    """Sisma!I29:I30, I34, I38, I41, I48:I50 (spec Tool 6). Sampling range is parametric; the
    default (0-4 s, step 0.05 s) covers the sheet's own row grid (`docs/specs/sisma.md` Tool 6)."""

    model_config = ConfigDict(frozen=True)

    stato_limite: StatoLimite = Field(description="Stato limite considerato", json_schema_extra={"group": "Stato limite"})
    ag_g: float = Field(
        description="Accelerazione orizzontale massima al sito",
        gt=0,
        json_schema_extra={"unit": "g", "symbol": "a_g", "group": "Pericolosità di base"},
    )
    f0: float = Field(
        description="Fattore di amplificazione massima dello spettro",
        gt=0,
        json_schema_extra={"unit": "-", "symbol": "F_0", "group": "Pericolosità di base"},
    )
    s: float = Field(
        description="Amplificazione del suolo",
        gt=0,
        json_schema_extra={"unit": "-", "symbol": "S", "group": "Parametri di sito"},
    )
    tb_s: float = Field(
        description="Inizio del tratto ad accelerazione costante",
        gt=0,
        json_schema_extra={"unit": "s", "symbol": "T_B", "group": "Parametri di sito"},
    )
    tc_s: float = Field(
        description="Inizio del tratto a velocità costante",
        gt=0,
        json_schema_extra={"unit": "s", "symbol": "T_C", "group": "Parametri di sito"},
    )
    td_s: float = Field(
        description="Inizio del tratto a spostamento costante",
        gt=0,
        json_schema_extra={"unit": "s", "symbol": "T_D", "group": "Parametri di sito"},
    )
    eta: float = Field(
        description="Correzione per smorzamento",
        gt=0,
        json_schema_extra={"unit": "-", "symbol": "η", "group": "Struttura"},
    )
    q: float = Field(
        description="Fattore di struttura",
        gt=0,
        json_schema_extra={"unit": "-", "symbol": "q", "group": "Struttura"},
    )
    t_start_s: float = Field(
        default=0.0, description="Periodo iniziale del campionamento", ge=0,
        json_schema_extra={"unit": "s", "symbol": "T_min", "group": "Campionamento", "advanced": True},
    )
    t_end_s: float = Field(
        default=4.0, description="Periodo finale del campionamento", gt=0,
        json_schema_extra={"unit": "s", "symbol": "T_max", "group": "Campionamento", "advanced": True},
    )
    step_s: float = Field(
        default=0.05, description="Passo di campionamento", gt=0,
        json_schema_extra={"unit": "s", "symbol": "ΔT", "group": "Campionamento", "advanced": True},
    )
    legacy_compat: bool = Field(
        default=False,
        description="Riproduci il foglio Excel originale (errori inclusi)",
        json_schema_extra={"group": "Avanzate", "advanced": True},
    )


class PuntoSpettro(BaseModel):
    """One (T, Se, Sd) sample (Sisma!I/N/J columns)."""

    model_config = ConfigDict(frozen=True)

    t_s: float = Field(description="Periodo", json_schema_extra={"unit": "s", "symbol": "T"})
    se_g: float = Field(description="Ordinata dello spettro elastico", json_schema_extra={"unit": "g", "symbol": "S_e(T)"})
    sd_g: float = Field(
        description="Ordinata dello spettro di progetto (per SLO/SLD coincide con lo spettro elastico)",
        json_schema_extra={"unit": "g", "symbol": "S_d(T)"},
    )


class SismaSpettroOutput(BaseModel):
    """Sisma!I55:J149."""

    model_config = ConfigDict(frozen=True)

    punti: tuple[PuntoSpettro, ...] = Field(
        description="Punti dello spettro di risposta",
        json_schema_extra={
            "chart": {
                "x": "t_s",
                "y": ["se_g", "sd_g"],
                "x_label": "T [s]",
                "y_label": "S [g]",
            }
        },
    )
