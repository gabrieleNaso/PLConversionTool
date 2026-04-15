# Guida Completa: Compilare l'Excel IR Manuale

Questa guida spiega esattamente come compilare ogni colonna del file Excel per ottenere:
1. IR JSON (`<Sequence>_ir.json`)
2. XML TIA (`FB/DB/FC`)

Template disponibili:
- `data/input/templates/ir_excel_template.xlsx`
- `data/input/templates/ir_excel_template_no_network.xlsx` (senza foglio `networks`)

## 1) Regole di Compilazione
- Non cambiare nome fogli e header.
- Usa `;` per liste multiple (accettati anche `,` e `|`).
- Celle vuote = informazione non fornita.
- Nomi step consigliati: `S1`, `S2`, `S3`, ...

## 2) Mappa Fogli -> Scopo
- `meta`: metadati globali del bundle.
- `networks` (opzionale): tracciabilita' e contesto logico delle reti.
- `steps`: stati della sequenza.
- `transitions`: passaggi tra step (foglio piu' importante).
- `timers`: timer da riportare nel modello.
- `memories`: memorie ausiliarie.
- `faults`: segnali/fatti diagnostici.
- `outputs`: uscite fisiche.

## 3) Dizionario Colonne (Dettaglio Completo)

### 3.1 Foglio `meta`
Colonne fisse: `key`, `value`

Righe chiave supportate:
- `sequence_name`
  - Obbligatoria: consigliata fortemente.
  - Formato: testo libero (verra' normalizzato).
  - Effetto: nome base di cartella e file XML.
  - Esempio: `Linea_Imbottigliamento_01`
- `source_name`
  - Obbligatoria: no.
  - Effetto: etichetta sorgente in `analysis`.
  - Esempio: `linea_imbottigliamento.xlsx`
- `manual_logic_networks`
  - Obbligatoria: no.
  - Formato: lista indici rete (`2;5`).
  - Effetto: flag/manual hints nel report.
- `auto_logic_networks`
  - Obbligatoria: no.
  - Formato: lista indici rete (`1;3;4`).
  - Effetto: flag/auto hints nel report.
- `external_refs`
  - Obbligatoria: no.
  - Formato: lista operandi esterni (`I0.0;DB100.DBX0.0`).
  - Effetto: arricchisce diagnostica e support artifacts.
- `assumptions`
  - Obbligatoria: no.
  - Formato: note separate da `;`.
  - Effetto: riportato in IR/analysis.

### 3.2 Foglio `networks` (opzionale)
Se usi il template `*_no_network.xlsx`, questo foglio non c'e' ed e' corretto.

Colonne:
- `network_index`
  - Obbligatoria: no (ma consigliata se il foglio esiste).
  - Formato: intero (`1`, `2`, `3`...).
  - Effetto: collega steps/transitions/timers a una rete.
- `network_title`
  - Obbligatoria: no.
  - Formato: testo breve.
  - Effetto: leggibilita'/naming support XML.
- `network_lines_for_traceability`
  - Obbligatoria: no.
  - Formato: testo con righe separate da `|`.
  - Effetto: solo tracciabilita' (non parsing AWL completo).

Fallback se manca `networks`:
- il tool crea reti sintetiche dagli indici trovati nelle transizioni.

### 3.3 Foglio `steps`
Colonne:
- `step_name`
  - Obbligatoria: si.
  - Formato: stringa step (`S1`, `S2`, ...).
  - Effetto: crea nodi step GRAPH.
- `networks_where_step_is_read`
  - Obbligatoria: no.
  - Formato: lista interi (`1;2`).
  - Effetto: metadato IR (source_networks).
- `networks_where_step_is_activated`
  - Obbligatoria: no.
  - Formato: lista interi.
  - Effetto: metadato IR (activation_networks).
- `networks_with_step_actions`
  - Obbligatoria: no.
  - Formato: lista interi.
  - Effetto: metadato IR (action_networks).

### 3.4 Foglio `transitions` (fondamentale)

Questa tabella va letta cosi':
- una riga = **una freccia** del GRAPH
- `from_step` = da dove parte la freccia
- `to_step` = dove arriva la freccia
- `condition_expression` = quando la freccia e' vera/scatta

Se capisci questo, il resto e' solo dettaglio tecnico.

Colonne (versione chiara):
- `transition_id`
  - Cosa rappresenta: nome tecnico della freccia.
  - Obbligatoria: no.
  - Se vuota: il tool genera `T1`, `T2`, ...
  - Esempio: `T_FILL_READY`
- `from_step`
  - Cosa rappresenta: step attivo di partenza.
  - Obbligatoria: si (sempre).
  - Esempio: `S10`
- `to_step`
  - Cosa rappresenta: step in cui vuoi andare.
  - Obbligatoria: si (sempre).
  - Esempio: `S20`
- `condition_expression`
  - Cosa rappresenta: logica booleana della transizione.
  - Obbligatoria: no (default `TRUE`).
  - Esempi:
    - `TRUE` (passaggio sempre consentito)
    - `M10.0 AND T1`
    - `I0.1 AND NOT M20.0`
    - `DB100.DBX0.0 OR M30.1`
- `operands_used_in_condition`
  - Cosa rappresenta: elenco token usati nella condizione.
  - Obbligatoria: no ma consigliata.
  - Formato: lista separata da `;`
  - Esempio: `M10.0;T1`
- `condition_network_index`
  - Cosa rappresenta: riferimento rete di provenienza della logica (solo tracciabilita').
  - Obbligatoria: no.
  - Esempio: `3`
- `jump_labels_used`
  - Cosa rappresenta: etichette AWL legacy correlate, se le hai.
  - Obbligatoria: no.
  - Esempio: `NEXT`

Ordine mentale consigliato per compilare una riga:
1. Decidi `from_step`.
2. Decidi `to_step`.
3. Scrivi `condition_expression`.
4. Copia gli operandi in `operands_used_in_condition`.
5. Compila gli altri campi solo se ti servono.

Pattern pronti da copiare:
- Passaggio diretto:
  - `from_step=S1`, `to_step=S2`, `condition_expression=TRUE`
- Passaggio con consenso + timer:
  - `from_step=S2`, `to_step=S3`, `condition_expression=M10.0 AND T1`, `operands_used_in_condition=M10.0;T1`
- Bivio (due uscite dallo stesso step):
  - Riga 1: `from_step=S3`, `to_step=S4`, `condition_expression=I0.0`
  - Riga 2: `from_step=S3`, `to_step=S5`, `condition_expression=NOT I0.0`

Errori comuni sulle transizioni:
- `from_step`/`to_step` non presenti nel foglio `steps`
  - Effetto: topologia incoerente o warning.
- condizione scritta ma operandi non allineati
  - Effetto: naming guard meno leggibile nel DB.
- due righe duplicate identiche
  - Effetto: duplicazioni inutili in IR/XML.

### 3.5 Foglio `timers`
Colonne:
- `timer_name`
  - Obbligatoria: no.
  - Formato: `T1`, `T209`, ...
  - Effetto: crea member timer nel DB.
- `defined_in_network_index`
  - Obbligatoria: no.
  - Formato: intero.
- `timer_instruction_kind`
  - Obbligatoria: no (default `SD`).
  - Formato: `SD|SE|SP|SS|SF`.
- `timer_preset_value`
  - Obbligatoria: no.
  - Formato: es. `S5T#5S`.
- `timer_trigger_operands`
  - Obbligatoria: no.
  - Formato: lista operandi.

### 3.6 Foglio `memories`
Colonne:
- `memory_operand`
  - Obbligatoria: no.
  - Formato: es. `M10.0`.
  - Effetto: member memoria nel DB support.
- `memory_role`
  - Obbligatoria: no (default `aux`).
  - Formato: testo (`aux`, ...).
- `found_in_network_index`
  - Obbligatoria: no.
  - Formato: intero.

### 3.7 Foglio `faults`
Colonne:
- `fault_tag`
  - Obbligatoria: no.
  - Formato: es. `ALARM_OVERTEMP`.
  - Effetto: diagnostica + support artifacts.
- `found_in_network_index`
  - Obbligatoria: no.
- `fault_evidence`
  - Obbligatoria: no.
  - Formato: testo libero.

### 3.8 Foglio `outputs`
Colonne:
- `output_operand`
  - Obbligatoria: no ma consigliata.
  - Formato: `Q4.0` o `A4.0`.
  - Effetto: output family XML e temp LAD.
- `found_in_network_index`
  - Obbligatoria: no.
- `write_action`
  - Obbligatoria: no (default `=`).
  - Formato: `=`, `S`, `R` (se usi semantica coerente).

## 4) Procedura Pratica (consigliata)
Compila in questo ordine:
1. `steps` (definisci tutti gli stati)
2. `transitions` (disegna tutte le frecce)
3. `outputs` (uscite fisiche)
4. opzionali: `timers`, `memories`, `faults`, `meta`

Regola d'oro:
- se la sequenza "non gira", il 90% delle volte il problema e' nelle `transitions`.

## 5) Minimo Sindacale per Generare
Per un caso minimo funzionante:
1. `meta`: almeno `sequence_name`
2. `steps`: almeno 2 righe (`S1`, `S2`)
3. `transitions`: almeno 1 riga (`from_step=S1`, `to_step=S2`)

Tutto il resto puo' restare vuoto.

## 6) Esempio Minimo (righe)
- `meta`: `sequence_name = Demo_Line`
- `steps`: `S1` e `S2`
- `transitions`: `T1 | S1 | S2 | 1 | TRUE | |`

## 7) Esempio Completo Transizioni (sequenza 3 step)
Supponiamo di avere `S10 -> S20 -> S30`:

- Riga 1:
  - `transition_id = T_START`
  - `from_step = S10`
  - `to_step = S20`
  - `condition_expression = I0.0`
  - `operands_used_in_condition = I0.0`
- Riga 2:
  - `transition_id = T_DONE`
  - `from_step = S20`
  - `to_step = S30`
  - `condition_expression = M100.0 AND T1`
  - `operands_used_in_condition = M100.0;T1`

## 8) Errori Tipici e Fix
- Transizione ignorata:
  - Causa: `from_step` o `to_step` vuoti.
  - Fix: compila entrambi.
- Step non collegato:
  - Causa: step in `steps` ma mai usato in `transitions`.
  - Fix: aggiungi una transizione entrante/uscente.
- Nomi output strani:
  - Causa: `output_operand` non canonico.
  - Fix: usa `Qx.y` o `Ax.y`.

## 9) Generazione da Excel
```bash
make generate-excel-ir EXCEL_FILE="data/input/templates/ir_excel_template.xlsx"
```

Senza foglio `networks`:
```bash
make generate-excel-ir EXCEL_FILE="data/input/templates/ir_excel_template_no_network.xlsx"
```

Output:
- `data/output/generated/<sequence_name_lower>/`
- `<Sequence>_ir.json`
- `<Sequence>_analysis.json`
- XML baseline + support

## 10) Import in TIA
```bash
make import-generated \
  PROJECT_PATH="C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20" \
  TARGET_PATH="Program blocks/generati da tool/<nome_bundle>" \
  IMPORT_BUNDLE="<nome_bundle>"
```

## 11) Checklist Finale
- Ogni `from_step`/`to_step` esiste in `steps`.
- `sequence_name` valorizzato.
- Generazione OK senza errori.
- `TARGET_PATH` parte con `Program blocks/`.
