<!-- GENERATED FILE — do not edit by hand. Source: src/strutture/data/divergences/*.json, rendered by `python -m strutture.shared.divergences.render`. -->

# Divergences — `ca-mensole`

## Errori del foglio

| titolo | foglio | corretto | clausola | impatto | strumenti | modalità Excel |
|---|---|---|---|---|---|---|
| L'acciaio FeB22k è selezionabile dal menu ma assente dalla tabella dei materiali | selezionando FeB22k dal menu a tendina, la ricerca in tabella restituisce un errore che si propaga ai risultati | usa la tabella acciai unificata che include FeB22k (fyk=215 MPa) |  | nessuno (il caso golden usa B450C) | ca-mensola-tozza | riprodotta |
| La capacità globale della mensola non è limitata dal puntone di calcestruzzo | PR = PRS + 0,8·ΔPR senza limite, e la gerarchia confronta con PRC il solo PRS: con armatura inclinata (ΔPR > 0) la mensola può risultare verificata mentre il carico supera la resistenza del puntone | PR = min(PRS + 0,8·ΔPR; PRC): il puntone limita la capacità globale (NTC2018 §4.1.6.1.3 / EN 1992-1-1 §6.5.2: la resistenza del puntone è un limite del modello tirante-puntone) | NTC2018 §4.1.6.1.3 / EN 1992-1-1 §6.5.2 | nessuno sul caso guida (ΔPR = 0); non cautelativo fino a 0,8·ΔPR con armatura inclinata | ca-mensola-tozza | riprodotta |
| Il coefficiente c restituisce un testo invece di un numero su uno dei due rami | restituisce la stringa "1,5" sul ramo SI e il numero 1 sul ramo NO; Excel converte automaticamente la stringa nei calcoli successivi | restituisce sempre un numero (1,0 o 1,5) |  | nessuno (il caso golden usa il ramo NO, c=1 in entrambe le modalità) | ca-mensola-tozza | NON riprodotta — Il bug di tipo (stringa vs numero) non è riproducibile in un modello Pydantic tipizzato: coefficiente_c restituisce sempre un numero, identico nelle due modalità. |

## Da verificare

| titolo | foglio | corretto | clausola | impatto | strumenti | modalità Excel |
|---|---|---|---|---|---|---|
| Continuità non verificata tra i due rami della formula dell'armatura di sospensione al variare di a/h | As,lnk = 0,25·As,hor se a<0,5h, altrimenti 0,5·PEd/fyd, senza raccordo verificato tra i due rami alla soglia | mantenuto identico al foglio in entrambe le modalità, in attesa di conferma della clausola di riferimento |  |  | ca-mensola-tozza | NON riprodotta — La formula è mantenuta identica al foglio in entrambe le modalità in attesa di conferma della clausola: armature() non riceve legacy_compat. |
| Le costanti delle formule puntone-tirante (0,2; 0,4; 0,8; 0,9; 1,5) non sono verificate contro il testo NTC2018 | le formule di capacità (PRS, PRC, ΔPR, l=a+0,2d, c=1,5) corrispondono a una formulazione nota di un manuale di progettazione ma non sono verificate indipendentemente contro il testo NTC2018 | riprodotte come sono in entrambe le modalità, in attesa di conferma |  |  | ca-mensola-tozza | NON riprodotta — Le costanti sono riprodotte identiche in entrambe le modalità in attesa di conferma: capacita() non riceve legacy_compat. |
