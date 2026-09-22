"""Shared constants and tiny helpers reused by every `acciaio_colonna_ec3` relazione module
(docs/architecture-phase2.md §6). Unit-conversion constants are embedded INLINE in a formula's own
text (never through `Passo.scala`) whenever the formula also carries a comparison, because the
harness re-evaluates a check's boolean `esito` from the RAW, unscaled operands
(`strutture.shared.relazione.verifica._problemi_confronto`) — `scala` alone would silently compare
mismatched units. `modulo_flessionale` mirrors the classe-dependent modulus pick every EN1993-1-1
§6.2.5-family formula in this package makes (`sezione.momento_plastico_resistente_kNm`,
`flessione.mrd_y_kNm`/`mrd_z_kNm`, `instabilita_flesso_torsionale.snellezza_lt`): it only picks
which already-validated INPUT value and identifier the trace shows, the calculation itself stays in
its own module, untouched.
"""
import math

KN_A_N = 1000.0  # kN -> N, embedded inline (e.g. inside a sqrt/ratio); mirrors shared.units.kn_to_n
N_A_KN = 1e-3  # N -> kN, embedded inline in a check formula
NMM_A_KNM = 1e-6  # N*mm -> kN*m, embedded inline in a check formula
PI_GRECO = math.pi


def modulo_flessionale(classe_num: int, wel_mm3: float, wpl_mm3: float, asse: str) -> tuple[str, float]:
    """(simbolo, valore) del modulo di resistenza impiegato per l'asse `asse` ("y"/"z"): W_pl per le
    sezioni di classe 1/2, W_el per le classi 3/4 (EN1993-1-1 §6.2.5(2))."""
    if classe_num < 3:
        return f"W_pl,{asse}", wpl_mm3
    return f"W_el,{asse}", wel_mm3


def simbolo_momento_rd(classe_num: int, asse: str) -> str:
    """"M_pl,{asse},Rd" per le classi 1-2 (davvero plastico, `W_pl·f_yd`), "M_c,{asse},Rd" per le
    classi 3-4 (`modulo_flessionale` sceglie `W_el`: chiamarlo "M_pl" sarebbe autocontraddittorio,
    review finding WRONG_CLAUSE — EN1993-1-1 usa M_c,Rd/M_el,Rd, non M_pl,Rd, quando il modulo è
    elastico). Un solo punto di scelta, riusato sia dal passo che lo definisce
    (`relazione_sezione.py`) sia da chi lo riusa (`relazione_interazione_semplificata.py`), cosà
    così che i due moduli restino sempre allineati."""
    return f"M_pl,{asse},Rd" if classe_num < 3 else f"M_c,{asse},Rd"
