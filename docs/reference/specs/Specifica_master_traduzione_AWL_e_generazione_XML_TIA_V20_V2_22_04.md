Specifica master consolidata del 21-04-2026
per le regole di traduzione e generazione XML
AWL / Excel -> IR -> GRAPH / GlobalDB / FC LAD per TIA Portal V20

> Documento unico che unisce: 1) la specifica normativa di traduzione `AWL / Excel -> IR -> blocchi TIA`, 2) la specifica rigida di generazione XML, 3) il template operativo e lo pseudo-codice del serializer.

# Uso del documento

Questo file è il riferimento unico per il convertitore.

Gerarchia documentale fissata:
- questa specifica prevale sui documenti operativi derivati;
- il report consolidato descrive baseline, evidenze e architettura del progetto;
- `docs/guide/standards/conventions.md`, `docs/guide/process/flow.md`, `docs/guide/operations/operations.md`, `docs/guide/integration/tia-integration.md` e `docs/guide/checklists/workflow-checklists.md` devono restare coerenti con questa specifica e non possono allentarne le regole hard.

Le Parti I-VI definiscono le regole di traduzione della sorgente di partenza (AWL oppure Excel strutturato), la costruzione dell'IR, il partizionamento nei blocchi TIA e le regole operative finali del convertitore.
Le Parti VII-IX definiscono la grammatica XML consolidata, il template operativo e lo pseudo-codice del serializer.

---

# Parte I - Principi generali della traduzione

Regola metodologica di fondo: il convertitore deve essere deterministico ma non letterale. Non deve copiare il contenitore storico dell'AWL; deve estrarre il significato della sequenza e ricostruirlo nel formato architetturalmente corretto del target TIA.

## 1. Obiettivo corretto della traduzione

L'obiettivo della traduzione non è produrre un XML formalmente valido che assomigli al sorgente.

L'obiettivo corretto è produrre un insieme di blocchi TIA V20 coerenti, importabili e manutentivi che preservino:

- comportamento funzionale;
- struttura sequenziale;
- leggibilità manutentiva;
- separazione corretta delle responsabilità.

Regola hard aggiuntiva:

- i blocchi generati non vanno considerati unità indipendenti;
- `FB GRAPH`, `GlobalDB`, `FC LAD` e ogni eventuale blocco aggiuntivo costituiscono un unico pacchetto coerente;
- la cardinalità del pacchetto è asimmetrica: per ogni sequenza AWL il generatore deve emettere esattamente `1 x FB GRAPH`, mentre i `GlobalDB` e le `FC LAD` devono essere trattati come insiemi a cardinalità variabile;
- la validità reale del risultato non è "XML singolarmente importabile", ma "insieme di blocchi coerente e compilabile";
- ogni simbolo, member, tag di transizione, nome blocco, contratto dati o assunzione runtime emessa in un blocco deve essere soddisfatta dagli altri blocchi del pacchetto che la consumano.

## 2. Regola di non equivalenza contenitore-contenitore

Una FC AWL monolitica non corrisponde a un solo blocco target.

La cardinalità corretta da usare in generazione è la seguente:

`1 sequenza AWL -> 1 x FB GRAPH + N x GlobalDB + M x FC LAD`

### 2.1 Regola hard di cardinalità

Il generatore deve applicare le seguenti regole senza eccezioni:

- da una singola sequenza AWL deve nascere una sola topologia sequenziale target;
- questa topologia deve essere emessa in un solo blocco `SW.Blocks.FB` GRAPH;
- non è ammesso spezzare la stessa sequenza AWL in due o più GRAPH distinti;
- i dati applicativi, le strutture HMI, gli ausiliari, gli I-O, i parametri e le altre aree non runtime devono essere partizionati in uno o più `SW.Blocks.GlobalDB`;
- le reti LAD di supporto devono essere partizionate in una o più `SW.Blocks.FC`, separate per famiglia funzionale quando il caso reale lo richiede.

### 2.2 Procedura obbligatoria di compilazione

Per ogni sequenza AWL il convertitore deve procedere in questo ordine:

1. identificare nell'IR una sola macchina a stati della sequenza;
2. compilare tale macchina a stati in `1 x FB GRAPH`;
3. estrarre dall'IR tutti i dati non runtime GRAPH e partizionarli nei `GlobalDB` richiesti dal modello;
4. estrarre dall'IR tutte le reti combinatorie e di supporto non appartenenti al GRAPH e partizionarle nelle `FC LAD` richieste dal modello;
5. validare che nessun riferimento del GRAPH, dei DB e delle FC punti a member o blocchi non emessi nel pacchetto finale.

### 2.3 Famiglie minime da supportare

Il generatore deve poter emettere almeno le seguenti famiglie architetturali:

- `1 x FB GRAPH` della sequenza;
- `DB 11..` base;
- `DB 12..` HMI;
- `DB 13..` AUX;
- `DB 14..` transitions;
- `DB 16..` sequenza;
- `DB 18.. EXT`;
- `DB 19..` output;
- `DB HMI`;
- `FC 02 HMI`;
- `FC 03 Aux`;
- `FC 04 Transitions`;
- `FC 06 Output`;
- eventuali blocchi addizionali di servizio coerenti col progetto.

### 2.4 Esempio verificativo sui file XML di riferimento

Nel pacchetto `T1-A ARUNC` il comportamento atteso del generatore è confermato dalla struttura osservata:

- un solo blocco sequenziale `05 T1-A ARUNC Sequence`;
- più FC di supporto: `02 T1-A ARUNC HMI`, `03 T1-A ARUNC Aux`, `04 T1-A ARUNC Transitions`, `06 T1-A ARUNC Output`, `07 T1-A ARUNC LEV2`;
- più DB applicativi e di integrazione: `T1-A ARUNC`, `T1-A ARUNC HMI`, `T1-A ARUNC I-O`, `T1-A ARUNC AUX`, `T1-A ARUNC PARAMETERS`, `T1-A ARUNC LEV2`, oltre a DB esterni come `DB81-OPIN` e `DB82-OPOUT`.

Questo esempio va usato come verifica di cardinalità del pacchetto, non come eccezione.

## 3. Regola di target definitivo

Il target di emissione è chiuso su:

- `TIA Portal V20`;
- `GRAPH V2`;
- datatype runtime della famiglia `..._V2`.

Ogni campione legacy di altra famiglia runtime va usato solo come riferimento semantico e non come pattern finale da emettere.

## 4. Regola di ingresso e backbone del sequenziatore

La struttura iniziale del sequenziatore non deve dipendere dal nome testuale del passo.

Interpretazione operativa:

- lo step iniziale e' quello con `step_number=1`;
- il nome passo e' libero (`Init`, `Start`, `S1`, ...);
- i ruoli manuale/fault/emergenza vanno riconosciuti semanticamente nell'IR e modellati nel GRAPH secondo la policy di progetto, senza rinomina forzata dei nomi.

Il parser AWL deve riconoscere la logica che porta a questi stati; il builder GRAPH deve preservare topologia e semantica senza imporre nomi hard-coded.

## 4-bis. Regola di doppio ingresso dell'IR

L'IR del convertitore può essere alimentato da due sorgenti ammesse:

- parser AWL;
- Excel strutturato di progetto.

Le due sorgenti devono convergere sullo stesso contratto semantico di steps, transitions, memories, timers, outputs, hmi_conditions ed external_refs.

Non è ammesso introdurre un backend XML separato che trasformi direttamente l'Excel in blocchi finali bypassando l'IR comune.

L'Excel va quindi trattato come sorgente alternativa di modellazione e catalogazione, non come formato finale di emissione.

### 4-ter. Contratto fogli Excel (formato consolidato 21-04-2026)

Per il percorso Excel del convertitore, il contratto minimo dei fogli e' da considerare hard:

- `operands` obbligatorio;
- `support_fc` obbligatorio;
- `support_fc` e' pagina unica FC e contiene sia dati member sia logica LAD.

Colonne canoniche di `support_fc`:

- `category`
- `member_name`
- `result_member`
- `condition_expression`
- `condition_operands`
- `comment`
- `network`

Regole hard:

- almeno una riga valida in `support_fc` con `member_name` e/o `result_member`;
- `network` e' il numero rete della FC per ordinare le compile unit;
- `network_index` resta solo alias legacy in input e non cambia il contratto canonico;
- non e' ammesso introdurre una pipeline separata che dipenda da un foglio FC logico dedicato diverso da `support_fc`.

# Parte II - Regole di analisi del sorgente AWL

## 5. Regola di segmentazione primaria

La FC AWL va segmentata in famiglie logiche prima di qualunque tentativo di emissione target.

Famiglie minime da riconoscere:

1. allarmi e timeout di dispositivo;
2. memorie generali e appoggi temporizzati;
3. riconoscimento stabile di feedback e stati fisici;
4. preset e parametri di timeout;
5. sequenza automatica;
6. logica manuale;
7. fault ed emergenza;
8. uscite macchina;
9. HMI e popup.

L'ordine sorgente può aiutare l'analisi, ma la classificazione deve essere semantica e non solo testuale.

## 6. Regola di riconoscimento dei passi AWL

Un passo AWL va identificato tramite i bit di stato del sequenziatore storico, tipicamente della forma `Sxx`.

Un bit `Sxx` non è ancora uno step GRAPH finale, ma è un marcatore affidabile di identità logica del passo sorgente.

Il convertitore deve registrare per ogni passo almeno:

- id logico sorgente;
- nome sorgente se disponibile;
- reti che lo leggono;
- reti che lo attivano;
- azioni eseguite mentre il passo è attivo.

## 7. Regola di riconoscimento delle transizioni AWL

Va considerato pattern forte di transizione lo schema seguente:

- test di un passo `Sxx`;
- valutazione di una condizione combinatoria;
- salto condizionato se la condizione è falsa;
- caricamento del numero del passo destinazione;
- scrittura del numero nella variabile di transizione o richiesta passo.

Quando questo pattern è presente, il convertitore deve estrarre un edge semantico:

- `source_step`;
- `guard_condition`;
- `target_step`.

## 8. Regola di non dipendenza dall'ordine dei segmenti

L'ordine dei segmenti AWL non è una rappresentazione affidabile della topologia finale della macchina a stati.

La topologia va ricostruita dagli edge estratti e non dall'ordine in cui i segmenti appaiono nel listato.

## 9. Regola di riconoscimento dei timer storici

I timer storici dell'AWL, inclusi `Txx`, `S5T#...`, `SD`, `SE` e pattern equivalenti, non vanno lasciati nel modello sequenziale principale.

Vanno estratti come entità tecniche con:

- trigger di avvio;
- preset;
- semantica d'uso;
- bit di uscita;
- relazione con memorie o fault derivati.

## 10. Regola di riconoscimento delle memorie tecniche e semantiche

Non tutte le memorie AWL hanno lo stesso ruolo.

Il convertitore deve distinguere almeno:

- memoria tecnica di appoggio;
- memoria di stato fisico;
- memoria di consenso permanente;
- memoria cumulativa di fault;
- memoria di comando;
- memoria manuale;
- memoria di sequenza.

## 11. Regola di riconoscimento di fault ed emergenza

Le logiche di fault ed emergenza vanno identificate come classe autonoma.

Non devono essere trattate come semplici condizioni locali di transizione.

Il parser deve estrarre:

- fault elementari;
- cumulativi di fault;
- condizioni di emergenza;
- reset fault;
- condizioni di rientro.

## 12. Regola di riconoscimento di manuale e automatico

La logica di modo operativo non è una semplice condizione aggiuntiva.

Va modellata esplicitamente distinguendo:

- richiesta manuale;
- richiesta automatica;
- conferma automatica;
- comandi manuali di attuatore;
- vincoli di rientro da manuale a automatico.

# Parte III - Regole di costruzione dell'IR

## 13. IR minimo obbligatorio

Prima della compilazione verso i blocchi TIA, indipendentemente dal fatto che la sorgente sia AWL o Excel strutturato, il convertitore deve costruire un IR esplicito contenente almeno:

- `steps`;
- `transitions`;
- `timers`;
- `memories`;
- `faults`;
- `manual_logic`;
- `auto_logic`;
- `outputs`;
- `hmi_conditions`;
- `external_refs`.

## 14. Regola di separazione tra identità logica e nome finale

Nell'IR ogni passo deve avere almeno due livelli distinti:

- identità logica del passo sorgente;
- nome finale del passo target.

Questo è necessario perché i casi reali mostrano che il GRAPH finale può:

- preservare alcuni numeri storici;
- rinominare semanticamente alcuni step;
- introdurre step target più leggibili del legacy.

## 15. Regola di rappresentazione delle transizioni

Ogni transizione nell'IR deve contenere almeno:

- identificativo;
- step sorgente;
- step destinazione;
- formula booleana normalizzata;
- dipendenze da timer;
- dipendenze da variabili esterne;
- dipendenze da fault o interblocchi;
- tag che ne indicano la famiglia semantica.

## 16. Regola di rappresentazione delle memorie

Ogni memoria nell'IR deve contenere almeno:

- nome sorgente;
- ruolo semantico;
- area target proposta;
- eventuale remanenza;
- dipendenze di calcolo;
- consumer target.

## 17. Regola di rappresentazione dei timer

Ogni timer nell'IR deve contenere almeno:

- identificativo sorgente;
- preset;
- tipo target IEC proposto;
- trigger di attivazione;
- output derivati;
- area target proposta nel `DB 13..`.

## 18. Regola di rappresentazione delle uscite

Le uscite non vanno memorizzate come semplice copia della bobina sorgente.

Ogni uscita va rappresentata come formula target composta da:

- passi automatici attivi;
- comandi manuali;
- interblocchi;
- consensi permanenti;
- eventuali fault o lock.

## 19. Regola di rappresentazione della HMI

Le condizioni HMI devono essere entità esplicite dell'IR.

Per ognuna devono esistere almeno:

- gruppo popup target;
- numero o chiave popup;
- lista condizioni normalizzate;
- testi o label associate;
- fonte semantica delle condizioni.

# Parte IV - Regole di partizionamento nel target TIA

## 20. Regola di numbering dei blocchi

La convenzione fissa del progetto è:

- il numero blocco reale e' il valore XML `<Number>`;
- il formato e' `XXGG`:
  - `XX` identifica la famiglia funzionale del blocco;
  - `GG` e' il numero comune di gruppo della traduzione;
- `GG` non e' fisso: `03` e' un esempio operativo, non un vincolo semantico.

Mappa famiglie consolidata:
- `11GG` -> alarms/diag;
- `12GG` -> HMI;
- `13GG` -> AUX;
- `14GG` -> transitions;
- `15GG` -> GRAPH (FB);
- `16GG` -> sequenza;
- `18GG` -> external;
- `19GG` -> output.

## 21. Regola sui DB di progetto

La distribuzione corretta dei dati è:

- `11GG` = DB allarmi/diagnostica;
- `12GG` = DB HMI;
- `13GG` = DB AUX;
- `14GG` = DB transitions;
- `16GG` = DB sequenza;
- `18GG` = DB `EXT`;
- `19GG` = DB output.

## 21-bis. Regola di natura normativa della partizione target

La partizione per famiglie `11GG/12GG/13GG/14GG/15GG/16GG/18GG/19GG` definita in questa specifica e' una regola del convertitore target e del serializer finale.

Non deve essere letta come vincolo retroattivo sui tipici legacy del corpus.

Conseguenze operative:

- i file legacy possono presentare strutture diverse, accorpate o storicamente ibride;
- tali strutture restano utili per riconoscimento semantico, mapping e reverse engineering;
- il backend finale del progetto deve comunque emettere la partizione target fissata dalla presente specifica quando non vi siano eccezioni progettuali deliberate e modellate nell'IR.

## 22. Regola di allocazione nel `DB 11..`

Nel DB base devono confluire almeno:

- `Seq Status`;
- `Transitions`;
- `Memory`;
- eventuali strutture semantiche di diagnostica o stato leggibile del sequenziatore.

Il `DB 11..` è il contenitore leggibile dell'applicazione, non il runtime interno del GRAPH.

## 23. Regola di allocazione nel `DB 16..`

Il `DB 16..` rappresenta il contenitore della sequenza in se', secondo il modello di progetto adottato.

Non deve essere usato come replica del vecchio DB AWL unico se questo conteneva ruoli misti.

## 24. Regola di allocazione nel `DB 18.. EXT`

Nel `DB 18..` devono finire tutte le variabili che arrivano dall'esterno della sequenza, ad esempio:

- comandi impianto;
- feedback macchina esterni;
- segnali provenienti da altri blocchi o altre sezioni impianto;
- riferimenti fissi di progetto esposti al sequenziatore.

## 25. Regola di allocazione nel `DB 13.. AUX`

Nel `DB 13..` devono finire:

- timer IEC;
- contatori IEC;
- one-shot;
- appoggi tecnici;
- supporti necessari alle reti della `FC 03 Aux`.

## 25-bis. Regola hard di ownership DB da Excel (`operands`)

Quando la sorgente e' Excel:

- il DB owner di ogni variabile e' determinato dal catalogo `operands`;
- l'uso cross-categoria nelle FC e' ammesso, ma non deve spostare il DB owner della variabile;
- i riferimenti LAD devono puntare al DB owner reale, anche se la variabile e' usata in una FC di categoria diversa;
- eccezione di robustezza su `FC transitions`: se un owner non e' risolto, fallback sul DB transitions per evitare import error.

## 26. Regola di allocazione HMI

Nel DB HMI devono finire:

- popup;
- liste condizioni;
- strutture visualizzate;
- campi di supporto all'operatore;
- eventuali testi o numerazioni di supporto HMI.

## 26-bis. Regola hard di assegnazione, naming e serializzazione delle variabili globali

Questa regola non definisce una policy generica di naming.

Definisce invece come il convertitore deve decidere, scrivere e validare il nome finale e il path finale di ogni variabile globale del pacchetto XML.

La sola allocazione per famiglia non basta: una variabile globale e' corretta solo quando il convertitore ha determinato in modo univoco:

- il DB owner reale;
- il ramo strutturale interno al DB;
- il nome finale del member foglia;
- la forma completa del path simbolico usato dai consumer;
- la coerenza del riferimento in tutti i blocchi che la leggono o la scrivono.

### 26-bis.1 Record minimo obbligatorio nell'IR

Prima della serializzazione XML, per ogni variabile globale l'IR deve contenere almeno:

- `semantic_role`;
- `owner_db_kind`;
- `owner_db_name`;
- `target_branch_path`;
- `leaf_member_name`;
- `naming_policy`;
- `consumers`;
- `source_ref`.

Non e' ammesso arrivare al serializer XML con il solo nome semantico libero della variabile.

### 26-bis.2 Procedura obbligatoria di risoluzione

Per ogni variabile globale il convertitore deve eseguire sempre i passi seguenti, nell'ordine indicato.

1. classificare la variabile per ruolo semantico (`transition`, `memory`, `seq_status`, `ext_command`, `output_state`, `hmi_condition`, `aux_timer`, `aux_support`, `io_signal` o altra classe prevista dal modello);
2. scegliere il DB target in funzione della classe semantica e non del solo nome storico AWL;
3. scegliere il ramo interno al DB target;
4. applicare la convenzione di naming obbligatoria di quel DB o di quel ramo;
5. costruire il path simbolico completo che verra' serializzato negli `Access/Symbol/Component` dei blocchi consumer;
6. verificare che ogni consumer del pacchetto referenzi esattamente quel path e non una variante semplificata.

Se uno di questi sei passi non e' risolto, la variabile non e' emettibile nel pacchetto finale.

### 26-bis.3 Mapping vincolante DB -> naming -> path

Il mapping seguente va considerato normativo.

- Variabili semantiche di avanzamento del sequenziatore -> DB base `11..`, ramo `Transitions`, leaf name semantico leggibile. Forma target: `<DB11>.Transitions.<nome>`.
- Memorie semantiche, consensi cumulativi, stati fisici stabilizzati -> DB base `11..`, ramo `Memory`, leaf name semantico leggibile. Forma target: `<DB11>.Memory.<nome>`.
- Stato leggibile della sequenza e storico -> DB base `11..`, ramo `Seq Status`. Forma target: `<DB11>.Seq Status.<campo>`.
- Variabili esterne di comando/preset gia' appartenenti a DB fissi di comando tipo OPIN -> DB fisso esterno, leaf name obbligatorio della famiglia `Pnnn`. Non e' ammesso sostituire `P013` con un nome semantico libero come `Cmd_Up`.
- Variabili esterne di uscita o stato comandato gia' appartenenti a DB fissi tipo OPOUT -> DB fisso esterno, leaf name obbligatorio della famiglia `Lnnn`. Non e' ammesso sostituire `L045` con un nome semantico libero come `ShakerCmd`.
- Condizioni HMI elementari -> DB HMI, ramo `Conditions.<gruppo>.Conditions.nX`. Non e' ammesso saltare il ramo intermedio `Conditions` del gruppo. Questa regola vale per le condizioni elementari del popup e non esaurisce la struttura del gruppo HMI.
- Strutture HMI operative -> DB HMI, ramo `HMI.*` secondo la struttura del blocco HMI generato.
- Metadati e stati di gruppo HMI -> DB HMI, all'interno del gruppo `Conditions.<gruppo>` oppure in rami equivalenti del modello HMI finale, con campi come `PopUpNumber`, `ConditionOK`, `Visible`, `FO` o equivalenti. Non e' ammesso ridurre tutto il modello HMI al solo vettore `nX`.
- Timer, one-shot e supporti tecnici -> DB `13.. AUX`, rami coerenti con il modello ausiliario, ad esempio `AUX.TIMER[...]`, `AUX.OS[...]`, `AUX_MEMORY.*`.
- Segnali I/O fisici modellati in DB dedicato -> DB I-O, rami `DI.*` o `DO.*`.

### 26-bis.4 Come deve essere scritto il riferimento XML

Quando un blocco consumer usa una variabile globale, il riferimento non deve essere serializzato come nome piatto.

Deve essere scritto come catena completa di `Component Name`, nell'ordine reale del path simbolico.

Forma corretta di principio:

```text
<Access Scope="GlobalVariable">
  <Symbol>
    <Component Name="<DB owner>" />
    <Component Name="<ramo 1>" />
    <Component Name="<ramo 2>" />
    <Component Name="<leaf>" />
  </Symbol>
</Access>
```

Questo vale per `GRAPH`, `FC 02`, `FC 03`, `FC 04`, `FC 06` e per ogni altro blocco consumer del pacchetto.

### 26-bis.5 Esempi vincolanti ricavati dagli XML campione

Gli XML osservati nel progetto fissano le seguenti forme target, che il convertitore deve riprodurre.

Esempio 1: una transizione semantica nel DB base viene referenziata come path completo del tipo:

```text
T1-A ARUNC -> Transitions -> Bypass ilock
```

Esempio 2: una memoria semantica nel DB base viene referenziata come path completo del tipo:

```text
T1-A ARUNC -> Memory -> Permanent Condition
```

Esempio 3: una condizione HMI non usa un nome libero, ma un path strutturato del tipo:

```text
T1-A ARUNC HMI -> Conditions -> MOV_UP -> Conditions -> n1
```

Esempio 4: nel DB di comando esterno il member foglia deve restare nella famiglia `Pnnn`, come nei casi `P001`, `P013`.

Esempio 5: nel DB di uscita esterno il member foglia deve restare nella famiglia `Lnnn`, come nei casi `L001`, `L045`.

Esempio 6: nel DB ausiliario i supporti tecnici non sono member sciolti, ma restano sotto rami strutturali come `AUX.TIMER`, `AUX.OS`, `AUX_MEMORY`.

### 26-bis.6 Regole di emissione per il generatore

Il generatore deve applicare le regole seguenti.

- Se il target e' il DB base `11..`, il leaf name puo' essere semantico leggibile, ma il ramo deve essere obbligatoriamente uno fra `Transitions`, `Memory`, `Seq Status`.
- Se il target e' un DB fisso esterno che usa codifica storica, il leaf name non deve essere rigenerato semanticamente: deve essere quello canonico del DB target (`Pnnn`, `Lnnn` o altra famiglia fissata dal blocco reale).
- Se il target e' HMI, il convertitore deve emettere il path HMI completo, incluso il gruppo e l'indice `nX` delle condizioni elementari quando il modello HMI lo richiede.
- Se il target e' AUX, il convertitore deve emettere supporti tecnici soltanto dentro le strutture ausiliarie previste e non come member globali sciolti.
- Se il nome canonico del DB fisso non e' ricostruibile in modo deterministico a partire dall'AWL e dal mapping disponibile, il convertitore deve marcare il punto come `mapping_required` e non deve inventare un nome libero.

### 26-bis.7 Errori da considerare bloccanti

Devono essere considerati errori bloccanti di generazione almeno i seguenti casi:

- variabile globale senza `owner_db_name` determinato;
- variabile globale con DB corretto ma ramo interno errato;
- variabile globale con ramo corretto ma leaf name non conforme alla convenzione del DB target;
- `Access/Symbol` che omette uno o piu' componenti del path reale;
- uso in una FC o nel GRAPH di placeholder come `var_*`, `temp_*`, `memory_*` o equivalenti come nome globale finale;
- emissione di nomi semantici liberi dentro DB fissi che richiedono codifica storica;
- presenza di due candidate destinazioni diverse per lo stesso simbolo globale senza disambiguazione deterministica.

### 26-bis.8 Validator obbligatorio

Prima dell'emissione finale il convertitore deve eseguire un validator dedicato sul naming globale.

Il validator deve verificare, per ogni simbolo globale usato dal pacchetto, il triplo vincolo seguente:

`DB corretto + path corretto + naming corretto`

La variabile e' valida solo se il triplo vincolo e' soddisfatto e se tutti i consumer del pacchetto usano esattamente lo stesso path.

# Parte V - Regole di costruzione dei backend target

## 27. Regola sul backend `FC 04 Transitions`

La `FC 04` deve calcolare le condizioni di avanzamento semantiche.

Non deve limitarsi a copiare l'AWL.

Deve:

- produrre booleani nominati e leggibili;
- raccogliere logiche comuni riusabili da GRAPH e HMI;
- separare il calcolo della condizione dalla topologia della sequenza.

## 28. Regola sul backend `FC 03 Aux`

La `FC 03 Aux` deve ricostruire in LAD la parte tecnica del sorgente AWL:

- timer;
- appoggi;
- memorie temporanee;
- riconoscimento stabile di sensori o stati fisici;
- comandi tecnici derivati.

## 29. Regola sul backend `FC 06 Output`

La `FC 06 Output` deve generare i comandi finali macchina a partire da segnali semantici già puliti.

Le uscite devono nascere dalla composizione di:

- step automatici attivi;
- comandi manuali;
- interblocchi;
- consensi permanenti;
- condizioni macchina normalizzate.

## 30. Regola sul backend `FC 02 HMI`

La `FC 02 HMI` deve trattare la HMI come consumer del modello semantico.

Deve quindi usare preferenzialmente:

- booleane in `Transitions`;
- memorie semantiche in `Memory`;
- fault ed emergency già normalizzati;
- strutture popup del DB HMI.

## 31. Regola sul GRAPH

Il GRAPH non deve contenere tutta la complessità storica dell'AWL in forma grezza.

Deve contenere:

- backbone coerente con il modello IR;
- ingresso sequenza deterministico (`step_number=1`);
- passi automatici espliciti;
- transizioni già normalizzate;
- runtime interno `..._V2`;
- topologia coerente con il sottoinsieme validato del progetto.

## 32. Regola sui fault e sulle emergenze nel target

Fault ed emergenza devono essere trattati su due livelli distinti:

- livello dettagliato di diagnostica e allarme;
- livello sintetico di governo della sequenza.

Il livello sintetico è quello che guida:

- i rami semantici di fault;
- i rami semantici di emergenza;
- reset;
- rientro alla sequenza.

## 33. Regola sui DB fissi esterni

I DB esterni stabili del progetto vanno trattati come riferimenti `1:1` del modello, non come variabili da reinventare caso per caso.

Sono da considerare fissi almeno:

- `DB81`;
- `DB82`;
- `DB2020`;
- `DB2025`.

# Parte VI - Regole operative finali del convertitore

## 34. Pipeline obbligatoria

La pipeline corretta del convertitore è:

`AWL / Excel -> normalizzazione sorgente -> IR -> partizionamento dati -> builder GRAPH/DB/FC -> serializer XML V2 -> validator -> import TIA`

## 35. Regola di non scorciatoia

Non è ammesso il percorso diretto:

`AWL testo libero -> XML finale`

oppure

`Excel foglio libero -> XML finale`

senza passare da:

- IR semantico;
- partizionamento dati;
- builder separati;
- validator strutturali;
- linter semantici.

## 36. Regola di qualità della traduzione

Una traduzione va considerata corretta solo se soddisfa contemporaneamente:

- coerenza funzionale col sorgente;
- coerenza architetturale col target;
- importabilità in TIA;
- leggibilità manutentiva;
- compatibilità col backbone semantico del progetto.

## 37. Sintesi finale

Le regole consolidate di traduzione del progetto portano a questa conclusione pratica:

- la sorgente AWL deve essere interpretata semanticamente e non copiata nel contenitore storico;
- l'Excel strutturato può alimentare lo stesso IR del flusso AWL, ma non bypassarlo;
- l'IR è il centro del convertitore;
- il partizionamento dei dati è una regola hard del metodo;
- GRAPH, DB, FC e HMI sono backend distinti ma coordinati;
- il target finale resta esclusivamente `TIA Portal V20 / GRAPH V2`.


---

# Parte VII - Specifica rigida di generazione XML

Regola metodologica di fondo: il generatore deve essere universale ma non libero. Deve emettere solo pattern, topologie e strutture che rientrano nel sottoinsieme validato.

## 1. SW.Blocks.FB GRAPH

Obiettivo: generare un FB GRAPH autosufficiente per topologia, runtime, Temp e Static.

Root obbligatorio: Document -> Engineering version="V20" -> SW.Blocks.FB ID="0".

Dentro AttributeList devono comparire: GraphVersion, Interface, Name, Namespace, Number, ProgrammingLanguage, SetENOAutomatically.

L'Interface deve dichiarare localmente il namespace SW/Interface/v5.

La sezione Base deve contenere GRAPH_BASE con Input, Output, InOut e Static.

Le sezioni effettivamente consolidate sono: Input, Output, InOut, Static, Temp, Constant.

In Static devono esistere almeno RT_DATA : G7_RTDataPlus_V2, un G7_TransitionPlus_V2 per ogni transition e un G7_StepPlus_V2 per ogni step.

In Temp devono esistere gli ET_Tx per le transition temporizzate.

Nel CompileUnit il NetworkSource deve contenere Graph nel namespace SW/NetworkSource/Graph/v5.

La Sequence deve essere composta da Steps, Transitions, Branches e Connections.

Le transition sono in LAD e vanno emesse nel sottoinsieme sicuro: Access, Contact, Contact negato, O, comparatori validati, TrCoil.

I branch consolidati sono AltBegin, SimBegin, SimEnd; i link ammessi sono Direct e Jump.

### Composizione canonica

```text
Document
  Engineering version="V20"
  SW.Blocks.FB ID="0"
    AttributeList
      GraphVersion = 2.0
      Interface
        Sections xmlns=".../SW/Interface/v5"
          Section Base
          Section Input
          Section Output
          Section InOut
          Section Static
          Section Temp
          Section Constant
      Name
      Namespace
      Number
      ProgrammingLanguage = GRAPH
      SetENOAutomatically = false
    ObjectList
      MultilingualText Comment
      SW.Blocks.CompileUnit
        AttributeList
          NetworkSource
            Graph xmlns=".../SW/NetworkSource/Graph/v5"
              PreOperations
              Sequence
                Steps
                Transitions
                Branches
                Connections
              PostOperations
```

### Esempio minimo

```text
<?xml version="1.0" encoding="utf-8"?>
<Document>
  <Engineering version="V20" />
  <SW.Blocks.FB ID="0">
    <AttributeList>
      <GraphVersion>2.0</GraphVersion>
      <Interface><Sections xmlns="http://www.siemens.com/automation/Openness/SW/Interface/v5">
  <Section Name="Base">
    <Sections Datatype="GRAPH_BASE" Version="1.0">
      <Section Name="Input" />
      <Section Name="Output" />
      <Section Name="InOut" />
      <Section Name="Static" />
    </Sections>
  </Section>
  <Section Name="Input">
    <Member Name="condition_type_1_transition_1" Datatype="Bool" />
  </Section>
  <Section Name="Output" />
  <Section Name="InOut" />
  <Section Name="Static">
    <Member Name="RT_DATA" Datatype="G7_RTDataPlus_V2" Version="1.0" />
    <Member Name="Transition_1" Datatype="G7_TransitionPlus_V2" Version="1.0" />
    <Member Name="Step_1" Datatype="G7_StepPlus_V2" Version="1.0" />
  </Section>
  <Section Name="Temp" />
  <Section Name="Constant" />
</Sections></Interface>
      <Name>Type_1</Name>
      <Namespace />
      <Number>1</Number>
      <ProgrammingLanguage>GRAPH</ProgrammingLanguage>
      <SetENOAutomatically>false</SetENOAutomatically>
    </AttributeList>
  </SW.Blocks.FB>
</Document>
```

## 2. SW.Blocks.GlobalDB

Obiettivo: generare uno o più `SW.Blocks.GlobalDB` applicativi del pacchetto, senza replicare il runtime interno del GRAPH.

Il root obbligatorio è Document -> Engineering version="V20" -> SW.Blocks.GlobalDB ID="0".

In AttributeList devono comparire: Interface, MemoryLayout, MemoryReserve (se usato), Name, Namespace, Number, ProgrammingLanguage.

L'Interface usa Sections con namespace locale SW/Interface/v5.

La sezione dati consolidata è Section Name="Static".

Ogni Member può contenere AttributeList, Comment, StartValue e figli Member se il Datatype è Struct.

I commenti visibili in TIA devono essere emessi in forma semplice Comment + MultiLanguageText.

IEC_TIMER e IEC_COUNTER vanno serializzati con Version="1.0".

Nessun `GlobalDB` del pacchetto deve replicare RT_DATA né gli statici runtime del GRAPH.

Regola di coerenza cross-blocco (hard):

- ogni tag usato nelle transition GRAPH o nelle reti LAD di supporto deve essere dichiarato in uno dei `GlobalDB` emessi nel pacchetto;
- la sorgente canonica dei tag di guardia deve essere la topologia finale delle transizioni, incluse eventuali transizioni sintetiche (es. `T_HOLD_*`, `T_CHAIN_*`);
- non è ammesso generare riferimenti LAD/GRAPH a member non presenti nei `GlobalDB` effettivamente emessi.

Estensione obbligatoria della regola:

- la coerenza cross-blocco non riguarda solo `GRAPH <-> GlobalDB`;
- vale anche per `GRAPH <-> FC`, `FC <-> GlobalDB` e, più in generale, per ogni coppia di blocchi del pacchetto che si referenziano fra loro;
- non è ammesso che un blocco del pacchetto compili soltanto assumendo naming o member che gli altri blocchi non emettono realmente.

Regola aggiuntiva per IR da Excel (modalita' strict):

- la logica transizioni GRAPH deve mantenere gli operandi della condizione;
- la dichiarazione member nei `GlobalDB` deve usare il catalogo `operands` dell'Excel (piu' categorie derivate);
- non e' ammesso introdurre member DB non catalogati per inferenza non esplicita.
- per le FC di supporto, member e logica devono essere letti dal foglio unico `support_fc` secondo il contratto di cui alla sezione 4-ter.

### Composizione canonica

```text
Document
  Engineering version="V20"
  SW.Blocks.GlobalDB ID="0"
    AttributeList
      Interface
        Sections xmlns=".../SW/Interface/v5"
          Section Name="Static"
            Member
            Member
      MemoryLayout
      MemoryReserve
      Name
      Namespace
      Number
      ProgrammingLanguage = DB
    ObjectList
      MultilingualText Comment
      MultilingualText Title
```

### Esempio minimo

```text
<?xml version="1.0" encoding="utf-8"?>
<Document>
  <Engineering version="V20" />
  <SW.Blocks.GlobalDB ID="0">
    <AttributeList>
      <Interface><Sections xmlns="http://www.siemens.com/automation/Openness/SW/Interface/v5">
  <Section Name="Static">
    <Member Name="var_1" Datatype="Bool" />
    <Member Name="var_2" Datatype="Int" />
    <Member Name="var_4" Datatype="Array[0..9] of Bool" Remanence="Retain" />
    <Member Name="var_5" Datatype="Struct">
      <Member Name="var_5_1" Datatype="Bool" />
      <Member Name="var_5_2" Datatype="Int" />
      <Member Name="var_5_3" Datatype="Real" />
    </Member>
    <Member Name="var_8" Datatype="IEC_COUNTER" Version="1.0" />
    <Member Name="var_9" Datatype="IEC_TIMER" Version="1.0" />
  </Section>
</Sections></Interface>
      <MemoryLayout>Optimized</MemoryLayout>
      <MemoryReserve>100</MemoryReserve>
      <Name>db_1</Name>
      <Namespace />
      <Number>1</Number>
      <ProgrammingLanguage>DB</ProgrammingLanguage>
    </AttributeList>
  </SW.Blocks.GlobalDB>
</Document>
```

## 3. SW.Blocks.FC in LAD

Obiettivo: generare reti LAD importabili, solo tramite pattern già validati.

Il root obbligatorio è Document -> Engineering version="V20" -> SW.Blocks.FC ID="0".

In AttributeList devono comparire: Interface, MemoryLayout, Name, Namespace, Number, ProgrammingLanguage, SetENOAutomatically.

L'Interface standard contiene Input, Output, InOut, Temp, Constant e Return con Ret_Val : Void.

Un FC importabile è una lista ordinata di CompileUnit.

Dentro ogni CompileUnit il NetworkSource contiene FlgNet nel namespace SW/NetworkSource/FlgNet/v5.

Ogni FlgNet deve essere composto da Parts e Wires coerenti.

L'OR va serializzato con Part Name="O" e TemplateValue Name="Card" Type="Cardinality".

TON, TOF e CTU vanno serializzati come box IEC nativi, non come call generiche.

PT timer va come TypedConstant di tipo Time; PV CTU come LiteralConstant Int; i pin non usati vanno preferibilmente a OpenCon.

### Composizione canonica

```text
Document
  Engineering version="V20"
  SW.Blocks.FC ID="0"
    AttributeList
      Interface
        Sections xmlns=".../SW/Interface/v5"
          Section Input
          Section Output
          Section InOut
          Section Temp
          Section Constant
          Section Return
      MemoryLayout
      Name
      Namespace
      Number
      ProgrammingLanguage = LAD
      SetENOAutomatically = false
    ObjectList
      MultilingualText Comment
      SW.Blocks.CompileUnit
        AttributeList
          NetworkSource
            FlgNet xmlns=".../SW/NetworkSource/FlgNet/v5"
              Parts
              Wires
          ProgrammingLanguage = LAD
```

### Esempio minimo

```text
<?xml version="1.0" encoding="utf-8"?>
<Document>
  <Engineering version="V20" />
  <SW.Blocks.FC ID="0">
    <AttributeList>
      <Interface><Sections xmlns="http://www.siemens.com/automation/Openness/SW/Interface/v5">
  <Section Name="Input" />
  <Section Name="Output" />
  <Section Name="InOut" />
  <Section Name="Temp">
    <Member Name="Start" Datatype="Bool" />
    <Member Name="m_req" Datatype="Bool" />
  </Section>
  <Section Name="Constant" />
  <Section Name="Return">
    <Member Name="Ret_Val" Datatype="Void" />
  </Section>
</Sections></Interface>
      <MemoryLayout>Optimized</MemoryLayout>
      <Name>fc_3</Name>
      <Namespace />
      <Number>2</Number>
      <ProgrammingLanguage>LAD</ProgrammingLanguage>
      <SetENOAutomatically>false</SetENOAutomatically>
    </AttributeList>
  </SW.Blocks.FC>
</Document>
```

# Parte VIII - Template generator operativo

Questa parte traduce la specifica in contratti di emissione. I placeholder sono pensati per un serializer Python che lavori su IR espliciti.

## Convenzioni

[REQ] = obbligatorio

[OPT] = opzionale

[COND] = obbligatorio solo in certe condizioni

[REP] = ripetibile

[DER] = derivato dal modello o calcolato

```text
Placeholder principali:
{BLOCK_NAME} {BLOCK_NUMBER} {DB_NAME} {DB_NUMBER} {FC_NAME} {FC_NUMBER}
{STEP_NAME} {STEP_NO} {TRANS_NAME} {TRANS_NO}
{INPUT_NAME} {TEMP_NAME} {MEMBER_NAME} {DATATYPE}
{COMMENT_TEXT} {START_VALUE} {UId_N} {TIME_CONST} {DB_SYMBOL} {VAR_SYMBOL}
```

## 1. Contratto del GRAPH compiler

```text
graph_block:
  name
  number
  inputs[]
  outputs[]
  inouts[]
  static_runtime
  steps[]
  transitions[]
  branches[]
  connections[]
  temp_vars[]
  block_comment
```

[REQ] GraphVersion = 2.0

[REQ] Section Base con GRAPH_BASE

[REQ] RT_DATA + runtime transition + runtime step

[COND] Section Temp ed ET_Tx solo se esistono transition temporizzate

[REQ] Steps, Transitions, Branches, Connections

[REQ] Transition LAD solo nel sottoinsieme validato

### Ordine di emissione del GRAPH

```text
1. Document
2. Engineering(version="V20")
3. SW.Blocks.FB(ID="0")
4. AttributeList
5. GraphVersion
6. Interface
7. Base / Input / Output / InOut / Static / Temp / Constant
8. Name / Namespace / Number / ProgrammingLanguage / SetENOAutomatically
9. ObjectList
10. Comment blocco
11. CompileUnit
12. NetworkSource/Graph
13. PreOperations
14. Sequence
15. Steps
16. Transitions
17. Branches
18. Connections
19. PostOperations
```

## 2. Contratto del GlobalDB compiler

```text
global_db:
  name
  number
  memory_layout
  memory_reserve
  block_comment
  block_title
  members[]
```

[REQ] Section Name="Static"

[REQ] serializer ricorsivo e tree-based

[REQ] supporto a scalari, array, struct, IEC_TIMER, IEC_COUNTER

[OPT] AttributeList, Comment, StartValue a livello Member

[COND] Version per tipi IEC versionati

### Funzione ricorsiva canonica

```text
emit_member(m):
    open <Member Name=... Datatype=... [Version=...] [Remanence=...]>

    if m.attributes:
        emit <AttributeList>...</AttributeList>

    if m.comment:
        emit <Comment><MultiLanguageText Lang="en-US">...</MultiLanguageText></Comment>

    if m.start_value exists:
        emit <StartValue>...</StartValue>

    for child in m.children:
        emit_member(child)

    close </Member>
```

## 3. Contratto del FC compiler

```text
fc_block:
  name
  number
  temp_members[]
  compile_units[]
  block_comment
```

[REQ] Interface standard con Return/Ret_Val : Void

[REQ] CompileUnit ordinate

[REQ] FlgNet con Parts e Wires coerenti

[COND] Access LocalVariable o GlobalVariable

[COND] O con TemplateValue Card

[COND] TON/TOF/CTU come box IEC nativi

[REQ] pattern library validata; niente XML LAD libero

### Checklist strutturale minima del backend FC

```text
Document presente
Engineering version="V20" presente
SW.Blocks.FC presente
ProgrammingLanguage = LAD coerente a livello blocco e rete
CompileUnit ordinate
FlgNet con Parts e Wires
UId coerenti
connessioni risolte
nessun pin inesistente
nessun nodo orfano
```

# Parte IX - Pseudo-codice del serializer Python

Lo pseudo-codice seguente non è ancora il codice finale del tool, ma è pensato per essere tradotto quasi direttamente in Python. Presuppone tre IR distinti e una libreria comune di helper XML.

## 1. Strutture IR minime

```text
class GraphIR:
    name: str
    number: int
    inputs: list[VarDecl]
    outputs: list[VarDecl]
    inouts: list[VarDecl]
    temp_vars: list[VarDecl]
    steps: list[StepIR]
    transitions: list[TransitionIR]
    branches: list[BranchIR]
    connections: list[ConnectionIR]
    block_comment: str

class GlobalDBIR:
    name: str
    number: int
    memory_layout: str
    memory_reserve: int | None
    block_comment: str
    block_title: str
    members: list[MemberIR]

class FCIR:
    name: str
    number: int
    temp_members: list[VarDecl]
    compile_units: list[CompileUnitIR]
    block_comment: str
class MemberIR:
    name: str
    datatype: str
    version: str | None
    remanence: str | None
    attributes: list[AttributeIR]
    comment: str | None
    start_value: str | None
    children: list["MemberIR"]

class TransitionIR:
    number: int
    name: str
    flgnet: FlgNetIR
    has_timer: bool
    et_name: str | None
```

## 2. Helper comuni

```text
def el(tag: str, text: str | None = None, attrs: dict | None = None) -> X:
    node = Element(tag)
    if attrs:
        for k, v in attrs.items():
            node.set(k, str(v))
    if text is not None:
        node.text = text
    return node

def append(parent: X, child: X) -> X:
    parent.append(child)
    return child

def sorted_by_name(items):
    return sorted(items, key=lambda x: x.name)

def assert_unique(values, what: str):
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {what}")

def validate_bool_string(value: str):
    if value not in {"true", "false"}:
        raise ValueError("Expected XML bool string")
```

## 3. Validator GRAPH

```text
def validate_graph_ir(g: GraphIR) -> None:
    assert g.name
    assert g.number > 0
    assert len(g.steps) >= 1
    assert len(g.transitions) >= 1

    assert_unique([s.number for s in g.steps], "step numbers")
    assert_unique([t.number for t in g.transitions], "transition numbers")

    init_steps = [s for s in g.steps if s.is_init]
    if len(init_steps) != 1:
        raise ValueError("GRAPH must have exactly one init step")

    for t in g.transitions:
        if t.flgnet is None:
            raise ValueError(f"Transition {t.name} has no FlgNet")
        if not t.flgnet.has_trcoil():
            raise ValueError(f"Transition {t.name} must end with one TrCoil")
        if t.has_timer and not t.et_name:
            raise ValueError(f"Transition {t.name} missing ET temp variable")

    validate_graph_topology(g)

def validate_graph_topology(g: GraphIR) -> None:
    # Implementare qui:
    # - ingressi/uscite consentiti
    # - uso corretto di AltBegin / SimBegin / SimEnd
    # - assenza di doppi ingressi Direct su step non iniziale
    # - coerenza fra nodes e connections
    pass
```

Nota pratica: se uno step non iniziale riceve piu' ingressi, il primo puo' restare
`Direct` mentre gli ingressi aggiuntivi vanno trasformati in link `Jump` per evitare
la violazione "doppi ingressi Direct" e ridurre i rischi di crash in TIA.
Nota operativa import/export: il `targetPath` dei job TIA parte sempre da
`Program blocks/`. Per creare sottocartelle ordinare usare ad esempio
`Program blocks/generati da tool/<nome>`.
Nota sui numeri step: la numerazione GRAPH deve seguire il `step_number` dell'IR.
Il nome del passo e' una label e non deve forzare la numerazione.

## 4. Serializer GRAPH

```text
def emit_graph_fb(g: GraphIR) -> X:
    validate_graph_ir(g)

    doc = el("Document")
    append(doc, el("Engineering", attrs={"version": "V20"}))
    fb = append(doc, el("SW.Blocks.FB", attrs={"ID": "0"}))

    attr = append(fb, el("AttributeList"))
    append(attr, el("GraphVersion", "2.0"))
    append(attr, emit_graph_interface(g))
    append(attr, el("Name", g.name))
    append(attr, el("Namespace", ""))
    append(attr, el("Number", str(g.number)))
    append(attr, el("ProgrammingLanguage", "GRAPH"))
    append(attr, el("SetENOAutomatically", "false"))

    obj = append(fb, el("ObjectList"))
    append(obj, emit_block_comment(comment_id=1, item_id=2, text=g.block_comment))
    append(obj, emit_graph_compile_unit(g, cu_id=3))

    return doc
def emit_graph_interface(g: GraphIR) -> X:
    interface = el("Interface")
    sections = append(interface, el("Sections", attrs={
        "xmlns": "http://www.siemens.com/automation/Openness/SW/Interface/v5"
    }))

    base = append(sections, el("Section", attrs={"Name": "Base"}))
    base_sections = append(base, el("Sections", attrs={"Datatype": "GRAPH_BASE", "Version": "1.0"}))
    append(base_sections, el("Section", attrs={"Name": "Input"}))
    append(base_sections, el("Section", attrs={"Name": "Output"}))
    append(base_sections, el("Section", attrs={"Name": "InOut"}))
    append(base_sections, el("Section", attrs={"Name": "Static"}))

    sec_in = append(sections, el("Section", attrs={"Name": "Input"}))
    for v in sorted_by_name(g.inputs):
        append(sec_in, emit_simple_member(v))

    append(sections, el("Section", attrs={"Name": "Output"}))
    append(sections, el("Section", attrs={"Name": "InOut"}))

    sec_static = append(sections, el("Section", attrs={"Name": "Static"}))
    append(sec_static, el("Member", attrs={"Name": "RT_DATA", "Datatype": "G7_RTDataPlus_V2", "Version": "1.0"}))
    for t in sorted(g.transitions, key=lambda x: x.number):
        append(sec_static, el("Member", attrs={"Name": t.runtime_name, "Datatype": "G7_TransitionPlus_V2", "Version": "1.0"}))
    for s in sorted(g.steps, key=lambda x: x.number):
        append(sec_static, el("Member", attrs={"Name": s.runtime_name, "Datatype": "G7_StepPlus_V2", "Version": "1.0"}))

    sec_temp = append(sections, el("Section", attrs={"Name": "Temp"}))
    for t in sorted(g.transitions, key=lambda x: x.number):
        if t.has_timer:
            append(sec_temp, el("Member", attrs={"Name": t.et_name, "Datatype": "Time"}))

    append(sections, el("Section", attrs={"Name": "Constant"}))
    return interface
def emit_graph_compile_unit(g: GraphIR, cu_id: int) -> X:
    cu = el("SW.Blocks.CompileUnit", attrs={"ID": str(cu_id), "CompositionName": "CompileUnits"})
    attr = append(cu, el("AttributeList"))
    ns = append(attr, el("NetworkSource"))
    graph = append(ns, el("Graph", attrs={
        "xmlns": "http://www.siemens.com/automation/Openness/SW/NetworkSource/Graph/v5"
    }))

    pre = append(graph, el("PreOperations"))
    append(pre, el("PermanentOperation", attrs={"ProgrammingLanguage": "LAD"}))

    seq = append(graph, el("Sequence"))
    append(seq, el("Title"))
    c = append(seq, el("Comment"))
    append(c, el("MultiLanguageText", attrs={"Lang": "en-US"}))

    steps = append(seq, el("Steps"))
    for s in sorted(g.steps, key=lambda x: x.number):
        append(steps, emit_graph_step(s))

    transitions = append(seq, el("Transitions"))
    for t in sorted(g.transitions, key=lambda x: x.number):
        append(transitions, emit_graph_transition(t))

    branches = append(seq, el("Branches"))
    for b in g.branches:
        append(branches, emit_graph_branch(b))

    connections = append(seq, el("Connections"))
    for c in g.connections:
        append(connections, emit_graph_connection(c))

    post = append(graph, el("PostOperations"))
    append(post, el("PermanentOperation", attrs={"ProgrammingLanguage": "LAD"}))

    append(attr, el("ProgrammingLanguage", "GRAPH"))
    return cu
```

## 5. Validator e serializer GlobalDB

```text
def validate_db_ir(db: GlobalDBIR) -> None:
    assert db.name
    assert db.number > 0
    if not db.members:
        raise ValueError("GlobalDB must contain at least one member")

def emit_global_db(db: GlobalDBIR) -> X:
    validate_db_ir(db)

    doc = el("Document")
    append(doc, el("Engineering", attrs={"version": "V20"}))
    gdb = append(doc, el("SW.Blocks.GlobalDB", attrs={"ID": "0"}))

    attr = append(gdb, el("AttributeList"))
    append(attr, emit_db_interface(db))
    append(attr, el("MemoryLayout", db.memory_layout or "Optimized"))
    if db.memory_reserve is not None:
        append(attr, el("MemoryReserve", str(db.memory_reserve)))
    append(attr, el("Name", db.name))
    append(attr, el("Namespace", ""))
    append(attr, el("Number", str(db.number)))
    append(attr, el("ProgrammingLanguage", "DB"))

    obj = append(gdb, el("ObjectList"))
    append(obj, emit_block_comment(comment_id=1, item_id=2, text=db.block_comment))
    append(obj, emit_block_title(title_id=3, item_id=4, text=db.block_title))
    return doc
def emit_db_interface(db: GlobalDBIR) -> X:
    interface = el("Interface")
    sections = append(interface, el("Sections", attrs={
        "xmlns": "http://www.siemens.com/automation/Openness/SW/Interface/v5"
    }))
    sec_static = append(sections, el("Section", attrs={"Name": "Static"}))
    for m in db.members:
        append(sec_static, emit_member(m))
    return interface

def emit_member(m: MemberIR) -> X:
    attrs = {"Name": m.name, "Datatype": m.datatype}
    if m.version:
        attrs["Version"] = m.version
    if m.remanence:
        attrs["Remanence"] = m.remanence

    node = el("Member", attrs=attrs)

    if m.attributes:
        attr = append(node, el("AttributeList"))
        for a in m.attributes:
            append(attr, emit_attribute(a))

    if m.comment:
        c = append(node, el("Comment"))
        append(c, el("MultiLanguageText", m.comment, attrs={"Lang": "en-US"}))

    if m.start_value is not None:
        append(node, el("StartValue", m.start_value))

    for child in m.children:
        append(node, emit_member(child))

    return node
```

## 6. Validator e serializer FC

```text
def validate_fc_ir(fc: FCIR) -> None:
    assert fc.name
    assert fc.number > 0
    if not fc.compile_units:
        raise ValueError("FC must contain at least one CompileUnit")

    seen = set()
    for cu in fc.compile_units:
        if cu.id in seen:
            raise ValueError("Duplicate CompileUnit id")
        seen.add(cu.id)
        validate_flgnet(cu.flgnet)

def validate_flgnet(net: FlgNetIR) -> None:
    if not net.parts:
        raise ValueError("FlgNet without parts")
    if not net.wires:
        raise ValueError("FlgNet without wires")
    # Qui aggiungere:
    # - controllo UId univoci
    # - controllo endpoint esistenti
    # - nessun pin inesistente
    # - nessun nodo orfano
def emit_fc_lad(fc: FCIR) -> X:
    validate_fc_ir(fc)

    doc = el("Document")
    append(doc, el("Engineering", attrs={"version": "V20"}))
    block = append(doc, el("SW.Blocks.FC", attrs={"ID": "0"}))

    attr = append(block, el("AttributeList"))
    append(attr, el("AutoNumber", "false"))
    append(attr, emit_fc_interface(fc))
    append(attr, el("MemoryLayout", "Optimized"))
    append(attr, el("Name", fc.name))
    append(attr, el("Namespace", ""))
    append(attr, el("Number", str(fc.number)))
    append(attr, el("ProgrammingLanguage", "LAD"))
    append(attr, el("SetENOAutomatically", "false"))

    obj = append(block, el("ObjectList"))
    append(obj, emit_block_comment(comment_id=1, item_id=2, text=fc.block_comment))
    for cu in fc.compile_units:
        append(obj, emit_fc_compile_unit(cu))

    return doc
def emit_fc_interface(fc: FCIR) -> X:
    interface = el("Interface")
    sections = append(interface, el("Sections", attrs={
        "xmlns": "http://www.siemens.com/automation/Openness/SW/Interface/v5"
    }))
    append(sections, el("Section", attrs={"Name": "Input"}))
    append(sections, el("Section", attrs={"Name": "Output"}))
    append(sections, el("Section", attrs={"Name": "InOut"}))

    sec_temp = append(sections, el("Section", attrs={"Name": "Temp"}))
    for v in fc.temp_members:
        append(sec_temp, emit_simple_member(v))

    append(sections, el("Section", attrs={"Name": "Constant"}))
    sec_ret = append(sections, el("Section", attrs={"Name": "Return"}))
    append(sec_ret, el("Member", attrs={"Name": "Ret_Val", "Datatype": "Void"}))
    return interface
def emit_fc_compile_unit(cu: CompileUnitIR) -> X:
    node = el("SW.Blocks.CompileUnit", attrs={"ID": str(cu.id), "CompositionName": "CompileUnits"})
    attr = append(node, el("AttributeList"))
    ns = append(attr, el("NetworkSource"))
    flgnet = append(ns, el("FlgNet", attrs={
        "xmlns": "http://www.siemens.com/automation/Openness/SW/NetworkSource/FlgNet/v5"
    }))

    parts = append(flgnet, el("Parts"))
    for p in cu.flgnet.parts:
        append(parts, emit_part_or_access(p))

    wires = append(flgnet, el("Wires"))
    for w in cu.flgnet.wires:
        append(wires, emit_wire(w))

    append(attr, el("ProgrammingLanguage", "LAD"))
    return node
```

## 7. Emettitori di nodi LAD

```text
def emit_part_or_access(node):
    if node.kind == "access":
        access = el("Access", attrs={"Scope": node.scope, "UId": str(node.uid)})
        sym = append(access, el("Symbol"))
        for comp in node.symbol_components:
            append(sym, el("Component", attrs={"Name": comp}))
        return access

    if node.kind == "part":
        part = el("Part", attrs={"Name": node.name, "UId": str(node.uid)})
        if node.version:
            part.set("Version", node.version)
        for tv in node.template_values:
            append(part, el("TemplateValue", tv.value, attrs={"Name": tv.name, "Type": tv.type}))
        if node.instance:
            inst = append(part, el("Instance", attrs={"Scope": node.instance.scope, "UId": str(node.instance.uid)}))
            append(inst, el("Component", attrs={"Name": node.instance.component}))
        return part

    raise ValueError("Unknown node type")
def emit_wire(w: WireIR) -> X:
    wire = el("Wire", attrs={"UId": str(w.uid)})
    for ep in w.endpoints:
        if ep.kind == "powerrail":
            append(wire, el("Powerrail"))
        elif ep.kind == "ident":
            append(wire, el("IdentCon", attrs={"UId": str(ep.uid)}))
        elif ep.kind == "name":
            append(wire, el("NameCon", attrs={"UId": str(ep.uid), "Name": ep.name}))
        elif ep.kind == "open":
            append(wire, el("OpenCon", attrs={"UId": str(ep.uid)}))
        else:
            raise ValueError("Unknown endpoint kind")
    return wire
```

## 8. Helper documentali comuni

```text
def emit_block_comment(comment_id: int, item_id: int, text: str) -> X:
    mt = el("MultilingualText", attrs={"ID": str(comment_id), "CompositionName": "Comment"})
    obj = append(mt, el("ObjectList"))
    item = append(obj, el("MultilingualTextItem", attrs={"ID": str(item_id), "CompositionName": "Items"}))
    attr = append(item, el("AttributeList"))
    append(attr, el("Culture", "en-US"))
    append(attr, el("Text", text or ""))
    return mt

def emit_block_title(title_id: int, item_id: int, text: str) -> X:
    mt = el("MultilingualText", attrs={"ID": str(title_id), "CompositionName": "Title"})
    obj = append(mt, el("ObjectList"))
    item = append(obj, el("MultilingualTextItem", attrs={"ID": str(item_id), "CompositionName": "Items"}))
    attr = append(item, el("AttributeList"))
    append(attr, el("Culture", "en-US"))
    append(attr, el("Text", text or ""))
    return mt

def emit_simple_member(v: VarDecl) -> X:
    return el("Member", attrs={"Name": v.name, "Datatype": v.datatype})
```

## 9. Pipeline complessiva consigliata

```text
AWL
 -> parser
 -> estrazione macchina a stati + pattern
 -> IR sequenza
 -> IR dati
 -> IR reti
 -> validator GRAPH / DB / FC
 -> emit_graph_fb()
 -> emit_global_db()
 -> emit_fc_lad()
 -> export XML
 -> import TIA
 -> compile
 -> export regressione
```

Nota operativa di orchestrazione:

- nel workflow mediato da `tia-bridge`, `import` e `compile` sono operazioni esplicite e separate;
- il tracciamento end-to-end deve considerare i due `JobId` distinti (import e compile), senza dipendere da compile automatica post-import.

Nota operativa Excel FC (consolidata al 22-04-2026):

- i tag con `datatype=IEC_TIMER` e `control_kind` coerente (`t_on`, `t_off`, `t_p`) devono generare blocchi LAD timer completi con `PT` derivato da `control_value`;
- i tag con `datatype=IEC_COUNTER` e `control_kind` coerente (`ctu`, `ctd`, `ctud`) devono generare blocchi LAD contatore completi con `PV` derivato da `control_value`;
- i pin obbligatori non valorizzati nel foglio Excel devono essere cablati con default sicuro per garantire import robusto su TIA.

## 10. Regole finali da non violare

Mai derivare regole del generatore da un singolo test isolato.

I file esempio validati sono oracoli di regressione, non il generatore.

Il backend GRAPH deve restare pattern-driven e validator-driven.

Il backend GlobalDB deve restare un serializer ricorsivo generale con grammatica fissa.

Il backend FC deve emettere solo pattern LAD già convalidati e combinazioni autorizzate.

# Appendice A - Integrazioni consolidate dal caso `AWL Romania / FC102`

## A.1 Regola sul backbone automatico ricorrente

Nel caso FC102 il parsing dell'AWL rende leggibile una catena automatica ricorrente della forma:

`S01 -> S02 -> S03 -> S04 -> S07 -> S10 -> S14 -> S18 -> S22 -> S26 -> S03`

con rami separati verso `S29` e `S32`.

Questa catena va trattata come pattern forte del sorgente. In particolare, i passi `1, 2, 3, 4, 7` sono da considerare parte ricorrente dell'ossatura automatica del caso d'uso.

## A.2 Regola di distinzione tra step e stato fisico

Segnali come `UP`, `DOWN`, `STC` e feedback equivalenti non sono step GRAPH finali.

Essi vanno classificati come:

- feedback fisici filtrati;
- memorie semantiche di stato;
- consensi di transizione o di start ciclo.

Il convertitore non deve quindi creare step GRAPH a partire da questi segnali, ma allocarli come memorie o condizioni nel modello target.

## A.3 Regola sui timeout di dispositivo e sui preset di sequenza

Il convertitore deve distinguere due famiglie di temporizzazioni:

1. timeout di dispositivo/movimento che generano diagnostica o fault;
2. preset temporali della sequenza che modificano il comportamento del passo.

Le due famiglie non devono essere fuse né serializzate nello stesso ruolo semantico.

## A.4 Regola sulle uscite come formule target

La formula di una uscita target deve essere costruita come combinazione di:

- step automatici attivi;
- comandi manuali;
- interblocchi;
- consensi permanenti;
- lock o fault;
- eventuali stati fisici già elaborati.

Il backend `FC 06 Output` è quindi un compilatore semantico di formule, non un trascrittore diretto di bobine sorgenti.

## A.5 Regola sui fault e sull'emergenza

I dettagli dei fault e dei bit allarme devono rimanere nel livello diagnostico sorgente o nei DB fissi di progetto.

La sequenza target deve consumare invece cumulativi semantici, ad esempio `Fault` ed `Emergency`, agganciati ai rami di sicurezza del modello.

## A.6 Regola sul rientro da manuale ed emergenza

La logica di rientro da manuale/emergenza verso il passo iniziale (numero `1`) va trattata come regola strutturale del convertitore.

Non è una semplice transizione locale, ma parte del backbone fisso di sequenza.

## A.7 Regola sulla policy di naming del GRAPH

L'identità logica del passo sorgente AWL va estratta in modo deterministico.

Il naming finale dei passi GRAPH resta invece una policy del builder, che può:

- mantenere il numero storico;
- assegnare un nome semantico più leggibile;
- introdurre step di chiusura o fine ciclo, purché il comportamento funzionale resti equivalente.


# Appendice B - Integrazioni consolidate al 21-04-2026

## B.1 Regola di prevalenza normativa
In caso di conflitto tra una convenzione di repository, un'abitudine storica del team o una semplificazione implementativa del tool, prevale sempre la presente specifica.

## B.2 Regola hard sul naming globale completo
Il generatore non puo' considerare sufficiente un nome finale corretto se mancano owner DB e path completo del simbolo.

Il record minimo di una variabile globale serializzabile deve sempre consentire di ricostruire:
- DB proprietario;
- path dei branch intermedi;
- leaf finale;
- forma finale del riferimento XML nel `FlgNet`.

Un riferimento abbreviato, orfano o ricostruito per euristica tardiva e' da considerare errore bloccante.

## B.3 Regola sull'uso dei tipici legacy
I tipici `V6` o di altra famiglia runtime possono essere usati per:
- riconoscimento semantico della sequenza;
- topologia del GRAPH;
- naming storico di rami e campi;
- confronto diagnostico.

Non possono invece imporre al serializer finale:
- `GraphVersion` legacy;
- datatype runtime legacy;
- wrapper XML incompatibili con il target `V20 / GRAPH V2`.

## B.4 Regola di segmentazione AWL ricorrente
Quando il sorgente AWL e' monolitico, il parser deve cercare esplicitamente almeno le seguenti famiglie:
- allarmi;
- memorie e ausiliari;
- sequenza principale;
- gestione manuale/automatico;
- emergenza e fault;
- uscite macchina.

La presenza di tali famiglie non implica un ordine testuale fisso, ma impone una classificazione semantica nell'IR.

## B.5 Regola di gate prima dell'import TIA
Prima dell'import il bundle deve superare almeno i seguenti controlli:
- target `GraphVersion = 2.0`;
- datatype runtime della famiglia `..._V2`;
- cardinalita' `1 x FB GRAPH + N x GlobalDB + M x FC LAD`;
- naming globale completo e coerente;
- topologia GRAPH valida;
- separazione corretta fra semantica del corpus legacy e serializer finale target.

## B.6 Regola di lettura del corpus reale rispetto al target
I file XML reali del corpus devono essere letti su due livelli distinti:
- come fonte di verita' per pattern di naming globale, path simbolici, organizzazione LAD e famiglie funzionali realmente usate;
- come fonte non vincolante per il runtime GRAPH finale quando appartengono a famiglie legacy come `V6`.

Il convertitore deve quindi imparare dal corpus reale senza riprodurne automaticamente gli elementi incompatibili con `TIA Portal V20 / GRAPH V2`.

## B.7 Regola esplicita sul modello HMI
Il modello HMI target non coincide con il solo insieme delle condizioni booleane elementari `nX`.

Per ogni gruppo HMI il convertitore deve poter rappresentare almeno due livelli:
- condizioni elementari serializzabili nel ramo `Conditions.<gruppo>.Conditions.nX`;
- campi di stato o metadati di gruppo, come numero popup, visibilita', esito aggregato delle condizioni, first-out o equivalenti del modello adottato.

Questa distinzione e' obbligatoria sia nell'IR sia nel serializer dei DB e delle FC di supporto.
