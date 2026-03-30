## Tipici XML (TIA exports “di riferimento”)

Questa cartella contiene i **tipici** usati per reverse engineering e confronto (non necessariamente “golden”).

### Struttura
- `graph_fb/`: tipici `SW.Blocks.FB` GRAPH
- `globaldb/`: tipici `SW.Blocks.GlobalDB`
- `fc_lad/`: tipici `SW.Blocks.FC` LAD

### Regola pratica
- Se un file è **import riuscito** e diventa riferimento stabile → spostarlo in `../golden/`.
- Se è un output prodotto dal tool → deve stare in `../../output/`.

