"""Shared utilization/pass-fail step used by all three `ca_fessurazione` tools: every checked
row in the three sheets reduces to the same pattern, `IF(limite>agente,"ok","non verificato")`
plus a utilization ratio (`Limitazione delle tensioni!E13..E31`, `Apertura delle fessure!D48`,
`Apertura delle fessure SEMP!F21..F67`)."""


def utilizzo(agente: float, limite: float) -> float:
    """Tasso di sfruttamento = valore agente / valore limite."""
    if limite <= 0:
        raise ValueError(f"il valore limite deve essere positivo, ricevuto {limite}")
    return agente / limite


def verificato(agente: float, limite: float) -> bool:
    """True se il valore limite è maggiore del valore agente (verifica soddisfatta)."""
    return limite > agente
