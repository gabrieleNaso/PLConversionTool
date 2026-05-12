# Convenzioni e dataset

## Gerarchia delle regole
- Questo documento raccoglie convenzioni operative e di repository.
- Le regole hard di traduzione e serializer stanno nella specifica master corrente.
- In caso di conflitto fra convenzione generica e tipico XML validato o regola della specifica, prevale sempre la specifica master.


## Naming file (artefatti XML)
Per il generatore corrente, usare naming deterministico aderente al profilo blocchi:
- **FB GRAPH**: `FB_<SequenceName>_GRAPH_auto.xml`
- **GlobalDB di famiglia**: `DB<XX>_<SequenceName>_<family>_db_auto.xml`
- **FC LAD di famiglia**: `FC<XX>_<SequenceName>_<family>_lad_auto.xml`

Suggerimento: usare suffissi di variante solo quando aggiungono informazione utile:
- `strict`: serializer/validator "hard rules" attivo
- `rebased`: wrapper/struttura riallineata senza cambiare la logica interna
- `golden`: campione import riuscito da usare come riferimento stabile

## Naming strutture nel GlobalDB (consigliato)
Organizzare per macro-strutture funzionali, evitando DB piatti, **quando il caso non richiede il mantenimento di naming storici gia' fissati dai tipici**:
- `Cmd` (comandi)
- `Fb` (feedback)
- `Par` (parametri/ricetta)
- `En` (enable/consensi)
- `Diag` (diagnostica)
- `Hmi` (dati HMI)
- `Map` (mapping AWL->GRAPH / supporto tool)

Nota importante:
- per i DB fissi del progetto e per i bundle che devono restare aderenti ai tipici reali, il generatore puo' dover preservare naming storici come `Transitions`, `Memory`, `Seq Status`, `Conditions`, `AUX`, `AUX_MEMORY`, ecc.;
- la normalizzazione va applicata all'identita' logica interna, non cancellando automaticamente il nome finale richiesto dal contratto XML.

## Regole pratiche
- **Stabilita'**: il naming deve essere deterministico (stesso input -> stessi simboli).
- **Allineamento**: simboli referenziati nel `FlgNet` devono esistere e avere naming identico tra FB/DB.
- **Evitare ambiguita'**: niente acronimi non condivisi; preferire naming impiantistico.
- **Workflow strict DB (Excel)**: la logica transizioni GRAPH puo' referenziare operandi completi, ma la dichiarazione member DB deve seguire il catalogo strict:
  - Excel: foglio `operands`.
- **Workflow AI-first (IR JSON)**: usare di default `strict_operand_catalog: false` cosi' il generatore dichiara automaticamente i simboli usati in GRAPH/FC nei DB corretti.
- **Workflow IR JSON strict** (`strict_operand_catalog: true`): equivalente concettuale dell'Excel strict; richiede `operand_catalog` completo + ownership esplicita via `operand_categories`/`support_members`.

## Convenzioni logiche AWL -> Guard XML
- **Operatori booleani**:
  - `A/U` -> `AND`
  - `AN/UN` -> `AND NOT`
  - `O` -> `OR`
  - `ON` -> `OR NOT`
- **Gruppi parentesizzati**:
  - i blocchi `A(...)` / `O(...)` vanno mantenuti come sottogruppi in `guard_expression`.
- **Passi sorgente**:
  - i token step (`Sxx`) usati per identificare la sorgente transizione non devono inquinare la parte semantica della guardia.
- **Bit presenza pezzo**:
  - quando esiste un operando di presenza (`DB*.DBX23.*` o `*.PT/PT_END`) e un punto di split, le guardie delle uscite devono essere rese mutuamente esclusive (`presence` / `NOT presence`) per evitare transizioni vuote o doppie `TRUE`.
- **Output fisiche**:
  - riconoscere sia notazione `Axx(.x)` sia `Qxx(.x)` per mapping uscite.

## Regola IR JSON: simboli puntati
- Nel flusso IR JSON (AI-first) i simboli con `.` sono trattati come **leaf token** (sanitizzati) per evitare DB esterni non importati (“DB fantasma”).
- Eccezione: step del GRAPH e accesso `.X` restano strutturati e puntano al DB istanza del GRAPH (`ZZ_DB15...`).

## Datasets e campioni

### Obiettivo
Tenere separati:
- campioni di riferimento (import riuscito, golden sample)
- corpus di reverse engineering (es. `Type_*.xml`)
- output generati dal tool (che vanno in `work/output/`, non qui)

### Struttura consigliata
- `datasets/corpus/`
  - (opzionale) materiale grezzo di reverse engineering
- `cases/`
  - `input/` (sorgenti AWL) + `expected_output/` (attesi) **versionati**
- `datasets/typicals/`
  - `graph_fb/` (tipici FB GRAPH per reverse engineering/confronto)
  - `globaldb/` (tipici GlobalDB)
  - `fc_lad/` (tipici FC LAD)

### Regola d'oro
Se un file serve da riferimento stabile per debug/validator, deve stare in `datasets/typicals/` (o in una cartella `datasets/golden/` se viene reintrodotta).


## Naming globale obbligatorio nel bundle
Ogni variabile globale deve essere trattata come record strutturato, non come semplice stringa di nome.

Campi minimi da preservare nell'IR:
- `owner_db`: DB proprietario del simbolo (`T1-A ARUNC`, `T1-A ARUNC HMI`, `DB81-OPIN`, ...)
- `branch_path`: percorso dei branch interni (`Transitions`, `Conditions/SC/Conditions`, `Memory`, ...)
- `leaf_name`: nome finale del member (`Safe`, `n1`, `Cycle start request`, ...)
- `serialized_path`: path finale usato nel `FlgNet`

Regole pratiche:
- il naming corretto non e' solo il suffisso finale: senza owner DB e path completo il riferimento non e' realmente collegato;
- i riferimenti con spazi, numeri o naming storici validati dai tipici non vanno riscritti in forma semplificata se il target del bundle li richiede;
- un simbolo orfano, abbreviato o serializzato con path incompleto va considerato errore bloccante.
- il target deve restare **solo simbolico**: non usare indirizzi fisici (`DB202.DBX62.1`, `I30.1`, ...) come nome member o come `serialized_path`; se il sorgente li contiene, vanno usati solo per determinare ownership/mapping.
- eccezione di tracciabilità (solo IR/report): in `external_refs` può comparire anche l'evidenza raw di un indirizzo (soprattutto per DB esterni tipo `DB81-OPIN` / `DB82-OPOUT`) a fianco di un alias strutturato (`DB81.Pxxx`, `DB82.Lxxx`), ma questo non deve "bucare" nel naming dei member e nei path XML finali.
- unicita': i nomi member devono essere univoci anche ignorando il case (evitare collisioni tipo `T1_Auto` vs `t1_auto`) e non devono mai risultare vuoti dopo sanitizzazione.

Esempi coerenti coi tipici:
- `T1-A ARUNC -> Transitions -> Safe`
- `T1-A ARUNC HMI -> Conditions -> SC -> Conditions -> n1`
- `T1-A ARUNC -> Memory -> Piece Transfered`

## Regole di corpus e target
- I tipici `V6` o di runtime legacy vanno marcati come **semantic_only** o equivalente nella conoscenza del progetto.
- I golden sample di target devono essere coerenti con `TIA Portal V20 / GRAPH V2`.
- Un file puo' essere ottimo per reverse engineering semantico ma inadatto come pattern di serializer finale.
