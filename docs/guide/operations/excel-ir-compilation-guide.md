# Guida Excel IR (Formato Singola Pagina)

Obiettivo: compilare un Excel leggibile per generare `IR JSON` e XML TIA (`FB/DB/FC`) senza passare da AWL.

Aggiornato al `23-04-2026`:
- timer e contatori in `support_fc` vengono generati come blocchi LAD completi (non come contatti semplici);
- il preset usa sempre `operands.control_value` (`PT` per timer, `PV` per contatori).
- nelle transition GRAPH viene mantenuta la logica booleana reale dell'Excel (non fallback su marker `T1/T2`);
- nelle transition GRAPH ogni variabile e' risolta sul DB owner corretto dal catalogo `operands` (cross-DB);
- i blocchi supporto vengono creati sempre anche se vuoti (placeholder `NoData`), incluso `DB14 ... transitions`.
- separazione commenti FC/DB: i commenti delle reti FC non vengono copiati nei tag DB.
- commenti DB non autocompilati: se non presenti in Excel (o in `operands.note`), restano vuoti.
- righe `support_fc` con stesso `network` e stessa `category` vengono aggregate nella stessa rete FC (con un solo power rail LAD).

Template consigliato:
- `docs/templates/ir_excel_template_single_page_with_support_fc.xlsx` (pagina FC completa: `support_fc` obbligatoria)

Regola di allineamento:
- ogni modifica alla struttura dei fogli Excel (colonne, nomi, vincoli) deve aggiornare nello stesso commit anche il template d'esempio in `docs/templates/`.

Output:
1. `<Sequence>_ir.json`
2. `<Sequence>_analysis.json`
3. bundle XML TIA in `data/output/generated/<sequence_name>/` (`FB + DB + FC`)

Compatibilita':
- il parser supporta solo il formato corrente a pagina singola (`sequence`, `operands`, `support_fc`).
- fogli legacy (`steps`, `transitions`, `timers`, `memories`, `faults`, `outputs`) e alias (`fc_support`, `support_fc_logic`, ...) non sono piu' accettati.

## 1) Struttura workbook
- `sequence`: topologia step/transizioni.
- `operands`: catalogo operandi e categoria funzionale.
- `support_fc`: pagina unica FC (member + logica LAD).

Regola base:
- nei fogli supporto usa la colonna `network` (semplice).
- per il flusso Excel, `operands` e `support_fc` sono obbligatori e devono contenere almeno una riga valida.

## 2) Foglio `sequence`
Ogni riga puo' descrivere uno step, una transizione, o entrambi.

Colonne:
- `step_name`: nome passo libero (es. `Init`, `Carico`, `Fine_Ciclo`).
- `numero_step`: numero passo (intero positivo).
- `transition_id`: id transizione (opzionale, auto `T1`, `T2`, ... se vuoto).
- `from_step`: passo sorgente transizione.
- `to_step`: passo destinazione transizione.
- `condition_expression`: espressione LAD/booleana (default `TRUE`).
- `flow_type`: `alternative` oppure `parallel`.
- `parallel_group`: gruppo parallelo (obbligatorio quando `flow_type=parallel`).

Regole importanti:
- i nomi passo sono liberi: il generatore non impone nomi fissi.
- l'inizio sequenza e' determinato da `numero_step = 1`.
- `from_step`/`to_step` possono usare alias tipo `S1`, `S2`: se in `steps` esiste un passo con `numero_step` corrispondente, l'alias viene risolto al nome reale.

## 3) Foglio `operands`
Questo foglio e' il catalogo ufficiale dei segnali usati dal caso Excel.

Colonne:
- `operand`: nome operando (es. `M10.0`, `Q4.0`, `ALM_OVERTEMP`, `DB81.DBX0.0`).
- `category`: categoria funzionale.
- `datatype`: tipo variabile PLC (es. `Bool`, `Int`, `DInt`, `Real`, `Time`, `String`).
- `control_kind`: tipo blocco controllo, opzionale:
  - timer: `t_on`, `t_off`, `t_p`
  - counter: `ctu`, `ctd`, `ctud`
- `control_value`: valore blocco controllo, opzionale:
  - timer: tempo in formato semplice (`5s`, `20ms`, `1m`, `2h`)
  - counter: setpoint intero (`10`, `25`, ...)
- `note`: testo libero.

Uso di `note` e `comment`:
- `operands.note` viene propagata nei commenti dei member DB quando il segnale viene dichiarato nel DB owner.
- `support_fc.comment` viene usata solo come commento della rete FC.
- i commenti FC (`support_fc.comment`) non vengono propagati nei commenti dei member DB.
- in modalita' strict Excel, i commenti DB derivano solo da commenti espliciti `support_fc.member_name`/`support_members` e da `operands.note`.
- se commenti e note non sono valorizzati, il commento DB resta vuoto (nessun testo automatico).

Nota timer:
- `trigger_operands` non e' piu' usato nel foglio `operands`; i trigger/consensi si modellano nella logica FC (`support_fc`).

Categorie supportate:
- `alarm` -> `faults`
- `aux` -> `memories` (aux)
- `hmi` -> `memories` (hmi) + ref esterni
- `output` -> `outputs`
- `memory` -> `memories` (mappata come `aux`)
- `external` -> `external_refs`
- `lv2`/`lev2` -> owner DB LEV2
- `transition`/`transitions` -> owner DB TRANSITIONS

Nota importante:
- `timer`, `counter`, `manual_mode`, `auto_mode` non sono categorie valide nel foglio `operands`.
- `mode` non e' una categoria valida in input Excel: usa `lv2` (o `lev2`).
- timer/contatori si definiscono tramite `datatype` (`IEC_TIMER`/`IEC_COUNTER`) + `control_kind` + `control_value`.

## 4) Regola Strict DB (Excel)
Per input Excel, il generatore usa `operands` come catalogo strict:
- la logica LAD delle transizioni GRAPH resta completa (non viene semplificata);
- i member DB vengono dichiarati solo se coerenti col catalogo `operands` e con le categorie derivate;
- il tipo del member DB segue `operands.datatype` quando presente (default `Bool`);
- per i timer, `control_value` viene normalizzato automaticamente in formato TIA (`T#...`);
- variabili non catalogate non vengono aggiunte "a caso" nei DB.

Se una transizione usa operandi non presenti nel catalogo, il report analysis segnala warning dedicati.

## 5) Compilazione FC (Pagina Unica)
Tutto cio' che riguarda le FC e' in un solo foglio: `support_fc` (obbligatorio).

Categorie FC supportate:
- `io`
- `output`
- `diag`
- `hmi`
- `aux`
- `transitions`
- `lv2`

Colonne:
- `category`
- `member_name`
- `result_member`
- `condition_expression`
- `coil_mode` (opzionale: `set` / `reset`; vuoto = bobina normale)
- `comment`
- `network`

Regole pratiche:
- una riga puo' essere:
  - riga member (compili `member_name`);
  - riga logica (compili `result_member` + condizione);
  - riga mista (member + logica insieme).
- se compili una categoria qui, il generatore usa questi dati invece dell'inferenza automatica.
- `operands` resta comunque obbligatorio e continua a governare il catalogo strict DB.
- `network` e' il numero rete (1, 2, 3, ...): usa questo campo per ordinare e separare le reti.
- piu' righe logiche con stessa `category` + stesso `network` vengono aggregate in un'unica network LAD.
- se vuoi reti distinte, usa numeri `network` diversi.
- se compili `result_member`/condizione, la FC della categoria usa la logica scritta qui.
- `coil_mode` e' per-riga: `set` genera `SCoil`, `reset` genera `RCoil`, vuoto genera `Coil` normale.
- i segnali presenti in `operands` vengono collegati ai DB supporto.
- i segnali NON presenti in `operands` restano comunque usabili nella logica FC come variabili globali non agganciate a DB.
- nelle transition GRAPH i simboli sono risolti per owner DB: una condizione puo' leggere variabili da DB diversi nella stessa rete.
- se in una rete FC compare una variabile catalogata come controllo:
  - `datatype=IEC_TIMER` -> blocco completo `TON/TOF/TP` con `PT` da `control_value`;
  - `datatype=IEC_COUNTER` -> blocco completo `CTU/CTD/CTUD` con `PV` da `control_value`.
- nei contatori, i pin necessari non valorizzati in Excel vengono cablati con default sicuri (`FALSE`) per evitare errori di import TIA.
- il generatore valida `control_kind/control_value` in base alla tipologia (`datatype`) e usa fallback sicuri solo quando i campi sono vuoti.
- se vuoi referenziare campi specifici del timer (es. `.Q`, `.ET`) in una logica senza blocco timer automatico, scrivili esplicitamente in `condition_expression`.
- se entrambe sono vuote, la rete risulta `TRUE`.
- nello sheet `sequence`, gli operandi transizione vengono ricavati automaticamente da `condition_expression`.
- nello sheet `support_fc`, gli operandi rete vengono ricavati automaticamente da `condition_expression`.
- `condition_expression` supporta parentesi e precedenza logica (`NOT` > `AND` > `OR`) sia per `support_fc` sia per le transizioni.
- quando mischi `OR` e `AND` nello stesso livello, usa sempre parentesi esplicite per evitare ambiguita' di lettura LAD.
- esempi validi con semantica diversa:
  - `M1 AND (NOT M2 OR M3)`
  - `(M1 AND NOT M2) OR M3`

Formato riga consigliato:
`category | member_name | result_member | condition_expression | coil_mode | comment | network`

Esempi:
- `io | I_START_BTN |  |  |  | Pulsante start |`
- `io | I_STOP_BTN |  |  |  | Pulsante stop |`
- `io |  | RUN_ENABLE | I_START_BTN AND NOT I_STOP_BTN |  | Rete start/stop | 1`
- `aux |  | MOTOR_LATCH | RUN_ENABLE | set | Set marcia | 2`
- `aux |  | MOTOR_LATCH | STOP_BTN OR FAULT | reset | Reset marcia | 3`

Checklist compilazione manuale FC:
1. Compila sempre `support_fc` (almeno una riga valida con `member_name` e/o `result_member`).
2. Inserisci solo categorie reali (`io/output/diag/hmi/aux/transitions/lv2`).
3. Se vuoi logica custom, compila `result_member` + condizione con `network` numerato.
4. Mantieni nomi coerenti tra `member_name`, `result_member` e variabili usate in `condition_expression`.

## 6) Paralleli
Per modellare un parallelo reale:
1. split: stesso `from_step`, target diversi, `flow_type=parallel`.
2. join: source diversi, stesso `to_step`, `flow_type=parallel`.
3. stesso `parallel_group` per tutto il blocco.

Il generatore emette:
- `SimBegin` per split
- `SimEnd` per join

## 7) Esempio minimo
`sequence`:
- `Init | 1 | T1 | Init | Dosaggio | M_START | M_START | alternative |`
- `Dosaggio | 2 | T2 | Dosaggio | Fine | M_DONE | M_DONE | alternative |`

`operands`:
- `M_START | aux | | | | | consenso avvio`
- `M_DONE | aux | | | | | consenso fine`
- `ALM_TEMP | alarm | | | | | allarme temperatura`

## 8) Generazione
```bash
make generate-excel-ir EXCEL_FILE="docs/templates/ir_excel_template_single_page_with_support_fc.xlsx"
```

## 9) Import in TIA
```bash
make import-generated \
  PROJECT_PATH="C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20" \
  TARGET_PATH="Program blocks/generati da tool/<nome_bundle>" \
  IMPORT_BUNDLE="<nome_bundle>"
```

Regole consolidate (23-04-2026):
- `import-generated` esegue polling automatico del job import.
- i numeri blocco sono il valore reale XML `<Number>` (non il prefisso nel nome file).
- il suffisso finale e' il numero comune di gruppo (`GG`): `03` e' un esempio, non un valore obbligatorio.
- mappa gruppi numerici blocchi (forma `XXGG`, esempio con `GG=03`):
  - `11GG` (es. `1103`) -> alarms/diag
  - `12GG` (es. `1203`) -> hmi
  - `13GG` (es. `1303`) -> aux
  - `14GG` (es. `1403`) -> transitions
  - `15GG` (es. `1503`) -> graph (FB)
  - `16GG` (es. `1603`) -> sequenza
  - `18GG` (es. `1803`) -> external
  - `19GG` (es. `1903`) -> output
- nota importante su `15GG`:
  - `FB15GG` e' il blocco GRAPH;
  - `DB15GG SEQ` e' il DB istanza generato automaticamente da TIA per la FB GRAPH, non va emesso dal tool come DB custom.
- profilo blocchi target corretto (con `GG` variabile):
  - FC: `FC11` Alarms, `FC12` HMI, `FC13` Aux, `FC14` Transitions, `FC16` Output, `FC17` LEV2
  - FB: `FB15` Sequence (GRAPH)
  - DB custom: `DB11` base/alarms, `DB12` HMI, `DB13` PARAMETERS, `DB16` I/O, `DB17` LEV2, `DB18` external, `DB19` AUX
  - DB istanza TIA: `DB15` SEQ (auto-creato da TIA, non serializzato dal tool)
- anche quando una famiglia DB/FC non ha member valorizzati dall'Excel, il blocco viene comunque emesso con placeholder per mantenere il pacchetto completo.
- le variabili usate nelle FC possono essere cross-categoria, ma il DB owner non cambia:
  - il DB owner e' determinato dal catalogo `operands`;
  - se una variabile e' usata in un'altra FC, resta referenziata nel DB owner originale;
  - eccezione di robustezza per `FC transitions`: se una variabile non ha owner risolto, fallback sul DB transitions per evitare import error.
- per ogni network LAD FC viene mantenuto un solo `Powerrail`; in caso di merge righe su stesso `network`, i rami vengono accorpati sulla stessa alimentazione.
