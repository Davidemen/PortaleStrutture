"""Clauses, γR and warning texts for the optional bearing-capacity check on the foundation soil —
split out of `capacita_portante_muro.py`, regola dura 12 dei moduli piccoli.
"""
from strutture.shared.ntc_combos import fattori_resistenza

from .combinazioni import SEISMIC_COMBOS
from .models import NomeCombo

CLAUSE_CAPACITA_PORTANTE = "NTC2018 §6.5.3.1.1, Tab. 6.5.I, §6.4.2.1 / EN1997-1 Annex D"
# HIGH finding: NTC2018 §6.4.2.1 offre due schemi non miscelabili — Approccio 2 (A1+M1+R3, i
# parametri caratteristici del terreno non ridotti, gamma_R=1.4/Tab. 6.5.I R3 statico) e Approccio
# 1 Combinazione 2 (A2+M2+R2, gamma_phi'=1.25 sul terreno, gamma_R=1.0). Questo modulo applica
# sempre i parametri caratteristici non ridotti al terreno DI FONDAZIONE (M1, vedi
# `_capacita_portante_riga` in `capacita_portante_muro.py`): questo e' coerente solo con le righe
# A1+M1 (STR_1/STR_2, lo stesso schema di `fond-plinto-isolato`) e con le sismiche (gamma_R
# dedicato §7.11.6.2.1, gia' separato sotto). GEO_1/GEO_2 (A2+M2) ed EQU_1/EQU_2 (approccio EQU)
# userebbero un gamma_R/uno schema di parametri geotecnici diverso (non implementato qui): restano
# quindi ESCLUSE da questa verifica piuttosto che essere valutate con lo schema sbagliato (prima:
# gamma_R=1.4 applicato anche a queste righe, fino a +92% di sovrastima della capacita' con
# omega=30 deg).
CLAUSE_CAPACITA_PORTANTE_SISMICA = (
    "NTC2018 §7.11.5.3.1 / §7.11.6.2.1 (formula statica dell'Annesso D, riduzione inerziale del "
    "terreno non implementata)"
)
COMBO_CAPACITA_PORTANTE: tuple[NomeCombo, ...] = ("STR_1", "STR_2") + SEISMIC_COMBOS
# NTC2018 Tab. 6.5.I γR per le opere di sostegno (capacità portante): R3 = 1.4 statico (identico a
# `ntc_combos.fattori_resistenza("capacita_portante").r3`, la stessa tabella già usata da
# ribaltamento/scorrimento in questo modulo); 1.2 sismico (§7.11.6.2.1) era già citato
# nell'avviso sotto prima che questo controllo esistesse, quindi è il valore confermato per questo
# pacchetto piuttosto che un nuovo numero da inventare (docs/BUILD_CONTRACT.md).
GAMMA_R_CAPACITA_PORTANTE_STATICO = fattori_resistenza("capacita_portante").r3
GAMMA_R_CAPACITA_PORTANTE_SISMA = 1.2
AVVISO_ECCENTRICITA_LIMITE = (
    "L'eccentricità è qui verificata solo contro |e| > B/2 (risultante fuori "
    "dalla fondazione), non contro i limiti di normativa dell'§6.4.2.1."
)
AVVISO_CAPACITA_PORTANTE = (
    "La verifica a collasso per capacità portante del terreno (NTC2018 §6.5.3.1.1, γR=1.4 statico / "
    "1.2 sismico, Tab. 6.5.I) non è calcolata da questo strumento: usare uno strumento geotecnico "
    "dedicato per confrontare la pressione di contatto con qlim, oppure compilare il blocco facoltativo "
    "'Terreno di fondazione'. " + AVVISO_ECCENTRICITA_LIMITE
)
AVVISO_TERRENO_IGNORATO_LEGACY = (
    "Modalità legacy_compat: il blocco 'Terreno di fondazione' è stato compilato ma viene ignorato "
    "(il foglio Excel originale non include una verifica di capacità portante)."
)
AVVISO_CAPACITA_PORTANTE_SISMICA = (
    "Capacità portante in condizioni sismiche: inerzia del terreno di fondazione non considerata, "
    "da confermare."
)
# HIGH finding: `terreno_profondita_posa_m` (D, models.py) non e' mai incrociata con la geometria
# del muro. Un D piu' grande dell'altezza fuori terra del muro e' un segnale forte che l'utente ha
# inserito la quota del piano campagna a MONTE (dove il terreno arriva quasi in sommita' al
# paramento) invece che a VALLE (dove D va misurato, per la mancia): D piu' grande produce sempre
# un q'/gamma' maggiore, quindi un esito meno cautelativo, mai piu' cautelativo, proprio quando
# l'utente crede di essere prudente aumentando D.
SOGLIA_PROFONDITA_POSA_SOSPETTA_M = 1.0  # D oltre 1 m e' gia' insolito per una mancia di fondazione
