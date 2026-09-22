from strutture.shared.dimensiona.sfruttamento import eta, impara_orientamenti, rapporto, valuta_esito
from strutture.shared.report import Check


def _check(name="V", value=None, limit=None, passed=True):
    return Check(name=name, passed=passed, value=value, limit=limit)


def test_rapporto_none_senza_value_o_limit():
    assert rapporto(_check(value=None, limit=1.0)) is None
    assert rapporto(_check(value=1.0, limit=None)) is None


def test_rapporto_none_con_limite_zero_o_segni_discordi():
    assert rapporto(_check(value=1.0, limit=0.0)) is None
    assert rapporto(_check(value=1.0, limit=-1.0)) is None


def test_rapporto_normale():
    assert rapporto(_check(value=3.0, limit=6.0)) == 0.5


def test_orientamento_diretto():
    campioni = (
        (_check(value=0.5, limit=1.0, passed=True),),
        (_check(value=2.0, limit=1.0, passed=False),),
    )
    assert impara_orientamenti(campioni)["V"] == "diretto"


def test_orientamento_inverso():
    campioni = (
        (_check(value=2.0, limit=1.0, passed=True),),
        (_check(value=0.5, limit=1.0, passed=False),),
    )
    assert impara_orientamenti(campioni)["V"] == "inverso"


def test_orientamento_contraddittorio_diventa_solo_esito():
    campioni = (
        (_check(value=2.0, limit=1.0, passed=True),),  # r=2 passed -> contradicts both readings alone,
        (_check(value=0.5, limit=1.0, passed=True),),  # combined with this it is neither diretto nor inverso
    )
    assert impara_orientamenti(campioni)["V"] is None


def test_orientamento_tutti_a_uno_e_solo_esito():
    campioni = ((_check(value=1.0, limit=1.0, passed=True),),) * 3
    assert impara_orientamenti(campioni)["V"] is None


def test_eta_diretto_e_inverso():
    assert eta(_check(value=0.5, limit=1.0), "diretto") == 0.5
    assert eta(_check(value=2.0, limit=1.0), "inverso") == 0.5


def test_valuta_esito_ammissibile_diretto():
    checks = (_check(name="A", value=0.5, limit=1.0, passed=True),)
    esito = valuta_esito(checks, {"A": "diretto"}, obiettivo=1.0, obiettivo_su_minimi=False)
    assert esito.ammissibile
    assert esito.eta_max == 0.5
    assert esito.governante == ("A", 0.5)


def test_valuta_esito_obiettivo_stretto_su_diretto():
    checks = (_check(name="A", value=0.9, limit=1.0, passed=True),)
    esito = valuta_esito(checks, {"A": "diretto"}, obiettivo=0.8, obiettivo_su_minimi=False)
    assert not esito.ammissibile


def test_valuta_esito_inverso_senza_obiettivo_su_minimi():
    checks = (_check(name="Amin", value=4.0, limit=1.0, passed=True),)  # η = 1/4 = 0.25, well under any target
    esito = valuta_esito(checks, {"Amin": "inverso"}, obiettivo=0.9, obiettivo_su_minimi=False)
    assert esito.ammissibile
    assert "Amin" in esito.senza_obiettivo


def test_valuta_esito_inverso_con_obiettivo_su_minimi_puo_fallire():
    checks = (_check(name="Amin", value=1.0, limit=1.0, passed=True),)  # η = 1
    esito = valuta_esito(checks, {"Amin": "inverso"}, obiettivo=0.5, obiettivo_su_minimi=True)
    assert not esito.ammissibile
    assert "Amin" not in esito.senza_obiettivo


def test_valuta_esito_check_non_passata_non_ammissibile():
    checks = (_check(name="A", value=0.1, limit=1.0, passed=False),)
    esito = valuta_esito(checks, {"A": "diretto"}, obiettivo=1.0, obiettivo_su_minimi=False)
    assert not esito.ammissibile


def test_valuta_esito_check_solo_esito_conta_solo_come_passata():
    checks = (_check(name="Dettaglio", value=None, limit=None, passed=True),)
    esito = valuta_esito(checks, {}, obiettivo=1.0, obiettivo_su_minimi=False)
    assert esito.ammissibile
    assert esito.solo_esito == ("Dettaglio",)


def test_valuta_esito_orientamento_incoerente_segnalato():
    checks = (_check(name="A", value=2.0, limit=1.0, passed=True),)  # r=2 but orientation says diretto (should fail)
    esito = valuta_esito(checks, {"A": "diretto"}, obiettivo=1.0, obiettivo_su_minimi=False)
    assert "A" in esito.incoerenze
