"""Tool 4 — verifica-sle-tensioni: limitazione delle tensioni in esercizio, sezione parzializzata
(stadio II) in campo elastico, n=15, NTC2018 §4.1.2.2.5 (combinazioni rara e quasi permanente).

La profondità dell'asse neutro parzializzato x è calcolata da
`strutture.shared.section_geometry.cracked_neutral_axis` (sezione semplicemente armata: As2=0,
d2=0 — coincide esattamente con la formula del foglio Z38 quando non c'è armatura compressa); il
braccio di leva elastico (d - x/3) è comune alle verifiche in entrambe le combinazioni.
"""
from strutture.shared.divergences import legacy
from strutture.shared.section_geometry import cracked_neutral_axis

from .models import Combinazione, SleTensioniOutput

COEFF_SIGMA_C_RARA = 0.60  # NTC2018 §4.1.2.2.5 — combinazione rara, limite tensione cls
COEFF_SIGMA_C_QUASI_PERMANENTE = 0.45  # NTC2018 §4.1.2.2.5 — combinazione quasi permanente, limite tensione cls
COEFF_SIGMA_S = 0.80  # NTC2018 §4.1.2.2.5 — limite tensione armatura, entrambe le combinazioni
SIGMA_S_LIMITE_LEGACY_MPA = 360.0  # foglio Z42: IF(Z41<360,...) cablato, corretto solo per B450C (fyk=450)
HOMOGENISATION_N = 15.0  # NTC2018 §4.1.2.2.5 — coefficiente di omogeneizzazione n = Es/Ec
MEDIA_A_STADIO_II_FATTORE = 1e6  # kNm -> N*mm


def braccio_leva_elastico_mm(d_mm: float, x_mm: float) -> float:
    """d - x/3, braccio di leva della sezione parzializzata [mm]."""
    return d_mm - x_mm / 3.0


def sigma_calcestruzzo_MPa(med_kNm: float, b_mm: float, x_mm: float, braccio_mm: float) -> float:
    """sigma_c = 2*Med/(b*x*braccio) [MPa] (Med,rara/qp [Z39/Z46])."""
    return 2.0 * med_kNm * MEDIA_A_STADIO_II_FATTORE / (b_mm * x_mm * braccio_mm)


def sigma_acciaio_MPa(med_kNm: float, as_o_mm2: float, braccio_mm: float) -> float:
    """sigma_s = Med/(As,o*braccio) [MPa] (Med,rara/qp [Z41/ricalcolo Z53])."""
    return med_kNm * MEDIA_A_STADIO_II_FATTORE / (as_o_mm2 * braccio_mm)


def limite_sigma_acciaio_MPa(fyk_MPa: float, *, legacy_compat: bool = False) -> float:
    """Limite di tensione nell'acciaio, valido per entrambe le combinazioni.

    `legacy_compat=True` riproduce il valore 360 MPa cablato in cella (Z42), corretto solo per
    B450C (fyk=450 -> 0.8*450=360); per qualunque altro grado di acciaio selezionato è una
    verifica sbagliata (vedi docs/divergences/ca-travi.md). `legacy_compat=False` applica
    0.80*fyk dinamicamente, come già fa il foglio per il cls (Z47/Y47).
    """
    if legacy("ca-travi/limite-sigma-acciaio-sle-fisso", legacy_compat):
        return SIGMA_S_LIMITE_LEGACY_MPA
    return COEFF_SIGMA_S * fyk_MPa


def verifica_sle_tensioni(
    *,
    b_mm: float,
    d_mm: float,
    as_o_mm2: float,
    med_rara_kNm: float,
    med_qp_kNm: float,
    fck_MPa: float,
    fyk_MPa: float,
    combinazione: Combinazione,
    legacy_compat: bool = False,
) -> SleTensioniOutput:
    x_mm = cracked_neutral_axis(b_mm, d_mm, 0.0, as_o_mm2, 0.0, HOMOGENISATION_N).x_mm
    braccio_mm = braccio_leva_elastico_mm(d_mm, x_mm)

    sigma_c_rara_MPa = sigma_calcestruzzo_MPa(med_rara_kNm, b_mm, x_mm, braccio_mm)
    sigma_s_rara_MPa = sigma_acciaio_MPa(med_rara_kNm, as_o_mm2, braccio_mm)
    sigma_c_qp_MPa = sigma_calcestruzzo_MPa(med_qp_kNm, b_mm, x_mm, braccio_mm)
    sigma_s_qp_MPa = sigma_acciaio_MPa(med_qp_kNm, as_o_mm2, braccio_mm)
    sigma_s_combinazione_MPa = sigma_s_rara_MPa if combinazione == "Frequente" else sigma_s_qp_MPa

    return SleTensioniOutput(
        x_mm=x_mm,
        sigma_c_rara_MPa=sigma_c_rara_MPa,
        sigma_s_rara_MPa=sigma_s_rara_MPa,
        sigma_c_qp_MPa=sigma_c_qp_MPa,
        sigma_s_qp_MPa=sigma_s_qp_MPa,
        sigma_s_combinazione_MPa=sigma_s_combinazione_MPa,
        limite_sigma_c_rara_MPa=COEFF_SIGMA_C_RARA * fck_MPa,
        limite_sigma_c_qp_MPa=COEFF_SIGMA_C_QUASI_PERMANENTE * fck_MPa,
        limite_sigma_s_MPa=limite_sigma_acciaio_MPa(fyk_MPa, legacy_compat=legacy_compat),
    )
