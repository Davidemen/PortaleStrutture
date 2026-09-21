"""Step: bending check against a user-supplied MRd, row G25/K25. No M-N interaction domain exists
in the sheet: MRd is always an external input (see PilastroRettangolareInput.mrd_kNm docstring)."""


def tasso_sfruttamento_pct(domanda: float, capacita: float) -> float:
    return round(domanda / capacita * 100.0, 2)


def verifica_flessione(mrd_kNm: float, med_kNm: float) -> bool:
    return mrd_kNm > med_kNm
