Specifica XML consolidata
e pseudo-codice del serializer Python
AWL -> GRAPH / GlobalDB / FC LAD per TIA Portal V20

> Documento unico che raccoglie: 1) la specifica rigida di generazione XML, 2) il template generator operativo, 3) il pseudo-codice del serializer.

# Uso del documento

Questo file è strutturato per passare direttamente dalla baseline del progetto all'implementazione. La Parte I descrive la grammatica XML consolidata; la Parte II traduce la baseline in contratti di generazione; la Parte III propone uno pseudo-codice Python per i serializer e i validator minimi.

Questo documento va usato come baseline tecnica del backend di emissione XML dentro un progetto il cui obiettivo resta la conversione `AWL -> GRAPH`.

Ordine di lavoro raccomandato:

1. mantenere separato l'obiettivo finale `AWL -> GRAPH` dal backend di generazione XML;
2. definire IR manuali o di test per `FB GRAPH`, `GlobalDB` e `FC LAD`;
3. implementare validator e serializer XML sul sottoinsieme consolidato;
4. agganciare poi il parser AWL e la logica di estrazione della macchina a stati.

# Parte I - Specifica rigida di generazione XML

Regola metodologica di fondo: il generatore deve essere universale ma non libero. Deve emettere solo pattern, topologie e strutture che rientrano nel sottoinsieme validato.

## 1. SW.Blocks.FB GRAPH

Obiettivo: generare un FB GRAPH autosufficiente per topologia, runtime, Temp e Static.

Root obbligatorio: Document -> Engineering version="V20" -> SW.Blocks.FB ID="0".

Dentro AttributeList devono comparire: GraphVersion, Interface, Name, Namespace, Number, ProgrammingLanguage, SetENOAutomatically.

L'Interface deve dichiarare localmente il namespace SW/Interface/v5.

La sezione Base deve contenere GRAPH_BASE con Input, Output, InOut e Static.

Le sezioni effettivamente consolidate sono: Input, Output, InOut, Static, Temp, Constant.

In Static devono esistere almeno RT_DATA : G7_RTDataPlus_V2, un G7_TransitionPlus_V2 per ogni transition e un G7_StepPlus_V2 per ogni step.

In Temp devono esistere gli ET_Tx per le transition temporizzate.

Nel CompileUnit il NetworkSource deve contenere Graph nel namespace SW/NetworkSource/Graph/v5.

La Sequence deve essere composta da Steps, Transitions, Branches e Connections.

Le transition sono in LAD e vanno emesse nel sottoinsieme sicuro: Access, Contact, Contact negato, O, comparatori validati, TrCoil.

I branch consolidati sono AltBegin, SimBegin, SimEnd; i link ammessi sono Direct e Jump.

### Composizione canonica

```text
Document
  Engineering version="V20"
  SW.Blocks.FB ID="0"
    AttributeList
      GraphVersion = 2.0
      Interface
        Sections xmlns=".../SW/Interface/v5"
          Section Base
          Section Input
          Section Output
          Section InOut
          Section Static
          Section Temp
          Section Constant
      Name
      Namespace
      Number
      ProgrammingLanguage = GRAPH
      SetENOAutomatically = false
    ObjectList
      MultilingualText Comment
      SW.Blocks.CompileUnit
        AttributeList
          NetworkSource
            Graph xmlns=".../SW/NetworkSource/Graph/v5"
              PreOperations
              Sequence
                Steps
                Transitions
                Branches
                Connections
              PostOperations
```

### Esempio minimo

```text
<?xml version="1.0" encoding="utf-8"?>
<Document>
  <Engineering version="V20" />
  <SW.Blocks.FB ID="0">
    <AttributeList>
      <GraphVersion>2.0</GraphVersion>
      <Interface><Sections xmlns="http://www.siemens.com/automation/Openness/SW/Interface/v5">
  <Section Name="Base">
    <Sections Datatype="GRAPH_BASE" Version="1.0">
      <Section Name="Input" />
      <Section Name="Output" />
      <Section Name="InOut" />
      <Section Name="Static" />
    </Sections>
  </Section>
  <Section Name="Input">
    <Member Name="condition_type_1_transition_1" Datatype="Bool" />
  </Section>
  <Section Name="Output" />
  <Section Name="InOut" />
  <Section Name="Static">
    <Member Name="RT_DATA" Datatype="G7_RTDataPlus_V2" Version="1.0" />
    <Member Name="Transition_1" Datatype="G7_TransitionPlus_V2" Version="1.0" />
    <Member Name="Step_1" Datatype="G7_StepPlus_V2" Version="1.0" />
  </Section>
  <Section Name="Temp" />
  <Section Name="Constant" />
</Sections></Interface>
      <Name>Type_1</Name>
      <Namespace />
      <Number>1</Number>
      <ProgrammingLanguage>GRAPH</ProgrammingLanguage>
      <SetENOAutomatically>false</SetENOAutomatically>
    </AttributeList>
  </SW.Blocks.FB>
</Document>
```

## 2. SW.Blocks.GlobalDB

Obiettivo: generare il DB companion applicativo, non il runtime interno del GRAPH.

Il root obbligatorio è Document -> Engineering version="V20" -> SW.Blocks.GlobalDB ID="0".

In AttributeList devono comparire: Interface, MemoryLayout, MemoryReserve (se usato), Name, Namespace, Number, ProgrammingLanguage.

L'Interface usa Sections con namespace locale SW/Interface/v5.

La sezione dati consolidata è Section Name="Static".

Ogni Member può contenere AttributeList, Comment, StartValue e figli Member se il Datatype è Struct.

I commenti visibili in TIA devono essere emessi in forma semplice Comment + MultiLanguageText.

IEC_TIMER e IEC_COUNTER vanno serializzati con Version="1.0".

Il DB companion non deve replicare RT_DATA né gli statici runtime del GRAPH.

### Composizione canonica

```text
Document
  Engineering version="V20"
  SW.Blocks.GlobalDB ID="0"
    AttributeList
      Interface
        Sections xmlns=".../SW/Interface/v5"
          Section Name="Static"
            Member
            Member
      MemoryLayout
      MemoryReserve
      Name
      Namespace
      Number
      ProgrammingLanguage = DB
    ObjectList
      MultilingualText Comment
      MultilingualText Title
```

### Esempio minimo

```text
<?xml version="1.0" encoding="utf-8"?>
<Document>
  <Engineering version="V20" />
  <SW.Blocks.GlobalDB ID="0">
    <AttributeList>
      <Interface><Sections xmlns="http://www.siemens.com/automation/Openness/SW/Interface/v5">
  <Section Name="Static">
    <Member Name="var_1" Datatype="Bool" />
    <Member Name="var_2" Datatype="Int" />
    <Member Name="var_4" Datatype="Array[0..9] of Bool" Remanence="Retain" />
    <Member Name="var_5" Datatype="Struct">
      <Member Name="var_5_1" Datatype="Bool" />
      <Member Name="var_5_2" Datatype="Int" />
      <Member Name="var_5_3" Datatype="Real" />
    </Member>
    <Member Name="var_8" Datatype="IEC_COUNTER" Version="1.0" />
    <Member Name="var_9" Datatype="IEC_TIMER" Version="1.0" />
  </Section>
</Sections></Interface>
      <MemoryLayout>Optimized</MemoryLayout>
      <MemoryReserve>100</MemoryReserve>
      <Name>db_1</Name>
      <Namespace />
      <Number>1</Number>
      <ProgrammingLanguage>DB</ProgrammingLanguage>
    </AttributeList>
  </SW.Blocks.GlobalDB>
</Document>
```

## 3. SW.Blocks.FC in LAD

Obiettivo: generare reti LAD importabili, solo tramite pattern già validati.

Il root obbligatorio è Document -> Engineering version="V20" -> SW.Blocks.FC ID="0".

In AttributeList devono comparire: Interface, MemoryLayout, Name, Namespace, Number, ProgrammingLanguage, SetENOAutomatically.

L'Interface standard contiene Input, Output, InOut, Temp, Constant e Return con Ret_Val : Void.

Un FC importabile è una lista ordinata di CompileUnit.

Dentro ogni CompileUnit il NetworkSource contiene FlgNet nel namespace SW/NetworkSource/FlgNet/v5.

Ogni FlgNet deve essere composto da Parts e Wires coerenti.

L'OR va serializzato con Part Name="O" e TemplateValue Name="Card" Type="Cardinality".

TON, TOF e CTU vanno serializzati come box IEC nativi, non come call generiche.

PT timer va come TypedConstant di tipo Time; PV CTU come LiteralConstant Int; i pin non usati vanno preferibilmente a OpenCon.

### Composizione canonica

```text
Document
  Engineering version="V20"
  SW.Blocks.FC ID="0"
    AttributeList
      Interface
        Sections xmlns=".../SW/Interface/v5"
          Section Input
          Section Output
          Section InOut
          Section Temp
          Section Constant
          Section Return
      MemoryLayout
      Name
      Namespace
      Number
      ProgrammingLanguage = LAD
      SetENOAutomatically = false
    ObjectList
      MultilingualText Comment
      SW.Blocks.CompileUnit
        AttributeList
          NetworkSource
            FlgNet xmlns=".../SW/NetworkSource/FlgNet/v5"
              Parts
              Wires
          ProgrammingLanguage = LAD
```

### Esempio minimo

```text
<?xml version="1.0" encoding="utf-8"?>
<Document>
  <Engineering version="V20" />
  <SW.Blocks.FC ID="0">
    <AttributeList>
      <Interface><Sections xmlns="http://www.siemens.com/automation/Openness/SW/Interface/v5">
  <Section Name="Input" />
  <Section Name="Output" />
  <Section Name="InOut" />
  <Section Name="Temp">
    <Member Name="Start" Datatype="Bool" />
    <Member Name="m_req" Datatype="Bool" />
  </Section>
  <Section Name="Constant" />
  <Section Name="Return">
    <Member Name="Ret_Val" Datatype="Void" />
  </Section>
</Sections></Interface>
      <MemoryLayout>Optimized</MemoryLayout>
      <Name>fc_3</Name>
      <Namespace />
      <Number>2</Number>
      <ProgrammingLanguage>LAD</ProgrammingLanguage>
      <SetENOAutomatically>false</SetENOAutomatically>
    </AttributeList>
  </SW.Blocks.FC>
</Document>
```

# Parte II - Template generator operativo

Questa parte traduce la specifica in contratti di emissione. I placeholder sono pensati per un serializer Python che lavori su IR espliciti.

## Convenzioni

[REQ] = obbligatorio

[OPT] = opzionale

[COND] = obbligatorio solo in certe condizioni

[REP] = ripetibile

[DER] = derivato dal modello o calcolato

```text
Placeholder principali:
{BLOCK_NAME} {BLOCK_NUMBER} {DB_NAME} {DB_NUMBER} {FC_NAME} {FC_NUMBER}
{STEP_NAME} {STEP_NO} {TRANS_NAME} {TRANS_NO}
{INPUT_NAME} {TEMP_NAME} {MEMBER_NAME} {DATATYPE}
{COMMENT_TEXT} {START_VALUE} {UId_N} {TIME_CONST} {DB_SYMBOL} {VAR_SYMBOL}
```

## 1. Contratto del GRAPH compiler

```text
graph_block:
  name
  number
  inputs[]
  outputs[]
  inouts[]
  static_runtime
  steps[]
  transitions[]
  branches[]
  connections[]
  temp_vars[]
  block_comment
```

[REQ] GraphVersion = 2.0

[REQ] Section Base con GRAPH_BASE

[REQ] RT_DATA + runtime transition + runtime step

[COND] Section Temp ed ET_Tx solo se esistono transition temporizzate

[REQ] Steps, Transitions, Branches, Connections

[REQ] Transition LAD solo nel sottoinsieme validato

### Ordine di emissione del GRAPH

```text
1. Document
2. Engineering(version="V20")
3. SW.Blocks.FB(ID="0")
4. AttributeList
5. GraphVersion
6. Interface
7. Base / Input / Output / InOut / Static / Temp / Constant
8. Name / Namespace / Number / ProgrammingLanguage / SetENOAutomatically
9. ObjectList
10. Comment blocco
11. CompileUnit
12. NetworkSource/Graph
13. PreOperations
14. Sequence
15. Steps
16. Transitions
17. Branches
18. Connections
19. PostOperations
```

## 2. Contratto del GlobalDB compiler

```text
global_db:
  name
  number
  memory_layout
  memory_reserve
  block_comment
  block_title
  members[]
```

[REQ] Section Name="Static"

[REQ] serializer ricorsivo e tree-based

[REQ] supporto a scalari, array, struct, IEC_TIMER, IEC_COUNTER

[OPT] AttributeList, Comment, StartValue a livello Member

[COND] Version per tipi IEC versionati

### Funzione ricorsiva canonica

```text
emit_member(m):
    open <Member Name=... Datatype=... [Version=...] [Remanence=...]>

    if m.attributes:
        emit <AttributeList>...</AttributeList>

    if m.comment:
        emit <Comment><MultiLanguageText Lang="en-US">...</MultiLanguageText></Comment>

    if m.start_value exists:
        emit <StartValue>...</StartValue>

    for child in m.children:
        emit_member(child)

    close </Member>
```

## 3. Contratto del FC compiler

```text
fc_block:
  name
  number
  temp_members[]
  compile_units[]
  block_comment
```

[REQ] Interface standard con Return/Ret_Val : Void

[REQ] CompileUnit ordinate

[REQ] FlgNet con Parts e Wires coerenti

[COND] Access LocalVariable o GlobalVariable

[COND] O con TemplateValue Card

[COND] TON/TOF/CTU come box IEC nativi

[REQ] pattern library validata; niente XML LAD libero

### Checklist strutturale minima del backend FC

```text
Document presente
Engineering version="V20" presente
SW.Blocks.FC presente
ProgrammingLanguage = LAD coerente a livello blocco e rete
CompileUnit ordinate
FlgNet con Parts e Wires
UId coerenti
connessioni risolte
nessun pin inesistente
nessun nodo orfano
```

# Parte III - Pseudo-codice del serializer Python

Lo pseudo-codice seguente non è ancora il codice finale del tool, ma è pensato per essere tradotto quasi direttamente in Python. Presuppone tre IR distinti e una libreria comune di helper XML.

## 1. Strutture IR minime

```text
class GraphIR:
    name: str
    number: int
    inputs: list[VarDecl]
    outputs: list[VarDecl]
    inouts: list[VarDecl]
    temp_vars: list[VarDecl]
    steps: list[StepIR]
    transitions: list[TransitionIR]
    branches: list[BranchIR]
    connections: list[ConnectionIR]
    block_comment: str

class GlobalDBIR:
    name: str
    number: int
    memory_layout: str
    memory_reserve: int | None
    block_comment: str
    block_title: str
    members: list[MemberIR]

class FCIR:
    name: str
    number: int
    temp_members: list[VarDecl]
    compile_units: list[CompileUnitIR]
    block_comment: str
class MemberIR:
    name: str
    datatype: str
    version: str | None
    remanence: str | None
    attributes: list[AttributeIR]
    comment: str | None
    start_value: str | None
    children: list["MemberIR"]

class TransitionIR:
    number: int
    name: str
    flgnet: FlgNetIR
    has_timer: bool
    et_name: str | None
```

## 2. Helper comuni

```text
def el(tag: str, text: str | None = None, attrs: dict | None = None) -> X:
    node = Element(tag)
    if attrs:
        for k, v in attrs.items():
            node.set(k, str(v))
    if text is not None:
        node.text = text
    return node

def append(parent: X, child: X) -> X:
    parent.append(child)
    return child

def sorted_by_name(items):
    return sorted(items, key=lambda x: x.name)

def assert_unique(values, what: str):
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {what}")

def validate_bool_string(value: str):
    if value not in {"true", "false"}:
        raise ValueError("Expected XML bool string")
```

## 3. Validator GRAPH

```text
def validate_graph_ir(g: GraphIR) -> None:
    assert g.name
    assert g.number > 0
    assert len(g.steps) >= 1
    assert len(g.transitions) >= 1

    assert_unique([s.number for s in g.steps], "step numbers")
    assert_unique([t.number for t in g.transitions], "transition numbers")

    init_steps = [s for s in g.steps if s.is_init]
    if len(init_steps) != 1:
        raise ValueError("GRAPH must have exactly one init step")

    for t in g.transitions:
        if t.flgnet is None:
            raise ValueError(f"Transition {t.name} has no FlgNet")
        if not t.flgnet.has_trcoil():
            raise ValueError(f"Transition {t.name} must end with one TrCoil")
        if t.has_timer and not t.et_name:
            raise ValueError(f"Transition {t.name} missing ET temp variable")

    validate_graph_topology(g)

def validate_graph_topology(g: GraphIR) -> None:
    # Implementare qui:
    # - ingressi/uscite consentiti
    # - uso corretto di AltBegin / SimBegin / SimEnd
    # - assenza di doppi ingressi Direct su step non iniziale
    # - coerenza fra nodes e connections
    pass
```

## 4. Serializer GRAPH

```text
def emit_graph_fb(g: GraphIR) -> X:
    validate_graph_ir(g)

    doc = el("Document")
    append(doc, el("Engineering", attrs={"version": "V20"}))
    fb = append(doc, el("SW.Blocks.FB", attrs={"ID": "0"}))

    attr = append(fb, el("AttributeList"))
    append(attr, el("GraphVersion", "2.0"))
    append(attr, emit_graph_interface(g))
    append(attr, el("Name", g.name))
    append(attr, el("Namespace", ""))
    append(attr, el("Number", str(g.number)))
    append(attr, el("ProgrammingLanguage", "GRAPH"))
    append(attr, el("SetENOAutomatically", "false"))

    obj = append(fb, el("ObjectList"))
    append(obj, emit_block_comment(comment_id=1, item_id=2, text=g.block_comment))
    append(obj, emit_graph_compile_unit(g, cu_id=3))

    return doc
def emit_graph_interface(g: GraphIR) -> X:
    interface = el("Interface")
    sections = append(interface, el("Sections", attrs={
        "xmlns": "http://www.siemens.com/automation/Openness/SW/Interface/v5"
    }))

    base = append(sections, el("Section", attrs={"Name": "Base"}))
    base_sections = append(base, el("Sections", attrs={"Datatype": "GRAPH_BASE", "Version": "1.0"}))
    append(base_sections, el("Section", attrs={"Name": "Input"}))
    append(base_sections, el("Section", attrs={"Name": "Output"}))
    append(base_sections, el("Section", attrs={"Name": "InOut"}))
    append(base_sections, el("Section", attrs={"Name": "Static"}))

    sec_in = append(sections, el("Section", attrs={"Name": "Input"}))
    for v in sorted_by_name(g.inputs):
        append(sec_in, emit_simple_member(v))

    append(sections, el("Section", attrs={"Name": "Output"}))
    append(sections, el("Section", attrs={"Name": "InOut"}))

    sec_static = append(sections, el("Section", attrs={"Name": "Static"}))
    append(sec_static, el("Member", attrs={"Name": "RT_DATA", "Datatype": "G7_RTDataPlus_V2", "Version": "1.0"}))
    for t in sorted(g.transitions, key=lambda x: x.number):
        append(sec_static, el("Member", attrs={"Name": t.runtime_name, "Datatype": "G7_TransitionPlus_V2", "Version": "1.0"}))
    for s in sorted(g.steps, key=lambda x: x.number):
        append(sec_static, el("Member", attrs={"Name": s.runtime_name, "Datatype": "G7_StepPlus_V2", "Version": "1.0"}))

    sec_temp = append(sections, el("Section", attrs={"Name": "Temp"}))
    for t in sorted(g.transitions, key=lambda x: x.number):
        if t.has_timer:
            append(sec_temp, el("Member", attrs={"Name": t.et_name, "Datatype": "Time"}))

    append(sections, el("Section", attrs={"Name": "Constant"}))
    return interface
def emit_graph_compile_unit(g: GraphIR, cu_id: int) -> X:
    cu = el("SW.Blocks.CompileUnit", attrs={"ID": str(cu_id), "CompositionName": "CompileUnits"})
    attr = append(cu, el("AttributeList"))
    ns = append(attr, el("NetworkSource"))
    graph = append(ns, el("Graph", attrs={
        "xmlns": "http://www.siemens.com/automation/Openness/SW/NetworkSource/Graph/v5"
    }))

    pre = append(graph, el("PreOperations"))
    append(pre, el("PermanentOperation", attrs={"ProgrammingLanguage": "LAD"}))

    seq = append(graph, el("Sequence"))
    append(seq, el("Title"))
    c = append(seq, el("Comment"))
    append(c, el("MultiLanguageText", attrs={"Lang": "en-US"}))

    steps = append(seq, el("Steps"))
    for s in sorted(g.steps, key=lambda x: x.number):
        append(steps, emit_graph_step(s))

    transitions = append(seq, el("Transitions"))
    for t in sorted(g.transitions, key=lambda x: x.number):
        append(transitions, emit_graph_transition(t))

    branches = append(seq, el("Branches"))
    for b in g.branches:
        append(branches, emit_graph_branch(b))

    connections = append(seq, el("Connections"))
    for c in g.connections:
        append(connections, emit_graph_connection(c))

    post = append(graph, el("PostOperations"))
    append(post, el("PermanentOperation", attrs={"ProgrammingLanguage": "LAD"}))

    append(attr, el("ProgrammingLanguage", "GRAPH"))
    return cu
```

## 5. Validator e serializer GlobalDB

```text
def validate_db_ir(db: GlobalDBIR) -> None:
    assert db.name
    assert db.number > 0
    if not db.members:
        raise ValueError("GlobalDB must contain at least one member")

def emit_global_db(db: GlobalDBIR) -> X:
    validate_db_ir(db)

    doc = el("Document")
    append(doc, el("Engineering", attrs={"version": "V20"}))
    gdb = append(doc, el("SW.Blocks.GlobalDB", attrs={"ID": "0"}))

    attr = append(gdb, el("AttributeList"))
    append(attr, emit_db_interface(db))
    append(attr, el("MemoryLayout", db.memory_layout or "Optimized"))
    if db.memory_reserve is not None:
        append(attr, el("MemoryReserve", str(db.memory_reserve)))
    append(attr, el("Name", db.name))
    append(attr, el("Namespace", ""))
    append(attr, el("Number", str(db.number)))
    append(attr, el("ProgrammingLanguage", "DB"))

    obj = append(gdb, el("ObjectList"))
    append(obj, emit_block_comment(comment_id=1, item_id=2, text=db.block_comment))
    append(obj, emit_block_title(title_id=3, item_id=4, text=db.block_title))
    return doc
def emit_db_interface(db: GlobalDBIR) -> X:
    interface = el("Interface")
    sections = append(interface, el("Sections", attrs={
        "xmlns": "http://www.siemens.com/automation/Openness/SW/Interface/v5"
    }))
    sec_static = append(sections, el("Section", attrs={"Name": "Static"}))
    for m in db.members:
        append(sec_static, emit_member(m))
    return interface

def emit_member(m: MemberIR) -> X:
    attrs = {"Name": m.name, "Datatype": m.datatype}
    if m.version:
        attrs["Version"] = m.version
    if m.remanence:
        attrs["Remanence"] = m.remanence

    node = el("Member", attrs=attrs)

    if m.attributes:
        attr = append(node, el("AttributeList"))
        for a in m.attributes:
            append(attr, emit_attribute(a))

    if m.comment:
        c = append(node, el("Comment"))
        append(c, el("MultiLanguageText", m.comment, attrs={"Lang": "en-US"}))

    if m.start_value is not None:
        append(node, el("StartValue", m.start_value))

    for child in m.children:
        append(node, emit_member(child))

    return node
```

## 6. Validator e serializer FC

```text
def validate_fc_ir(fc: FCIR) -> None:
    assert fc.name
    assert fc.number > 0
    if not fc.compile_units:
        raise ValueError("FC must contain at least one CompileUnit")

    seen = set()
    for cu in fc.compile_units:
        if cu.id in seen:
            raise ValueError("Duplicate CompileUnit id")
        seen.add(cu.id)
        validate_flgnet(cu.flgnet)

def validate_flgnet(net: FlgNetIR) -> None:
    if not net.parts:
        raise ValueError("FlgNet without parts")
    if not net.wires:
        raise ValueError("FlgNet without wires")
    # Qui aggiungere:
    # - controllo UId univoci
    # - controllo endpoint esistenti
    # - nessun pin inesistente
    # - nessun nodo orfano
def emit_fc_lad(fc: FCIR) -> X:
    validate_fc_ir(fc)

    doc = el("Document")
    append(doc, el("Engineering", attrs={"version": "V20"}))
    block = append(doc, el("SW.Blocks.FC", attrs={"ID": "0"}))

    attr = append(block, el("AttributeList"))
    append(attr, emit_fc_interface(fc))
    append(attr, el("MemoryLayout", "Optimized"))
    append(attr, el("Name", fc.name))
    append(attr, el("Namespace", ""))
    append(attr, el("Number", str(fc.number)))
    append(attr, el("ProgrammingLanguage", "LAD"))
    append(attr, el("SetENOAutomatically", "false"))

    obj = append(block, el("ObjectList"))
    append(obj, emit_block_comment(comment_id=1, item_id=2, text=fc.block_comment))
    for cu in fc.compile_units:
        append(obj, emit_fc_compile_unit(cu))

    return doc
def emit_fc_interface(fc: FCIR) -> X:
    interface = el("Interface")
    sections = append(interface, el("Sections", attrs={
        "xmlns": "http://www.siemens.com/automation/Openness/SW/Interface/v5"
    }))
    append(sections, el("Section", attrs={"Name": "Input"}))
    append(sections, el("Section", attrs={"Name": "Output"}))
    append(sections, el("Section", attrs={"Name": "InOut"}))

    sec_temp = append(sections, el("Section", attrs={"Name": "Temp"}))
    for v in fc.temp_members:
        append(sec_temp, emit_simple_member(v))

    append(sections, el("Section", attrs={"Name": "Constant"}))
    sec_ret = append(sections, el("Section", attrs={"Name": "Return"}))
    append(sec_ret, el("Member", attrs={"Name": "Ret_Val", "Datatype": "Void"}))
    return interface
def emit_fc_compile_unit(cu: CompileUnitIR) -> X:
    node = el("SW.Blocks.CompileUnit", attrs={"ID": str(cu.id), "CompositionName": "CompileUnits"})
    attr = append(node, el("AttributeList"))
    ns = append(attr, el("NetworkSource"))
    flgnet = append(ns, el("FlgNet", attrs={
        "xmlns": "http://www.siemens.com/automation/Openness/SW/NetworkSource/FlgNet/v5"
    }))

    parts = append(flgnet, el("Parts"))
    for p in cu.flgnet.parts:
        append(parts, emit_part_or_access(p))

    wires = append(flgnet, el("Wires"))
    for w in cu.flgnet.wires:
        append(wires, emit_wire(w))

    append(attr, el("ProgrammingLanguage", "LAD"))
    return node
```

## 7. Emettitori di nodi LAD

```text
def emit_part_or_access(node):
    if node.kind == "access":
        access = el("Access", attrs={"Scope": node.scope, "UId": str(node.uid)})
        sym = append(access, el("Symbol"))
        for comp in node.symbol_components:
            append(sym, el("Component", attrs={"Name": comp}))
        return access

    if node.kind == "part":
        part = el("Part", attrs={"Name": node.name, "UId": str(node.uid)})
        if node.version:
            part.set("Version", node.version)
        for tv in node.template_values:
            append(part, el("TemplateValue", tv.value, attrs={"Name": tv.name, "Type": tv.type}))
        if node.instance:
            inst = append(part, el("Instance", attrs={"Scope": node.instance.scope, "UId": str(node.instance.uid)}))
            append(inst, el("Component", attrs={"Name": node.instance.component}))
        return part

    raise ValueError("Unknown node type")
def emit_wire(w: WireIR) -> X:
    wire = el("Wire", attrs={"UId": str(w.uid)})
    for ep in w.endpoints:
        if ep.kind == "powerrail":
            append(wire, el("Powerrail"))
        elif ep.kind == "ident":
            append(wire, el("IdentCon", attrs={"UId": str(ep.uid)}))
        elif ep.kind == "name":
            append(wire, el("NameCon", attrs={"UId": str(ep.uid), "Name": ep.name}))
        elif ep.kind == "open":
            append(wire, el("OpenCon", attrs={"UId": str(ep.uid)}))
        else:
            raise ValueError("Unknown endpoint kind")
    return wire
```

## 8. Helper documentali comuni

```text
def emit_block_comment(comment_id: int, item_id: int, text: str) -> X:
    mt = el("MultilingualText", attrs={"ID": str(comment_id), "CompositionName": "Comment"})
    obj = append(mt, el("ObjectList"))
    item = append(obj, el("MultilingualTextItem", attrs={"ID": str(item_id), "CompositionName": "Items"}))
    attr = append(item, el("AttributeList"))
    append(attr, el("Culture", "en-US"))
    append(attr, el("Text", text or ""))
    return mt

def emit_block_title(title_id: int, item_id: int, text: str) -> X:
    mt = el("MultilingualText", attrs={"ID": str(title_id), "CompositionName": "Title"})
    obj = append(mt, el("ObjectList"))
    item = append(obj, el("MultilingualTextItem", attrs={"ID": str(item_id), "CompositionName": "Items"}))
    attr = append(item, el("AttributeList"))
    append(attr, el("Culture", "en-US"))
    append(attr, el("Text", text or ""))
    return mt

def emit_simple_member(v: VarDecl) -> X:
    return el("Member", attrs={"Name": v.name, "Datatype": v.datatype})
```

## 9. Pipeline complessiva consigliata

```text
Fase 1: implementazione generatori XML
 -> IR sequenza / IR dati / IR reti definiti manualmente o da fixture
 -> validator GRAPH / DB / FC
 -> emit_graph_fb()
 -> emit_global_db()
 -> emit_fc_lad()
 -> export XML
 -> import TIA
 -> compile
 -> export regressione

Fase 2: automazione conversione AWL
 -> parser
 -> estrazione macchina a stati + pattern
 -> popolamento degli IR
 -> riuso invariato dei validator e serializer
```

## 10. Regole finali da non violare

Mai derivare regole del generatore da un singolo test isolato.

I file esempio validati sono oracoli di regressione, non il generatore.

Il backend GRAPH deve restare pattern-driven e validator-driven.

Il backend GlobalDB deve restare un serializer ricorsivo generale con grammatica fissa.

Il backend FC deve emettere solo pattern LAD già convalidati e combinazioni autorizzate.
