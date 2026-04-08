# PLConversionTool

Repository di lavoro per il progetto di conversione di sequenziatori PLC da `AWL` a `GRAPH` in `TIA Portal V20` tramite generazione e validazione di XML.

## Obiettivo del progetto
- analizzare logiche sequenziali AWL e ricostruirne la macchina a stati;
- generare blocchi `SW.Blocks.FB` GRAPH V2 importabili in TIA Portal;
- generare il `GlobalDB` companion separato, mantenendo gli statici runtime interni obbligatori del GRAPH;
- predisporre un tool deterministico con backend, frontend e adapter TIA per automatizzare il workflow.

Il contesto tecnico consolidato è descritto in [Contesto_progetto.md](/home/administrator/PLConversionTool/Contesto_progetto.md).

## Da dove partire
- [Indice documentazione](/home/administrator/PLConversionTool/docs/INDEX.md)
- [Report tecnico consolidato](/home/administrator/PLConversionTool/Contesto_progetto.md)
- [Struttura operativa repository](/home/administrator/PLConversionTool/docs/project-structure.md)
- [Checklist import TIA / GRAPH / DB / FC](/home/administrator/PLConversionTool/docs/workflow/import-checklists.md)
- [Convenzioni naming](/home/administrator/PLConversionTool/docs/conventions/naming.md)
- [Guida dataset e campioni](/home/administrator/PLConversionTool/docs/datasets/README.md)

## Stack attuale
- `backend/`: FastAPI minimale per API e logica del tool
- `frontend/`: Next.js per UI di supporto al workflow
- `tia_bridge/`: servizio dedicato al layer `TIA Portal Openness`, separato dalla generazione XML
- `tia_windows_agent/`: agent .NET da eseguire nella VM Windows che ospita TIA Portal
- `docker/` + `compose.dev.yml`: ambiente di sviluppo standardizzato
- `datasets/`: tipici, corpus e golden sample XML
- `output/`: file generati dal tool
- `tmp/`: artefatti temporanei di lavoro

## Stato attuale

Il progetto non e' piu' solo nella fase di generazione XML: oggi esiste anche una pipeline reale di collegamento a `TIA Portal` tramite VM Windows.

Stato verificato:

- il compose Linux espone `backend`, `frontend` e `tia-bridge`;
- `tia-bridge` punta alla VM Windows che ospita `TIA Portal`;
- l'agent Windows si avvia localmente su `:8050`;
- la VM Linux raggiunge correttamente l'agent Windows via rete;
- l'agent Windows apre `TIA Portal Openness` in modalita' reale;
- l'agent apre il progetto `.ap20` configurato;
- l'agent trova il `PlcSoftware` del progetto;
- l'agent arriva a invocare realmente `PlcBlockComposition.Import(...)`;
- gli errori Openness vengono intercettati e riportati nel `detail` dei job.

Questo significa che l'intera catena tecnica:

- Linux -> `tia-bridge` -> VM Windows -> `TIA Portal Openness`

e' stata verificata fino al punto dell'import reale nel progetto TIA.

## Punto Di Blocco Attuale

Il blocco reale emerso nei test non e' piu' nel codice dell'agent o nella connettivita', ma nel licensing di TIA:

- l'import di un blocco `SW.Blocks.FB` parte davvero;
- TIA tenta di creare il blocco;
- l'operazione viene rifiutata con `LicenseNotFoundException`;
- il messaggio esplicito restituito da TIA indica che manca la licenza `STEP 7 Professional`.

In altre parole:

- l'agent Windows ora funziona;
- Openness ora funziona;
- il progetto TIA viene aperto;
- la chiamata reale di import viene eseguita;
- il rifiuto arriva da TIA per requisito di licenza, non per errore applicativo del progetto.

## Cosa Fa Oggi L'Agent Windows

Il modulo [tia_windows_agent/README.md](/home/administrator/PLConversionTool/tia_windows_agent/README.md) contiene solo la guida operativa, ma sul piano funzionale oggi l'agent:

- espone `GET /health`;
- espone `GET /api/status`;
- espone `GET /api/openness/diagnostics`;
- espone `POST /api/jobs/import`;
- espone `POST /api/jobs/compile`;
- espone `POST /api/jobs/export`;
- espone `GET /api/jobs`;
- espone `GET /api/jobs/{jobId}`;
- accoda i job in memoria;
- li esegue in background;
- li processa in modo seriale;
- carica `Siemens.Engineering.dll`;
- apre `TiaPortal`;
- apre il progetto `.ap20`;
- prova compile/import/export via reflection sulle API Siemens disponibili;
- intercetta in modo esplicito errori come `EngineeringSecurityException` e `LicenseNotFoundException`.

## Implicazione Tecnica

Questo repository ha quindi gia' validato la parte architetturale piu' rischiosa del layer TIA:

- adapter Linux separato da runtime Windows;
- uso reale di `TIA Portal Openness`;
- isolamento del layer di orchestrazione rispetto alla generazione XML;
- diagnostica degli errori TIA a livello di job.

I prossimi passi pratici non sono piu' "far parlare l'agent con TIA", ma:

1. rendere disponibile una licenza `STEP 7 Professional` sulla VM;
2. ripetere l'import reale del blocco;
3. estendere la stessa pipeline a compile ed export con esiti consolidati.

## Quickstart
Da root progetto:

```bash
cp .env.example .env
export HOME="$HOME"
make doctor
make build
make up
make logs
```

Se hai collegato GitHub via SSH sul tuo host, il setup di sviluppo inoltra nei container:
- `~/.gitconfig`
- `~/.ssh`

In questo modo `git`, fetch/pull e dipendenze private raggiungibili via GitHub restano utilizzabili anche dentro `tia-bridge`, backend e frontend.

Servizi attesi:
- tia-bridge: `http://localhost:8010`
- backend: `http://localhost:8000`
- frontend: `http://localhost:3000`

Nota architetturale:
il container `tia-bridge` non esegue TIA Portal dentro Linux. Rappresenta il boundary service dedicato all'orchestrazione Openness, da collegare al target Windows/TIA reale mantenendo separato questo layer dal backend applicativo.

Nel caso in cui `TIA Portal` giri su una VM Windows VMware, il pattern corretto e':
- `backend/frontend` -> `tia-bridge` nel compose Linux;
- `tia-bridge` -> agent di integrazione esposto dalla VM Windows;
- agent Windows -> `TIA Portal Openness` locale alla VM.

`TIA Portal Openness` non e' una API remota nativa: per lavorare con una VM Windows serve quindi un servizio lato Windows che faccia da adapter verso TIA.

## Comandi utili
- `make build`: build immagini di sviluppo
- `make up`: avvia `tia-bridge`, backend e frontend
- `make down`: ferma i servizi
- `make logs`: segue i log dei container
- `make shell-backend`: shell nel container backend
- `make shell-frontend`: shell nel container frontend
- `make shell-tia`: shell nel container `tia-bridge`
- `make run-backend`: avvio backend con porte esposte
- `make run-tia`: avvio `tia-bridge` con porta esposta
- `make test-backend`: esegue i test Python
- `make fmt-backend`: formatta il backend con Ruff
- `make lint-backend`: lint del backend con Ruff
- `make clean`: pulisce `tmp/` e `output/`

## Struttura della repository
- `backend/`: API, servizi e test backend già avviati
- `frontend/`: interfaccia Next.js
- `tia_bridge/`: adapter service per il layer TIA / Openness
- `tia_windows_agent/`: agent Windows compatibile con Openness usato per import/compile/export reali verso TIA
- `docker/`: Dockerfile di sviluppo
- `datasets/typicals/`: XML di riferimento usati per reverse engineering
- `datasets/corpus/`: corpus da analizzare e classificare
- `datasets/golden/`: file importati con successo da usare come riferimento stabile
- `docs/`: documentazione tecnica, workflow e convenzioni
- `scripts/`: script di progetto da usare al posto di comandi improvvisati
- `src/`: futura libreria core del convertitore deterministico
- `tests/`: test cross-modulo o end-to-end del tool
- `output/`: XML e report prodotti dal tool
- `tmp/`: file temporanei di runtime

## Nota importante
La repository non va più trattata come un template generico: il focus è il dominio `PLC AWL -> GRAPH XML`. La documentazione e le cartelle sono state riallineate a questo obiettivo per facilitare i prossimi step di implementazione.
