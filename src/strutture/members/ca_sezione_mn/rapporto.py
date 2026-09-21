"""Step: the pressoflessione utilisation ratio for one `azioni` row, given the section's uniaxial
`M_Rd` capacities (`M_Rd+`, `M_Rd-`) already resolved at `N = N_Ed` — either by cheap interpolation
(`capacita.riga_azione`) or exactly (`capacita.riga_azione_esatta`); this module only turns those
numbers into a ratio, for every `TipoPressoflessione` branch.

**Uniaxial (finding CRITICO capacita._rd_nel_verso/_rapporto_componente).** The membership rule is
`M_Rd- <= M_Ed <= M_Rd+` (`M_Rd+ >= M_Rd-` holds for every `N` because the two branches trace the
domain's upper/lower boundary at that `N`, and the domain is convex — see
`docs/architecture-phase4.md` §A invariant 2). Picking a branch by the SIGN of `M_Ed` and dividing
by that single `M_Rd` (the previous implementation) gives a finite ratio < 1 even when `M_Ed` is
outside `[M_Rd-, M_Rd+]`, whenever that interval does not straddle zero (asymmetric reinforcement,
or any `forma`/preset whose polo is not the plastic centroid — see `sezione_builder.py`'s fix for
the polo itself). The rule now lives in the engine, `shared.sezione_ca.verifica.rapporto_uniassiale`
(one implementation for the engine and for this tool): the classic `|M_Ed| / |M_Rd|` in the sign of
`M_Ed` when the interval contains zero — the number an engineer expects, e.g. 150/208 for a beam
with more bottom than top steel — and the distance from the interval's centre over its half-width
when it does not; in both cases `rapporto <= 1 <=> M_Rd- <= M_Ed <= M_Rd+` exactly.

**Biaxial (finding ALTO capacita._rapporto).** `EN1992-1-1 §5.8.9(4)`:
`(|Mx_Ed|/|Mx_Rd|)^a + (|My_Ed|/|My_Rd|)^a <= 1`, with the exponent `a` interpolated on `N_Ed/N_Rd`
(rectangular sections: `a=1.0` at `N_Ed/N_Rd=0.1`, `a=1.5` at `0.7`, `a=2.0` at `1.0`) — not the
linear interaction `|Mx_Ed|/|Mx_Rd| + |My_Ed|/|My_Rd|` used before, which is only conservative when
the Mx-My domain at that `N` contains the origin (docs/architecture-phase4.md §A's own
`shared.sezione_ca.verifica.verifica` gives the exact ray-from-origin ratio, but its direction
search costs ~10-20 ms per row — too slow for the ≤ 500-row budget; the EC2 closed form is the
documented, code-compliant, O(1) alternative, chosen here and named in `RigaAzione.rapporto`'s
description). Like the uniaxial fix, this still assumes `Mx_Rd`/`My_Rd` (picked by sign) are
meaningful references — the residual edge case (asymmetric biaxial capacity whose domain excludes
the origin) is the same caveat EC2's own simplified formula carries.

**Axial-only (finding MEDIO capacita._tipo).** `M_Ed,x = M_Ed,y = 0` is checked against the minimum
eccentricity of `EN1992-1-1 §6.1(4)`, `e0 = max(h/30, 20 mm)`, per axis — not against `M_Ed = 0`
itself, which would always pass regardless of how close `N_Ed` is to `N_Rd`."""
from math import isinf

from strutture.shared.numeric import clamp
from strutture.shared.sezione_ca.verifica import rapporto_uniassiale
from strutture.shared.tables import interp_lookup

from .models_output import TipoPressoflessione
from .rows import AzioneRow

FRAZIONE_ALTEZZA_ECCENTRICITA_MINIMA_MM = 30.0  # EN1992-1-1 §6.1(4): e0 >= h/30.
ECCENTRICITA_MINIMA_ASSOLUTA_MM = 20.0  # EN1992-1-1 §6.1(4): e0 >= 20 mm.

# EN1992-1-1 §5.8.9(4), sezioni rettangolari: (N_Ed/N_Rd, esponente a), interpolazione lineare.
TABELLA_ESPONENTE_INTERAZIONE: tuple[tuple[float, float], ...] = ((0.1, 1.0), (0.7, 1.5), (1.0, 2.0))

RdPosNeg = tuple[float, float]


def rd_nel_verso(rd_pos_neg: RdPosNeg, m_ed_kNm: float) -> float:
    """`M_Rd` nel verso (segno) di `m_ed_kNm`: solo per la colonna informativa `mx_rd_kNm`/
    `my_rd_kNm` in output, MAI per calcolare `rapporto` (vedi il docstring del modulo)."""
    rd_pos, rd_neg = rd_pos_neg
    return rd_pos if m_ed_kNm >= 0.0 else rd_neg


def _rapporto_componente(m_ed_kNm: float, rd_pos_neg: RdPosNeg) -> float | None:
    """None = no finite ratio exists (degenerate interval): the caller reports it as not verified."""
    rd_pos, rd_neg = rd_pos_neg
    valore = rapporto_uniassiale(m_ed_kNm, rd_pos, rd_neg)
    return None if isinf(valore) else valore


def _eccentricita_minima_mm(dimensione_mm: float) -> float:
    return max(dimensione_mm / FRAZIONE_ALTEZZA_ECCENTRICITA_MINIMA_MM, ECCENTRICITA_MINIMA_ASSOLUTA_MM)


def _rapporto_assiale(n_ed_kN: float, rd_x: RdPosNeg, rd_y: RdPosNeg, h_x_mm: float, h_y_mm: float) -> float | None:
    m_min_x = n_ed_kN * _eccentricita_minima_mm(h_x_mm) / 1000.0
    m_min_y = n_ed_kN * _eccentricita_minima_mm(h_y_mm) / 1000.0
    rx, ry = _rapporto_componente(m_min_x, rd_x), _rapporto_componente(m_min_y, rd_y)
    return None if rx is None or ry is None else max(rx, ry)


def esponente_interazione(n_ed_kN: float, n_rd_kN: float) -> float:
    rapporto_assiale = clamp(n_ed_kN / n_rd_kN, 0.1, 1.0) if n_rd_kN > 0.0 else 0.1
    return interp_lookup(TABELLA_ESPONENTE_INTERAZIONE, rapporto_assiale)


def _rapporto_biassiale(azione: AzioneRow, rd_x: RdPosNeg, rd_y: RdPosNeg, n_rd_kN: float) -> float | None:
    mx_rd, my_rd = rd_nel_verso(rd_x, azione.m_ed_x_kNm), rd_nel_verso(rd_y, azione.m_ed_y_kNm)
    if mx_rd == 0.0 or my_rd == 0.0:
        return None
    a = esponente_interazione(azione.n_ed_kN, n_rd_kN)
    return (abs(azione.m_ed_x_kNm) / abs(mx_rd)) ** a + (abs(azione.m_ed_y_kNm) / abs(my_rd)) ** a


def rapporto(
    tipo: TipoPressoflessione, azione: AzioneRow, rd_x: RdPosNeg, rd_y: RdPosNeg,
    h_x_mm: float, h_y_mm: float, n_rd_kN: float,
) -> float | None:
    """Tasso di sfruttamento della riga, per `tipo` (vedi il docstring del modulo per ogni ramo)."""
    if tipo == "compressione/trazione semplice":
        return _rapporto_assiale(azione.n_ed_kN, rd_x, rd_y, h_x_mm, h_y_mm)
    if tipo == "uniassiale x":
        return _rapporto_componente(azione.m_ed_x_kNm, rd_x)
    if tipo == "uniassiale y":
        return _rapporto_componente(azione.m_ed_y_kNm, rd_y)
    return _rapporto_biassiale(azione, rd_x, rd_y, n_rd_kN)
