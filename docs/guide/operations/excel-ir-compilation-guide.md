# Guida Excel IR (Nuovo Formato Semplice)

Obiettivo: compilare un Excel **chiaro e leggibile** con:
- una pagina unica per sequenza (`step + transition + operandi LAD`)
- una pagina per classificare gli operandi (`allarmi`, `aux`, `hmi`, ecc.)

Output generato:
1. `<Sequence>_ir.json`
2. XML TIA (`FB/DB/FC`)

Template consigliato:
- `docs/templates/ir_excel_template_single_page.xlsx`

Compatibilita':
- il parser legge anche il formato legacy (`steps`, `transitions`, `timers`, `memories`, `faults`, `outputs`).

## 1) Fogli del Nuovo Formato
- `meta`: metadati generali.
- `sequence`: pagina principale (step + transition).
- `operands`: classificazione operandi per funzione.

Nota importante:
- non devi compilare nessun `network_index`.
- il generatore assegna automaticamente i network interni partendo dall'ordine delle transizioni e dagli operandi usati.

## 2) Foglio `meta`
Colonne: `key`, `value`

Chiavi principali:
- `sequence_name`: nome sequenza (consigliato).
- `source_name`: etichetta sorgente.
- `assumptions`: note separate da `;`.

## 3) Foglio `sequence` (pagina principale)
Ogni riga puo' essere:
- una riga step (compili `step_name`)
- una riga transition (compili `from_step` + `to_step`)
- oppure entrambe nello stesso record.

Colonne:
- `step_name`: nome step (`S1`, `S2`, ...).
- `numero_step`: numero step (intero positivo).
- `transition_id`: id transizione (`T1`, `T2`, ...), opzionale.
- `from_step`: step sorgente transizione.
- `to_step`: step destinazione transizione.
- `condition_expression`: logica LAD/booleana transizione (default `TRUE`).
- `operands_used_in_condition`: operandi condizione separati da `;`.
- `flow_type`: `alternative` oppure `parallel`.
- `jump_labels_used`: opzionale.

Regole pratiche:
- per una transition sono obbligatori `from_step` e `to_step`.
- `flow_type=parallel` va usato solo per blocchi paralleli reali.
- se `flow_type` e' vuoto: default `alternative`.

## 4) Foglio `operands` (classificazione segnali)
Qui classifichi gli operandi usati nella logica LAD delle transizioni.

Colonne:
- `operand`: nome operando (es. `M10.0`, `Q4.0`, `ALM_OVERTEMP`, `DB81.DBX0.0`).
- `category`: categoria funzionale.
- `write_action`: per output (`=`, `S`, `R`), opzionale.
- `timer_instruction_kind`: per timer (`SD`, `SE`, `SP`, `SS`, `SF`), opzionale.
- `timer_preset_value`: preset timer, opzionale.
- `trigger_operands`: trigger timer separati da `;`, opzionale.
- `note`: testo libero.

Categorie supportate:
- `alarm`: genera voci diagnostiche (`faults`)
- `aux`: genera memoria ausiliaria (`memories`)
- `hmi`: classifica segnale HMI (support HMI)
- `output`: genera uscita (`outputs`)
- `timer`: genera timer (`timers`)
- `memory`: memoria (mappata come `aux`)
- `external`: riferimento esterno
- `manual_mode`: aggiunge rete in `manual_logic_networks`
- `auto_mode`: aggiunge rete in `auto_logic_networks`

Categorie non riconosciute:
- vengono trattate come memoria custom (`memories.role=<categoria>`).

## 5) Paralleli (chiaro per il generatore)
Per avere parallelismo esplicito:
1. Split: transizioni con stesso `from_step`, target diversi, `flow_type=parallel`.
2. Join: transizioni con source diversi, stesso `to_step`, `flow_type=parallel`.

Il generatore:
- crea `SimBegin` per split parallelo
- crea `SimEnd` per join parallelo

Se `flow_type` non e' `parallel`, il ramo resta `alternative`.

## 6) Esempio Minimo
`sequence`:
- `S1 | 1 | T1 | S1 | S2 | TRUE | | alternative`
- `S2 | 2 |    |    |    |      | |`

`operands`:
- `M10.0 | aux | 1 | | | | | consenso`
- `ALM_TEMP | alarm | 3 | | | | | allarme temperatura`

## 7) Comando Generazione
```bash
make generate-excel-ir EXCEL_FILE="docs/templates/ir_excel_template_single_page.xlsx"
```

## 8) Import in TIA
```bash
make import-generated \
  PROJECT_PATH="C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20" \
  TARGET_PATH="Program blocks/generati da tool/<nome_bundle>" \
  IMPORT_BUNDLE="<nome_bundle>"
```
