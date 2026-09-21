"""ISO 834 nominal standard fire curve (EN1991-1-2 Annex A / acciaio-incendio!resistenza C9:C32)."""
import math

ISO834_AMBIENT_C = 20.0
ISO834_SLOPE = 345.0
ISO834_TIME_SCALE_MIN = 8.0


def gas_temperature_C(t_min: float) -> float:
    """θg(t) = 20 + 345·log10(8·t + 1), t in minutes. Unbounded; callers clamp/validate `t` themselves."""
    if t_min < 0:
        raise ValueError(f"t_min must be >= 0, got {t_min}")
    return ISO834_AMBIENT_C + ISO834_SLOPE * math.log10(ISO834_TIME_SCALE_MIN * t_min + 1)
