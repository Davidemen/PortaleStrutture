from decimal import Decimal

from strutture.shared.dimensiona.campioni import Campione
from strutture.shared.dimensiona.griglia import costruisci_griglia
from strutture.shared.dimensiona.ricerca import cerca


def _griglia(a=10):
    return costruisci_griglia(0, a, 1, intero=True)


def _valuta_soglia(soglia, *, cresce=True, messaggio_errore="", eta_max_fn=None):
    """Synthetic tool: admissible above `soglia` (cresce) or below it (not cresce)."""

    def _v(valore):
        ammissibile = (valore >= soglia) if cresce else (valore <= soglia)
        eta = eta_max_fn(valore) if eta_max_fn else (0.5 if ammissibile else 1.5)
        return Campione(valore=valore, esito="ammissibile" if ammissibile else "non_ammissibile", eta_max=eta)

    return _v


def test_monotona_crescente_verso_minimo():
    r = cerca(_griglia(), _valuta_soglia(6), "auto")
    assert r.esito == "trovato"
    assert r.verso == "minimo"
    assert r.valore == Decimal(6)
    assert r.affidabile


def test_monotona_decrescente_verso_massimo():
    r = cerca(_griglia(), _valuta_soglia(6, cresce=False), "auto")
    assert r.esito == "trovato"
    assert r.verso == "massimo"
    assert r.valore == Decimal(6)


def test_tutto_ammissibile_con_trend_eta_decrescente_verso_da():
    def v(valore):
        return Campione(valore=valore, esito="ammissibile", eta_max=1.0 - float(valore) / 100)

    r = cerca(_griglia(), v, "auto")
    assert r.esito == "estremo_sufficiente"
    assert r.valore == Decimal(0)


def test_tutto_ammissibile_senza_trend():
    def v(valore):
        return Campione(valore=valore, esito="ammissibile", eta_max=0.5)

    r = cerca(_griglia(), v, "auto")
    assert r.esito == "estremo_sufficiente"
    assert r.valore is None


def test_nessun_valore_ammissibile():
    def v(valore):
        return Campione(valore=valore, esito="non_ammissibile", eta_max=2.0)

    r = cerca(_griglia(), v, "auto")
    assert r.esito == "nessun_valore"
    assert r.valore is None


def test_due_finestre_non_monotono():
    def v(valore):
        ammissibile = valore in (2, 3, 7, 8)
        return Campione(valore=valore, esito="ammissibile" if ammissibile else "non_ammissibile", eta_max=0.5)

    r = cerca(_griglia(), v, "auto")
    assert not r.affidabile
    assert "non è monotono" in r.motivi[0]


def test_banda_di_errore_alla_bordatura_e_limite_validita():
    def v(valore):
        if valore < 3:
            return Campione(valore=valore, esito="errore", eta_max=None, messaggio="fuori range")
        return Campione(valore=valore, esito="ammissibile", eta_max=0.5)

    r = cerca(_griglia(), v, "auto")
    assert r.esito == "limite_validita"
    assert not r.affidabile
    assert r.valore == Decimal(3)
    assert any("fuori range" in m and "limite di validità" in m for m in r.motivi)


def test_errore_durante_la_bisezione():
    """A validity gap invisible to sampling (grid big enough that only some points are sampled):
    the sampled points look like a clean N..N A..A boundary, but a value inside the bisection
    interval — never directly sampled — raises `errore`."""

    def v(valore):
        if 59 <= valore <= 61:
            return Campione(valore=valore, esito="errore", eta_max=None, messaggio="metodo non applicabile")
        ammissibile = valore >= 62
        return Campione(valore=valore, esito="ammissibile" if ammissibile else "non_ammissibile", eta_max=0.5)

    r = cerca(_griglia(100), v, "auto")
    assert r.esito == "trovato"
    assert not r.affidabile
    assert any("non è applicabile" in m for m in r.motivi)


def test_verso_forzato_coerente_con_la_sequenza():
    r = cerca(_griglia(), _valuta_soglia(6), "minimo")
    assert r.esito == "trovato"
    assert r.valore == Decimal(6)


def test_verso_forzato_minimo_con_da_gia_ammissibile():
    r = cerca(_griglia(), _valuta_soglia(-5), "minimo")  # everything admissible, da included
    assert r.esito == "estremo_sufficiente"
    assert r.valore == Decimal(0)


def test_verso_forzato_in_contraddizione_con_la_sequenza_cade_in_non_monotona():
    r = cerca(_griglia(), _valuta_soglia(6), "massimo")  # sequence is N..N A..A, "massimo" forced
    assert not r.affidabile


def test_nuovo_avviso_alla_risposta_rende_inaffidabile():
    def v(valore):
        ammissibile = valore >= 6
        avvisi = ("Nuovo avviso",) if valore == 6 else ()
        return Campione(valore=valore, esito="ammissibile" if ammissibile else "non_ammissibile", eta_max=0.5, avvisi_nuovi=avvisi)

    r = cerca(_griglia(), v, "auto")
    assert r.esito == "trovato"
    assert not r.affidabile
    assert any("Nuovo avviso" in m for m in r.motivi)


def test_orientamento_incoerente_dopo_essere_fissato_non_e_gestito_qui():
    """`ricerca.py` is orientation-agnostic: it only sees admissible/non-admissible/errore, already
    decided by the caller's `valuta`. The incoherence flag itself is `sfruttamento.py`'s job
    (see test_sfruttamento.py); this only checks the search still finds a boundary in that case."""
    r = cerca(_griglia(), _valuta_soglia(6), "auto")
    assert r.esito == "trovato"


def test_limite_di_valutazioni_da_interrotta():
    r = cerca(_griglia(1000), _valuta_soglia(500), "auto", max_valutazioni=5)
    assert r.esito == "interrotta"
    assert not r.affidabile
    assert r.valutazioni <= 5


def test_limite_di_tempo_da_interrotta():
    r = cerca(_griglia(1000), _valuta_soglia(500), "auto", tempo_max_s=0.0)
    assert r.esito == "interrotta"
