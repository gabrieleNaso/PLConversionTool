## Convenzioni di naming (workspace)

### Naming file (artefatti XML)
- **FB GRAPH**: `FB_<AreaOImpianto>_<Funzione>_GRAPH_<variant>.xml`
  - es.: `FB_BottlingLine_GRAPH_strict_rebased.xml`
- **GlobalDB companion**: `DB_<AreaOImpianto>_<Funzione>_companion_<variant>.xml`
- **FC LAD**: `FC_<AreaOImpianto>_<Funzione>_<variant>.xml`

Suggerimento: usare suffissi di variante solo quando aggiungono informazione utile:
- `strict`: serializer/validator “hard rules” attivo
- `rebased`: wrapper/struttura riallineata senza cambiare la logica interna
- `golden`: campione “import riuscito” da usare come riferimento stabile

### Naming strutture nel GlobalDB (consigliato)
Organizzare per macro-strutture funzionali, evitando DB “piatti”:
- `Cmd` (comandi)
- `Fb` (feedback)
- `Par` (parametri/ricetta)
- `En` (enable/consensi)
- `Diag` (diagnostica)
- `Hmi` (dati HMI)
- `Map` (mapping AWL→GRAPH / supporto tool)

### Regole pratiche
- **Stabilità**: il naming deve essere deterministico (stesso input → stessi simboli).
- **Allineamento**: simboli referenziati nel `FlgNet` devono esistere e avere naming identico tra FB/DB.
- **Evitare ambiguità**: niente acronimi non condivisi; preferire naming impiantistico.

