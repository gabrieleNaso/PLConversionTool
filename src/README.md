# Core Converter

Questa cartella contiene il nucleo deterministico del progetto.
Qui devono vivere logiche riusabili condivise tra backend, script e test.

Responsabilita' principali:
- parser AWL
- modello intermedio della macchina a stati
- mapper verso GRAPH
- generatori XML (`FB`, `GlobalDB`, `FC`)
- validator e normalizzatori condivisi

Regola chiave:
- il core deve produrre un pacchetto coerente (`FB GRAPH` + `GlobalDB` + `FC LAD` + blocchi aggiuntivi)
