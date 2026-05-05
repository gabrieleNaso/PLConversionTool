# Cases (input / expected)

Cartella per **casi riproducibili**: AWL in input + output atteso.

Obiettivo:
- contesto stabile per discutere regole (diff chiaro)
- rigenerare `output/` e confrontare con `expected/`

## Struttura (lineare)

- `examples/cases/input/` (versionato)
  - un file per caso: `CASE__descrizione.awl` / `CASE__descrizione.md` / `CASE__descrizione.txt`
- `examples/cases/expected/` (versionato)
  - artefatti attesi, con stesso prefisso `CASE__...` (es. `CASE__...__ir.json`, `CASE__...__analysis.json`, `CASE__...__fb.xml`, ecc.)
Nota: `examples/` e' versionato (commitare `input/` + `expected/`).

## Rigenerazione

```bash
python3 scripts/generate_from_input.py \
  --input-dir examples/cases/input \
  --output-root work/output/generated
```

Poi confrontare i file generati con `examples/cases/expected/`.
