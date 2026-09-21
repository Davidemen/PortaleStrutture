"""Frozen pydantic models for the RC section engine: `Sezione` (outline + bars + materials) and
`Risultante` (an (N, Mx, My) integration result). Validation happens once at construction
(NTC 2018 §4.1.2.1.2.1 materials from `shared.materials`); everything downstream is pure tuples.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from strutture.shared.materials.concrete import ConcreteProperties
from strutture.shared.materials.rebar import RebarProperties

from .geometria import area_con_segno, normalizza_antiorario, poligono_semplice, punto_in_poligono

TOLLERANZA_BORDO_MM_DEFAULT = 1e-6  # tolleranza per "barra sul bordo" / area nulla.

LeggeCalcestruzzo = Literal["parabola-rettangolo", "bilineare"]
LeggeAcciaio = Literal["elastico-perfettamente-plastico", "bilineare"]


class MaterialiSezione(BaseModel):
    """Materiali e leggi costitutive di una sezione in c.a. (NTC2018 §4.1.2.1.2.1)."""

    model_config = ConfigDict(frozen=True)

    calcestruzzo: ConcreteProperties = Field(description="Proprietà del calcestruzzo (classe ≤ C50/60)")
    acciaio: RebarProperties = Field(description="Proprietà dell'acciaio da armatura")
    legge_calcestruzzo: LeggeCalcestruzzo = Field(
        default="parabola-rettangolo", description="Legge costitutiva del calcestruzzo",
    )
    legge_acciaio: LeggeAcciaio = Field(
        default="elastico-perfettamente-plastico", description="Legge costitutiva dell'acciaio",
    )


class Barra(BaseModel):
    """Una barra d'armatura come area puntiforme."""

    model_config = ConfigDict(frozen=True)

    x_mm: float = Field(description="Ascissa del baricentro della barra")
    y_mm: float = Field(description="Ordinata del baricentro della barra")
    diametro_mm: float = Field(description="Diametro della barra", gt=0)

    @property
    def area_mm2(self) -> float:
        from math import pi
        return pi * self.diametro_mm ** 2 / 4.0


class Risultante(BaseModel):
    """Risultante di un'integrazione (N, Mx, My): N > 0 compressione, M > 0 trazione al lembo
    inferiore — vedi la convenzione dei segni in `integrazione.py`."""

    model_config = ConfigDict(frozen=True)

    n_kN: float = Field(description="Sforzo normale risultante", json_schema_extra={"unit": "kN"})
    mx_kNm: float = Field(description="Momento risultante attorno a x", json_schema_extra={"unit": "kNm"})
    my_kNm: float = Field(description="Momento risultante attorno a y", json_schema_extra={"unit": "kNm"})
    n_strisce: int = Field(description="Numero di strisce usate dopo il raffinamento adattivo", ge=1)


def _normalizza_contorno_prima(dati: object) -> object:
    if not isinstance(dati, dict) or "contorno" not in dati:
        return dati
    contorno = tuple((float(p[0]), float(p[1])) for p in dati["contorno"])
    if len(contorno) >= 3 and area_con_segno(contorno) < 0.0:
        contorno = normalizza_antiorario(contorno)
    return {**dati, "contorno": contorno}


class Sezione(BaseModel):
    """Sezione in c.a.: contorno in cls (poligono semplice, mm, CCW — un contorno orario in
    ingresso viene riordinato automaticamente), barre come aree puntiformi, materiali."""

    model_config = ConfigDict(frozen=True)

    contorno: tuple[tuple[float, float], ...] = Field(
        description="Vertici del contorno in cls, in mm, in senso antiorario (poligono semplice)",
    )
    barre: tuple[Barra, ...] = Field(default=(), description="Armatura come aree puntiformi")
    materiali: MaterialiSezione = Field(description="Materiali e leggi costitutive")
    tolleranza_bordo_mm: float = Field(
        default=TOLLERANZA_BORDO_MM_DEFAULT,
        description="Tolleranza geometrica per considerare una barra interna al contorno",
        gt=0,
    )

    @model_validator(mode="before")
    @classmethod
    def _riordina_contorno(cls, dati: object) -> object:
        return _normalizza_contorno_prima(dati)

    @model_validator(mode="after")
    def _valida_geometria(self) -> "Sezione":
        if len(self.contorno) < 3:
            raise ValueError("Il contorno deve avere almeno 3 vertici.")
        if abs(area_con_segno(self.contorno)) <= 0.0:
            raise ValueError("Il contorno ha area nulla o è degenere.")
        if not poligono_semplice(self.contorno):
            raise ValueError("Il contorno non è un poligono semplice: i lati si intersecano.")
        for i, barra in enumerate(self.barre, start=1):
            punto = (barra.x_mm, barra.y_mm)
            if not punto_in_poligono(punto, self.contorno, tolleranza_mm=self.tolleranza_bordo_mm):
                raise ValueError(
                    f"La barra n. {i} in ({barra.x_mm}, {barra.y_mm}) mm è esterna al contorno della sezione.",
                )
        return self
