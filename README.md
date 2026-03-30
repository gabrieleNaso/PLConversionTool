# PLConversionTool

Repository di lavoro per il progetto di conversione di sequenziatori PLC da `AWL` a `GRAPH` in `TIA Portal V20` tramite generazione e validazione di XML.

## Obiettivo del progetto
- analizzare logiche sequenziali AWL e ricostruirne la macchina a stati;
- generare blocchi `SW.Blocks.FB` GRAPH V2 importabili in TIA Portal;
- generare il `GlobalDB` companion separato, mantenendo gli statici runtime interni obbligatori del GRAPH;
- predisporre un tool deterministico con backend e frontend per automatizzare il workflow.

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
- `docker/` + `compose.dev.yml`: ambiente di sviluppo standardizzato
- `datasets/`: tipici, corpus e golden sample XML
- `output/`: file generati dal tool
- `tmp/`: artefatti temporanei di lavoro

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

In questo modo `git`, fetch/pull e dipendenze private raggiungibili via GitHub restano utilizzabili anche dentro backend e frontend.

Servizi attesi:
- backend: `http://localhost:8000`
- frontend: `http://localhost:3000`

## Comandi utili
- `make build`: build immagini di sviluppo
- `make up`: avvia backend e frontend
- `make down`: ferma i servizi
- `make logs`: segue i log dei container
- `make shell-backend`: shell nel container backend
- `make shell-frontend`: shell nel container frontend
- `make run-backend`: avvio backend con porte esposte
- `make test-backend`: esegue i test Python
- `make fmt-backend`: formatta il backend con Ruff
- `make lint-backend`: lint del backend con Ruff
- `make clean`: pulisce `tmp/` e `output/`

## Struttura della repository
- `backend/`: API, servizi e test backend già avviati
- `frontend/`: interfaccia Next.js
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
