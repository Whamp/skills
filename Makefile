.PHONY: test validate

MARKDOWNLINT_VERSION := 0.23.2
RUFF_VERSION := 0.16.0
SKILLS_CLI_VERSION := 1.5.22
TY_VERSION := 0.0.69
PYTHON_PATHS := scripts tests engineering/herdr engineering/model-routing

test:
	uv run python -m unittest discover -s tests -v
	uv run python -m unittest discover -s engineering/model-routing/tests -v
	uvx ruff@$(RUFF_VERSION) check $(PYTHON_PATHS)
	uvx ruff@$(RUFF_VERSION) format --check $(PYTHON_PATHS)
	uvx ty@$(TY_VERSION) check $(PYTHON_PATHS)
	bash engineering/omarchy-free-disk-space/tests/run.sh

validate: test
	uv run python scripts/validate_skill_repository.py
	npx --yes markdownlint-cli2@$(MARKDOWNLINT_VERSION) '**/*.md'
	bash scripts/validate_skill_installer_discovery.sh $(SKILLS_CLI_VERSION)
