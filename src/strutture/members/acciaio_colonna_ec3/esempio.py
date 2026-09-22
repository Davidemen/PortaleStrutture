"""Golden/example input values for `acciaio-colonna-h-ec3`, split out of `tool.py` (regola dura 12).

`ESEMPIO_AUREO` (with `legacy_compat: True`) is the single golden/legacy fixture shared by the unit,
golden and model tests. `ESEMPIO_TOOL` is the same values without `legacy_compat`, used as the
`Tool.example` shown in the interface (standard mode).
"""

ESEMPIO_AUREO = {
    "sezione_nome": "550x450x8x16 + plate 100x16", "b_mm": 280, "h_mm": 500, "tw_mm": 8, "tf_mm": 12,
    "area_mm2": 10528, "grado_acciaio": "Q345", "gamma_m0": 1, "gamma_m1": 1, "tipo_lavorazione": "hot finished",
    "classe_sezione": "class 3", "iyy_mm4": 4.72063e8, "izz_mm4": 4.39243e7, "wel_y_mm3": 1.88825e6,
    "wpl_y_mm3": 2.09283e6, "wel_z_mm3": 3.13745e5, "wpl_z_mm3": 4.78016e5, "it_mm4": 4.05255e5,
    "e_MPa": 206000, "iy_mm": 211.752, "iz_mm": 62.5921, "nsd_kN": 172.326, "my_sd_kNm": 120.689,
    "mz_sd_kNm": 0.00639699, "vy_sd_kN": 29.2057, "vz_sd_kN": 0.00235166, "lcr_yy_mm": 16485.6,
    "lcr_zz_mm": 2083.1, "ly_mm": 18850, "lt_mm": 1800, "c1": 1.871, "mj_y_kNm": 0.00695734,
    "mj_z_kNm": 0.0224413, "dmax_yy_mm": 0, "dmax_zz_mm": 0, "diagramma_tipo_y": "1", "diagramma_tipo_z": "1",
    "legacy_compat": True,
}

ESEMPIO_TOOL = {
    "sezione_nome": "550x450x8x16 + plate 100x16", "b_mm": 280, "h_mm": 500, "tw_mm": 8, "tf_mm": 12,
    "area_mm2": 10528, "grado_acciaio": "Q345", "gamma_m0": 1, "gamma_m1": 1, "tipo_lavorazione": "hot finished",
    "classe_sezione": "class 3", "iyy_mm4": 4.72063e8, "izz_mm4": 4.39243e7, "wel_y_mm3": 1.88825e6,
    "wpl_y_mm3": 2.09283e6, "wel_z_mm3": 3.13745e5, "wpl_z_mm3": 4.78016e5, "it_mm4": 4.05255e5,
    "e_MPa": 206000, "iy_mm": 211.752, "iz_mm": 62.5921, "nsd_kN": 172.326, "my_sd_kNm": 120.689,
    "mz_sd_kNm": 0.00639699, "vy_sd_kN": 29.2057, "vz_sd_kN": 0.00235166, "lcr_yy_mm": 16485.6,
    "lcr_zz_mm": 2083.1, "ly_mm": 18850, "lt_mm": 1800, "c1": 1.871, "mj_y_kNm": 0.00695734,
    "mj_z_kNm": 0.0224413, "dmax_yy_mm": 0, "dmax_zz_mm": 0, "diagramma_tipo_y": "1", "diagramma_tipo_z": "1",
}
