# Cases (inputN -> expected_outputN)

Cartella per **casi riproducibili**: AWL in input + expected output curato a mano.

Obiettivo:
- contesto stabile per discutere regole (diff chiaro)
- confrontare l'output del tool con un expected (JSON o XML) messo nel repo

## Struttura (a coppie)

Ogni cartella `inputN/` corrisponde a una cartella `expected_outputN/` con lo stesso numero:

- `cases/input/input1/`  -> `cases/expected_output/expected_output1/`
- `cases/input/input2/`  -> `cases/expected_output/expected_output2/`
- ...

Nota: `cases/` e' versionato (commitare sia input che expected_output).

## Generare output dal tool (per confronto)

Esempio per `input1`:

```bash
python3 scripts/generate_from_input.py \
  --input-dir cases/input/input1 \
  --output-root work/output/generated \
  --name-prefix Case1
```

Poi confronta i JSON/XML generati nel bundle con quelli che hai messo in:
- `cases/expected_output/expected_output1/`

## Regola pratica

In `expected_outputN/` puoi mettere:
- JSON (`*_ir.json`, `*_analysis.json`) se vuoi fissare l'IR/diagnosi attesa
- e/o XML se vuoi fissare direttamente gli artefatti TIA attesi
