<!-- GENERATED FILE — do not edit by hand. Source: src/strutture/data/divergences/*.json, rendered by `python -m strutture.shared.divergences.render`. -->

# Divergences — `ntc-site-seismic`

## Errori del foglio

| titolo | foglio | corretto | clausola | impatto | strumenti | modalità Excel |
|---|---|---|---|---|---|---|
| Il coefficiente di amplificazione stratigrafica Ss per il suolo B ha un limite inferiore troppo basso | Ss e' limitato all'intervallo [0.40, 1.20] | Ss e' limitato all'intervallo [1.00, 1.20], come richiesto dalla Tab. 3.2.IV | NTC2018 Tab. 3.2.IV | nessuno sul caso golden (valore grezzo 1.3045, limitato a 1.20 in entrambi i modi); la divergenza compare solo per F0*ag alti, es. F0=2.5, ag=1.1g: foglio da' Ss=0.40, corretto da' Ss=1.00 | sisma-parametri-sito, sisma-completo, muro-sostegno | riprodotta |
| La vita di riferimento VR non ha il minimo di 35 anni | VR = VN*Cu senza limite inferiore, puo' scendere sotto 35 anni | VR = max(VN*Cu, 35) come richiesto | NTC2018 §2.4.3 | nessuno sul caso golden (VN=50, Cu=1, VR=50); per VN=10, classe I (Cu=0.7): foglio da' VR=7, corretto da' VR=35 | sisma-vita-riferimento, sisma-completo | riprodotta |
