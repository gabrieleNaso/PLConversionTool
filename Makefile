.PHONY: help doctor build pull up logs shell-backend shell-frontend shell-tia run-backend run-tia test-backend lint-backend fmt-backend generate-input import-generated generate-and-import clean down

PROJECT_NAME := plconversiontool
COMPOSE := docker compose -p $(PROJECT_NAME) -f compose.dev.yml

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
	"  generate-input - generate XML from input/*.awl|*.txt|*.md" \
	"  import-generated - import output/generated bundles into TIA" \
	"  generate-and-import - generate-input + import-generated" \
	"  clean   - remove tmp/ and output/*" \
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
	@python3 scripts/generate_from_input.py --input-dir input --output-root output/generated --name-prefix Auto

import-generated:
	@python3 scripts/import_generated_to_tia.py --output-root output/generated --project-path "$(PROJECT_PATH)" --target-path "$(TARGET_PATH)"

generate-and-import: generate-input import-generated

clean:
	@rm -rf ./tmp/*
	@rm -rf ./output/*
	@echo "Pulito: tmp/* e output/*"

down:
	@$(COMPOSE) down --remove-orphans
