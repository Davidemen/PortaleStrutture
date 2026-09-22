"""Step: build the per-`azioni`-row `RigaAzione` (docs/architecture-phase4.md §B). `riga_azione`
resolves `M_Rd` by the cheap `interpolazione.m_rd_da_dominio` read-off (used for every row, see that
module's docstring for the performance budget); `riga_azione_esatta` resolves it by an exact engine
bisection instead (`shared.sezione_ca.domini.m_rd`) — reserved for the governing row (`compose.py`),
where the interpolation error (up to ~7% close to a pivot-domain kink) would otherwise leak into the
envelope check (finding ALTO interpolazione.m_rd_da_dominio). An exact `m_rd` call costs ~12 ms on a
representative test section (measured, not the ~0.4 ms this finding's own review assumed): calling
it for every row of a 500-row table would cost ~12 s, well over the 5 s/500-row budget of
docs/BUILD_CONTRACT.md, hence the split instead of "exact everywhere"."""
from strutture.shared.sezione_ca.domini import PuntoDominio, intervallo_n
from strutture.shared.sezione_ca.domini import m_rd as m_rd_esatto
from strutture.shared.sezione_ca.modelli import Sezione

from .interpolazione import m_rd_da_dominio
from .models_output import ResistenzeGovernante, RigaAzione, TipoPressoflessione
from .rapporto import RdPosNeg, rd_nel_verso
from .rapporto import rapporto as calcola_rapporto
from .rows import AzioneRow


def _tipo(m_ed_x_kNm: float, m_ed_y_kNm: float) -> TipoPressoflessione:
    if m_ed_x_kNm == 0.0 and m_ed_y_kNm == 0.0:
        return "compressione/trazione semplice"
    if m_ed_y_kNm == 0.0:
        return "uniassiale x"
    if m_ed_x_kNm == 0.0:
        return "uniassiale y"
    return "biassiale"


def _costruisci_riga(
    azione: AzioneRow, tipo: TipoPressoflessione, rd_x: RdPosNeg | None, rd_y: RdPosNeg | None,
    h_x_mm: float, h_y_mm: float, n_rd_kN: float,
) -> RigaAzione:
    if rd_x is None or rd_y is None:
        return RigaAzione(
            nome=azione.nome, n_ed_kN=azione.n_ed_kN, m_ed_x_kNm=azione.m_ed_x_kNm, m_ed_y_kNm=azione.m_ed_y_kNm,
            tipo=tipo, mx_rd_kNm=None, my_rd_kNm=None, rapporto=None, dentro=False,
        )
    rapporto = calcola_rapporto(tipo, azione, rd_x, rd_y, h_x_mm, h_y_mm, n_rd_kN)
    dentro = rapporto is not None and rapporto <= 1.0
    return RigaAzione(
        nome=azione.nome, n_ed_kN=azione.n_ed_kN, m_ed_x_kNm=azione.m_ed_x_kNm, m_ed_y_kNm=azione.m_ed_y_kNm,
        tipo=tipo, mx_rd_kNm=rd_nel_verso(rd_x, azione.m_ed_x_kNm), my_rd_kNm=rd_nel_verso(rd_y, azione.m_ed_y_kNm),
        rapporto=rapporto, dentro=dentro,
    )


def riga_azione(
    azione: AzioneRow, dominio_x: tuple[PuntoDominio, ...], dominio_y: tuple[PuntoDominio, ...],
    h_x_mm: float, h_y_mm: float, n_rd_kN: float,
) -> RigaAzione:
    """Verifica a pressoflessione della riga `azione`, per interpolazione sui domini già tracciati."""
    tipo = _tipo(azione.m_ed_x_kNm, azione.m_ed_y_kNm)
    rd_x, rd_y = m_rd_da_dominio(dominio_x, azione.n_ed_kN), m_rd_da_dominio(dominio_y, azione.n_ed_kN)
    return _costruisci_riga(azione, tipo, rd_x, rd_y, h_x_mm, h_y_mm, n_rd_kN)


def riga_azione_esatta(
    azione: AzioneRow, sezione: Sezione, h_x_mm: float, h_y_mm: float, n_rd_kN: float,
) -> tuple[RigaAzione, ResistenzeGovernante | None]:
    """Stessa verifica di `riga_azione`, ma con `M_Rd` risolti esattamente dal motore (una
    bisezione ciascuno) invece che letti per interpolazione lineare — vedi il docstring del modulo.
    Restituisce anche le resistenze esatte di entrambi gli assi (None se N_Ed è fuori dal dominio):
    sono i numeri che un altro strumento può riusare (collegamento `sezione.mrd_x_kNm`)."""
    tipo = _tipo(azione.m_ed_x_kNm, azione.m_ed_y_kNm)
    n_min, n_max = intervallo_n(sezione)
    fuori_campo = not n_min <= azione.n_ed_kN <= n_max
    rd_x = None if fuori_campo else m_rd_esatto(sezione, azione.n_ed_kN, "x")
    rd_y = None if fuori_campo else m_rd_esatto(sezione, azione.n_ed_kN, "y")
    resistenze = None if rd_x is None or rd_y is None else ResistenzeGovernante(
        n_ed_kN=azione.n_ed_kN, mrd_x_pos_kNm=rd_x[0], mrd_x_neg_kNm=rd_x[1], mrd_y_pos_kNm=rd_y[0], mrd_y_neg_kNm=rd_y[1],
    )
    return _costruisci_riga(azione, tipo, rd_x, rd_y, h_x_mm, h_y_mm, n_rd_kN), resistenze
