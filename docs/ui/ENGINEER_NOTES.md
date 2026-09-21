# Note dell'ingegnere — vocabolario di sezione, simboli, evidenziazione

Convenzioni ricavate dai 9 strumenti "carichi" (`hints_loads.json`), da riusare identiche sugli
strumenti di elemento in lavorazione (travi, pilastri, mensole, fessurazione, muro di sostegno,
colonna in acciaio, incendio). Non inventare titoli nuovi: se un campo non rientra qui, aggiungerlo.

## 1. Ordine e titoli delle sezioni di input (obbligatorio, sempre in quest'ordine)
1. `Sito` — comune/provincia, zona, altitudine, categoria di sottosuolo/topografica, esposizione.
2. `Geometria` — luce, campata, sezione, altezza, copriferro (`Geometria della sezione` se coesistono luce e sezione).
3. `Materiali` — calcestruzzo (`f_ck`, `γ_c`), acciaio (`f_yk`, `f_sk`, `γ_s`), terreno (`φ'`, `c'`, `γ`), legno.
4. `Azioni` — `G_1`, `G_2`, `Q_k`, `ψ_0/ψ_1/ψ_2`, azioni sismiche, spinte; `Sollecitazioni di progetto` se si inseriscono direttamente `M_Ed`, `V_Ed`, `N_Ed`.
5. `Combinazione` / `Stato limite` — SLU/SLE, SLO-SLD-SLV-SLC, rara/frequente/quasi permanente, classe di esposizione.
6. `Parametri di calcolo` / `Campionamento` — numero di sezioni, passo, tolleranze, curva di incendio, durata `t`.
7. `Avanzate` — sempre ultima, chiusa di default; contiene `legacy_compat`, etichettato
   «Riproduci il foglio Excel originale (errori inclusi)», e ogni campo di sola compatibilità
   (es. `neve_sheet_as_m`). Mai in mezzo ai dati di progetto.

Regole: un campo "alternativa a" (zona vs comune) sta nella stessa sezione del campo che
sostituisce, con etichetta «… (se nota, in alternativa al comune)». I campi condizionali
(angoli di falda 1/2) restano nella sezione geometrica e vengono nascosti, non spostati.

## 2. Etichette
Frase breve in italiano corrente, prima lettera maiuscola, niente maiuscoletto né ALL-CAPS.
Vietati nell'etichetta: riferimenti a celle o fogli (`Tabelle!M1`, `Sisma!I31`), nomi di
campo Python, «(parametrico)», «None se…», il nome della modalità legacy. La condizione di
obbligatorietà non va nell'etichetta ma nel messaggio di errore al campo. Il riferimento di
norma (§) va nel margine della riga di risultato, non dentro l'etichetta.

## 3. Simboli (NTC 2018, `symbol` hint)
Underscore = pedice, greche in Unicode, mai LaTeX. Il simbolo è la chiave di lettura:
la riga si legge `simbolo = valore unità §clausola`. Set da riusare:
`f_ck f_cd f_yk f_yd γ_c γ_s γ_G γ_Q ψ_0 ψ_2 M_Ed M_Rd V_Ed V_Rd N_Ed N_Rd
λ λ_lim χ N_b,Rd ρ A_s A_s,min x/d ε_s w_k σ_s K_a K_p e/B q_lim θ_E θ_R
q_sk C_E C_t μ_1 v_b,0 c_a c_r v_r c_e(z) q_b p(z) c_pe a_g F_0 T*_C S_S S_T S C_C
T_B T_C T_D η q S_e(T) S_d(T) V_N C_U V_R T_R`.
Ogni grandezza adimensionale dichiara comunque l'unità `-`: nessuna colonna unità vuota.

## 4. Risultati: gerarchia ed evidenziazione
`highlight` = massimo 3 campi, e sono i valori che finiscono in relazione: il **valore di
progetto** (q_s, p(H), M_Rd, V_Rd, N_b,Rd, w_k, e/B), il **coefficiente di sfruttamento**
`M_Ed/M_Rd` e l'**esito**. Non evidenziare mai i valori intermedi (k_r, z_0, C_C, S_S):
restano nel gruppo "Passaggi di calcolo", leggibili ma non in giallo. Per gli strumenti di
verifica la riga di esito va sopra tutto: «Verifica soddisfatta — sfruttamento 0,82»,
con parola + icona + barra, mai solo colore. Numeri: it-IT, 4 cifre significative,
valore pieno nel `title` e nella copia.

## 5. Gruppi di output e tabelle
I modelli annidati diventano sezioni con titolo italiano ("Coefficienti di amplificazione",
"Periodi caratteristici dello spettro", "Direzione 1 — vento perpendicolare al lato b"),
non il nome del modello. Le tuple di righe diventano tabella + grafico (`chart`) con una
sola grandezza per asse; per i profili lungo l'altezza x = quota. Per gli elementi: diagramma
`M(x)`/`V(x)`, `σ_c`-`σ_s` lungo la sezione, `f_y(t)` per l'incendio, tensioni sul terreno
per il muro seguono lo stesso contratto.

## 6. Stampa della relazione (identica per tutti gli strumenti)
Cartiglio: committente/progetto (campo libero salvato), elemento, strumento, norma
(`norm` dello schema), data, versione, modalità (standard oppure «foglio Excel»).
Poi, in quest'ordine: echo integrale degli input raggruppati come al §1, i passaggi con
simbolo-valore-unità-clausola, i risultati governanti, la tabella dei dati, il grafico,
l'esito delle verifiche. Senza echo degli input e senza modalità la pagina non è firmabile.
