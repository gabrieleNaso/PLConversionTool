# AI Handoff Operativo: PLConversionTool Generator

Scopo: permettere a un'altra AI di continuare a lavorare sul generatore ed eseguire
tutti i comandi necessari senza chiedere altro contesto.

## 0. Prerequisiti minimi

- Sei nella repo: `pwd` deve essere `/home/administrator/PLConversionTool`.
- `docker compose` disponibile.
- Il backend risponde su `http://127.0.0.1:8000`.

## 1. Comandi base (ordine operativo)

### 1.1 Build/Restart backend

```bash
docker compose -f compose.dev.yml up -d --build backend
```

### 1.2 Creazione XML (da AWL a XML)

Gli XML vengono creati con `POST /api/conversion/export`.
Il backend genera sempre il pacchetto completo:
- FB GRAPH (`FB_<Nome>_GRAPH_auto.xml`)
- Global DB (`DB_<Nome>_global_auto.xml`)
- FC LAD (`FC_<Nome>_lad_auto.xml`)

Passi operativi:
1. Prepara `awlSource` (AWL completo con `NETWORK`).
2. Scegli `outputDir` (cartella di output).
3. Lancia l’export: gli XML verranno creati dentro `output/generated/<nome-bundle>/`.

### 1.3 Export bundle (da AWL a XML)

1. Prepara un payload JSON con AWL:

```bash
cat > /tmp/export_payload.json << 'JSON'
{
  "sequenceName": "Mega_Trial_Fix",
  "sourceName": "mega_trial_fix.awl",
  "awlSource": "NETWORK 1\n      U     S1\n      U     M10.0\n      S     S2\nNETWORK 2\n      U     S2\n      U     M11.0\n      S     S3",
  "outputDir": "output/generated/mega-trial-fix-jump-vX"
}
JSON
```

2. Lancia l’export:

```bash
curl -fsS -X POST -H "Content-Type: application/json" \
  --data @/tmp/export_payload.json \
  http://127.0.0.1:8000/api/conversion/export
```

Output atteso: file XML in `output/generated/<nome-bundle>/`.

### 1.4 Import bundle in TIA (via bridge)

```bash
curl -fsS -X POST -H "Content-Type: application/json" -d '{
  "artifactPath": "/workspace/output/generated/mega-trial-fix-jump-vX",
  "projectPath": "C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20",
  "targetPath": "Program blocks/generati da tool/mega-trial-fix-jump-vX",
  "targetName": null,
  "saveProject": true,
  "notes": "import mega-trial-fix-jump-vX"
}' http://127.0.0.1:8000/api/tia/jobs/import
```

Nota: l’import accoda automaticamente una `compile`.

### 1.5 Poll di un job TIA

```bash
curl -fsS http://127.0.0.1:8000/api/tia/jobs/JOB_ID
```

## 2. Regole operative essenziali (da non violare)

- **Numerazione step**: `Sxx` deve diventare `Step Number="xx"` (es. `S29` -> 29).
- **Ingressi multipli** su uno step non iniziale:
  - il primo ingresso puo' essere `Direct`;
  - gli ingressi extra devono essere `Jump`.
- **targetPath**: deve partire da `Program blocks/`.
  - Se ometti il prefisso, TIA crea un gruppo con nome letterale (es. `generati da tool/xxx`).

## 3. Dove mettere le mani nel codice

- Generatore (logica principale): `src/plc_converter/analysis.py`
- Backend API: `backend/app/main.py`
- Bridge client: `backend/app/tia_bridge_client.py`

## 4. Debug rapido (errore -> causa -> fix)

- Errore import: `A connection between "T6" and "Branch 1" cannot be created`
  - Causa: connessione `Transition -> Branch` non accettata.
  - Fix: usa `Jump` sugli ingressi multipli (no join con `SimEnd`).

- Crash TIA aprendo FB GRAPH:
  - Causa tipica: topologia invalida (doppi ingressi `Direct`).
  - Fix: converti gli ingressi extra in `Jump`.

## 5. Checklist operativa minima (da seguire sempre)

1. Modifica il generatore.
2. `docker compose ... --build backend`
3. Export bundle in cartella nuova.
4. Import in TIA con `targetPath` completo.
5. Apri la FB in TIA e verifica che non crashi.

## 6. File di documentazione da aggiornare quando cambi regole

- `Specifica_master_traduzione_AWL_e_generazione_XML_TIA_V20_V2_14_04.md`
- `report_del_14-04-2026.md`
- `tia_windows_agent/README.md`
- `tia_windows_agent/COMMANDS.md`
- `docs/tia-windows-agent-api.md`
