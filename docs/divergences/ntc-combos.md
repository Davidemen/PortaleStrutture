<!-- FILE GENERATO — non modificare a mano. Origine: src/strutture/data/divergences/*.json, prodotto da `python -m strutture.shared.divergences.render`. -->

# Correzioni — `ntc-combos`

## Aggiornamenti normativi

| titolo | foglio | corretto | clausola | impatto | strumenti | modalità Excel |
|---|---|---|---|---|---|---|
| Il coefficiente gamma_G2 favorevole era ancora il valore NTC2008 | Il coefficiente gamma_G2 favorevole (carichi permanenti non strutturali) era impostato a 0.0 in tutte e tre le righe di approccio (EQU/A1/A2), il valore previsto dalla NTC2008. | gamma_G2 favorevole e' 0.8 in tutte e tre le righe, il valore NTC2018. | NTC2018 Tab. 6.2.I/6.2.II §6.2.1 | nessuno su qualunque caso golden/oracolo attuale (l'unico consumatore, muro-sostegno, legge solo i campi gamma_G1); latente per i futuri consumatori | muro-sostegno | NON riprodotta — shared.ntc_combos non ha parametro legacy_compat: la tabella FATTORI_AZIONI contiene solo il valore corretto 0,8, applicato sempre; non esiste un ramo che riproduca il vecchio 0,0 |
| La tabella dei coefficienti di resistenza non includeva la riga per la verifica a ribaltamento | La tabella elencava solo 3 delle 4 righe della Tab. 6.5.I (capacita' portante, scorrimento, resistenza del terreno a valle), senza la riga 'ribaltamento', impedendo di ottenere un gamma_R per quella verifica. | Aggiunta la riga 'ribaltamento' (r1=1.0, r2=1.15, r3=1.15) alla tabella e alla lista dei valori ammessi. | NTC2018 Tab. 6.5.I | nessuno su qualunque caso golden/oracolo attuale; sblocca la verifica a ribaltamento del muro di sostegno | muro-sostegno | NON riprodotta — shared.ntc_combos non ha parametro legacy_compat: la tabella FATTORI_RESISTENZA include sempre la riga 'ribaltamento'; non esiste una modalità legacy che la ometta |
