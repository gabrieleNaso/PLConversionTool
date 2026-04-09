# PLConversionTool

Repository per la conversione di sequenziatori PLC `AWL` in artefatti `GRAPH` XML importabili in `TIA Portal V20`, con `GlobalDB` companion e `FC LAD` di supporto quando necessari.

Baseline documentale corrente:

- [report_del_09-04-2026 (1).md](/home/administrator/PLConversionTool/report_del_09-04-2026%20(1).md): stato consolidato del progetto, scelte architetturali e priorita' operative.
- [Specifica_master_traduzione_e_generazione_XML_TIA_V20_V2.md](/home/administrator/PLConversionTool/Specifica_master_traduzione_e_generazione_XML_TIA_V20_V2.md): specifica consolidata AWL -> IR -> GRAPH / GlobalDB / FC LAD.

Direzione di lavoro attuale:

1. mantenere come obiettivo centrale la conversione `AWL -> GRAPH`;
2. implementare come fondazione tecnica validator e generatori XML per `SW.Blocks.FB`, `SW.Blocks.GlobalDB` e `SW.Blocks.FC`;
3. usare `tia_bridge/` e `tia_windows_agent/` per import, compile ed export di regressione.

API backend operative del primo slice:

- `POST /api/conversion/bootstrap`: scaffold e piano iniziale.
- `POST /api/conversion/analyze`: parsing AWL incrementale, IR, issue locali e preview artefatti.
- `POST /api/conversion/export`: scrittura del bundle di analisi e delle preview XML in `output/`.

Documentazione utile:

- [docs/INDEX.md](/home/administrator/PLConversionTool/docs/INDEX.md)
- [docs/project-structure.md](/home/administrator/PLConversionTool/docs/project-structure.md)
- [docs/workflow/import-checklists.md](/home/administrator/PLConversionTool/docs/workflow/import-checklists.md)
