"""Verified restatement (docs/architecture-phase2.md) of `baricentro.py`/`inerzia.py`: area,
centroid and second moments of area of the composite section — plain statics, no EC3 clause (the
architecture brief's "cite the definition not a clause" case: `elementi.py`'s own docstring notes
downstream modules only ever see plain rectangle geometry, nothing member-specific).

Each element contributes a term to A/x_N/y_N (`baricentro.py`) built dynamically, one per ACTIVE
element (3 profile parts + up to 10 plates, `models.MAX_PIATTI`), mirroring how
`ca_travi.relazione_geometria._passo_as` builds a variable-length sum for a variable number of
rebar layers. I_x/I_y (`inerzia.py`) reuse the per-element Steiner CONTRIBUTIONS already exposed by
`ElementoRisultato.ix_i_cm4`/`iy_i_cm4` (own-axis inertia + A·Δ², EN — the parallel-axis theorem,
stated in the `descrizione` of each contribution rather than re-derived, the way the architecture
brief allows for a value the trace does not itself need to decompose further) instead of
re-deriving each element's own-axis inertia from scratch.

I_x,0/I_y,0 (`Sezione.ix_base_cm4`/`iy_base_cm4`) are the SAME statics applied to the base profile
alone (no plates, its own centroid): cited directly rather than re-run through the whole derivation
a second time, since nothing downstream needs their own per-element breakdown.
"""
from strutture.shared.relazione import Passo, Traccia, Valore

from .risultati import ElementoRisultato, Sezione


def traccia_geometria(elementi: tuple[ElementoRisultato, ...], sezione: Sezione) -> Traccia:
    """7 passi: A, x_N, y_N, I_x, I_y, I_x/I_x,0, I_y/I_y,0."""
    return Traccia(
        titolo="Area, baricentro e momenti d'inerzia della sezione composta",
        passi=(
            _passo_area(elementi, sezione), _passo_baricentro(elementi, sezione, "x"), _passo_baricentro(elementi, sezione, "y"),
            _passo_inerzia(elementi, sezione, "x"), _passo_inerzia(elementi, sezione, "y"),
            _passo_rapporto(sezione, "x"), _passo_rapporto(sezione, "y"),
        ),
    )


def _nomi_simboli(elementi: tuple[ElementoRisultato, ...]) -> tuple[str, ...]:
    return tuple(f"{i + 1}" for i in range(len(elementi)))


def _passo_area(elementi: tuple[ElementoRisultato, ...], sezione: Sezione) -> Passo:
    indici = _nomi_simboli(elementi)
    formula = " + ".join(f"A_{i}" for i in indici)
    valori = tuple(
        Valore(simbolo=f"A_{i}", valore=e.area_mm2, unita="mm2", descrizione=f"area, {e.nome.lower()}")
        for i, e in zip(indici, elementi, strict=True)
    )
    return Passo(
        simbolo="A", formula=formula, valori=valori, risultato=sezione.area_mm2, unita="mm2",
        clausola="Statica — A = ΣA_i", nota="Area totale della sezione composta (profilo base + piatti attivi).",
    )


def _passo_baricentro(elementi: tuple[ElementoRisultato, ...], sezione: Sezione, asse: str) -> Passo:
    indici = _nomi_simboli(elementi)
    coord_simbolo = "x" if asse == "x" else "y"
    formula = " + ".join(f"A_{i}*{coord_simbolo}_{i}" for i in indici) + " ) / A"
    formula = f"({formula}"
    coordinate = tuple(e.x_mm if asse == "x" else e.y_mm for e in elementi)
    valori = tuple(
        v for i, e, c in zip(indici, elementi, coordinate, strict=True)
        for v in (
            Valore(simbolo=f"A_{i}", valore=e.area_mm2, unita="mm2", descrizione=f"area, {e.nome.lower()}"),
            Valore(simbolo=f"{coord_simbolo}_{i}", valore=c, unita="mm", descrizione=f"baricentro proprio, {e.nome.lower()}"),
        )
    )
    valori = (*valori, Valore(simbolo="A", valore=sezione.area_mm2, unita="mm2", descrizione="calcolato sopra"))
    risultato = sezione.x_n_mm if asse == "x" else sezione.y_n_mm
    return Passo(
        simbolo=f"{coord_simbolo}_N", formula=formula, valori=valori, risultato=risultato, unita="mm",
        clausola=f"Statica — {coord_simbolo}_N = Σ(A_i·{coord_simbolo}_i)/A",
        nota="Baricentro della sezione composta, media pesata sulle aree.",
    )


def _passo_inerzia(elementi: tuple[ElementoRisultato, ...], sezione: Sezione, asse: str) -> Passo:
    indici = _nomi_simboli(elementi)
    simbolo_i = "Ix" if asse == "x" else "Iy"
    formula = " + ".join(f"{simbolo_i}_{i}" for i in indici)
    contributi = tuple(e.ix_i_cm4 if asse == "x" else e.iy_i_cm4 for e in elementi)
    valori = tuple(
        Valore(simbolo=f"{simbolo_i}_{i}", valore=c, unita="cm4",
               descrizione=f"contributo di {e.nome.lower()}: inerzia propria + A·Δ² (teorema di Steiner/asse parallelo)")
        for i, e, c in zip(indici, elementi, contributi, strict=True)
    )
    risultato = sezione.ix_cm4 if asse == "x" else sezione.iy_cm4
    simbolo_asse = "I_x" if asse == "x" else "I_y"
    return Passo(
        simbolo=simbolo_asse, formula=formula, valori=valori, risultato=risultato, unita="cm4",
        clausola=f"Statica — {simbolo_asse} = Σ(I_0,i + A_i·Δ_i²)",
        nota="Somma dei contributi di ciascun elemento, già comprensivi del trasporto rispetto al baricentro.",
    )


def _passo_rapporto(sezione: Sezione, asse: str) -> Passo:
    simbolo_asse = "I_x" if asse == "x" else "I_y"
    valore_composta = sezione.ix_cm4 if asse == "x" else sezione.iy_cm4
    valore_base = sezione.ix_base_cm4 if asse == "x" else sezione.iy_base_cm4
    risultato = sezione.rapporto_ix if asse == "x" else sezione.rapporto_iy
    return Passo(
        simbolo=f"{simbolo_asse}/{simbolo_asse},0", formula=f"{simbolo_asse} / {simbolo_asse},0",
        valori=(
            Valore(simbolo=simbolo_asse, valore=valore_composta, unita="cm4", descrizione="calcolato sopra"),
            Valore(simbolo=f"{simbolo_asse},0", valore=valore_base, unita="cm4",
                   descrizione="stessa definizione, applicata al solo profilo base (senza piatti), con il proprio baricentro"),
        ),
        risultato=risultato, unita="-",
        nota=f"Incremento di rigidezza flessionale rispetto al profilo non rinforzato, asse {'forte' if asse == 'x' else 'debole'}.",
    )
