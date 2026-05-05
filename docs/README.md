# Documentazione progetto (allineamento guide: 27-04-2026)

Indice rapido:
- `guide/process/flow.md`

Struttura:
- `guide/process/flow.md`
- `guide/standards/conventions.md`
- `guide/operations/operations.md`
- `guide/operations/excel-ir-compilation-guide.md`
- `guide/integration/tia-integration.md`
- `guide/checklists/workflow-checklists.md`
- `templates/reports/daily-report-template.md`
- `reference/reports/report_del_27-04-2026.md`
- `reference/specs/Specifica_master_traduzione_AWL_e_generazione_XML_TIA_V20_V2_27_04.md`
- `../cases/README.md` (workflow casi input/expected)
- `../cases/translation_rules.md` (regole generiche AWL -> IR)

Criteri di aggiornamento integrati:
- gerarchia documentale chiara tra specifica/report e guide operative;
- conferma del modello `1 x FB GRAPH + N x GlobalDB + M x FC LAD` come pacchetto unico;
- rafforzamento del contratto di naming globale con owner DB + path + leaf name;
- distinzione esplicita tra tipici legacy `V6` e target finale `V20 / GRAPH V2`;
- segmentazione AWL ricorrente derivata anche dal caso `FC102` (sequenziatore/FC32-style).
