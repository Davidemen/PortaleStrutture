"""`schizzo.py`: section outline + bars + governing-combination neutral axis (`shared/sketch.py`
COMPOSITION RULES, docs/ui/WORKBENCH_SPEC.md §7). A failure here must never fail the calculation
(guarded in `compose.run`, same pattern as `ca_punzonamento.schizzo`)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from test_sketch_layout import layout_problems, overlap_problems, readability_problems

from strutture.members.ca_sezione_mn.assi_neutri import asse_neutro
from strutture.members.ca_sezione_mn.models_output import RigaAzione
from strutture.members.ca_sezione_mn.schizzo import disegna
from strutture.members.ca_sezione_mn.tool import TOOLS
from strutture.shared.sezione_ca.domini import intervallo_n
from strutture.shared.sezione_ca.modelli import Sezione
from strutture.shared.tool import execute

pytestmark = pytest.mark.unit

TOOL = TOOLS[0]


def _riga(tipo: str, n_ed_kN: float, mx: float = 0.0, my: float = 0.0) -> RigaAzione:
    return RigaAzione(
        nome="G", n_ed_kN=n_ed_kN, m_ed_x_kNm=mx, m_ed_y_kNm=my, tipo=tipo,
        mx_rd_kNm=None, my_rd_kNm=None, rapporto=None, dentro=True,
    )


def test_schizzo_disegna_contorno_e_barre(sezione_rettangolare: Sezione) -> None:
    sketch = disegna(sezione_rettangolare, None)
    assert len(sketch.viste) == 1
    forme = sketch.viste[0].forme
    assert forme[0].kind == "polygon"
    assert any(f.kind == "bars" for f in forme)


def test_schizzo_senza_asse_neutro_ha_nota(sezione_rettangolare: Sezione) -> None:
    sketch = disegna(sezione_rettangolare, None)
    assert "fuori dal dominio" in sketch.nota
    assert not any(f.kind == "line" for f in sketch.viste[0].forme)


def test_schizzo_con_asse_neutro_disegna_linea_ed_etichetta(sezione_rettangolare: Sezione) -> None:
    n_min, n_max = intervallo_n(sezione_rettangolare)
    piano = asse_neutro(sezione_rettangolare, _riga("uniassiale x", (n_min + n_max) / 2.0, mx=50.0))
    sketch = disegna(sezione_rettangolare, piano)
    forme = sketch.viste[0].forme
    assert any(f.kind == "line" for f in forme)
    assert any(f.kind == "label" and f.testo == "Asse neutro" for f in forme)
    assert sketch.nota == ""


def test_schizzo_stato_uniforme_ha_nota_dedicata(sezione_rettangolare: Sezione) -> None:
    """Uno stato di compressione (o trazione) pura ha curvatura nulla: nessun asse neutro da
    disegnare, ma una nota esplicita — mai un disegno silenziosamente incompleto."""
    piano_uniforme = (-0.001, 0.0, 0.0)  # (eps0, kx, ky): deformazione uniforme, kappa = 0
    sketch = disegna(sezione_rettangolare, piano_uniforme)
    assert not any(f.kind == "line" for f in sketch.viste[0].forme)
    assert "compressione o trazione pura" in sketch.nota


def test_barre_raggruppate_per_diametro(sezione_rettangolare: Sezione) -> None:
    sketch = disegna(sezione_rettangolare, None)
    gruppi_barre = [f for f in sketch.viste[0].forme if f.kind == "bars"]
    assert len(gruppi_barre) == 1  # una sola fila con lo stesso diametro nel fixture
    assert len(gruppi_barre[0].centri) == 6


@pytest.mark.parametrize(
    "overrides",
    [
        {},  # esempio
        {"azioni": [{"nome": "C1", "n_ed_kN": 400, "m_ed_x_kNm": 120, "m_ed_y_kNm": 60}]},  # biassiale
        {"forma": "circolare", "b_mm": None, "h_mm": None, "diametro_mm": 450,
         "armatura_modo": "layout", "layout_tipo": "circolare", "layout_n_barre": 8,
         "layout_copriferro_mm": 30, "layout_diametro_mm": 18},
        {"forma": "a_t", "b_mm": None, "bf_mm": 500, "hf_mm": 150, "bw_mm": 250, "h_mm": 600,
         "armatura_modo": "tabella",
         "barre": [{"x_mm": -75, "y_mm": 30, "diametro_mm": 20}, {"x_mm": 75, "y_mm": 30, "diametro_mm": 20}]},
    ],
)
def test_geometrie_realistiche_non_hanno_problemi_di_layout(overrides: dict) -> None:
    modificato = {**TOOL.example, **overrides}
    report = execute(TOOL, modificato)
    assert report.ok, report.errors
    sketch = report.data.schizzo
    assert sketch is not None
    problemi = layout_problems(sketch) + readability_problems(sketch) + overlap_problems(sketch)
    assert problemi == [], problemi
