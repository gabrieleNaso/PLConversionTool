# Struttura operativa della repository

Questa repository serve a portare il progetto da analisi manuale e reverse engineering XML a tool deterministico per la conversione `AWL -> GRAPH`.

## Vista per responsabilita'

- `backend/`
  Backend FastAPI. Qui vivono API, servizi applicativi, parser, generatori e test backend locali.
- `frontend/`
  Interfaccia Next.js per pilotare il workflow, mostrare esiti, errori e artefatti generati.
- `tia_bridge/`
  Servizio dedicato al layer di orchestrazione `TIA Portal Openness`, separato dal backend che genera XML.
- `src/`
  Spazio riservato alla libreria core condivisa del convertitore, separata dalla superficie API/UI.
- `tests/`
  Test trasversali, integrazione o end-to-end non legati solo al backend.
- `scripts/`
  Script operativi e utility di progetto. Se un comando diventa stabile, va qui o in `Makefile`.
- `docker/`
  Definizioni container di sviluppo.
- `datasets/`
  Materiale di riferimento XML, separato per ruolo.
- `output/`
  Output generati dal tool o da pipeline di trasformazione.
- `tmp/`
  Artefatti temporanei, staging, file intermedi.
- `docs/`
  Documentazione tecnica, workflow, naming e report.

## Regole pratiche

- I file XML di riferimento non vanno salvati in `output/`.
- I file generati dal tool non vanno salvati in `datasets/typicals/`.
- Un file validato con import riuscito e usato come riferimento stabile va promosso in `datasets/golden/`.
- Le logiche condivise del convertitore dovrebbero convergere in `src/`, evitando di spargerle tra UI, script e backend.
- Le integrazioni verso TIA/Openness non vanno mescolate nel backend di generazione: devono restare isolate nel servizio `tia_bridge/`.
- Gli esperimenti temporanei vanno in `tmp/`, non in root.

## Organizzazione dataset

- `datasets/typicals/`
  Tipici di reverse engineering gia' raccolti.
- `datasets/corpus/`
  Materiale grezzo da classificare o usare come corpus di analisi.
- `datasets/golden/`
  Campioni importati con successo da usare come target di confronto.

## Direzione consigliata per i prossimi step

1. Consolidare in `src/` il modello dati intermedio del sequenziatore.
2. Tenere in `backend/` solo API, orchestrazione e test di servizio.
3. Usare `datasets/golden/` come baseline per validator e regression test.
4. Salvare ogni XML generato in `output/` con naming coerente e report associato.
