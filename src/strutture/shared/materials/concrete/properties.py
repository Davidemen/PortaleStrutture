"""Composes the concrete class chain into one result (NTC2018 §4.1.2.1.1.1)."""
from .fcd import fcd, fctd
from .fck import fck
from .models import ConcreteClass, ConcreteProperties
from .rck import rck
from .resistenze import ecm, fcm, fctk, fctm
from .tables import ALPHA_CC, GAMMA_C


def concrete_properties(
    classe: ConcreteClass,
    *,
    legacy_compat: bool = False,
    gamma_c: float = GAMMA_C,
    alpha_cc: float = ALPHA_CC,
) -> ConcreteProperties:
    """Full mechanical property set for a concrete class."""
    rck_mpa = rck(classe)
    fck_mpa = fck(classe, legacy_compat=legacy_compat)
    fcm_mpa = fcm(fck_mpa)
    fctm_mpa = fctm(fck_mpa)
    fctk_mpa = fctk(fctm_mpa)
    return ConcreteProperties(
        classe=classe,
        rck_MPa=rck_mpa,
        fck_MPa=fck_mpa,
        fcm_MPa=fcm_mpa,
        ecm_MPa=ecm(fcm_mpa),
        fctm_MPa=fctm_mpa,
        fctk_MPa=fctk_mpa,
        fcd_MPa=fcd(fck_mpa, gamma_c=gamma_c, alpha_cc=alpha_cc),
        fctd_MPa=fctd(fctk_mpa, gamma_c=gamma_c),
    )
