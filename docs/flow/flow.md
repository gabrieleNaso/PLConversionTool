# Flusso del progetto (AWL -> Codex -> Python -> XML -> TIA)

Questa guida spiega end-to-end come un sorgente AWL diventa un pacchetto XML importabile in TIA Portal.

## 1) Input AWL (come entra in Python)

- I sorgenti AWL vivono in `data/input/`.
- Formati supportati: `.awl`, `.txt`, `.md`.
- Nei file `.md` viene usato il primo blocco fenced che contiene `NETWORK`.
- Il backend legge i file AWL e li passa al core converter come stringa (`awlSource`).

### Variante: input via Codex (quando scrivi a me il GRAPH da fare in XML)
Quando descrivi a Codex il GRAPH/il comportamento da generare:
1. Codex traduce la tua richiesta in un input strutturato per il tool
   (tipicamente AWL o parametri compatibili col core converter).
2. Codex salva il sorgente in `data/input/` oppure prepara un payload
   `awlSource` per le API backend.
3. Il flusso poi e' identico: analisi -> IR -> XML bundle in `data/output/`.

## 2) Analisi e IR (Python)

### Punto di ingresso
- Libreria core: `src/plc_converter/`.
- Modulo principale di analisi: `src/plc_converter/analysis.py`.

### Cosa produce
- Parsing AWL incrementale.
- Modello intermedio (IR) che descrive:
  - step, transizioni, timer, memorie, output;
  - topologia logica del sequenziatore;
  - regole di coerenza fra blocchi.

### Come l'AWL viene interpretato
- L'AWL viene letto come testo e segmentato per `NETWORK`.
- Il parser identifica:
  - step e transizioni;
  - logiche LAD/GRAPH equivalenti;
  - simboli e riferimenti che devono esistere nel `GlobalDB`.
- L'IR risultante e' usato per generare GRAPH, DB e FC in modo coerente.

### Cos'e' l'IR (in pratica)
L'IR e' la rappresentazione strutturata e normalizzata del sequenziatore,
non e' piu' testo AWL ma un modello dati con:
- sequenza di step e transizioni con guard e condizioni;
- mapping esplicito tra simboli/logiche e i blocchi di destinazione;
- metadati per costruire `FB GRAPH`, `GlobalDB`, `FC LAD`;
- vincoli di coerenza (nomi, riferimenti, contratti cross‑blocco).

In breve: l'IR e' il "contratto interno" del pacchetto XML che il generatore
deve produrre. Serve a garantire che FB/DB/FC restino sempre coerenti.

### Come viene creato l'IR (passi operativi)
1. Lettura file AWL e split per `NETWORK`.
2. Parsing di istruzioni e simboli.
3. Normalizzazione dei nomi e dei riferimenti.
4. Costruzione di nodi IR (step, transition, timer, memory, output).
5. Validazioni locali (coerenza minimale).
6. Emissione di una struttura IR riusabile dal generator.

## 3) Generazione XML

### Output del generator
Il generator produce sempre un **pacchetto coerente**:
- `FB GRAPH`
- `GlobalDB`
- `FC LAD`
- eventuali blocchi aggiuntivi richiesti dal caso

Gli artefatti finiscono in:
- `data/output/generated/<nome_bundle>/`

### Regola chiave
Il pacchetto e' indivisibile:
- nessun blocco va considerato isolato;
- ogni riferimento deve essere risolto tra `FB`, `DB`, `FC` e blocchi extra.

## 4) Backend API

Il backend espone:
- `POST /api/conversion/analyze`
- `POST /api/conversion/export`

Questo layer orchestra:
- invocazione del core converter;
- serializzazione XML;
- scrittura in `data/output/`.

Passaggi tipici:
1. `POST /api/conversion/analyze` riceve `awlSource`.
2. Il backend invoca `src/plc_converter/analysis.py`.
3. Il core produce IR + anteprime XML.
4. `POST /api/conversion/export` scrive i file in `data/output/generated/<bundle>/`.

## 5) Bridge TIA e Windows Agent

### TIA Bridge (`tia_bridge/`)
- boundary service Linux per chiamare Openness.
- monta `data/output/` e `data/tmp/` (creata on-demand).
 - usa `data/output/` per leggere gli XML da importare.
 - usa `data/tmp/` per staging e file intermedi.

### Windows Agent (`tia_windows_agent/`)
- processo .NET vicino a TIA Portal (VM Windows).
- riceve richieste HTTP dal bridge.
 - usa `artifactPath` per import/export e compila tramite Openness.

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

## 7) Cosa serve ai container Python (backend + tia-bridge)

### Backend (Python)
- `data/input/` per leggere AWL.
- `data/output/` per scrivere XML e report.
- accesso al core converter (`src/plc_converter/`).

### TIA Bridge (Python)
- `data/output/` per leggere XML da importare in TIA.
- `data/tmp/` per staging e file intermedi.
- accesso al Windows Agent via HTTP.

## 8) Dove guardare rapidamente

- Operazioni: `docs/guide/operations.md`
- Checklists: `docs/guide/workflow-checklists.md`
- Convenzioni: `docs/guide/conventions.md`
- Integrazione TIA: `docs/guide/tia-integration.md`
- Architettura: `docs/architettura/plant.uml`
