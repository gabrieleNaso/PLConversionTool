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
- prepara il punto di integrazione verso una VM Windows che ospita `TIA Portal`.

## VM Windows remota

Se `TIA Portal` gira su una VM VMware Windows, la topologia consigliata e':

- `backend/frontend` parlano con `tia-bridge` nel compose Linux;
- `tia-bridge` parla con un agent HTTP o RPC esposto dalla VM Windows;
- l'agent Windows usa localmente le DLL `TIA Portal Openness`.

Questo vincolo e' importante: `Openness` non si collega da remoto direttamente come un normale servizio TCP. Serve un processo lato Windows vicino a TIA.

## Variabili di configurazione principali

- `TIA_VMWARE_NETWORK_MODE`
- `TIA_WINDOWS_TRANSPORT`
- `TIA_WINDOWS_HOST`
- `TIA_WINDOWS_AGENT_PORT`
- `TIA_WINDOWS_AGENT_URL`

## Nota importante

`TIA Portal Openness` richiede un ambiente Windows con installazione TIA compatibile e permessi corretti lato host. Per questo motivo il container Linux non ospita TIA Portal: funge da servizio di confine, pronto per collegarsi al target reale senza sporcare l'architettura del progetto.
