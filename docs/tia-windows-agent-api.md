# TIA Windows Agent API

API minima prevista per l'agent Windows che gira vicino a `TIA Portal`.

## Endpoint

- `GET /health`
  Ritorna lo stato base del servizio.
- `GET /api/status`
  Ritorna modalita', versione TIA e directory operative.
- `GET /api/openness/diagnostics`
  Ritorna lo stato della configurazione Siemens lato VM Windows.
- `POST /api/jobs/import`
  Accoda un job di import di un artefatto XML in TIA.
- `POST /api/jobs/compile`
  Accoda un job di compilazione del progetto/blocco target.
- `POST /api/jobs/export`
  Accoda un job di export dal progetto TIA.
- `GET /api/jobs`
  Elenca i job in memoria.
- `GET /api/jobs/{jobId}`
  Legge il dettaglio di un job.

## Payload base

```json
{
  "operation": "import",
  "artifactPath": "C:\\PLConversionTool\\output\\FB_Graph.xml",
  "projectPath": "C:\\PLConversionTool\\projects\\Demo.ap20",
  "targetPath": "Program blocks",
  "targetName": null,
  "saveProject": true,
  "notes": "import di validazione"
}
```

Per gli endpoint `import`, `compile` ed `export`, il campo `operation` viene normalizzato dal server in base alla route chiamata.

Campi aggiuntivi:

- `targetPath`: path logico del `BlockGroup` di destinazione per l'import
- `targetName`: nome del blocco da esportare
- `saveProject`: se `true`, prova a salvare il progetto dopo l'operazione
- per `compile`, `targetPath` e `targetName` possono essere usati per compilare solo un gruppo/blocco specifico invece dell'intero `PlcSoftware`

Nota operativa: `targetPath` va inteso come percorso che parte da `Program blocks/`.
Per creare una sottocartella ordinata usa ad esempio `Program blocks/generati da tool/<nome>`.

Nota bridge: quando il job passa da `tia-bridge`, dopo ogni `import` viene accodato automaticamente un job `compile` e la risposta dell'import espone anche `AutoCompileJobId`.

## Note

- l'agent processa i job in modo seriale, scelta prudente per il runtime TIA;
- in modalita' `real` prova a caricare `Siemens.Engineering.dll` via reflection e ad aprire una istanza `TiaPortal`;
- in modalita' `real` prova davvero ad aprire il progetto, compilare e invocare metodi `Import` / `Export` compatibili via reflection;
- se la firma API trovata nella tua installazione non coincide con una variante supportata, il job torna `blocked` con dettaglio diagnostico.
