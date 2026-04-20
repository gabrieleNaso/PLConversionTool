# Convenzioni e dataset

## Gerarchia delle regole
- Questo documento raccoglie convenzioni operative e di repository.
- Le regole hard di traduzione e serializer stanno nella specifica master corrente.
- In caso di conflitto fra convenzione generica e tipico XML validato o regola della specifica, prevale sempre la specifica master.


## Naming file (artefatti XML)
- **FB GRAPH**: `FB_<AreaOImpianto>_<Funzione>_GRAPH_<variant>.xml`
  - es.: `FB_BottlingLine_GRAPH_strict_rebased.xml`
- **GlobalDB del pacchetto**: `DB_<AreaOImpianto>_<Funzione>_global_<variant>.xml`
- **FC LAD del pacchetto**: `FC_<AreaOImpianto>_<Funzione>_lad_<variant>.xml`

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
- **Workflow Excel (strict DB)**: la logica transizioni GRAPH puo' referenziare operandi completi, ma la dichiarazione member DB deve seguire il catalogo `operands` del file Excel (e categorie derivate), evitando inferenze non dichiarate.

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
- **Output fisiche**:
  - riconoscere sia notazione `Axx(.x)` sia `Qxx(.x)` per mapping uscite.

## Datasets e campioni

### Obiettivo
Tenere separati:
- campioni di riferimento (import riuscito, golden sample)
- corpus di reverse engineering (es. `Type_*.xml`)
- output generati dal tool (che vanno in `data/output/`, non qui)

### Struttura consigliata
- `data/datasets/corpus/`
  - `type_xml/` (es. `Type_*.xml` come corpus GRAPH)
  - `tia_exports/` (export grezzi TIA per reverse engineering)
- `data/datasets/typicals/`
  - `graph_fb/` (tipici FB GRAPH per reverse engineering/confronto)
  - `globaldb/` (tipici GlobalDB)
  - `fc_lad/` (tipici FC LAD)
- `data/datasets/golden/`
  - `graph_fb/` (FB GRAPH importati con successo)
  - `globaldb/` (GlobalDB del pacchetto importati con successo, commenti verificati)
  - `fc_lad/` (FC LAD importati con successo)

### Regola d'oro
Se un file serve da riferimento stabile per debug/validator, deve stare in `data/datasets/golden/`.


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

Esempi coerenti coi tipici:
- `T1-A ARUNC -> Transitions -> Safe`
- `T1-A ARUNC HMI -> Conditions -> SC -> Conditions -> n1`
- `T1-A ARUNC -> Memory -> Piece Transfered`

## Regole di corpus e target
- I tipici `V6` o di runtime legacy vanno marcati come **semantic_only** o equivalente nella conoscenza del progetto.
- I golden sample di target devono essere coerenti con `TIA Portal V20 / GRAPH V2`.
- Un file puo' essere ottimo per reverse engineering semantico ma inadatto come pattern di serializer finale.
