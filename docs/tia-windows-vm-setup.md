# TIA Windows VM Setup

Questa nota serve quando `TIA Portal` gira su una VM Windows VMware separata dal compose Linux.

## Architettura corretta

- il compose locale non deve tentare di eseguire `TIA Portal`;
- il servizio `tia-bridge` deve conoscere host e porta della VM Windows;
- nella VM Windows deve esistere un piccolo agent applicativo che riceve richieste e invoca `TIA Portal Openness` localmente.

Nel repository questo ruolo e' ora preparato in `tia_windows_agent/`.

## Perche' serve un agent Windows

Le DLL `TIA Portal Openness` vivono nell'ambiente Windows dove e' installato TIA. Questo significa che il container Linux non puo' caricarle direttamente via rete come farebbe con un database o una REST API standard.

## Rete VMware consigliata

- preferire `bridged` se vuoi che il container raggiunga la VM con un IP stabile sulla stessa rete;
- usare `NAT` solo se hai regole chiare di forwarding e raggiungibilita' tra host Linux, Docker e VM;
- assegnare, se possibile, un IP statico o prenotato alla VM Windows.

## Variabili da valorizzare

Esempio tipico:

```env
TIA_VMWARE_NETWORK_MODE=bridged
TIA_WINDOWS_TRANSPORT=http
TIA_WINDOWS_HOST=192.168.1.50
TIA_WINDOWS_AGENT_PORT=8050
TIA_WINDOWS_AGENT_URL=http://192.168.1.50:8050
```

## Materiale pronto da copiare nella VM

Cartella da importare:

- `tia_windows_agent/`

Script gia' pronti:

- `bootstrap-vm.ps1`
- `run-agent.ps1`
- `publish-agent.ps1`
- `install-firewall-rule.ps1`
- `start-agent.cmd`

## Checklist minima lato Windows

- `TIA Portal` installato nella versione corretta;
- utente Windows nel gruppo locale `Siemens TIA Openness`;
- agent Windows in ascolto sulla porta scelta;
- firewall Windows aperto verso l'host/container che deve chiamarlo;
- test di raggiungibilita' dalla macchina Linux verso la VM.
