# Convenzioni e dataset

Questo documento unifica:
- `docs/conventions/naming.md`
- `docs/datasets/README.md`

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
Organizzare per macro-strutture funzionali, evitando DB piatti:
- `Cmd` (comandi)
- `Fb` (feedback)
- `Par` (parametri/ricetta)
- `En` (enable/consensi)
- `Diag` (diagnostica)
- `Hmi` (dati HMI)
- `Map` (mapping AWL->GRAPH / supporto tool)

## Regole pratiche
- **Stabilita'**: il naming deve essere deterministico (stesso input -> stessi simboli).
- **Allineamento**: simboli referenziati nel `FlgNet` devono esistere e avere naming identico tra FB/DB.
- **Evitare ambiguita'**: niente acronimi non condivisi; preferire naming impiantistico.

## Datasets e campioni

### Obiettivo
Tenere separati:
- campioni di riferimento (import riuscito, golden sample)
- corpus di reverse engineering (es. `Type_*.xml`)
- output generati dal tool (che vanno in `output/`, non qui)

### Struttura consigliata
- `datasets/corpus/`
  - `type_xml/` (es. `Type_*.xml` come corpus GRAPH)
  - `tia_exports/` (export grezzi TIA per reverse engineering)
- `datasets/typicals/`
  - `graph_fb/` (tipici FB GRAPH per reverse engineering/confronto)
  - `globaldb/` (tipici GlobalDB)
  - `fc_lad/` (tipici FC LAD)
- `datasets/golden/`
  - `graph_fb/` (FB GRAPH importati con successo)
  - `globaldb/` (GlobalDB del pacchetto importati con successo, commenti verificati)
  - `fc_lad/` (FC LAD importati con successo)

### Regola d'oro
Se un file serve da riferimento stabile per debug/validator, deve stare in `datasets/golden/`.
