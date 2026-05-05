# Cases (input -> expected_output)

Cartella per **casi riproducibili**: AWL in input + output atteso.

Obiettivo:
- contesto stabile per discutere regole (diff chiaro)
- rigenerare l'output del tool e confrontare con `expected_output/`

## Struttura (lineare)

Ogni file in `cases/input/` ha una cartella gemella in `cases/expected_output/`.

- `cases/input/<input_name>.(awl|md|txt)` (versionato)
- `cases/expected_output/<case_id>/` (versionato)
  - `ir.json`
  - `analysis.json`

Dove:
- `<case_id>` = versione "slug" di `<input_name>` (minuscolo, spazi/simboli -> `_`)

Nota: `cases/` e' versionato (commitare `input/` + `expected_output/`).

## Rigenerazione

```bash
python3 scripts/generate_from_input.py \
  --input-dir cases/input \
  --output-root work/output/generated
```

Poi confrontare almeno:
- `work/output/generated/<bundle>/<Name>_ir.json` vs `cases/expected_output/<case_id>/ir.json`
- `work/output/generated/<bundle>/<Name>_analysis.json` vs `cases/expected_output/<case_id>/analysis.json`

## Aggiornare un expected_output (consigliato)

Per creare/aggiornare automaticamente `expected_output` di un singolo input:

```bash
python3 scripts/update_case_expected.py --input "cases/input/<input_name>.md"
```

Per aggiornare tutti i casi (uno per file in `cases/input/`):

```bash
for f in cases/input/*; do python3 scripts/update_case_expected.py --input "$f"; done
```
