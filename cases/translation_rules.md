# Regole di traduzione (focus: AWL -> IR)

Questo documento raccoglie **regole generali** estratte dai casi in `cases/` (input + expected_output).

Obiettivo:
- avere un riferimento unico e stabile per capire *come* estrarre un IR corretto partendo da AWL
- evitare fix “ad hoc”: ogni divergenza va ricondotta a una regola qui

Ambito (importante):
- Questo file definisce **solo regole AWL -> IR** (parsing/normalizzazione).
- Le convenzioni di target (IR -> XML: naming/numbering/serializer) sono **fuori scope** qui e non devono
  influenzare l’estrazione IR.

---

## 1) Principi (genericità)

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

Nota: i principi sopra descrivono il “contratto” complessivo; qui fissiamo solo cosa significa
estrarre un IR coerente, verificabile e riusabile su casi diversi.

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

### 5.1.1 Derivare transizioni da `Trs` (pattern sequenziatore / FC32)

Nei casi basati su sequenziatore (es. FC32-style) il passo target viene spesso deciso scrivendo `Trs` nel DB sequenza:

```awl
L 18
T "M02".Trs DB102.DBW2
```

Regola per costruire l’IR JSON manuale:
- se dentro un segmento `Sxx` compare `T "...".Trs` con un valore `L <n>`, allora esiste una transizione `Sxx -> Snn`
- la guardia è l’insieme delle condizioni tra la riga `A "...".Sxx` e il relativo `JNB` (includendo `A/AN` e gruppi `A(` / `O(`)
- evitare wildcard: per transizioni tipo “Any -> S29/S32” espandere la sorgente su tutti gli step noti nel case

Regola (pattern “sequenziatore” osservato nei casi):
- oltre ai passi “di processo” (`S01`, `S02`, ...), il GRAPH include anche passi standard di progetto come `S28_END`, `S30_Fault`, `S100_TRK CHECK`, `S101_TRK TRANSFER` con transizioni dedicate (tracking/ritorni).

Regola (quando l’expected include XML, per validare l’IR):
- se in `cases/expected_output/...` sono presenti gli XML (es. `05 ... Sequence.xml`), per costruire l’IR manuale le guardie e le negazioni vanno ricostruite **leggendo i contatti del FlgNet** nella transizione (Access + Contact + Negated), non solo dal testo AWL.

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

---

## 8) Come generare IR JSON “a mano” (senza expected)

Obiettivo: dato **solo** l’AWL (spesso in markdown con `## Segmento ...` + blocchi fenced), produrre un `AwlIR` che il tool possa convertire in XML coerenti con lo standard dei casi.

### 8.1 Struttura minima del payload IR

Campi essenziali (gli altri possono essere vuoti se non ricostruibili):
- `sequence_name`: nome sequenza target (stabile)
- `source_name`: filename sorgente AWL
- `networks[]`: una entry per segmento/network
  - `index`: numero network/segmento (1-based)
  - `title`: titolo leggibile
  - `raw_lines[]`: righe AWL “pulite” (senza linee vuote; commenti ok)
- `steps[]`: catalogo passi (nome + numero)
- `transitions[]`: collegamenti step→step con guardie
- `timers[]`: elenco timer/counter con preset e trigger
- `external_refs[]`: blocchi chiamati (es. `FC32`)
- `step_roles{}`: ruoli semantici (entry/manual/emergency/fault/end_cycle/tracking…)
- `assumptions[]`: tutto ciò che hai “assunto” perché non deducibile in modo certo

Regola: se non riesci a ricostruire una sezione (es. `operand_catalog`), lasciala vuota ma **non inventare** valori.

### 8.2 Network extraction (markdown → `networks`)

Pattern tipico in input:
- heading: `## Segmento N: ...`
- blocco: fenced ` ```awl ... ``` `

Regole:
- ogni `Segmento N` diventa una `AwlNetwork(index=N, title=..., raw_lines=...)`
- `raw_lines` contiene SOLO le righe dentro il fenced block `awl`
- preserva l’ordine delle righe (serve per ricostruire logica come `L ... / SD ... / A Txx`)

### 8.3 Alias/operand extraction (per naming simbolico)

Molte righe hanno forma:

```awl
A "M:T1-A:Auto" M49.0
= "M02".EM DB102.DBX25.5
```

Regole:
- quando trovi `"SOMETHING".Leaf <address>`:
  - salva un alias map `address → Leaf` (es. `DB102.DBX25.5 → EM`)
  - salva anche `address → SOMETHING.Leaf` quando serve distinguere domini diversi
- evita di usare l’indirizzo come leaf name nei path finali (a meno che manchi un alias)

### 8.4 Catalogo step (`steps`)

Regole base:
- il set di step deriva da:
  - bit step nel DB sequenza (es. `"M02".S01 DB102.DBX6.0`, `"M02".S29 DB102.DBX9.4`, ecc.)
  - scritture a `Trs` (target step) e/o tabelle di mapping se presenti
- `step_number` è l’intero del passo (`S01` → 1)
- se il progetto usa naming descrittivo (`S01_Init`, `S03_Check Piece Presence`), il nome step deve rispettare lo standard del dominio:
  - **senza expected**, usa un naming deterministico: `S01`, `S02`, … e aggiungi `assumptions` che i descrittivi non sono disponibili
  - **con standard fisso di progetto**: applica le regole di normalizzazione simbolica (vedi sezione 9.4)

### 8.5 Transizioni (`transitions`)

Regola: una transizione esiste solo se puoi stabilire:
- `source_step`
- `target_step`
- guardia (anche `TRUE` se chiaramente incondizionata)

#### 8.5.1 Pattern `Trs` (FC32)

Vedi sezione 5.1.1: `L <n>; T "...".Trs` implica target step `Snn`.

#### 8.5.2 Pattern branch “Any → Manual/Emergency/Fault”

In molti progetti basati su sequenziatore esiste un “AltBegin” dal passo Init con transizioni tipo:
- Safe
- Manual
- Fault
- Emergency

Regole:
- **non** espandere “Any → Manual/Emergency/Fault” su tutti i passi: queste richieste vanno modellate come **branch dal passo Init** (AltBegin).
- quindi, quando l’AWL ha reti dedicate che forzano `Trs=29` (manuale) o `Trs=32` (emergenza) o condizioni fault/safe, mappa a transizioni **da Init** verso gli step standard (`S29_Manual`, `S32_Emergency`, `S30_Fault`, …).
- le transizioni “back-to-begin” sono transizioni **da** `S29_Manual`/`S30_Fault`/`S32_Emergency` **a** `S01_Init` con guardia negata (`NOT Manual`, ecc.).

### 8.6 Timer (`timers`)

Regole:
- quando vedi un preset `L S5T#...` seguito da `SD T xx` (o `SE "Tnn" Tnn`), crea un `TimerCandidate`:
  - `source_timer = "Txx"` / `"Tnn"`
  - `network_index` = network corrente
  - `kind` = `SD` / `SE`
  - `preset` = stringa `S5T#...`
- `trigger_operands[]`: raccogli gli operandi booleani che abilitano il timer (es. contatti `A/AN/O/ON` prima dell’istruzione timer)

Regola hard (già vista): `A Txx` è contatto done bit, mai istanza timer.

---

## 9) Pattern “sequenziatore / FC32” (estrazione IR senza expected)

Questa sezione raccoglie un pattern ricorrente: la FC applicativa **non** attiva direttamente tutti i bit step,
ma scrive una richiesta di step (`Trs`) che viene materializzata da un runtime esterno (spesso in `FC32` o equivalente).
Le regole qui sono **di estrazione IR** (non naming target) e servono per costruire transizioni coerenti anche senza XML reference.

### 9.1 Riconoscere il DB sequenza e i campi standard

Nei casi osservati la sequenza tipicamente ha:
- `Seq` (DBW0)
- `Trs` (DBW2) = prossimo step richiesto
- `COUNT_STEP` (DBW4) / stato step
- bit step `Sxx` in area DBX (es. `DBX6.0`..)

Regola: riconosci il DB sequenza osservando pattern ripetuti su `DB?.DBW2` e bit `Sxx`.

### 9.2 Step “standard” oltre ai passi di processo

Nel GRAPH compaiono spesso (nome/numero standard):
- `S01_Init` (entry)
- `S29_Manual` (manual)
- `S32_Emergency` (emergency)
- `S30_Fault` (fault)
- `S28_END` (end_cycle)
- `S100_TRK CHECK`, `S101_TRK TRANSFER` (tracking)

Regola: se il sorgente contiene elementi tracking/LEV2 o blocchi di interfaccia, crea anche gli step tracking.

### 9.3 Transizioni standard (tipiche)

Pattern più ricorrenti:
- `Init → Safe/Emergency/Manual/Fault` (AltBegin 4)
- tracking split: `TRK CHECK → (OK|not OK)` (AltBegin 2)
- starting conditions split: `StartingCond → (StartMov|Back)` (AltBegin 2)
- back-to-begin: `Manual/Fault/Emergency → Init` con guardie negate (`NOT Manual`, ecc.)

### 9.4 Normalizzazione simbolica delle guardie (Transitions/Memory/LEV2)

Per evitare di rimanere “attaccati” agli indirizzi (M/I/Q/DBX), usa un mapping deterministico basato su:
- alias dal testo (`"M02".EM`, `"M:T1-A:Auto"`, ecc.)
- convenzioni di progetto:
  - condizioni globali in `Transitions.*`
  - stati/feedback macchina in `Memory.*`
  - interfacce tracking in `LEV2.ITF.*`

Regola: se l’alias è ambiguo o mancante, mantieni l’operando grezzo (es. `DB102.DBX25.5`) ma segnala in `assumptions` che manca la normalizzazione simbolica.

### 9.5 Come ricostruire guardie equivalenti senza XML

Regole:
- preserva grouping `A(` / `O(` generando un albero booleano (non una lista piatta)
- `AN/ON` diventano negazioni sul termine o sul gruppo
- se il segmento costruisce `Trs` con `JNB`:
  - la guardia vera è “condizione che *non* salta” (cioè il blocco tra `A ...` e `JNB` è TRUE)
- se più condizioni diverse portano allo stesso `Trs`, uniscile con `OR` (stesso `source_step` → stesso `target_step`)

---

## 10) Validazioni “senza expected” (autoconsistenza)

Anche senza XML reference, un IR corretto deve soddisfare:
- ogni `transition.source_step/target_step` esiste in `steps`
- almeno uno step ha ruolo `entry` (o `Init=true` nel GRAPH derivato)
- nessuna guardia usa token non rappresentabile (timer istanza come contatto, address raw come member name “sporco”, ecc.)
- i timer hanno `preset` valido e `kind` coerente
- le transizioni di ritorno (manual/fault/emergency) non creano dead-end non voluti

---
