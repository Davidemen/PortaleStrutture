"""The divergence register: every place where the default (code-standard) result differs from the
original spreadsheet. Source of truth = `src/strutture/data/divergences/<unita>.json`; the markdown
under docs/divergences/ is generated from it."""
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Tipo = Literal["errore_foglio", "aggiornamento_normativo", "scelta_ingegneristica", "da_verificare"]
Ramo = Literal["codice", "nessuno"]
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*/[a-z0-9]+(?:-[a-z0-9]+)*$")  # "<unita>/<slug>"


class Divergence(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(description='Stable key "<unita>/<slug>", e.g. "ca-pilastri/lambda-lim-unita"; never reused')
    titolo: str = Field(min_length=5, max_length=120, description="One Italian sentence an engineer recognises")
    tipo: Tipo
    strumenti: tuple[str, ...] = Field(description="Tool names affected (empty for shared modules used indirectly)")
    cella: str = Field(default="", description="Sheet!cell(s) where the spreadsheet does it, if any")
    foglio: str = Field(min_length=3, description="What the spreadsheet does (Italian)")
    corretto: str = Field(min_length=3, description="What the default mode does instead (Italian)")
    clausola: str = Field(default="", description="Governing clause, e.g. 'NTC2018 §4.1.2.3.9.2'")
    impatto: str = Field(default="", description="Numeric impact on the golden case, e.g. 'λ_lim 1084 -> 34,3'")
    uscite: tuple[str, ...] = Field(default=(), description="Output paths that can change, e.g. 'snellezza.lambda_lim'")
    ramo: Ramo = Field(default="codice", description=(
        '"codice": a `legacy("<id>", legacy_compat)` branch reproduces the spreadsheet; "nessuno": there is '
        "deliberately no such branch (a label, a sheet limit, a behaviour that cannot be reproduced)"))
    motivo_senza_ramo: str = Field(default="", description='Why there is no branch (Italian); required iff ramo="nessuno"')

    @field_validator("id")
    @classmethod
    def _id_format(cls, value: str) -> str:
        if not ID_PATTERN.match(value):
            raise ValueError(f"id {value!r} must look like '<unita>/<slug>' (lowercase, digits, hyphens)")
        return value

    @model_validator(mode="after")
    def _motivo_iff_senza_ramo(self) -> "Divergence":
        if self.ramo == "nessuno" and len(self.motivo_senza_ramo.strip()) < 5:
            raise ValueError('ramo="nessuno" requires motivo_senza_ramo (why no legacy branch exists)')
        if self.ramo == "codice" and self.motivo_senza_ramo:
            raise ValueError('motivo_senza_ramo is only allowed with ramo="nessuno"')
        return self
