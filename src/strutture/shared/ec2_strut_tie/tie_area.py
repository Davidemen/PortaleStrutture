"""EN 1992-1-1 §6.5.3/§9.8.1 tie: required rebar area to resist a tie's design tension force."""


def tie_area(f_kN: float, fyd_MPa: float) -> float:
    """As = F / fyd, returned in mm² (F in kN, fyd in MPa)."""
    if f_kN < 0:
        raise ValueError(f"f_kN must be non-negative, got {f_kN}")
    if fyd_MPa <= 0:
        raise ValueError(f"fyd_MPa must be positive, got {fyd_MPa}")
    return f_kN * 1000.0 / fyd_MPa
