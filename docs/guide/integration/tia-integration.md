# Integrazione TIA (bridge + agent Windows)

## TIA Bridge Service (`tia_bridge/`)

Il servizio `tia_bridge/` e' il boundary layer dedicato all'orchestrazione verso `TIA Portal Openness`.

### Perche' esiste
Il progetto separa due responsabilita':
- generazione deterministica degli XML (`backend/` e, progressivamente, `src/`)
- orchestrazione di import, compile, export e confronto verso TIA (`tia_bridge/`)

Questa separazione evita di mescolare nel backend applicativo dettagli runtime e prerequisiti specifici di TIA Portal.

### Stato attuale
Nel setup dev il container `tia-bridge`:
- e' sulla stessa rete Compose di `backend` e `frontend`
- espone una API minima di health/status
- monta `data/output/` e `data/tmp/` (creata on-demand) come aree condivise di scambio artefatti
- prepara il punto di integrazione verso una VM Windows che ospita TIA Portal
- dopo ogni job `import` accoda automaticamente un job `compile` usando lo stesso `targetPath/targetName`

### Variabili di configurazione principali
- `TIA_VMWARE_NETWORK_MODE`
- `TIA_WINDOWS_TRANSPORT`
- `TIA_WINDOWS_HOST`
- `TIA_WINDOWS_AGENT_PORT`
- `TIA_WINDOWS_AGENT_URL`

### Comportamento import -> compile
- `POST /api/jobs/import` inoltra l'import all'agent Windows
- se l'import viene accodato correttamente, il bridge accoda subito `POST /api/jobs/compile`
- il job compile riusa `targetPath` e `targetName` dell'import
- la risposta dell'import include `AutoCompileJobId` per tracciare entrambe le operazioni
- il bridge deve essere pensato come orchestratore di **bundle**, non come semplice uploader di XML isolati

## Windows VM + Agent (`tia_windows_agent/`)

### Architettura corretta
- il compose Linux non deve tentare di eseguire TIA Portal
- `tia-bridge` deve conoscere host e porta della VM Windows
- nella VM Windows esiste un piccolo agent applicativo che riceve richieste e invoca TIA Portal Openness localmente

### Perche' serve un agent Windows
Le DLL `TIA Portal Openness` vivono nell'ambiente Windows dove e' installato TIA.
Il container Linux non puo' caricarle direttamente via rete come un servizio standard.

### Rete VMware consigliata
- preferire `bridged` se vuoi che il container raggiunga la VM con un IP stabile
- usare `NAT` solo con regole chiare di forwarding e raggiungibilita'
- assegnare, se possibile, un IP statico o prenotato alla VM Windows

### Esempio variabili ambiente

```env
TIA_VMWARE_NETWORK_MODE=bridged
TIA_WINDOWS_TRANSPORT=http
TIA_WINDOWS_HOST=192.168.1.50
TIA_WINDOWS_AGENT_PORT=8050
TIA_WINDOWS_AGENT_URL=http://192.168.1.50:8050
```

### Materiale pronto da copiare nella VM
Cartella:
- `tia_windows_agent/`

Script pronti:
- `bootstrap-vm.ps1`
- `run-agent.ps1`
- `publish-agent.ps1`
- `install-firewall-rule.ps1`
- `start-agent.cmd`

Per i dettagli operativi di installazione e avvio, vedi `tia_windows_agent/agent.md`.

### Checklist minima lato Windows
- TIA Portal installato (versione target: V20)
- utente Windows nel gruppo locale `Siemens TIA Openness`
- agent Windows in ascolto sulla porta scelta
- firewall Windows aperto verso l'host/container che deve chiamarlo
- test di raggiungibilita' dalla macchina Linux verso la VM

## API minima dell'agent Windows

### Endpoint
- `GET /health`
  Stato base del servizio.
- `GET /api/status`
  Modalita', versione TIA e directory operative.
- `GET /api/openness/diagnostics`
  Diagnostica configurazione Siemens lato VM.
- `POST /api/jobs/import`
  Accoda un job di import di un artefatto XML in TIA.
- `POST /api/jobs/compile`
  Accoda un job di compilazione del progetto/blocco target.
- `POST /api/jobs/export`
  Accoda un job di export dal progetto TIA.
- `GET /api/jobs`
  Elenca i job in memoria.
- `GET /api/jobs/{jobId}`
  Dettaglio di un job.

### Payload base

```json
{
  "operation": "import",
  "artifactPath": "C:\\PLConversionTool\\output\\FB_Graph.xml",
  "projectPath": "C:\\PLConversionTool\\projects\\Demo.ap20",
  "targetPath": "Program blocks",
  "targetName": null,
  "saveProject": true,
  "notes": "import di validazione"
}
```

Campi principali:
- `targetPath`: path logico del `BlockGroup` di destinazione per l'import
- `targetName`: nome del blocco da esportare
- `saveProject`: se `true`, prova a salvare il progetto dopo l'operazione
- per `compile`, `targetPath` e `targetName` possono limitare la compile al blocco specifico

Note operative:
- `targetPath` parte da `Program blocks/`
- il bridge accoda automaticamente una `compile` post-import e restituisce `AutoCompileJobId`
- l'agent processa i job in modo seriale (scelta prudente per il runtime TIA)
- in modalita' `real` prova a caricare `Siemens.Engineering.dll` via reflection


## Regole operative consolidate per l'integrazione
- Il successo dell'import del singolo file non chiude la validazione: il criterio corretto e' import + compile del pacchetto.
- L'agent Windows non deve correggere XML sbagliati: deve eseguire operazioni TIA su artefatti gia' coerenti.
- La diagnostica ideale del bridge deve mantenere separati: errore di import strutturale, errore di compile cross-blocco, errore di raggiungibilita' della VM, errore applicativo Openness.
- In prospettiva, export e confronto post-compile devono essere trattati come parte della regressione del pacchetto generato, non come step indipendente.
- I bundle che derivano da tipici legacy possono essere importati nel progetto target solo dopo normalizzazione esplicita a `V20 / GRAPH V2`.
