# Core Converter

Questa cartella e' riservata al nucleo deterministico del progetto.

Destinazione consigliata:
- parser AWL;
- modello intermedio della macchina a stati;
- mapper verso GRAPH;
- generatori XML per `FB`, `GlobalDB` e `FC`;
- validator e normalizzatori condivisi.

Tenere qui la logica riusabile aiuta a non duplicarla tra backend, script e test.

Baseline operativa attuale:
- parser AWL incrementale con reti, step, transizioni, timer, memorie e output;
- IR esplicito riusabile dal backend;
- validator locali iniziali;
- preview XML strutturali per il pacchetto completo `FB GRAPH` + `GlobalDB` + `FC LAD`;
- coerenza cross-blocco sui tag transizione: ogni tag usato in `GRAPH/FC` e' dichiarato nel `GlobalDB` companion, incluse transizioni sintetiche (es. `T_HOLD_*`, `T_CHAIN_*`).

Regola di sviluppo da mantenere sempre:
- il core non deve generare blocchi validi solo presi singolarmente;
- deve generare un pacchetto coerente, in cui `FB GRAPH`, `GlobalDB`, `FC LAD` e ogni blocco aggiuntivo richiesto condividano naming, simboli, member, contratti runtime e assunzioni topologiche;
- un riferimento introdotto in uno dei blocchi del pacchetto deve essere validabile contro gli altri blocchi, non solo contro il singolo XML che lo contiene.
