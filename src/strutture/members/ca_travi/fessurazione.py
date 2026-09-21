"""Tool 5 — verifica-fessurazione: controllo indiretto dell'ampiezza di fessura senza calcolo
diretto di w, NTC2018 §4.1.2.2.4 + Circolare 7/2019 C4.1.2.2.4.5 (Tab. C4.1.II).

Il limite di tensione nell'acciaio è letto dalla tabella diametro-vs-classe di apertura
(`strutture.shared.rebar_catalog.sigma_limit_by_diameter`, Tab. C4.1.II) invece che calcolato:
`legacy_compat=True` riproduce l'esatto VLOOKUP a corrispondenza esatta del foglio (`#N/A` per
un diametro non tabulato, cella AI54 — bug §7.4 della spec, qui sollevato come `CalcError`);
`legacy_compat=False` interpola tra i due diametri della tabella più vicini.

La classe di apertura di fessura richiesta dalla normativa per la combinazione di
esposizione/carico/sensibilità dell'armatura è letta da
`strutture.shared.durability_cover.crack_width_limit` (Tab. 4.1.IV) e confrontata, come controllo
aggiuntivo di conformità, con la classe scelta manualmente dall'utente in cella Z54.
"""
from strutture.shared.durability_cover import crack_width_limit
from strutture.shared.rebar_catalog import sigma_limit_by_diameter
from strutture.shared.report import CalcError
from strutture.shared.tables import KeyNotFound

from .models import ClasseAperturaFessura, Combinazione, CondizioniAmbientali, FessurazioneOutput, SensibilitaArmatura

_CONDIZIONE_MAP: dict[CondizioniAmbientali, str] = {
    "Ordinarie": "ordinarie",
    "Aggressive": "aggressive",
    "Molto aggressive": "molto aggressive",
}
_COMBINAZIONE_MAP: dict[Combinazione, str] = {"Frequente": "frequente", "Quasi permanente": "quasi permanente"}
_SENSIBILITA_MAP: dict[SensibilitaArmatura, str] = {"Poco sensibile": "poco sensibile", "Sensibile": "sensibile"}


def diametro_massimo_mm(diametro_ferri1_mm: float, diametro_ferri2_mm: float) -> float:
    """Ø max = MAX(H12,H14), diametro governante per il controllo di fessurazione."""
    return max(diametro_ferri1_mm, diametro_ferri2_mm)


def classe_normativa(
    condizioni_ambientali: CondizioniAmbientali, combinazione: Combinazione, sensibilita_armatura: SensibilitaArmatura
) -> ClasseAperturaFessura | None:
    """Classe di apertura di fessura richiesta da NTC2018 Tab. 4.1.IV (None se è richiesta una
    verifica a decompressione anziché un limite di ampiezza di fessura)."""
    return crack_width_limit(
        _CONDIZIONE_MAP[condizioni_ambientali],
        _COMBINAZIONE_MAP[combinazione],
        _SENSIBILITA_MAP[sensibilita_armatura],
    )


def verifica_fessurazione(
    *,
    sigma_s_MPa: float,
    diametro_ferri1_mm: float,
    diametro_ferri2_mm: float,
    condizioni_ambientali: CondizioniAmbientali,
    combinazione: Combinazione,
    sensibilita_armatura: SensibilitaArmatura,
    classe_apertura_fessura: ClasseAperturaFessura,
    legacy_compat: bool = False,
) -> FessurazioneOutput:
    diametro_max_mm = diametro_massimo_mm(diametro_ferri1_mm, diametro_ferri2_mm)
    try:
        sigma_limite_MPa = sigma_limit_by_diameter(diametro_max_mm, classe_apertura_fessura, legacy_compat=legacy_compat)
    except KeyNotFound as exc:
        raise CalcError(
            f"nessun valore tabulato (Tab. C4.1.II) per Ø={diametro_max_mm} mm, classe "
            f"{classe_apertura_fessura!r}: il foglio restituirebbe #N/A (vedi divergenze ca-travi)"
        ) from exc

    return FessurazioneOutput(
        diametro_max_mm=diametro_max_mm,
        sigma_limite_MPa=sigma_limite_MPa,
        classe_normativa=classe_normativa(condizioni_ambientali, combinazione, sensibilita_armatura),
    )
