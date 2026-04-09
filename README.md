# PLConversionTool

Repository per la conversione di sequenziatori PLC `AWL` in artefatti `GRAPH` XML importabili in `TIA Portal V20`, con `GlobalDB` companion e `FC LAD` di supporto quando necessari.

Baseline documentale corrente:

- [report_del_09-04-2026.md](/home/administrator/PLConversionTool/report_del_09-04-2026.md): stato consolidato del progetto, scelte architetturali e priorita' operative.
- [Specifica_regole_generatore_xml_tia_v20.md](/home/administrator/PLConversionTool/Specifica_regole_generatore_xml_tia_v20.md): regole rigide di generazione XML e pseudo-codice dei serializer.

Direzione di lavoro attuale:

1. mantenere come obiettivo centrale la conversione `AWL -> GRAPH`;
2. implementare come fondazione tecnica validator e generatori XML per `SW.Blocks.FB`, `SW.Blocks.GlobalDB` e `SW.Blocks.FC`;
3. usare `tia_bridge/` e `tia_windows_agent/` per import, compile ed export di regressione.

Documentazione utile:

- [docs/INDEX.md](/home/administrator/PLConversionTool/docs/INDEX.md)
- [docs/project-structure.md](/home/administrator/PLConversionTool/docs/project-structure.md)
- [docs/workflow/import-checklists.md](/home/administrator/PLConversionTool/docs/workflow/import-checklists.md)
