# Report aggiornato del 22-04-2026

## Progetto
Conversione di sequenziatori PLC da AWL a GRAPH in TIA Portal V20 tramite XML.

---

## 1. Scopo del documento

Questo documento sostituisce la versione accumulativa del report del 10-04-2026 e ne mantiene solo il contenuto tecnico consolidato.

L'obiettivo di questa versione consolidata è:

- eliminare duplicazioni e sezioni storiche sovrapposte;
- rimuovere stati intermedi ormai superati;
- mantenere una baseline unica, leggibile e riusabile;
- integrare in un unico testo sia la parte di reverse engineering XML sia la parte operativa su TIA Portal Openness.

Il documento va quindi usato come riferimento tecnico corrente del progetto alla data del 22-04-2026.

---

## 2. Obiettivo generale del progetto

L'obiettivo del progetto è definire un metodo affidabile per tradurre sequenziatori complessi sviluppati in AWL in implementazioni equivalenti GRAPH per TIA Portal V20, utilizzando XML come formato intermedio e mantenendo un flusso compatibile con import, validazione ed eventuale automazione tramite TIA Portal Openness.

Le direttrici di lavoro restano due, complementari.

### 2.1 Traduzione assistita

Uso di ChatGPT per:

- analizzare codice AWL;
- riconoscere stati, transizioni, azioni, interblocchi e timeout;
- proporre il modello GRAPH equivalente;
- supportare la generazione degli XML di destinazione.

### 2.2 Tool deterministico

Sviluppo di un convertitore che esegua:

- parsing del codice AWL oppure lettura di una sorgente Excel strutturata;
- estrazione formale della macchina a stati implicita oppure acquisizione strutturata del modello sequenziale;
- costruzione di un IR esplicito comune;
- compilazione verso:
  - `1 x SW.Blocks.FB` GRAPH per la sequenza;
  - `N x SW.Blocks.GlobalDB` applicativi e di supporto quando richiesti dal caso reale;
  - `M x SW.Blocks.FC` LAD di supporto.

### 2.2-bis Ingresso alternativo da Excel

L'IR del progetto non va più considerato legato esclusivamente al parser AWL.

È ora da considerare ammessa anche una seconda sorgente controllata:

- Excel strutturato per passi, transizioni, operandi e mapping dati;
- catalogo `operands` come sorgente vincolante per il popolamento strict dei `GlobalDB`;
- pagina FC unica `support_fc` come sorgente strutturata per member e logica LAD delle FC di supporto;
- convergenza obbligatoria sullo stesso IR usato dal flusso AWL.

Conseguenza architetturale da considerare fissata:

`AWL parser` oppure `Excel strutturato` -> `IR comune` -> `builder GRAPH / GlobalDB / FC` -> `serializer XML`.

Regola operativa consolidata al 22-04-2026 per il flusso Excel:

- `operands` e `support_fc` sono fogli obbligatori;
- nel foglio `support_fc` devono convivere sia la definizione member (`member_name`) sia la logica FC (`result_member`, `condition_expression`, `condition_operands`, `network`);
- non e' piu' previsto un secondo foglio dedicato separato per la logica FC nel formato corrente.

### 2.3 Automazione con TIA Portal Openness

Il progetto include ora anche il livello operativo di orchestrazione TIA, con obiettivo di automatizzare:

- apertura o connessione a TIA Portal;
- apertura del progetto `.ap20` di test;
- import degli XML generati;
- compile del progetto;
- export dei blocchi per confronto e regressione;
- raccolta strutturata degli errori di import o compile.

---


## 2-bis. Chiarimenti documentali e operativi consolidati al 22-04-2026

A valle del confronto tra i documenti operativi, i report consolidati e i tipici XML del caso `T1-A ARUNC`, i seguenti punti sono da considerare fissati.

- La documentazione del progetto e' ora distinta in due livelli: **documenti normativi** (`report` + `specifica master`) e **documenti operativi derivati** (`flow`, `operations`, `tia-integration`, `workflow-checklists`, `conventions`, template).
- In caso di conflitto tra una convenzione generica e una regola hard di traduzione o serializer, prevale sempre la specifica master del convertitore.
- La regola corretta di cardinalita' resta: `1 sequenza AWL -> 1 x FB GRAPH + N x GlobalDB + M x FC LAD`.
- Il naming globale non puo' essere ridotto a un semplice suffisso finale: owner DB, branch path e leaf name costituiscono un contratto bloccante tra IR, serializer e bundle XML.
- L'IR comune del progetto puo' ora essere alimentato sia da parsing AWL sia da Excel strutturato, pur restando invariati i contratti semantici richiesti dai backend.
- I tipici legacy importabili ma basati su runtime `V6` restano utili per reverse engineering semantico e topologico, ma non sono pattern validi per il serializer finale `V20 / GRAPH V2`.
- La segmentazione reale dell'AWL deve tenere conto delle famiglie funzionali ricorrenti osservate nel caso `FC102 / AWL Romania`: allarmi, memorie/ausiliari, sequenza, manuale/automatico, emergenza/fault, uscite.

## 2-ter. Integrazioni consolidate dal confronto puntuale con i tipici XML del corpus

Il confronto tra i documenti normativi aggiornati e i file XML reali oggi disponibili nel corpus (`T1-A ARUNC`, `DB81-OPIN`, `DB82-OPOUT`, `LEV2`, `HMI`, `I-O`, `AUX`, `PARAMETERS`) ha permesso di fissare con maggiore precisione i seguenti punti.

- I tipici reali confermano in modo forte la cardinalita' architetturale del pacchetto target: `1 x FB GRAPH + N x GlobalDB + M x FC LAD`. Questo e' da considerare requisito strutturale del generatore e non convenzione descrittiva.
- Il pacchetto `T1-A ARUNC` resta un riferimento molto utile per naming, topologia dei path globali, separazione per responsabilita' e pattern LAD di supporto, ma non puo' essere assunto come template serializer finale, perche' il suo blocco sequenziale osservato e' ancora su runtime `V6`.
- La numerazione blocchi del convertitore va considerata normativa in formato `XXGG`: `XX` identifica la famiglia, `GG` il gruppo comune della traduzione (`03` e' solo esempio, non valore fisso).
- Il modello HMI va esplicitato su due livelli: condizioni elementari nel path `Conditions.<gruppo>.Conditions.nX` e metadati/stati di gruppo nello stesso owner DB HMI, con campi del tipo `PopUpNumber`, `ConditionOK`, `Visible`, `FO` o equivalenti previsti dal modello finale.
- I DB esterni fissi di integrazione, quando presenti, costituiscono un contratto rigido di naming. In particolare i pattern `Pnnn` e `Lnnn` osservati in `DB81-OPIN` e `DB82-OPOUT` non devono essere rinominati liberamente dal generatore.
- I casi legacy come `T1-A ARUNC LEV2` confermano che nel corpus storico esistono sequenze e strutture dati utili per il reverse engineering semantico, ma non necessariamente allineate alla partizione target chiusa del nuovo convertitore.
- Mappa famiglie consolidata al 22-04-2026 (forma `XXGG`): `11GG` alarms/diag, `12GG` hmi (`12GG` = DB HMI), `13GG` aux, `14GG` transitions, `15GG` graph, `16GG` sequenza, `18GG` external, `19GG` output.
- `DB15GG SEQ` va considerato DB istanza del GRAPH generato da TIA: non deve essere emesso dal convertitore come DB custom.
- Profilo operativo corretto: `FC11/12/13/14/16/17`, `FB15`, DB custom `11/12/13/16/17/18/19` + `DB15` solo istanza TIA.
- Nel flusso Excel l'ownership DB e' determinata da `operands`: uso cross-FC ammesso ma senza migrazione del DB owner della variabile.

## 3. Target tecnico consolidato

Il target validato del progetto è:

- `TIA Portal V20`;
- `GRAPH V2`;
- datatype runtime della famiglia `..._V2`;
- XML importabili in stile Openness/TIA;
- blocchi principali:
  - `SW.Blocks.FB` per il GRAPH;
  - `SW.Blocks.GlobalDB` per i DB applicativi e di supporto della sequenza;
  - `SW.Blocks.FC` per logiche LAD di supporto o orchestrazione.

### 3.1 Chiusura definitiva del target runtime

Da questo punto in avanti il target del progetto va considerato chiuso in modo definitivo su `TIA Portal V20` e `GRAPH V2`.

Conseguenze operative:

- tutti i nuovi generatori devono emettere solo XML coerenti con `GraphVersion = 2.0`;
- i datatype runtime da generare devono appartenere esclusivamente alla famiglia `..._V2`;
- eventuali XML campione di versioni diverse, inclusi casi legacy in `V6`, vanno usati solo come riferimento semantico, topologico e architetturale;
- gli esempi legacy non devono pilotare il serializer finale se entrano in conflitto con il target `V2`.

La presenza nel corpus di esempi importabili ma basati su runtime diversi non modifica quindi il target del convertitore: il convertitore deve produrre `V2`, non replicare dialetti storici differenti.

---

## 4. Problema tecnico reale

Il problema non è solo generare XML ben formati.

Occorre trasformare una logica AWL implicita, dispersa in bit di stato, set/reset, latch, salti, timer, consensi e logiche auto/manuale/allarme, in artefatti espliciti e coerenti.

Gli output corretti del progetto sono:

1. un solo `FB GRAPH` strutturalmente valido e importabile per ciascuna sequenza AWL;
2. uno o più `GlobalDB` leggibili e manutentivi, ciascuno con responsabilità coerente;
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

Sono i dati che hanno senso in uno o più `GlobalDB` applicativi e di supporto, ad esempio:

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

> il GRAPH mantiene i suoi statici runtime interni obbligatori e, in aggiunta, il progetto genera i blocchi dati e le FC di supporto necessari al caso reale.

Il DB esterno non sostituisce il runtime interno del GRAPH.

### 5.3 Chiarimento sulla cardinalità dei blocchi target

Questo punto va letto come chiarimento architetturale del progetto.

Nel materiale del progetto la formula abbreviata `GRAPH + GlobalDB + FC` serve solo a nominare le famiglie di backend coinvolte nella traduzione. Non descrive una cardinalità fissa del tipo `1 + 1 + 1`.

Il modello corretto, osservato sia nell'analisi AWL sia negli XML di riferimento, è il seguente: una sequenza AWL corrisponde a un solo GRAPH che rappresenta l'intera macchina a stati della sequenza, mentre i dati applicativi e le logiche di supporto vengono distribuiti su più DB e su più FC, separati per responsabilità.

In pratica, il GRAPH resta l'artefatto unico che formalizza la topologia sequenziale; i DB possono articolarsi in contenitori distinti come base, sequenza, HMI, AUX, I-O, parameters, EXT o altri DB coerenti col tipico; allo stesso modo le FC possono articolarsi in famiglie diverse come HMI, Aux, Transitions, Output, handshake, manuale o altri servizi additivi.

L'esempio reale del pacchetto XML `T1-A ARUNC` rende il punto molto chiaro: si osserva un solo blocco sequenziale `05 T1-A ARUNC Sequence`, ma più FC di supporto (`02 T1-A ARUNC HMI`, `03 T1-A ARUNC Aux`, `04 T1-A ARUNC Transitions`, `06 T1-A ARUNC Output`, `07 T1-A ARUNC LEV2`) e più DB (`T1-A ARUNC`, `T1-A ARUNC HMI`, `T1-A ARUNC I-O`, `T1-A ARUNC AUX`, `T1-A ARUNC PARAMETERS`, `T1-A ARUNC LEV2`, oltre ai DB esterni `DB81-OPIN` e `DB82-OPOUT`).
La numerazione `02/03/04/06/07` resta una evidenza del campione storico; nel convertitore corrente la naming FC e' allineata ai DB (`FC12/FC13/FC14/FC19` + eventuali FC di servizio).

La conseguenza architetturale è che l'IR deve descrivere una sola topologia GRAPH per sequenza AWL, mentre i backend DB e FC devono restare variabili nella cardinalità e aderire alla partizione reale del caso tradotto.

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
- per gli import, `targetPath` parte sempre da `Program blocks/`; per sottocartelle usare `Program blocks/generati da tool/<nome>`.
- la numerazione step in GRAPH deve seguire il `step_number` dell'IR; il nome step e' una label logica.

### 8.6 Stato di stabilita' generatore

- Generatore considerato affidabile per import/export su bundle complessi (es. `mega-trial-ultra-v1`).
- Blocchi FB/DB/FC apribili in TIA senza crash nelle prove correnti.

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
3. i DB applicativi e di supporto sono utili ma non sostituiscono la completezza del GRAPH;
4. le transition temporizzate richiedono `Temp` locale reale con `ET_Tx`;
5. gli operandi usati nel LAD devono essere risolvibili esplicitamente;
6. parallelismi, join e rami allarme richiedono topologia concreta e non solo equivalenza logica astratta.

---

# PARTE B - BASELINE CONSOLIDATA DEL BACKEND GLOBALDB

## 12. Ruolo dei `GlobalDB` applicativi e di supporto

Nel target reale della traduzione i dati del sequenziatore non confluiscono necessariamente in un solo DB. La famiglia `GlobalDB` serve a ospitare dati applicativi, strutture di integrazione, diagnostica e manutenzione distribuite nei contenitori necessari al caso reale.

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

## 17. Modello canonico consigliato dei DB applicativi

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
5. ruolo dei DB come contenitori dati applicativi e ausiliari, non come sostituti del runtime GRAPH.

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

Le istanze IEC possono stare nei DB applicativi o ausiliari del pacchetto quando necessario.

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

`AWL / Excel -> normalizzazione sorgente -> IR sequenza + IR dati + IR reti -> validator -> GRAPH compiler + GlobalDB compiler + FC compiler -> test import TIA`

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
- uno o più `GlobalDB` importabili, ciascuno con ruolo coerente;
- una o più `FC` di supporto, quando richieste dal modello o dal workflow;
- report di validazione e differenze rispetto alla baseline.

### 32.1 Convenzioni fissate di numbering e partizionamento dei blocchi

Per la traduzione AWL -> GRAPH il progetto adotta ora una convenzione fissa di numbering dei blocchi.

Regola generale:

- il numero blocco reale e' il valore XML `<Number>`;
- il formato e' `XXGG`, dove `XX` identifica la famiglia e `GG` e' il gruppo comune della traduzione;
- `03` e' un esempio operativo di `GG`, non un valore fisso.

Mappa famiglie consolidata: `11GG` alarms/diag, `12GG` hmi (`12GG` = DB HMI), `13GG` aux, `14GG` transitions, `15GG` graph, `16GG` sequenza, `18GG` external, `19GG` output.

Nota: `DB15GG SEQ` e' l'istanza FB GRAPH generata da TIA; il convertitore non deve serializzarla come DB applicativo.

Questa convenzione è normativa per il convertitore, anche se alcuni campioni legacy caricati mostrano distribuzioni storiche diverse dei numeri blocco.

### 32.2 Convenzioni fissate sui DB di progetto

Nella baseline corrente la partizione dei DB di una sequenza tradotta va considerata fissa.

- `11..` = DB alarms/diag;
- `12..` = DB HMI;
- `13..` = DB ausiliare (timer, contatori, appoggi tecnici);
- `14..` = DB transitions;
- `16..` = DB sequenza;
- `18..` = DB `EXT`;
- `19..` = DB output.

Questa distribuzione deve essere rispettata dal modello IR e dai serializer, evitando accorpamenti opportunistici fra aree con ruolo diverso.

### 32.3 Blocchi fissi esterni alla sequenza

Per ogni traduzione AWL vanno considerati presenti e stabili i seguenti DB esterni, trattati come elementi `1:1` nel progetto:

- `DB81`;
- `DB82`;
- `DB2020`;
- `DB2025`.

Questi blocchi non sono da reinventare caso per caso, ma da trattare come riferimenti fissi del modello di conversione quando la sequenza AWL li usa o li presuppone.

### 32.4 Regola di ingresso e ossatura del GRAPH

La topologia iniziale del GRAPH non deve dipendere dal nome testuale del passo.

Regola operativa:

- lo step iniziale e' quello con `step_number=1`;
- il nome passo e' libero (`Init`, `StartCycle`, `S1`, ...);
- eventuali ruoli strutturali (manuale/fault/emergenza) possono essere modellati con numeri convenzionali o naming di progetto, ma non devono essere imposti con rinomina forzata.

Questa scelta riduce regressioni di import, mantiene coerenza con l'Excel manuale e rende il builder piu' deterministico.


### 32.5 Regola architetturale sul formato reale della traduzione

La traduzione di una FC AWL di sequenza non va interpretata come generazione del solo GRAPH.

La forma corretta dell'output è un insieme coordinato di artefatti:

- `FB GRAPH` per la macchina a stati esplicita;
- `DB 11..` per memorie, transizioni semantiche e stato leggibile del sequenziatore;
- `DB 12..` per dati HMI, popup, condizioni visualizzate e strutture HMI (`12GG` = DB HMI);
- `DB 13..` per supporti ausiliari (timer, contatori, appoggi tecnici);
- `DB 14..` per transitions;
- `DB 16..` per il contenitore della sequenza secondo il modello scelto;
- `DB 18..` per variabili esterne alla sequenza;
- `DB 19..` per output;
- `FC 12` HMI;
- `FC 13` Aux;
- `FC 14` Transitions;
- `FC 19` Output;
- eventuale FC di servizio coerente alla famiglia numerica prevista (es. `FC16..` o equivalente).

Il convertitore deve quindi ragionare in termini di ecosistema di blocchi e non in termini di singolo artefatto XML isolato.

### 32.6 Regola di scomposizione della FC AWL in famiglie logiche

L'AWL di sequenza va prima segmentato per famiglie logiche e solo dopo tradotto.

Le famiglie principali da riconoscere sono:

1. allarmi e timeout di dispositivo;
2. memorie generali e appoggi temporizzati;
3. riconoscimento stabile di stati fisici o feedback macchina;
4. preset e parametri di timeout;
5. logica dei passi automatici;
6. logica manuale;
7. fault ed emergenza;
8. uscite e comandi macchina;
9. HMI e popup.

Questa scomposizione è obbligatoria perché nell'AWL originario tali logiche convivono nello stesso blocco, mentre nel target TIA vanno separate in blocchi con responsabilità diverse.

### 32.7 Regola di identificazione dei passi e delle transizioni dall'AWL

Nel parser AWL va considerato un pattern forte e quasi deterministico il seguente schema:

- lettura di un bit di passo `Sxx`;
- valutazione di una condizione combinatoria;
- salto condizionato in caso di condizione falsa;
- caricamento del numero di passo destinazione;
- scrittura del numero nella variabile di transizione o richiesta passo.

Quando questo schema viene riconosciuto, il convertitore deve estrarre:

- step sorgente;
- condizione di avanzamento;
- step destinazione.

La macchina a stati va quindi ricostruita a partire da questi edge e non da una lettura puramente lessicale dell'ordine dei segmenti.

### 32.8 Regola di separazione dei dati AWL nel nuovo modello

Un DB AWL unico non deve essere replicato nel target.

La regola corretta è separare i dati in base al ruolo:

- bit semantici di avanzamento -> `Transitions` nel DB `14..`;
- memorie di processo, consensi cumulativi e stati fisici -> `Memory` nel DB base `11..`;
- stato leggibile della sequenza, step attuale e storico -> `Seq Status` nel DB base `11..`;
- timer e contatori AWL -> `DB 13..` con tipi IEC e supporto `FC 13 Aux`;
- variabili esterne alla sequenza -> `DB 18.. EXT`;
- informazioni HMI e popup -> DB HMI.

Il runtime interno del GRAPH resta nel blocco GRAPH e non deve essere duplicato nel DB applicativo.

### 32.9 Regola di normalizzazione delle transizioni

Le condizioni di transizione AWL non vanno copiate direttamente come testo dentro il GRAPH.

Prima devono essere normalizzate in booleani semantici nel DB base e calcolate in una `FC 14 Transitions`.

Il GRAPH e la HMI devono poi consumare questi booleani già normalizzati.

Conseguenze:

- la `FC 14` è un compilatore di condizioni;
- il GRAPH usa transizioni semanticamente pulite;
- la HMI usa la stessa base semantica per popup e diagnostica;
- si evita di replicare più volte la stessa logica complessa in blocchi diversi.

### 32.9A Regola hard sul naming con suffisso e ownership dei DB

La sola suddivisione dei dati per famiglie non è sufficiente.

Il confronto con i tipici reali mostra che molte variabili devono essere non solo allocate nel DB corretto, ma anche nominate secondo la convenzione richiesta dal DB stesso; in caso contrario il blocco viene importato ma i riferimenti simbolici restano scollegati oppure incoerenti.

Regola hard:

- ogni variabile globale emessa dal tool deve avere un owner DB deterministico;
- ogni riferimento usato in `GRAPH`, `FC 12`, `FC 13`, `FC 14`, `FC 19` e HMI deve puntare al path reale del member nel DB che la contiene;
- se il DB di destinazione impone una convenzione di naming con prefisso o suffisso, il generatore deve rispettarla integralmente e non può sostituirla con nomi generici.

Conseguenze pratiche da considerare fissate:

- nel DB tipo OPIN i comandi e i preset devono restare nella famiglia `Pxxx`;
- nel DB tipo OPOUT uscite, lampade e stati comandati devono restare nella famiglia `Lxxx`;
- nel DB `14..` le variabili di transizione devono restare nel ramo `Transitions`;
- nel DB base `11..` le variabili di stato/memoria devono restare nei rami `Memory`, `Seq Status`;
- nel `DB 13.. AUX` i supporti tecnici devono restare nella famiglia ausiliaria e non migrare con naming libero in altri DB;
- nel DB HMI popup e condizioni devono mantenere il path HMI coerente al gruppo di appartenenza.

Non è quindi ammesso che il generatore produca variabili globali con nomi neutri o incompleti quando il target richiede naming specifico.

Esempi da considerare errore di generazione:

- usare un nome semantico libero dove il DB fisso richiede `P013`, `L045` o equivalente;
- referenziare da una FC un booleano globale senza il path del DB corretto;
- creare member globali provvisori che non corrispondono a nessuna convenzione reale del progetto.

Regola di validazione:

- il builder deve verificare per ogni simbolo globale il triplo vincolo `DB corretto + path corretto + naming corretto`;
- se uno dei tre elementi manca, la variabile va marcata come non risolta e non considerata valida per l'emissione finale.

### 32.9B Regola Excel strict sul popolamento DB

Quando la sorgente IR arriva da Excel con catalogo `operands`, il popolamento dei DB deve seguire una regola strict:

- la logica LAD delle transizioni GRAPH resta completa;
- i member DB vengono dichiarati solo se presenti nel catalogo `operands` o nelle categorie derivate (`alarm`, `aux`, `hmi`, `output`, `timer`, ...);
- non e' ammesso aggiungere member DB per inferenza opportunistica da testo AWL o parsing guard non catalogato.

Se una transizione usa operandi non presenti nel catalogo, il validator deve segnalarlo come warning di coerenza.

### 32.10 Regola di normalizzazione delle memorie e dei timer

I timer AWL `Txx`, i preset `S5T`, i bit di appoggio pulsati e le memorie tecniche non devono restare nel DB sequenza monolitico.

Devono essere convertiti in:

- istanze IEC nel `DB 13..`;
- reti LAD nella `FC 13 Aux`;
- eventuali memorie semantiche derivate nel DB base `11..`.

La `FC 13 Aux` ha quindi il ruolo di ricostruire in forma leggibile e importabile la parte di AWL che nel sorgente faceva da appoggio tecnico alla sequenza.

### 32.11 Regola sul backbone della sequenza

Il backbone non va inferito con rinomina forzata dei nomi passo.

Regola consolidata:

- l'ingresso sequenza e' `step_number=1`;
- manuale/fault/emergenza restano ruoli semantici da riconoscere nell'IR;
- il builder GRAPH puo' usare numbering convenzionale quando richiesto dal caso, ma senza imporre nomi hard-coded.

### 32.12 Regola sulle uscite macchina

Le uscite finali non vanno generate direttamente dalle bobine AWL originali.

Nel target TIA le uscite devono nascere dalla composizione di:

- step automatici attivi;
- comandi manuali;
- interblocchi;
- consensi permanenti;
- condizioni macchina già normalizzate.

La `FC 19 Output` è quindi un backend combinatorio separato che riceve segnali semantici dal DB base, dal GRAPH, dai DB fissi e dai DB I/O.

### 32.13 Regola sulla HMI

Le condizioni HMI non vanno costruite direttamente da segnali grezzi I/Q/T dell'AWL se esiste già una forma semantica normalizzata.

Il target corretto è:

- DB HMI con strutture popup e liste condizioni;
- `FC 12 HMI` che popola popup, testi e bit visualizzati;
- uso preferenziale di transizioni e memorie semantiche già calcolate.

La HMI va quindi trattata come consumer del modello semantico e non come duplicazione indipendente della logica AWL.

### 32.14 Regola sui fault e sulle emergenze

I fault tecnologici e le emergenze non vanno tradotti come insieme casuale di bobine sparse.

La regola corretta è:

- mantenere i DB allarme fissi del progetto come sorgenti o sink stabili;
- costruire cumulativi semantici di `Fault` ed `Emergency` nel modello base;
- collegare tali cumulativi ai nodi semantici di fault/emergenza del GRAPH;
- mantenere separata la diagnostica dettagliata dalla topologia del sequenziatore.

### 32.15 Regola sul naming dei passi GRAPH

La numerazione o il naming dei passi GRAPH non deve essere dedotto ciecamente dalla sola numerazione AWL storica.

I casi legacy mostrano che il target TIA può:

- preservare alcuni numeri di passo storici;
- rinominare semanticamente alcuni step;
- introdurre step di supporto più leggibili del sorgente.

Conseguenza progettuale:

- il convertitore deve separare `identità logica del passo` da `nome finale del passo`;

Corollario operativo sul naming delle variabili:

> la stessa libertà non vale per le variabili globali del pacchetto. Per queste il builder non può inventare naming libero: deve rispettare DB owner, path e convenzione richiesta dal blocco o DB target.
- la politica di naming finale del GRAPH deve essere una regola esplicita del builder e non una conseguenza accidentale del parser AWL.

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

# PARTE F - BASELINE FINALE DEL PROGETTO AL 22-04-2026

## 38. Baseline consolidata

Alla data del 22-04-2026 la baseline consolidata del progetto è la seguente.

### 38.1 Sul GRAPH

- target `GRAPH V2` confermato come scelta definitiva del progetto;
- esempi legacy di altre versioni runtime utilizzabili solo come riferimento semantico e architetturale, non come target di emissione;
- backend GRAPH validato su regole strutturali, topologiche e runtime;
- blocco `FB` da generare come elemento autosufficiente;
- supporto a operandi locali o referenziati simbolicamente nei DB applicativi del pacchetto;
- forte distinzione fra topologia GRAPH e logica OR nel LAD delle transition;
- ingresso GRAPH governato dal numero passo (`step_number=1`) e non dal nome; eventuali nodi speciali restano policy di modello.

### 38.2 Sul `GlobalDB`

- serializer stabile e ricorsivo;
- forma XML consolidata;
- commenti visibili in TIA;
- supporto a member strutturati, array e tipi IEC;
- ruolo dei DB chiarito come contenitori applicativi e di supporto del pacchetto;
- partizione dei DB di progetto fissata in `11..` base, `12..` sequenza, `18..` EXT, `19..` ausiliario;
- DB HMI da generare ex novo per popup e strutture HMI;
- DB fissi `81`, `82`, `2020`, `2025` da trattare come elementi stabili del modello di conversione.

### 38.3 Sul backend FC

- grammatica FC consolidata;
- box IEC consolidati in forma conservativa;
- pattern LAD elementari validati;
- supporto a variabili locali e globali;
- necessità ormai fissata di validator e linter semantico.

### 38.4 Sul metodo generale

- IR espliciti;
- doppio ingresso verso IR comune: parser AWL oppure Excel strutturato;
- validator strutturali;
- linter semantici;
- selezione dei pattern validati;
- serializer dedicati per backend;
- regressione su casi importati davvero in TIA;
- numbering dei blocchi vincolato in formato `XXGG` (famiglia + gruppo comune, con `03` solo esempio operativo);
- distinzione netta fra vincoli strutturali del target `V2` e soli riferimenti semantici ricavati da campioni legacy;
- scomposizione obbligatoria dell'AWL in famiglie logiche prima della traduzione;
- ricostruzione della macchina a stati a partire dagli edge estratti e non dal solo ordine dei segmenti;
- separazione obbligatoria fra modello semantico, builder GRAPH e backend HMI/Output;
- distinzione hard tra passi di sequenza e stati fisici/consensi (`UP`, `DOWN`, `STC` e simili), da allocare come memorie o transizioni semantiche e non come step GRAPH;
- generazione delle uscite come compilazione combinatoria di step automatici, manuale, interblocchi e consensi, non come copia diretta delle bobine AWL;
- riconoscimento del backbone automatico ricorrente `1 -> 2 -> 3 -> 4 -> 7` come pattern forte di sequenza sorgente, pur lasciando al builder la policy finale di naming e rinumerazione GRAPH.

### 38.5 Sul layer TIA

- bridge Linux/Windows operativo;
- import/compile/export reali verificati;
- pipeline end-to-end pronta per essere agganciata al convertitore.

### 38.6 Aggiornamenti operativi successivi consolidati

- nel `tia-bridge`, l'import e la compile sono job distinti (nessuna compile automatica post-import);
- il polling operativo traccia separatamente il `JobId` di import e l'eventuale `JobId` di compile richiesto esplicitamente;
- il generatore allinea in modo deterministico `GRAPH`, `GlobalDB` e `FC` sulle stesse transizioni, includendo anche i member delle transizioni sintetiche (es. `T_HOLD_*`, `T_CHAIN_*`) nei `GlobalDB` quando usati dalle reti LAD/GRAPH;
- la diagnostica compile lato `tia_windows_agent` è stata estesa con messaggi dettagliati, contesto e classificazione errori/warning.

### 38.7 Aggiornamento del 22-04-2026 (Excel FC timer/contatori)

- nel flusso Excel, timer e contatori usati in `support_fc` vengono emessi come blocchi LAD completi (`TON/TOF/TP`, `CTU/CTD/CTUD`);
- il preset viene letto dal catalogo `operands.control_value` (`PT` per timer, `PV` per contatori);
- i pin obbligatori dei contatori non valorizzati esplicitamente vengono cablati con default sicuro (`FALSE`) per prevenire errori di import TIA.

---

## 39. Prossimi passi consigliati

I prossimi passi più utili sono:

1. formalizzare un IR unico di progetto per sequenza, dati e reti, gia' coerente con la mappa famiglie `11/12/13/14/15/16/18/19` in formato `XXGG`;
2. costruire una libreria di pattern GRAPH e FC esplicitamente convalidati;
3. implementare validator e linter come parte obbligatoria della pipeline;
4. estendere i test reali su più tipologie di blocchi XML, mantenendo il target finale sempre in `V2`;
5. collegare la generazione AWL / Excel -> XML alla pipeline TIA già funzionante;
6. introdurre una matrice di regressione formale su golden sample importati con successo;
7. formalizzare nel generatore la regola hard di ingresso (`step_number=1`) e la policy esplicita sui nodi speciali di sicurezza;
8. fissare in codice una policy esplicita di naming dei passi GRAPH separata dalla numerazione storica AWL.

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

Alla data del 22-04-2026 il progetto ha raggiunto una baseline forte su quattro livelli:

1. reverse engineering strutturale del `GRAPH`;
2. generazione stabile dei `GlobalDB` applicativi e di supporto;
3. backend `FC` guidato da pattern e non da emissione libera;
4. pipeline reale `Linux -> bridge -> Windows -> TIA Portal Openness` verificata end-to-end.

Il problema centrale del progetto non è più capire se il workflow sia praticabile, ma rendere sistematica, deterministica e regressivamente sicura la conversione `AWL / Excel -> IR -> GRAPH XML (+ DB/FC)` su casi reali.

---

# PARTE G - INTEGRAZIONI CONSOLIDATE DAL NUOVO AWL ROMANIA (FC102)

## 43. Valore metodologico del nuovo sorgente AWL

Il file `AWL Romania` conferma in modo più leggibile la struttura reale della FC102 perché espone segmenti numerati, titoli funzionali e commenti che separano chiaramente:

- logiche di servizio;
- filtri e timer di dispositivo;
- stati fisici stabilizzati;
- edge della sequenza automatica;
- ramo manuale;
- ramo emergenza/fault;
- formule finali di uscita.

Di conseguenza il parsing della sequenza può essere considerato più robusto se basato su segmentazione semantica dei segmenti del sorgente, invece che su semplice scansione lineare del listato.

## 44. Regola sul backbone automatico ricorrente della FC102

Nel caso FC102 il nuovo AWL rende leggibile una catena automatica ricorrente della forma:

`S01 -> S02 -> S03 -> S04 -> S07 -> S10 -> S14 -> S18 -> S22 -> S26 -> S03`

con rami separati verso:

- `S29` per il manuale;
- `S32` per l'emergenza.

Questa osservazione consolida una regola di progetto:

> i passi iniziali `1, 2, 3, 4, 7` vanno trattati come pattern forte della sequenza sorgente AWL, presente in modo ricorrente e riconoscibile, anche se il naming finale del GRAPH può essere normalizzato dal builder.

## 45. Regola di distinzione tra passi di sequenza e stati fisici

Il nuovo AWL chiarisce che segnali come `UP`, `DOWN` e `STC` non sono passi della macchina a stati.

Essi rappresentano invece:

- feedback fisici filtrati nel tempo;
- consensi di avvio o di processo;
- memorie semantiche di stato macchina.

Regola consolidata:

> i feedback fisici stabilizzati non devono essere convertiti in step GRAPH; devono essere mappati nel modello target come memorie semantiche o condizioni di transizione, tipicamente nelle aree `Memory` e `Transitions` del `DB 11..`.

## 46. Regola sulla doppia famiglia dei timeout

Il caso FC102 distingue chiaramente due famiglie diverse di temporizzazioni:

1. timeout di dispositivo o di movimento, che generano fault o diagnostica;
2. preset temporali di sequenza, che modificano il comportamento del passo attivo.

Regola consolidata:

> i timer di fault e i preset di sequenza non vanno fusi nello stesso ruolo semantico. I primi devono alimentare diagnostica, fault e rami di sicurezza; i secondi devono essere portati nel modello della sequenza e nei backend ausiliari secondo il ruolo effettivo.

## 47. Regola sulle uscite macchina come compilazione semantica

Il nuovo AWL conferma che le uscite finali non derivano da una singola bobina sorgente, ma da formule miste che combinano:

- step automatici attivi;
- comandi manuali;
- consensi di modo operativo;
- interblocchi;
- segnali fisici di stato;
- eventuali lock o fault.

Regola consolidata:

> il backend `FC 19 Output` deve essere un compilatore combinatorio di uscite, non un semplice serializer di bobine AWL.

## 48. Regola sui fault, l'emergenza e il rientro alla sequenza

Il nuovo AWL chiarisce che i fault elementari e i bit allarme fissi vengono prima cumulati semanticamente e solo dopo influenzano la sequenza tramite variabili come `EM`.

Da tale cumulativo derivano:

- salto o mantenimento in `S32`;
- gestione del fault/backbone di sicurezza;
- regole di rientro verso il passo iniziale (numero `1`) dai rami manuale/emergenza quando le condizioni tornano valide.

Regola consolidata:

> il convertitore deve distinguere i dettagli diagnostici dai loro effetti sequenziali. I DB fissi di allarme restano il livello di dettaglio; la sequenza GRAPH deve consumare cumulativi semantici di `Fault` ed `Emergency` agganciati ai rami di sicurezza del modello.

## 49. Regola sulla policy di naming e sul passo finale del ciclo

Il confronto tra AWL FC102 e controparte TIA mostra che la topologia logica può essere mantenuta anche quando il target GRAPH introduce:

- nomi semanticamente più leggibili dei passi;
- rinumerazioni non perfettamente identiche al legacy;
- uno step di chiusura o fine ciclo prima del rientro al passo iniziale.

Regola consolidata:

> l'identità logica del passo va estratta in modo deterministico dal sorgente AWL; il naming finale del GRAPH è invece una policy del builder. Il builder può introdurre step target di chiusura o normalizzazione, purché preservi il comportamento funzionale della sequenza.
