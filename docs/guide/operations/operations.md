# Operazioni e comandi (PLConversionTool)

Questo documento raccoglie setup, comandi base, workflow end-to-end e debug rapido.

## Prerequisiti
- Linux con `docker` e `docker compose`
- Repo clonata (esempio: `/home/administrator/PLConversionTool`)
- VM Windows con TIA Portal V20 + Openness
- Agent Windows (`tia_windows_agent/`) in esecuzione e raggiungibile dal `tia-bridge`

## Setup rapido (dev)

### 1) Configura il bridge verso l'agent Windows
La configurazione sta nelle variabili ambiente del compose (`compose.dev.yml` / `.env` / `.env.example`).
Valorizza l'URL dell'agent Windows, ad esempio:

```text
TIA_WINDOWS_AGENT_URL=http://192.168.1.41:8050
```

Controllo rapido dallo status:

```bash
curl -sS http://127.0.0.1:8010/api/status
```


### 2) Avvia lo stack
Da root repo:

```bash
make up
```

Servizi:
- backend: `http://127.0.0.1:8000`
- tia-bridge: `http://127.0.0.1:8010`

Verifica:

```bash
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8010/health
curl -sS http://127.0.0.1:8000/api/tia/overview
```


## Prima di generare: controlli obbligatori
- Verificare se il caso AWL sta usando tipici target `V20/GRAPH V2` o tipici legacy solo semantici.
- Ricordare che il bundle atteso non e' `1 + 1 + 1`, ma `1 x FB GRAPH + N x GlobalDB + M x FC LAD`.
- Verificare che il caso abbia una policy chiara per il naming globale: owner DB, branch path e leaf name devono essere determinabili prima della serializzazione.
- Se il caso deriva da un AWL monolitico, segmentarlo almeno nelle famiglie ricorrenti: allarmi, memorie/ausiliari, sequenza, manuale/automatico, emergenza/fault, uscite.
- Se esiste un caso gia' tracciato in `cases/expected_output/expected_outputN/`, usarlo come baseline di regressione: le regole vanno estratte da li' e generalizzate, evitando fix "ad hoc" solo per un caso.

Gli expected dei casi vengono curati a mano in `cases/expected_output/expected_outputN/`.

## Generare XML senza AI (da file in `work/input/`)

### 1) Metti i sorgenti AWL
Metti i file in `work/input/` con estensione:
- `.awl`
- `.txt`
- `.md` (vengono estratti i blocchi fenced AWL/STL; se non rilevati, viene usato il testo completo)
  - nota: per i fenced block in `.md`, il parser prova a usare l'heading markdown piu' vicino (es. `## Segmento ...`) come titolo rete; in TIA verra' mostrato come `Title` della network LAD.

### 2) Genera i bundle

```bash
make generate-input
```

Output:
- un bundle per file in `work/output/generated/<nome>/`
- file baseline sempre presenti:
  - `FB_<Name>_GRAPH_auto.xml`
  - `FC14_<Name>_transitions_lad_auto.xml`
  - `<Name>_ir.json`
  - `<Name>_analysis.json`
- in base al contenuto AWL compaiono anche `DB_*` e `FC_*` di supporto (incluse le famiglie DB operative del pacchetto)

Comportamento importante:
- la cartella del bundle target viene **pulita automaticamente** prima della nuova generazione;
- non restano file XML "stale" di run precedenti nello stesso bundle;
- il percorso AWL passa esplicitamente da IR (`AWL -> IR JSON -> XML`), allineato al flusso Excel;
- il target XML resta **solo simbolico**: gli indirizzi fisici eventualmente presenti nel sorgente (I/Q/M/DBX/...) sono usati solo come input di mapping, ma non devono comparire nel naming dei member o nei path serializzati;
- il bundle va letto come pacchetto coerente e non come somma casuale di file;
- il file `<Name>_analysis.json` va conservato come diagnosi primaria del mapping AWL -> IR -> XML.
 - i DB supporto possono contenere member gerarchici (es. `HMI.ST.ST Sequencer step`): in questo caso il generatore crea automaticamente le `Struct` intermedie e le FC referenziano sempre il path completo includendo il DB owner.
 - la `FC12 HMI` contiene `Move` di status comparabili al progetto esempio (non decine di `Move` legacy `Trs/Seq/Preset`).

### Genera da un solo file

```bash
make generate-input INPUT_FILE="AWL romania.md"
```

### Genera solo file con prefisso

```bash
make generate-input INPUT_PREFIX="romania_"
```

## Import in TIA (via bridge)

### Import batch di tutto `work/output/generated/`

Prerequisito: stack avviato (backend + tia-bridge).

```bash
make up
curl -sS http://127.0.0.1:8000/health
```

```bash
make import-generated \
  PROJECT_PATH="C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20" \
  TARGET_PATH="Program blocks/generati da tool"
```

Nota:
- `PROJECT_PATH` e `TARGET_PATH` sono obbligatori, ma puoi passarli anche via variabili ambiente:
  - `TIA_PROJECT_PATH` (equivale a `PROJECT_PATH`)
  - `TIA_TARGET_PATH` (equivale a `TARGET_PATH`)

### Import di una sola cartella bundle (consigliato)

```bash
make import-generated \
  PROJECT_PATH="C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20" \
  TARGET_PATH="Program blocks/generati da tool/mio_test" \
  IMPORT_BUNDLE="auto_awl_romania"
```

Alternative:
- `IMPORT_BUNDLE`: match esatto del nome cartella in `work/output/generated/`
- `IMPORT_PREFIX`: importa solo cartelle che iniziano con quel prefisso

Note operative:
- l'import non accoda compile automatiche
- se un blocco con lo stesso nome esiste gia' in TIA, il singolo tentativo di import va in collisione; `import-generated` gestisce il caso con retry e rinomina automatica.
- lo script `import-generated` effettua polling del job e, su collisione nome blocco, prova automaticamente suffissi numerici (`...1`, `...2`, ...).
- `tia-bridge` carica e invia all'agent Windows solo i file `*.xml` del bundle: i report `.json` restano locali e non bloccano l'import.

## Multi-blocco (best effort)

Se in `work/input/` sono presenti piu' blocchi (es. `# FC102`, `# FC32` in file diversi), la generazione indicizza i blocchi disponibili e registra nel report eventuali dipendenze trovate via `CALL`:
- nel file `<Name>_analysis.json` trovi `ir.support_logic.kind=project_dependencies` con `called_blocks/present_blocks/missing_blocks`.
- se manca un blocco chiamato, compare un warning `missing_called_blocks`.
- quando il blocco chiamato e' presente, il report include anche `ir.support_logic.kind=dependency_analyses` con un sommario dell'analisi dei blocchi dipendenti (utile per verificare correlazioni e segnali mancanti).

Quando i sorgenti esterni non sono disponibili (caso: AWL monolitico unico), alcune diramazioni possono comunque essere ricostruite con regole interne (es. split su presenza pezzo), ma il tool segnala comunque le chiamate AWL non risolte.

### One command: genera + importa

```bash
make generate-and-import \
  PROJECT_PATH="C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20" \
  TARGET_PATH="Program blocks/generati da tool"
```

## API (equivalenti ai comandi make)

### Export (generazione bundle) via API backend

```bash
curl -sS -X POST "http://127.0.0.1:8000/api/conversion/export" \
  -H "Content-Type: application/json" \
  -d '{
    "sequenceName":"MySeq_001",
    "sourceName":"myseq_001.awl",
    "awlSource":"NETWORK 1\n      U     S1\n      U     \\\"START_REQ\\\"\\n      S     S29\\n",
    "outputDir":"work/output/generated/myseq_001"
  }'
```

### Export da IR JSON (senza AWL) via API backend

```bash
curl -sS -X POST "http://127.0.0.1:8000/api/conversion/export-ir" \
  -H "Content-Type: application/json" \
	  -d '{
	    "sequenceName":"MySeq_IR_001",
	    "sourceName":"myseq_ir.xlsx",
	    "outputDir":"work/output/generated/myseq_ir_001",
	    "ir":{
	      "networks":[{"index":1,"title":"Init"}],
	      "steps":[{"name":"S1"},{"name":"S2"}],
	      "step_roles":{"S1":"entry"},
	      "transitions":[
	        {
	          "transition_id":"T1",
	          "source_step":"S1",
	          "target_step":"S2",
	          "guard_expression":"TRUE"
	        }
	      ]
	    }
	  }'
```

## Generare da Excel manuale (IR -> JSON -> XML)

Guida completa compilazione Excel:
- `docs/guide/operations/excel-ir-compilation-guide.md`

Template pronto:
- `docs/templates/ir_excel_template_single_page_with_support_fc.xlsx` (pagina FC unica: `support_fc` obbligatoria)

Comando:

```bash
make generate-excel-ir EXCEL_FILE="docs/templates/ir_excel_template_single_page_with_support_fc.xlsx"
```

Shortcut (usa il template default configurato in `Makefile`):

```bash
make generate-excel
```

Output nel bundle:
- `<Name>_ir.json` (IR estratto dall'Excel)
- `<Name>_analysis.json` (analisi completa usata per generare XML)
- XML baseline e support per `GRAPH + DB + FC`:
  - baseline manifest: `graph_fb` + `lad_fc`
  - support manifest/previews: DB e FC di supporto (`support_global_db_*`, `support_lad_fc_*`)

Fogli Excel consigliati:
- `sequence`: `step_name`, `numero_step`, `from_step`, `transition_id`, `to_step`, `condition_expression`, `flow_type`, `parallel_group`
- `operands`: `operand`, `category`, `datatype`, `control_kind`, `control_value`, `note`
- `support_fc` (obbligatorio, pagina unica FC): `category`, `member_name`, `result_member`, `condition_expression`, `coil_mode`, `comment`, `network`

Regole Excel importanti:
- l'inizio sequenza e' il passo con `numero_step=1` (non dal nome del passo);
- i nomi passo sono liberi (`Init`, `StartCiclo`, ecc.);
- in modalita' Excel, il catalogo `operands` guida la dichiarazione variabili DB (niente inferenze casuali).
- in modalita' strict Excel, i commenti DB derivano solo da commenti espliciti del member e da `operands.note`; se mancanti, restano vuoti.
- i commenti non vengono piu' emessi nelle network LAD generate: il campo `support_fc.comment` viene ignorato (commento rete vuoto).
- il testo visibile in TIA per ogni network LAD e' solo il **titolo** della network (derivato dal titolo AWL/Excel); in assenza di titolo si usa il numero `network`.
- in `operands.category` usa solo categorie funzionali (`alarm`, `aux`, `hmi`, `output`, `memory`, `external`, `lv2`/`lev2`, `transition`/`transitions`).
- alias legacy `timer`/`counter`/`manual_mode`/`auto_mode` sono accettati dal parser e normalizzati a `aux`.
- per LEV2 usa `lv2`/`lev2`; la categoria `mode` non viene normalizzata automaticamente a LEV2 nel parser `operands`.
- non usare variabili FC assenti da `operands`: se compaiono in una `condition_expression` vengono considerate **non risolte** (mancanza di owner DB) e il bundle non va considerato valido per import/compile.
- timer/contatori definiti in `operands` e usati in `support_fc` vengono emessi come blocchi LAD completi, con preset da `control_value`.
- per le scritture non booleane (pattern AWL `L ... / T ...`) il backend genera box LAD `Move` in `FC12 HMI` con enable coerente con la rete sorgente (no enable sempre a `Powerrail`).
- se piu' righe `support_fc` hanno stessa `category` e stesso `network`, vengono aggregate in una sola network FC.
- ogni network FC deve avere un solo `Powerrail` LAD (vincolo import TIA).
- `coil_mode` per riga: `set` -> `SCoil`, `reset` -> `RCoil`, vuoto -> bobina normale (`Coil`).
- `sequence`, `operands` e `support_fc` sono obbligatori: se manca uno di questi (o `operands`/`support_fc` sono vuoti), `generate-excel-ir` termina con errore.
- nelle espressioni logiche (`condition_expression` / `guard_expression`) sono supportate parentesi e precedenza booleana.
- il generatore deduce automaticamente gli operandi da `condition_expression`/`guard_expression` (non servono colonne operandi dedicate nel formato corrente).
- nel GRAPH, le transition usano la logica reale dell'Excel (`condition_expression`) e non vengono ridotte a marker tipo `T1/T2`.
- i riferimenti variabile nelle transition GRAPH sono cross-DB: ogni simbolo punta al DB owner derivato dal catalogo `operands`.
- i blocchi supporto vengono emessi in modo completo per famiglia; un placeholder `NoData` e' ammesso solo quando la famiglia e' davvero non usata nel bundle (nessun simbolo richiesto da FB/FC/GRAPH). Se una famiglia e' referenziata (es. variabili esterne o HMI presenti), deve contenere i member richiesti.

Compatibilita':
- lo script accetta solo il formato Excel corrente (`sequence`, `operands`, `support_fc`) con colonne canoniche.
- alias legacy di fogli/colonne non sono supportati.

Nota Openness (lingue progetto):
- per evitare failure di import, gli XML emettono solo `Culture=en-US` nei `MultilingualText` (non `it-IT`).

### Import via API backend (inoltro al bridge)

```bash
curl -sS -X POST "http://127.0.0.1:8000/api/tia/jobs/import" \
  -H "Content-Type: application/json" \
  -d '{
    "artifactPath":"work/output/generated/myseq_001",
    "projectPath":"C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20",
    "targetPath":"Program blocks/generati da tool",
    "targetName":null,
    "saveProject":true,
    "notes":"import myseq_001"
  }'
```

La risposta dell'import include:
- `JobId` (import)

### Poll di un job

```bash
curl -sS "http://127.0.0.1:8000/api/tia/jobs/<JOB_ID>"
```

## Regole operative essenziali (da non violare)
- **Numerazione step**: la sorgente primaria e' `step_number/numero_step`; il passo iniziale e' quello con numero `1`.
- **Naming step**: il nome passo e' libero e non deve cambiare la topologia.
- **Ingressi multipli** su uno step non iniziale:
  - il primo ingresso puo' essere `Direct`;
  - gli ingressi extra devono essere `Jump`.
- **Guard logiche transizioni (`Trs`)**:
  - il parser preserva operatori booleani `AND` / `OR` / `NOT` da AWL (`A/AN/O/ON`, inclusi gruppi `A(...)`/`O(...)`);
  - le guardie non vanno appiattite in `AND` quando in AWL esistono rami `OR`.
- **Excel strict DB**:
  - la logica transizioni GRAPH resta completa;
  - nei DB vengono dichiarati solo segnali presenti nel catalogo `operands` (e categorie derivate).
- **Output fisiche**:
  - sono riconosciute sia in formato `Axx(.x)` sia `Qxx(.x)` quando usate con `=`.
- **targetPath**: deve partire da `Program blocks/`.
  - Se ometti il prefisso, TIA crea un gruppo con nome letterale (es. `generati da tool/xxx`).
- **Naming famiglie blocchi**: le FC seguono la famiglia numerica prevista; `15GG` e' riservato al GRAPH (`FB15GG`) e al suo DB istanza (`DB15GG`) associato alla sequenza.
- **Profilo target corretto**:
  - FC: `FC11` Alarms, `FC12` HMI, `FC13` Aux, `FC14` Transitions, `FC16` Output, `FC17` LEV2
  - DB custom: `DB11` alarms, `DB12` HMI, `DB13` PARAMETERS, `DB14` transitions, `DB16` I/O + output, `DB17` LEV2, `DB18` external, `DB19` AUX
  - FB/istanza: `FB15` GRAPH + `DB15` SEQ (istanza creata da TIA quando l'FB viene istanziato)

Nota operativa (bootstrap import/compile):
- per permettere la **prima compilazione** quando le FC referenziano `DB15_<Seq>_GRAPH_DB.Sxx.X`, il tool emette anche un `InstanceDB` di bootstrap `ZZ_DB15_<Seq>_graph_db_auto.xml`.
- il file ha prefisso `ZZ_` per essere importato **dopo** `FB_<Seq>_GRAPH_auto.xml` (l'import batch del bridge e' ordinato alfabeticamente).
- questo DB non e' un "DB custom applicativo": serve solo a sbloccare il ciclo import/compile; TIA potra' poi rigenerarlo/aggiornarlo in base all'istanza reale.

Nota sui nomi member DB:
- i nomi in transizione privilegiano alias semantici derivati dall'AWL (es. da simboli/tag ricorrenti nel sorgente).
- in caso di alias ambiguo il generatore usa fallback deterministico basato sul token AWL originale (sanitizzato), senza introdurre indirizzi nuovi e senza lasciare nomi vuoti.
- i member della famiglia transizioni sono sempre emessi e referenziati come path strutturato: `DB14_<Name>_TRANSITIONS_DB -> Transitions -> <member>`.

Nota timer (AWL):
- quando in AWL compaiono `Txx` in logica booleana, il significato e' il done del timer: in XML deve diventare `Txx.Q` oppure un box IEC in-line. Il token `Txx_DONE` e' solo una rappresentazione interna e non deve diventare un member BOOL nei DB.

## Problemi comuni (e cosa fare)

### Import bloccato: "block name already exists"
- `import-generated` prova automaticamente rinomina con suffissi numerici.
- se finisce i retry, rinomina sequenza/bundle oppure elimina blocchi duplicati in TIA.

### Compile in `blocked` con molti errori
Se il target compile e' ampio (es. `Program blocks/generati da tool`), puo' includere errori di blocchi gia' presenti.

Strategie:
- usa un `targetPath` piu' specifico per bundle (es. `Program blocks/generati da tool/<nome_bundle>`)
- se serve isolamento massimo, imposta anche `targetName` sul blocco specifico da compilare
- pulisci i blocchi legacy nel progetto prima di compilare globalmente

### Backend o bridge non raggiungibili
- avvia: `make up`
- verifica: `curl http://127.0.0.1:8000/health` e `curl http://127.0.0.1:8010/health`

### Windows agent non raggiungibile
Verifica in `http://127.0.0.1:8010/api/status` che `remoteAgentStatus` sia popolato e che l'URL sia corretto.

### `make generate-input INPUT_FILE="..."` non genera nulla
Cause tipiche:
- nome file non esatto rispetto a `input/` (maiuscole/spazi inclusi);
- file presente ma estensione non supportata;
- file `.md` senza blocchi riconoscibili come AWL e testo non interpretabile.

Verifica rapida:
```bash
ls -la work/input/
```

## Debug rapido (errore -> causa -> fix)
- Errore import: `A connection between "T6" and "Branch 1" cannot be created`
  - Causa: connessione `Transition -> Branch` non accettata.
  - Fix: usa `Jump` sugli ingressi multipli (no join con `SimEnd`).

- Crash TIA aprendo FB GRAPH:
  - Causa tipica: topologia invalida (doppi ingressi `Direct`).
  - Fix: converti gli ingressi extra in `Jump`.

- Logica XML "diversa" dall'AWL su transizioni:
  - Causa tipica: sorgente con condizioni complesse `OR/NOT` o gruppi non verificata dopo rigenerazione.
  - Fix rapido:
    1. rigenera (`make generate-input INPUT_FILE="..."`);
    2. controlla `<Name>_analysis.json` (`ir.transitions[].guard_expression`);
    3. verifica che l'espressione mantenga `OR` e `NOT` dove presenti in AWL.

### Note su tracking (step 100/101)
- Il convertitore puo' introdurre automaticamente i passi sintetici `S100_TRK_CHECK` / `S101_TRK_TRANSFER` quando rileva un pattern di tracking (sequenza remota + presenza `PT/PT_END`) nel sorgente.
- Regola aggiornata: il pattern viene considerato *remoto* solo se il prefisso/DB della sequenza esterna e' diverso da quello della sequenza locale (evita falsi positivi in sorgenti che usano solo `PT/PT_END` locali).

### Audit bundle (regressione rapida)
Per verificare velocemente che i bundle generati non contengano:
- espressioni booleane malformate (`AND )`, parentesi vuote, ecc.)
- guardie di transizione con step impossibili

usa:

```bash
node scripts/audit_generated_ir.mjs
```

Nota: l'audit lavora sui file in `work/output/generated/` e stampa un riepilogo per i bundle `auto_awl_romania*`.
- Override via env `PLC_ENABLE_TRACKING_TRANSLATION`:
  - `0`/`false`/`off` = disabilita;
  - `1`/`true`/`on` = forza abilitazione;
  - valore non settato/altro = auto (default).

## Comandi base utili

### Logs

```bash
make logs
```

### Restart stack

```bash
make down
make up
```

### Shell nei container

```bash
make shell-backend
make shell-tia
```

### Clean output e tmp (attenzione: cancella)

```bash
make clean
```
