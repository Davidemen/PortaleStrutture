<!-- GENERATED FILE — do not edit by hand. Source: src/strutture/data/divergences/*.json, rendered by `python -m strutture.shared.divergences.render`. -->

# Divergences — `materials`

## Errori del foglio

| titolo | foglio | corretto | clausola | impatto | strumenti |
|---|---|---|---|---|---|
| Le proprietà dell'acciaio strutturale non considerano la fascia di spessore dell'elemento | una sola coppia fyk/fuk per classe, sempre la fascia t<=40mm, anche per spessori maggiori | la fascia è scelta in base allo spessore reale t, come richiesto da EN1993-1-1 Tab. 3.1 | EN1993-1-1 §3.2.1, Tab. 3.1 | S355, t=60mm: fyk 355 -> 335 MPa (-5,6%, il foglio è non conservativo per spessori >40mm) |  |
| fck del calcestruzzo è calcolato come 0,83·Rck invece del valore letterale di Tab. 4.1.I | fck = 0,83·Rck per ogni classe (es. C35/45 -> fck=37,35), un'approssimazione, non il valore letterale della classe; solo la riga C35/45 del foglio fessurazione è già corretta a 35 a mano | fck usa il valore letterale di Tab. 4.1.I per ogni classe | NTC2018 §4.1.2.1.1.1, Tab. 4.1.I | caso peggiore C35/45: fck 37,35 -> 35,0 MPa (-6,3%); fcd 21,165 -> 19,833 MPa (-6,3%, il foglio è non conservativo) | ca-trave-rettangolare, ca-mensola-tozza, ca-pilastro-rettangolare, ca-pilastro-circolare, ca-apertura-fessure |

## Aggiornamenti normativi

| titolo | foglio | corretto | clausola | impatto | strumenti |
|---|---|---|---|---|---|
| Il catalogo acciai per armatura include gradi storici non più ammessi dalla normativa vigente | il catalogo unificato include B500C, FeB22k/FeB32k/FeB38k/FeB44k e RB500W, gradi non più ammessi da NTC2018 §11.3.2 Tab. 11.3.Ia per nuove armature ordinarie in Italia | ogni proprietà acciaio riporta un flag legacy_grade che segnala i gradi non più ammessi; i valori numerici restano quelli del foglio | NTC2018 §11.3.2, Tab. 11.3.Ia | nessuno sui valori numerici, solo un flag informativo | ca-trave-rettangolare, ca-mensola-tozza, ca-pilastro-rettangolare, ca-pilastro-circolare |

## Da verificare

| titolo | foglio | corretto | clausola | impatto | strumenti |
|---|---|---|---|---|---|
| I gradi acciaio S420/S460 non sono verificabili contro un valore tabulato del foglio | il foglio tabula solo S235, S275, S355 | S420/S460 aggiunti con i valori standard EN1993-1-1 Tab. 3.1 per acciai normalizzati a grana fine, ma non verificabili contro un valore di cella; il grado S450 non è implementato | EN1993-1-1 Tab. 3.1, EN10025-3 |  |  |
