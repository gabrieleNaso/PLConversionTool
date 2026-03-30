## Checklist operative (TIA Portal V20 / GRAPH V2)

Queste checklist sono “da eseguire sempre” prima di perdere tempo su debug casuale.
La fonte è il report consolidato `Contesto_progetto.md` (sezioni “Checklist” e “Prossimi passi”).

### A) Checklist rapida — FB GRAPH importabile
- **Documento/namespace**: root `Document` senza prefissi tipo `ns0:`, namespace `Interface` e `Graph` dichiarati localmente.
- **Struttura blocco**: `SW.Blocks.FB` + `AttributeList` + `CompileUnit` con GRAPH.
- **Interface bilanciata**: almeno `Input/Output/InOut/Static/Temp/...` coerenti.
- **Static runtime obbligatori**: `RT_DATA : G7_RTDataPlus_V2` + member per ogni step/transition.
- **Topologia GRAPH**: `Steps/Transitions/Branches/Connections` completa e chiusa.
- **Transition FlgNet “subset sicuro”**: struttura LAD delle transition nel sottoinsieme accettato da TIA.
- **Simboli risolvibili**: tutto ciò che è referenziato nel `FlgNet` deve essere dichiarato (locale FB o `GlobalDB` con riferimento simbolico esplicito).

### B) Checklist rapida — GlobalDB companion importabile (+ commenti visibili)
- **Blocco**: `SW.Blocks.GlobalDB` con struttura Openness standard (`AttributeList`, `ObjectList` coerente).
- **Serializer Member ricorsivo**: `Member` annidati correttamente; niente “template statici copiati”.
- **Organizzazione**: preferire `Struct` funzionali (cmd/feedback/param/diag/mapping…).
- **Naming coerente**: naming deterministico, stabile, leggibile (vedi `../conventions/naming.md`).
- **Commenti visibili in TIA**: verificare forma/posizionamento commenti come nel caso validato del DB di prova.

### C) Checklist rapida — FC LAD importabile
- **Blocco**: `SW.Blocks.FC` in LAD, importabile anche con interfaccia minima.
- **CompileUnit ordinati**: sequenza coerente di `SW.Blocks.CompileUnit`.
- **FlgNet valido**: uso corretto di `PartNode`, `TemplateValue`, `CallInfo`, ecc.
- **GlobalVariable**: ok usarle nel `FlgNet` (riferimenti simbolici espliciti), purché risolvibili.

### D) Diagnosi quando l’import fallisce
- **Prima**: validare struttura XML (hard) prima dei metadati runtime (soft).
- **Poi**: isolare la causa con “diff mentale” rispetto a un golden sample importato.
- **Regola pratica**: nei GRAPH complessi serve coerenza più stretta tra `Sequence`, `Static`, `Temp` e `FlgNet`.

