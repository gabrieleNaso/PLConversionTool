# Datasets

Questa cartella contiene i campioni usati per studio, confronto e regressione.
Regole e naming: `../../docs/guide/standards/conventions.md`.

## Struttura

Nota: i casi riproducibili (input + expected) stanno in `examples/`, non in `datasets/`.

### `corpus/`
File grezzi usati per studio, classificazione o reverse engineering.
- separare per origine o tipologia
- non usare per output generati
- promuovere in `golden/` solo i campioni verificati con import riuscito
Esempi:
- `corpus/traduzione_awl/` (sorgenti AWL / note di traduzione)
- `corpus/traduzione_xml/` (XML di traduzione di riferimento)

### `typicals/`
Tipici usati per reverse engineering e confronto (non necessariamente golden).
Sottocartelle consigliate:
- `graph_fb/`
- `globaldb/`
- `fc_lad/`

Regole:
- se un file e' un import riuscito e diventa riferimento stabile -> spostarlo in `golden/`
- se e' un output prodotto dal tool -> deve stare in `work/output/`

### `golden/`
Riferimenti stabili usati per validare generatori e regression test.
Sottocartelle consigliate:
- `graph_fb/`
- `globaldb/`
- `fc_lad/`
