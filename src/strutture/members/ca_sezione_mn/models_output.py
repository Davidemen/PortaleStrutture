"""Output models for `ca-sezione-dominio-mn` (docs/architecture-phase4.md §B): geometric summary,
per-combination row, domains with chart hints, the governing row and the sketch."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.sezione_ca.domini import PuntoDominio
from strutture.shared.sezione_ca.modelli import MaterialiSezione
from strutture.shared.sketch import Sketch, campo_schizzo

TipoPressoflessione = Literal["compressione/trazione semplice", "uniassiale x", "uniassiale y", "biassiale"]


class GeometriaOutput(BaseModel):
    """Riepilogo geometrico della sezione (contorno + armatura)."""

    model_config = ConfigDict(frozen=True)

    ac_mm2: float = Field(description="Area lorda di calcestruzzo", ge=0, json_schema_extra={"unit": "mm2", "symbol": "A_c"})
    as_mm2: float = Field(description="Area totale dell'armatura longitudinale", ge=0,
                          json_schema_extra={"unit": "mm2", "symbol": "A_s", "highlight": True})
    rho: float = Field(description="Rapporto geometrico di armatura A_s/A_c (frazione: 0,0168 = 1,68 %)", ge=0,
                       json_schema_extra={"unit": "-", "symbol": "ρ", "highlight": True})
    n_barre: int = Field(description="Numero di barre longitudinali", ge=0, json_schema_extra={"symbol": "n"})


class RigaAzione(BaseModel):
    """Verifica a pressoflessione di una riga della tabella `azioni`."""

    model_config = ConfigDict(frozen=True)

    nome: str = Field(description="Nome della combinazione di carico", json_schema_extra={"unit": "-"})
    n_ed_kN: float = Field(description="Sforzo normale di progetto (positivo di compressione)", json_schema_extra={"unit": "kN", "symbol": "N_Ed"})
    m_ed_x_kNm: float = Field(description="Momento flettente di progetto attorno a x", json_schema_extra={"unit": "kNm", "symbol": "M_Ed,x"})
    m_ed_y_kNm: float = Field(description="Momento flettente di progetto attorno a y", json_schema_extra={"unit": "kNm", "symbol": "M_Ed,y"})
    tipo: TipoPressoflessione = Field(
        description="Tipo individuato dalle componenti di momento della riga: 'compressione/trazione "
                    "semplice' se M_Ed,x = M_Ed,y = 0 (verificata comunque con l'eccentricità minima), "
                    "altrimenti uniassiale x/y o biassiale a seconda delle componenti nulle",
        json_schema_extra={"unit": "-"},
    )
    mx_rd_kNm: float | None = Field(
        description="Momento resistente attorno a x, nel verso di M_Ed,x (stesso segno: positivo "
                    "tende il lembo di ordinata minima), a N = N_Ed",
        json_schema_extra={"unit": "kNm", "symbol": "M_Rd,x"},
    )
    my_rd_kNm: float | None = Field(
        description="Momento resistente attorno a y, nel verso di M_Ed,y (stesso segno: positivo "
                    "tende il lembo di ascissa massima), a N = N_Ed",
        json_schema_extra={"unit": "kNm", "symbol": "M_Rd,y"},
    )
    rapporto: float | None = Field(
        description="Tasso di sfruttamento a pressoflessione (≤ 1 = verificata). Flessione retta: M_Ed/M_Rd nel verso "
                    "di M_Ed quando il dominio a N = N_Ed contiene M = 0; altrimenti la distanza di M_Ed dal centro "
                    "dell'intervallo [M_Rd−, M_Rd+] rapportata alla sua semiampiezza. Sforzo normale semplice: con "
                    "l'eccentricità minima e0 = max(h/30, 20 mm) di EN 1992-1-1 §6.1(4). Flessione deviata: "
                    "(|Mx_Ed|/|Mx_Rd|)^a + (|My_Ed|/|My_Rd|)^a con a da EN 1992-1-1 §5.8.9(4)",
        # no `highlight`: this is a ROW model (every combination + the governing one) — the Sintesi already
        # shows the governing utilisation as η_max, and a highlight here printed the same symbol twice
        json_schema_extra={"unit": "-", "symbol": "η"},
    )
    dentro: bool = Field(description="True se la combinazione è interna al dominio di resistenza (rapporto ≤ 1)")


class ResistenzeGovernante(BaseModel):
    """The exact M_Rd of both axes at the governing combination's N_Ed — the numbers another tool can
    take (phase 5 link `sezione.mrd_x_kNm` -> the column tools' typed M_Rd)."""

    model_config = ConfigDict(frozen=True)

    n_ed_kN: float = Field(description="Sforzo normale della combinazione governante (positivo di compressione)", json_schema_extra={"unit": "kN", "symbol": "N_Ed"})
    mrd_x_pos_kNm: float = Field(description="Momento resistente attorno a x, verso positivo, a N = N_Ed (esatto)", json_schema_extra={"unit": "kNm", "symbol": "M_Rd,x+", "provides": "sezione.mrd_x_kNm"})
    mrd_x_neg_kNm: float = Field(description="Momento resistente attorno a x, verso negativo, a N = N_Ed (esatto)", json_schema_extra={"unit": "kNm", "symbol": "M_Rd,x−"})
    mrd_y_pos_kNm: float = Field(description="Momento resistente attorno a y, verso positivo, a N = N_Ed (esatto)", json_schema_extra={"unit": "kNm", "symbol": "M_Rd,y+"})
    mrd_y_neg_kNm: float = Field(description="Momento resistente attorno a y, verso negativo, a N = N_Ed (esatto)", json_schema_extra={"unit": "kNm", "symbol": "M_Rd,y−"})


class SezioneMnOutput(BaseModel):
    """Dominio di resistenza e verifica a pressoflessione su tutte le combinazioni di `azioni`."""

    model_config = ConfigDict(frozen=True)

    geometria: GeometriaOutput = Field(description="Riepilogo geometrico della sezione")
    materiali: MaterialiSezione = Field(description="Materiali e leggi costitutive impiegate")
    dominio_x: tuple[PuntoDominio, ...] = Field(
        description="Dominio di resistenza N-Mx (flessione attorno a x)",
        json_schema_extra={"chart": {"x": "n_kN", "y": ["m_kNm"], "x_label": "N [kN]", "y_label": "M_x [kNm]"}},
    )
    dominio_y: tuple[PuntoDominio, ...] = Field(
        description="Dominio di resistenza N-My (flessione attorno a y)",
        json_schema_extra={"chart": {"x": "n_kN", "y": ["m_kNm"], "x_label": "N [kN]", "y_label": "M_y [kNm]"}},
    )
    righe: tuple[RigaAzione, ...] = Field(
        description="Verifica a pressoflessione di ogni combinazione della tabella azioni",
        json_schema_extra={"rows_page": 200},
    )
    governante: RigaAzione = Field(description="Combinazione governante (rapporto di sfruttamento massimo)")
    resistenze_governante: ResistenzeGovernante | None = Field(
        default=None, description="M_Rd esatti di entrambi gli assi a N = N_Ed della combinazione governante (assente se N_Ed è fuori dal dominio)",
    )
    schizzo: Sketch | None = campo_schizzo()
