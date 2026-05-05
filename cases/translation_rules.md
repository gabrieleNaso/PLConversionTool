# Regole di traduzione (AWL -> IR -> XML TIA)

Questo documento raccoglie **regole generali** estratte dai casi in `cases/` (input + expected_output).

Obiettivo:
- avere un riferimento unico e stabile per capire *cosa* deve produrre il tool
- evitare fix “ad hoc”: ogni differenza va ricondotta a una regola qui

---

## 1) Principi

1. **Expected = verità assoluta**  
   Gli artefatti in `cases/expected_output/expected_outputN/` sono la reference corretta.  
   L’output del tool deve convergere lì (naming, cardinalità, logica, topologia).

2. **Bundle coerente, non singolo file**  
   Il risultato è un pacchetto (FB GRAPH + FC + DB) che deve essere coerente cross‑blocco:
   - ogni riferimento in `FlgNet` deve esistere nel DB owner corretto
   - naming identico tra FC/DB/FB

3. **Target simbolico**  
   Gli indirizzi fisici (I/Q/M/DBx.DBX…) possono comparire nel sorgente AWL e come evidenza diagnostica,
   ma il naming dei member e i path serializzati negli XML devono restare **simbolici**.

---

## 2) Struttura bundle e cardinalità (pattern “progetto”)

Dai reference (es. `expected_output1`) emerge che il bundle “di progetto” non è solo output auto del tool:

- FC “famiglia” con naming di progetto (es. `01 ... Alarms`, `04 ... Transitions`, ecc.)
- FB GRAPH “Sequence”
- DB di progetto:
  - DB “funzionali” (`... I-O`, `... HMI`, `... AUX`, `... PARAMETERS`, `... LEV2`)
  - DB aggregatori / runtime (`... SEQ`, `...`)

Regola: se l’expected ha DB aggregatori/runtime, vanno preservati (non sostituiti con DB auto per famiglia).

---

## 3) Naming target (blocchi e member)

### 3.1 Naming blocchi

Il naming deve aderire al reference del caso.  
Esempio (pattern visto in `expected_output1`):
- FC: `01 <Area> <Machine> Alarms`, `02 ... HMI`, `03 ... Aux`, `04 ... Transitions`, `06 ... Output`, `07 ... LEV2`
- FB GRAPH: `05 ... Sequence`
- DB: `<Machine> I-O`, `<Machine> HMI`, `<Machine> AUX`, `<Machine> PARAMETERS`, `<Machine> LEV2`, `<Machine> SEQ`, `<Machine>`

Se l’output del tool genera naming “auto”, serve una modalità di **rebase** del naming verso il naming target del caso
senza cambiare la logica interna.

### 3.2 Naming member e path

Ogni variabile globale deve avere ownership completa:
- owner DB
- branch/path interno
- leaf name

Regola pratica:
- non basta il leaf: senza DB owner + path, il riferimento non è realmente risolvibile.

---

## 4) Gestione dipendenze (`CALL`, FC runtime) e contesto progetto

Quando il sorgente AWL contiene `CALL` a blocchi esterni (es. FC runtime):
- la traduzione deve preservare l’informazione di dipendenza (è parte della semantica)
- l’analisi non deve inventare logica “missing” se il reference assume il blocco esistente nel progetto

Caso tipico:
- `CALL ... FC32` (sequenziatore): influenza gestione step/transition/runtime e la presenza di DB “SEQ”.

Regola: distinguere chiaramente fra:
- **dipendenza esterna** (esiste nel progetto target, non la rigeneri qui)
- **dipendenza disponibile in input** (solo se fornita nei sorgenti del caso)

---

## 5) Regole logiche AWL -> guard / LAD (subset TIA)

### 5.1 Operatori booleani

- `A/U` -> `AND`
- `AN/UN` -> `AND NOT`
- `O` -> `OR`
- `ON` -> `OR NOT`
- gruppi `A(...)` / `O(...)` vanno mantenuti come sottogruppi (no flatten distruttivo)

### 5.2 Timer AWL

Pattern AWL:
- `L S5T#...` + `SD T xx` + `A T xx`

Regola:
- in AWL, `A Txx` è il “done bit”: **mai** usare l’istanza `IEC_TIMER` (es. `T218`) come contatto booleano in LAD/GRAPH.
- nel target il contatto deve puntare a un booleano equivalente (es. `Txx.Q` oppure un alias stabile tipo `Txx_DONE`).

### 5.3 SET/RESET/ASSIGN

Regola:
- mantenere la semantica AWL materializzando le operazioni (SET/RESET/ASSIGN) nel modello IR e poi in LAD.

---

## 6) Mapping famiglie (cosa finisce in quale FC/DB)

Da input e expected emergono famiglie ricorrenti:
- Alarms
- HMI
- Aux / memories
- Transitions
- Output
- LEV2
- Parameters
- I/O
- Sequencer runtime (`SEQ`)

Regola: l’output deve segmentare e serializzare per famiglia come da reference del caso.

---

## 7) Come usare questa pagina quando aggiungi un nuovo case

1. Metti AWL in `cases/input/inputN/`
2. Metti i reference corretti in `cases/expected_output/expected_outputN/`
3. Scrivi una traccia dedicata in `cases/traces/inputN_expected_outputN.md`
4. Ogni divergenza trovata in diff deve diventare una regola qui (o una precisazione di una regola esistente).
