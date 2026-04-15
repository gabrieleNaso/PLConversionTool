# Flusso del progetto (AWL -> Codex -> Python -> XML -> TIA)

Guida completa: da un sorgente AWL a un pacchetto XML importabile in TIA, con i passaggi operativi e i punti di controllo.

## 1) Input (AWL)

- I sorgenti AWL vivono in `data/input/`.
- Formati supportati: `.awl`, `.txt`, `.md` (nei `.md` si usa il primo blocco fenced con `NETWORK`).
- Il backend legge il file AWL e lo passa al core converter come stringa (`awlSource`).

### Variante: input via Codex
Quando descrivi a Codex il GRAPH/comportamento:
1. Codex traduce la richiesta in un input strutturato (AWL o parametri compatibili col core converter).
2. Salva il sorgente in `data/input/` oppure invia `awlSource` via API.
3. Il flusso resta identico: analisi -> IR -> XML.

## 2) Analisi e IR (Python)

### Punto di ingresso
- Libreria core: `src/plc_converter/`.
- Modulo principale: `src/plc_converter/analysis.py`.

### Da cosa deriva l'IR
L'IR nasce da:
- testo AWL completo;
- regole di mapping (AWL -> GRAPH/DB/FC);
- vincoli di coerenza (naming e contratti cross‑blocco).

### Come l'AWL viene interpretato
- L'AWL viene letto come testo e segmentato per `NETWORK`.
- Il parser identifica:
  - step e transizioni;
  - logiche LAD/GRAPH equivalenti (incluse guardie booleane con `AND/OR/NOT`);
  - simboli e riferimenti che devono esistere nel `GlobalDB`.

### Come l'IR viene creato (passi operativi)
1. **Split per `NETWORK`** e tokenizzazione (istruzioni, simboli, indirizzi).
2. **Parsing semantico**: ogni network diventa logica sequenziale (step, transizioni, guard, timer, set/reset).
   - Per le transizioni pilotate da `Trs` viene preservata la struttura booleana delle condizioni (`A/AN/O/ON` e gruppi con parentesi).
3. **Normalizzazione**: naming deterministico e riferimenti uniformati.
4. **Costruzione IR**: grafo/struttura di nodi (step, transition, timer, mapping DB).
5. **Validazione**: coerenza minima (riferimenti presenti, topologia consistente).

### Cos'e' l'IR (cosa rappresenta)
L'IR e' il modello dati del sequenziatore:
- topologia di step e transizioni;
- condizioni/guard;
- simboli e variabili richieste dal `GlobalDB`;
- mapping coerente verso `FB GRAPH`, `GlobalDB`, `FC LAD`.

In pratica e' il **contratto interno** che garantisce coerenza tra i blocchi.

### Da IR a XML
1. **Builder**: genera `FB GRAPH`, `GlobalDB`, `FC LAD` (e blocchi extra se servono).
2. **Allineamento**: simboli/guard replicati coerentemente tra FB/DB/FC.
3. **Serializzazione**: output XML compatibile TIA.
4. **Scrittura**: `data/output/generated/<nome_bundle>/`.

## 3) Generazione XML (pacchetto coerente)

Il generator produce sempre un **pacchetto coerente**:
- `FB GRAPH`
- `GlobalDB`
- `FC LAD`
- eventuali blocchi aggiuntivi richiesti dal caso

Regola chiave:
- nessun blocco va considerato isolato;
- ogni riferimento deve essere risolto tra `FB`, `DB`, `FC` e blocchi extra.

## 4) Backend API

Endpoint principali:
- `POST /api/conversion/analyze`
- `POST /api/conversion/export`

Flusso tipico:
1. `analyze` riceve `awlSource`.
2. Il core produce IR + anteprime XML.
3. `export` scrive i file in `data/output/generated/<bundle>/`.
   - Prima della scrittura, il bundle target viene ricreato pulito per evitare residui XML di run precedenti.

## 5) Bridge TIA e Windows Agent

### TIA Bridge (`tia_bridge/`)
- Servizio Linux che parla con Openness.
- Usa `data/output/` per leggere gli XML.
- Usa `data/tmp/` per staging (creata on-demand).

### Windows Agent (`tia_windows_agent/`)
- Processo .NET vicino a TIA (VM Windows).
- Riceve richieste HTTP dal bridge.
- Usa `artifactPath` per import/export e compile.

### Flusso import/compile
1. Backend chiama `POST /api/tia/jobs/import`.
2. Bridge inoltra all'agent Windows.
3. L'agent usa le DLL Openness per importare in TIA.
4. Il bridge accoda automaticamente una `compile` sullo stesso target.

## 6) Output finale in TIA

Il risultato corretto e' un progetto TIA che:
- importa senza errori;
- compila il pacchetto coerente;
- mantiene naming e simboli allineati.

## 7) Cosa serve ai container Python

### Backend (Python)
- `data/input/` per leggere AWL.
- `data/output/` per scrivere XML e report.
- accesso al core converter (`src/plc_converter/`).

### TIA Bridge (Python)
- `data/output/` per leggere XML da importare.
- `data/tmp/` per staging.
- accesso al Windows Agent via HTTP.

## 8) Dove guardare rapidamente

- Operazioni: `docs/guide/operations.md`
- Checklists: `docs/guide/workflow-checklists.md`
- Convenzioni: `docs/guide/conventions.md`
- Integrazione TIA: `docs/guide/tia-integration.md`
- Architettura: `docs/architettura/plant.uml`
