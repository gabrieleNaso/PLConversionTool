# Flusso del progetto (AWL -> ChatGPT/Codex -> IR -> XML -> TIA)

Guida completa: da un sorgente AWL a un pacchetto XML importabile in TIA, con i passaggi operativi, i punti di controllo e le regole di coerenza oggi consolidate.


## 0) Qualificazione delle fonti di riferimento

Prima dell'analisi il convertitore deve distinguere sempre fra:
- **sorgente primario**: AWL reale da tradurre;
- **tipici XML target**: campioni compatibili col target corrente `TIA Portal V20 / GRAPH V2`;
- **tipici XML legacy**: campioni semanticamente utili ma basati su runtime diversi (es. `V6`), da usare solo per topologia, naming storico e significato funzionale;
- **documentazione normativa**: report e specifica master, che fissano cardinalita', regole hard e criteri di validazione.

Il convertitore non deve mescolare questi piani: il target finale resta `V20 / GRAPH V2`.

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
- L'AWL viene letto come testo e segmentato per `NETWORK` e per famiglie logiche ricorrenti del sequenziatore.
- Il parser identifica:
  - step e transizioni;
  - logiche LAD/GRAPH equivalenti (incluse guardie booleane con `AND/OR/NOT`);
  - simboli e riferimenti che devono esistere nel `GlobalDB`;
  - famiglie funzionali ricorrenti: allarmi, memorie/ausiliari, sequenza, manuale/automatico, emergenza/fault, uscite.

### Come l'IR viene creato (passi operativi)
1. **Split per `NETWORK`** e tokenizzazione (istruzioni, simboli, indirizzi).
2. **Parsing semantico**: ogni network diventa logica sequenziale (step, transizioni, guard, timer, set/reset).
   - Per le transizioni pilotate da `Trs` viene preservata la struttura booleana delle condizioni (`A/AN/O/ON` e gruppi con parentesi).
3. **Normalizzazione**: naming deterministico e riferimenti uniformati.
4. **Costruzione IR**: grafo/struttura di nodi (step, transition, timer, mapping DB, ownership delle variabili globali, riferimenti simbolici completi).
5. **Validazione**: coerenza minima e contratti cross-blocco (riferimenti presenti, topologia consistente, owner DB, branch path, leaf name, cardinalita' del pacchetto).

### Cos'e' l'IR (cosa rappresenta)
L'IR e' il modello dati del sequenziatore:
- topologia di step e transizioni;
- passo iniziale determinato da `step_number = 1` quando disponibile;
- eventuali backbone strutturali speciali quando richiesti dal caso;
- condizioni/guard;
- simboli e variabili richieste dal `GlobalDB`;
- owner DB, branch path e leaf name delle variabili globali;
- mapping coerente verso `FB GRAPH`, `GlobalDB`, `FC LAD`.

In pratica e' il **contratto interno** che garantisce coerenza tra i blocchi.

### Da IR a XML
1. **Builder**: genera `FB GRAPH`, `GlobalDB`, `FC LAD` (e blocchi extra se servono).
2. **Allineamento**: simboli/guard replicati coerentemente tra FB/DB/FC.
3. **Serializzazione**: output XML compatibile TIA con naming member deterministico e owner DB coerente.
4. **Scrittura**: `data/output/generated/<nome_bundle>/`.

## 3) Generazione XML (pacchetto coerente)

Il generator produce sempre un **pacchetto coerente**:
- `1 x FB GRAPH` della sequenza
- `N x GlobalDB` applicativi e di supporto
- `M x FC LAD` di supporto
- eventuali blocchi aggiuntivi richiesti dal caso

Regola chiave:
- nessun blocco va considerato isolato;
- ogni riferimento deve essere risolto tra `FB`, `DB`, `FC` e blocchi extra;
- la riuscita reale non e' l'import del singolo XML, ma la coerenza del bundle importato e compilato;
- i campioni legacy servono a capire il comportamento, non a imporre `GraphVersion`, datatype runtime o serializer finale.

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
4. La `compile` va richiesta esplicitamente con `POST /api/tia/jobs/compile` quando serve.

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

- Operazioni: `docs/guide/operations/operations.md`
- Checklists: `docs/guide/checklists/workflow-checklists.md`
- Convenzioni: `docs/guide/standards/conventions.md`
- Integrazione TIA: `docs/guide/integration/tia-integration.md`
