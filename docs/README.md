# Documentazione PLConversionTool

Questa cartella contiene solo la documentazione operativa attiva del progetto.
Per storico e specifiche consolidate: `docs/reference/`.

## Start here
- `operations.md`: comandi e workflow end-to-end (generazione, import, compile)
- `tia-integration.md`: bridge + agent Windows + VM setup
- `workflow-checklists.md`: checklist import/compile
- `conventions.md`: naming e gestione dataset
- `reports/daily-report-template.md`: template report
- `reference/report-2026-04-14.md`: report consolidato
- `reference/spec-awl-xml-tia-v20-2026-04-14.md`: specifica master

## Struttura repository (operativa)
- `backend/`
  Backend FastAPI. API, servizi applicativi, parser, generatori e test backend.
- `frontend/`
  UI Next.js per pilotare il workflow e visualizzare artefatti.
- `tia_bridge/`
  Boundary service per orchestrare import/compile/export via TIA Portal Openness.
- `src/`
  Libreria core condivisa del convertitore, separata da API/UI.
- `tests/`
  Test trasversali e integrazione.
- `scripts/`
  Script operativi e utility. Quando un comando diventa stabile, va qui o in `Makefile`.
- `docker/`
  Definizioni container di sviluppo.
- `data/input/`
  Sorgenti AWL da convertire in batch.
- `data/datasets/`
  Materiale di riferimento XML (golden, corpus, typicals).
- `data/output/`
  Output generati dal tool o da pipeline di trasformazione.
- `data/tmp/`
  Artefatti temporanei e staging.
- `docs/`
  Documentazione tecnica, workflow e regole operative.

## Regole pratiche
- I file XML di riferimento non vanno salvati in `data/output/`.
- I file generati dal tool non vanno salvati in `data/datasets/typicals/`.
- Un file validato con import riuscito e usato come riferimento stabile va promosso in `data/datasets/golden/`.
- Le logiche condivise del convertitore dovrebbero convergere in `src/`, evitando di spargerle tra UI, script e backend.
- Le integrazioni verso TIA/Openness non vanno mescolate nel backend di generazione: devono restare isolate in `tia_bridge/`.
- Gli esperimenti temporanei vanno in `data/tmp/`, non in root.
- `FB GRAPH`, `GlobalDB`, `FC LAD` e blocchi aggiuntivi vanno trattati come pacchetto coerente (non come XML indipendenti).

## Direzione consigliata (prossimi step)
1. Consolidare in `src/` il modello dati intermedio del sequenziatore.
2. Tenere in `backend/` solo API, orchestrazione e test di servizio.
3. Usare `data/datasets/golden/` come baseline per validator e regression test.
4. Salvare ogni XML generato in `data/output/` con naming coerente e report associato.
