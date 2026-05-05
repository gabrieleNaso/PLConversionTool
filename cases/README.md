# Cases (input / expected_output)

Cartella per **casi riproducibili**: AWL in input + output atteso.

Obiettivo:
- contesto stabile per discutere regole (diff chiaro)
- rigenerare l'output del tool e confrontare con `expected_output/`

## Struttura (lineare)

- `cases/input/` (versionato)
  - un file per caso: `CASE__descrizione.awl` / `CASE__descrizione.md` / `CASE__descrizione.txt`
- `cases/expected_output/` (versionato)
  - artefatti attesi, con stesso prefisso `CASE__...` (es. `CASE__...__ir.json`, `CASE__...__analysis.json`, `CASE__...__fb.xml`, ecc.)
Nota: `cases/` e' versionato (commitare `input/` + `expected_output/`).

## Rigenerazione

```bash
python3 scripts/generate_from_input.py \
  --input-dir cases/input \
  --output-root work/output/generated
```

Poi confrontare i file generati con `cases/expected_output/`.
