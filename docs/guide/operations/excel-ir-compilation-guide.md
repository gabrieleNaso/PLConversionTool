# Guida Excel IR (Formato Singola Pagina)

Obiettivo: compilare un Excel leggibile per generare `IR JSON` e XML TIA (`FB/DB/FC`) senza passare da AWL.

Template consigliato:
- `docs/templates/ir_excel_template_single_page_with_support_fc.xlsx` (pagina FC completa: `support_fc` obbligatoria)

Output:
1. `<Sequence>_ir.json`
2. `<Sequence>_analysis.json`
3. bundle XML TIA in `data/output/generated/<sequence_name>/` (`FB + DB + FC`)

Compatibilita':
- il parser legge anche il formato legacy (`steps`, `transitions`, `timers`, `memories`, `faults`, `outputs`), ma per nuovi file usare il formato singola pagina.
- il foglio per override FC puo' chiamarsi `support_fc` (consigliato) o `fc_support` (alias compatibile).

## 1) Struttura workbook
- `meta`: metadati generali.
- `sequence`: topologia step/transizioni.
- `operands`: catalogo operandi e categoria funzionale.
- `support_fc`: override espliciti dei member nelle FC/DB di supporto.
- `support_fc_logic` (opzionale): logica LAD interna delle FC di supporto.

Regola base:
- nei fogli supporto usa la colonna `network` (semplice); `network_index` resta solo alias legacy.
- per il flusso Excel, `operands` e `support_fc` sono obbligatori e devono contenere almeno una riga valida.

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

## 6) Compilazione FC (Unico Blocco)
Tutto cio' che riguarda le FC e' concentrato in due fogli:
1. `support_fc` (obbligatorio): definisce i segnali da usare in DB/FC di supporto.
2. `support_fc_logic` (opzionale): definisce la logica LAD interna delle FC.

Categorie FC supportate:
- `io`
- `output`
- `diag`
- `hmi`
- `aux`
- `transitions`
- `mode`

### 6.1 Foglio `support_fc` (obbligatorio)
Colonne minime:
- `category`
- `member_name`
- `comment`

Regole pratiche:
- una riga = un segnale della categoria.
- se compili una categoria qui, il generatore usa questi member invece dell'inferenza automatica.
- `operands` resta comunque obbligatorio e continua a governare il catalogo strict DB.

Formato riga consigliato:
`category | member_name | comment`

Esempi:
- `io | I_START_BTN | Pulsante start`
- `io | I_STOP_BTN | Pulsante stop`
- `output | Q_MOTOR_CMD | Comando motore`
- `aux | M_CYCLE_ACTIVE | Memoria ciclo`

### 6.2 Foglio `support_fc_logic` (opzionale)
Colonne:
- `category`
- `result_member`
- `condition_expression`
- `condition_operands`
- `comment`
- `network`

Regole pratiche:
- una riga = una network LAD della FC della categoria.
- `network` e' il numero rete (1, 2, 3, ...): usa questo campo per ordinare e separare le reti.
- se compili `support_fc_logic` per una categoria, la FC di quella categoria usa la logica scritta qui.
- i segnali in `result_member` e `condition_operands` vengono aggiunti automaticamente ai member DB supporto se mancanti.
- se `condition_expression` e' vuota ma `condition_operands` e' compilata, il generatore crea una `AND`.
- se entrambe sono vuote, la rete risulta `TRUE`.

Formato riga consigliato:
`category | result_member | condition_expression | condition_operands | comment | network`

Esempi:
- `io | RUN_ENABLE | I_START_BTN AND NOT I_STOP_BTN | I_START_BTN;I_STOP_BTN | Rete start/stop | 1`
- `output | Q_MOTOR_CMD | RUN_ENABLE AND SAFETY_OK | RUN_ENABLE;SAFETY_OK | Comando motore | 1`
- `aux | AUX_READY | AUX_IN_1 OR AUX_IN_2 | AUX_IN_1;AUX_IN_2 | Logica ausiliaria | 2`

Checklist compilazione manuale FC:
1. Compila sempre `support_fc` (almeno una riga valida).
2. Inserisci solo categorie reali (`io/output/diag/hmi/aux/transitions/mode`).
3. Se vuoi logica custom, compila `support_fc_logic` con `network` numerato.
4. Mantieni nomi coerenti tra `member_name`, `result_member` e `condition_operands`.

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
make generate-excel-ir EXCEL_FILE="docs/templates/ir_excel_template_single_page_with_support_fc.xlsx"
```

## 10) Import in TIA
```bash
make import-generated \
  PROJECT_PATH="C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20" \
  TARGET_PATH="Program blocks/generati da tool/<nome_bundle>" \
  IMPORT_BUNDLE="<nome_bundle>"
```
