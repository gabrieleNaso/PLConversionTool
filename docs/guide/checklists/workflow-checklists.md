# Checklist operative (TIA Portal V20 / GRAPH V2)

Queste checklist sono da eseguire sempre prima di perdere tempo su debug casuale.
Fonte: `docs/reference/reports/report_del_23-04-2026.md` e `docs/reference/specs/Specifica_master_traduzione_AWL_e_generazione_XML_TIA_V20_V2_23_04.md`.

Regola trasversale:
- `FB GRAPH`, `GlobalDB`, `FC LAD` e ogni eventuale blocco aggiuntivo vanno verificati come pacchetto coerente.
- Un import riuscito del singolo XML non e' sufficiente se il blocco non e' coerente con gli altri blocchi che dovranno compilarlo o consumarlo.
- La checklist va applicata tenendo distinto il ruolo dei tipici legacy semantici dai tipici target `V20 / GRAPH V2`.

## A) Checklist rapida — FB GRAPH importabile
- **Documento/namespace**: root `Document` senza prefissi tipo `ns0:`, namespace `Interface` e `Graph` dichiarati localmente.
- **Struttura blocco**: `SW.Blocks.FB` + `AttributeList` + `CompileUnit` con GRAPH.
- **Interface bilanciata**: almeno `Input/Output/InOut/Static/Temp/...` coerenti.
- **Static runtime obbligatori**: `RT_DATA : G7_RTDataPlus_V2` + member per ogni step/transition.
- **Topologia GRAPH**: `Steps/Transitions/Branches/Connections` completa e chiusa.
- **Transition FlgNet "subset sicuro"**: struttura LAD delle transition nel sottoinsieme accettato da TIA.
- **Step iniziale**: verificare che `Init="true"` sia assegnato al passo corretto (in workflow Excel: `step_number=1`).
- **Simboli risolvibili**: tutto cio' che e' referenziato nel `FlgNet` deve essere dichiarato (locale FB o `GlobalDB` con riferimento simbolico esplicito).
- **Coerenza col pacchetto**: ogni tag, member o nome di blocco referenziato dal `GRAPH` deve esistere e combaciare davvero nel `GlobalDB`/`FC` del pacchetto corrente.

## B) Checklist rapida — GlobalDB del pacchetto importabile (+ commenti visibili)
- **Blocco**: `SW.Blocks.GlobalDB` con struttura Openness standard (`AttributeList`, `ObjectList` coerente).
- **Serializer Member ricorsivo**: `Member` annidati correttamente; niente template statici copiati.
- **Organizzazione**: preferire `Struct` funzionali (cmd/feedback/param/diag/mapping...).
- **Naming coerente**: naming deterministico, stabile, leggibile (vedi `docs/guide/standards/conventions.md`).
- **Commenti visibili in TIA**: verificare forma/posizionamento commenti come nel caso validato del DB di prova.
- **Origine commenti DB (Excel)**: nei DB usare solo `operands.note` + commenti member espliciti; non copiare commenti rete FC nei tag DB.
- **No autocompilazione commenti**: se Excel non valorizza commento/note, il commento DB deve restare vuoto.
- **Contratto cross-blocco**: il DB deve dichiarare tutti i member richiesti dal `GRAPH`, dalla `FC LAD` e da eventuali blocchi aggiuntivi del pacchetto, senza drift di naming.
- **Caso Excel strict**: verificare che i member DB siano coerenti con il catalogo `operands` del file Excel, senza extra non dichiarati.

## C) Checklist rapida — FC LAD importabile
- **Blocco**: `SW.Blocks.FC` in LAD, importabile anche con interfaccia minima.
- **CompileUnit ordinati**: sequenza coerente di `SW.Blocks.CompileUnit`.
- **Merge reti da Excel**: righe con stessa `category` + stesso `network` devono stare nella stessa CompileUnit FC.
- **FlgNet valido**: uso corretto di `PartNode`, `TemplateValue`, `CallInfo`, ecc.
- **Power rail unico**: ogni network LAD deve avere un solo `Powerrail`.
- **GlobalVariable**: ok usarle nel `FlgNet` (riferimenti simbolici espliciti), purché risolvibili.
- **Coerenza col pacchetto**: la `FC LAD` non deve introdurre riferimenti, mapping o nomi di member che non esistono davvero nel `GlobalDB` o che divergono dal `GRAPH`.

## D) Diagnosi quando l'import fallisce
- **Prima**: validare struttura XML (hard) prima dei metadati runtime (soft).
- **Poi**: isolare la causa con diff mentale rispetto a un golden sample importato.
- **Regola pratica**: nei GRAPH complessi serve coerenza piu' stretta tra `Sequence`, `Static`, `Temp` e `FlgNet`.
- **Regola pratica 2**: distinguere sempre fra errore di import del singolo XML ed errore di incoerenza del pacchetto compilato; i due problemi hanno cause diverse e vanno tracciati separatamente.
- **Regola pratica 3**: quando la logica diverge dall'AWL, verificare in `<bundle>_analysis.json` le `guard_expression` delle transizioni (`OR/NOT` e gruppi devono restare semantici).
- **Regola pratica 4**: prima di confrontare output vecchi/nuovi, rigenerare il bundle assicurandosi che la cartella target sia stata ricreata pulita (no XML residui).


## E) Gate di coerenza prima dell'import
- **Target runtime**: confermare che `GraphVersion`, datatype runtime e namespace siano coerenti con `TIA Portal V20 / GRAPH V2`.
- **Cardinalita' reale**: confermare che il bundle rappresenti `1 x FB GRAPH + N x GlobalDB + M x FC LAD`, senza moltiplicare impropriamente il GRAPH.
- **Backbone/inizio sequenza**: verificare la coerenza del passo iniziale (`step_number=1` in workflow Excel) e degli eventuali nodi strutturali richiesti dal caso.
- **Naming globale**: verificare owner DB, branch path e leaf name di tutti i riferimenti globali usati in `FlgNet` e GRAPH.
- **Segmentazione AWL**: verificare che la traduzione non abbia perso famiglie logiche ricorrenti (allarmi, memorie, sequenza, manuale/automatico, emergenza/fault, uscite).
- **Corpus di riferimento**: se il caso e' stato guidato da tipici `V6`, verificare che l'uso sia rimasto solo semantico e non abbia contaminato il serializer finale.
