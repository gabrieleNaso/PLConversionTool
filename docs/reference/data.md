# Workspace folders

Cartelle principali del repo (separate fra **workspace del tool** e **materiale versionato**).

Struttura:
- `work/` (non versionato: solo struttura in git)
  - `work/input/`  sorgenti AWL da convertire (run locali)
  - `work/output/` artefatti generati dal tool
  - `work/tmp/`    staging e file temporanei
- `cases/` (versionato)
  - `cases/input/` + `cases/expected_output/` per casi riproducibili
- `datasets/` (versionato) campioni di riferimento (corpus, typicals, golden)
