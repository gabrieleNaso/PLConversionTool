# Report aggiornato del 09-04-2026

## Progetto
Conversione di sequenziatori PLC da AWL a GRAPH in TIA Portal V20 tramite XML.

---

## 1. Scopo del documento

Questo documento sostituisce la versione accumulativa del report del 09-04-2026 e ne mantiene solo il contenuto tecnico consolidato.

L'obiettivo di questa versione ripulita è:

- eliminare duplicazioni e sezioni storiche sovrapposte;
- rimuovere stati intermedi ormai superati;
- mantenere una baseline unica, leggibile e riusabile;
- integrare in un unico testo sia la parte di reverse engineering XML sia la parte operativa su TIA Portal Openness.

Il documento va quindi usato come riferimento tecnico corrente del progetto alla data del 09-04-2026.

---

## 2. Obiettivo generale del progetto

L'obiettivo del progetto è definire un metodo affidabile per tradurre sequenziatori complessi sviluppati in AWL in implementazioni equivalenti GRAPH per TIA Portal V20, utilizzando XML come formato intermedio e mantenendo un flusso compatibile con import, validazione ed eventuale automazione tramite TIA Portal Openness.

Le direttrici di lavoro restano due, complementari.

L'obiettivo primario non cambia: convertire sequenziatori `AWL` in `GRAPH`.

La sequenza di implementazione raccomandata, alla data del 09-04-2026, richiede pero' di consolidare prima il backend di generazione XML sul sottoinsieme gia' validato, cosi' da avere una base stabile quando verra' implementata l'analisi AWL.

### 2.1 Traduzione assistita

Uso di ChatGPT per:

- analizzare codice AWL;
- riconoscere stati, transizioni, azioni, interblocchi e timeout;
- proporre il modello GRAPH equivalente;
- supportare la generazione degli XML di destinazione.

### 2.2 Tool deterministico

Sviluppo di un convertitore che esegua:

- parsing del codice AWL;
- estrazione formale della macchina a stati implicita;
- costruzione di un IR esplicito;
- compilazione verso:
  - `SW.Blocks.FB` GRAPH;
  - `SW.Blocks.GlobalDB` companion;
  - eventuali `SW.Blocks.FC` LAD di supporto.

Questa direttrice va oggi separata in due fasi tecniche:

- fase di fondazione: implementazione di IR, validator e serializer XML per `GRAPH`, `GlobalDB` e `FC`;
- fase centrale del convertitore: analisi AWL automatica e popolamento dell'IR.

### 2.3 Automazione con TIA Portal Openness

Il progetto include ora anche il livello operativo di orchestrazione TIA, con obiettivo di automatizzare:

- apertura o connessione a TIA Portal;
- apertura del progetto `.ap20` di test;
- import degli XML generati;
- compile del progetto;
- export dei blocchi per confronto e regressione;
- raccolta strutturata degli errori di import o compile.

---

## 3. Target tecnico consolidato

Il target validato del progetto è:

- `TIA Portal V20`;
- `GRAPH V2`;
- datatype runtime della famiglia `..._V2`;
- XML importabili in stile Openness/TIA;
- blocchi principali:
  - `SW.Blocks.FB` per il GRAPH;
  - `SW.Blocks.GlobalDB` per il DB companion;
  - `SW.Blocks.FC` per logiche LAD di supporto o orchestrazione.

---

## 4. Problema tecnico reale

Il problema non è solo generare XML ben formati.

Occorre trasformare una logica AWL implicita, dispersa in bit di stato, set/reset, latch, salti, timer, consensi e logiche auto/manuale/allarme, in artefatti espliciti e coerenti.

Gli output corretti del progetto sono:

1. un `FB GRAPH` strutturalmente valido e importabile;
2. un `GlobalDB` companion leggibile e manutentivo;
3. quando serve, una o più `FC LAD` importabili e coerenti con i pattern TIA realmente osservati.

---

## 5. Decisione architetturale fondamentale

### 5.1 Due livelli distinti di dati

Nel progetto vanno sempre distinti due livelli.

#### A. Dati runtime interni obbligatori del GRAPH

Sono parte integrante del blocco `FB GRAPH` e servono alla coerenza col runtime Siemens.

Dentro la sezione `Static` del GRAPH devono comparire almeno:

- `RT_DATA : G7_RTDataPlus_V2`;
- un member `G7_TransitionPlus_V2` per ogni transition;
- un member `G7_StepPlus_V2` per ogni step.

#### B. Dati applicativi esterni del sequenziatore

Sono i dati che hanno senso in un `GlobalDB` companion, ad esempio:

- comandi macchina;
- feedback;
- parametri;
- ricette;
- diagnostica;
- mapping AWL -> nuovo modello;
- dati HMI;
- strutture ausiliarie del sequenziatore.

### 5.2 Regola da considerare fissata

La regola corretta è:

> il GRAPH mantiene i suoi statici runtime interni obbligatori e, in aggiunta, il progetto può generare un `GlobalDB` companion separato.

Il DB esterno non sostituisce il runtime interno del GRAPH.

---

# PARTE A - BASELINE CONSOLIDATA DEL BACKEND GRAPH

## 6. Regole hard del GRAPH

Gli elementi che incidono realmente sull'importabilità sono:

- struttura generale del documento XML;
- corretto uso dei namespace;
- `SW.Blocks.FB` con `GraphVersion = 2.0`;
- `Interface` completa e coerente;
- sezione `Temp` quando necessaria;
- sezione `Static` con runtime coerente;
- `Sequence` composta da `Steps`, `Transitions`, `Branches`, `Connections`;
- forma valida del `FlgNet` LAD delle transition;
- topologia del graph conforme ai pattern TIA osservati.

I dati runtime numerici derivati possono essere in parte ricalcolati da TIA, ma la struttura non può essere approssimata nei casi complessi.

## 7. Regole consolidate sulla struttura del blocco GRAPH

### 7.1 Struttura generale

La forma di riferimento è:

- `Document`
  - `Engineering version="V20"`
  - `SW.Blocks.FB`
    - `AttributeList`
    - `Interface`
    - `ObjectList`
    - `SW.Blocks.CompileUnit` con il graph.

### 7.2 Namespace

Regole consolidate:

- root `Document` senza prefissi invasivi tipo `ns0:`;
- namespace `Interface` dichiarato localmente;
- namespace `Graph` dichiarato localmente;
- serializzazione pulita, senza riallocazioni aggressive dei namespace.

### 7.3 Interface del GRAPH

Il blocco deve essere autosufficiente.

L'`Interface` non può essere minimale: deve essere coerente con ciò che le transition leggono e con ciò che il runtime usa.

Sezioni rilevanti:

- `Input`;
- `Output`;
- `InOut`;
- `Temp`;
- `Static`.

### 7.4 Sezione `Static`

Dentro `Static` devono esistere almeno:

- `RT_DATA : G7_RTDataPlus_V2`;
- un member `G7_TransitionPlus_V2` per ogni transition, con `TNO` coerente;
- un member `G7_StepPlus_V2` per ogni step, con `SNO` coerente.

### 7.5 Sezione `Temp`

Nei casi con transition temporizzate, il blocco deve contenere una vera area `Temp` locale con tutti gli `ET_Tx` necessari.

La loro assenza è una causa strutturale di fallimento nei GRAPH non banali.

## 8. Regole topologiche hard del GRAPH

### 8.1 Step

- uno e un solo step iniziale con `Init="true"`;
- gli altri step con `Init="false"`;
- uno step ha una sola uscita diretta verso una transition o un branch.

### 8.2 Transition

- ogni transition ha numero univoco;
- `ProgrammingLanguage = LAD`;
- `FlgNet` valido;
- una sola uscita verso step, branch oppure `EndConnection`.

### 8.3 Branch

Tipi validati:

- `AltBegin`;
- `SimBegin`;
- `SimEnd`.

Uso corretto:

- `AltBegin` per alternative;
- `SimBegin` / `SimEnd` per paralleli.

### 8.4 Connections

Riferimenti osservati:

- `StepRef`;
- `TransitionRef`;
- `BranchRef`;
- `EndConnection`.

`LinkType` validati:

- `Direct`;
- `Jump`.

### 8.5 Regole di topologia da considerare fissate

- uno step non iniziale non deve ricevere due ingressi `Direct`;
- le confluenze multiple vanno gestite correttamente con `Jump` o join espliciti;
- le alternative si modellano con `AltBegin`;
- i paralleli si modellano con `SimBegin` e `SimEnd`;
- i rami di allarme devono chiudersi correttamente.

## 9. Transition LAD: sottoinsieme sicuro

La parte più fragile del progetto si è dimostrata la generazione del LAD nelle transition.

Il sottoinsieme oggi considerato sicuro è basato su:

- `Access`;
- `Contact`;
- `Contact` negato;
- nodo `O` per le OR;
- comparatori già validati;
- `TrCoil` finale.

Regole operative:

- `AND` = serie;
- `OR` = nodo `O`;
- `NOT` = contatto negato;
- una sola `TrCoil` finale;
- evitare composizioni non osservate nei tipici TIA reali.

## 10. Regole progettuali ormai consolidate per il backend GRAPH

Il compilatore GRAPH deve essere:

- model-based;
- grammar-driven;
- constraint-driven;
- deterministico.

Non deve essere costruito copiando e rattoppando template XML esistenti.

Pipeline concettuale:

`AWL -> parser -> estrazione macchina a stati -> IR -> normalizzazione -> validator GRAPH -> compilatore transition -> serializer XML -> validator finale`

## 11. Sintesi consolidata sul GRAPH

La baseline corrente del backend GRAPH è:

1. `GRAPH V2` è il target corretto;
2. il blocco deve essere un `FB` autosufficiente;
3. il companion DB è utile ma non sostituisce la completezza del GRAPH;
4. le transition temporizzate richiedono `Temp` locale reale con `ET_Tx`;
5. gli operandi usati nel LAD devono essere risolvibili esplicitamente;
6. parallelismi, join e rami allarme richiedono topologia concreta e non solo equivalenza logica astratta.

---

# PARTE B - BASELINE CONSOLIDATA DEL BACKEND GLOBALDB

## 12. Ruolo del `GlobalDB` companion

Il `GlobalDB` companion serve a ospitare dati applicativi del sequenziatore e dati utili a integrazione, diagnostica e manutenzione.

Ruoli tipici:

- HMI;
- diagnostica;
- mapping AWL -> GRAPH;
- parametri macchina;
- ricette;
- segnali applicativi referenziati dalle transition;
- supporto agli artefatti FC.

## 13. Regole hard del `GlobalDB`

La forma consolidata del DB è:

- `Document` senza `ns0:`;
- `Engineering version="V20"`;
- `SW.Blocks.GlobalDB`;
- `ProgrammingLanguage = DB`;
- `Interface` con `Sections` e namespace locale corretto;
- `Section Name="Static"`;
- `ObjectList` standard con `Comment` e `Title` del blocco.

## 14. Serializer DB: regole consolidate

Il serializer DB deve essere tree-based e ricorsivo.

Classi minime di `Member` da supportare:

- scalari semplici;
- member con `AttributeList`;
- array;
- member con `Remanence`;
- `Struct` ricorsive;
- tipi speciali versionati come:
  - `IEC_TIMER Version="1.0"`;
  - `IEC_COUNTER Version="1.0"`.

Ogni `Member` deve poter essere modellato almeno con:

- `name`;
- `datatype`;
- `version?`;
- `remanence?`;
- `attributes?`;
- `comment?`;
- `start_value?`;
- `children?`.

## 15. Commenti e visibilità in TIA

È consolidato che i commenti visibili in TIA richiedono una forma semplice e coerente basata su:

- `Comment`;
- `MultiLanguageText`.

La generazione dei commenti va trattata come parte della grammatica del DB, non come rifinitura opzionale.

## 16. Regole su `StartValue`

Le `StartValue` vanno gestite in modo coerente col tipo del member.

Particolare attenzione è necessaria su:

- `Bool`;
- `Int`;
- `Real`;
- `Struct`;
- tipi IEC.

## 17. Modello canonico consigliato del companion DB

Il DB non deve replicare il runtime interno del GRAPH.

La struttura consigliata è funzionale e impiantistica, ad esempio con `Struct` come:

- `Cmd`;
- `Fb`;
- `Par`;
- `Diag`;
- `Manual`;
- `Auto`;
- `Recipe`;
- `StepData`;
- `TransitionData`;
- `AwlMapping`.

## 18. Regole progettuali consolidate sul backend DB

Il compiler `GlobalDB` deve:

- lavorare su un IR esplicito;
- serializzare ricorsivamente i member;
- validare namespace, struttura e tipi;
- produrre un DB leggibile e manutentivo;
- supportare dati IEC quando servono al modello FC o al modello impianto.

## 19. Sintesi consolidata sul `GlobalDB`

La baseline corrente del backend DB è:

1. serializer ricorsivo tree-based;
2. namespace locale corretto su `Sections`;
3. commenti visibili in TIA con forma semplice e stabile;
4. supporto a `IEC_TIMER` e `IEC_COUNTER` con `Version="1.0"`;
5. ruolo del DB come companion dati, non come sostituto del runtime GRAPH.

---

# PARTE C - BASELINE CONSOLIDATA DEL BACKEND FC LAD

## 20. Ruolo del backend FC

Il backend FC serve a generare reti LAD importabili per logiche di supporto, orchestrazione o servizio.

La generazione FC va trattata con la stessa disciplina del backend GRAPH: non come emissione libera di XML, ma come compilazione guidata da pattern osservati.

## 21. Corpus FC consolidato

Il corpus minimo consolidato è articolato su quattro livelli:

1. `fc_1.xml` come grammatica generale del blocco FC;
2. `fc_2.xml` come grammatica dei box IEC standard;
3. `fc_3.xml` come corpus di pattern LAD elementari;
4. micro-test e casi composti usati per validare progressivamente pattern e combinazioni.

## 22. Regole strutturali del blocco FC

La forma consolidata del backend FC è:

- `Document`;
- `Engineering version="V20"`;
- `SW.Blocks.FC`;
- `ProgrammingLanguage = LAD` coerente a livello blocco e rete;
- `CompileUnit` ordinate;
- `FlgNet` con `Parts` e `Wires` coerenti;
- `UId` consistenti;
- tutte le connessioni risolte;
- nessun nodo orfano o pin inesistente.

## 23. Nodi e pattern minimi da supportare

Il compilatore FC deve saper emettere e validare almeno:

- `Access`;
- `Part`;
- `Wires`;
- `CallInfo`;
- `Contact`;
- `Coil`;
- `SCoil`;
- `RCoil`;
- nodo `O`;
- box IEC `TON`, `TOF`, `CTU`.

## 24. Regole consolidate sui box IEC

Per timer e contatori, il backend deve aderire al dialetto TIA/IEC osservato.

Pin reali da considerare:

- timer: `IN`, `PT`, `Q`, `ET`;
- contatore: `CU`, `R`, `PV`, `Q`, `CV`.

Le istanze IEC possono stare in DB companion quando necessario.

## 25. Regole consolidate sulle variabili globali

È consolidato che le `GlobalVariable` non sono un problema di import in sé.

La regola corretta è:

> usare simboli esplicitamente risolvibili; locali o globali è una scelta architetturale, non un vincolo rigido di importabilità XML.

Va anche distinto:

- importabilità XML del blocco;
- coerenza simbolica o semantica post-import.

Sono concetti diversi.

## 26. Regola metodologica chiave del backend FC

La validazione del backend FC deve essere incrementale.

Strategia corretta:

1. validare il contenitore FC minimale;
2. validare i box IEC;
3. validare latch base `S/R`;
4. validare reset multipli;
5. validare OR verso bobina;
6. validare combinazioni miste;
7. comporre solo pattern già confermati.

Non è più corretto generare una FC completa e correggere a posteriori senza una libreria di pattern convalidati.

## 27. Stato consolidato del backend FC

Lo stato da considerare fissato è il seguente:

1. `fc_1.xml` consolida la grammatica generale del backend FC;
2. `fc_2.xml` consolida la grammatica dei box IEC;
3. `fc_3.xml` consolida i pattern LAD minimi rilevanti;
4. micro-test e casi progressivi hanno validato la composizione conservativa dei pattern;
5. il backend FC ha raggiunto una validazione pratica forte;
6. le FC complete vanno comunque generate solo passando da pattern selezionati e validati.

## 28. Architettura corretta del compiler FC

Il backend FC va articolato almeno in:

1. `fc_ir_builder`;
2. `fc_pattern_validator`;
3. `fc_xml_serializer`;
4. `fc_semantic_linter`.

Il linter deve intercettare almeno:

- scritture miste incoerenti dello stesso bit;
- doppie bobine normali sospette;
- call IEC incomplete;
- timer non cablati correttamente;
- reset multipli non coerenti;
- pattern combinatori fuori sottoinsieme validato.

## 29. Sintesi consolidata sul backend FC

La baseline corrente del backend FC è:

- grammatica XML consolidata;
- uso conservativo dei box IEC;
- supporto a pattern LAD elementari validati;
- supporto a variabili locali e globali;
- necessità di pattern library, validator e linter semantico;
- esclusione della strategia “XML LAD libero”.

---

# PARTE D - ARCHITETTURA COMPLESSIVA CONSOLIDATA DEL TOOL

## 30. Architettura a tre backend

L'architettura del progetto resta a tre compilatori complementari:

1. `GRAPH FB compiler`;
2. `GlobalDB compiler`;
3. `FC LAD compiler`.

Pipeline concettuale consolidata:

`AWL -> parser -> estrazione pattern e macchina a stati -> IR sequenza + IR dati + IR reti -> validator -> GRAPH compiler + GlobalDB compiler + FC compiler -> test import TIA`

Pipeline di implementazione consigliata nell'immediato:

`IR di test/manuale -> validator -> GRAPH compiler + GlobalDB compiler + FC compiler -> import TIA -> regressione`

## 31. Principi da considerare fissati

Il tool deve essere:

- universale sul piano del metodo;
- conservativo sul piano dei pattern emessi;
- deterministico;
- fondato su IR espliciti;
- protetto da validator strutturali;
- protetto da linter semantici;
- verificato con suite di regressione su casi reali e golden sample.

## 32. Output attesi del convertitore

Per ciascun sequenziatore AWL, gli output corretti restano:

- specifica di conversione leggibile;
- `FB GRAPH` importabile;
- `GlobalDB` companion importabile;
- eventuali `FC` di supporto, solo se richieste dal modello o dal workflow;
- report di validazione e differenze rispetto alla baseline.

---

# PARTE E - STATO OPERATIVO CONSOLIDATO DI TIA PORTAL OPENNESS

## 33. Salto di livello del progetto

Il progetto non è più solo nella fase di reverse engineering XML.

È ora validata anche la pipeline operativa reale di collegamento tra ambiente Linux, bridge applicativo, VM Windows e TIA Portal Openness.

## 34. Catena tecnica verificata

La catena verificata è:

`Linux -> tia-bridge -> VM Windows -> TIA Portal Openness`

Sono stati verificati con esito positivo:

- avvio dell'agent Windows;
- raggiungibilità di rete dalla VM Linux;
- apertura reale di TIA Portal;
- apertura del progetto `.ap20`;
- accesso al `PlcSoftware`;
- invocazione reale di `PlcBlockComposition.Import(...)`;
- import reale di blocchi XML in TIA;
- compile reale del progetto;
- export reale dei blocchi verso XML;
- staging automatico degli XML dalla VM Ubuntu alla VM Windows;
- sincronizzazione automatica dei file esportati da Windows verso Ubuntu;
- raccolta e reporting degli errori Openness nei job.

## 35. Ruolo del `tia-bridge`

Il container `tia-bridge` non esegue TIA Portal in Linux.

È il boundary service che orchestra il dialogo con l'agent Windows che gira accanto a TIA Portal.

Pattern corretto:

- `backend/frontend` nel compose Linux;
- `tia-bridge` come adapter di orchestrazione;
- agent Windows come adapter locale verso le API Openness;
- TIA Portal eseguito solo sul target Windows.

## 36. Capacità operative oggi validate

L'agent Windows oggi copre almeno:

- health e diagnostica;
- job di `import`;
- job di `compile`;
- job di `export`;
- staging file per import remoto;
- sincronizzazione dei risultati export;
- gestione seriale dei job;
- apertura TIA e progetto;
- gestione esplicita di eccezioni note del layer Siemens.

## 37. Implicazione tecnica ormai fissata

La parte più rischiosa del layer TIA è stata superata.

I prossimi step non sono più “far parlare il sistema con TIA”, ma:

1. consolidare test su più famiglie di blocchi XML;
2. stabilizzare la gestione di dipendenze progetto, blocchi e tipi;
3. collegare il convertitore AWL -> GRAPH alla pipeline TIA già validata.

---

# PARTE F - BASELINE FINALE DEL PROGETTO AL 09-04-2026

## 38. Baseline consolidata

Alla data del 09-04-2026 la baseline consolidata del progetto è la seguente.

### 38.1 Sul GRAPH

- target `GRAPH V2` confermato;
- regole XML del backend GRAPH consolidate su struttura, topologia e runtime;
- blocco `FB` da generare come elemento autosufficiente;
- supporto a operandi locali o referenziati simbolicamente nel companion DB;
- forte distinzione fra topologia GRAPH e logica OR nel LAD delle transition.

### 38.2 Sul `GlobalDB`

- forma XML consolidata;
- serializer atteso di tipo ricorsivo tree-based;
- commenti visibili in TIA;
- supporto a member strutturati, array e tipi IEC;
- ruolo del DB chiarito come companion applicativo.

### 38.3 Sul backend FC

- grammatica FC consolidata;
- box IEC consolidati in forma conservativa;
- pattern LAD elementari validati;
- supporto a variabili locali e globali;
- necessità ormai fissata di validator e linter semantico.

### 38.4 Sul metodo generale

- IR espliciti;
- validator strutturali;
- linter semantici;
- selezione dei pattern validati;
- serializer dedicati per backend;
- regressione su casi importati davvero in TIA.

### 38.5 Sul layer TIA

- bridge Linux/Windows operativo;
- import/compile/export reali verificati;
- pipeline end-to-end pronta per validare il backend XML mentre viene costruito il convertitore AWL.

---

## 39. Prossimi passi consigliati

I prossimi passi più utili sono:

1. formalizzare un IR unico di progetto per sequenza, dati e reti, anche inizialmente popolato a mano o da fixture;
2. implementare i serializer XML di `GRAPH`, `GlobalDB` e `FC` sul sottoinsieme gia' consolidato;
3. costruire validator e linter come parte obbligatoria della pipeline;
4. costruire una libreria di pattern GRAPH e FC esplicitamente convalidati;
5. avviare poi il parser e l'analisi AWL come cuore del convertitore;
6. estendere i test reali su più tipologie di blocchi XML e collegare la generazione `AWL -> XML` alla pipeline TIA già funzionante.

---

## 40. Uso consigliato di questo report

Questo documento va usato come:

1. baseline tecnica consolidata del progetto `04-225`;
2. riferimento per lo sviluppo del convertitore deterministico;
3. checklist per evitare regressioni su GRAPH, DB, FC e pipeline TIA;
4. documento di allineamento prima di introdurre nuovi generatori o nuovi pattern;
5. base per i report successivi.

---

## 41. Regola operativa finale

Da questo punto in avanti va considerata fissata una regola pratica:

> prima di generare nuovi artefatti XML o modificare il tool, rileggere la baseline consolidata del progetto e verificare che il caso da emettere rientri nel sottoinsieme di pattern già validati oppure introduca una nuova regola in modo controllato.

Questa non è una regola organizzativa, ma un vincolo tecnico del progetto.

---

## 42. Sintesi finale

Alla data del 09-04-2026 il progetto ha raggiunto una baseline forte su quattro livelli:

1. reverse engineering strutturale del `GRAPH`;
2. regole di generazione consolidate del `GlobalDB` companion;
3. backend `FC` guidato da pattern e non da emissione libera;
4. pipeline reale `Linux -> bridge -> Windows -> TIA Portal Openness` verificata end-to-end.

Il problema centrale del progetto non è più capire se il workflow sia praticabile, ma implementare in modo sistematico, deterministico e regressivamente sicuro i generatori XML; la conversione automatica `AWL -> GRAPH XML (+ DB/FC)` resta la fase successiva.
