# Scripts

Questa cartella contiene script di progetto ripetibili.
Per il workflow operativo completo vedi `../docs/guide/operations/operations.md`.

Script principali:
- `generate_from_input.py`
  - genera un bundle in `data/output/generated/<bundle>/` a partire dai sorgenti in `data/input/`.
  - nei `.md` estrae i blocchi fenced AWL/STL.
  - scrive sempre `<Name>_ir.json` e `<Name>_analysis.json` (diagnosi primaria).
  - per estrarre regole e fare regressione, confrontare l'output con le traduzioni gia' presenti in `data/datasets/corpus/traduzione/` quando disponibili.
- `generate_from_excel_ir.py`
- `import_generated_to_tia.py`
  - importa solo file `*.xml` del bundle (i `.json` non vengono inviati a TIA).
