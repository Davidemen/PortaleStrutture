"""EN 1992-1-1 §6.5.2(1) strength-reduction factor for cracked concrete, ν' = 1 - fck/250."""

FCK_LIMIT = 250.0


def nu_prime(fck_MPa: float) -> float:
    if fck_MPa <= 0:
        raise ValueError(f"fck_MPa must be positive, got {fck_MPa}")
    return 1.0 - fck_MPa / FCK_LIMIT
