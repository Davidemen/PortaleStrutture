"""Frozen output models for `acciaio-sezione-h-rimpiattata`."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.units import MM_PER_CM

MM3_PER_CM3 = MM_PER_CM**3
MM4_PER_CM4 = MM_PER_CM**4


class ElementoRisultato(BaseModel):
    """Riga per elemento (ali, anima, piatti): A, baricentro, scostamenti dal baricentro
    complessivo, contributo a Wpl,x/Wpl,y e a Ix/Iy (sheet columns D..N, O)."""

    model_config = ConfigDict(frozen=True)

    nome: str = Field(description="Elemento")
    area_mm2: float = Field(description="Area A", json_schema_extra={"unit": "mm2", "symbol": "A"})
    x_mm: float = Field(description="Ascissa del baricentro dell'elemento xi", json_schema_extra={"unit": "mm", "symbol": "x_i"})
    y_mm: float = Field(description="Ordinata del baricentro dell'elemento yi", json_schema_extra={"unit": "mm", "symbol": "y_i"})
    delta_x_mm: float = Field(description="|xi - xN|", json_schema_extra={"unit": "mm", "symbol": "Δx"})
    delta_y_mm: float = Field(description="|yi - yN|", json_schema_extra={"unit": "mm", "symbol": "Δy"})
    wpl_x_i_cm3: float = Field(description="Contributo dell'elemento a Wpl,x (A*Δy)", json_schema_extra={"unit": "cm3", "symbol": "Wpl,x,i"})
    wpl_y_i_cm3: float = Field(description="Contributo dell'elemento a Wpl,y (A*Δx)", json_schema_extra={"unit": "cm3", "symbol": "Wpl,y,i"})
    ix_i_cm4: float = Field(description="Contributo dell'elemento a Ix (asse forte)", json_schema_extra={"unit": "cm4", "symbol": "Ix,i"})
    iy_i_cm4: float = Field(description="Contributo dell'elemento a Iy (asse debole)", json_schema_extra={"unit": "cm4", "symbol": "Iy,i"})


class Sezione(BaseModel):
    """Proprietà della sezione composta e confronto con il profilo non rinforzato."""

    model_config = ConfigDict(frozen=True)

    area_mm2: float = Field(description="Area totale della sezione composta A", gt=0,
                             json_schema_extra={"unit": "mm2", "symbol": "A", "highlight": True})
    x_n_mm: float = Field(description="Ascissa del baricentro xN", json_schema_extra={"unit": "mm", "symbol": "x_N"})
    y_n_mm: float = Field(description="Ordinata del baricentro yN", json_schema_extra={"unit": "mm", "symbol": "y_N"})
    ix_cm4: float = Field(description="Momento d'inerzia rispetto all'asse forte Ix", gt=0,
                           json_schema_extra={"unit": "cm4", "symbol": "I_x", "highlight": True})
    iy_cm4: float = Field(description="Momento d'inerzia rispetto all'asse debole Iy", gt=0,
                           json_schema_extra={"unit": "cm4", "symbol": "I_y", "highlight": True})
    ix_base_cm4: float = Field(description="Ix del solo profilo base (non rinforzato)", gt=0,
                                json_schema_extra={"unit": "cm4", "symbol": "I_x,0"})
    iy_base_cm4: float = Field(description="Iy del solo profilo base (non rinforzato)", gt=0,
                                json_schema_extra={"unit": "cm4", "symbol": "I_y,0"})
    rapporto_ix: float = Field(description="Ix / Ix,0 rispetto al profilo non rinforzato", gt=0,
                                json_schema_extra={"unit": "-", "symbol": "I_x/I_x,0"})
    rapporto_iy: float = Field(description="Iy / Iy,0 rispetto al profilo non rinforzato", gt=0,
                                json_schema_extra={"unit": "-", "symbol": "I_y/I_y,0"})
    wel_x_superiore_cm3: float = Field(description="Modulo elastico Wel,x lato superiore", gt=0,
                                        json_schema_extra={"unit": "cm3", "symbol": "Wel,x,sup"})
    wel_x_inferiore_cm3: float = Field(description="Modulo elastico Wel,x lato inferiore", gt=0,
                                        json_schema_extra={"unit": "cm3", "symbol": "Wel,x,inf"})
    wel_y_destro_cm3: float = Field(description="Modulo elastico Wel,y lato +x", gt=0,
                                     json_schema_extra={"unit": "cm3", "symbol": "Wel,y,+"})
    wel_y_sinistro_cm3: float = Field(description="Modulo elastico Wel,y lato -x", gt=0,
                                       json_schema_extra={"unit": "cm3", "symbol": "Wel,y,-"})
    wpl_x_cm3: float = Field(description="Modulo plastico Wpl,x", gt=0,
                              json_schema_extra={"unit": "cm3", "symbol": "Wpl,x"})
    wpl_y_cm3: float = Field(
        description="Modulo plastico Wpl,y (in modalità legacy è 0 per un profilo non rinforzato: "
                     "l'approssimazione del foglio somma solo lo scostamento del baricentro dei "
                     "piatti, non la distribuzione propria delle ali attorno all'asse debole)",
        ge=0, json_schema_extra={"unit": "cm3", "symbol": "Wpl,y"},
    )
    raggio_x_mm: float = Field(description="Raggio d'inerzia rispetto all'asse forte ix", gt=0,
                                json_schema_extra={"unit": "mm", "symbol": "i_x"})
    raggio_y_mm: float = Field(description="Raggio d'inerzia rispetto all'asse debole iy", gt=0,
                                json_schema_extra={"unit": "mm", "symbol": "i_y"})


class SezioneHRimpiattataOutput(BaseModel):
    """Output di `acciaio-sezione-h-rimpiattata`."""

    model_config = ConfigDict(frozen=True)

    elementi: tuple[ElementoRisultato, ...] = Field(description="Elementi della sezione (ali, anima, piatti)")
    sezione: Sezione = Field(description="Proprietà della sezione composta")
