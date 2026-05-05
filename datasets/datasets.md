# Datasets

Questa cartella contiene i campioni usati per studio, confronto e regressione.
Regole e naming: `../../docs/guide/standards/conventions.md`.

## Struttura

Nota: i casi riproducibili (input + expected_output) stanno in `cases/`, non in `datasets/`.

### `typicals/`
Tipici usati per reverse engineering e confronto (non necessariamente golden).
Sottocartelle consigliate:
- `graph_fb/`
- `globaldb/`
- `fc_lad/`

Regole:
- se e' un output prodotto dal tool -> deve stare in `work/output/`
