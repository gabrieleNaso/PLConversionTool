# TIA Windows Agent

Servizio Windows compatibile con `.NET Framework 4.8` da eseguire nella VM dove sono installati `TIA Portal` e `TIA Portal Openness`.

## Scopo

Questo file contiene solo le istruzioni operative per installare, avviare, fermare e testare l'agent Windows.

Per lo stato complessivo del progetto e il punto tecnico raggiunto dall'integrazione con TIA, fare riferimento al [README generale](/home/administrator/PLConversionTool/README.md).

## Contenuto della cartella

File principali:

- `PLConversionTool.TiaAgent.csproj`
- `Program.cs`
- `appsettings.json`
- `appsettings.Local.template.json`

Script pronti:

- `bootstrap-vm.ps1`
- `run-agent.ps1`
- `stop-agent.ps1`
- `clean-agent.ps1`
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
5. Nella VM e' installato un ambiente di build compatibile con `net48`:
   `Visual Studio Build Tools`, `MSBuild` oppure `dotnet SDK` capace di compilare il progetto.
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
- `TiaAgent:AllowedOrigins`

Esempio realistico:

```json
{
  "TiaAgent": {
    "ListenUrl": "http://0.0.0.0:8050",
    "ProjectRoot": "C:\\Users\\Admin\\Desktop\\PLConverionTool",
    "OutputDirectory": "C:\\Users\\Admin\\Desktop\\PLConverionTool\\output",
    "TempDirectory": "C:\\Users\\Admin\\Desktop\\PLConverionTool\\tmp",
    "TiaPortalVersion": "V20",
    "OpennessMode": "real",
    "SiemensAssemblyDirectory": "C:\\Program Files\\Siemens\\Automation\\Portal V20\\PublicAPI\\V20",
    "DefaultProjectPath": "C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20",
    "LaunchUi": false,
    "AllowedOrigins": [
      "http://localhost:8010",
      "http://192.167.1.20:8010"
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

Per chiuderlo correttamente:

- se la console e' aperta, premi `Ctrl+C`
- se vuoi forzare lo stop del processo, usa:

```powershell
.\stop-agent.ps1
```

Per liberare anche la cartella e pulire i file di build:

```powershell
.\clean-agent.ps1
```

Questo script:

- sposta la shell fuori dalla cartella dell'agent;
- termina il processo se ancora presente;
- rimuove `bin/` e `obj/`;
- evita il caso tipico in cui Windows considera ancora la cartella "in uso".

Oppure:

```powershell
dotnet build -c Release
.\bin\Release\net48\PLConversionTool.TiaAgent.exe
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

Esempio corretto quando la VM Windows ha IP `192.167.1.41`:

```env
TIA_VMWARE_NETWORK_MODE=bridged
TIA_WINDOWS_TRANSPORT=http
TIA_WINDOWS_HOST=192.167.1.41
TIA_WINDOWS_AGENT_PORT=8050
TIA_WINDOWS_AGENT_URL=http://192.167.1.41:8050
```

Se lasci `host.docker.internal` ma TIA e' in una VM separata, quasi certamente punti al target sbagliato.

## Come usare gli endpoint job

Campi del payload:

- `operation`
- `artifactPath`
- `projectPath`
- `targetPath`
- `targetName`
- `saveProject`
- `notes`

### Import

Esempio:

```powershell
$body = @{
  operation = "import"
  artifactPath = "C:\Users\Admin\Desktop\PLConverionTool\output\Type_28.xml"
  projectPath = "C:\Users\Admin\Desktop\prova_connessione_openness\prova_connessione_openness.ap20"
  targetPath = $null
  targetName = $null
  saveProject = $true
  notes = "test import"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8050/api/jobs/import `
  -ContentType "application/json" `
  -Body $body
```

Nota:
per importare nel gruppo root dei blocchi, usa preferibilmente `targetPath = $null`. Se vuoi un sottogruppo specifico, passa un path come `"Program blocks/Sottogruppo1"`.

### Compile

```powershell
$body = @{
  operation = "compile"
  artifactPath = "C:\Users\Admin\Desktop\PLConverionTool\tmp\compile-request.json"
  projectPath = "C:\Users\Admin\Desktop\prova_connessione_openness\prova_connessione_openness.ap20"
  targetPath = $null
  targetName = $null
  saveProject = $false
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
  artifactPath = "C:\Users\Admin\Desktop\PLConverionTool\output\export-target.xml"
  projectPath = "C:\Users\Admin\Desktop\prova_connessione_openness\prova_connessione_openness.ap20"
  targetPath = $null
  targetName = "FB_Graph"
  saveProject = $false
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

## Comandi utili gia' usati nei test reali

Questi sono i comandi PowerShell usati nei test reali sulla VM Windows, mantenendo i path operativi gia' validati.

### Avvio pulito dell'agent

```powershell
cd C:\Users\Admin\Desktop\tia_windows_agent
.\clean-agent.ps1
dotnet build .\PLConversionTool.TiaAgent.csproj --configuration Release
.\run-agent.ps1
```

### Health e diagnostica

```powershell
Invoke-RestMethod http://localhost:8050/health
Invoke-RestMethod http://localhost:8050/api/status
Invoke-RestMethod http://localhost:8050/api/openness/diagnostics
```

### Import reale

```powershell
$body = @{
  operation = "import"
  artifactPath = "C:\Users\Admin\Desktop\PLConverionTool\output\Type_28.xml"
  projectPath = "C:\Users\Admin\Desktop\prova_connessione_openness\prova_connessione_openness.ap20"
  targetPath = $null
  targetName = $null
  saveProject = $true
  notes = "import test"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8050/api/jobs/import `
  -ContentType "application/json" `
  -Body $body
```

### Compile reale

```powershell
$body = @{
  operation = "compile"
  artifactPath = "C:\Users\Admin\Desktop\PLConverionTool\tmp\compile-request.json"
  projectPath = "C:\Users\Admin\Desktop\prova_connessione_openness\prova_connessione_openness.ap20"
  targetPath = $null
  targetName = $null
  saveProject = $true
  notes = "compile before export"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8050/api/jobs/compile `
  -ContentType "application/json" `
  -Body $body
```

### Export reale

Aggiorna solo `targetName` con il nome effettivo del blocco presente in TIA se diverso.

```powershell
$body = @{
  operation = "export"
  artifactPath = "C:\Users\Admin\Desktop\PLConverionTool\output\Type_28_export.xml"
  projectPath = "C:\Users\Admin\Desktop\prova_connessione_openness\prova_connessione_openness.ap20"
  targetPath = $null
  targetName = "Type_28"
  saveProject = $false
  notes = "export test"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8050/api/jobs/export `
  -ContentType "application/json" `
  -Body $body
```

### Lettura rapida dell'ultimo job

```powershell
(Invoke-RestMethod http://localhost:8050/api/jobs) | Select-Object -Last 1
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

- `completed`: il job e' terminato correttamente, sia in `stub` sia in esecuzione reale
- `prepared`: stato legacy di job vecchi, non dovrebbe piu' essere lo stato normale
- `blocked`: manca qualcosa nell'ambiente Siemens
- `failed`: errore di path o eccezione runtime

## Come leggere i job `blocked`

Se un job torna `blocked`, guarda il campo `detail`.

I casi tipici sono:

- ambiente Siemens non pronto;
- `Import` non trovato sulla composition selezionata;
- `Export` non trovato sul blocco selezionato;
- `TargetPath` errato;
- `TargetName` errato.

Quando possibile, il runtime include anche le firme pubbliche osservate, cosi' possiamo vedere subito come adattare l'implementazione alla tua installazione TIA reale.

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

## Nota operativa finale

Quando import, compile ed export funzionano, il punto successivo non e' piu' il setup dell'agent ma l'integrazione del workflow automatico del progetto con questi endpoint gia' validati.
