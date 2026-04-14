# Checklist operative (TIA Portal V20 / GRAPH V2)

Queste checklist sono da eseguire sempre prima di perdere tempo su debug casuale.
Fonte: `docs/reference/report-2026-04-14.md` e `docs/reference/spec-awl-xml-tia-v20-2026-04-14.md`.

Regola trasversale:
- `FB GRAPH`, `GlobalDB`, `FC LAD` e ogni eventuale blocco aggiuntivo vanno verificati come pacchetto coerente.
- Un import riuscito del singolo XML non e' sufficiente se il blocco non e' coerente con gli altri blocchi che dovranno compilarlo o consumarlo.

## A) Checklist rapida — FB GRAPH importabile
- **Documento/namespace**: root `Document` senza prefissi tipo `ns0:`, namespace `Interface` e `Graph` dichiarati localmente.
- **Struttura blocco**: `SW.Blocks.FB` + `AttributeList` + `CompileUnit` con GRAPH.
- **Interface bilanciata**: almeno `Input/Output/InOut/Static/Temp/...` coerenti.
- **Static runtime obbligatori**: `RT_DATA : G7_RTDataPlus_V2` + member per ogni step/transition.
- **Topologia GRAPH**: `Steps/Transitions/Branches/Connections` completa e chiusa.
- **Transition FlgNet "subset sicuro"**: struttura LAD delle transition nel sottoinsieme accettato da TIA.
- **Simboli risolvibili**: tutto cio' che e' referenziato nel `FlgNet` deve essere dichiarato (locale FB o `GlobalDB` con riferimento simbolico esplicito).
- **Coerenza col pacchetto**: ogni tag, member o nome di blocco referenziato dal `GRAPH` deve esistere e combaciare davvero nel `GlobalDB`/`FC` del pacchetto corrente.

## B) Checklist rapida — GlobalDB del pacchetto importabile (+ commenti visibili)
- **Blocco**: `SW.Blocks.GlobalDB` con struttura Openness standard (`AttributeList`, `ObjectList` coerente).
- **Serializer Member ricorsivo**: `Member` annidati correttamente; niente template statici copiati.
- **Organizzazione**: preferire `Struct` funzionali (cmd/feedback/param/diag/mapping...).
- **Naming coerente**: naming deterministico, stabile, leggibile (vedi `docs/conventions.md`).
- **Commenti visibili in TIA**: verificare forma/posizionamento commenti come nel caso validato del DB di prova.
- **Contratto cross-blocco**: il DB deve dichiarare tutti i member richiesti dal `GRAPH`, dalla `FC LAD` e da eventuali blocchi aggiuntivi del pacchetto, senza drift di naming.

## C) Checklist rapida — FC LAD importabile
- **Blocco**: `SW.Blocks.FC` in LAD, importabile anche con interfaccia minima.
- **CompileUnit ordinati**: sequenza coerente di `SW.Blocks.CompileUnit`.
- **FlgNet valido**: uso corretto di `PartNode`, `TemplateValue`, `CallInfo`, ecc.
- **GlobalVariable**: ok usarle nel `FlgNet` (riferimenti simbolici espliciti), purché risolvibili.
- **Coerenza col pacchetto**: la `FC LAD` non deve introdurre riferimenti, mapping o nomi di member che non esistono davvero nel `GlobalDB` o che divergono dal `GRAPH`.

## D) Diagnosi quando l'import fallisce
- **Prima**: validare struttura XML (hard) prima dei metadati runtime (soft).
- **Poi**: isolare la causa con diff mentale rispetto a un golden sample importato.
- **Regola pratica**: nei GRAPH complessi serve coerenza piu' stretta tra `Sequence`, `Static`, `Temp` e `FlgNet`.
- **Regola pratica 2**: distinguere sempre fra errore di import del singolo XML ed errore di incoerenza del pacchetto compilato; i due problemi hanno cause diverse e vanno tracciati separatamente.
