# Indice della documentazione

Lingua: IT = italiano, EN = inglese. I documenti per il titolare sono tutti in italiano; le specifiche tecniche
e l'architettura, scritte durante lo sviluppo, restano in inglese (gli agenti le leggono senza problemi;
tradurle non aggiunge nulla e rischia errori nelle formule). I comandi sono identici su Windows e macOS.

## Per il titolare
| File | Lingua | Contenuto |
|---|---|---|
| `README.md` | IT | cos'è, avvio rapido, comandi essenziali |
| `docs/GUIDA_PROPRIETARIO.md` | IT | installazione, avvio, uso quotidiano, dati e backup, cose da fare, lavorare con gli agenti, problemi comuni, glossario |
| `docs/CONSEGNA.md` | IT | stato alla consegna: numeri dei test, cosa è in corso, lavori aperti, convenzioni |
| `docs/DECISIONI_DA_CONFERMARE.md` | IT | scelte ingegneristiche da confermare, dubbi aperti, lavori rinviati |
| `docs/VERIFICA_WINDOWS.md` | IT | controlli da fare una volta sul PC Windows |
| `docs/VERIFICA_MIDAS.md` | IT | verifica dell'importazione da MIDAS NX su un modello reale |
| `docs/VALIDAZIONE_STRUMENTI.md` | IT | validazione strumento per strumento: i sei passi, la tabella di stato (compilata a mano, conservata) e le schede generate da `scripts/validazione_strumenti.py` |
| `docs/divergences/*.md` (29 file) | IT | registro delle correzioni per unità, GENERATO dai JSON (`render`); si firma nell'app, pagina Registro |

## Per gli agenti di sviluppo
| File | Lingua | Contenuto |
|---|---|---|
| `CLAUDE.md`, `AGENTS.md` | IT | istruzioni operative: lingua, mappa, comandi, regole dure, ricette |
| `docs/BUILD_CONTRACT.md` | EN | contratto di costruzione: modularità, contratto Tool/Report, test (golden/oracle/unit), portabilità, registro, avvisi per campo |
| `docs/architecture.md` | EN | architettura generale del pacchetto, 6 ondate del porting, divergenze |
| `docs/architecture-batch2.md` | EN | secondo lotto (11 fogli): geotecnica, fondazioni, tabelle di ingresso, decisioni del committente D1–D5 (§9) |
| `docs/architecture-phase2.md` | EN | relazione con formule: notazione, parser, tracce `Passo`, harness |
| `docs/architecture-phase3.md` | EN | progetti ed elementi salvati: modello dati, blocco ottimistico, API |
| `docs/architecture-phase4.md` | EN | motore sezione M-N (poligono + barre) e capacità portante (EC7 Annesso D) |
| `docs/ROADMAP.md` | EN | piano delle fasi dopo il porting; fase 7; "Marked down" = rinviato |
| `docs/integrations/MIDAS.md` | EN | integrazione MIDAS NX: API, sicurezza (sola lettura, chiave, allow-list), forme delle risposte |
| `docs/specs/<unità>.md` | EN | specifica per foglio/strumento: celle, formule, casi di riferimento (§8), errori sospetti (§7) |
| `docs/ui/WORKBENCH_SPEC.md` | EN | specifica normativa dell'interfaccia (§0–17): layout, calcolo automatico, sintesi, schizzi, relazione (§10–11), barra laterale (§12), registro (§13), progetti (§14), "Usa in…" (§15), ritiro della modalità Excel (§16), avvisi con salto al campo (§17) |
| `docs/ui/DESIGN_SPEC.md` | EN | sistema di design: tipografia, colori, accessibilità, suggerimenti di schema (§4, §4b) |
| `docs/ui/ENGINEER_NOTES.md` | IT | vocabolario delle sezioni, simboli ed evidenziazioni per gli strumenti |
| `docs/ui/UI_BRIEF.md` | EN | brief iniziale dell'interfaccia (direzione "foglio di calcolo dell'ingegnere") |
| `docs/ui/REVIEW_FABLE_2026-09-21.md` | EN | revisione di design prima della messa in linea; risultati applicati |

## Specifiche per strumento (`docs/specs/`)
`acciaio.md` (COL, INC, TMP, SHR) · `ca-fessurazione.md` (SLE, FES, FSS) · `ca-mensole.md` (MEN) ·
`ca-pilastri.md`, `ca-pilastri-ntc2018.md`, `ca-pilastri-ec2.md` (PIR, PIC) · `ca-punzonamento.md` (PUN) ·
`ca-travi.md` (TRV, TNA) · `fond-plinti-isolati.md` (PLI) · `fond-plinti-pali.md` (PLP) ·
`fond-travi-collegamento.md` (TCO) · `geo-cedimenti-edometrico.md` (EDO) · `geo-cedimenti-elastico.md` (NEW, TG) ·
`muro-sostegno.md` (MUR) · `neve.md` (NEV, NAC) · `pavimento-industriale.md` (PAV) · `sisma.md` (SVR, SPS, SFS,
SSP, SIS) · `vento.md` (VEN) · `small-units.md` (CPE, TMP e unità minori). Il motore M-N (SMN) è in
`architecture-phase4.md`.
