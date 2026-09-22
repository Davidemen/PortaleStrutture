"""Verified restatement (docs/architecture-phase2.md §6, wave-3 adoption) of the two table lookups
`vento-pressione` reads from `tables.py`: the wind-zone parameters v_b,0/a_0/k_s (`zona_parametri`,
NTC2018 §3.3.1 Tab. 3.3.I — `k_a`, the superseded NTC2008 coefficient, is `legacy_only` and never
appears here) and the exposure-category parameters k_r/z_0/z_min (`categoria_parametri`, NTC2018
§3.3.7 Tab. 3.3.II). Neither has a formula an engineer would write — each is a pure table lookup, so
each gets a short `Passo` whose `formula` is the identifier itself (docs/architecture-phase2.md §6),
with a `nota` naming the table and the key. The calculation code is never touched."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import VentoPressioneInput, VentoPressioneOutput

CLAUSOLA_ZONA = "NTC2018 §3.3.1 Tab. 3.3.I"
CLAUSOLA_CATEGORIA = "NTC2018 §3.3.7 Tab. 3.3.II"


def traccia_zona_e_categoria(inputs: VentoPressioneInput, output: VentoPressioneOutput) -> Traccia:
    """6 passi di lookup: v_b,0/a_0/k_s dalla zona vento, k_r/z_0/z_min dalla categoria di esposizione."""
    return Traccia(
        titolo="Zona vento e categoria di esposizione",
        passi=(
            _passo_lookup("v_b,0", output.vb0, "m/s", CLAUSOLA_ZONA, f"Velocità base di riferimento, zona vento {output.zona}."),
            _passo_lookup("a_0", output.a0, "m", CLAUSOLA_ZONA, f"Altitudine di riferimento, zona vento {output.zona}."),
            _passo_lookup("k_s", output.ks, "-", CLAUSOLA_ZONA, f"Coefficiente di zona per il coefficiente di altitudine, zona vento {output.zona}."),
            _passo_lookup("k_r", output.kr, "-", CLAUSOLA_CATEGORIA, f"Fattore di terreno, categoria di esposizione {inputs.categoria_esposizione}."),
            _passo_lookup("z_0", output.z0, "m", CLAUSOLA_CATEGORIA, f"Lunghezza di rugosità del terreno, categoria di esposizione {inputs.categoria_esposizione}."),
            _passo_lookup("z_min", output.zmin, "m", CLAUSOLA_CATEGORIA, f"Quota minima del profilo di pressione, categoria di esposizione {inputs.categoria_esposizione}."),
        ),
    )


def _passo_lookup(simbolo: str, valore: float, unita: str, clausola: str, nota: str) -> Passo:
    return Passo(
        simbolo=simbolo, formula=simbolo,
        valori=(Valore(simbolo=simbolo, valore=valore, unita=unita),),
        risultato=valore, unita=unita, clausola=clausola, nota=nota,
    )
