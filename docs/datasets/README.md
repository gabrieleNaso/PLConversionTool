## Datasets e campioni (come organizzare i file)

### Obiettivo
Tenere separati:
- **campioni di riferimento** (import riuscito, “golden sample”)
- **corpus di reverse engineering** (es. `Type_*.xml`)
- **output generati dal tool** (che vanno in `output/`, non qui)

### Struttura consigliata (da creare/popolarne i contenuti)
- `datasets/corpus/`
  - `type_xml/` (es. `Type_*.xml` come corpus GRAPH)
  - `tia_exports/` (export grezzi TIA per reverse engineering)
- `datasets/typicals/`
  - `graph_fb/` (tipici FB GRAPH per reverse engineering/confronto)
  - `globaldb/` (tipici GlobalDB)
  - `fc_lad/` (tipici FC LAD)
- `datasets/golden/`
  - `graph_fb/` (FB GRAPH importati con successo)
  - `globaldb/` (GlobalDB companion importati con successo, commenti verificati)
  - `fc_lad/` (FC LAD importati con successo)

### Regola d’oro
Se un file serve da riferimento stabile per debug/validator, deve stare in `datasets/golden/`.

