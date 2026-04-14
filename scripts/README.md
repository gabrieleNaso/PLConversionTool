# Scripts

Questa cartella e' riservata a script di progetto ripetibili.

Usarla per:
- import/export helper;
- validatori XML;
- normalizzatori naming;
- utility di confronto tra output generati e golden sample.

Se un comando viene eseguito piu' volte in modo manuale, dovrebbe diventare uno script qui o un target `make`.

## Generazione one-shot da cartella input

Per semplificare il flusso senza chiamate API manuali:

1. metti i sorgenti in `input/` (`.awl`, `.txt`, `.md`);
2. esegui:

```bash
make generate-input
```

Generazione di un solo file:

```bash
make generate-input INPUT_FILE="AWL romania.md"
```

Generazione per prefisso:

```bash
make generate-input INPUT_PREFIX="romania_"
```

Output:

- per ogni file valido viene creato un bundle in `output/generated/<nome_sequenza>/`;
- il bundle contiene `FB_*`, `DB_*`, `FC_*` e `<Sequence>_analysis.json`.

Note:

- nei file `.md` viene usato il primo blocco fenced che contiene `NETWORK`; se assente, viene usato il testo completo;
- i file senza `NETWORK` vengono saltati.
- per limitare le sorgenti usa `INPUT_FILE` (nome esatto) o `INPUT_PREFIX` (prefisso).

## Import automatico in TIA (batch)

Prerequisito: backend e bridge attivi (es. `make up`).

Esempio:

```bash
make import-generated PROJECT_PATH="C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20" TARGET_PATH="Program blocks/generati da tool"
```

Import di una sola cartella:

```bash
make import-generated PROJECT_PATH="C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20" TARGET_PATH="Program blocks/generati da tool/mio_test" IMPORT_BUNDLE="check_awl_romania"
```

Oppure in un colpo solo:

```bash
make generate-and-import PROJECT_PATH="C:\\Users\\Admin\\Desktop\\prova_connessione_openness\\prova_connessione_openness.ap20" TARGET_PATH="Program blocks/generati da tool"
```

Note:

- l'import viene fatto per ogni sottocartella in `output/generated/`;
- dopo ogni import, il `tia-bridge` accoda automaticamente la `compile` usando lo stesso `targetPath/targetName` dell'import (compile scoped sul target importato);
- se vuoi limitare a un sottoinsieme, usa `IMPORT_PREFIX` (prefisso) o `IMPORT_BUNDLE` (nome esatto cartella).
