# TIA Windows Agent Commands

Raccolta operativa dei comandi usati per lavorare con l'agent Windows e con il `tia-bridge`.

Questo file non sostituisce [agent.md](/home/administrator/PLConversionTool/tia_windows_agent/agent.md): serve come reference rapida, pronta da copiare e incollare.

## Convenzioni usate qui

- VM Ubuntu/Linux: `192.167.1.20`
- VM Windows/TIA: `192.167.1.41`
- agent Windows: `http://192.167.1.41:8050`
- tia-bridge Linux: `http://192.167.1.20:8010`
- progetto TIA:
  `C:\Users\Admin\Desktop\prova_connessione_openness\prova_connessione_openness.ap20`
- root output Windows:
  `C:\Users\Admin\Desktop\PLConverionTool\output`
- root tmp Windows:
  `C:\Users\Admin\Desktop\PLConverionTool\tmp`
- root repo Ubuntu:
  `/home/administrator/PLConversionTool`

## Regola operativa fondamentale

- `FB GRAPH`, `GlobalDB`, `FC LAD` e ogni eventuale blocco aggiuntivo vanno trattati come un pacchetto coerente.
- Se cambi il serializer, il naming dei member, le transition guard, la topologia GRAPH o il contratto dati, non e' sicuro reimportare solo il `FB`.
- In questi casi va riallineato l'intero pacchetto del caso (`FB + DB + FC`, e gli altri blocchi richiesti).
- Un `FB` importato sopra un `GlobalDB` o una `FC` non aggiornati puo' restare importabile ma diventare incoerente in compile e, nei casi peggiori, destabilizzare l'apertura del GRAPH in TIA.

## 1. Avvio agent Windows

### Pulizia e build completa

Usalo quando hai aggiornato il codice dell'agent e vuoi ripartire pulito.

```powershell
cd C:\Users\Admin\Desktop\tia_windows_agent
.\clean-agent.ps1
dotnet build .\PLConversionTool.TiaAgent.csproj --configuration Release
```

### Avvio standard

Avvia l'agent con la configurazione locale gia' presente in `appsettings.Local.json`.

```powershell
cd C:\Users\Admin\Desktop\tia_windows_agent
.\run-agent.ps1
```

### Stop standard

Ferma il processo dell'agent.

```powershell
cd C:\Users\Admin\Desktop\tia_windows_agent
.\stop-agent.ps1
```

### Pulizia completa

Ferma l'agent, prova a chiudere eventuali processi figli e pulisce `bin/` e `obj/`.

```powershell
cd C:\Users\Admin\Desktop\tia_windows_agent
.\clean-agent.ps1
```

## 2. Diagnostica agent Windows

### Health

Verifica che il processo HTTP dell'agent sia in ascolto.

```powershell
Invoke-RestMethod http://localhost:8050/health
```

### Status

Mostra modalita', cartelle operative e operazioni supportate.

```powershell
Invoke-RestMethod http://localhost:8050/api/status
```

### Diagnostica Openness

Verifica presenza DLL Siemens, modalita' `real/stub` e progetto di default.

```powershell
Invoke-RestMethod http://localhost:8050/api/openness/diagnostics
```

### Tutti i job

Mostra la cronologia dei job dell'agent.

```powershell
Invoke-RestMethod http://localhost:8050/api/jobs
```

### Ultimo job

Comando rapido per leggere l'ultimo job.

```powershell
(Invoke-RestMethod http://localhost:8050/api/jobs) | Select-Object -Last 1
```

## 3. Test di rete tra VM

### Dalla VM Ubuntu verso l'agent Windows

Verifica connettivita' Linux -> Windows.

```bash
curl http://192.167.1.41:8050/health
curl http://192.167.1.41:8050/api/status
curl http://192.167.1.41:8050/api/openness/diagnostics
```

### Dalla VM Ubuntu verso il tia-bridge

Verifica connettivita' Linux locale verso il boundary service.

```bash
curl http://192.167.1.20:8010/health
curl http://192.167.1.20:8010/api/status
```

## 4. Comandi Docker lato Ubuntu

### Ricostruire tia-bridge e backend

Usalo dopo modifiche al bridge o al backend.

```bash
cd /home/administrator/PLConversionTool
docker compose -f compose.dev.yml up -d --build tia-bridge backend
```

### Stato container

```bash
cd /home/administrator/PLConversionTool
docker compose -f compose.dev.yml ps
```

### Log del tia-bridge

```bash
cd /home/administrator/PLConversionTool
docker compose -f compose.dev.yml logs --tail=200 tia-bridge
```

### Verifica che il tia-bridge veda un file Linux

Utile prima di un import remoto da Ubuntu.

```bash
cd /home/administrator/PLConversionTool
docker compose -f compose.dev.yml exec tia-bridge ls -l /workspace/data/output/Graph_StressTest_Impianto_v3.xml
```

## 5. Import locale direttamente da Windows

### Import di un file XML

Importa un singolo file XML gia' presente sulla VM Windows.

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

### Import di una cartella XML

Importa tutti i `*.xml` presenti in una cartella Windows.

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

### Import in un gruppo specifico

Importa nel gruppo `Program blocks/Group_1`.
Se `Group_1` non esiste ancora sotto `Program blocks`, l'agent prova a crearlo automaticamente durante l'import.

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

## 6. Compile locale direttamente da Windows

### Compile del progetto

`artifactPath` qui e' solo un placeholder tecnico richiesto dal contratto.

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

Nota:
- i warning non bloccano il compile
- gli errori reali lo bloccano

## 7. Export locale direttamente da Windows

### Export di un solo blocco

Esporta il blocco `Type_28` in un file XML.

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

### Export di un gruppo intero

Esporta tutti i blocchi del gruppo `Group_1` in una directory Windows.

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

### Export di un solo blocco verso una cartella

Se `artifactPath` e' una directory ma `targetName` e' valorizzato, l'agent esporta solo quel blocco dentro quella cartella.

```powershell
$body = @{
  operation = "export"
  artifactPath = "C:\Users\Admin\Desktop\PLConverionTool\output\single_export_dir"
  projectPath = "C:\Users\Admin\Desktop\prova_connessione_openness\prova_connessione_openness.ap20"
  targetPath = $null
  targetName = "Graph_StressTest_Impianto_v3"
  saveProject = $false
  notes = "single export into directory"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8050/api/jobs/export `
  -ContentType "application/json" `
  -Body $body
```

## 8. Import remoto Ubuntu -> Windows -> TIA

### Import remoto di un file XML Linux

Il file parte dalla VM Ubuntu, il `tia-bridge` lo copia su Windows e poi l'agent lo importa in TIA.

```bash
curl -X POST http://192.167.1.20:8010/api/jobs/import \
  -H 'Content-Type: application/json' \
  -d '{
    "artifactPath": "data/output/Graph_StressTest_Impianto_v3.xml",
    "projectPath": "C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20",
    "targetPath": null,
    "targetName": null,
    "saveProject": true,
    "notes": "remote import from ubuntu"
  }'
```

### Import remoto di una cartella Linux verso `Group_1`

Se `Group_1` non esiste ancora sotto `Program blocks`, l'agent prova a crearlo automaticamente durante l'import.

```bash
curl -X POST http://192.167.1.20:8010/api/jobs/import \
  -H 'Content-Type: application/json' \
  -d '{
    "artifactPath": "data/output/mia_cartella_xml",
    "projectPath": "C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20",
    "targetPath": "Program blocks/Group_1",
    "targetName": null,
    "saveProject": true,
    "notes": "remote bulk import from ubuntu"
  }'
```

## 9. Export remoto Windows -> Ubuntu

### Export remoto di un solo blocco verso Ubuntu

Il blocco viene esportato su Windows in una path temporanea e poi sincronizzato sulla VM Ubuntu.

```bash
curl -X POST http://192.167.1.20:8010/api/jobs/export \
  -H 'Content-Type: application/json' \
  -d '{
    "artifactPath": "data/output/remote_exports/Graph_StressTest_Impianto_v3.xml",
    "projectPath": "C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20",
    "targetPath": null,
    "targetName": "Graph_StressTest_Impianto_v3",
    "saveProject": false,
    "notes": "remote single export to ubuntu"
  }'
```

Poi leggi il job per attivare la sync:

```bash
curl http://192.167.1.20:8010/api/jobs
```

Infine verifica il file sulla VM Ubuntu:

```bash
ls -l /home/administrator/PLConversionTool/data/output/remote_exports/Graph_StressTest_Impianto_v3.xml
```

### Export remoto di un gruppo intero verso Ubuntu

Esporta tutti i blocchi del gruppo `Group_1` nella directory Linux `data/output/remote_exports/Group_1`.

```bash
curl -X POST http://192.167.1.20:8010/api/jobs/export \
  -H 'Content-Type: application/json' \
  -d '{
    "artifactPath": "data/output/remote_exports/Group_1",
    "projectPath": "C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20",
    "targetPath": "Program blocks/Group_1",
    "targetName": null,
    "saveProject": false,
    "notes": "remote export Group_1 to ubuntu"
  }'
```

Poi:

```bash
curl http://192.167.1.20:8010/api/jobs
ls -R /home/administrator/PLConversionTool/data/output/remote_exports/Group_1
```

## 10. Workflow completo da Ubuntu/Linux

Questa sezione raccoglie i comandi operativi principali da usare direttamente dalla VM Ubuntu.

### Import remoto di un FB generato dal tool

```bash
curl -X POST http://192.167.1.20:8010/api/jobs/import \
  -H 'Content-Type: application/json' \
  -d '{
    "artifactPath": "data/output/generated/import-trial-linked/FB_Import_Trial_Linked_GRAPH_auto.xml",
    "projectPath": "C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20",
    "targetPath": "Program blocks/generati da tool",
    "targetName": null,
    "saveProject": true,
    "notes": "ubuntu import generated graph"
  }'
```

### Import remoto di un pacchetto completo generato dal tool

Importa tutti gli XML presenti in una cartella Linux.
Nota: il `targetPath` parte sempre da `Program blocks/`. Se vuoi creare una sottocartella
ordinata sotto `generati da tool`, usa un path completo tipo
`Program blocks/generati da tool/<nome>`.

```bash
curl -X POST http://192.167.1.20:8010/api/jobs/import \
  -H 'Content-Type: application/json' \
  -d '{
    "artifactPath": "data/output/generated/complex-trial-fix",
    "projectPath": "C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20",
    "targetPath": "Program blocks/generati da tool/complex-trial-fix",
    "targetName": null,
    "saveProject": true,
    "notes": "ubuntu import full generated package"
  }'
```

### Compile remota da Ubuntu via tia-bridge

Per `compile`, `artifactPath` resta un placeholder tecnico obbligatorio.

```bash
curl -X POST http://192.167.1.20:8010/api/jobs/compile \
  -H 'Content-Type: application/json' \
  -d '{
    "artifactPath": "data/output/generated/compile-request.json",
    "projectPath": "C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20",
    "targetPath": "Program blocks/generati da tool",
    "targetName": null,
    "saveProject": true,
    "notes": "ubuntu compile generated folder"
  }'
```

### Export remoto di un blocco verso Ubuntu

```bash
curl -X POST http://192.167.1.20:8010/api/jobs/export \
  -H 'Content-Type: application/json' \
  -d '{
    "artifactPath": "data/output/remote_exports/Complex_Trial_Fix_GRAPH.xml",
    "projectPath": "C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20",
    "targetPath": "Program blocks/generati da tool/complex-trial-fix",
    "targetName": "Complex_Trial_Fix",
    "saveProject": false,
    "notes": "ubuntu export generated graph"
  }'
```

### Export remoto di un gruppo verso Ubuntu

```bash
curl -X POST http://192.167.1.20:8010/api/jobs/export \
  -H 'Content-Type: application/json' \
  -d '{
    "artifactPath": "data/output/remote_exports/complex-trial-fix",
    "projectPath": "C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20",
    "targetPath": "Program blocks/generati da tool/complex-trial-fix",
    "targetName": null,
    "saveProject": false,
    "notes": "ubuntu export generated folder"
  }'
```

### Polling rapido di un job da Ubuntu

Sostituisci `JOB_ID` con l'id reale restituito dal bridge.

```bash
curl http://192.167.1.20:8010/api/jobs/JOB_ID
```

### Polling continuo fino a chiusura

```bash
for i in $(seq 1 10); do
  date
  curl -fsS http://192.167.1.20:8010/api/jobs/JOB_ID
  echo
  sleep 15
done
```

### Verifica file esportati su Ubuntu

```bash
ls -l /home/administrator/PLConversionTool/data/output/remote_exports
find /home/administrator/PLConversionTool/data/output/remote_exports -maxdepth 3 -type f | sort
```

### Chiamata diretta dalla VM Ubuntu all'agent Windows

Utile per debug quando vuoi bypassare temporaneamente il `tia-bridge`.

```bash
curl -X POST http://192.167.1.41:8050/api/jobs/compile \
  -H 'Content-Type: application/json' \
  -d '{
    "operation": "compile",
    "artifactPath": "C:\\Users\\Admin\\Desktop\\PLConverionTool\\tmp\\compile-request.json",
    "projectPath": "C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20",
    "targetPath": "Program blocks/generati da tool",
    "targetName": null,
    "saveProject": true,
    "notes": "ubuntu direct compile to windows agent"
  }'
```

## 11. Lettura job dal bridge Linux

### Tutti i job

```bash
curl http://192.167.1.20:8010/api/jobs
```

### Singolo job

```bash
curl http://192.167.1.20:8010/api/jobs/JOB_ID
```

## 12. Regole pratiche da ricordare

- `targetPath = null` significa root dei `Program blocks`
- quando vuoi creare sottocartelle dedicate, usa sempre `Program blocks/<cartella>` come prefisso
- `targetName = null` + `artifactPath` directory in `export` significa export multiplo del gruppo
- `targetName` valorizzato + `artifactPath` directory in `export` significa export di un solo blocco dentro quella directory
- `saveProject = true` e' consigliato per `import`
- `compile` viene eseguito automaticamente prima di ogni `export`
- per l'`export` remoto verso Ubuntu, la sync avviene quando il bridge legge il job completato
- se un job remoto mostra ancora un `artifactPath` Linux lato Windows, il `tia-bridge` non e' aggiornato
