# PLConversionTool — Setup completo e guida d’uso (unificata)

Questo documento raccoglie **in un unico posto**:
- setup completo (Linux/Docker + VM Windows/TIA/Openness + agent);
- come usare il tool end‑to‑end (AWL/Excel/IR JSON → XML → import TIA);
- comandi `make`, script e API realmente presenti nel repo.

Nota gerarchia (importante):
- le regole *hard* di traduzione/serializer stanno nella **spec master**: `docs/reference/specs/Specifica_master_traduzione_AWL_e_generazione_XML_TIA_V20_V2_18_05.md`;
- questo documento è operativo (setup/uso), e deve restare coerente con la spec e con i report consolidati.

---

## 1) Panoramica rapida (cosa fa il progetto)

Obiettivo: convertire sequenziatori PLC (AWL o Excel strutturato) in un **pacchetto coerente** di blocchi TIA Portal V20:

`1 x FB GRAPH + N x GlobalDB + M x FC LAD` → esportati come XML Openness importabili in TIA.

Componenti principali:
- `src/`: libreria core di conversione (`plc_converter/*`) usata dal backend.
- `backend/`: API FastAPI per analisi/esportazione bundle e orchestrazione verso il bridge.
- `tia_bridge/`: boundary service che parla con un **agent Windows** (per Openness) e gestisce job import/compile/export.
- `tia_windows_agent/`: agent su VM Windows (.NET Framework 4.8) che invoca TIA Portal Openness.
- `frontend/`: UI Next.js (dev) per status/overview.
- `scripts/`: script CLI ripetibili (generate/import/check).
- `work/`: workspace locale non versionato (input/output/tmp).
- `cases/`: casi versionati (input + expected_output) per regressione.
- `datasets/`: corpus/typicals/golden (materiale di riferimento).

Riferimenti operativi già presenti:
- comandi & workflow: `docs/guide/operations/operations.md`
- flusso concettuale: `docs/guide/process/flow.md`
- integrazione TIA: `docs/guide/integration/tia-integration.md`
- checklist: `docs/guide/checklists/workflow-checklists.md`
- convenzioni naming/dataset: `docs/guide/standards/conventions.md`
- struttura workspace: `docs/reference/data.md`

---

## 2) Prerequisiti

### 2.1 Linux / host che esegue Docker
- `docker` + `docker compose` disponibili (vedi `make doctor`).
- `make` (per usare i target del `Makefile`).
- Accesso di rete dalla macchina Linux verso la VM Windows (porta agent, default `8050`).

### 2.2 VM Windows (TIA side)
Sulla VM Windows devono essere veri almeno questi punti:
- TIA Portal **V20** installato + Openness.
- Utente Windows nel gruppo locale `Siemens TIA Openness`.
- `.NET Framework 4.8` e tool di build: `dotnet` (consigliato) oppure Visual Studio/MSBuild.
- Agent Windows avviabile dalla cartella `tia_windows_agent/` (vedi sotto).

---

## 3) Setup Windows (TIA Windows Agent)

Questa parte si fa **dentro la VM Windows**.

1) Copia la cartella `tia_windows_agent/` nella VM, ad esempio:
- `C:\\PLConversionTool\\tia_windows_agent`

2) Apri PowerShell nella cartella:
- `cd C:\\PLConversionTool\\tia_windows_agent`

3) Crea/configura `appsettings.Local.json`:
- copia `appsettings.Local.template.json` → `appsettings.Local.json`
- verifica almeno: `ListenUrl`, `ProjectRoot`, `OutputDirectory`, `TempDirectory`, `SiemensAssemblyDirectory`, `DefaultProjectPath`

4) Bootstrap (crea config se manca + firewall rule):
- `.\bootstrap-vm.ps1`
- (porta diversa) `.\bootstrap-vm.ps1 -Port 8060`

5) Avvio agent:
- `.\run-agent.ps1`

6) Test locale in VM:
- `Invoke-RestMethod http://localhost:8050/health`
- `Invoke-RestMethod http://localhost:8050/api/status`
- `Invoke-RestMethod http://localhost:8050/api/openness/diagnostics`

Documentazione dettagliata Windows agent: `tia_windows_agent/agent.md`.

---

## 4) Setup Linux (Docker Compose dev)

### 4.1 Variabili ambiente (consigliato: `.env`)
Parti da `.env.example` e crea un `.env` nella root repo.

Minimo consigliato per integrazione reale (TIA bridge in modalità `real`):
- `TIA_BRIDGE_MODE=real`
- `TIA_WINDOWS_AGENT_URL=http://<IP_VM_WINDOWS>:8050`

Alternative equivalenti (se preferisci host/porta):
- `TIA_WINDOWS_HOST=<IP_VM_WINDOWS>`
- `TIA_WINDOWS_AGENT_PORT=8050`
- `TIA_WINDOWS_TRANSPORT=http`

Nota: in `compose.dev.yml` esistono default hard-coded (es. IP) che vanno **sovrascritti** col tuo `.env`.

Variabili utili aggiuntive (in base al caso):
- porte esposte host:
  - `BACKEND_PORT=8000`
  - `FRONTEND_PORT=3000`
  - `TIA_BRIDGE_PORT=8010`
- timezone:
  - `TZ=UTC`
- modalità bridge (per sviluppo senza Windows/TIA):
  - `TIA_BRIDGE_MODE=stub` (default) → il bridge accetta job ma li salva in memoria (nessuna chiamata alla VM)
- target profile generazione (solo IR → XML):
  - `PLC_TARGET_PROFILE=romania` (oppure passa `TARGET_PROFILE=...` ai comandi `make`)

Esempio `.env` completo (tipico):
```env
TZ=UTC
BACKEND_PORT=8000
FRONTEND_PORT=3000
TIA_BRIDGE_PORT=8010

TIA_BRIDGE_MODE=real
TIA_WINDOWS_AGENT_URL=http://192.168.1.50:8050
TIA_VMWARE_NETWORK_MODE=bridged
```

Nota su UID/GID e volumi:
- il compose passa `USER_UID/USER_GID/USERNAME` come build args (default `1000/dev`);
- monta la repo in `/workspace` e monta anche `~/.gitconfig` e `~/.ssh` in read-only nei container.

### 4.2 Avvio stack
Da root repo:
- `make doctor`
- `make up`

Servizi (default):
- backend: `http://127.0.0.1:8000`
- tia-bridge: `http://127.0.0.1:8010`
- frontend: `http://127.0.0.1:3000`

Health check:
- `curl -sS http://127.0.0.1:8000/health`
- `curl -sS http://127.0.0.1:8010/health`
- `curl -sS http://127.0.0.1:8000/api/tia/overview`

Log:
- `make logs`

Shell nei container:
- `make shell-backend`
- `make shell-tia`
- `make shell-frontend`

### 4.3 Cosa aspettarsi dai servizi (ruoli)
- `backend` (FastAPI) genera bundle XML e fornisce endpoint di conversione; espone anche un proxy verso il bridge (`/api/tia/*`).
- `tia-bridge` (FastAPI) è l’orchestratore: stage-a artefatti da Linux → VM Windows e accoda job (import/compile/export).
- `frontend` (Next.js) è una pagina di overview (status backend/bridge/agent).

Nota: se `TIA_BRIDGE_MODE=stub`, i job TIA risultano “completati” solo a livello stub e non producono side effects su TIA.

---

## 5) Input/Output: cartelle del workspace

Cartelle principali (vedi anche `docs/reference/data.md`):
- input runtime: `work/input/`
  - AWL/MD/TXT: `work/input/*.awl|*.md|*.txt`
  - IR JSON manuale: `work/input/ir_json/*.json`
  - Excel: `work/input/excel/*.xlsx` (opzionale, percorso libero)
- output runtime: `work/output/generated/<bundle>/`
- temp/staging: `work/tmp/`

Struttura tipica di un bundle in `work/output/generated/<bundle>/`:
- XML principali:
  - `FB_<SequenceName>_GRAPH_auto.xml`
  - `DB<XX>_<SequenceName>_<family>_db_auto.xml` (più famiglie DB)
  - `FC<XX>_<SequenceName>_<family>_lad_auto.xml` (più famiglie FC)
- report/diagnosi:
  - `<SequenceName>_analysis.json` (diagnosi completa + anteprime artefatti)
  - `<SequenceName>_ir.json` (se generato via script IR o se copiato per tracciabilità)
- export Excel (quando l’IR è disponibile):
  - `<SequenceName>_from_ir.xlsx`

Nota sui casi versionati:
- `cases/input/` e `cases/expected_output/` sono la base per regressione e regole (`cases/translation_rules.md`).

---

## 6) Workflow di uso (3 ingressi → 1 uscita: bundle XML)

### 6.1 Workflow consigliato (AI-first): IR JSON → XML
1) Crea/curi un IR JSON in `work/input/ir_json/` (manualmente o con AI).
2) Genera il bundle:
- `make gen-ir IR_JSON="work/input/ir_json/<file>_ir.json" SEQUENCE_NAME="<SequenceName>"`

Opzionale (profilo target solo per IR→XML):
- `make gen-ir IR_JSON="..." SEQUENCE_NAME="..." TARGET_PROFILE=romania`

Equivalente script:
- `python3 scripts/generate_from_ir_json.py --ir-json "work/input/ir_json/<file>.json" --sequence-name "<SequenceName>"`

Dettagli pratici:
- lo script `scripts/generate_from_ir_json.py` crea/ricrea la cartella bundle sotto `work/output/generated/<slug_sequence_name>/` (pulizia inclusa).
- se passi `--target-profile` (o `TARGET_PROFILE`), viene impostata `PLC_TARGET_PROFILE` e l’IR viene marcato con `target_profile_name`.

Punto di partenza consigliato per costruire IR JSON:
- bootstrap (scaffold) via API backend:
  - `POST http://127.0.0.1:8000/api/conversion/bootstrap` con payload `{ "sequenceName": "...", "awlSource": "...", "sourceName": "..." }`
  - usa il JSON risultante come base (poi cura `ir` e rigenera con `gen-ir`).

Strumenti utili per creare IR da markdown AWL (senza parser automatico):
- `python3 scripts/manual_awl_md_to_ir.py --source "work/input/<file>.md" --sequence-name "<SequenceName>" --out "work/input/ir_json/<SequenceName>_ir.json"`

### 6.2 Workflow automatico (parser AWL): AWL → IR → XML
1) Metti i sorgenti in `work/input/` (`.awl`, `.txt`, `.md`).
2) Genera:
- `make gen`

Filtri:
- `make gen INPUT_FILE="AWL romania fc112.md"`
- `make gen INPUT_PREFIX="romania_"`

Output tipico per bundle:
- `*_ir.json` (IR usato)
- `*_analysis.json` (diagnosi/anteprime)
- XML: `FB_*_GRAPH_auto.xml`, `DB*_*_db_auto.xml`, `FC*_*_lad_auto.xml`

Dettagli input `.md`:
- se il file è markdown, il parser prova a estrarre i blocchi fenced AWL/STL; se non li rileva, usa il testo completo.

### 6.3 Workflow Excel: Excel → IR → XML
1) Parti dal template: `docs/templates/ir_excel_template_single_page_with_support_fc.xlsx`
2) Genera:
- `make generate-excel-ir EXCEL_FILE="docs/templates/ir_excel_template_single_page_with_support_fc.xlsx"`

Equivalente script:
- `python3 scripts/generate_from_excel_ir.py --excel "<file>.xlsx" --output-root work/output/generated --sequence-name "<SequenceName>"`

Regole Excel (hard) e colonne: `docs/guide/operations/excel-ir-compilation-guide.md`.

---

## 7) Validazioni rapide (prima di importare in TIA)

Checklist operative:
- `docs/guide/checklists/workflow-checklists.md`

Controllo simboli (tutto ciò che è referenziato deve essere dichiarato nel DB owner):
- `python3 scripts/check_bundle_symbol_resolution.py --bundle-dir work/output/generated/<bundle>`

Output del check:
- stampa un JSON con `xml_files`, `accesses`, `missing`;
- se `missing > 0`, l’import/compile in TIA è tipicamente a rischio (member non dichiarati o DB non trovato).

Rigenerazione “pulita”:
- la generazione ricrea/pulisce la cartella bundle target (evita XML “stale”).

---

## 8) Import in TIA (via backend → bridge → agent Windows)

Prerequisiti:
- stack Linux avviato (`make up`)
- agent Windows in ascolto e raggiungibile

Import batch di tutto `work/output/generated/`:
- `make import-generated PROJECT_PATH="C:\\path\\progetto.ap20" TARGET_PATH="Program blocks/generati da tool"`

Import di un solo bundle:
- `make import-generated PROJECT_PATH="C:\\path\\progetto.ap20" TARGET_PATH="Program blocks/generati da tool/mio_test" IMPORT_BUNDLE="<bundle_dir_name>"`

Alternative con variabili ambiente:
- `TIA_PROJECT_PATH` equivale a `PROJECT_PATH`
- `TIA_TARGET_PATH` equivale a `TARGET_PATH`
- `TIA_IMPORT_BUNDLE` equivale a `IMPORT_BUNDLE`
- `TIA_IMPORT_PREFIX` equivale a `IMPORT_PREFIX`

Nota collisioni nomi:
- lo script `scripts/import_generated_to_tia.py` gestisce retry e rinomina automatica in caso di collisione nomi blocco in TIA.

Import + attesa esito (via script, utile in debug):
- `python3 scripts/import_generated_to_tia.py --project-path "C:\\path\\progetto.ap20" --target-path "Program blocks/generati da tool" --bundle "<bundle>" --wait`

Nota compile:
- il flusso import non accoda compile automatiche: se vuoi verificare coerenza reale del pacchetto, fai import + compile (vedi esempi API sotto).

---

## 9) API (backend e bridge)

### 9.1 Backend (`http://127.0.0.1:8000`)
Health:
- `GET /health`

Conversione:
- `POST /api/conversion/analyze` (AWL → analysis+IR+previews)
- `POST /api/conversion/export` (AWL → scrittura bundle su `work/output/...`)
- `POST /api/conversion/analyze-ir` (IR JSON payload → analysis)
- `POST /api/conversion/export-ir` (IR JSON payload → scrittura bundle)
- `GET /api/conversion/profile`

TIA boundary (proxy verso bridge):
- `GET /api/tia/overview`
- `GET /api/tia/openness/diagnostics`
- `POST /api/tia/jobs/import|compile|export`
- `GET /api/tia/jobs` / `GET /api/tia/jobs/{jobId}`

Esempi `curl` (backend):

Analyze (AWL → analisi + anteprime):
```bash
curl -sS -X POST "http://127.0.0.1:8000/api/conversion/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "sequenceName":"MySeq_001",
    "sourceName":"myseq_001.awl",
    "awlSource":"NETWORK 1\n      U     S1\n      S     S29\n"
  }'
```

Export (scrive bundle sotto `work/output/generated/...`):
```bash
curl -sS -X POST "http://127.0.0.1:8000/api/conversion/export" \
  -H "Content-Type: application/json" \
  -d '{
    "sequenceName":"MySeq_001",
    "sourceName":"myseq_001.awl",
    "awlSource":"NETWORK 1\n      U     S1\n      S     S29\n",
    "outputDir":"work/output/generated/myseq_001"
  }'
```

Accodare un import TIA (passando una cartella bundle come `artifactPath`):
```bash
curl -sS -X POST "http://127.0.0.1:8000/api/tia/jobs/import" \
  -H "Content-Type: application/json" \
  -d '{
    "artifactPath":"work/output/generated/myseq_001",
    "projectPath":"C:\\\\path\\\\progetto.ap20",
    "targetPath":"Program blocks/generati da tool",
    "saveProject": true,
    "notes":"import bundle myseq_001"
  }'
```

Accodare una compile (stesso progetto, target opzionali):
```bash
curl -sS -X POST "http://127.0.0.1:8000/api/tia/jobs/compile" \
  -H "Content-Type: application/json" \
  -d '{
    "artifactPath":"work/output/generated/myseq_001",
    "projectPath":"C:\\\\path\\\\progetto.ap20",
    "targetPath":"Program blocks/generati da tool",
    "saveProject": true,
    "notes":"compile post-import"
  }'
```

### 9.2 TIA bridge (`http://127.0.0.1:8010`)
- `GET /health`
- `GET /api/status`
- `GET /api/openness/diagnostics`
- `POST /api/jobs/import|compile|export`
- `GET /api/jobs` / `GET /api/jobs/{jobId}`

Note bridge (dettagli che impattano il setup):
- il bridge legge `TIA_BRIDGE_MODE` (`stub`/`real`) e l’URL dell’agent via `TIA_WINDOWS_AGENT_URL` oppure `TIA_WINDOWS_HOST`+porta;
- quando `artifactPath` è una cartella, stage-a e invia all’agent Windows **solo** i file `*.xml` (i `.json` restano locali).

---

## 10) Troubleshooting essenziale

### Bridge “unreachable” / agent non configurato
- verifica `.env` su Linux (`TIA_WINDOWS_AGENT_URL`, `TIA_BRIDGE_MODE=real`);
- verifica reachability: dalla macchina Linux verso `http://<IP_VM>:8050/health`;
- verifica firewall VM Windows (script `tia_windows_agent/install-firewall-rule.ps1`).

Comandi rapidi (Linux):
- `curl -sS http://127.0.0.1:8010/health`
- `curl -sS http://127.0.0.1:8010/api/status`
- `curl -sS http://127.0.0.1:8000/api/tia/overview`

### Import OK ma compile fallisce
- trattare il bundle come **pacchetto** (non singolo XML);
- eseguire checklist su GRAPH/DB/FC e controllo simboli (`scripts/check_bundle_symbol_resolution.py`);
- usare `*_analysis.json` del bundle come diagnosi primaria.

Segnali tipici (cause ricorrenti):
- riferimenti GlobalVariable a member non dichiarati nel DB owner;
- mismatch datatype (es. BOOL vs REAL/TIME/DINT) quando l’IR contiene reti non booleane o `raw_flgnet`;
- dipendenze di progetto mancanti (CALL a blocchi non disponibili nei sorgenti forniti).

### Frontend mostra URL “strani”
Nel compose, `NEXT_PUBLIC_BACKEND_URL` e `NEXT_PUBLIC_TIA_BRIDGE_URL` sono attualmente valorizzate con un IP specifico
direttamente in `compose.dev.yml`. Se vuoi che il browser punti a un host diverso (es. `127.0.0.1` o un altro IP),
modifica `compose.dev.yml` (oppure introduci un meccanismo di override nel tuo workflow compose).
