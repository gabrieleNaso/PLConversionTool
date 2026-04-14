# How to use (PLConversionTool)

Questo file raccoglie **setup + comandi base** per:

- generare XML da AWL **senza AI**
- importare in TIA via `tia-bridge` / `tia-windows-agent`
- ottenere compile automatica post-import

---

## Prerequisiti

- Linux con `docker` e `docker compose`
- Repo clonata in una path tipo: `/home/administrator/PLConversionTool`
- VM Windows con:
  - TIA Portal **V20**
  - Openness abilitato
  - `tia_windows_agent` attivo e raggiungibile dal container `tia-bridge`

---

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

### 2) Configura il bridge verso Windows agent

La configurazione sta nelle variabili ambiente del compose (`compose.dev.yml` / `.env` / `.env.example`).

In pratica deve essere valorizzato l’URL dell’agent Windows, ad esempio:

```text
TIA_WINDOWS_AGENT_URL=http://192.167.1.41:8050
```

Controllo rapido dallo status:

```bash
curl -sS http://127.0.0.1:8010/api/status
```

---

## Generare XML senza AI (da file in input/)

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
- file generati nel bundle:
  - `FB_<Name>_GRAPH_auto.xml`
  - `DB_<Name>_global_auto.xml`
  - `FC_<Name>_lad_auto.xml`
  - `<Name>_analysis.json`

---

## Import in TIA (via bridge) + compile automatica

### Import batch di tutto `output/generated/`

```bash
make import-generated \
  PROJECT_PATH="C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20" \
  TARGET_PATH="Program blocks/generati da tool"
```

Note:

- per ogni import, il `tia-bridge` **accoda automaticamente una compile** post-import
- se un blocco con lo stesso nome esiste già in TIA, l’import verrà rifiutato (name collision)

### One command: genera + importa

```bash
make generate-and-import \
  PROJECT_PATH="C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20" \
  TARGET_PATH="Program blocks/generati da tool"
```

---

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

### Import via API backend (che inoltra al bridge)

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

La risposta dell’import include:

- `JobId` (import)
- `AutoCompileJobId` (compile accodata automaticamente)

### Poll di un job

```bash
curl -sS "http://127.0.0.1:8000/api/tia/jobs/<JOB_ID>"
```

---

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

---

## Problemi comuni (e cosa fare)

### Import bloccato: “block name already exists”

Significa collisione di nome nel progetto TIA.

Soluzioni:

- rinominare la sequenza (generare un bundle con nome nuovo)
- oppure cancellare/rinominare il blocco già presente in TIA

### Compile post-import va in `blocked` con molti errori

La compile automatica è spesso **globale** (CPU / Program blocks) e può includere blocchi legacy.

Strategie:

- compila solo il blocco/gruppo appena importato (targetName/targetPath)
- pulisci i blocchi legacy nel progetto prima di compilare globalmente

### Backend o bridge non raggiungibili

- avvia: `make up`
- verifica: `curl http://127.0.0.1:8000/health` e `curl http://127.0.0.1:8010/health`

### Windows agent non raggiungibile

Verifica in `http://127.0.0.1:8010/api/status` che `remoteAgentStatus` sia popolato e che l’URL sia corretto.

---

## Nota sulla coerenza del pacchetto

Il generatore produce un pacchetto coerente:

- le transition GRAPH referenziano i member guard nel `GlobalDB` del pacchetto
- la FC LAD referenzia lo stesso `GlobalDB`
- le transizioni sintetiche (es. `T_HOLD_*`, `T_CHAIN_*`) sono dichiarate nel DB quando usate

Questo evita errori tipici del tipo “Tag … not defined”.

