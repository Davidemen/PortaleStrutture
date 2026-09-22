"""The `η_v` highlighted output (docs/architecture-phase2.md §6): governing utilisation across
taglio/punzonamento colonna/punzonamento palo (`tool.py::run`'s own `max(...)`). Informative summary
only, mirrors `relazione_puntoni_tiranti._passo_utilizzo_st` for `η_st`."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import PlintoSuPaliOutput


def traccia_utilizzo_taglio_punzonamento(output: PlintoSuPaliOutput) -> Traccia:
    """1 passo informativo: η_v = max(utilizzo taglio, punzonamento colonna, punzonamento palo)."""
    valori = (
        Valore(simbolo="η_taglio", valore=output.taglio.utilizzo, unita="-", descrizione="utilizzo a taglio, calcolato sopra"),
        Valore(simbolo="η_punz,col", valore=output.punzonamento.utilizzo, unita="-", descrizione="utilizzo a punzonamento al filo pilastro, calcolato sopra"),
        Valore(simbolo="η_punz,palo", valore=output.punzonamento_palo.utilizzo, unita="-", descrizione="utilizzo a punzonamento del palo d'angolo, calcolato sopra"),
    )
    formula = "max(" + ", ".join(v.simbolo for v in valori) + ")"
    passo = Passo(
        simbolo="η_v", formula=formula, valori=valori, risultato=output.utilizzo_taglio_punzonamento, unita="-",
        nota="Utilizzo governante fra taglio e punzonamento (indicatore di sintesi, non un Check autonomo).",
    )
    return Traccia(titolo="Utilizzo governante — taglio e punzonamento", passi=(passo,))
