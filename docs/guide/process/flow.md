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

- I sorgenti AWL vivono in `work/input/`.
- Formati supportati: `.awl`, `.txt`, `.md` (nei `.md` si usa il primo blocco fenced con `NETWORK`).
- Il backend legge il file AWL e lo passa al core converter come stringa (`awlSource`).
- Quando in `work/input/` sono presenti più blocchi correlati (es. FC sequenza + FC runtime chiamate), il tool può eseguire un'analisi **di progetto**: indicizza i blocchi disponibili e prova a risolvere le dipendenze `CALL` durante l'analisi del blocco principale.

### Variante: input via Codex/AI (AI-first)
Quando usi Codex/AI come “interprete” dell'AWL:
1. Codex/AI analizza il sorgente AWL e costruisce direttamente l'IR (JSON) secondo le regole e i casi.
2. Salva l’IR in `work/input/ir_json/`.
3. Il tool viene usato solo per `IR JSON -> XML` (`make gen-ir ...`).

Nota strict:
- se l’IR ha `strict_operand_catalog: true`, ogni variabile usata nelle espressioni deve essere:
  - presente in `operand_catalog`;
  - dichiarata nel DB owner (tipicamente aggiunta in `support_members` con la `category` corretta).

## 2) Analisi e IR (Python)

### Punto di ingresso
- Libreria core: `src/plc_converter/`.
- Modulo principale: `src/plc_converter/analysis.py`.

### Da cosa deriva l'IR
L'IR nasce da:
- testo AWL completo;
- regole di mapping (AWL -> GRAPH/DB/FC);
- vincoli di coerenza (naming e contratti cross‑blocco).
- casi di riferimento quando disponibili (es. `cases/expected_output/expected_outputN/`) usati per estrarre regole generali e fare regressione sul generatore.

### Come l'AWL viene interpretato
- L'AWL viene letto come testo e segmentato per `NETWORK` e per famiglie logiche ricorrenti del sequenziatore.
- Il parser identifica:
  - step e transizioni;
  - logiche LAD/GRAPH equivalenti (incluse guardie booleane con `AND/OR/NOT`);
  - scritture non booleane (pattern `L ... / T ...`) da tradurre come box LAD `Move` nel backend HMI;
  - simboli e riferimenti che devono esistere nel `GlobalDB`;
  - famiglie funzionali ricorrenti: allarmi, memorie/ausiliari, sequenza, manuale/automatico, emergenza/fault, uscite.

### Come l'IR viene creato (passi operativi)
1. **Split per `NETWORK`** e tokenizzazione (istruzioni, simboli, eventuali indirizzi presenti nel sorgente: usati solo come input di mapping, non come naming nell'output).
2. **Parsing semantico**: ogni network diventa logica sequenziale (step, transizioni, guard, timer, set/reset).
   - Per le transizioni pilotate da `Trs` viene preservata la struttura booleana delle condizioni (`A/AN/O/ON` e gruppi con parentesi).
3. **Normalizzazione**: naming deterministico e riferimenti uniformati.
   - include canonicalizzazione dei token step quando il sorgente usa forme zero‑padded (`S01` -> `S1`) per mantenere coerenza con il catalogo step derivato dal GRAPH.
4. **Costruzione IR**: grafo/struttura di nodi (step, transition, timer, mapping DB, ownership delle variabili globali, riferimenti simbolici completi).
5. **Validazione**: coerenza minima e contratti cross-blocco (riferimenti presenti, topologia consistente, owner DB, branch path, leaf name, cardinalita' del pacchetto).
   - gate hard: nessuna variabile globale "orfana"; tutto cio' che viene referenziato in `FB/FC/GRAPH` deve esistere davvero in un DB owner con naming simbolico coerente.
   - se l'AWL contiene `CALL` a blocchi non presenti nei sorgenti disponibili, il report segnala una dipendenza mancante (warning `missing_called_blocks`); se invece i blocchi chiamati sono presenti in `work/input/`, la dipendenza viene correlata e riportata come analisi di progetto.
   - quando è presente un runtime sequenziatore esterno (es. un blocco stile `FC32`), il convertitore può usare tale contesto per migliorare l'estrazione delle transizioni (alias vista bit passo tipo `Mxx.Syy` -> `Syy`, confinata al prefisso del sequenziatore locale) e per produrre un contratto dati sequenziatore più pulito.

### Cos'e' l'IR (cosa rappresenta)
L'IR e' il modello dati del sequenziatore:
- topologia di step e transizioni;
- passo iniziale determinato da `step_number = 1` quando disponibile;
- eventuali backbone strutturali speciali quando richiesti dal caso;
- condizioni/guard;
- simboli e variabili richieste dal `GlobalDB`;
- owner DB, branch path e leaf name delle variabili globali;
- hint semantici opzionali (es. `step_roles`) per ruoli ricorrenti (entry/manual/fault/emergency/end_cycle/...), senza hard-code di numeri passo;
- mapping coerente verso `FB GRAPH`, `GlobalDB`, `FC LAD`.

In pratica e' il **contratto interno** che garantisce coerenza tra i blocchi.

### Da IR a XML
1. **Builder**: genera `FB GRAPH`, `GlobalDB`, `FC LAD` (e blocchi extra se servono).
   - opzionale: un `TARGET_PROFILE` può influenzare solo questa fase (IR -> XML: naming/numbering/serializer).
2. **Allineamento**: simboli/guard replicati coerentemente tra FB/DB/FC.
3. **Serializzazione**: output XML compatibile TIA con naming member deterministico e owner DB coerente.
4. **Scrittura**: `work/output/generated/<nome_bundle>/`.

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
3. `export` scrive i file in `work/output/generated/<bundle>/`.
   - Prima della scrittura, il bundle target viene ricreato pulito per evitare residui XML di run precedenti.

## 5) Bridge TIA e Windows Agent

### TIA Bridge (`tia_bridge/`)
- Servizio Linux che parla con Openness.
- Usa `work/output/` per leggere gli XML.
- Usa `work/tmp/` per staging (creata on-demand).

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
- `work/input/` per leggere AWL.
- `work/output/` per scrivere XML e report.
- accesso al core converter (`src/plc_converter/`).

### TIA Bridge (Python)
- `work/output/` per leggere XML da importare.
- `work/tmp/` per staging.
- accesso al Windows Agent via HTTP.

## 8) Dove guardare rapidamente

- Operazioni: `docs/guide/operations/operations.md`
- Checklists: `docs/guide/checklists/workflow-checklists.md`
- Convenzioni: `docs/guide/standards/conventions.md`
- Integrazione TIA: `docs/guide/integration/tia-integration.md`
- Casi traduzione/regressione: `cases/expected_output/expected_outputN/`
