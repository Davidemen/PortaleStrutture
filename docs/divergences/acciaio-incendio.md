<!-- FILE GENERATO — non modificare a mano. Origine: src/strutture/data/divergences/*.json, prodotto da `python -m strutture.shared.divergences.render`. -->

# Correzioni — `acciaio-incendio`

## Errori del foglio

| titolo | foglio | corretto | clausola | impatto | strumenti | modalità Excel |
|---|---|---|---|---|---|---|
| La resistenza a rottura a 20°C dell'acciaio S275 non viene mai selezionata correttamente | La formula a cascata per fu(20°C) testa due volte la stessa condizione sul grado sbagliato, cosicche' il ramo per S275 non scatta mai e S275 riceve per errore il valore di S355 (510 MPa) invece del proprio (430 MPa). | La cascata testa correttamente il grado selezionato: S235->360, S275->430, S355->510 MPa. | EN10025 - fu nominale S275 | nessuno con grado S355 (default, invariato); con grado S275: fu,theta a t=5min = 276.995 MPa (foglio) vs 233.545 MPa (corretto), -15.7% | acciaio-resistenza-incendio | riprodotta |
