# Report aggiornato del 30-03-2026

## Progetto
Conversione di sequenziatori PLC da AWL a GRAPH in TIA Portal V20 tramite XML.

---

## 1. Scopo del report

Questo report consolida lo stato tecnico del progetto dopo:

- l'analisi sistematica dei file `Type_*.xml` come corpus di riferimento GRAPH;
- la validazione pratica delle regole strutturali che rendono un GRAPH importabile in TIA Portal V20;
- l'analisi del file `db_1.xml` come tipico di `GlobalDB`;
- la generazione e importazione riuscita di un `GlobalDB` di prova con commenti visibili in TIA;
- la nuova analisi approfondita del file `fc_1.xml` come tipico di `SW.Blocks.FC` in LAD;
- la generazione, correzione strutturale e importazione riuscita del nuovo blocco GRAPH completo di linea imbottigliamento, con file finale validato `FB_BottlingLine_GRAPH_strict_rebased.xml`.
- la correzione strutturale e importazione riuscita del nuovo blocco GRAPH `FB_GateCycle_GRAPH_v3_rebased.xml`, ottenuta con riallineamento del wrapper esterno del blocco senza alterare la logica del graph interno.

Il documento fissa quindi tre famiglie di regole ormai separate e complementari:

1. **regole per generare il blocco GRAPH XML**;
2. **regole per generare un DB XML separato da affiancare al GRAPH**;
3. **regole per generare un blocco `FC` XML in LAD**.

---

## 2. Obiettivo generale del progetto

L'obiettivo generale rimane definire un metodo affidabile per tradurre sequenziatori complessi sviluppati in AWL in implementazioni equivalenti GRAPH per TIA Portal V20, usando XML come formato intermedio.

Le due direttrici del progetto restano:

### 2.1 Traduzione assistita con ChatGPT
- analisi del codice AWL;
- riconoscimento della logica sequenziale implicita;
- proposta della struttura GRAPH equivalente;
- supporto alla generazione dell'XML;
- supporto alla definizione del DB esterno associato.

### 2.2 Sviluppo di un tool deterministico
- parser del codice AWL;
- estrazione formale della macchina a stati;
- mappatura verso un modello GRAPH;
- generazione automatica di XML compatibile con TIA Portal V20;
- generazione automatica del `GlobalDB` companion.

### 2.3 Automazione di import/export XML tramite TIA Openness
- apertura o connessione automatica a un'istanza TIA Portal;
- apertura o creazione automatica del progetto di destinazione;
- import automatico degli XML generati (`FB` GRAPH, `GlobalDB`, eventuali `FC`) nel progetto TIA;
- export automatico da TIA degli XML/strutture utili come baseline di reverse engineering, regressione e confronto;
- eventuale compilazione e validazione post-import con raccolta degli esiti;
- integrazione del ciclo end-to-end `generazione -> import -> validazione -> export -> confronto` con minimo intervento manuale.

Questa direttrice estende il progetto dal solo livello di generazione XML al livello di orchestrazione completa del ciclo tecnico. Nel materiale Openness disponibile risultano infatti presenti funzioni per aprire o collegarsi a TIA Portal, creare/aprire/salvare progetti e usare funzioni di import/export e gestione sorgenti PLC; nel progetto corrente queste capacità vanno assunte come base architetturale da adattare e verificare sul target TIA Portal V20.

---

## 3. Target tecnico validato

Il target effettivamente consolidato nel progetto è:

- **TIA Portal V20**;
- **GRAPH V2**;
- datatype della famiglia `..._V2` per il runtime GRAPH;
- XML in stile Openness/TIA importabile senza correzioni manuali strutturali;
- blocchi di tipo:
  - `SW.Blocks.FB` per il GRAPH;
  - `SW.Blocks.GlobalDB` per il DB separato;
  - `SW.Blocks.FC` per logiche LAD di orchestrazione o servizio.

---

## 4. Problema tecnico reale

Il problema non è soltanto “scrivere XML corretto”, ma trasformare una logica AWL implicita in due artefatti coerenti:

1. **un GRAPH esplicito, topologicamente valido e importabile**;
2. **un DB esterno pulito e manutenibile**, usato per comandi, feedback, parametri, diagnostica, mapping e integrazione impianto.

I sequenziatori AWL implementano spesso la sequenza in modo implicito tramite:

- bit di stato;
- reti di set/reset;
- latch;
- salti condizionati;
- timer;
- catene di abilitazione;
- combinazioni automatico/manuale/allarmi;
- interblocchi distribuiti;
- logiche di consenso sparse.

GRAPH richiede invece una struttura esplicita fatta di:

- step;
- transition;
- branch;
- connessioni;
- eventuali paralleli;
- eventuali chiusure di sequenza.

Il DB separato richiede a sua volta una struttura dati esplicita, non deducibile dal GRAPH runtime interno Siemens.

---

## 5. Scoperta architetturale decisiva

La decisione più importante emersa nei test recenti è la seguente:

### 5.1 Esistono due livelli distinti di dati

#### A. Dati interni obbligatori del blocco GRAPH
Sono parte dell'`FB` GRAPH e servono a rendere il blocco importabile e coerente con il runtime atteso da TIA.

In particolare, nella sezione `Static` del GRAPH devono comparire almeno:

- `RT_DATA : G7_RTDataPlus_V2`;
- un member `G7_TransitionPlus_V2` per ogni transition;
- un member `G7_StepPlus_V2` per ogni step.

Questi dati **non vanno sostituiti** con un DB esterno.

#### B. Dati applicativi esterni del sequenziatore
Sono i dati che ha senso mettere in un `GlobalDB` separato, ad esempio:

- comandi macchina;
- feedback sensori/attuatori;
- parametri ricetta;
- abilitazioni;
- diagnostica;
- dati HMI;
- mapping AWL -> GRAPH;
- eventuali dati di supporto al sequenziatore.

### 5.2 Conseguenza progettuale

La regola corretta non è:

> genero un DB separato e al suo posto elimino gli statici del GRAPH.

La regola corretta è:

> genero il GRAPH con i suoi statici interni obbligatori **e inoltre** genero un `GlobalDB` companion separato.

Questa separazione è ormai da considerare consolidata.

---

# PARTE A - REGOLE CONSOLIDATE PER IL GRAPH XML

---

## 6. Livello hard e livello soft nel GRAPH

La scoperta più importante emersa dai test sui file `Type_*.xml` è questa:

**TIA decide l'importabilità soprattutto dalla grammatica strutturale del GRAPH e dalla forma delle transition, non dalla precisione assoluta dei metadati runtime che spesso ricalcola.**

### 6.1 Livello hard
Elementi che influenzano realmente l'import:

- namespace;
- struttura del documento;
- `Interface`;
- `Static`;
- `RT_DATA`;
- member step/transition;
- `Steps`;
- `Transitions`;
- `Branches`;
- `Connections`;
- topologia del graph;
- struttura del `FlgNet` delle transition.

### 6.2 Livello soft
Elementi spesso tollerati o ricalcolati da TIA:

- `S_CNT`;
- `T_CNT`;
- `SQ_PART_CNT`;
- `MAX_TVAL`;
- `MAX_SACT`;
- offsets runtime;
- altri dati interni derivati.

---

## 7. Specifica validata XML GRAPH V2 per TIA Portal V20

### 7.1 Struttura generale del documento
La struttura valida è:

- `Document`
  - `Engineering`
  - eventuale `DocumentInfo` o struttura minima equivalente;
  - `SW.Blocks.FB`
    - `AttributeList`
    - `ObjectList` e/o blocchi compilati coerenti;
    - `SW.Blocks.CompileUnit` contenente il GRAPH.

### 7.2 Namespace
Regole hard validate:

- root `Document` senza prefissi tipo `ns0:`;
- namespace `Interface` dichiarato localmente;
- namespace `Graph` dichiarato localmente;
- evitare serializzazioni aggressive dei namespace sulla root.

### 7.3 AttributeList del blocco GRAPH
Attributi da mantenere coerenti:

- `GraphVersion = 2.0`;
- nome blocco coerente;
- numero blocco coerente;
- struttura `FB` corretta.

### 7.4 Interface
La `Interface` deve avere sezioni bilanciate.

Sezioni tipiche:

- `Input`;
- `Output`;
- `InOut`;
- `Static`;
- `Temp`;
- `Constant`.

La sezione cruciale per GRAPH è `Static`.

### 7.5 Sezione Static del GRAPH
Dentro `Static` devono esistere almeno tre famiglie di member:

1. `RT_DATA`;
2. un member per ogni transition;
3. un member per ogni step.

### 7.6 RT_DATA
Datatype hard consolidato:

- `G7_RTDataPlus_V2`

Il contenuto numerico deve essere plausibile, ma non è il vincolo principale di importabilità.

### 7.7 Member statici delle transition
Per ogni transition del graph deve esistere un member statico:

- datatype `G7_TransitionPlus_V2`;
- campo `TNO` coerente con il numero della transition.

### 7.8 Member statici degli step
Per ogni step del graph deve esistere un member statico:

- datatype `G7_StepPlus_V2`;
- campo `SNO` coerente con il numero dello step.

Campi tipici osservati:

- `SNO`;
- `T_MAX`;
- `T_WARN`;
- `H_SV_FLT`.

---

## 8. Specifica topologica del GRAPH

La `Sequence` contiene i quattro blocchi fondamentali:

- `Steps`;
- `Transitions`;
- `Branches`;
- `Connections`.

### 8.1 Step
Ogni step ha tipicamente:

- `Number`;
- `Init`;
- `Name`;
- `MaximumStepTime`;
- `WarningTime`;
- `Actions`;
- `Supervisions`;
- `Interlocks`.

Regole hard:

- uno e un solo step iniziale con `Init="true"`;
- tutti gli altri con `Init="false"`.

### 8.2 Transition
Ogni transition ha tipicamente:

- `IsMissing`;
- `Name`;
- `Number`;
- `ProgrammingLanguage="LAD"`;
- `FlgNet`
  - `Parts`
  - `Wires`

Regole hard:

- numero univoco;
- `ProgrammingLanguage = LAD`;
- member statico coerente;
- `FlgNet` valido.

### 8.3 Branch
Tipi osservati e validati:

- `AltBegin`;
- `SimBegin`;
- `SimEnd`.

Uso corretto:

- `AltBegin` per alternative;
- `SimBegin` e `SimEnd` per paralleli.

### 8.4 Connections
Ogni connessione è composta da:

- `NodeFrom`;
- `NodeTo`;
- `LinkType`.

Riferimenti osservati:

- `StepRef`;
- `TransitionRef`;
- `BranchRef`;
- `EndConnection`.

Valori `LinkType` validati:

- `Direct`;
- `Jump`.

---

## 9. Regole topologiche hard emerse dai test

### 9.1 Uno step ha una sola uscita diretta
Uno step può uscire con `Direct` solo verso:

- una transition;
- un branch.

Non deve avere:

- due uscite dirette;
- collegamenti step -> step;
- salti diretti non mediati.

### 9.2 Una transition ha una sola uscita
Una transition deve uscire verso:

- uno step;
- un branch;
- un `EndConnection`.

### 9.3 Uno step non iniziale non deve ricevere due ingressi `Direct`
Se più rami devono confluire sullo stesso step:

- uno solo entra `Direct`;
- gli altri entrano con `Jump`.

### 9.4 Le alternative si fanno sempre con `AltBegin`
Forma corretta:

- step -> `AltBegin`;
- `AltBegin` -> transition dei rami.

### 9.5 I paralleli si fanno sempre con `SimBegin` / `SimEnd`
Forma corretta:

- transition -> `SimBegin`;
- `SimBegin` -> step dei rami;
- rami -> `SimEnd`;
- `SimEnd` -> transition di uscita.

### 9.6 Gli allarmi e i rami terminali devono chiudersi
Pattern validato:

- step di allarme;
- transition finale;
- `EndConnection`.

---

## 10. Transition LAD: problema reale e sottoinsieme sicuro

La parte più fragile del progetto si è dimostrata la generazione del LAD nelle transition.

### 10.1 Errore reale osservato
Una transition logicamente corretta può comunque non importare se la topologia XML del `FlgNet` non segue il sottoinsieme accettato da TIA.

Sono risultati problematici:

- uso improprio di `Part Name="A"` come convergenza finale;
- composizioni ibride non allineate ai pattern validati;
- reti con ricombinazioni fuori profilo.

### 10.2 Sottoinsieme LAD sicuro consolidato
Il sottoinsieme affidabile è basato su:

- `Access`;
- `Contact`;
- `Contact` negato;
- `O`;
- comparatori già validati, ad esempio `Gt`;
- `TrCoil`.

Regole operative:

- `AND` = serie;
- `OR` = nodo `O`;
- `NOT` = contatto negato;
- una sola `TrCoil` finale;
- evitare `A` finché non esiste un caso validato che lo renda necessario.

### 10.3 Pattern validati
Pattern minimo valido:

- `Powerrail -> TrCoil`

Pattern semplice valido:

- `Access -> Contact -> TrCoil`

Pattern composto valido:

- contatto iniziale;
- due rami o più tramite `O`;
- eventuale confronto come `Gt(Time > T#5S)`;
- `TrCoil` finale.

---

## 11. Strategia corretta per il tool GRAPH

Il tool non deve essere template-based nel senso di copiare e modificare file XML esistenti.

Deve essere:

- model-based;
- grammar-driven;
- constraint-driven;
- deterministico.

I file validi servono come:

- corpus di reverse engineering;
- golden reference;
- suite di regressione;
- base di validazione.

---

## 12. Architettura raccomandata del compilatore GRAPH

Pipeline concettuale:

`AWL -> parser -> estrazione macchina a stati -> IR -> normalizzazione logica -> validazione GRAPH -> compilatore transition -> serializer XML -> validator finale`

Componenti principali:

1. parser AWL;
2. estrattore della macchina a stati;
3. IR del sequenziatore;
4. normalizzatore booleano;
5. compilatore GRAPH;
6. compilatore `FlgNet` delle transition;
7. serializer XML;
8. validator strutturale.

### 12.1 AST booleano minimo consigliato
Tipi consigliati:

- `Var`;
- `Not`;
- `And`;
- `Or`;
- `Compare`.

### 12.2 Normalizzazione
Prima della serializzazione in LAD:

- flatten degli `AND`;
- flatten degli `OR`;
- eliminazione dei doppi `NOT`;
- ordinamento stabile opzionale;
- costruzione di una forma serializzabile.

### 12.3 Validator della transition
Controlli necessari:

- una sola `TrCoil`;
- almeno un percorso dal powerrail alla coil;
- nessun nodo orfano;
- nessun `A`;
- cardinalità coerente degli `O`;
- collegamenti operand corretti;
- rete interamente connessa.

---

# PARTE B - REGOLE CONSOLIDATE PER IL GLOBALDB SEPARATO

---

## 13. Nuovo obiettivo specifico del progetto

Oltre alla generazione del GRAPH, il progetto richiede ora la capacità di generare un **DB separato** da affiancare al GRAPH corretto.

Questo DB deve essere:

- importabile in TIA Portal V20;
- indipendente dal runtime interno GRAPH;
- pulito dal punto di vista manutentivo;
- generabile in modo deterministico;
- adatto a contenere dati applicativi del sequenziatore.

---

## 14. Riferimento di base per il DB: `db_1.xml`

Il file `db_1.xml` va interpretato come **tipico di serializzazione di un `SW.Blocks.GlobalDB`**, non come runtime GRAPH.

Ciò che fornisce è una grammatica minima e valida del DB XML TIA.

### 14.1 Struttura generale del `GlobalDB`
La struttura valida osservata è:

- `Document`
  - `Engineering version="V20"`
  - `SW.Blocks.GlobalDB`
    - `AttributeList`
      - `Interface`
        - `Sections`
          - `Section Name="Static"`
            - `Member...`
      - `MemoryLayout`
      - `MemoryReserve`
      - `Name`
      - `Namespace`
      - `Number`
      - `ProgrammingLanguage`
    - `ObjectList`
      - `MultilingualText` per `Comment`
      - `MultilingualText` per `Title`

### 14.2 Regole hard per il `GlobalDB`
Le regole ormai consolidate sono:

- root `Document` senza `ns0:`;
- `Engineering version="V20"`;
- blocco di tipo `SW.Blocks.GlobalDB`;
- `ProgrammingLanguage = DB`;
- `Interface/Sections/Section Name="Static"` presente;
- namespace `http://www.siemens.com/automation/Openness/SW/Interface/v5` dichiarato localmente su `Sections`;
- `MemoryLayout` valorizzato;
- `Name` e `Number` coerenti;
- `ObjectList` presente con `Comment` e `Title` del blocco.

### 14.3 Regole soft per il `GlobalDB`
Elementi modificabili purché coerenti:

- `MemoryReserve`;
- naming delle variabili;
- presenza o meno di attributi opzionali sui `Member`;
- presenza di `StartValue` quando applicabile;
- organizzazione logica dei campi.

---

## 15. Scoperta fondamentale sul DB separato

La regola più importante emersa dall'analisi è:

**il `GlobalDB` va generato come serializer ricorsivo di `Member`, non come copia di un XML campione.**

In altre parole:

- `db_1.xml` serve per fissare la grammatica;
- il contenuto del DB deve essere generato da un IR;
- il tool deve sapere serializzare member semplici, array, struct, tipi versionati, attributi e commenti.

---

## 16. Tipi di `Member` da supportare nel serializer DB

Dal tipico `db_1.xml` e dai test successivi risulta che il serializer deve supportare almeno queste classi di member.

### 16.1 Scalare semplice
Esempi:

- `Bool`
- `Int`
- `Real`

Forma minima:

```xml
<Member Name="var_x" Datatype="Bool" />
```

### 16.2 Scalare con `AttributeList`
Esempio:

```xml
<Member Name="var_x" Datatype="Int">
  <AttributeList>
    <BooleanAttribute Name="ExternalAccessible" SystemDefined="true">false</BooleanAttribute>
  </AttributeList>
</Member>
```

### 16.3 Array
Esempio:

```xml
<Member Name="var_x" Datatype="Array[0..9] of Bool" />
```

### 16.4 Member con `Remanence`
Esempio:

```xml
<Member Name="var_x" Datatype="Array[0..9] of Bool" Remanence="Retain" />
```

### 16.5 `Struct` ricorsiva
Esempio:

```xml
<Member Name="my_struct" Datatype="Struct">
  <Member Name="field_1" Datatype="Bool" />
  <Member Name="field_2" Datatype="Int" />
</Member>
```

### 16.6 Tipo speciale versionato
Esempi osservati:

- `IEC_COUNTER Version="1.0"`
- `IEC_TIMER Version="1.0"`

Esempio:

```xml
<Member Name="timer_01" Datatype="IEC_TIMER" Version="1.0" />
```

---

## 17. Regola di serializzazione ricorsiva dei `Member`

Questa regola è ormai da considerare definitiva.

### 17.1 Modello logico del `Member`
Ogni `Member` del DB deve poter essere descritto da un modello con i campi:

- `name`
- `datatype`
- `version?`
- `remanence?`
- `attributes?`
- `comment?`
- `start_value?`
- `children?`

### 17.2 Regola di emissione
Per ogni `Member`:

1. aprire il tag con `Name` e `Datatype`;
2. aggiungere eventuali attributi inline come `Version` e `Remanence`;
3. emettere eventuale `AttributeList`;
4. emettere eventuale `Comment` del campo;
5. emettere eventuale `StartValue`;
6. se il datatype è `Struct`, serializzare ricorsivamente i figli `Member`;
7. chiudere il tag.

### 17.3 Conseguenza progettuale
Il generatore DB deve essere **tree-based**, non string-based.

---

## 18. Regola validata sui commenti visibili in TIA

Questa è una delle novità più importanti emerse dai test pratici.

### 18.1 Obiettivo
Si voleva ottenere non solo un DB importabile, ma un DB in cui i commenti dei singoli campi risultassero **visibili in TIA**.

### 18.2 Tentativo non riuscito
Una prima variante con commenti in forma più ricca non è stata letta correttamente da TIA come commento campo visibile.

### 18.3 Variante riuscita
La forma che ha funzionato è la seguente:

```xml
<Member Name="bool_01" Datatype="Bool">
  <Comment>
    <MultiLanguageText Lang="en-US">Boolean test signal 1</MultiLanguageText>
  </Comment>
  <StartValue>false</StartValue>
</Member>
```

Per i `Real`:

```xml
<Member Name="real_01" Datatype="Real">
  <Comment>
    <MultiLanguageText Lang="en-US">Real test value 1</MultiLanguageText>
  </Comment>
  <StartValue>0.0</StartValue>
</Member>
```

Per gli `Int`:

```xml
<Member Name="int_01" Datatype="Int">
  <Comment>
    <MultiLanguageText Lang="en-US">Integer test value 1</MultiLanguageText>
  </Comment>
  <StartValue>0</StartValue>
</Member>
```

Per gli `IEC_TIMER`:

```xml
<Member Name="timer_01" Datatype="IEC_TIMER" Version="1.0">
  <Comment>
    <MultiLanguageText Lang="en-US">Timer instance 1</MultiLanguageText>
  </Comment>
</Member>
```

### 18.4 Regola pratica consolidata
Per i campi semplici del `GlobalDB`, la forma più affidabile per avere commenti visibili in TIA è:

- `Comment`
  - `MultiLanguageText Lang="en-US"`
- `StartValue` per i tipi semplici compatibili.

### 18.5 Regola empirica importante
Nei test, la variante con:

- `Comment` semplice;
- `StartValue` sui tipi semplici;

ha funzionato meglio della variante più “ricca” con forme informative aggiuntive.

Questa regola va quindi considerata **validata empiricamente** per il progetto corrente.

---

## 19. Regole sui `StartValue`

Per massimizzare compatibilità e leggibilità del DB generato, conviene adottare queste regole.

### 19.1 `Bool`
Usare:

```xml
<StartValue>false</StartValue>
```

### 19.2 `Int`
Usare:

```xml
<StartValue>0</StartValue>
```

### 19.3 `Real`
Usare:

```xml
<StartValue>0.0</StartValue>
```

### 19.4 `Struct`
La `Struct` in sé può avere un commento del nodo padre; i figli semplici possono avere i propri `StartValue`.

### 19.5 `IEC_TIMER`
Nei test riusciti è stato usato:

- `Comment` presente;
- `Version="1.0"` presente;
- nessun `StartValue` esplicito.

Questa è quindi la forma da preferire per ora.

---

## 20. Regole sul commento di blocco e sul titolo di blocco

Oltre ai commenti di campo, il `GlobalDB` deve mantenere una struttura standard di `ObjectList` per:

- `Comment` del blocco;
- `Title` del blocco.

Forma tipica:

```xml
<ObjectList>
  <MultilingualText ID="1" CompositionName="Comment">
    <ObjectList>
      <MultilingualTextItem ID="2" CompositionName="Items">
        <AttributeList>
          <Culture>en-US</Culture>
          <Text>Block comment</Text>
        </AttributeList>
      </MultilingualTextItem>
    </ObjectList>
  </MultilingualText>
  <MultilingualText ID="3" CompositionName="Title">
    <ObjectList>
      <MultilingualTextItem ID="4" CompositionName="Items">
        <AttributeList>
          <Culture>en-US</Culture>
          <Text>Block title</Text>
        </AttributeList>
      </MultilingualTextItem>
    </ObjectList>
  </MultilingualText>
</ObjectList>
```

Questa forma è coerente con il tipico `db_1.xml` e con i DB di prova generati.

---

## 21. Regole sui namespace del `GlobalDB`

Anche per il DB separato valgono regole di prudenza analoghe a quelle emerse per il GRAPH.

### 21.1 Regola consigliata
Usare:

- root `Document` senza prefissi `ns0:`;
- namespace dell'interfaccia dichiarato localmente su `Sections`.

Esempio:

```xml
<Interface>
  <Sections xmlns="http://www.siemens.com/automation/Openness/SW/Interface/v5">
    ...
  </Sections>
</Interface>
```

### 21.2 Regola da evitare
Evitare, salvo validazione esplicita, serializzazioni che propagano namespace aggressivi all'intera root.

---

## 22. Regole di naming e numbering per il `GlobalDB`

### 22.1 Nome blocco
Il `Name` del blocco deve essere coerente con la sua funzione.

Pattern consigliati:

- `DB_<Machine>_<Sequence>`
- `DB_<GraphName>_Data`
- `DB_<Cell>_<Function>_Seq`

### 22.2 Numero blocco
Il `Number` deve essere assegnato in modo deterministico.

Strategie possibili:

- regola fissa per famiglia di blocchi;
- tabella di allocazione centralizzata;
- derivazione da naming registry del progetto.

### 22.3 Naming dei member
Evitare nomi puramente casuali salvo DB di test.

Per DB reali, usare naming funzionale coerente, ad esempio:

- `Cmd_Start`
- `Cmd_Stop`
- `Fb_CylinderFwd`
- `Fb_CylinderHome`
- `Par_FillTimeout`
- `Diag_AlarmActive`

---

## 23. Modello canonico consigliato per il DB companion

Il DB separato non deve essere una replica dei dati runtime interni GRAPH.

La struttura consigliata è invece funzionale e impiantistica.

### 23.1 Sezioni logiche consigliate
Organizzare il contenuto tramite `Struct` principali, ad esempio:

- `Cmd`
- `Fb`
- `Par`
- `Diag`
- `Manual`
- `Auto`
- `Recipe`
- `StepData`
- `TransitionData`
- `AwlMapping`

### 23.2 Esempio di struttura logica

```text
DB_Seq_Pallet
 ├─ Cmd
 │   ├─ Start
 │   ├─ Stop
 │   └─ Reset
 ├─ Fb
 │   ├─ CylinderHome
 │   ├─ CylinderFwd
 │   └─ PartPresent
 ├─ Par
 │   ├─ StepTimeout
 │   ├─ AlarmDelay
 │   └─ SpeedRef
 ├─ Diag
 │   ├─ AlarmActive
 │   ├─ AlarmCode
 │   └─ WarningActive
 └─ AwlMapping
     ├─ OldStateBit_10
     ├─ OldStateBit_11
     └─ LegacyTimer_1
```

### 23.3 Vantaggio
Questa struttura rende il DB:

- leggibile;
- più stabile del runtime interno;
- più adatto a manutenzione;
- adatto a HMI e diagnostica;
- indipendente dai dettagli interni Siemens del GRAPH.

---

## 24. IR consigliato per il compilatore `GlobalDB`

Il generatore DB deve lavorare su un modello intermedio esplicito.

### 24.1 IR del blocco DB
Campi consigliati:

- `db_name`
- `db_number`
- `memory_layout`
- `memory_reserve`
- `block_comment`
- `block_title`
- `members[]`

### 24.2 IR del member
Campi consigliati:

- `name`
- `datatype`
- `version`
- `remanence`
- `attributes[]`
- `comment`
- `start_value`
- `children[]`

### 24.3 Vantaggio dell'IR
Il generatore:

- non dipende da template statici;
- separa il contenuto dalla serializzazione;
- rende possibile validazione preventiva;
- consente naming deterministico;
- rende testabile ogni classe di `Member`.

---

## 25. Serializer raccomandato per il `GlobalDB`

### 25.1 Pipeline concettuale

`IR DB -> validator DB -> serializer XML -> test import TIA`

### 25.2 Passi del serializer

1. creare `Document`;
2. creare `Engineering version="V20"`;
3. creare `SW.Blocks.GlobalDB`;
4. creare `AttributeList`;
5. emettere `Interface`;
6. emettere `Sections` con namespace locale corretto;
7. creare `Section Name="Static"`;
8. serializzare ricorsivamente tutti i `Member`;
9. emettere `MemoryLayout`, `MemoryReserve`, `Name`, `Namespace`, `Number`, `ProgrammingLanguage`;
10. emettere `ObjectList` con `Comment` e `Title` del blocco.

### 25.3 Pseudocodice del serializer

```text
emit_global_db(db):
    create Document
    create Engineering(version="V20")
    create SW.Blocks.GlobalDB
    create AttributeList
    emit Interface
    emit Sections(ns=Interface/v5)
    emit Section(Name="Static")
    for member in db.members:
        emit_member(member)
    emit MemoryLayout
    emit MemoryReserve
    emit Name
    emit Namespace
    emit Number
    emit ProgrammingLanguage("DB")
    emit block Comment/Title in ObjectList
```

```text
emit_member(m):
    open Member(Name, Datatype, optional Version, optional Remanence)
    if m.attributes:
        emit AttributeList
    if m.comment:
        emit Comment/MultiLanguageText
    if m.start_value exists:
        emit StartValue
    for child in m.children:
        emit_member(child)
    close Member
```

---

## 26. Validator consigliato per il `GlobalDB`

Il tool deve avere anche un validator DB dedicato.

### 26.1 Controlli strutturali minimi
- root `Document` presente;
- `Engineering version="V20"` presente;
- `SW.Blocks.GlobalDB` presente;
- `ProgrammingLanguage = DB`;
- `Interface/Sections/Section Name="Static"` presente;
- namespace `Interface/v5` presente localmente su `Sections`;
- `Name` valorizzato;
- `Number` valorizzato.

### 26.2 Controlli sui member
- ogni `Member` ha `Name` e `Datatype`;
- `Version` presente quando richiesto dal datatype;
- `Struct` con figli coerenti;
- `StartValue` coerente col datatype;
- `Comment` ben formato quando presente.

### 26.3 Controlli consigliati sui commenti
- `Comment` deve contenere `MultiLanguageText`;
- `Lang` valorizzato;
- testo non nullo quando il commento è richiesto;
- per i tipi semplici commentati, preferire presenza anche di `StartValue`.

---

## 27. Caso di test pratico già validato

È stato generato e importato con successo un DB di prova contenente:

- 20 booleani;
- 15 reali;
- 12 interi;
- 1 struct con 3 interi e 2 booleani;
- 10 timer `IEC_TIMER Version="1.0"`.

Successivamente sono stati aggiunti commenti di campo visibili in TIA.

### 27.1 Regole pratiche emerse da questo test
- la struttura `GlobalDB` era corretta;
- i tipi semplici con `Comment + StartValue` sono risultati visibili in TIA;
- i timer hanno funzionato con `Comment` e `Version="1.0"` senza `StartValue`;
- i commenti sui campi della struct funzionano a livello dei member figli;
- il commento del nodo struct può essere presente come commento del contenitore.

Questa prova è attualmente la migliore evidenza pratica per la serializzazione dei commenti campo lato DB.

---

## 28. Architettura complessiva aggiornata del tool Python

A questo punto l'architettura corretta del tool è composta da **due compilatori distinti** che condividono lo stesso IR di sequenziatore o una sua proiezione.

### 28.1 Compilatore 1: GRAPH FB compiler
Input:
- IR della macchina a stati.

Output:
- `SW.Blocks.FB` GRAPH con:
  - `GraphVersion = 2.0`;
  - interface corretta;
  - statici interni obbligatori;
  - sequence valida;
  - transition LAD nel sottoinsieme sicuro.

### 28.2 Compilatore 2: GlobalDB compiler
Input:
- IR dei dati applicativi del sequenziatore.

Output:
- `SW.Blocks.GlobalDB` con:
  - sezione `Static`;
  - member semplici/array/struct/tipi versionati;
  - commenti visibili in TIA;
  - eventuali start value.

### 28.3 Coordinamento tra i due compilatori
I due artefatti devono essere coerenti sul piano applicativo, ma non devono essere confusi:

- il GRAPH contiene il runtime interno e la topologia della sequenza;
- il DB contiene dati applicativi e di integrazione.

---

## 29. Decisioni progettuali ora da considerare fissate

Le seguenti decisioni possono essere considerate consolidate.

### 29.1 Sul GRAPH
1. target = GRAPH V2 / TIA Portal V20;
2. approccio non template-based;
3. approccio IR-driven + grammar-driven;
4. il runtime numerico non è il centro del problema;
5. il punto più fragile sono le transition;
6. il LAD va compilato in un sottoinsieme sicuro;
7. `AND = serie`;
8. `OR = nodo O`;
9. `NOT = contatto negato`;
10. niente `A` finché non esiste un caso validato che lo richieda;
11. alternative sempre con `AltBegin`;
12. paralleli sempre con `SimBegin/SimEnd`;
13. merge multipli sugli step tramite `Jump`;
14. `SNO` e `TNO` coerenti con `Number`;
15. validator parte integrante del tool.

### 29.2 Sul DB separato
1. il DB companion è un `SW.Blocks.GlobalDB` separato;
2. non sostituisce gli statici interni del GRAPH;
3. il riferimento sintattico di base è `db_1.xml`;
4. la generazione deve essere IR-driven;
5. il serializer deve essere ricorsivo sui `Member`;
6. vanno supportati scalari, array, struct, tipi versionati e attributi;
7. i commenti campo visibili in TIA si ottengono in modo affidabile con `Comment + MultiLanguageText`;
8. per i tipi semplici è consigliato aggiungere `StartValue`;
9. per `IEC_TIMER` mantenere `Version="1.0"`;
10. namespace dichiarato localmente su `Sections`;
11. `ProgrammingLanguage = DB`;
12. `ObjectList` con `Comment` e `Title` del blocco sempre presente.

---

## 30. Checklist pratica da riusare per i `GlobalDB`

Quando si genera o si corregge un DB XML, verificare sempre:

1. `Document` senza `ns0:`;
2. `Engineering version="V20"`;
3. blocco `SW.Blocks.GlobalDB`;
4. `ProgrammingLanguage = DB`;
5. `Interface` presente;
6. `Sections` con namespace `Interface/v5` locale;
7. `Section Name="Static"` presente;
8. `Name` del blocco valorizzato;
9. `Number` del blocco valorizzato;
10. `MemoryLayout` valorizzato;
11. `ObjectList` con `Comment` e `Title` del blocco;
12. ogni `Member` con `Name` e `Datatype`;
13. `Version` presente sui tipi che la richiedono;
14. `Struct` con figli coerenti;
15. `Comment` ben formato se richiesto;
16. `MultiLanguageText Lang="en-US"` presente nei commenti campo;
17. `StartValue` coerente sui tipi semplici;
18. niente forme XML ridondanti non validate se non strettamente necessarie.

---

## 31. Pipeline complessiva aggiornata del progetto

La pipeline concettuale aggiornata diventa:

`AWL -> parser -> estrazione macchina a stati -> IR sequenza + IR dati -> validator -> GRAPH compiler + GlobalDB compiler -> test import TIA`

### 31.1 Output finali attesi
Per ogni sequenziatore AWL il sistema dovrebbe produrre:

1. specifica leggibile della sequenza;
2. `FB` GRAPH importabile;
3. `GlobalDB` companion importabile;
4. eventualmente mapping leggibile tra simboli AWL originali e nuovo modello GRAPH/DB.

---

## 32. Prossimi passi consigliati

I prossimi passi tecnicamente più utili sono i seguenti.

### 32.1 Formalizzare un IR unico di progetto
Un unico IR dovrebbe descrivere:

- macchina a stati;
- transition logic;
- segnali applicativi;
- parametri;
- mapping AWL;
- metadati di naming.

Da questo IR si dovrebbero poi derivare:

- il GRAPH XML;
- il `GlobalDB` XML.

### 32.2 Definire il template logico canonico del companion DB
Per il progetto reale conviene fissare una struttura canonica, ad esempio:

- `Cmd`
- `Fb`
- `Par`
- `Diag`
- `Manual`
- `Auto`
- `Recipe`
- `AwlMapping`

### 32.3 Implementare un validator automatico del DB
Serve un validator che controlli:

- struttura XML;
- coerenza tipi;
- correttezza commenti;
- correttezza `StartValue`;
- conformità ai pattern validati.

### 32.4 Creare test di regressione
La suite minima dovrebbe includere:

- DB con soli scalari;
- DB con scalari commentati;
- DB con struct annidata;
- DB con timer IEC;
- DB con array;
- DB con attributi.

---

## 33. Sintesi finale consolidata

La sintesi più corretta dello stato del progetto, dopo gli ultimi test, è questa:

**il progetto non richiede più soltanto la generazione di un XML GRAPH valido, ma la generazione coordinata di due artefatti distinti e complementari:**

1. **un `SW.Blocks.FB` GRAPH V2 importabile**, costruito con regole topologiche hard e con transition LAD in un sottoinsieme sicuro;
2. **un `SW.Blocks.GlobalDB` companion importabile**, generato con serializer ricorsivo di `Member`, coerente con la grammatica TIA, e capace di mostrare commenti di campo visibili in TIA secondo la forma validata dai test.

Di conseguenza, l'architettura corretta del futuro tool Python non è un semplice generatore di XML, ma un sistema deterministico composto almeno da:

- parser AWL;
- estrattore della macchina a stati;
- IR comune;
- compilatore GRAPH;
- compilatore `GlobalDB`;
- validator per entrambi gli output.

---

## 34. Uso consigliato di questo report

Questo file va usato come:

- memoria tecnica consolidata del progetto;
- contesto per le prossime chat;
- base per la specifica del tool Python;
- base per implementare il serializer del `GlobalDB`;
- checklist pratica per generare o correggere XML GRAPH e DB per TIA Portal V20.

---

## 35. Nuova regola consolidata emersa dal GRAPH corretto importato

Dal confronto con il file `Graph_pallet_station_parallel_timeout_with_alarm_end.xml`, che TIA importa correttamente, emerge una regola nuova e decisiva:

**un GRAPH importabile non può essere modellato come sola `Sequence` più eventuale DB companion esterno; deve essere generato come `SW.Blocks.FB` GRAPH autosufficiente, con interfaccia coerente, area `Temp`, statici runtime coerenti e transizioni LAD che referenziano simboli risolvibili e dichiarati in modo consistente. Tali simboli possono essere locali al blocco oppure, se l'accesso è esplicito e simbolico, membri di un `GlobalDB` companion.**

Questa regola modifica in modo sostanziale l'architettura del generatore.

### 35.1 Formula corretta
La formula corretta non è:

`GRAPH = Sequence + transition logic + DB esterno`

La formula corretta è:

`GRAPH = FB autosufficiente = Interface completa + Temp + Static runtime + Sequence + transition LAD + solo in aggiunta eventuale DB companion`

### 35.2 Conseguenza pratica
Il `GlobalDB` companion resta utile, ma **non sostituisce mai**:

- la sezione `Input` del FB GRAPH quando serve esporre operandi locali;
- la sezione `Temp` del FB GRAPH;
- la sezione `Static` del FB GRAPH;
- gli operandi di transition che devono essere comunque risolvibili nel `FlgNet`;
- la coerenza interna del runtime GRAPH.

In altre parole: il companion DB è un artefatto di supporto, integrazione, diagnostica o mapping, ma il GRAPH deve essere comunque internamente completo.

---

## 36. Diagnosi del motivo per cui i GRAPH precedenti non importavano

Il motivo del fallimento non era principalmente la forma XML generale del documento, ma l'incompletezza del modello interno del FB GRAPH rispetto a quanto TIA si aspetta davvero.

### 36.1 Errore concettuale principale
L'errore più importante è stato trattare il blocco come:

- topologia GRAPH corretta;
- logiche di transizione LAD corrette;
- DB companion con le variabili.

Questo non basta.

Il file corretto mostra che TIA vuole invece:

- operandi delle transition dichiarati in modo coerente e risolvibile dal `FlgNet`, localmente oppure tramite path simbolico verso DB;
- tempi delle transition dichiarati nel `Temp` del blocco;
- statici runtime completi e coerenti;
- corrispondenza stretta fra `Sequence`, `Static`, `Temp` e `FlgNet`.

### 36.2 Mancanza della sezione `Temp`
Nei tentativi falliti mancava la vera infrastruttura temporale del blocco.

Nel file corretto esiste una `Section Name="Temp"` con una variabile `ET_Tx : Time` per ciascuna transition del GRAPH. Questa famiglia di variabili non è opzionale quando il `FlgNet` usa confronti temporali nelle transition.

Regola nuova:

**se una transition usa un confronto temporale, il FB deve dichiarare in `Temp` la relativa variabile `ET_Tx : Time`, con numerazione coerente con la transition `Tx`.**

### 36.3 Errore sul posizionamento delle variabili di transition
Nei tentativi falliti le condizioni di transition erano state spostate troppo nel DB companion.

Il file corretto mostra che una soluzione molto robusta è dichiarare gli operandi letti dai contatti LAD nella `Interface` del FB, tipicamente in `Input`, e referenziarli poi con `Access Scope="LocalVariable"`. Le prove successive hanno però confermato anche una seconda forma valida: gli operandi logici possono risiedere in un `GlobalDB` companion, purché il `FlgNet` li referenzi in modo esplicito con `Access Scope="GlobalVariable"` e `Symbol` composto dal nome del DB e dal nome del membro.

Regola nuova:

**gli operandi letti nel `FlgNet` delle transition devono essere simboli risolvibili dal FB GRAPH. Possono essere locali al blocco (tipicamente `Input`) oppure membri di un `GlobalDB` companion, ma in questo secondo caso devono essere referenziati in modo esplicito e simbolico come `GlobalVariable`. Non è sufficiente che il DB esista: il `FlgNet` deve puntare davvero al percorso simbolico del DB.**

### 36.4 Errore di modellazione del parallelismo
I tentativi falliti avevano rappresentato i paralleli a 3 rami in modo troppo generico o troppo astratto.

Il file corretto mostra che i paralleli vengono accettati da TIA solo se espressi con una topologia concreta e coerente con GRAPH, spesso includendo nodi di join espliciti e step di sincronizzazione dedicati, anziché forzare una rappresentazione teorica minimale.

Regola nuova:

**la sincronizzazione di rami paralleli deve essere modellata con strutture topologiche concrete (`SimBegin`, `SimEnd`, eventuali step di join e transition di riunificazione) e non con scorciatoie di sola connettività logica.**

### 36.5 Errore sugli statici runtime interni
I tentativi precedenti usavano valori runtime plausibili ma non sempre pienamente coerenti con la sequenza reale.

Il file corretto mostra invece che:

- `RT_DATA` è strutturalmente coerente;
- il conteggio step/transition/parti di sequenza è coerente;
- ogni step ha il suo `G7_StepPlus_V2`;
- ogni transition ha il suo `G7_TransitionPlus_V2`;
- i metadati runtime interni sono complessivamente allineati alla topologia effettiva del blocco.

Regola nuova:

**nei GRAPH semplici può bastare una buona approssimazione degli statici runtime; nei GRAPH complessi con paralleli, join e allarmi terminali è necessario costruire gli statici runtime in modo molto più aderente alla sequenza effettiva.**

---

## 37. Regole hard nuove per il compilatore GRAPH

Le regole già consolidate vanno ora estese con i vincoli seguenti.

### 37.1 Il GRAPH deve essere un FB autosufficiente
Il compilatore GRAPH deve sempre emettere un `SW.Blocks.FB` completo, non solo una `CompileUnit` o una `Sequence` isolata.

Il blocco deve includere almeno:

- `AttributeList` coerente;
- `Interface` completa;
- `ObjectList` coerente;
- `SW.Blocks.CompileUnit` con `NetworkSource/Graph`.

### 37.2 La `Interface` non può essere minimale
La `Interface` del GRAPH deve essere progettata come parte integrante del modello, non come contenitore vuoto.

Devono essere gestite in modo esplicito almeno queste sezioni:

- `Input`
- `Output`
- `InOut`
- `Static`
- `Temp`
- `Constant`

Di queste, `Input`, `Static` e `Temp` sono ora da considerare strutturalmente decisive.

### 37.3 Regola sugli operandi delle transition
Per ogni transition `Tx`, il compilatore deve derivare l'insieme degli operandi usati nel suo `FlgNet`.

Tali operandi devono essere dichiarati nel blocco, con naming coerente.

Schema pratico raccomandato:

- contatto iniziale o condizione primaria -> `Input` **oppure** `GlobalDB` companion
- contatti paralleli -> `Input` **oppure** `GlobalDB` companion
- variabile temporale elapsed -> `Temp`
- costanti temporali -> `TypedConstant` nel `FlgNet`

### 37.4 Regola sugli elapsed times `ET_Tx`
Per ogni transition `Tx` che usa una soglia temporale:

- creare `ET_Tx : Time` in `Temp`;
- usare `Access Scope="LocalVariable"` verso `ET_Tx` nel `FlgNet`;
- confrontare `ET_Tx` contro costante `Time` nel `Gt`.

Questa regola vale anche se esiste un companion DB con parametri o timer applicativi.

### 37.5 Regola sugli ingressi locali nel LAD
Nel `FlgNet` delle transition, gli `Access` verso gli operandi logici devono usare uno scope coerente con la reale collocazione del simbolo:

- `LocalVariable` se il simbolo è dichiarato nell'interfaccia o in una sezione locale del FB;
- `GlobalVariable` se il simbolo risiede nel `GlobalDB` companion ed è referenziato con percorso simbolico completo.

Il vincolo hard non è quindi "tutto locale", ma "tutto esplicitamente risolvibile".

---

## 38. Pattern validato delle transition con tempo

Il file corretto fissa un pattern LAD molto più preciso di quanto si era ipotizzato inizialmente.

### 38.1 Pattern osservato
Il pattern ricorrente e valido è:

1. un primo `Contact` con condizione primaria;
2. due `Contact` su rami paralleli;
3. un nodo `O` con `Cardinality = 2`;
4. un comparatore `Gt` con `SrcType = Time`;
5. una costante temporale tipizzata `Time`;
6. una `TrCoil` finale.

### 38.2 Forma logica equivalente
La forma logica è:

`ContattoIniziale AND (ParA OR ParB) AND (ET_Tx > T#nS)`

### 38.3 Nuova interpretazione progettuale
Questa osservazione è importante:

- il primo contatto esprime la precondizione della transition;
- il nodo `O` non rappresenta un branch topologico del GRAPH, ma una OR interna al LAD della transition;
- il tempo non è modellato con un bit booleano, ma con una vera variabile `Time` confrontata a soglia.

### 38.4 Estensione controllata al triplo parallelo
Quando serve una transizione del tipo:

`Condizione0 AND (A OR B OR C) AND tempo`

non si deve presumere automaticamente che GRAPH accetti un nodo `O` con cardinalità arbitraria senza verifica.

Regola prudenziale:

**i pattern nuovi di `FlgNet` vanno introdotti solo dopo verifica su export reale TIA oppure per trasformazione controllata di un pattern già osservato.**

Se non esiste un export TIA che mostri `O` con cardinalità 3 in una transition GRAPH, la forma più prudente è:

- annidare due OR binarie nel LAD, oppure
- generare un simbolo ausiliario locale che aggreghi la terza condizione.

---

## 39. Regole nuove per parallelismi e join

### 39.1 Parallelismo topologico diverso dalla OR nel LAD
Va distinta in modo definitivo la differenza fra:

- parallelismo topologico della `Sequence`;
- OR logica nel `FlgNet` di una transition.

Sono due meccanismi diversi e non intercambiabili.

### 39.2 Regola sui rami paralleli
I rami paralleli veri del GRAPH devono essere modellati con:

- `SimBegin`;
- step dei rami;
- `SimEnd`;
- eventuali transition e step di join dedicati.

### 39.3 Regola sui join espliciti
Il file corretto mostra che, in casi complessi, conviene introdurre step di join intermedi dedicati, per esempio `S71_Join_*`, `S72_Join_*`, anziché tentare merge aggressivi o troppo impliciti.

Regola consigliata:

**nei GRAPH complessi con più rami e timeout, il compilatore dovrebbe poter generare step di join espliciti come elementi di sincronizzazione.**

### 39.4 Regola sui rami allarme
I rami di allarme terminali devono essere chiusi in modo pulito e strutturalmente esplicito.

Pattern da considerare consolidato:

- step di allarme;
- eventuale transition finale dedicata;
- chiusura con `EndConnection` oppure ritorno strutturato a step ammessi, secondo il pattern del caso validato.

---

## 40. Aggiornamento dell'architettura del tool

Alla luce del file corretto, l'architettura del futuro tool deve essere raffinata ulteriormente.

### 40.1 Architettura aggiornata
La pipeline concettuale corretta diventa:

`AWL -> parser -> estrazione macchina a stati -> IR topologico + IR interfaccia + IR transition logic + IR DB companion -> validator -> GRAPH FB compiler + GlobalDB compiler -> test import TIA`

### 40.2 Nuovi sotto-modelli IR necessari
L'IR unico precedente va esteso almeno con i seguenti sotto-modelli dedicati:

- `graph_interface_model`
- `graph_temp_model`
- `graph_static_runtime_model`
- `graph_sequence_model`
- `graph_transition_lad_model`
- `companion_db_model`

### 40.3 Responsabilità del GRAPH compiler
Il GRAPH compiler deve ora generare in modo deterministico:

1. `Interface` completa del FB;
2. sezione `Input` con le variabili usate dalle transition;
3. sezione `Temp` con tutti gli `ET_Tx` richiesti;
4. sezione `Static` con `RT_DATA`, step e transition coerenti;
5. `Sequence` topologicamente valida;
6. transition LAD coerenti con operandi esplicitamente risolvibili, locali oppure globali su companion DB;
7. eventuali join e step ausiliari di sincronizzazione.

### 40.4 Responsabilità del companion DB compiler
Il compiler del `GlobalDB` companion resta utile per:

- HMI;
- diagnostica;
- mapping AWL -> nuovo modello;
- parametri di linea;
- ricette;
- dati applicativi non direttamente runtime del GRAPH.

Non sostituisce però la completezza del FB GRAPH: anche quando ospita gli operandi logici delle transition, il blocco GRAPH deve restare autosufficiente per `Temp`, `Static`, runtime e topologia.

---

## 41. Nuove checklist operative

### 41.1 Checklist GRAPH complesso importabile
Prima di considerare pronto un GRAPH XML complesso, verificare sempre:

1. `SW.Blocks.FB` completo e non solo `CompileUnit`;
2. `GraphVersion = 2.0`;
3. `Interface` con sezioni complete;
4. `Input` contenente gli operandi realmente letti dalle transition;
5. `Temp` contenente tutti gli `ET_Tx` necessari;
6. `Static` con `RT_DATA` coerente;
7. un `G7_TransitionPlus_V2` per ogni transition;
8. un `G7_StepPlus_V2` per ogni step;
9. naming coerente tra `Sequence`, `Static`, `Temp` e `FlgNet`;
10. topologia di `AltBegin`, `SimBegin`, `SimEnd`, `Jump` e join conforme ai pattern validati;
11. rami di allarme chiusi correttamente;
12. nessun simbolo usato nel `FlgNet` che non sia risolvibile nel blocco o nel companion DB tramite `GlobalVariable`;
13. ogni transition temporizzata con il proprio `ET_Tx`;
14. costanti temporali espresse come costanti di tipo `Time`;
15. controlli OR nel LAD usati solo in forme già validate.

### 41.2 Checklist di diagnosi in caso di import fallito
Se un GRAPH non entra in TIA, controllare in questo ordine:

1. namespace e struttura XML generale;
2. coerenza `Interface`;
3. presenza `Temp`;
4. presenza `ET_Tx` per le transition temporizzate;
5. presenza degli operandi letti nel `FlgNet`, locali oppure referenziati correttamente come `GlobalVariable`;
6. coerenza fra step/transition della `Sequence` e statici del blocco;
7. topologia dei branch/join;
8. chiusura dei rami di allarme;
9. forma del `FlgNet` rispetto ai pattern osservati in export TIA reali;
10. plausibilità di `RT_DATA` e dei conteggi runtime.

---

## 42. Sintesi finale aggiornata dopo il file corretto

Dopo la validazione del file corretto importabile, la sintesi più precisa dello stato del progetto è la seguente:

1. **il companion DB è utile ma non è sufficiente**;
2. **il GRAPH deve essere generato come FB autosufficiente**;
3. **le transition temporizzate richiedono una vera area `Temp` locale con `ET_Tx`**;
4. **gli operandi usati nel LAD devono essere risolvibili in modo esplicito: locali al blocco oppure nel companion DB come `GlobalVariable`**;
5. **parallelismi e join complessi richiedono una topologia concreta, non solo connettività logica astratta**;
6. **nei casi semplici si possono tollerare approssimazioni runtime, nei casi complessi serve coerenza strutturale molto più stretta**.

Questa è ora la base corretta per la futura implementazione del compilatore GRAPH del progetto.

---

## 43. Regola consolidata nuova: collegamento esplicito delle transition al companion DB

Le prove successive hanno aggiunto una regola importante che corregge una formulazione troppo rigida delle sezioni precedenti.

In una prima fase era emersa la regola prudenziale secondo cui gli operandi delle transition dovessero stare sempre nell'interfaccia locale del FB GRAPH. Questa regola resta valida come **forma robusta e conservativa**, ma non è l'unica forma importabile.

È stato infatti verificato un caso corretto in cui:

- il FB GRAPH resta autosufficiente per struttura, runtime e tempi;
- le variabili logiche delle transition non sono locali;
- gli operandi logici vengono letti dal `GlobalDB` companion;
- il `FlgNet` usa `Access Scope="GlobalVariable"`;
- il `Symbol` è costruito come path TIA del tipo:
  - `<Component Name="NomeDB" />`
  - `<Component Name="NomeVariabile" />`

### 43.1 Regola hard aggiornata

La regola hard corretta non è:

`operandi transition = sempre LocalVariable`

La regola hard corretta è:

`operandi transition = simboli esplicitamente risolvibili`

Quindi:

- se il simbolo è nel FB -> `Access Scope="LocalVariable"`;
- se il simbolo è nel companion DB -> `Access Scope="GlobalVariable"` con path simbolico completo del DB.

### 43.2 Regola mista ormai consolidata

La forma che oggi risulta più solida è mista:

- `ET_Tx` resta locale al FB, in `Temp`, e viene letto come `LocalVariable`;
- gli operandi booleani della transition possono essere:
  - locali al FB, oppure
  - nel `GlobalDB` companion;
- le costanti temporali restano nel `FlgNet` come costanti tipizzate `Time`.

Formula pratica:

`Transition = (operandi logici locali o globali) AND (ET_Tx locale > soglia Time)`

### 43.3 Pattern XML da considerare valido

Pattern valido per una variabile logica nel DB companion:

```xml
<Access Scope="GlobalVariable" UId="...">
  <Symbol>
    <Component Name="DB_Name" />
    <Component Name="Var_Name" />
  </Symbol>
</Access>
```

Questo corrisponde al riferimento simbolico TIA:

`DB_Name.Var_Name`

### 43.4 Conseguenza architetturale

Questa regola rafforza il modello a due livelli:

1. **FB GRAPH autosufficiente** per topologia, runtime, `Static`, `Temp`, `ET_Tx` e coerenza interna;
2. **GlobalDB companion** come contenitore legittimo degli operandi logici di transition, HMI, diagnostica, mapping e parametri.

Quindi il companion DB:

- non sostituisce il FB GRAPH;
- non sostituisce `Temp`;
- non sostituisce `RT_DATA`;
- può però diventare la sede effettiva delle condizioni booleane lette dalle transition.

### 43.5 Checklist aggiuntiva per GRAPH collegati al DB

Quando il GRAPH usa un companion DB per le transition, verificare sempre:

1. esistenza del `GlobalDB` con il nome simbolico atteso;
2. esistenza di ogni `Member` referenziato nel `FlgNet`;
3. uso di `Access Scope="GlobalVariable"` sugli operandi DB;
4. presenza del path simbolico completo `DB -> Variabile`;
5. `ET_Tx` ancora presenti in `Temp` come `LocalVariable`;
6. assenza di riferimenti misti incoerenti tra nome DB reale e nome DB usato nel `Symbol`.

### 43.6 Sintesi aggiornata finale

A oggi la regola più precisa è questa:

**un GRAPH importabile deve essere un FB autosufficiente, ma le condizioni logiche delle transition possono essere tenute nel companion DB purché siano referenziate in modo simbolico esplicito come `GlobalVariable`; i tempi `ET_Tx` restano invece locali al FB.**



---

# PARTE C - REGOLE CONSOLIDATE PER GLI FC LAD

---

## 33. Nuovo obiettivo specifico emerso dal caso `fc_1.xml`

Oltre al compilatore GRAPH e al compilatore `GlobalDB`, il progetto deve ora considerare come target nativo anche la generazione di **blocchi `FC` in LAD importabili in TIA Portal V20**.

La scoperta importante è che `fc_1.xml` non rappresenta un GRAPH travestito, ma un vero tipico `SW.Blocks.FC` usato come blocco di orchestrazione applicativa.

Questo apre una terza linea di compilazione:

- `GRAPH compiler` per la sequenza esplicita;
- `GlobalDB compiler` per i dati applicativi esterni;
- `FC compiler` per logiche LAD combinatorie, latch e call di coordinamento.

---

## 34. Riferimento di base per gli FC: `fc_1.xml`

Il file `fc_1.xml` va interpretato come **tipico di serializzazione di un `SW.Blocks.FC` in linguaggio LAD**.

### 34.1 Struttura generale del blocco FC
La struttura valida osservata è:

- `Document`
  - `Engineering version="V20"`
  - `SW.Blocks.FC`
    - `AttributeList`
      - `AutoNumber`
      - `Interface`
      - `MemoryLayout`
      - `Name`
      - `Namespace`
      - `Number`
      - `ProgrammingLanguage`
      - `SetENOAutomatically`
    - `ObjectList`
      - `MultilingualText` per `Comment`
      - una sequenza di `SW.Blocks.CompileUnit`

### 34.2 Attributi hard del blocco FC osservati
Nel caso `fc_1.xml` risultano coerenti e significativi almeno questi attributi:

- `AutoNumber = false`;
- `MemoryLayout = Optimized`;
- `Name = FC_Sequenza_Start`;
- `Number = 300`;
- `ProgrammingLanguage = LAD`;
- `SetENOAutomatically = false`.

### 34.3 Interfaccia del blocco FC
L'interfaccia osservata è quella standard Openness:

- `Input`;
- `Output`;
- `InOut`;
- `Temp`;
- `Constant`;
- `Return` con `Ret_Val : Void`.

Osservazione importante:

**un FC LAD importabile non richiede necessariamente una interfaccia applicativa ricca**, perché può lavorare quasi interamente tramite `GlobalVariable` referenziate nel `FlgNet`.

---

## 35. Natura funzionale dell'FC emerso da `fc_1`

`fc_1` non implementa una sequenza GRAPH esplicita con `Step` e `Transition`.

Implementa invece una **sequenza implicita distribuita**, ottenuta tramite:

- reti combinatorie;
- reti `S/R`;
- bit globali di avanzamento o abilitazione;
- chiamate ripetute a FC ausiliari parametrizzati;
- timer globali esterni;
- latch di completamento;
- segnali di fronte.

Conseguenza progettuale:

il compilatore FC non deve ragionare in termini di `Sequence` GRAPH, ma in termini di **lista ordinata di reti LAD**.

---

## 36. Grammatica strutturale del `SW.Blocks.FC`

### 36.1 Unità base: `CompileUnit`
Ogni rete LAD è serializzata come una `SW.Blocks.CompileUnit` distinta.

Per ogni `CompileUnit` compaiono almeno:

- `AttributeList`;
- `NetworkSource`;
- `ProgrammingLanguage = LAD`;
- `ObjectList` con `Comment` e `Title` della rete.

### 36.2 Sorgente rete: `FlgNet`
La rete vera e propria è contenuta in:

- `NetworkSource`
  - `FlgNet`
    - `Parts`
    - `Wires`

Questa è la grammatica hard da serializzare correttamente per ottenere import in TIA.

### 36.3 Regola pratica sugli `UId`
Nel caso `fc_1` gli `UId` sono da considerare **significativi a livello di singolo `FlgNet`**.

Ne consegue che il generatore FC deve garantire:

- coerenza perfetta degli `UId` interni alla rete;
- nessun riferimento a nodi mancanti;
- nessun `Wire` verso porte inesistenti;
- nessun nodo orfano.

---

## 37. Nodi minimi che il compilatore FC deve saper emettere

Dal caso `fc_1.xml` risulta che il generatore FC deve supportare almeno i seguenti nodi.

### 37.1 `Access`
Classi minime osservate:

- `Access Scope="GlobalVariable"`;
- `Access Scope="LiteralConstant"`.

Regola importante:

i simboli globali devono essere serializzati come **catena ordinata di `Component`** e non come stringa piatta.

### 37.2 `Part`
Elementi minimi da supportare:

- `Contact`;
- `Contact` negato tramite `Negated Name="operand"`;
- `Coil`;
- `SCoil`;
- `RCoil`;
- `O` con `TemplateValue Name="Card"`;
- `Call`.

### 37.3 `Wires`
Il compilatore deve saper serializzare correttamente:

- `Powerrail`;
- `IdentCon`;
- `NameCon`.

La rete deve supportare anche:

- fan-out da un nodo verso più destinazioni;
- OR multi-ingresso;
- cablaggio verso parametri nominati delle call.

### 37.4 `CallInfo`
Per le chiamate funzione, la serializzazione deve includere:

- nome blocco chiamato;
- `BlockType`;
- dichiarazione dei parametri formali (`Input`, `Output`, `InOut`);
- datatype dei parametri;
- associazione reale tramite `Wire` ai pin della call.

---

## 38. Pattern funzionali estratti da `fc_1`

Le reti osservate nel blocco sono sei.

### 38.1 Rete 1 - Controllo ventilatori zona 1
Questa rete implementa una logica combinatoria del tipo **2-su-3**.

La bobina `Ventilator_Selezionati_zona_1` si attiva se almeno due tra i ventilatori 1, 2 e 3 risultano contemporaneamente:

- in automatico;
- selezionati.

Questo è realizzato come OR di tre rami AND distinti.

### 38.2 Rete 2 - Controllo ventilatori zona 2
La rete replica il pattern della zona 1 per i ventilatori 4, 5 e 6.

Tuttavia l'analisi ha evidenziato una **anomalia strutturale/funzionale del sorgente**:

nel terzo ramo compare un duplicato di `Ventilatore 5.Automatico` dove ci si aspetterebbe `Ventilatore 5.Selezionato`.

Questa osservazione è importante perché introduce un nuovo requisito per il tool:

oltre al serializer XML, serve anche una fase di **lint semantico** dei pattern LAD.

### 38.3 Rete 3 - Controllo ventilatore 7
Rete combinatoria semplice:

- `Ventilatore 7.Automatico`;
- `Ventilatore 7.Selezionato`;
- coil `Ventilatore_7_Automatico_e_Selezionato`.

Il ventilatore 7 è quindi trattato come risorsa condivisa con consenso dedicato.

### 38.4 Rete 4 - Selezione zona ventilatore 7
Questa rete introduce la logica di armamento delle sequenze di start di zona tramite:

- due rami condizionati dai feedback valvola;
- i consensi zona 1 / zona 2;
- il consenso del ventilatore 7;
- `Pls_Start_Supervisione`.

Le uscite principali sono due `SCoil`:

- `Sequenza_Start_Avviata_Zona_1`;
- `Sequenza_Start_Avviata_Zona_2`.

A valle, un OR finale pilota più `RCoil` di pulizia stato.

### 38.5 Rete 5 - Accensione ventilatori
Questa è la rete più importante del blocco.

La logica di sequenza non è espressa come catena GRAPH, ma come serie di chiamate a `FC_Start_Ventilatori` con parametri ripetuti:

- `Ventilatore_Auto`;
- `Ventilatore_Selezionato`;
- `Prossimo_Ventilatore_IN`;
- `Reset_Timer_Accensione`;
- `CMD_OUT`;
- `Timer`;
- `Prossimo_Ventilatore_OUT`.

Il pattern osservato è fondamentale:

**la progressione della sequenza è delegata allo stato parametrico delle call e ai bit globali di completamento**, non al solo wiring grafico della rete.

### 38.6 Rete 6 - Gestione avvio pompe a sequenza attiva
Questa rete contiene chiamate ripetute a `FC_Gestione_Accensionee_Sequenza_Attiva` e conferma il pattern architetturale generale:

- il blocco principale orchestri segnali e parametri;
- la logica riusabile venga incapsulata in FC ausiliari dedicati.

---

## 39. IR consigliato per il compilatore FC

Il compilatore FC deve lavorare su un IR esplicito di reti LAD.

### 39.1 IR del blocco FC
Campi consigliati:

- `fc_name`;
- `fc_number`;
- `memory_layout`;
- `auto_number`;
- `set_eno_automatically`;
- `interface_sections`;
- `block_comment`;
- `networks[]`.

### 39.2 IR della rete
Campi consigliati:

- `title`;
- `comment`;
- `parts[]`;
- `wires[]`.

### 39.3 IR dei nodi
Classi consigliate:

- `AccessNode` con `scope`, `symbol_components` oppure `literal_value`;
- `PartNode` con `name`, `negated`, `template_values`, `call_info`;
- `Wire` con lista ordinata di endpoint (`Powerrail`, `IdentCon`, `NameCon`).

### 39.4 Vantaggio dell'IR FC
Questo approccio:

- separa la logica dalla serializzazione XML;
- consente validazione preventiva della rete;
- rende possibile lint strutturale e semantico;
- permette di riusare pattern LAD noti;
- rende generabili anche reti con call parametrizzate.

---

## 40. Serializer e validator consigliati per il compilatore FC

### 40.1 Pipeline concettuale
La pipeline consigliata è:

`IR FC -> validator rete -> serializer XML FC -> test import TIA`

### 40.2 Controlli strutturali minimi
Il validator FC dovrebbe controllare almeno:

- `Document` presente;
- `Engineering version="V20"` presente;
- blocco `SW.Blocks.FC` presente;
- `ProgrammingLanguage = LAD` coerente a livello blocco e rete;
- presenza di `CompileUnit` ordinate;
- presenza di `FlgNet` con `Parts` e `Wires`;
- `UId` coerenti nella rete;
- tutte le connessioni risolte;
- nessun pin inesistente;
- nessun nodo orfano.

### 40.3 Controlli semantici consigliati
Oltre al controllo XML, conviene introdurre verifiche semantiche come:

- pattern combinatori sospetti;
- duplicazione anomala di operandi;
- call con parametri mancanti;
- timer non cablati;
- bit di completamento non usati;
- `SCoil/RCoil` non coerenti con la logica attesa.

### 40.4 Conseguenza progettuale
Il compilatore FC non deve essere soltanto un emettitore XML, ma un componente che conosce e valida la **grammatica LAD effettivamente usata nei tipici TIA**.

---

## 41. Architettura complessiva aggiornata del tool

Dopo l'analisi di `fc_1.xml`, l'architettura complessiva del progetto va considerata aggiornata come segue.

### 41.1 Compilatore 1 - GRAPH FB compiler
Input:

- IR della macchina a stati.

Output:

- `SW.Blocks.FB` GRAPH importabile.

### 41.2 Compilatore 2 - GlobalDB compiler
Input:

- IR dei dati applicativi del sequenziatore.

Output:

- `SW.Blocks.GlobalDB` companion importabile.

### 41.3 Compilatore 3 - FC LAD compiler
Input:

- IR di reti LAD applicative o di orchestrazione.

Output:

- `SW.Blocks.FC` importabile con una sequenza ordinata di `CompileUnit` LAD.

### 41.4 Coordinamento tra i tre compilatori
I tre artefatti non sono alternativi ma complementari:

- il `GRAPH` esplicita la macchina a stati;
- il `GlobalDB` contiene i dati applicativi e di integrazione;
- l'`FC` contiene logiche di servizio, consenso, orchestrazione o riuso funzionale.

### 41.5 Pipeline aggiornata del progetto
La pipeline concettuale aggiornata diventa:

`AWL -> parser -> estrazione pattern -> IR sequenza + IR dati + IR reti -> validator -> GRAPH compiler + GlobalDB compiler + FC compiler -> test import TIA`

---

## 42. Decisioni progettuali aggiuntive ora da considerare fissate

Le seguenti decisioni, emerse dal caso `fc_1`, possono essere considerate consolidate.

### 42.1 Sugli FC
1. il target `SW.Blocks.FC` va trattato come terzo backend nativo del progetto;
2. un FC LAD importabile è organizzato come lista ordinata di `CompileUnit`;
3. la rete elementare è `FlgNet` con `Parts` e `Wires`;
4. i simboli globali vanno serializzati come catena di `Component`;
5. il compilatore deve supportare `Contact`, `Coil`, `SCoil`, `RCoil`, `O`, `Call`, costanti e contatti negati;
6. le call devono essere serializzate con parametri formali e wiring coerente;
7. gli `UId` vanno gestiti con coerenza stretta a livello di rete;
8. oltre al validator XML serve un lint semantico dei pattern LAD;
9. `fc_1` dimostra che una sequenza implicita può essere distribuita su FC ausiliari e bit globali;
10. il progetto non deve limitarsi alla conversione AWL -> GRAPH, ma deve saper anche generare blocchi FC di supporto o di orchestrazione.

---

## 43. Prossimi passi consigliati dopo l'analisi di `fc_1`

I prossimi passi più utili sono:

1. formalizzare l'IR del compilatore FC;
2. creare un serializer minimo capace di generare reti LAD con `Contact`, `O`, `Coil`;
3. estendere poi il serializer a `SCoil`, `RCoil` e `Call`;
4. aggiungere un validator strutturale dedicato agli FC;
5. aggiungere un lint semantico per intercettare anomalie come quella osservata nella rete zona 2 di `fc_1`;
6. decidere quali pattern AWL dovranno produrre GRAPH e quali invece FC LAD di supporto.


---

## 44. Nuovo tipico decisivo per il backend FC: `fc_2.xml`

Dopo il consolidamento del caso `fc_1.xml`, il file `fc_2.xml` ha introdotto una seconda famiglia di regole molto più specifiche e decisive: la serializzazione reale in LAD dei **box IEC standard**.

Questo file va considerato il riferimento principale per:

- `TON`;
- `TOF`;
- `CTU`.

### 44.1 Struttura osservata del blocco

Nel caso `fc_2.xml` il blocco è ancora un vero `SW.Blocks.FC` in LAD, con struttura Openness standard:

- `Document`;
- `Engineering version="V20"`;
- `SW.Blocks.FC`;
- `AttributeList` con `Interface`, `MemoryLayout`, `Name`, `Number`, `ProgrammingLanguage`, `SetENOAutomatically`;
- `ObjectList` con `Comment` e una sequenza di `CompileUnit`.

Osservazione importante:

`fc_2.xml` mostra che `AutoNumber` non è da considerare un attributo hard obbligatorio per ogni FC; in questo tipico non è necessario per avere una struttura valida.

### 44.2 Regola sugli operandi locali nel backend FC

`fc_2.xml` mostra in modo esplicito che i segnali applicativi semplici del box possono stare in `Temp` e venire referenziati come `Access Scope="LocalVariable"`.

Questo vale, nel tipico osservato, per segnali come:

- attivazione del timer;
- bit di uscita del timer;
- bit di conteggio;
- reset del contatore.

Regola consolidata:

**nel backend FC gli operandi semplici possono essere locali al blocco (`Temp`) oppure globali, purché la loro collocazione sia coerente con il tipo di segnale e con la serializzazione del `FlgNet`.**

### 44.3 Regola hard per `TON` e `TOF`

Nel caso `fc_2.xml`, `TON` e `TOF` non sono serializzati come `Call` generiche ma come veri `Part` dedicati:

- `Part Name="TON" Version="1.0"`;
- `Part Name="TOF" Version="1.0"`.

Ogni box contiene una `Instance` interna:

- `Instance Scope="GlobalVariable"`;
- componente simbolico del DB istanza.

Regola consolidata:

**`TON` e `TOF` vanno emessi come box IEC nativi del `FlgNet`, non come call generiche a FC.**

### 44.4 Regola hard su `PT`

Nel tipico `fc_2.xml`, il pin `PT` dei timer è serializzato come:

- `Access Scope="TypedConstant"`;
- costante tempo esplicita, per esempio `T#5MS`.

Regola consolidata:

**`PT` dei timer IEC nel backend FC va serializzato come `TypedConstant` di tipo `Time`, non come `LiteralConstant`.**

### 44.5 Regola hard per `CTU`

Nel caso `fc_2.xml`, il contatore è serializzato come:

- `Part Name="CTU" Version="1.0"`;
- `Instance Scope="GlobalVariable"`;
- pin `CU`, `R`, `PV`, `Q`, `CV` cablati esplicitamente.

Il preset `PV` compare come:

- `Access Scope="LiteralConstant"`;
- `ConstantType = Int`;
- valore numerico intero.

Regola consolidata:

**`CTU` va emesso come box IEC nativo; `PV` va serializzato come `LiteralConstant` tipizzato `Int`.**

### 44.6 Regola sui pin non usati

`fc_2.xml` mostra che i pin non utilizzati dei box IEC non vengono omessi, ma terminati con `OpenCon`.

Esempi osservati:

- `ET` del timer non usato;
- `CV` del contatore non usato.

Regola consolidata:

**quando un pin standard del box IEC non viene utilizzato, il serializer FC dovrebbe preferire `OpenCon` alla semplice omissione.**

### 44.7 Conseguenza progettuale del caso `fc_2`

Il caso `fc_2.xml` sposta il livello di maturità del backend FC:

- `fc_1.xml` aveva consolidato la grammatica generale del LAD;
- `fc_2.xml` consolida la grammatica specifica dei box IEC standard.

Conseguenza:

**il backend FC non è più soltanto “reti LAD generiche”, ma deve includere serializer dedicati per box IEC standard (`TON`, `TOF`, `CTU`).**

---

## 45. Nuovo tipico mirato sui pattern LAD elementari: `fc_3.xml`

Il file `fc_3.xml` introduce un terzo livello di osservazione: non i box IEC, ma i **pattern LAD elementari di latch, reset, OR e doppia scrittura**.

Nel tipico risultano presenti almeno i seguenti pattern:

- rete con `Contact -> SCoil`;
- rete con `Contact -> RCoil`;
- rete con `Contact -> SCoil` e `RCoil` nello stesso trasferimento di stato;
- rete con una stessa condizione che pilota più `RCoil`;
- rete con OR (`Part Name="O"`) verso una `Coil`;
- rete con due bobine normali in forma separata.

### 45.1 Valore progettuale di `fc_3`

Anche quando non è ancora usato come gold sample definitivo di import riuscito, `fc_3.xml` è estremamente utile come **tipico mirato di reverse engineering** per i pattern LAD che nella FC completa erano ancora sospetti.

In particolare permette di isolare:

1. comportamento di `SCoil` e `RCoil`;
2. reset multipli pilotati dalla stessa condizione;
3. OR reale verso una bobina;
4. scritture multiple di bit in LAD.

### 45.2 Conseguenza progettuale

Il backend FC non deve essere validato solo sui blocchi grandi (`fc_1`) o sui box IEC (`fc_2`), ma anche sui pattern LAD **microscopici e combinabili**.

Conseguenza:

**serve una suite di micro-tipici per convalidare ogni famiglia di rete prima di ricomporre una FC complessa.**

---

## 46. Esito dei test pratici sulla generazione della FC completa

Durante questa sessione è stata tentata la generazione di una FC completa di sequenziatore in più varianti successive (`v1` ... `v7`, incluse varianti bisecate e con namespace corretti).

### 46.1 Osservazione chiave

Le varianti complete della FC **non sono risultate importabili** in TIA, anche quando sono stati corretti via via:

- gli `ID` globali;
- i riferimenti simbolici ai membri del DB;
- il pattern dei box IEC;
- la forma dei namespace;
- la normalizzazione dei segnali `.DN` verso il dialetto IEC `Q`.

### 46.2 Conseguenza metodologica

La mancata importazione della FC completa non può più essere interpretata come semplice errore “di sintassi XML generica”.

Il problema va interpretato come uno o più dei seguenti casi:

1. pattern LAD non ancora pienamente ancorato a un export reale TIA;
2. combinazione di pattern validi singolarmente ma non ancora validata nella stessa FC;
3. modellazione non abbastanza conservativa delle scritture multiple o dei latch;
4. differenza tra notazione ladder generica e dialetto IEC/TIA effettivamente importabile.

### 46.3 Stato attuale della validazione FC

Lo stato corretto da fissare oggi è questo:

- **backend FC grammaticalmente compreso** su `fc_1.xml`;
- **box IEC compresi** su `fc_2.xml`;
- **pattern elementari da consolidare ulteriormente** con `fc_3.xml` e con micro-tipici successivi;
- **FC complessa completa non ancora considerabile consolidata come importabile**.

Questa distinzione è importante e va fissata nel report per evitare di trattare come “risolto” ciò che è solo parzialmente validato.

---

## 47. Test minimale decisivo riuscito: `GlobalDB + FC_Test_IEC_GlobalDB`

Tra tutti i test eseguiti, quello che ha dato il segnale più forte è stato il test minimale con:

- `GlobalDB` di prova;
- FC minimale con box IEC e riferimenti globali coerenti.

Il test è stato importato subito con successo.

### 47.1 Conseguenza tecnica immediata

Questo dimostra che il problema **non è**:

- il contenitore generale `SW.Blocks.FC`;
- la presenza di un `GlobalDB` companion in sé;
- il solo uso di box IEC in LAD;
- il solo uso di riferimenti globali.

### 47.2 Regola hard aggiornata per il backend FC

La regola corretta da fissare è la seguente:

**un FC LAD con box IEC può importare correttamente se usa simboli globali realmente risolvibili e istanze IEC coerenti con il modello dati dichiarato.**

### 47.3 Conseguenza architetturale

Questa prova rafforza definitivamente il modello a tre backend:

- `GRAPH compiler`;
- `GlobalDB compiler`;
- `FC compiler`.

Ma aggiunge una regola più precisa per il terzo backend:

**la generazione FC deve essere guidata da pattern validati rete-per-rete, non da una sola emissione monolitica dell'intera sequenza.**

---

## 48. Normalizzazione del dialetto ladder verso TIA/IEC

Durante la generazione della FC completa è emersa una differenza importante tra la specifica testuale iniziale del sequenziatore e il dialetto realmente coerente con TIA/IEC.

### 48.1 Differenza osservata

La specifica testuale usava forme del tipo:

- `FEED_MAX.DN`;
- `CLAMP_MAX.DN`;
- `WORK.DN`;
- `EJECT_MAX.DN`;
- `EJECT_DWELL.DN`;
- `DONE_PULSE.DN`;
- `PARTS_COUNT.DN`;
- `RES PARTS_COUNT`.

Nel backend TIA/IEC osservato in `fc_2.xml`, i box usano invece i pin reali:

- per timer: `IN`, `PT`, `Q`, `ET`;
- per contatore: `CU`, `R`, `PV`, `Q`, `CV`.

### 48.2 Regola nuova di normalizzazione

Per il progetto va adottata la seguente normalizzazione concettuale:

- i riferimenti `.DN` dei timer vanno reinterpretati come `Q`;
- il completamento del contatore va reinterpretato come `Q` del `CTU`;
- il reset del contatore non va modellato come istruzione separata `RES`, ma tramite il pin `R` del `CTU`.

### 48.3 Stato della regola

Questa normalizzazione è da considerare **corretta sul piano del dialetto TIA/IEC**, ma **non ancora sufficiente da sola** a rendere importabile l'intera FC complessa.

Quindi va classificata come:

- regola semantica corretta;
- ma non ancora prova sufficiente di importabilità globale.

---

## 49. Diagnosi attuale del problema sulla FC completa

Alla luce di tutti i test, la diagnosi più onesta e utile è questa.

### 49.1 Cosa è già escluso

Sono stati sostanzialmente esclusi come causa unica:

- il semplice contenitore `SW.Blocks.FC`;
- la sola presenza di `GlobalDB`;
- la sola presenza di `TON/TOF/CTU`;
- la sola correzione dei namespace;
- la sola normalizzazione `.DN -> Q`.

### 49.2 Cosa resta come causa più probabile

Le cause più probabili rimaste sono una o più fra queste:

1. uso di pattern LAD non ancora direttamente ancorati a un export reale TIA;
2. presenza di bit scritti con ruoli misti (bobina normale più `S/R`);
3. più bobine normali verso lo stesso operando in forma non sufficientemente conservativa;
4. combinazione nella stessa FC di:
   - latch `S/R`;
   - timer IEC;
   - contatore IEC;
   - OR;
   - reset multipli;
   senza una suite progressiva di pattern convalidati.

### 49.3 Conseguenza progettuale

Non conviene più usare la strategia:

> genero la FC completa e correggo a posteriori.

Conviene invece adottare la strategia:

> valido micro-pattern LAD, poi compongo solo pattern già confermati.

---

## 50. Strategia di validazione aggiornata per il backend FC

La strategia corretta del progetto, dopo i test odierni, deve diventare esplicitamente incrementale.

### 50.1 Ordine corretto di validazione

1. validare il contenitore `FC` minimale;
2. validare i box IEC (`TON`, `TOF`, `CTU`);
3. validare i latch base (`SCoil`, `RCoil`);
4. validare i reset multipli;
5. validare l'OR verso bobina;
6. validare eventuali doppie scritture dello stesso bit;
7. validare un mini-sequenziatore con due step e un timer;
8. solo alla fine comporre la FC completa.

### 50.2 Nuova definizione di “pattern consolidato”

Nel backend FC, un pattern può essere considerato consolidato solo se soddisfa tre condizioni:

1. esiste almeno un tipico reale o un micro-tipico coerente che lo mostra;
2. il serializer è capace di emetterlo in modo deterministico;
3. il pattern è stato almeno una volta verificato in un contesto di import riuscito o in una famiglia di file chiaramente esportati da TIA.

---

## 51. Nuova suite minima di micro-tipici consigliata

Per uscire dall'attuale stallo sulla FC completa, la suite minima consigliata è la seguente.

### 51.1 Tipici minimi da consolidare

1. `FC_SR_Basic`
   - `Contact -> SCoil`
   - `Contact -> RCoil`

2. `FC_SR_StepTransfer`
   - una condizione che setta lo step successivo e resetta lo step precedente

3. `FC_ResetMulti`
   - una singola condizione che pilota più `RCoil`

4. `FC_DoubleCoilSameOperand`
   - due rami o due reti che scrivono la stessa bobina normale

5. `FC_OR_To_Coil`
   - OR reale verso una sola bobina

6. `FC_TON_SR_Sequence`
   - mini-sequenza a due step con `TON.Q` che causa il trasferimento di stato

7. `FC_CTU_Batch`
   - `CTU.Q` che pilota un bit di batch/completamento

8. `FC_AllGlobalOperands`
   - pattern LAD misti ma con operandi nel `GlobalDB`

### 51.2 Obiettivo della suite

Lo scopo non è avere esempi grandi, ma **isolare il primo costrutto che rompe l'import**.

---

## 52. Aggiornamento dell'architettura del tool

L'architettura generale del progetto resta a tre backend, ma il backend FC va raffinato ulteriormente.

### 52.1 Architettura aggiornata

`AWL -> parser -> estrazione pattern -> IR sequenza + IR dati + IR reti -> validator -> GRAPH compiler + GlobalDB compiler + FC compiler -> test import TIA`

### 52.2 Raffinamento specifico del backend FC

Il backend FC deve ora essere diviso logicamente in quattro sottocomponenti:

1. `fc_ir_builder`
   - costruisce l'IR delle reti LAD

2. `fc_pattern_validator`
   - valida che la rete appartenga a un sottoinsieme di pattern noti

3. `fc_xml_serializer`
   - emette `SW.Blocks.FC`, `CompileUnit`, `FlgNet`, `Parts`, `Wires`

4. `fc_semantic_linter`
   - intercetta anomalie di significato o di modellazione

### 52.3 Nuovo ruolo del linter semantico

Il linter semantico del backend FC deve controllare almeno:

- bit scritti sia con coil normali sia con `S/R`;
- scritture multiple della stessa bobina normale;
- timer o contatori non coerenti con i pin IEC reali;
- operandi duplicati in pattern combinatori;
- reset multipli sospetti;
- passaggi di stato non conservativi.

---

## 53. Stato consolidato finale al termine della giornata

Lo stato corretto e aggiornato del progetto, alla fine di questa giornata di lavoro, è il seguente.

### 53.1 Sul GRAPH

Restano consolidate le regole già fissate in precedenza:

- `GRAPH V2` come target;
- `FB` autosufficiente per topologia, `Temp`, `Static` e runtime;
- `GlobalDB` companion ammesso per gli operandi logici delle transition, purché referenziati in modo simbolico esplicito;
- distinzione netta tra parallelismo topologico GRAPH e OR nel LAD della transition.

### 53.2 Sul `GlobalDB`

Restano consolidate le regole già validate:

- serializer ricorsivo tree-based;
- namespace locale corretto su `Sections`;
- commenti visibili in TIA con forma semplice `Comment + MultiLanguageText`;
- supporto a `IEC_TIMER` e `IEC_COUNTER` con `Version="1.0"`.

### 53.3 Sul backend FC

Lo stato corretto è il seguente:

1. `fc_1.xml` consolida la grammatica generale del backend FC;
2. `fc_2.xml` consolida la grammatica dei box IEC standard;
3. `fc_3.xml` consolida o comunque rende osservabili i pattern LAD minimi su `S/R`, reset multipli, OR e bobine;
4. il test minimale `GlobalDB + FC` con box IEC è riuscito;
5. la FC completa del sequenziatore non è ancora consolidata come importabile;
6. il problema residuo non è più generico, ma riguarda la composizione controllata di pattern LAD complessi.

### 53.4 Decisione progettuale finale da fissare

La decisione più importante da considerare fissata è questa:

**il backend FC del progetto va sviluppato con la stessa disciplina del backend GRAPH: pattern osservati, IR esplicito, validator strutturale, linter semantico e progressione per casi minimi.**

Non è più ragionevole trattare la generazione di FC come emissione libera di XML LAD.

---

## 54. Prossimi passi consigliati dopo l'aggiornamento odierno

I prossimi passi più utili sono i seguenti.

1. analizzare in modo sistematico tutti i nuovi tipici FC caricati e classificarli per pattern;
2. costruire una matrice `pattern LAD -> tipico di riferimento -> stato validazione`;
3. implementare i micro-generatori per ciascun pattern elementare;
4. aggiungere un validator/linter che blocchi la generazione di pattern non ancora consolidati;
5. ricomporre solo dopo una FC completa a partire da pattern già convalidati;
6. aggiornare successivamente anche il report generale del progetto con una matrice di regressione formale.

---

## 55. Uso consigliato di questo report aggiornato

Questo file va ora usato come:

1. **baseline tecnica consolidata** per il progetto `04-225`;
2. riferimento per il disegno del tool Python a tre backend;
3. checklist operativa per evitare regressioni su GRAPH, DB e FC;
4. documento guida per decidere quali nuovi tipici raccogliere;
5. base per il prossimo report, che dovrà includere una vera matrice di validazione dei pattern FC.


---

# PARTE D - CHIUSURA DEL CICLO DI VALIDAZIONE FC E IMPORT RIUSCITO DELLA FC COMPLETA

---

## 56. Obiettivo della nuova estensione del report

Questa estensione aggiorna in modo sostanziale lo stato del backend `FC` LAD del progetto.

Nel report precedente era stato fissato correttamente che:

- il backend FC era grammaticalmente compreso su `fc_1.xml`;
- i box IEC erano compresi su `fc_2.xml`;
- i pattern LAD elementari erano osservabili tramite `fc_3.xml`;
- la FC completa del sequenziatore **non era ancora** da considerare consolidata come importabile.

Questa formulazione va ora aggiornata, perché i test successivi hanno portato a un risultato diverso:

**la FC completa del sequenziatore è stata infine rigenerata con successo in forma importabile (`FC_StationSequence_v8.xml`) e viene ora considerata importata correttamente in TIA Portal V20.**

Conseguenza:

il backend FC del progetto non è più soltanto “parzialmente compreso”, ma ha raggiunto una prima validazione pratica end-to-end su una FC reale e non banale.

---

## 57. Nuovo corpus FC consolidato

Alla fine dell'ultima sessione, il corpus di riferimento per il backend FC deve essere considerato composto da quattro livelli distinti.

### 57.1 `fc_1.xml` - grammatica generale del blocco FC
`fc_1.xml` resta il tipico che consolida:

- il contenitore `SW.Blocks.FC`;
- la struttura `CompileUnit -> NetworkSource -> FlgNet`;
- il supporto a `Contact`, `Coil`, `SCoil`, `RCoil`, `O`, `Call`;
- i riferimenti a `GlobalVariable`;
- il ruolo dell'FC come blocco di orchestrazione o servizio.

### 57.2 `fc_2.xml` - grammatica dei box IEC
`fc_2.xml` resta il tipico che consolida:

- `TON`;
- `TOF`;
- `CTU`;
- le `Instance` interne ai box IEC;
- `PT` come `TypedConstant` per i timer;
- `PV` come `LiteralConstant Int` per il contatore;
- `OpenCon` sui pin non usati.

### 57.3 `fc_3.xml` - pattern LAD elementari
`fc_3.xml` consolida o rende osservabili in modo diretto:

- `Contact -> SCoil`;
- `Contact -> RCoil`;
- trasferimento di step con una stessa condizione che pilota `S` e `R`;
- reset multipli pilotati dalla stessa condizione;
- OR verso bobina;
- doppia coil normale sullo stesso operando.

### 57.4 Micro-tipici generati e verificati
I micro-test generati durante il debug hanno avuto un ruolo decisivo.

Sono da considerare parte della suite di regressione del progetto almeno i seguenti file:

- `FC_SR_Basic_GlobalDB.xml`
- `FC_StepTransfer_GlobalDB.xml`
- `FC_ResetMulti_Local.xml`
- `FC_DoubleCoilSameOperand_Local_v2.xml`
- `FC_OR_To_Coil_Local_v2.xml`
- `FC_Mixed_NoTimers_Local_v2.xml`
- `FC_ResetMulti_Global_v2.xml`
- `FC_DoubleCoilSameOperand_Global_v2.xml`
- `FC_OR_To_Coil_Global_v2.xml`
- `FC_Mixed_NoTimers_Global_v2.xml`
- `FC_TON_SR_Sequence_Local_v2.xml`
- `FC_CTU_Batch_Local_v2.xml`
- `FC_TON_SR_Sequence_Global_v2.xml`
- `FC_CTU_Batch_Global_v2.xml`

### 57.5 Conseguenza progettuale
Il backend FC non è più validato solo su pochi tipici “grandi”, ma su una vera **suite progressiva di micro-pattern**.

Questa è una differenza decisiva rispetto allo stato del report precedente.

---

## 58. Sequenza reale del debug che ha portato alla soluzione

Il percorso che ha portato all'import riuscito della FC completa va fissato con precisione, perché è metodologicamente rilevante.

### 58.1 Fase iniziale: fallimento delle FC complete monolitiche
Le prime varianti della FC completa (`v1` ... `v7`, incluse varianti bisecate e con namespace corretti) non risultavano importabili.

Le correzioni via via introdotte avevano riguardato:

- `ID` globali;
- namespace;
- riferimenti al DB;
- forma dei box IEC;
- normalizzazione `.DN -> Q`.

Tuttavia questi interventi, da soli, non erano sufficienti.

### 58.2 Fase di diagnostica: esclusione dei falsi colpevoli
I test successivi hanno permesso di escludere come causa unica:

- il contenitore `SW.Blocks.FC`;
- il solo uso di `GlobalVariable`;
- il solo uso di `TON/CTU`;
- il solo uso di `S/R`;
- il solo uso di OR;
- la sola presenza di doppie bobine normali;
- la sola presenza di reset multipli;
- la sola assenza/presenza di DB già importato.

### 58.3 Fase decisiva: confronto con i tipici reali
Il problema è stato progressivamente ricondotto a una sola diagnosi ragionevole:

**la FC completa non falliva per colpa dei pattern singoli, ma per il modo in cui venivano composti o serializzati.**

Questa diagnosi è stata confermata dal fatto che i pattern elementari hanno iniziato a importare uno per uno.

### 58.4 Fase finale: ricomposizione della FC completa con soli pattern validati
La soluzione è arrivata solo dopo aver ricostruito la FC completa usando **esclusivamente** pattern già verificati in import riuscito o osservati in tipici reali.

Questo ha portato alla generazione della variante finale:

- `FC_StationSequence_v8.xml`
- `DB_FC_StationSequence_v8.xml`

con import riuscito della FC completa.

---

## 59. Regole nuove emerse dai micro-test sui pattern LAD di base

Le prove sui micro-pattern hanno trasformato molte ipotesi in regole consolidate.

### 59.1 Reset multipli
Il pattern:

- una condizione;
- più `RCoil`;

è da considerare valido e importabile.

Quindi reset multipli della stessa famiglia di step o bit non sono da evitare a priori.

### 59.2 Doppia bobina normale sullo stesso operando
Il pattern di doppia coil verso lo stesso bit è risultato importabile, ma con una precisazione fondamentale:

**il serializer deve duplicare anche gli `Access` dell'operando di destinazione**, seguendo la forma osservata in `fc_3.xml`, e non riusare un singolo `Access` condiviso in maniera “logicamente equivalente”.

Questa è una regola molto importante.

### 59.3 OR verso bobina
Il pattern OR è risultato importabile solo dopo l'allineamento letterale con il tipico.

Regola hard:

```xml
<Part Name="O" ...>
  <TemplateValue Name="Card" Type="Cardinality">2</TemplateValue>
</Part>
```

La forma errata con `Name="Cardinality"` va considerata da evitare.

### 59.4 Pattern misti senza IEC
La composizione di:

- `S/R`
- reset multipli
- OR
- doppia coil

in uno stesso FC è risultata importabile.

Conseguenza:

il backend FC può comporre pattern LAD elementari complessi, purché la serializzazione di ciascun pattern sia fedele ai tipici validati.

---

## 60. Regole nuove emerse dai micro-test sui box IEC

Anche il fronte IEC è stato chiarito in modo molto più preciso.

### 60.1 Uso diretto di `Q` del box e uso mediato
Una prima modellazione troppo “forzata” di:

- `TON.Q -> S/R`
- `CTU.Q -> S`

non risultava importabile.

La forma che ha funzionato è più conservativa:

1. il box IEC produce `Q`;
2. `Q` viene materializzato su un BOOL tramite una `Coil` normale;
3. tale BOOL entra poi in una rete separata con `S/R`.

### 60.2 Regola consolidata per comporre IEC e LAD
La regola da fissare è questa:

**quando un box IEC deve influenzare una logica di latch o di trasferimento di stato, il pattern più robusto è `IEC box -> BOOL -> rete S/R`, non la fusione aggressiva di tutto nello stesso box/rete.**

### 60.3 Conseguenza pratica
Per il compilatore FC, i timer e i contatori vanno trattati come **micro-componenti** del flusso, non come semplici nodi da saldare liberamente a qualsiasi topologia di rete.

---

## 61. Variabili globali: esito finale dei test

Un altro dubbio importante è stato definitivamente risolto.

### 61.1 Risultato osservato
Sono risultati importabili micro-test con:

- `GlobalVariable` semplici;
- pattern LAD base su variabili globali;
- pattern misti globali;
- box IEC con variabili globali;
- istanze IEC nel DB companion.

### 61.2 Regola consolidata
Le `GlobalVariable` **non sono un problema di import**.

La regola corretta non è:

> per importare conviene restare sempre su `LocalVariable`.

La regola corretta è:

> usare simboli esplicitamente risolvibili; locali o globali è una scelta architetturale, non un vincolo rigido di import.

### 61.3 Osservazione importante sul DB
È stato inoltre verificato che, ai fini del **solo import dell'FC**, il `GlobalDB` non deve necessariamente essere già presente.

Se manca, TIA può segnalare errori simbolici o semantici, ma non necessariamente rifiuta l'import XML della FC.

Questa distinzione va fissata nel progetto:

- **importabilità XML**
- **coerenza semantica/simbolica post-import**

non sono la stessa cosa.

---

## 62. Regole nuove sul `GlobalDB` companion per gli FC

I test sui DB di supporto agli FC hanno chiarito alcuni punti.

### 62.1 Il DB deve aderire letteralmente alla grammatica validata
Quando il `GlobalDB` companion non importava, il problema non era la logica PLC ma la forma strutturale del DB.

Regola consolidata:

- `Document` senza `ns0:`;
- `SW.Blocks.GlobalDB`;
- `ProgrammingLanguage = DB`;
- `Sections` con namespace locale;
- `Section Name="Static"`;
- `ObjectList` standard con `Comment` e `Title`.

### 62.2 Supporto a istanze IEC
Il `GlobalDB` companion può e deve contenere, quando necessario:

- `IEC_TIMER Version="1.0"`
- `IEC_COUNTER Version="1.0"`

Queste istanze sono pienamente legittime nella strategia FC.

### 62.3 Ruolo corretto del DB nel backend FC
Il DB companion per l'FC non è sempre obbligatorio per testare l'importabilità, ma resta molto utile per:

- simboli applicativi persistenti;
- bit di stato esterni;
- istanze IEC;
- integrazione impiantistica;
- compatibilità con il modello dati reale del sequenziatore.

---

## 63. Nuovo stato consolidato del backend FC dopo l'import della `v8`

Questa sezione sostituisce lo stato precedente più prudente.

### 63.1 Stato corretto aggiornato
Lo stato corretto del backend FC, alla fine di questa fase, è il seguente:

1. `fc_1.xml` consolida la grammatica generale del backend FC;
2. `fc_2.xml` consolida la grammatica dei box IEC standard;
3. `fc_3.xml` consolida i pattern LAD minimi su `S/R`, reset multipli, OR e doppia coil;
4. i micro-pattern locali sono stati verificati con import riuscito;
5. i micro-pattern globali sono stati verificati con import riuscito;
6. i pattern IEC locali/globali sono stati verificati con import riuscito in forma conservativa;
7. la FC completa del sequenziatore è stata infine importata con successo nella variante `v8`;
8. il backend FC del progetto può quindi essere considerato **validato in prima forma end-to-end**, pur restando aperta la necessità di formalizzare il tutto in codice generativo stabile.

### 63.2 Nuova formulazione da considerare fissata
La formulazione corretta non è più:

> la FC completa non è ancora consolidata come importabile.

La formulazione corretta diventa:

> la FC completa è stata resa importabile dopo una validazione incrementale dei micro-pattern e una ricomposizione controllata basata esclusivamente su pattern già confermati.

### 63.3 Limite ancora aperto
Il fatto che `v8` importi non significa ancora che il problema generale “AWL -> FC” sia risolto in forma automatica per qualsiasi caso.

Quello che è stato validato è:

- la grammatica XML/LAD;
- la suite di pattern di base;
- la possibilità di ricomporre una FC reale importabile;
- la correttezza del metodo incrementale.

Resta da trasformare tutto questo in:

- IR;
- serializer;
- validator;
- linter;
- regressione automatica.

---

## 64. Significato metodologico della `v8`

La `v8` ha un valore che va oltre il singolo file.

### 64.1 Cosa dimostra davvero
La `v8` dimostra che:

- il problema non era “TIA non accetta FC grandi”;
- il problema non era “i pattern sono sbagliati”;
- il problema non era “servono solo variabili locali”;
- il problema non era “il DB deve esistere prima”.

Dimostra invece che:

**l'importabilità di una FC complessa dipende dalla composizione conservativa di pattern validati e dalla fedeltà letterale del serializer ai tipici reali.**

### 64.2 Conseguenza per il progetto
Questo porta a una decisione metodologica forte:

**il compilatore FC del progetto deve essere costruito come libreria di micro-generatori di pattern, non come generatore monolitico di reti generiche.**

---

## 65. Architettura finale aggiornata del tool

L'architettura complessiva del progetto deve ora essere considerata stabilmente a tre backend, tutti guidati da IR e validator.

### 65.1 Pipeline completa aggiornata
La pipeline concettuale corretta è ormai:

`AWL -> parser -> estrazione macchina a stati + pattern LAD + dati applicativi -> IR comune -> validator -> GRAPH compiler + GlobalDB compiler + FC compiler -> test import TIA -> regressione`

### 65.2 Ruolo del compilatore FC
Il compilatore FC deve essere scomposto almeno in:

1. `fc_ir_builder`
2. `fc_pattern_library`
3. `fc_pattern_validator`
4. `fc_xml_serializer`
5. `fc_semantic_linter`

### 65.3 Pattern library minima da considerare obbligatoria
La libreria minima dei pattern FC deve includere almeno:

- `Contact -> Coil`
- `Contact -> SCoil`
- `Contact -> RCoil`
- `Contact -> S + R`
- `ResetMulti`
- `OR -> Coil`
- `DoubleCoilSameOperand`
- `TON -> BOOL`
- `BOOL -> S/R`
- `CTU -> BOOL`
- `BOOL -> S`

### 65.4 Linter semantico raccomandato
Il linter semantico deve controllare almeno:

- scritture multiple dello stesso bit;
- uso misto di coil normali e `S/R`;
- pattern timer/contatore non composti in forma conservativa;
- variabili duplicate o inutilizzate;
- step transfer non conservativi;
- anomalie di naming o di mapping verso DB.

---

## 66. Checklist finale aggiornata per generare FC importabili

Da questo punto in avanti, quando si genera un FC XML per il progetto, verificare sempre:

1. `Document` senza prefissi aggressivi;
2. `Engineering version="V20"`;
3. `SW.Blocks.FC`;
4. `ProgrammingLanguage = LAD` coerente a livello blocco e rete;
5. `Interface` standard con almeno `Return`;
6. `CompileUnit` ordinate;
7. `FlgNet` con `Parts` e `Wires` coerenti;
8. `UId` coerenti per rete;
9. OR serializzati con `TemplateValue Name="Card" Type="Cardinality"`;
10. doppie coil con `Access` distinti verso lo stesso operando;
11. reset multipli cablati con fan-out esplicito dalla stessa uscita;
12. `TON` e `CTU` come box IEC nativi, non come call generiche;
13. `PT` timer come `TypedConstant`;
14. `PV` contatore come `LiteralConstant Int`;
15. pin non usati verso `OpenCon`;
16. composizione conservativa `IEC -> BOOL -> logica latch`;
17. simboli locali o globali sempre esplicitamente risolvibili;
18. DB companion coerente quando serve, ma non confondere importabilità XML con coerenza simbolica post-import.

---

## 67. Stato finale aggiornato del progetto dopo questa chiusura

Lo stato aggiornato e corretto del progetto è ora il seguente.

### 67.1 Sul GRAPH
Restano valide tutte le regole già consolidate per:

- `GRAPH V2`;
- `FB` autosufficiente;
- `Temp`, `Static`, runtime e topologia;
- companion DB opzionale per gli operandi logici delle transition.

### 67.2 Sul `GlobalDB`
Restano valide tutte le regole già consolidate su:

- serializer ricorsivo tree-based;
- namespace locale su `Sections`;
- commenti campo visibili;
- `IEC_TIMER` e `IEC_COUNTER` con `Version="1.0"`.

### 67.3 Sul backend FC
La situazione aggiornata è ora:

- grammatica FC compresa;
- box IEC compresi;
- pattern LAD elementari compresi;
- pattern locali e globali compresi;
- composizione conservativa con IEC compresa;
- FC completa importata correttamente.

### 67.4 Decisione progettuale finale ora da considerare fissata
La decisione più importante da considerare fissata, dopo l'import riuscito della `v8`, è la seguente:

**il backend FC del progetto è realizzabile in modo affidabile, ma solo se viene costruito come sistema pattern-driven, validator-driven e serializer-driven, con progressione incrementale dai micro-pattern alla FC completa.**

---

## 68. Prossimi passi consigliati dopo questo aggiornamento

I prossimi passi più utili non sono più test manuali ad hoc, ma attività di consolidamento ingegneristico:

1. trasformare tutti i micro-pattern validati in codice del serializer FC;
2. costruire una vera matrice `pattern -> tipico -> stato -> test file`;
3. implementare il `fc_pattern_validator`;
4. implementare il `fc_semantic_linter`;
5. derivare dall'AWL una IR che distingua:
   - sequenza esplicita da portare in GRAPH;
   - logica di servizio/orchestrazione da portare in FC;
   - dati applicativi da portare in `GlobalDB`;
6. creare una suite automatica di regressione per:
   - GRAPH;
   - `GlobalDB`;
   - FC;
7. valutare, in una fase successiva, l'automazione con Openness end-to-end.

---

## 69. Uso consigliato di questo report aggiornato

Questo file, dopo questa ulteriore estensione, va usato come:

1. baseline tecnica aggiornata e completa del progetto;
2. riferimento per la futura implementazione del tool Python a tre backend;
3. documento di regressione per non perdere le regole emerse dai tipici FC;
4. memoria tecnica del percorso che ha portato dalla FC non importabile alla `v8` importabile;
5. base per il prossimo report, che dovrà contenere preferibilmente una matrice formale dei pattern FC e dei test associati.


---

# PARTE E - TEST INTEGRATI DB + GRAPH + FC E PRINCIPIO DI UNIVERSALITÀ DEL GENERATORE

---

## 70. Correzione metodologica importante

Questa sezione corregge esplicitamente una possibile lettura fuorviante della fase più recente.

I file:

- `DB_GraphDemo_10T.xml`
- `GRAPH_Demo_10T.xml`
- `FC_ActivateGraphTransitions.xml`
- `DB_GraphDemo_20T_v3.xml`
- `GRAPH_Demo_20T_v4_from10.xml`
- `FC_ActivateGraphTransitions_20T_v3.xml`

**non devono essere interpretati come template “finali” del generatore**.

Devono essere interpretati come:

- casi di test;
- esempi di regressione;
- prove controllate di import;
- strumenti per isolare vincoli strutturali del serializer.

Questa precisazione è fondamentale.

L’obiettivo del progetto **non è** costruire un generatore specializzato per:
- 10 transition,
- 20 transition,
- 50 transition,
- o per pochi esempi tipici preconfezionati.

L’obiettivo corretto è costruire un **generatore universale**, cioè capace di:

1. ricevere una rappresentazione intermedia astratta della sequenza;
2. validarla rispetto ai vincoli del target TIA;
3. scegliere solo pattern topologici e serializer ammessi;
4. emettere un XML importabile per un insieme ampio di casi, non per pochi esempi statici.

---

## 71. Significato corretto dei test a 10 / 20 / 50 transition

I test a 10, 20 e 50 transition hanno avuto valore diagnostico, ma non devono spostare il focus del progetto.

### 71.1 Cosa servivano a fare
Servivano a rispondere a domande precise:

- il `GlobalDB` companion può essere generato in modo coerente?
- un `FC` può attivare le transition di un `GRAPH` tramite variabili globali?
- un `GRAPH` più grande fallisce per il numero di transition o per un errore topologico/strutturale?
- quali parti del serializer restano affidabili quando il caso cresce?

### 71.2 Cosa non dimostrano da sole
Non dimostrano che il generatore debba essere costruito come:
- “replica del 10T”;
- “estensione lineare del 20T”;
- “template fisso del 50T”.

Il valore dei test è un altro:
- isolare vincoli;
- validare pattern;
- misurare robustezza del metodo;
- evitare regressioni.

### 71.3 Decisione da considerare fissata
Da questo punto in avanti, nel progetto, ogni esempio numerico di dimensione (`10T`, `20T`, `50T`, ecc.) va classificato come:

**caso di test del generatore universale**, non come forma speciale del generatore stesso.

---

## 72. Architettura corretta del generatore universale GRAPH

Alla luce del contesto di progetto e dei test svolti, il generatore GRAPH non deve essere modellato come un sistema che “allunga” un XML esempio.

Deve essere modellato come pipeline generale composta da:

1. `graph_ir_builder`
2. `graph_topology_validator`
3. `graph_pattern_selector`
4. `graph_static_builder`
5. `graph_transition_logic_builder`
6. `graph_xml_serializer`
7. `graph_import_regression_tests`

### 72.1 `graph_ir_builder`
Costruisce una rappresentazione astratta del GRAPH indipendente dal formato XML.

Questa IR deve contenere almeno:
- step;
- transition;
- condizioni di transition;
- branch alternativi;
- branch paralleli;
- join;
- eventuali loop;
- metadati minimi runtime.

### 72.2 `graph_topology_validator`
Valida la topologia della sequenza prima della serializzazione.

Deve controllare almeno:
- un solo punto iniziale;
- coerenza ingressi/uscite di step e transition;
- uso corretto di `AltBegin`, `SimBegin`, `SimEnd`;
- assenza di merge illegali;
- presenza di join espliciti nei casi complessi;
- compatibilità con il sottoinsieme topologico realmente ammesso dai tipici validati.

### 72.3 `graph_pattern_selector`
Questo punto è centrale.

Il generatore universale non deve “inventare” topologie nuove se non validate.
Deve invece:
- riconoscere la forma astratta dell’IR;
- scegliere la decomposizione in pattern ammessi;
- comporre il GRAPH usando solo pattern già validati.

Quindi i `Type_*.xml` e i file validi già ottenuti vanno trattati come:
- libreria di pattern;
- corpus di regressione;
- base per il selettore di pattern,
non come template rigidi da copiare meccanicamente.

### 72.4 `graph_static_builder`
Costruisce:
- `Static`;
- `RT_DATA`;
- member `Step*`;
- member `Trans*`;
- eventuali operandi di appoggio.

Questo builder deve essere guidato dall’IR e dai pattern scelti, non da un numero fisso di transition.

### 72.5 `graph_transition_logic_builder`
Genera il `FlgNet` delle transition usando il sottoinsieme sicuro già validato:
- `Access`;
- `Contact`;
- `Contact` negato;
- `O`;
- comparatori validati;
- `TrCoil`.

### 72.6 `graph_xml_serializer`
Serializza il blocco `SW.Blocks.FB` completo, rispettando:
- root `Document` pulita;
- namespace locali;
- `Interface` corretta;
- `Static` bilanciato;
- `Sequence` coerente;
- `ObjectList` coerente;
- pattern topologici ammessi.

### 72.7 `graph_import_regression_tests`
La regressione automatica deve includere:
- esempi piccoli;
- esempi medi;
- esempi con alternative;
- esempi con paralleli;
- esempi con join;
- casi coordinati `DB + GRAPH + FC`.

---

## 73. Uso corretto dei file di test generati in questa fase

I file generati in questa fase devono essere classificati in tre categorie.

### 73.1 Test coordinati di integrazione
Per esempio:
- `DB_GraphDemo_10T.xml`
- `GRAPH_Demo_10T.xml`
- `FC_ActivateGraphTransitions.xml`

Servono a dimostrare che i tre backend possono convivere.

### 73.2 Test di scaling
Per esempio:
- `GRAPH_Demo_20T*`
- `GRAPH_Demo_50T*`

Servono a capire:
- se una topologia resta valida quando cresce;
- dove il serializer esce dal profilo sicuro;
- come si comporta TIA su casi più grandi.

### 73.3 Test di regressione del serializer
Le versioni corrette di DB e FC generate durante il debug servono a evitare regressioni future:
- `DB_GraphDemo_20T_v3.xml`
- `FC_ActivateGraphTransitions_20T_v3.xml`

Anche qui il principio resta:
questi file non sono il generatore;
sono prove di correttezza del generatore.

---

## 74. Lezione emersa dalla fase GRAPH 20/50

Questa fase ha prodotto una lezione molto importante per il progetto.

### 74.1 Errore metodologico da evitare
L’errore metodologico è pensare:
> se un GRAPH piccolo importa, basta scalarlo aggiungendo step e transition.

Questo non è sufficientemente sicuro.

Perché:
- la topologia può uscire dal sottoinsieme valido;
- il runtime può diventare incoerente;
- i join possono diventare non conformi;
- il `Static` può non restare allineato;
- TIA può rifiutare l’import o addirittura reagire male a una topologia non robusta.

### 74.2 Correzione metodologica
La strategia corretta è:

- costruire una IR generale;
- validarla;
- scegliere pattern topologici consentiti;
- serializzare solo combinazioni già autorizzate dal validator.

Quindi i test numerici devono guidare il validator, non guidare la forma finale del generatore.

---

## 75. Nuova formulazione da considerare fissata per il backend GRAPH

La formulazione corretta, dopo questa fase, è la seguente:

> Il backend GRAPH deve essere universale, ma non “libero”.
> Deve essere universale **entro un insieme esplicitamente validato di pattern topologici, strutturali e di serializer**.

Questa frase è importante perché evita due estremi sbagliati:

- generatore troppo rigido, cucito su pochi esempi;
- generatore troppo libero, che inventa topologie non garantite.

La posizione corretta del progetto è nel mezzo:
**generatore universale, ma constraint-driven e pattern-driven.**

---

## 76. Integrazione del principio di universalità con FC e GlobalDB

Lo stesso principio vale anche per gli altri backend.

### 76.1 FC
Il backend FC non va visto come:
- collezione di pochi XML funzionanti.

Va visto come:
- libreria di micro-pattern;
- validator di composizione;
- serializer generale che usa solo pattern ammessi.

### 76.2 GlobalDB
Il backend GlobalDB non va visto come:
- copia di `db_1.xml` con nomi cambiati.

Va visto come:
- serializer ricorsivo generale;
- con grammatica fissa,
- ma contenuto arbitrario derivato dall’IR.

### 76.3 Coerenza complessiva
L’architettura corretta del progetto è quindi:

- IR comune;
- selezione backend;
- validator dedicati;
- serializer dedicati;
- suite di regressione.

I file esempio validati servono come:
- prove;
- ancore;
- oracoli di regressione.

Non come scorciatoie per rinunciare all’universalità.

---

## 77. Stato finale aggiornato dopo questa fase

Dopo questa ulteriore fase, lo stato corretto del progetto è:

1. il backend FC è validato su casi reali e micro-pattern;
2. il backend GlobalDB è validato come serializer tree-based;
3. il backend GRAPH è validato su casi significativi, ma la fase di scaling ha mostrato che la generazione deve restare strettamente guidata dal contesto e dai pattern topologici consentiti;
4. i test integrati `DB + GRAPH + FC` sono utili e vanno mantenuti;
5. il generatore da realizzare deve essere universale, ma universale nel senso corretto:
   - input generale;
   - output valido entro vincoli;
   - nessuna dipendenza da pochi template rigidi;
   - nessuna libertà di inventare strutture non validate.

---

## 78. Prossimo passo consigliato

Il prossimo passo più utile, dopo questo aggiornamento, non è generare altri esempi numerici casuali.

Il prossimo passo corretto è formalizzare:

1. la libreria di pattern topologici GRAPH validi;
2. la matrice `pattern -> vincoli -> serializer`;
3. il validator topologico;
4. la distinzione IR tra:
   - sequenza lineare,
   - branch alternativo,
   - branch parallelo,
   - join,
   - loop;
5. le regole di composizione ammesse tra pattern.

Solo dopo questa formalizzazione ha senso scalare in modo affidabile a casi molto grandi.


---

# PARTE F - CHIUSURA GIORNATA (ESCLUDENDO LA PARTE GRAPH, SU RICHIESTA)

---

## 79. Criterio di aggiornamento di questa revisione

Questa revisione del report viene aggiornata **escludendo volutamente tutta la parte relativa ai GRAPH** sviluppata nella parte finale della giornata.

La scelta è esplicita e intenzionale:
- i tentativi, le varianti e i test sui GRAPH non vengono consolidati in questa versione;
- non vengono quindi promossi a baseline;
- non vengono usati per derivare nuove regole hard del generatore.

Questa revisione deve quindi essere letta come:

- continuazione della baseline già consolidata;
- aggiornamento del metodo;
- ma **senza incorporare le prove GRAPH della parte finale della giornata**.

---

## 80. Stato consolidato che resta valido senza modifiche

Escludendo la parte GRAPH, lo stato consolidato del progetto **non cambia** nei suoi punti forti principali.

Restano validi e confermati:

### 80.1 Backend FC
Il backend FC resta il punto più maturo e meglio validato del progetto.

Sono da considerare consolidati:
- il contenitore `SW.Blocks.FC`;
- i pattern LAD di base;
- la libreria di micro-pattern;
- la validazione su variabili locali e globali;
- il supporto ai box IEC in forma conservativa;
- l’import riuscito della FC completa del sequenziatore nella variante `v8`.

Questa parte del progetto non subisce revisioni negative in questa chiusura giornaliera.

### 80.2 Backend GlobalDB
Il backend `GlobalDB` resta consolidato come serializer tree-based, con grammatica fissa e contenuto guidato dall’IR.

Restano valide:
- struttura `SW.Blocks.GlobalDB`;
- `ProgrammingLanguage = DB`;
- `Sections` con namespace locale;
- sezione `Static`;
- commenti e `StartValue` per tipi semplici;
- supporto a `IEC_TIMER` e `IEC_COUNTER` nei casi necessari.

### 80.3 Impostazione metodologica generale
Resta confermata la decisione metodologica principale del progetto:

- generatore universale;
- ma universale in forma **pattern-driven**, **constraint-driven** e **validator-driven**.

Questa parte è anzi ulteriormente da considerare rafforzata come principio di lavoro.

---

## 81. Chiarimento metodologico importante da fissare

Una lezione importante emersa oggi, indipendentemente dai GRAPH, è che il progetto deve essere gestito distinguendo sempre tra:

1. **casi di test**
2. **pattern validati**
3. **regole del generatore**
4. **baseline consolidata**

Questa distinzione va mantenuta rigorosamente.

### 81.1 Casi di test
I file prodotti per stressare il sistema o per verificare ipotesi non sono automaticamente baseline.

### 81.2 Pattern validati
Un pattern diventa realmente riusabile solo dopo:
- verifica strutturale;
- import riuscito;
- confronto con i tipici;
- coerenza con il report.

### 81.3 Regole del generatore
Le regole del generatore devono essere derivate:
- dal corpus valido;
- dal report;
- dai test riusciti;
- non da tentativi isolati.

### 81.4 Baseline consolidata
La baseline consolidata deve restare prudente:
si promuove a baseline solo ciò che è davvero stabile.

---

## 82. Regola operativa da mantenere da ora in avanti

Da questa giornata va considerata fissata una regola pratica molto importante:

**prima di generare, rileggere sempre il report e la specifica consolidata del progetto.**

Questo non è un dettaglio organizzativo, ma un requisito tecnico.

Perché:
- evita di reintrodurre errori già esclusi;
- evita di uscire dal sottoinsieme valido dei pattern;
- riduce i tentativi inutili;
- mantiene il lavoro coerente con il carattere universale del generatore.

Questa regola va intesa come parte del metodo di lavoro del progetto.

---

## 83. Stato finale della baseline dopo questo aggiornamento

Dopo questa revisione, che esclude la parte GRAPH finale della giornata, la baseline da considerare valida resta:

### 83.1 Sul FC
- backend FC validato in modo forte;
- micro-pattern e composizione validati;
- supporto a variabili locali/globali;
- supporto ai box IEC in forma conservativa;
- FC completa importata correttamente.

### 83.2 Sul GlobalDB
- serializer stabile;
- forma XML consolidata;
- uso come companion dati coerente.

### 83.3 Sul metodo generale
- IR comune;
- validator;
- selezione di pattern;
- serializer dedicati;
- suite di regressione.

### 83.4 Sul GRAPH
Questa revisione viene **superata** dall'ultimo esito validato della giornata.
La parte GRAPH non va più considerata esclusa: il caso completo di imbottigliamento è stato corretto e importato con successo, quindi entra ufficialmente nella baseline del progetto.

---

## 84. Regola aggiornata per il consolidamento del report

Il criterio corretto da usare da ora in poi è questo:

- includere nel report i tentativi solo quando producono una regola tecnica riutilizzabile;
- promuovere a baseline i file che hanno portato a un import riuscito o a una correzione strutturale confermata;
- mantenere traccia delle versioni intermedie solo come storia tecnica, distinguendole dal file finale validato.

Questo consente di usare il report sia come specifica tecnica sia come memoria delle correzioni che hanno realmente sbloccato l'import in TIA.

---

## 85. Sintesi finale aggiornata di questa revisione

La sintesi corretta, dopo l'ultimo test riuscito, è:

- il progetto ha una baseline forte su GRAPH, FC e GlobalDB;
- il principio di universalità del generatore resta confermato;
- il report va usato come vincolo prima della generazione;
- il caso GRAPH completo di imbottigliamento entra nella baseline come file corretto e importabile;
- la correzione del wrapper esterno del blocco si conferma un punto strutturale decisivo quando l'interno del graph è già coerente.

---

# PARTE E - AGGIORNAMENTO DEL 26-03-2026: NUOVO GRAPH COMPLETO GENERATO

## 58. Nuovo file GRAPH generato in questa sessione

Nell'ultima sessione è stato generato un nuovo blocco GRAPH completo:

- `FB_BottlingLine_GRAPH_strict.xml`
- `FB_BottlingLine_GRAPH_strict_fixed.xml`
- `FB_BottlingLine_GRAPH_strict_rebased.xml`

Questo file rappresenta una linea di imbottigliamento modellata come `SW.Blocks.FB` in `GRAPH V2`, con:

- `GraphVersion = 2.0`;
- `Interface` coerente con namespace locale corretto;
- `Static` comprensiva di:
  - `RT_DATA : G7_RTDataPlus_V2`;
  - un member `G7_TransitionPlus_V2` per ogni transition;
  - un member `G7_StepPlus_V2` per ogni step;
- `Sequence` completa con:
  - `Steps`;
  - `Transitions`;
  - `Branches`;
  - `Connections`;
- transizioni LAD espresse nel sottoinsieme già consolidato del progetto.

## 59. Struttura funzionale del GRAPH di imbottigliamento

Il nuovo GRAPH modella una sequenza completa di linea, con le seguenti macrofasi:

- inizializzazione / standby;
- ricerca bottiglia;
- posizionamento bottiglia;
- gestione allarme di posizionamento e reset verso init;
- blocco bottiglia;
- riempimento;
- gestione allarme di riempimento e reset verso init;
- stabilizzazione;
- discesa testa di tappatura;
- tappatura;
- gestione allarme di tappatura e reset verso init;
- risalita testa;
- sblocco bottiglia;
- uscita bottiglia;
- gestione allarme uscita e reset verso init;
- conteggio finale con loop automatico oppure ritorno all'inizializzazione.

## 60. Caratteristiche topologiche confermate nel nuovo file

L'esito complessivo della famiglia `FB_BottlingLine_GRAPH_strict*` conferma nella pratica diverse regole già consolidate nel progetto:

1. le alternative di esito e timeout sono realizzate con `AltBegin`;
2. gli step di allarme rientrano verso l'inizio tramite `Jump`;
3. ogni step mantiene una sola uscita diretta verso transition o branch;
4. ogni transition mantiene una sola uscita;
5. non vengono introdotti merge `Direct` multipli su step non iniziali.

## 61. Forma delle transition nel nuovo GRAPH

Le transition del file generato restano nel sottoinsieme LAD sicuro emerso dal progetto. In particolare si osservano pattern del tipo:

- `Access -> Contact -> TrCoil` per condizioni semplici;
- serie di contatti per AND logici;
- transition di timeout con confronto `Gt` su `Time`;
- assenza di costrutti fuori profilo, come `Part Name="A"`.

Questo rafforza la regola progettuale già fissata:

- `AND = serie`;
- `OR = nodo O`;
- `NOT = contatto negato`;
- confronti di timeout tramite blocchi di confronto coerenti con i tipici validi;
- nessuna topologia ibrida fuori dal dialetto TIA validato.

## 62. Nuovo stato consolidato del backend GRAPH

Dopo questa generazione, il backend GRAPH del progetto va considerato consolidato non solo sui micro-casi e sugli stress test già prodotti, ma anche su un ulteriore caso applicativo completo di sequenza macchina.

Di conseguenza, il corpus pratico dei GRAPH generati dal progetto deve ora includere anche:

- `FB_BottlingLine_GRAPH_strict.xml`

oltre ai graph già generati e raccolti nei report precedenti.

Tra questi file, quello da considerare baseline valida è:

- `FB_BottlingLine_GRAPH_strict_rebased.xml`

Mentre le versioni intermedie restano utili come storia tecnica della correzione:

- `FB_BottlingLine_GRAPH_strict.xml` = prima versione generata;
- `FB_BottlingLine_GRAPH_strict_fixed.xml` = tentativo di riallineamento dell'intestazione, non ancora sufficiente;
- `FB_BottlingLine_GRAPH_strict_rebased.xml` = versione finale corretta, importata con successo.

## 63. Effetto sul tool Python

Questo aggiornamento non cambia la direzione architetturale già fissata, ma la rafforza:

- il backend GRAPH deve restare `IR-driven`;
- il serializer deve restare `grammar-driven`;
- il validator topologico resta obbligatorio;
- il compilatore delle transition deve rimanere confinato nel sottoinsieme LAD sicuro.

Il nuovo file dimostra che questo approccio non è solo teorico, ma è già in grado di produrre un ulteriore GRAPH applicativo coerente con il corpus del progetto.

## 64. Uso di questo aggiornamento

Questa estensione del report deve essere usata da ora in poi come riferimento anche per:

- la generazione di GRAPH applicativi completi;
- la regressione del backend GRAPH su casi macchina reali;
- il futuro compilatore Python per sequenze di linea imbottigliamento o workflow simili.


## 65. Correzione strutturale riuscita del caso Bottling Line

Il caso `FB_BottlingLine_GRAPH_strict*` ha prodotto una regola molto importante per il tool Python e per le future correzioni manuali.

### 65.1 Sequenza dei file

Sono state prodotte tre versioni principali:

- `FB_BottlingLine_GRAPH_strict.xml`
- `FB_BottlingLine_GRAPH_strict_fixed.xml`
- `FB_BottlingLine_GRAPH_strict_rebased.xml`

### 65.2 Esito dei test

L'esito corretto da fissare nel report è questo:

- la prima versione non importava;
- la versione `fixed` non era ancora sufficiente;
- la versione `rebased` ha importato correttamente.

### 65.3 Correzione decisiva individuata

La correzione vincente non è stata una modifica alla logica del graph interno, ma il riallineamento del **wrapper esterno del blocco** al profilo di un GRAPH già validato in TIA.

In particolare, si è rivelato efficace:

- riallineare `AttributeList` al profilo dei file che importano;
- eliminare differenze non necessarie nel contenitore del blocco;
- riallineare l'ordine e la forma dell'`ObjectList`;
- mantenere invariati `Interface` e `NetworkSource/Graph` quando già coerenti.

### 65.4 Regola progettuale derivata

Questa esperienza introduce una regola forte per il tool Python:

> quando il graph interno è già topologicamente corretto ma il file non importa, il problema può stare nel wrapper `SW.Blocks.FB` / `ObjectList` / `CompileUnit`, non solo in `Steps`, `Transitions`, `Branches` o `Connections`.

### 65.5 Impatto sul backend XML

Il backend XML del tool dovrà quindi validare separatamente due livelli:

1. **wrapper del blocco**
   - `AttributeList`
   - `ObjectList`
   - `CompileUnit`
   - ordine dei nodi
   - presenza/assenza di campi tollerati o indesiderati

2. **contenuto del graph**
   - `Interface`
   - `Static`
   - `Sequence`
   - `Steps`
   - `Transitions`
   - `Branches`
   - `Connections`

### 65.6 Stato finale consolidato

Per il progetto, il file di riferimento di questo caso è ora:

- `FB_BottlingLine_GRAPH_strict_rebased.xml`

Questo file entra ufficialmente tra i GRAPH generati, corretti e validati con successo.


## 66. Correzione strutturale riuscita del caso GateCycle

Anche il caso `FB_GateCycle_GRAPH_v3*` ha confermato la stessa famiglia di regole emersa nel caso Bottling Line.

### 66.1 Sequenza dei file

Sono stati gestiti i seguenti file:

- `FB_GateCycle_GRAPH_v3.xml`
- `FB_GateCycle_GRAPH_v3_rebased.xml`

### 66.2 Esito dei test

L'esito corretto da fissare nel report è questo:

- la versione originale non importava;
- la versione `rebased` ha importato correttamente.

### 66.3 Correzione decisiva individuata

Anche in questo caso la correzione vincente non è stata una modifica della logica del graph interno, ma il riallineamento del wrapper esterno del blocco al profilo dei GRAPH già validati nel progetto.

In particolare si è rivelato efficace:

- rimuovere elementi non necessari o non allineati nel wrapper del blocco;
- riallineare l'ordine della `ObjectList`;
- normalizzare la forma del `CompileUnit`;
- mantenere invariati `Interface` e `NetworkSource/Graph` quando già coerenti.

### 66.4 Regola progettuale derivata

Il caso GateCycle rafforza la regola ormai consolidata:

> se il graph interno è già coerente ma il file non importa, il problema può essere nel wrapper `SW.Blocks.FB` e non nella sequenza GRAPH interna.

### 66.5 Stato finale consolidato

Per il progetto, il file di riferimento di questo caso è ora:

- `FB_GateCycle_GRAPH_v3_rebased.xml`

Questo file entra ufficialmente tra i GRAPH generati, corretti e validati con successo.

## 67. Baseline aggiornata dei GRAPH corretti e importati

Alla data del report, tra i file più significativi corretti e importati con successo rientrano almeno:

- `Graph_pallet_station_parallel_timeout_with_alarm_end.xml`;
- `FB_BottlingLine_GRAPH_strict_rebased.xml`;
- `FB_GateCycle_GRAPH_v3_rebased.xml`;
- i file della famiglia `Graph_TRANS_FWD_*` validati durante la correzione delle transition;
- i GRAPH di stress e di esempio raccolti nelle sezioni precedenti del report.

## 68. Regola finale aggiornata per il tool Python

La situazione consolidata del progetto impone che il tool Python validi e serializzi sempre due livelli distinti:

1. il **contenuto GRAPH interno**:
   - `Interface`;
   - `Static`;
   - `Steps`;
   - `Transitions`;
   - `Branches`;
   - `Connections`;
   - `FlgNet` delle transition;

2. il **wrapper XML del blocco**:
   - `SW.Blocks.FB`;
   - `AttributeList`;
   - `ObjectList`;
   - `CompileUnit`;
   - ordine dei nodi;
   - presenza/assenza dei campi tollerati.

Il backend non può considerare valido un XML solo perché la topologia del graph è corretta: deve anche serializzare il wrapper nel dialetto XML che TIA accetta davvero.

---

## 69. TIA Portal Openness nel progetto

Dalla rilettura della documentazione Siemens disponibile su TIA Portal Openness emerge un insieme di elementi che vanno integrati stabilmente nella visione del progetto, pur tenendo conto che il documento di riferimento disponibile è relativo a TIA Portal Openness V17 e quindi va usato come base concettuale e architetturale, non come prova finale di compatibilità runtime per il target V20.

### 69.1 Conferma del ruolo di Openness nel progetto

La documentazione conferma che TIA Portal Openness è pensato per automatizzare attività di engineering su TIA Portal e che il suo feature set comprende funzioni direttamente rilevanti per questo progetto:

- apertura di una nuova istanza TIA Portal;
- connessione a un'istanza TIA Portal già esistente;
- creazione, apertura, salvataggio e chiusura di progetti;
- navigazione dell'albero logico e fisico del progetto;
- compilazione di elementi del progetto;
- import di elementi come Simatic ML;
- import/export di strutture come Simatic ML;
- aggiunta di sorgenti esterne PLC;
- generazione di blocchi da sorgente esterna;
- generazione di sorgente a partire da blocchi esistenti.

Per il progetto AWL -> GRAPH questo significa che Openness non va considerato solo come accessorio finale, ma come possibile **quarto backend operativo** che automatizza il test loop di validazione del generatore XML.

### 69.2 Prerequisiti e vincoli operativi da fissare nel progetto

Dal materiale Siemens emergono alcuni prerequisiti che devono entrare nella specifica tecnica del layer Openness:

- Openness richiede l'installazione del TIA Portal corrispondente;
- le DLL Openness sono fornite con l'installazione TIA/STEP 7;
- l'applicazione usa le DLL `Siemens.Engineering.*`;
- l'utente Windows deve appartenere al gruppo locale `Siemens TIA Openness`;
- al primo avvio va gestita la finestra di autorizzazione accesso;
- contenuto e disponibilità delle funzioni dipendono anche dai moduli installati;
- la documentazione disponibile segnala esplicitamente che non è garantita compatibilità automatica tra versioni diverse.

Conseguenza pratica:

> il layer Openness del progetto deve essere progettato come **adapter versionato**, da validare esplicitamente sul target TIA Portal V20 e non da assumere come automaticamente portabile dalla documentazione V17.

### 69.3 Due pipeline Openness distinte da non confondere

La documentazione rende chiaro che esistono **due famiglie operative diverse**, entrambe utili al progetto ma con ruoli separati.

#### A. Pipeline Simatic ML / XML

Serve per lavorare con gli XML strutturali TIA.

Operazioni rilevanti:

- `Import Element as Simatic ML`;
- `Import Structure as Simatic ML`;
- `Export Structure as Simatic ML`.

Questa è la pipeline naturale per:

- importare il `FB` GRAPH generato;
- importare il `GlobalDB` companion;
- importare eventuali `FC` di servizio;
- esportare baseline XML da TIA per confronto, regressione e reverse engineering.

#### B. Pipeline PLC external sources

Serve per lavorare con sorgenti PLC testuali.

Operazioni rilevanti:

- `Add external source`;
- `Generate blocks from external source`;
- `Generate source from block`.

I formati citati nella documentazione per le external source sono:

- `*.awl`
- `*.scl`
- `*.db`
- `*.udt`

Questa pipeline è importante per il progetto perché permette di:

- importare AWL testuali come sorgenti esterne in TIA;
- generare blocchi TIA a partire da sorgenti testuali quando il caso d'uso lo consente;
- riesportare sorgenti da blocchi esistenti per analisi comparativa.

### 69.4 Regola architetturale nuova per il tool

Dalla documentazione Siemens deriva una regola progettuale molto importante:

> il tool deve separare il backend di generazione XML dal backend di orchestrazione Openness.

In termini pratici, l'architettura completa del progetto va letta così:

`AWL input -> parser -> IR sequenza/dati/reti -> compiler GRAPH + compiler DB + compiler FC -> validator XML -> backend Openness -> import/compile/export/compare`

Il backend Openness non genera la logica; la **orchestra e la valida** dentro TIA.

### 69.5 Struttura software consigliata del layer Openness

La documentazione del demo Siemens mostra una separazione netta fra GUI, ViewModel e servizi, e soprattutto conferma che l'accesso effettivo alla API è concentrato nei service layer.

Per il progetto corrente questo suggerisce una struttura minima del backend Openness composta da:

1. `tia_portal_session_service`
   - open / connect / disconnect / close;

2. `tia_project_service`
   - create / open / save / close project;

3. `tia_tree_locator`
   - ricerca dell'elemento di destinazione nell'albero logico o fisico;

4. `simaticml_service`
   - import element;
   - import structure;
   - export structure;

5. `plc_external_source_service`
   - add external source;
   - generate blocks from source;
   - generate source from block;

6. `tia_compile_service`
   - compilazione dell'elemento target;
   - raccolta messaggi, warning, errori;

7. `tia_version_adapter`
   - isolamento delle differenze fra V17/V20 o fra diverse installazioni.

### 69.6 Regola operativa su accessi esclusivi e transazioni

La documentazione mostra che almeno per l'import di strutture e per l'aggiunta di external source vengono usati `ExclusiveAccess` e transazioni con commit esplicito.

Questo implica che il backend Openness del progetto non deve limitarsi a chiamare API isolate, ma deve modellare correttamente:

- acquisizione dell'accesso esclusivo quando richiesto;
- apertura della transazione;
- esecuzione dell'operazione;
- commit solo in caso di esito valido;
- log degli errori e degli esiti.

Questa è una regola importante perché sposta il problema da “saper invocare la funzione” a “saper gestire correttamente il contesto di engineering TIA”.

### 69.7 Flusso end-to-end Openness raccomandato per il progetto

Il flusso operativo da assumere come obiettivo concreto diventa quindi:

1. aprire oppure collegarsi a TIA Portal;
2. aprire o creare il progetto di test;
3. individuare il nodo corretto dell'albero di progetto;
4. importare gli XML generati tramite pipeline Simatic ML;
5. in alternativa o in aggiunta, importare AWL/SCL/DB/UDT come external source;
6. generare eventuali blocchi da sorgente esterna quando applicabile;
7. compilare il target interessato;
8. raccogliere esiti, warning ed errori;
9. esportare nuovamente strutture o sorgenti utili;
10. confrontare export TIA e output del generatore.

Questo flusso deve diventare il riferimento del futuro smoke test automatico del progetto.

### 69.8 Nuovo obiettivo pratico derivato

Alla luce della documentazione, l'obiettivo Openness del progetto va raffinato così:

- non solo `import/export automatico XML`;
- ma **validazione automatica del ciclo tecnico completo** `generate -> import -> compile -> export -> compare`.

### 69.9 Limite metodologico da mantenere esplicito

È necessario fissare una distinzione chiara:

- la documentazione disponibile prova che il paradigma Openness supporta le operazioni necessarie;
- non prova da sola che ogni chiamata, namespace, comportamento o vincolo sia identico in V20.

Quindi, per il progetto, la regola corretta è:

> usare il materiale V17 come base di architettura e nomenclatura, ma validare sperimentalmente su TIA Portal V20 ogni tratto del backend Openness che entrerà nel flusso automatico reale.

### 69.10 Stato aggiornato del progetto dopo questa integrazione

Dopo questa lettura documentale, il progetto non va più considerato come composto solo da:

1. interpretazione AWL;
2. generazione GRAPH XML;
3. generazione DB/FC XML.

Ma da quattro livelli coordinati:

1. **estrazione semantica dal codice AWL**;
2. **generazione deterministica degli artefatti XML TIA**;
3. **validazione strutturale e semantica pre-import**;
4. **orchestrazione automatica TIA Portal tramite Openness per import, compile, export e confronto**.
