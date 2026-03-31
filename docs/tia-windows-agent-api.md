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
  "notes": "import di validazione"
}
```

Per gli endpoint `import`, `compile` ed `export`, il campo `operation` viene normalizzato dal server in base alla route chiamata.

## Note

- l'agent processa i job in modo seriale, scelta prudente per il runtime TIA;
- in modalita' `real` prova a caricare `Siemens.Engineering.dll` via reflection e ad aprire una istanza `TiaPortal`;
- l'implementazione reale di import/export/compile deve ancora essere completata con chiamate Openness specifiche del progetto.
