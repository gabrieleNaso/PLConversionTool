.PHONY: help doctor build pull up logs shell-backend shell-frontend shell-tia run-backend run-tia test-backend lint-backend fmt-backend generate-input generate-excel-ir generate-excel generate-ir gen gen-ir import-generated generate-and-import generate-import expected-analysis expected-analysis-all clean down

PROJECT_NAME := plconversiontool
COMPOSE := docker compose -p $(PROJECT_NAME) -f compose.dev.yml
EXCEL_FILE ?= docs/templates/ir_excel_template_single_page_with_support_fc.xlsx
# Optional defaults for TIA import (env fallback kept working even when make vars are unset)
PROJECT_PATH ?= $(TIA_PROJECT_PATH)
TARGET_PATH ?= $(TIA_TARGET_PATH)
TARGET_PROFILE ?= $(PLC_TARGET_PROFILE)

help:
	@printf "%s\n" \
	"Targets:" \
	"  doctor  - checks docker + compose availability" \
	"  build   - build dev image" \
	"  pull    - pull base images (best effort)" \
	"  up      - start tia-bridge+backend+frontend (dev)" \
	"  logs    - follow logs" \
	"  shell-backend  - shell in backend container" \
	"  shell-frontend - shell in frontend container" \
	"  shell-tia      - shell in tia-bridge container" \
	"  run-backend    - run backend (reload)" \
	"  run-tia        - run tia-bridge (reload)" \
	"  test-backend   - run backend tests" \
	"  fmt-backend    - format backend (ruff)" \
	"  lint-backend   - lint backend (ruff)" \
	"  generate-input - generate XML (use INPUT_FILE/INPUT_PREFIX filters)" \
	"  generate-ir - generate XML from an IR JSON file (use IR_JSON/SEQUENCE_NAME)" \
	"  gen - alias of generate-input" \
	"  gen-ir - alias of generate-ir" \
	"  generate-excel-ir - generate XML from Excel IR template (use EXCEL_FILE)" \
	"  generate-excel - alias of generate-excel-ir" \
	"  import-generated - import bundles into TIA (use IMPORT_BUNDLE/IMPORT_PREFIX)" \
	"  generate-and-import - generate-input + import-generated" \
	"  generate-import - alias of generate-and-import" \
	"  expected-analysis - generate cases/expected_output/*/analysis.json (use EXPECTED_DIR)" \
	"  expected-analysis-all - generate analysis.json for all expected_outputN" \
	"  clean   - remove work/tmp/ and work/output/*" \
	"  down    - stop compose services"

doctor:
	@docker version >/dev/null
	@docker compose version >/dev/null
	@echo "OK: docker + docker compose disponibili."

pull:
	@$(COMPOSE) pull --ignore-pull-failures

build:
	@$(COMPOSE) build --pull

up:
	@$(COMPOSE) up -d --remove-orphans

logs:
	@$(COMPOSE) logs -f --tail=200

shell-backend:
	@$(COMPOSE) run --rm backend bash

shell-frontend:
	@$(COMPOSE) run --rm frontend bash

shell-tia:
	@$(COMPOSE) run --rm tia-bridge bash

run-backend:
	@$(COMPOSE) run --rm --service-ports backend bash -lc "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

run-tia:
	@$(COMPOSE) run --rm --service-ports tia-bridge bash -lc "uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload"

test-backend:
	@$(COMPOSE) run --rm backend bash -lc "pytest -q"

fmt-backend:
	@$(COMPOSE) run --rm backend bash -lc "ruff format ."

lint-backend:
	@$(COMPOSE) run --rm backend bash -lc "ruff check ."

generate-input:
	@python3 scripts/generate_from_input.py --input-dir work/input --output-root work/output/generated --name-prefix Auto --source "$(INPUT_FILE)" --prefix "$(INPUT_PREFIX)" \
	  $(if $(strip $(TARGET_PROFILE)),--target-profile "$(TARGET_PROFILE)",)

generate-ir:
	@python3 scripts/generate_from_ir_json.py --ir-json "$(IR_JSON)" --output-root work/output/generated --sequence-name "$(SEQUENCE_NAME)" \
	  $(if $(strip $(TARGET_PROFILE)),--target-profile "$(TARGET_PROFILE)",)

gen: generate-input

gen-ir: generate-ir

generate-excel-ir:
	@python3 scripts/generate_from_excel_ir.py --excel "$(EXCEL_FILE)" --output-root work/output/generated --sequence-name "$(SEQUENCE_NAME)"

generate-excel: generate-excel-ir

import-generated:
	@python3 scripts/import_generated_to_tia.py --output-root work/output/generated \
	  $(if $(strip $(PROJECT_PATH)),--project-path "$(PROJECT_PATH)",) \
	  $(if $(strip $(TARGET_PATH)),--target-path "$(TARGET_PATH)",) \
	  --prefix "$(IMPORT_PREFIX)" \
	  --bundle "$(IMPORT_BUNDLE)"

generate-and-import: generate-input import-generated

generate-import: generate-and-import

expected-analysis:
	@python3 scripts/expected_xml_to_analysis_json.py --expected-dir "$(EXPECTED_DIR)"

expected-analysis-all:
	@python3 scripts/expected_xml_to_analysis_json.py --all

clean:
	@mkdir -p ./work/tmp
	@rm -rf ./work/tmp/*
	@rm -rf ./work/output/*
	@echo "Pulito: work/tmp/* e work/output/*"

down:
	@$(COMPOSE) down --remove-orphans
