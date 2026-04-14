# PLConversionTool

Repository per la conversione di sequenziatori PLC `AWL` in un pacchetto XML importabile in `TIA Portal V20`, con trio baseline `FB GRAPH` + `GlobalDB` + `FC LAD` ed eventuali blocchi aggiuntivi `DB/FC` derivati dall'IR.

Regola architetturale fondamentale:

- `FB GRAPH`, `GlobalDB` e `FC LAD` non vanno trattati come XML indipendenti, ma come un unico pacchetto coerente.
- Ogni riferimento simbolico emesso da un blocco deve essere soddisfatto dagli altri blocchi del pacchetto.
- Naming, tag di transizione, member DB, logiche LAD e topologia GRAPH devono restare allineati tra loro per tutta la pipeline `analyze -> export -> import -> compile`.
- Se il caso reale richiede piu' di tre blocchi, la stessa regola si estende a tutti i blocchi aggiuntivi del pacchetto.

Baseline documentale corrente:

- [report_del_14-04-2026.md](/home/administrator/PLConversionTool/report_del_14-04-2026.md): stato consolidato del progetto, scelte architetturali e priorita' operative.
- [Specifica_master_traduzione_AWL_e_generazione_XML_TIA_V20_V2_14_04.md](/home/administrator/PLConversionTool/Specifica_master_traduzione_AWL_e_generazione_XML_TIA_V20_V2_14_04.md): specifica master consolidata AWL -> IR -> GRAPH / GlobalDB / FC LAD.

Direzione di lavoro attuale:

1. mantenere come obiettivo centrale la conversione `AWL -> GRAPH`;
2. implementare come fondazione tecnica validator e generatori XML per `SW.Blocks.FB`, `SW.Blocks.GlobalDB` e `SW.Blocks.FC`;
3. usare `tia_bridge/` e `tia_windows_agent/` per import, compile ed export di regressione.

API backend operative del primo slice:

- `POST /api/conversion/bootstrap`: scaffold e piano iniziale.
- `POST /api/conversion/analyze`: parsing AWL incrementale, IR, issue locali e preview del pacchetto XML completo.
- `POST /api/conversion/export`: scrittura del bundle di analisi e delle preview XML del pacchetto completo in `output/`.

Aggiornamenti operativi consolidati:

- il `tia-bridge` accoda automaticamente un job `compile` subito dopo ogni job `import` (`POST /api/jobs/import`), riusando `targetPath/targetName` dell'import per limitare la compile al target appena toccato;
- il generatore mantiene coerenza tra tag usati nel `GRAPH/FC` e member dichiarati nel `GlobalDB`, incluse transizioni sintetiche (es. `T_HOLD_*`, `T_CHAIN_*`);
- la coerenza del pacchetto e' un requisito hard: non e' ammesso considerare `FB`, `DB`, `FC` o blocchi aggiuntivi come artefatti isolati se poi in compile si referenziano fra loro;
- la diagnostica compile lato Windows agent include dettaglio esteso dei messaggi e del contesto per accelerare il debug sui blocchi TIA.

Documentazione utile:

- [docs/INDEX.md](/home/administrator/PLConversionTool/docs/INDEX.md)
- [docs/project-structure.md](/home/administrator/PLConversionTool/docs/project-structure.md)
- [docs/workflow/import-checklists.md](/home/administrator/PLConversionTool/docs/workflow/import-checklists.md)
