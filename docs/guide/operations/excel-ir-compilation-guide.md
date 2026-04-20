# Guida Excel IR (Formato Singola Pagina)

Obiettivo: compilare un Excel leggibile per generare `IR JSON` e XML TIA (`FB/DB`) senza passare da AWL.

Template consigliato:
- `docs/templates/ir_excel_template_single_page.xlsx`

Output:
1. `<Sequence>_ir.json`
2. `<Sequence>_analysis.json`
3. bundle XML TIA in `data/output/generated/<sequence_name>/` (`FB + DB + FC`)

Compatibilita':
- il parser legge anche il formato legacy (`steps`, `transitions`, `timers`, `memories`, `faults`, `outputs`), ma per nuovi file usare il formato singola pagina.

## 1) Struttura workbook
- `meta`: metadati generali.
- `sequence`: topologia step/transizioni.
- `operands`: catalogo operandi e categoria funzionale.
- `support_fc` (opzionale): override espliciti dei member nelle FC/DB di supporto.

Regola base:
- non compilare `network_index`: viene assegnato dal generatore.

## 2) Foglio `meta`
Colonne:
- `key`
- `value`

Chiavi utili:
- `sequence_name`: nome sequenza/bundle.
- `source_name`: etichetta sorgente (es. nome file Excel).
- `assumptions`: note separate da `;`.

## 3) Foglio `sequence`
Ogni riga puo' descrivere uno step, una transizione, o entrambi.

Colonne:
- `step_name`: nome passo libero (es. `Init`, `Carico`, `Fine_Ciclo`).
- `numero_step`: numero passo (intero positivo).
- `transition_id`: id transizione (opzionale, auto `T1`, `T2`, ... se vuoto).
- `from_step`: passo sorgente transizione.
- `to_step`: passo destinazione transizione.
- `condition_expression`: espressione LAD/booleana (default `TRUE`).
- `operands_used_in_condition`: operandi separati da `;`.
- `flow_type`: `alternative` oppure `parallel`.
- `parallel_group`: gruppo parallelo (obbligatorio quando `flow_type=parallel`).
- `jump_labels_used`: opzionale.

Regole importanti:
- i nomi passo sono liberi: il generatore non impone nomi fissi.
- l'inizio sequenza e' determinato da `numero_step = 1`.
- `from_step`/`to_step` possono usare alias tipo `S1`, `S2`: se in `steps` esiste un passo con `numero_step` corrispondente, l'alias viene risolto al nome reale.

## 4) Foglio `operands`
Questo foglio e' il catalogo ufficiale dei segnali usati dal caso Excel.

Colonne:
- `operand`: nome operando (es. `M10.0`, `Q4.0`, `ALM_OVERTEMP`, `DB81.DBX0.0`).
- `category`: categoria funzionale.
- `write_action`: per output (`=`, `S`, `R`), opzionale.
- `timer_instruction_kind`: per timer (`SD`, `SE`, `SP`, `SS`, `SF`), opzionale.
- `timer_preset_value`: preset timer, opzionale.
- `trigger_operands`: trigger timer separati da `;`, opzionale.
- `note`: testo libero.

Categorie supportate:
- `alarm` -> `faults`
- `aux` -> `memories` (aux)
- `hmi` -> `memories` (hmi) + ref esterni
- `output` -> `outputs`
- `timer` -> `timers`
- `memory` -> `memories` (mappata come `aux`)
- `external` -> `external_refs`
- `manual_mode` -> `manual_logic_networks`
- `auto_mode` -> `auto_logic_networks`

## 5) Regola Strict DB (Excel)
Per input Excel, il generatore usa `operands` come catalogo strict:
- la logica LAD delle transizioni GRAPH resta completa (non viene semplificata);
- i member DB vengono dichiarati solo se coerenti col catalogo `operands` e con le categorie derivate;
- variabili non catalogate non vengono aggiunte "a caso" nei DB.

Se una transizione usa operandi non presenti nel catalogo, il report analysis segnala warning dedicati.

## 6) Foglio `support_fc` (opzionale, consigliato)
Usa questo foglio quando vuoi controllare direttamente cosa compare nelle FC/DB di supporto (`io`, `output`, `diag`, `hmi`, `aux`, `transitions`, `mode`, `network`) invece di usare l'inferenza automatica.

Colonne:
- `category`: categoria supporto. Valori: `io`, `output`, `diag`, `hmi`, `aux`, `transitions`, `mode`, `network`.
- `member_name`: nome variabile da inserire nel DB supporto e nella FC supporto collegata.
- `comment`: commento opzionale.
- `network_index`: usato solo con `category=network` per decidere in quale DB/FC rete mettere il member.
- `network_title`: opzionale per `category=network`.

Regole:
- se una categoria e' presente in `support_fc`, per quella categoria il generatore usa i member del foglio.
- se una categoria non e' presente, resta l'inferenza automatica standard.
- `support_fc` puo' convivere con `operands`: `operands` continua a governare topologia/strict DB, `support_fc` governa i support artifacts.

## 7) Paralleli
Per modellare un parallelo reale:
1. split: stesso `from_step`, target diversi, `flow_type=parallel`.
2. join: source diversi, stesso `to_step`, `flow_type=parallel`.
3. stesso `parallel_group` per tutto il blocco.

Il generatore emette:
- `SimBegin` per split
- `SimEnd` per join

## 8) Esempio minimo
`sequence`:
- `Init | 1 | T1 | Init | Dosaggio | M_START | M_START | alternative |`
- `Dosaggio | 2 | T2 | Dosaggio | Fine | M_DONE | M_DONE | alternative |`

`operands`:
- `M_START | aux | | | | | consenso avvio`
- `M_DONE | aux | | | | | consenso fine`
- `ALM_TEMP | alarm | | | | | allarme temperatura`

## 9) Generazione
```bash
make generate-excel-ir EXCEL_FILE="docs/templates/ir_excel_template_single_page.xlsx"
```

## 10) Import in TIA
```bash
make import-generated \
  PROJECT_PATH="C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20" \
  TARGET_PATH="Program blocks/generati da tool/<nome_bundle>" \
  IMPORT_BUNDLE="<nome_bundle>"
```
