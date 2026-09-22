<!-- FILE GENERATO — non modificare a mano. Origine: src/strutture/data/divergences/*.json, prodotto da `python -m strutture.shared.divergences.render`. -->

# Correzioni — `ec2-shared`

## Aggiornamenti normativi

| titolo | foglio | corretto | clausola | impatto | strumenti | modalità Excel |
|---|---|---|---|---|---|---|
| Il ramo av/2d della resistenza a punzonamento vicino all'appoggio non applicava il limite minimo vmin | n/a, bug del modulo condiviso, non del foglio sorgente: il termine calcestruzzo veniva moltiplicato per av/2d senza applicare prima il limite minimo vmin né il termine k1·σcp | max(termine_calcestruzzo, vmin)·av/2d + k1·σcp, come richiesto da EC2 §6.4.4(2) eq. 6.50, usato incondizionatamente in entrambe le modalità (non esisteva una distinzione legacy per questo punto) | EC2 §6.4.4(2) eq. 6.50 | nessun impatto sulle fixture golden/oracolo esistenti (il termine calcestruzzo supera già vmin in tutti i casi correnti) | ca-punzonamento, fond-plinto-su-pali | NON riprodotta — fix applicato incondizionatamente in entrambe le modalità legacy_compat, come dice il campo 'corretto': non esisteva (e non esiste) una distinzione legacy per questo punto |

## Scelte ingegneristiche

| titolo | foglio | corretto | clausola | impatto | strumenti | modalità Excel |
|---|---|---|---|---|---|---|
| Il coefficiente della resistenza massima a punzonamento/taglio vRd,max (0,4 vs 0,5) è una scelta dell'ingegnere | i fogli sorgente usano coefficienti diversi e non tutti riconducibili alla formula normativa (punzonamento: 0,2·0,85·fck/1,5 semplificato; plinto su pali: 0,5 con αcc=1,0; pavimento industriale: 0,5 NTC2018) | vRd,max = coeff_vrd_max·ν·fcd; l'ingegnere sceglie tra 0,4 (EN 1992-1-1:2004/A1:2014 §6.4.5(3), default) e 0,5 (EN 1992-1-1:2004 §6.4.5(3) + Appendice Nazionale italiana 2013); ogni strumento espone coeff_vrd_max come input avanzato esplicito, invece che una scelta silenziosa nel modulo condiviso | EC2 §6.4.5(3) | caso golden ca-punzonamento: uEd,0=0,376 MPa, ben sotto 3,967 MPa (foglio), 4,094 MPa (coeff=0,4) e 5,117 MPa (coeff=0,5), nessun cambio di esito | ca-punzonamento, fond-plinto-su-pali, fond-pavimento-industriale | riprodotta insieme a plinti-pali/coefficiente-vrd-max-taglio-punzonamento, ca-punzonamento/vrd-max-filo-pilastro-coefficiente-semplificato — coeff_vrd_max è un parametro esplicito passato dallo strumento chiamante (0,4 o 0,5), non un branch legacy_compat dentro shared.ec2_shear.v_rd_max, che applica sempre la stessa formula qualunque sia il coefficiente |

## Da verificare

| titolo | foglio | corretto | clausola | impatto | strumenti | modalità Excel |
|---|---|---|---|---|---|---|
| Area perimetro rettangolare del foglio punzonamento coincide con la formula standard solo per colonne quadrate | A_a = A·B + 4·MIN(A,B)·a + π·a² (foglio punzonamento) coincide con la formula standard A·B + 2·(A+B)·a + π·a² solo quando A=B | il modulo condiviso espone solo la formula standard; ca-punzonamento decide autonomamente la propria modalità 'riproduci il foglio', mantenendo ambigua la scelta per sezioni A≠B in attesa di conferma | EC2 §6.4.2 | vedi src/strutture/data/divergences/ca-punzonamento.json per l'impatto sul caso golden | ca-punzonamento | NON riprodotta — shared.ec2_shear.control_perimeter espone solo la formula standard, senza parametro legacy_compat; la scelta se riprodurre il foglio è del tutto interna a ca-punzonamento, che la traccia con un proprio id di registro |
| I coefficienti di resistenza dei nodi puntone-tirante del plinto su pali non corrispondono a quelli standard EC2 | il foglio del plinto su pali usa coefficienti apparentemente maggiorati per confinamento (CCC 1,18·(1-fck/250)/0,85·fcd; CCT 1 direzione (1-fck/250)·fcd; CCT 2 direzioni 0,88·(1-fck/250)·fcd) | il modulo condiviso espone solo i coefficienti standard EC2 §6.5.4(4) (k1=1,0 CCC, k2=0,85 CCT, k3=0,75 CTT), con k1/k2/k3 sovrascrivibili; fond-plinto-su-pali decide la propria formula 'riproduci il foglio' separatamente | EC2 §6.5.4(4) |  | fond-plinto-su-pali | riprodotta insieme a plinti-pali/nodi-puntone-tirante-coefficienti-non-standard — shared.ec2_strut_tie.sigma_rd_max espone solo i coefficienti standard EC2 (k1/k2/k3 sovrascrivibili), senza parametro legacy_compat; la formula 'riproduci il foglio' del plinto su pali è interamente responsabilità di fond-plinto-su-pali |
