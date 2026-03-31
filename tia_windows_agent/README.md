# TIA Windows Agent

Servizio `.NET 8` da eseguire nella VM Windows dove sono installati `TIA Portal` e `TIA Portal Openness`.

## Scopo

Questo agent e' il punto di collegamento tra:

- il progetto Linux con `backend`, `frontend` e `tia-bridge`;
- la VM Windows VMware dove esiste davvero `TIA Portal`.

Il flusso corretto e':

1. il `backend` o il `frontend` parlano con `tia-bridge`;
2. `tia-bridge` parla via HTTP con questo agent Windows;
3. questo agent Windows usa localmente `TIA Portal Openness`.

Questo passaggio e' necessario perche' le DLL Siemens vivono nella VM Windows e non possono essere usate direttamente dal container Linux come se fossero una libreria remota.

## Cosa fa oggi

L'agent espone gia' questi endpoint:

- `GET /health`
- `GET /api/status`
- `GET /api/openness/diagnostics`
- `POST /api/jobs/import`
- `POST /api/jobs/compile`
- `POST /api/jobs/export`
- `GET /api/jobs`
- `GET /api/jobs/{jobId}`

In questa versione:

- accoda i job;
- li esegue in background;
- li processa in modo seriale;
- controlla configurazione e path locali;
- in modalita' `real` prova a caricare `Siemens.Engineering.dll`;
- in modalita' `real` prova a creare una istanza `TiaPortal`.

Questa e' gia' una base eseguibile e utile per verificare che la VM sia preparata correttamente.

## Cosa non fa ancora completamente

La parte finale non e' ancora completa al 100%:

- apertura reale del progetto TIA;
- import reale di FB / DB / FC;
- compile reale del progetto;
- export reale degli artefatti da TIA;
- mapping dettagliato degli errori Siemens sullo stato job.

Quindi questo pacchetto e' pronto per essere copiato ed eseguito, ma la parte finale delle chiamate Openness reali va rifinita dopo il primo test nella tua VM.

## Contenuto della cartella

File principali:

- `PLConversionTool.TiaAgent.csproj`
- `Program.cs`
- `appsettings.json`
- `appsettings.Local.template.json`

Script pronti:

- `bootstrap-vm.ps1`
- `run-agent.ps1`
- `publish-agent.ps1`
- `install-firewall-rule.ps1`
- `start-agent.cmd`

Documentazione utile:

- [docs/tia-windows-vm-setup.md](/home/administrator/PLConversionTool/docs/tia-windows-vm-setup.md)
- [docs/tia-windows-agent-api.md](/home/administrator/PLConversionTool/docs/tia-windows-agent-api.md)

## Prerequisiti nella VM Windows

Prima di fare qualsiasi avvio, nella VM devono essere veri tutti questi punti:

1. `TIA Portal` e' installato.
2. La versione TIA corrisponde al target del progetto, in questo momento `V20`.
3. Le DLL `Openness` sono presenti nella macchina Windows.
4. L'utente Windows che esegue l'agent appartiene al gruppo locale `Siemens TIA Openness`.
5. Nella VM e' installato `.NET 8 SDK` oppure almeno il runtime necessario.
6. La VM e' raggiungibile dalla macchina Linux che esegue Docker.

## Dove verificare le DLL Siemens

Il path standard impostato nel progetto e':

```text
C:\Program Files\Siemens\Automation\Portal V20\PublicAPI\V20
```

Il file piu' importante da verificare e':

```text
C:\Program Files\Siemens\Automation\Portal V20\PublicAPI\V20\Siemens.Engineering.dll
```

Se il tuo path e' diverso, dovrai modificarlo in `appsettings.Local.json`.

## Rete VMware consigliata

Per evitare problemi di raggiungibilita', la configurazione consigliata della VM e':

- preferibilmente `bridged`;
- IP statico o prenotato sulla rete;
- firewall Windows aperto sulla porta dell'agent.

Se usi `NAT`, devi assicurarti che:

- la VM sia davvero raggiungibile dal tuo host Linux;
- l'eventuale port forwarding sia corretto;
- l'URL configurato in `compose.dev.yml` punti davvero alla VM e non all'host sbagliato.

## Procedura completa passo-passo

### 1. Copia la cartella nella VM

Copia tutta la cartella `tia_windows_agent/` nella VM Windows, ad esempio in:

```text
C:\PLConversionTool\tia_windows_agent
```

Non copiare solo i file `.cs`: porta l'intera cartella cosi' hai anche script e template pronti.

### 2. Apri PowerShell nella cartella

Esempio:

```powershell
cd C:\PLConversionTool\tia_windows_agent
```

### 3. Crea il file locale di configurazione

Se non esiste ancora, crea:

```text
appsettings.Local.json
```

partendo da:

```text
appsettings.Local.template.json
```

Puoi farlo manualmente oppure lasciarlo creare allo script di bootstrap.

### 4. Configura i path locali reali

Apri `appsettings.Local.json` e verifica con attenzione questi campi:

- `TiaAgent:ListenUrl`
- `TiaAgent:ProjectRoot`
- `TiaAgent:OutputDirectory`
- `TiaAgent:TempDirectory`
- `TiaAgent:TiaPortalVersion`
- `TiaAgent:OpennessMode`
- `TiaAgent:SiemensAssemblyDirectory`
- `TiaAgent:DefaultProjectPath`
- `TiaAgent:LaunchUi`

Esempio realistico:

```json
{
  "TiaAgent": {
    "ListenUrl": "http://0.0.0.0:8050",
    "ProjectRoot": "C:\\PLConversionTool",
    "OutputDirectory": "C:\\PLConversionTool\\output",
    "TempDirectory": "C:\\PLConversionTool\\tmp",
    "TiaPortalVersion": "V20",
    "OpennessMode": "real",
    "SiemensAssemblyDirectory": "C:\\Program Files\\Siemens\\Automation\\Portal V20\\PublicAPI\\V20",
    "DefaultProjectPath": "C:\\PLConversionTool\\projects\\Demo.ap20",
    "LaunchUi": false,
    "AllowedOrigins": [
      "http://localhost:8010"
    ]
  }
}
```

### 5. Decidi `stub` o `real`

Usa:

- `stub` se vuoi testare solo l'avvio dell'agent senza toccare TIA;
- `real` se vuoi che l'agent provi a caricare `Siemens.Engineering.dll` e aprire una istanza `TiaPortal`.

Per il tuo caso reale, dopo aver verificato i path, la modalita' corretta e':

```json
"OpennessMode": "real"
```

### 6. Esegui il bootstrap

Da PowerShell:

```powershell
.\bootstrap-vm.ps1
```

Questo script:

- controlla che `dotnet` sia disponibile;
- crea `appsettings.Local.json` se manca;
- verifica il path standard di `Siemens.Engineering.dll`;
- crea la regola firewall sulla porta `8050`.

Se vuoi una porta diversa:

```powershell
.\bootstrap-vm.ps1 -Port 8060
```

### 7. Avvia l'agent

Comando consigliato:

```powershell
.\run-agent.ps1
```

Oppure:

```powershell
dotnet run --configuration Release
```

Oppure con doppio click:

```text
start-agent.cmd
```

### 8. Verifica locale nella VM

Apri il browser della VM oppure usa PowerShell.

Health:

```powershell
Invoke-RestMethod http://localhost:8050/health
```

Status:

```powershell
Invoke-RestMethod http://localhost:8050/api/status
```

Diagnostica Openness:

```powershell
Invoke-RestMethod http://localhost:8050/api/openness/diagnostics
```

### 9. Cosa aspettarti dalla diagnostica

Nel risultato di `GET /api/openness/diagnostics` devi controllare almeno:

- `SiemensAssemblyDirectoryExists = true`
- `SiemensEngineeringAssemblyExists = true`
- `DefaultProjectPathExists = true` se hai gia' configurato un progetto
- `Mode = real` se vuoi usare davvero Openness

Se questi valori sono `false`, l'agent parte ma non e' ancora pronto a lavorare davvero con TIA.

### 10. Verifica dalla macchina Linux

Dalla macchina che esegue Docker, devi riuscire a raggiungere la VM Windows.

Esempio se la VM ha IP `192.168.1.50`:

```bash
curl http://192.168.1.50:8050/health
curl http://192.168.1.50:8050/api/openness/diagnostics
```

Se qui non risponde, il problema non e' nel codice dell'agent ma nella connettivita' tra Linux e VM.

## Come collegarlo al compose Linux

Nel progetto Linux, il servizio `tia-bridge` usa queste variabili in [compose.dev.yml](/home/administrator/PLConversionTool/compose.dev.yml):

- `TIA_VMWARE_NETWORK_MODE`
- `TIA_WINDOWS_TRANSPORT`
- `TIA_WINDOWS_HOST`
- `TIA_WINDOWS_AGENT_PORT`
- `TIA_WINDOWS_AGENT_URL`

Esempio corretto quando la VM ha IP `192.168.1.50`:

```env
TIA_VMWARE_NETWORK_MODE=bridged
TIA_WINDOWS_TRANSPORT=http
TIA_WINDOWS_HOST=192.168.1.50
TIA_WINDOWS_AGENT_PORT=8050
TIA_WINDOWS_AGENT_URL=http://192.168.1.50:8050
```

Se lasci `host.docker.internal` ma TIA e' in una VM separata, quasi certamente punti al target sbagliato.

## Come usare gli endpoint job

### Import

Esempio:

```powershell
$body = @{
  operation = "import"
  artifactPath = "C:\PLConversionTool\output\FB_Graph.xml"
  projectPath = "C:\PLConversionTool\projects\Demo.ap20"
  notes = "test import"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8050/api/jobs/import `
  -ContentType "application/json" `
  -Body $body
```

### Compile

```powershell
$body = @{
  operation = "compile"
  artifactPath = "C:\PLConversionTool\tmp\compile-request.json"
  projectPath = "C:\PLConversionTool\projects\Demo.ap20"
  notes = "test compile"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8050/api/jobs/compile `
  -ContentType "application/json" `
  -Body $body
```

Nota:
in questa versione `artifactPath` e' ancora obbligatorio come campo di contratto, anche se per `compile` e' solo un placeholder tecnico.

### Export

```powershell
$body = @{
  operation = "export"
  artifactPath = "C:\PLConversionTool\output\export-target.xml"
  projectPath = "C:\PLConversionTool\projects\Demo.ap20"
  notes = "test export"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8050/api/jobs/export `
  -ContentType "application/json" `
  -Body $body
```

### Leggere i job

Lista:

```powershell
Invoke-RestMethod http://localhost:8050/api/jobs
```

Dettaglio:

```powershell
Invoke-RestMethod http://localhost:8050/api/jobs/job-xxxxxxxx
```

## Significato degli stati job

Gli stati che puoi vedere oggi sono:

- `queued`
- `running`
- `completed`
- `prepared`
- `blocked`
- `failed`

Interpretazione pratica:

- `completed`: il job e' passato in modalita' `stub`
- `prepared`: il probe Openness reale e' riuscito, ma la logica finale di import/export/compile non e' ancora stata completata
- `blocked`: manca qualcosa nell'ambiente Siemens
- `failed`: errore di path o eccezione runtime

## Differenza tra `appsettings.json` e `appsettings.Local.json`

Usa questa regola:

- `appsettings.json`: base versionata nel repository
- `appsettings.Local.json`: override della tua VM, non da committare

Modifica sempre prima `appsettings.Local.json`, non il file base, a meno che tu non voglia cambiare il comportamento standard per tutti.

## Come pubblicarlo in una cartella standalone

Se vuoi una cartella pronta da conservare nella VM senza dipendere dal progetto completo:

```powershell
.\publish-agent.ps1
```

Output previsto:

```text
.\publish
```

Poi puoi copiare il contenuto di `publish/` in una cartella dedicata della VM.

## Problemi comuni

### `Siemens.Engineering.dll` non trovata

Cause tipiche:

- TIA installato in un path diverso
- versione TIA diversa da `V20`
- path non aggiornato in `appsettings.Local.json`

### `/health` risponde ma `diagnostics` mostra valori `false`

Significa che l'agent parte, ma l'ambiente TIA non e' ancora pronto.

### la macchina Linux non raggiunge la VM

Controlla:

- modalita' rete VMware
- IP corretto della VM
- firewall Windows
- porta configurata

### il job va in `failed`

Controlla:

- `artifactPath`
- `projectPath`
- modalita' `real` o `stub`
- presenza reale di `Siemens.Engineering.dll`

## Sequenza minima consigliata per te

Se vuoi andare dritto, fai esattamente questo:

1. copia `tia_windows_agent/` nella VM
2. apri PowerShell nella cartella
3. esegui `.\bootstrap-vm.ps1`
4. apri `appsettings.Local.json`
5. imposta i path reali della tua VM
6. metti `"OpennessMode": "real"`
7. esegui `.\run-agent.ps1`
8. chiama `http://localhost:8050/api/openness/diagnostics`
9. quando la diagnostica e' tutta corretta, aggiorna il `compose.dev.yml` Linux con l'IP reale della VM
10. verifica dal Linux `curl http://IP_VM:8050/health`

## Prossimo step tecnico

Quando l'agent parte correttamente nella VM e la diagnostica e' pulita, il passo successivo e':

- completare le chiamate reali `open project / import / compile / export`.

Quello e' il punto in cui i dettagli finali devono essere adattati al comportamento reale della tua installazione TIA.
