"""NTC 2018 §3.2.2/§3.2.3.2.1 — composes Ss, Cc, ST into the soil amplification factor S (Sisma!I31:I34)."""
from .models import AmplificazioneResult, CategoriaSottosuolo, CategoriaTopografica
from .stratigrafia import coefficiente_correzione_cc, fattore_amplificazione_ss
from .topografia import fattore_topografico_st


def amplificazione(
    categoria_sottosuolo: CategoriaSottosuolo,
    categoria_topografica: CategoriaTopografica,
    tc_star_s: float,
    f0: float,
    ag_g: float,
    *,
    legacy_compat: bool = False,
) -> AmplificazioneResult:
    """Ss/Cc/ST/S = ST·Ss (Sisma!I31:I34)."""
    ss = fattore_amplificazione_ss(categoria_sottosuolo, f0, ag_g, legacy_compat=legacy_compat)
    cc = coefficiente_correzione_cc(categoria_sottosuolo, tc_star_s)
    st = fattore_topografico_st(categoria_topografica)
    return AmplificazioneResult(ss=ss, cc=cc, st=st, s=st * ss)
