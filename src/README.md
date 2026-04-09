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
- preview XML strutturali per `FB GRAPH`, `GlobalDB` e `FC LAD`.
