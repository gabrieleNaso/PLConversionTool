# Operazioni e comandi (PLConversionTool)

Questo documento sostituisce `HOW_TO_USE.md` e `docs/AI_HANDOFF_GENERATOR.md`.
Raccoglie setup, comandi base, workflow end-to-end e debug rapido.

## Prerequisiti
- Linux con `docker` e `docker compose`
- Repo clonata (esempio: `/home/administrator/PLConversionTool`)
- VM Windows con TIA Portal V20 + Openness
- Agent Windows (`tia_windows_agent/`) in esecuzione e raggiungibile dal `tia-bridge`

## Setup rapido (dev)

### 1) Avvia lo stack
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

### 2) Configura il bridge verso l'agent Windows
La configurazione sta nelle variabili ambiente del compose (`compose.dev.yml` / `.env` / `.env.example`).
Valorizza l'URL dell'agent Windows, ad esempio:

```text
TIA_WINDOWS_AGENT_URL=http://192.167.1.41:8050
```

Controllo rapido dallo status:

```bash
curl -sS http://127.0.0.1:8010/api/status
```


## Prima di generare: controlli obbligatori
- Verificare se il caso AWL sta usando tipici target `V20/GRAPH V2` o tipici legacy solo semantici.
- Ricordare che il bundle atteso non e' `1 + 1 + 1`, ma `1 x FB GRAPH + N x GlobalDB + M x FC LAD`.
- Verificare che il caso abbia una policy chiara per il naming globale: owner DB, branch path e leaf name devono essere determinabili prima della serializzazione.
- Se il caso deriva da un AWL monolitico, segmentarlo almeno nelle famiglie ricorrenti: allarmi, memorie/ausiliari, sequenza, manuale/automatico, emergenza/fault, uscite.

## Generare XML senza AI (da file in `data/input/`)

### 1) Metti i sorgenti AWL
Metti i file in `data/input/` con estensione:
- `.awl`
- `.txt`
- `.md` (viene usato il primo blocco fenced che contiene `NETWORK`)

### 2) Genera i bundle

```bash
make generate-input
```

Output:
- un bundle per file in `data/output/generated/<nome>/`
- file baseline sempre presenti:
  - `FB_<Name>_GRAPH_auto.xml`
  - `DB_<Name>_global_auto.xml`
  - `FC_<Name>_lad_auto.xml`
  - `<Name>_analysis.json`
- in base al contenuto AWL possono comparire anche altri `DB_*` e `FC_*` di supporto

Comportamento importante:
- la cartella del bundle target viene **pulita automaticamente** prima della nuova generazione;
- non restano file XML "stale" di run precedenti nello stesso bundle;
- il bundle va letto come pacchetto coerente e non come somma casuale di file;
- il file `<Name>_analysis.json` va conservato come diagnosi primaria del mapping AWL -> IR -> XML.

### Genera da un solo file

```bash
make generate-input INPUT_FILE="AWL romania.md"
```

### Genera solo file con prefisso

```bash
make generate-input INPUT_PREFIX="romania_"
```

## Import in TIA (via bridge) + compile automatica

### Import batch di tutto `data/output/generated/`

```bash
make import-generated \
  PROJECT_PATH="C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20" \
  TARGET_PATH="Program blocks/generati da tool"
```

### Import di una sola cartella bundle (consigliato)

```bash
make import-generated \
  PROJECT_PATH="C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20" \
  TARGET_PATH="Program blocks/generati da tool/mio_test" \
  IMPORT_BUNDLE="check_awl_romania"
```

Alternative:
- `IMPORT_BUNDLE`: match esatto del nome cartella in `data/output/generated/`
- `IMPORT_PREFIX`: importa solo cartelle che iniziano con quel prefisso

Note operative:
- per ogni import, il `tia-bridge` accoda automaticamente una compile
- se un blocco con lo stesso nome esiste gia' in TIA, l'import viene rifiutato (name collision)
- lo script `import-generated` effettua polling del job e, su collisione nome blocco, prova automaticamente suffissi numerici (`...1`, `...2`, ...).

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
    "awlSource":"NETWORK 1\n      U     S1\n      U     M10.0\n      S     S29\n",
    "outputDir":"data/output/generated/myseq_001"
  }'
```

### Export da IR JSON (senza AWL) via API backend

```bash
curl -sS -X POST "http://127.0.0.1:8000/api/conversion/export-ir" \
  -H "Content-Type: application/json" \
  -d '{
    "sequenceName":"MySeq_IR_001",
    "sourceName":"myseq_ir.xlsx",
    "outputDir":"data/output/generated/myseq_ir_001",
    "ir":{
      "networks":[{"index":1,"title":"Init"}],
      "steps":[{"name":"S1"},{"name":"S2"}],
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
- `docs/templates/ir_excel_template_single_page_with_support_fc.xlsx` (pagina FC completa: `support_fc` obbligatoria, `support_fc_logic` opzionale)

Comando:

```bash
make generate-excel-ir EXCEL_FILE="docs/templates/ir_excel_template_single_page_with_support_fc.xlsx"
```

Output nel bundle:
- `<Name>_ir.json` (IR estratto dall'Excel)
- `<Name>_analysis.json` (analisi completa usata per generare XML)
- XML baseline e support per `GRAPH + DB + FC`

Fogli Excel consigliati:
- `meta`: chiavi libere `key/value` (`sequence_name`, `source_name`, `assumptions`)
- `sequence`: `step_name`, `numero_step`, `transition_id`, `from_step`, `to_step`, `condition_expression`, `operands_used_in_condition`, `flow_type`, `parallel_group`, `jump_labels_used`
- `operands`: `operand`, `category`, `write_action`, `timer_instruction_kind`, `timer_preset_value`, `trigger_operands`, `note`
- `support_fc` (obbligatorio): `category`, `member_name`, `comment`
- `support_fc_logic` (opzionale): `category`, `result_member`, `condition_expression`, `condition_operands`, `comment`, `network`

Regole Excel importanti:
- l'inizio sequenza e' il passo con `numero_step=1` (non dal nome del passo);
- i nomi passo sono liberi (`Init`, `StartCiclo`, ecc.);
- in modalita' Excel, il catalogo `operands` guida la dichiarazione variabili DB (niente inferenze casuali).
- `operands` e `support_fc` sono obbligatori: se manca uno dei due (o e' vuoto), `generate-excel-ir` termina con errore.

Compatibilita':
- lo script accetta anche vecchi alias di colonna, ma per nuovi file usare i nomi espliciti sopra.

### Import via API backend (inoltro al bridge)

```bash
curl -sS -X POST "http://127.0.0.1:8000/api/tia/jobs/import" \
  -H "Content-Type: application/json" \
  -d '{
    "artifactPath":"data/output/generated/myseq_001",
    "projectPath":"C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20",
    "targetPath":"Program blocks/generati da tool",
    "targetName":null,
    "saveProject":true,
    "notes":"import myseq_001"
  }'
```

La risposta dell'import include:
- `JobId` (import)
- `AutoCompileJobId` (compile accodata automaticamente)

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

## Problemi comuni (e cosa fare)

### Import bloccato: "block name already exists"
- `import-generated` prova automaticamente rinomina con suffissi numerici.
- se finisce i retry, rinomina sequenza/bundle oppure elimina blocchi duplicati in TIA.

### Compile post-import in `blocked` con molti errori
La compile post-import usa lo **stesso targetPath/targetName** dell'import.
Se il target e' ampio (es. `Program blocks/generati da tool`), puo' includere errori di blocchi gia' presenti.

Strategie:
- usa un `targetPath` piu' specifico per bundle (es. `Program blocks/generati da tool/<nome_bundle>`)
- se serve isolamento massimo, imposta anche `targetName` sul blocco specifico da compilare
- pulisci i blocchi legacy nel progetto prima di compilare globalmente

### Backend o bridge non raggiungibili
- avvia: `make up`
- verifica: `curl http://127.0.0.1:8000/health` e `curl http://127.0.0.1:8010/health`

### Windows agent non raggiungibile
Verifica in `http://127.0.0.1:8010/api/status` che `remoteAgentStatus` sia popolato e che l'URL sia corretto.

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

### Clean data/output e data/tmp (attenzione: cancella)

```bash
make clean
```
