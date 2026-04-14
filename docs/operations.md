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

## Generare XML senza AI (da file in `input/`)

### 1) Metti i sorgenti AWL
Metti i file in `input/` con estensione:
- `.awl`
- `.txt`
- `.md` (viene usato il primo blocco fenced che contiene `NETWORK`)

### 2) Genera i bundle

```bash
make generate-input
```

Output:
- un bundle per file in `output/generated/<nome>/`
- file baseline sempre presenti:
  - `FB_<Name>_GRAPH_auto.xml`
  - `DB_<Name>_global_auto.xml`
  - `FC_<Name>_lad_auto.xml`
  - `<Name>_analysis.json`
- in base al contenuto AWL possono comparire anche altri `DB_*` e `FC_*` di supporto

### Genera da un solo file

```bash
make generate-input INPUT_FILE="AWL romania.md"
```

### Genera solo file con prefisso

```bash
make generate-input INPUT_PREFIX="romania_"
```

## Import in TIA (via bridge) + compile automatica

### Import batch di tutto `output/generated/`

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
- `IMPORT_BUNDLE`: match esatto del nome cartella in `output/generated/`
- `IMPORT_PREFIX`: importa solo cartelle che iniziano con quel prefisso

Note operative:
- per ogni import, il `tia-bridge` accoda automaticamente una compile
- se un blocco con lo stesso nome esiste gia' in TIA, l'import viene rifiutato (name collision)

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
    "outputDir":"output/generated/myseq_001"
  }'
```

### Import via API backend (inoltro al bridge)

```bash
curl -sS -X POST "http://127.0.0.1:8000/api/tia/jobs/import" \
  -H "Content-Type: application/json" \
  -d '{
    "artifactPath":"output/generated/myseq_001",
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
- **Numerazione step**: `Sxx` deve diventare `Step Number="xx"` (es. `S29` -> 29).
- **Ingressi multipli** su uno step non iniziale:
  - il primo ingresso puo' essere `Direct`;
  - gli ingressi extra devono essere `Jump`.
- **targetPath**: deve partire da `Program blocks/`.
  - Se ometti il prefisso, TIA crea un gruppo con nome letterale (es. `generati da tool/xxx`).

## Problemi comuni (e cosa fare)

### Import bloccato: "block name already exists"
- rinominare la sequenza (generare un bundle con nome nuovo)
- oppure cancellare/rinominare il blocco gia' presente in TIA

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

### Clean output/tmp (attenzione: cancella)

```bash
make clean
```
