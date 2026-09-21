"""Step: minimum longitudinal reinforcement envelope (NTC2018 §7.4.6.2.1 / EC8 5.4.3.2.2),
rows CX25:DA27 / 23."""
from strutture.shared.divergences import legacy
from strutture.shared.units import kn_to_n

RS_MAX = 0.04  # H23 check — rapporto massimo di armatura longitudinale ammesso in CD "B"
AC_RATIO_FLOOR = 0.003  # CX25 = 0.003*Ac
NED_OVER_FYD_RATIO = 0.10  # CX26 = 0.10*Ned/fyd
AC_RATIO_CEILING = 0.01  # CX27 = 0.01*Ac — soglia superiore dell'inviluppo percentuale (1%)
AC_RATIO_MAX_CEILING = 0.04  # NTC2018 §7.4.6.2.2 — tetto massimo di armatura ammesso in CD "B"


def armatura_minima(
    ac_mm2: float, ned_kN: float, fyd_MPa: float, *,
    legacy_compat: bool, area_ratio: float = AC_RATIO_FLOOR, combinatore: str = "auto",
) -> tuple[float, float]:
    """Returns (as_min_mm2, rs_min).

    `as_min_mm2` (riga "Area minima barre long."): il foglio NTC2008/NTC2018 aggrega i due
    candidati CX25/CX26 con MIN; NTC2018 §4.1.6.1.2 ("As,min = 0,10*NEd/fyd e comunque non minore
    di 0,003*Ac") è invece un inviluppo per MAX, con tetto ad `AC_RATIO_MAX_CEILING`*Ac (§7.4.6.2.2,
    4%). `legacy_compat=True` riproduce fedelmente il MIN del foglio; `legacy_compat=False` applica
    il MAX corretto — vedi docs/divergences/ca-pilastri.md. Il foglio EC2 usa invece MAX in entrambe
    le modalità, senza tetto al 4% (verificato a parte da un check dedicato "area massima"): passare
    `combinatore="max"` e `area_ratio=0.002` (EC2 §9.5.2(2)) per riprodurlo.

    `rs_min` (riga H23) resta l'inviluppo a tre candidati MAX(DA25:DA27) con il coefficiente NTC
    fisso `AC_RATIO_FLOOR`, invariato in entrambe le modalità e per ogni normativa (asimmetria
    deliberata del foglio, non un bug — vedi divergenze)."""
    candidato_area = area_ratio * ac_mm2
    candidato_assiale = NED_OVER_FYD_RATIO * kn_to_n(ned_kN) / fyd_MPa
    candidato_percentuale = AC_RATIO_CEILING * ac_mm2
    if combinatore == "max":
        as_min_mm2 = max(candidato_area, candidato_assiale)
    elif legacy("ca-pilastri/area-minima-longitudinale-min-invece-max", legacy_compat):
        as_min_mm2 = min(candidato_area, candidato_assiale)
    else:
        as_min_mm2 = min(max(candidato_area, candidato_assiale), AC_RATIO_MAX_CEILING * ac_mm2)
    rs_min = max(AC_RATIO_FLOOR * ac_mm2, candidato_assiale, candidato_percentuale) / ac_mm2
    return as_min_mm2, rs_min


def verifica_percentuale_armatura(rs: float, rs_min: float, *, controlla_minimo: bool = True) -> bool:
    """H23/H24 check: ρs < 4% (sempre) AND ρs > ρs,min (solo quando `controlla_minimo`, che il
    foglio NTC2018 abbandona — vedi docs/specs/ca-pilastri-ntc2018.md §4 — mantenendo il solo
    controllo del tetto)."""
    if controlla_minimo:
        return rs < RS_MAX and rs > rs_min
    return rs < RS_MAX
