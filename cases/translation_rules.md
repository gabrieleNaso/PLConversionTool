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
- `OM` -> `OR` (treat as `O`, stesso ruolo booleano)
- `ON` -> `OR NOT`
- gruppi `A(...)` / `O(...)` vanno mantenuti come sottogruppi (no flatten distruttivo)

### 5.1.2 Istruzioni “di scaffolding” LAD (non semantiche)

In alcuni sorgenti AWL (tipicamente ricostruiti da compile LAD) compaiono istruzioni di supporto che **non**
modificano la logica booleana, ma servono a replicare la stessa RLO su più coil:

- `BLD 102`
- `= L 1.0` seguito da ripetizioni di `A L 1.0` + `= <dest>`

Regole:
- `BLD 102` va ignorato in estrazione IR (non è un operando logico).
- Il pattern `= L 1.0` / `A L 1.0` indica “fan-out” della stessa condizione:
  - la condizione vera è quella calcolata **prima** di `= L 1.0`;
  - tutte le assegnazioni `= <dest>` che seguono (precedute da `A L 1.0`) ereditano la **stessa guardia**,
    finché non viene ricalcolata una nuova RLO.

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

Regola (multi-target dallo stesso step):
- se nello stesso segmento dello stesso `Sxx` esistono più blocchi `... JNB ... L <n> T ...Trs` con `n` diversi,
  allora esistono **più transizioni uscenti** dallo stesso `source_step` (AltBegin nel GRAPH),
  ognuna con la propria guardia e il proprio `target_step`.

Regola (pattern `JNB`/`JC`):
- `JNB <lbl>` / `JC <lbl>` in questo contesto sono “salti su condizione falsa” del blocco corrente.
  La guardia della transizione è la condizione **che evita il salto** (cioè il blocco booleano prima del jump valutato TRUE).

Regola (cambio step “globale”, non legato a Sxx):
- In alcuni sequenziatori la scrittura a `Trs` può avvenire in reti che **non** sono sotto una condizione `A "<prefix>".Sxx`.
  In questo caso:
  - non inventare un `source_step` “a caso”;
  - se il segnale rappresenta una modalità/override (manual/emergency/fault/safe), modellalo come transizione da `Init`
    (AltBegin) oppure come transizione da uno step “mode” standard se già presente.

Regola (pattern “sequenziatore” osservato nei casi):
- oltre ai passi “di processo” (`S01`, `S02`, ...), il GRAPH include anche passi standard di progetto come `S28_END`, `S30_Fault`, `S100_TRK CHECK`, `S101_TRK TRANSFER` con transizioni dedicate (tracking/ritorni).

Regola (quando l’expected include XML, per validare l’IR):
- se in `cases/expected_output/...` sono presenti gli XML (es. `05 ... Sequence.xml`), per costruire l’IR manuale le guardie e le negazioni vanno ricostruite **leggendo i contatti del FlgNet** nella transizione (Access + Contact + Negated), non solo dal testo AWL.

### 5.1.3 GRAPH: ingressi multipli e `Direct` vs `Jump`

Negli XML GRAPH (`... Sequence.xml`) ogni transizione collega il proprio target step con un `LinkType`:
- `Direct`: edge “lineare”
- `Jump`: edge “salto” (usato anche per evitare più ingressi `Direct` sullo stesso step)

Regola generale osservata negli expected:
- quando **più transizioni** puntano allo **stesso target step**, solo **una** deve rimanere `Direct`; le altre devono essere `Jump`.

Problema tipico (perché “mancano” o sembrano diverse le diramazioni nel graph):
- se la scelta di quale edge sia `Direct` dipende solo dall’ordine delle transizioni, lo stesso IR può produrre un graph “equivalente” ma con collegamenti visivamente/strutturalmente diversi (es. `Trans33`/`Trans37` su `S18` in `expected_output2`).

Regola implementativa (per stabilizzare e avvicinarsi agli expected di progetto):
- per ogni target step con ingressi multipli, selezionare un “preferred direct incoming”:
  - evitare come `Direct` gli ingressi provenienti da step con `WAIT` nel nome (tipicamente rami laterali/back-edge),
  - altrimenti preferire l’ingresso con distanza numerica minore tra `source_step` e `target_step`.

Questo non cambia la semantica (GRAPH equivalente), ma stabilizza il layout e riduce diff inutili rispetto agli expected.

### 5.2 Timer AWL

Pattern AWL:
- `L S5T#...` + `SD/SF/SE/... T xx` + `A T xx`

Regola:
- in AWL, `A Txx` è il “done bit”: **mai** usare l’istanza `IEC_TIMER` (es. `T218`) come contatto booleano in LAD/GRAPH.
- nel target il contatto deve puntare a un booleano equivalente (es. `Txx.Q` oppure un alias stabile tipo `Txx_DONE`).

### 5.2.1 Fronte di salita (`FP`)

In alcuni casi la logica usa il fronte di salita per generare impulsi (es. `FP <operand>`).

Regole:
- `FP <x>` va trattato come un **operatore**, non come un semplice contatto “equivalente a `A x`”.
- Nell’IR, la guardia deve conservare l’informazione “rising edge”:
  - minimo: includere `<x>` in `guard_operands` e annotare l’edge in `operand_notes`/`support_logic`;
  - preferibile: rappresentare il termine come `RISING_EDGE(<x>)` (o struttura equivalente) nel modello booleano.

### 5.3 SET/RESET/ASSIGN

Regola:
- mantenere la semantica AWL materializzando le operazioni (SET/RESET/ASSIGN) nel modello IR e poi in LAD.

### 5.4 DB esterni di integrazione (OPIN/OPOUT)

Nei casi con integrazione esterna possono comparire DB “contrattuali” (es. `DB81-OPIN`, `DB82-OPOUT`)
con member `Pnnn` / `Lnnn`.

Regole:
- trattare questi riferimenti come `external_refs`/operandi esterni (ownership fissa nel DB esterno).
- preservare **esattamente** naming e zeri significativi (`P071`, `L103`, …): non sanitizzare/normalizzare in modo distruttivo.

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

## 7) Derivare gli output “di progetto” (solo da AWL, usando i casi come regole)

Obiettivo: riuscire a ricavare `Output`/`LEV2` anche quando una rete “uscite” dedicata e' vuota o mancante,
senza usare gli XML expected come sorgente (gli expected restano solo verifica).

### 7.1 Identificare cosa e' “output”

Regola base:
- in AWL le uscite “fisiche” compaiono come azioni su indirizzi `Q...` (e talvolta `A...`).
- nel markdown ricostruito spesso esiste sia il simbolico sia l’indirizzo:
  - simbolico: `"TF2 T5-K53.6"`
  - fisico: `Q172.5`

Regola di naming (derivata dai casi):
1) **Preferire il simbolico tra virgolette** quando presente (`"TF2 T5-K53.6"`), perche' e' stabile e leggibile.
2) Se manca il simbolico, usare un alias derivato dal commento (se affidabile) o dal token fisico (`Q172_5`).
3) L’indirizzo fisico non deve mai diventare “path” strutturale nel DB target, ma puo' restare come evidenza/nota.

### 7.1-bis Cosa include davvero `FC 16 Output` (dai casi)

Nei casi reference, la `FC 16 Output` **non** contiene solo “uscite fisiche”.
Contiene un mix di:
- interlock e condizioni di movimento (es. `... HMI.Conditions.MOV_FW.Conditions.n1`, `... Memory.Interlocks FW`);
- comandi macchina “interni” (bit in `Memory.*` come `FW_ON`, `BW_ON`, `EX_AUTO_FW`, `FW_MANUAL`);
- uscite fisiche (`I/O.DO.*`) che corrispondono a `Q...` (es. `TF2 T5-K53.4/5/6`, `K56.1`, `A24.3`);
- stato sequencer (`Seq Status.*`: `ReadyToAuto`, `AutoON`, `WaitPiece`, `Stopped`).

Regola: quando si parla di “output” nel contesto del tool, si intende **tutto** ciò che viene pilotato in `FC16`
(comandi, interlock e status), non solo le `Q`.

### 7.2 Da quale condizione dipende un output

Per ogni istruzione di azione:
- `= <dest>` (assign)
- `S <dest>` (set)
- `R <dest>` (reset)

la **guardia** dell’output e' la RLO calcolata immediatamente prima dell’azione, includendo:
- gruppi `A(` / `O(` (parentesi logiche),
- negazioni (`AN`, `ON`),
- eventuali pattern “fan-out” (`= L 1.0` + `A L 1.0`), dove la guardia vera resta quella calcolata prima del `= L 1.0`.

Regola pratica (solo AWL):
- costruire una `condition_expression` booleana a partire dalle istruzioni `A/AN/O/ON/...` fino al punto in cui avviene l’azione.
- se la rete contiene riferimenti a `Sxx` (o alias step-bit), questi diventano “step attivo” nel modello (tipicamente `.X` a livello runtime GRAPH).

### 7.3 Output “per step” (dedurre cosa fa ogni step)

I casi mostrano che molti output sono “step-driven”, cioe' validi solo quando un passo e' attivo.

Regola di inferenza:
- se nella guardia compare `S10`/`S14`/`S22` ecc (o i loro alias), allora l’output e' associabile allo step corrispondente.
- quando un output e' comandato in piu' reti/step:
  - il JSON deve contenere **piu righe logiche** (una per rete) oppure una guardia con OR dei casi,
  - ma non bisogna perdere `S/R/=` (la semantica cambia).

### 7.4 Timer usati per abilitare output

Pattern tipici (dai casi):
- `L S5T#...` + `SD/SF/... Txxx` + `A Txxx` usato come condizione prima dell’azione.

Regole:
- `A Txxx` e' “done bit” => nel modello booleano e' un leaf tipo `Txxx_DONE`.
- il timer va modellato come timer (non come bobina):
  - o come membro timer dedicato con preset,
  - o come blocco TON/TOF inline quando chiamata e uso avvengono nella stessa rete.

### 7.5 LEV2: cosa appartiene a LEV2 senza XML

Nei reference `expected_output1/2` la LEV2 ha una **struttura contrattuale** stabile (DB `... LEV2`) con:
- `ITF.*` (Check OK/not OK, Transfer OK/not OK, Production Lock, Skip, Status);
- `MEMORY.*` (es. `CheckRequestMemory`, `Cond move Fwd`, `PP_Man_Mov`, …);
- opzionale handshake `HSK TABLE.*` / `HSK Answer OK` (global tags esterni, non “memory” della sequenza).

Regole (derivazione generica, senza usare gli expected come sorgente):
- se dall’AWL/IR emerge un **tracking micro-flow** (tipicamente step sintetici `S100_TRK_CHECK` / `S101_TRK_TRANSFER`
  oppure pattern equivalente), allora:
  - `LEV2.MEMORY.CheckRequestMemory` deve essere TRUE mentre la sequenza e' in fase di tracking/check
    (minimo: TRUE quando `S100_TRK_CHECK` e' attivo; reset quando si esce dalla fase tracking);
  - `LEV2.ITF.Check OK` deve essere TRUE quando il check ha esito OK (cioe' quando la transizione “OK” da TRK_CHECK avanza);
  - `LEV2.ITF.Check not OK` deve essere TRUE nel caso complementare (transizione di ritorno/loop da TRK_CHECK);
  - `LEV2.ITF.Transfer OK` deve essere TRUE quando il transfer e' completato (minimo: quando `S101_TRK_TRANSFER` e' attivo
    o quando un flag tipo `Pipe Transfered`/`Cond move Fwd` diventa TRUE).
- se nell’AWL compaiono segnali chiaramente LEV2 (`...LEV2...`, `ITF.*`, `HSK*`, `BYPASS LEVEL2`, …), quelle azioni/alias
  vanno in famiglia `LEV2` con ownership nel DB LEV2 (DB `17..` nel profilo).
- se l’AWL **non contiene** indicatori LEV2 e **non** esiste tracking micro-flow, il convertitore non deve inventare logica LEV2.

Conseguenza: se una sequenza ha segmenti output/LEV2 vuoti, l’unico modo corretto per ricostruirli da AWL e'
che la logica sia comunque presente “sparsa” in altre reti (azioni su Q/alias LEV2); altrimenti serve sorgente aggiuntiva.

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
- quando vedi un preset `L S5T#...` seguito da `SD/SF/SE/... T xx`, crea un `TimerCandidate`:
  - `source_timer = "Txx"` / `"Tnn"`
  - `network_index` = network corrente
  - `kind` = opcode timer (`SD`, `SF`, `SE`, ...)
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

Nei casi osservati compaiono spesso alcuni **numeri step ricorrenti** (core del pattern):
- `1` (Init / entry)
- `2` (Check initial condition)
- `3` (Check Piece Presence)
- `7` (StartingCond)
- `28` (END / end_cycle)
- `29` (Manual)
- `30` (Fault)
- `32` (Emergency)
- `100/101` (tracking: TRK CHECK / TRK TRANSFER)

Oltre al core, la sequenza può includere step **machine-specific** (es. `10/12/14/18/22/26/...`) con descrizioni diverse
(`S10_FLIPPER UP` vs `S10_FORWARD`, ecc.).

Regola:
- nell’IR, `step_number` resta il riferimento stabile (1,2,3,7,...) e il `name` può essere:
  - canonico minimo: `S10`, `S14`, ...
  - arricchito: `S10_<descrizione>` se il sorgente (o un mapping) fornisce un descrittivo affidabile.

Regola: se il sorgente contiene elementi tracking/LEV2 o blocchi di interfaccia, crea anche gli step tracking.

### 9.3 Transizioni standard (tipiche)

Pattern più ricorrenti:
- `Init → Safe/Emergency/Manual/Fault` (AltBegin 4)
- tracking split: `TRK CHECK → (OK|not OK)` (AltBegin 2)
- starting conditions split: `StartingCond → (StartMov|Back)` (AltBegin 2)
- back-to-begin: `Manual/Fault/Emergency → Init` con guardie negate (`NOT Manual`, ecc.)

Regola (end-cycle/return loop):
- Quando esiste uno step “fine ciclo” che riporta alla presenza/ingresso ciclo (es. ritorno a `S03`),
  tratta quello step come **end-cycle** e rendilo esplicito nell’IR:
  - se nell’AWL c’è un `Sxx` con `Trs=3` (o “ritorno al passo presenza”), allora `Sxx` è un candidato end-cycle.
  - nell’IR mantieni `step_number` reale del sorgente, ma assegna un `step_roles` coerente (`end_cycle`)
    e rendi esplicita la transizione “end → S03”.

Regola (tracking steps):
- Se il caso mostra segnali di tracking/interfaccia (es. `LEV2`, `ITF`, DB esterni di linea) o un pattern
  di split “tracking ok / tracking not ok”, crea anche gli step di tracking (`S100_TRK CHECK`, `S101_TRK TRANSFER`)
  e le relative transizioni nell’IR, anche se l’AWL applicativo delega parte della logica al runtime esterno.

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
- i segnali **referenziati** come condizioni in un support-FC (es. un `Q...` usato dentro un allarme) devono restare “di proprietà” del loro DB famiglia (tipicamente `IO_DB`) e **non** essere riclassificati come `alarm/hmi/aux` solo perché compaiono nella logica di quel FC

---
