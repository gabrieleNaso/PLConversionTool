# TIA Bridge Service

Il servizio `tia_bridge/` e' il boundary layer dedicato all'orchestrazione verso `TIA Portal Openness`.

## Perche' esiste

Il contesto di progetto separa due responsabilita':

- generazione deterministica degli XML (`backend/` e, progressivamente, `src/`);
- orchestrazione di import, compile, export e confronto verso TIA (`tia_bridge/`).

Questa separazione evita di mescolare nel backend applicativo dettagli runtime e prerequisiti specifici di `TIA Portal`.

## Stato attuale

Nel setup dev il container `tia-bridge`:

- e' sempre sulla stessa rete Compose di `backend` e `frontend`;
- espone una API minima di health/status;
- monta `output/` e `tmp/` come aree condivise di scambio artefatti;
- prepara il punto di integrazione per il futuro adapter Openness reale.

## Nota importante

`TIA Portal Openness` richiede un ambiente Windows con installazione TIA compatibile e permessi corretti lato host. Per questo motivo il container Linux non ospita TIA Portal: funge da servizio di confine, pronto per collegarsi al target reale senza sporcare l'architettura del progetto.
