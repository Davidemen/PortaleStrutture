"""`compose.run`: end-to-end composition of the ca-sezione-dominio-mn steps — the governing row is
one of the table rows, the domains are traced for both axes, checks reflect the envelope, and a
sketch-drawing failure is absorbed without failing the calculation (same guard as
`ca_punzonamento.compose`)."""
import pytest

from strutture.members.ca_sezione_mn import compose as compose_module
from strutture.members.ca_sezione_mn.compose import N_PUNTI_DOMINIO, run
from strutture.members.ca_sezione_mn.models_input import SezioneMnInput

pytestmark = pytest.mark.unit

EXAMPLE = {
    "forma": "rettangolare", "b_mm": 300.0, "h_mm": 500.0,
    "armatura_modo": "layout", "layout_tipo": "perimetrale",
    "layout_copriferro_mm": 30.0, "layout_diametro_mm": 20.0, "layout_n_per_lato": 3,
    "classe_calcestruzzo": "C25/30", "grado_acciaio": "B450C",
    "azioni": [
        {"nome": "SLU1", "n_ed_kN": 800.0, "m_ed_x_kNm": 150.0, "m_ed_y_kNm": 0.0},
        {"nome": "SLU2", "n_ed_kN": 400.0, "m_ed_x_kNm": 120.0, "m_ed_y_kNm": 60.0},
        {"nome": "SLU3", "n_ed_kN": 1600.0, "m_ed_x_kNm": 40.0, "m_ed_y_kNm": 0.0},
    ],
}


def test_run_produce_domini_righe_e_governante() -> None:
    inputs = SezioneMnInput.model_validate(EXAMPLE)
    report = run(inputs)
    assert report.ok
    data = report.data
    assert len(data.dominio_x) == len(data.dominio_y) == N_PUNTI_DOMINIO
    assert len(data.righe) == 3
    assert {r.nome for r in data.righe} == {"SLU1", "SLU2", "SLU3"}
    assert data.governante.nome == max(data.righe, key=lambda r: r.rapporto or float("inf")).nome
    assert data.schizzo is not None
    assert data.geometria.n_barre == 8


def test_run_check_riflette_lenvelope() -> None:
    inputs = SezioneMnInput.model_validate(EXAMPLE)
    report = run(inputs)
    assert len(report.checks) == 1
    check = report.checks[0]
    assert check.passed == report.data.governante.dentro
    assert check.value == report.data.governante.rapporto


def test_run_riga_fuori_dal_dominio_fallisce_senza_eccezione() -> None:
    """N_Ed enorme rispetto alla capacità della sezione: la verifica fallisce ma il calcolo va
    comunque a buon fine (governante.rapporto=None, check fallito, mai un'eccezione)."""
    fuori = {**EXAMPLE, "azioni": [{"nome": "ESTREMO", "n_ed_kN": 1.0e7, "m_ed_x_kNm": 10.0, "m_ed_y_kNm": 0.0}]}
    inputs = SezioneMnInput.model_validate(fuori)
    report = run(inputs)
    assert report.ok
    assert report.data.governante.dentro is False
    assert report.data.governante.rapporto is None
    assert report.checks[0].passed is False


def test_governante_e_rifinita_a_m_rd_esatto() -> None:
    """Finding ALTO interpolazione.py: la riga governante non eredita l'errore di interpolazione
    del dominio tracciato — il suo M_Rd coincide con quello esatto del motore (`domini.m_rd`), non
    con la lettura interpolata."""
    from strutture.shared.sezione_ca.domini import m_rd as m_rd_esatto

    inputs = SezioneMnInput.model_validate(EXAMPLE)
    sezione = compose_module.costruisci_sezione(inputs)
    report = run(inputs)
    governante = report.data.governante

    asse = "x" if governante.tipo != "uniassiale y" else "y"
    mrd_pos_esatto, mrd_neg_esatto = m_rd_esatto(sezione, governante.n_ed_kN, asse)
    mrd_atteso = mrd_pos_esatto if getattr(governante, f"m_ed_{asse}_kNm") >= 0.0 else mrd_neg_esatto
    mrd_riportato = getattr(governante, f"m{asse}_rd_kNm")
    assert mrd_riportato == pytest.approx(mrd_atteso, rel=1e-6)


def test_errore_nel_disegno_non_fa_fallire_il_calcolo(monkeypatch: pytest.MonkeyPatch) -> None:
    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(compose_module, "disegna_schizzo", _rompi)
    inputs = SezioneMnInput.model_validate(EXAMPLE)
    report = run(inputs)
    assert report.ok
    assert report.data.schizzo is None
