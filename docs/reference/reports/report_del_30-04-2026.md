# Report aggiornato del 30-04-2026

## Progetto
Conversione di sequenziatori PLC da AWL a GRAPH in TIA Portal V20 tramite XML.

Questo report integra il report consolidato del 29-04-2026 (`docs/reference/reports/report_del_29-04-2026.md`) con i delta tecnici emersi il 30-04-2026.

---

## 1. Delta principali (30-04-2026)

### 1.1 `MOVE` (AWL `L/T`) correttamente in `FC 12 HMI` e non in `FC 13 Aux`

Problema osservato:
- i `MOVE` venivano serializzati in `FC 13 Aux` invece che in `FC 12 HMI` (divergenza rispetto al progetto di esempio).

Regola consolidata:
- le sequenze AWL `L ...` / `T ...` (scritture word/int/time/string) devono essere tradotte come box LAD `Move` nella `FC 12 HMI`;
- l'owner del target non cambia: la rete `Move` può scrivere anche verso member residenti in altri DB (es. AUX) tramite riferimenti simbolici, ma la logica `Move` resta in HMI.

### 1.2 Enable dei `MOVE`: fix canonicalizzazione step (`S01` → `S1`)

Problema osservato:
- alcuni `MOVE` risultavano senza logica di enable (enable collegato direttamente a `Powerrail`), perché in AWL venivano usati step zero-padded (`S01`, `S02`, ...) che non matchavano il catalogo step derivato (`S1`, `S2`, ...).

Correzione consolidata:
- i token step vengono canonicalizzati (`S0*(n)` → `Sn`) prima del filtro “step esiste nel GRAPH”;
- conseguenza: i `MOVE` condizionati da step attivo tornano ad avere la catena di contatti corretta (niente `Powerrail -> Move.en` nei casi analizzati).

