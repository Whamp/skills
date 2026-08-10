.PHONY: test validate

MARKDOWNLINT_VERSION := 0.23.2
RUFF_VERSION := 0.16.0
SKILLS_CLI_VERSION := 1.5.22
TY_VERSION := 0.0.69

test:
	uv run python -m unittest discover -s tests -v
	uvx ruff@$(RUFF_VERSION) check scripts tests
	uvx ruff@$(RUFF_VERSION) format --check scripts tests
	uvx ty@$(TY_VERSION) check scripts tests

validate: test
	uv run python scripts/validate_skill_repository.py
	npx --yes markdownlint-cli2@$(MARKDOWNLINT_VERSION) '**/*.md'
	npx --yes skills@$(SKILLS_CLI_VERSION) add . --list
