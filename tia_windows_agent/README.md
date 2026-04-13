# TIA Windows Agent

Servizio Windows compatibile con `.NET Framework 4.8` da eseguire nella VM dove sono installati `TIA Portal` e `TIA Portal Openness`.

## Scopo

Questo file contiene solo le istruzioni operative per installare, avviare, fermare e testare l'agent Windows.

Per lo stato complessivo del progetto e il punto tecnico raggiunto dall'integrazione con TIA, fare riferimento al [README generale](/home/administrator/PLConversionTool/README.md) e al [report consolidato](/home/administrator/PLConversionTool/report_del_09-04-2026%20(1).md).

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
- [COMMANDS.md](/home/administrator/PLConversionTool/tia_windows_agent/COMMANDS.md)

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
- richiama `stop-agent.ps1`;
- termina il processo agent e prova a chiudere anche eventuali processi figli ancora vivi;
- rimuove `bin/` e `obj/`;
- fa piu' tentativi di rimozione;
- riduce il caso tipico in cui Windows considera ancora la cartella "in uso".

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

## Workflow remoto Ubuntu -> Windows

Quando lavori tramite `tia-bridge`, il flusso remoto e' questo:

1. l'XML sta nella VM Ubuntu in una path visibile al container `tia-bridge`;
2. il `tia-bridge` legge il file o la cartella XML;
3. il `tia-bridge` carica gli XML nella directory temporanea della VM Windows tramite `POST /api/files/upload`;
4. il `tia-bridge` crea il job `import` verso l'agent Windows usando il path Windows appena creato;
5. l'agent Windows importa il contenuto in `TIA Portal`.

Stato operativo verificato:

- questo workflow remoto e' stato testato con successo;
- un file XML presente in `output/` sulla VM Ubuntu viene caricato nella `TempDirectory` Windows;
- il job remoto passa poi all'import reale in `TIA Portal`;
- non serve piu' copiare manualmente il file XML sulla VM Windows per l'import.

## Workflow remoto Windows -> Ubuntu

Quando lavori tramite `tia-bridge` per l'`export`, il flusso remoto e' questo:

1. la richiesta di `export` parte dalla VM Ubuntu con `artifactPath` Linux;
2. il `tia-bridge` prepara una path temporanea nella `TempDirectory` Windows;
3. l'agent Windows esegue `compile` automatica preliminare e poi l'`export` verso quella path temporanea;
4. il `tia-bridge` legge i file esportati dalla VM Windows;
5. il `tia-bridge` sincronizza il risultato nella path Linux richiesta sulla VM Ubuntu.

Stato operativo verificato:

- questo workflow remoto di `export` e' stato testato con successo;
- il file esportato compare sulla VM Ubuntu senza copia manuale dalla VM Windows;
- per l'`export` di un singolo blocco conviene usare `artifactPath` Linux con nome file `.xml` esplicito;
- per l'`export` di un gruppo intero conviene usare `artifactPath` Linux come directory.

Per il test remoto piu' semplice, usa file in:

- `/workspace/output`
- `/workspace/tmp`
- oppure path relative come `output/Type_28.xml` e `tmp/mia_cartella_xml`

Questi path sono gia' visibili al container `tia-bridge` nel `compose.dev.yml`.

## Come usare gli endpoint job

Campi del payload:

- `operation`
- `artifactPath`
- `projectPath`
- `targetPath`
- `targetName`
- `saveProject`
- `notes`

## Regole operative ed eccezioni dei comandi

Queste regole valgono per tutti i comandi `import`, `compile` ed `export`.

- `projectPath` e' obbligatorio per tutti i job reali.
- `artifactPath` e' sempre obbligatorio, anche per `compile`.
- `saveProject = $true` salva il progetto dopo l'operazione quando supportato.
- `targetPath = $null` indica il gruppo root dei `Program blocks`.
- `targetName` serve soprattutto per l'`export` di un singolo blocco.
- Se `artifactPath` e' un file `.xml`, il job lavora su un solo file.
- Se `artifactPath` e' una directory, `import` ed `export` lavorano su piu' file XML.

Eccezioni operative principali:

- `compile` non usa davvero il contenuto di `artifactPath`: quel campo resta un placeholder tecnico obbligatorio dal contratto.
- `compile` non si blocca per i `warning`; si blocca solo quando TIA restituisce errori reali.
- `export` esegue automaticamente una `compile` preliminare del `PlcSoftware`.
- quando il job passa tramite `tia-bridge`, anche `import` accoda automaticamente una `compile` post-import.
- Se la `compile` preliminare dell'`export` trova errori reali, l'`export` viene annullato.
- Per `import`, se `artifactPath` e' una directory, vengono importati tutti i `*.xml` trovati nella cartella e nelle sottocartelle, in ordine alfabetico.
- Per `export`, se `artifactPath` e' una directory, vengono esportati tutti i blocchi del gruppo selezionato e dei suoi sottogruppi.
- Per `export`, se `artifactPath` e' un file, devi indicare il blocco con `targetName` oppure usare un nome file coerente con il blocco da esportare.
- Per `export`, se `artifactPath` e' una directory ma `targetName` e' valorizzato, viene esportato un solo blocco dentro quella directory.
- Per `import`, se `targetPath` punta a un gruppo inesistente sotto `Program blocks`, l'agent prova a crearlo automaticamente prima dell'import.
- Se ometti il prefisso `Program blocks/`, TIA crea un gruppo con nome letterale (es. `generati da tool/xxx`).
- Per `compile` ed `export`, se `targetPath` punta a un gruppo inesistente, il job va in errore.
- Se `targetName` punta a un blocco inesistente, l'`export` va in errore.
- Se `artifactPath` di `import` non esiste come file o directory, il job va in errore.
- Se `artifactPath` di `export` e' una cartella, l'agent la crea se manca.
- Se `artifactPath` di `export` e' un file, l'agent crea automaticamente la directory padre se manca.

Convenzioni consigliate:

- usa `targetPath = $null` quando vuoi lavorare direttamente nel root `Program blocks`;
- usa `targetPath = "Program blocks/Group_1"` quando vuoi limitare import/export a un gruppo preciso;
- per creare una sottocartella ordinata (es. `generati da tool/<nome>`), passa sempre un path completo come `"Program blocks/generati da tool/<nome>"`;
- usa `saveProject = $true` per `import`;
- usa `saveProject = $true` per `compile` quando vuoi mantenere lo stato compilato;
- usa `saveProject = $false` per `export` se non hai bisogno di salvare altre modifiche.

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
Se `artifactPath` punta a una directory, l'agent importa tutti i file `*.xml` trovati nella cartella e nelle sottocartelle, in ordine alfabetico.
Se vuoi una cartella dentro `generati da tool`, usa sempre `"Program blocks/generati da tool/<nome>"` come `targetPath`.

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
Se TIA restituisce solo `warning`, il job viene considerato riuscito.

### Export

L'endpoint `export` esegue automaticamente una `compile` preliminare del `PlcSoftware` prima di tentare l'export. Se la compile trova errori reali, l'export viene annullato.

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

Se `artifactPath` punta a una directory invece che a un file:

- l'agent compila automaticamente il progetto;
- esporta tutti i blocchi del gruppo selezionato;
- crea piu' file XML nella cartella di output;
- mantiene la struttura dei sottogruppi come sottocartelle.

Eccezioni pratiche dell'`export`:

- con `artifactPath` file: esporta un solo blocco;
- con `artifactPath` cartella: esporta tutti i blocchi del gruppo selezionato;
- con `targetPath = $null`: parte dal root dei `Program blocks`;
- con `targetPath = "Program blocks/Group_1"`: esporta solo quel gruppo;
- con `targetName = $null` e `artifactPath` file: usa il nome file senza estensione come nome blocco da cercare;
- con `targetName` valorizzato: usa esplicitamente quel blocco;
- se il blocco o i tipi collegati sono inconsistenti, TIA puo' rifiutare l'export.

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

### Import reale da cartella

```powershell
$body = @{
  operation = "import"
  artifactPath = "C:\Users\Admin\Desktop\PLConverionTool\output"
  projectPath = "C:\Users\Admin\Desktop\prova_connessione_openness\prova_connessione_openness.ap20"
  targetPath = $null
  targetName = $null
  saveProject = $true
  notes = "bulk import test"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8050/api/jobs/import `
  -ContentType "application/json" `
  -Body $body
```

### Import reale da cartella esterna verso un gruppo specifico

```powershell
$body = @{
  operation = "import"
  artifactPath = "C:\Users\Admin\Desktop\mia_cartella_xml"
  projectPath = "C:\Users\Admin\Desktop\prova_connessione_openness\prova_connessione_openness.ap20"
  targetPath = "Program blocks/Group_1"
  targetName = $null
  saveProject = $true
  notes = "bulk import in Group_1"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8050/api/jobs/import `
  -ContentType "application/json" `
  -Body $body
```

### Import remoto passando per Ubuntu e `tia-bridge`

Se il file XML e' sulla VM Ubuntu in `output/Type_28.xml`, puoi usare il bridge Linux cosi':

```bash
curl -X POST http://192.167.1.20:8010/api/jobs/import \
  -H 'Content-Type: application/json' \
  -d '{
    "artifactPath": "output/Type_28.xml",
    "projectPath": "C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20",
    "targetPath": null,
    "targetName": null,
    "saveProject": true,
    "notes": "remote import from ubuntu"
  }'
```

Se invece vuoi importare una cartella Linux con piu' XML:

```bash
curl -X POST http://192.167.1.20:8010/api/jobs/import \
  -H 'Content-Type: application/json' \
  -d '{
    "artifactPath": "output/mia_cartella_xml",
    "projectPath": "C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20",
    "targetPath": "Program blocks/Group_1",
    "targetName": null,
    "saveProject": true,
    "notes": "remote bulk import from ubuntu"
  }'
```

Eccezioni pratiche del workflow remoto:

- il `tia-bridge` trasferisce automaticamente solo i file di `import`;
- perche' il bridge veda il file, il path deve essere accessibile dentro il container;
- il modo piu' semplice e' usare `output/...` o `tmp/...` del repository;
- dopo il trasferimento, il job gira sul path Windows temporaneo creato dall'agent.
- se il job remoto mostra ancora un `artifactPath` Linux nel dettaglio finale, il `tia-bridge` non sta usando la versione aggiornata.
- se il job remoto va in `completed`, in TIA conviene comunque fare refresh o riaprire il progetto per vedere subito il blocco importato.
- per l'`export`, la sync verso Ubuntu avviene quando il bridge legge il job completato tramite `/api/jobs` o `/api/jobs/{jobId}`.
- se l'`export` remoto finisce ma il file non compare su Ubuntu, controlla che il `tia-bridge` sia aggiornato e che tu abbia interrogato il job dopo il completamento.

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

Nota:
prima dell'export l'agent esegue automaticamente una `compile` del `PlcSoftware`. I `warning` non bloccano l'operazione; gli errori reali si'.

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

### Export reale in cartella

Per esportare piu' file XML in una directory di output:

```powershell
$body = @{
  operation = "export"
  artifactPath = "C:\Users\Admin\Desktop\PLConverionTool\output\bulk_export"
  projectPath = "C:\Users\Admin\Desktop\prova_connessione_openness\prova_connessione_openness.ap20"
  targetPath = $null
  targetName = $null
  saveProject = $false
  notes = "bulk export test"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8050/api/jobs/export `
  -ContentType "application/json" `
  -Body $body
```

Se vuoi limitare l'export a un gruppo specifico, imposta `targetPath`, per esempio:

```powershell
targetPath = "Program blocks/Sottogruppo1"
```

### Export reale di un solo gruppo

```powershell
$body = @{
  operation = "export"
  artifactPath = "C:\Users\Admin\Desktop\PLConverionTool\output\bulk_export"
  projectPath = "C:\Users\Admin\Desktop\prova_connessione_openness\prova_connessione_openness.ap20"
  targetPath = "Program blocks/Group_1"
  targetName = $null
  saveProject = $false
  notes = "export Group_1"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8050/api/jobs/export `
  -ContentType "application/json" `
  -Body $body
```

### Export remoto da Windows a Ubuntu di un solo blocco

Dalla VM Ubuntu:

```bash
curl -X POST http://192.167.1.20:8010/api/jobs/export \
  -H 'Content-Type: application/json' \
  -d '{
    "artifactPath": "output/remote_exports/Graph_StressTest_Impianto_v3.xml",
    "projectPath": "C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20",
    "targetPath": null,
    "targetName": "Graph_StressTest_Impianto_v3",
    "saveProject": false,
    "notes": "remote single export to ubuntu"
  }'
```

Poi leggi il job per attivare la sync verso Ubuntu:

```bash
curl http://192.167.1.20:8010/api/jobs
```

E controlla il file sulla VM Ubuntu:

```bash
ls -l /home/administrator/PLConversionTool/output/remote_exports/Graph_StressTest_Impianto_v3.xml
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
