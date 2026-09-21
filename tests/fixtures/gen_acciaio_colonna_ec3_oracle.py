"""Regenerate tests/fixtures/acciaio_colonna_ec3_oracle.json from the workbook via LibreOffice.

Run with: uv run python tests/fixtures/gen_acciaio_colonna_ec3_oracle.py
"""
from pathlib import Path

from extract.fixtures import generate

SLUG = "acciaio-colonne-ec3"
SHEET = "Column check"

# Field -> cell, in sheet order (models.ColonnaEc3Input).
CELLE = {
    "b_mm": "H6", "h_mm": "H7", "tw_mm": "H8", "tf_mm": "H9", "area_mm2": "H10",
    "grado_acciaio": "H11", "gamma_m0": "H12", "gamma_m1": "H13", "tipo_lavorazione": "G16",
    "classe_sezione": "Y16", "iyy_mm4": "P5", "izz_mm4": "P6", "wel_y_mm3": "P7", "wpl_y_mm3": "P8",
    "wel_z_mm3": "P10", "wpl_z_mm3": "P11", "it_mm4": "P13", "e_MPa": "P14", "iy_mm": "P15", "iz_mm": "P16",
    "nsd_kN": "J19", "my_sd_kNm": "J20", "mz_sd_kNm": "J21", "vy_sd_kN": "J22", "vz_sd_kN": "J23",
    "lcr_yy_mm": "Y19", "lcr_zz_mm": "Y20", "ly_mm": "Y64", "lt_mm": "AV42", "c1": "AZ33",
    "mj_y_kNm": "AI45", "mj_z_kNm": "AN45", "dmax_yy_mm": "AI52", "dmax_zz_mm": "AN52",
    "diagramma_tipo_y": "AJ61", "diagramma_tipo_z": "AJ62",
}

# Diagram-type dropdown stores 1/2 as numbers, "3a"/"3b" as text (build/cellmaps validation list).
DIAGRAMMA_NUMERICO = {"1", "2"}

BASE = {
    "b_mm": 280, "h_mm": 500, "tw_mm": 8, "tf_mm": 12, "area_mm2": 10528, "grado_acciaio": "Q345",
    "gamma_m0": 1, "gamma_m1": 1, "tipo_lavorazione": "hot finished", "classe_sezione": "class 3",
    "iyy_mm4": 4.72063e8, "izz_mm4": 4.39243e7, "wel_y_mm3": 1.88825e6, "wpl_y_mm3": 2.09283e6,
    "wel_z_mm3": 3.13745e5, "wpl_z_mm3": 4.78016e5, "it_mm4": 4.05255e5, "e_MPa": 206000,
    "iy_mm": 211.752, "iz_mm": 62.5921, "nsd_kN": 172.326, "my_sd_kNm": 120.689, "mz_sd_kNm": 0.00639699,
    "vy_sd_kN": 29.2057, "vz_sd_kN": 0.00235166, "lcr_yy_mm": 16485.6, "lcr_zz_mm": 2083.1, "ly_mm": 18850,
    "lt_mm": 1800, "c1": 1.871, "mj_y_kNm": 0.00695734, "mj_z_kNm": 0.0224413, "dmax_yy_mm": 0,
    "dmax_zz_mm": 0, "diagramma_tipo_y": "1", "diagramma_tipo_z": "1",
}

CASI_CAMPI = [
    {},  # golden case, spec §8
    {  # cold formed, class 1, S235, diagram type 2/2 (transverse-load Cm)
        "tipo_lavorazione": "cold formed", "classe_sezione": "class 1", "grado_acciaio": "S235",
        "diagramma_tipo_y": "2", "diagramma_tipo_z": "2", "dmax_yy_mm": 50, "dmax_zz_mm": 30,
        "gamma_m0": 1.05, "gamma_m1": 1.05, "mz_sd_kNm": 15.0, "mj_z_kNm": 5.0,
    },
    {  # class 2, S275, diagram 3a/3a, high shear triggering the MRd shear-reduction branch
        "classe_sezione": "class 2", "grado_acciaio": "S275", "diagramma_tipo_y": "3a",
        "diagramma_tipo_z": "3a", "vz_sd_kN": 600, "vy_sd_kN": 700,
    },
    {  # class 4, S355, cold formed, diagram 3b/3b, h/b>2 (BC17 -> "d" branch)
        "classe_sezione": "class 4", "grado_acciaio": "S355", "tipo_lavorazione": "cold formed",
        "diagramma_tipo_y": "3b", "diagramma_tipo_z": "3b", "b_mm": 200,
    },
    {"lt_mm": 8000, "c1": 1.0},  # LTB necessity flips to "necessary" (lambda_LT >= lambda_LT,0)
    {"tw_mm": 4},  # thin web: hw/tw > 72*eps*eta, shear buckling check not required
    {  # Q235, class 1, mixed diagram types
        "grado_acciaio": "Q235", "classe_sezione": "class 1", "diagramma_tipo_y": "2",
        "diagramma_tipo_z": "1", "dmax_yy_mm": 20,
    },
    {"mj_y_kNm": -80.0, "mz_sd_kNm": 5.0, "mj_z_kNm": -3.0},  # double-curvature (psi < 0)
]

LETTI = [
    "H14", "H15", "BC17", "Y25", "Y26", "BC25", "Y21", "Y22", "AV38", "W23", "W24", "W29", "W32",
    "AI8", "AI35", "U37", "O59", "D33", "D43", "G26", "G36", "J26", "J36", "AC27", "AD27", "K32",
    "C67", "O75", "R75", "AM64", "AM65", "AM66", "X42", "X43", "X44", "X45", "Y47", "AA47", "Y48",
    "Y50", "AA50", "Y52", "H46", "J53", "M53", "J54", "M54", "V54", "I56", "K56",
]


def _case_da_campi(campi: dict[str, object]) -> dict[str, object]:
    valori = {**BASE, **campi}
    caso: dict[str, object] = {}
    for campo, valore in valori.items():
        cella = CELLE[campo]
        if campo in ("diagramma_tipo_y", "diagramma_tipo_z") and valore in DIAGRAMMA_NUMERICO:
            valore = int(valore)
        caso[cella] = valore
    return caso


CASES = [_case_da_campi(campi) for campi in CASI_CAMPI]


def generate_fixture() -> list[dict]:
    target = Path(__file__).parent / "acciaio_colonna_ec3_oracle.json"
    return generate(SLUG, SHEET, cases=CASES, read=LETTI, target=target)


if __name__ == "__main__":
    fixtures = generate_fixture()
    print(f"wrote {len(fixtures)} cases")
