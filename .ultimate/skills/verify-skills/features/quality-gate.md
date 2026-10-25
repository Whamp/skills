# Contributor quality gate

A contributor runs the same repository checks locally that CI uses before accepting changes.

## Sub-features

- `quality-full`: tests, Python checks, manifest validation, Markdown lint and installer discovery run through `make validate`.
- `quality-tooling`: the project-local verification skill passes structural validation and scoped Markdown lint.

## How to get to it (user POV)

- Follow the root README's contributor instructions: `make validate`.
- Validate this project-local skill explicitly; hidden project tooling is outside canonical manifest discovery.

## Driving it with Bash

Preconditions: launch and doctor from the parent skill completed; `EVIDENCE_ROOT` is outside the checkout.

- **Full gate.** Run `make validate` using the parent's evidence-capture pattern. Require exit 0, then read the complete log. Record test and validator results, including the installer's listed names and the runner's successful exact-name comparison. Use the [discovery journey](discovery.md) to report that section's observations and limitations.
- **Tooling structure.** Capture `uv run python scripts/validate_skill_repository.py .ultimate/skills/verify-skills` and require exit 0 with `Skill repository validation passed.`
- **Tooling prose.** Capture `npx --yes markdownlint-cli2@0.23.2 '.ultimate/**/*.md'` and require exit 0 with no Markdown issues.
- **Side effects.** Capture `git status --short` after the commands. Require no tracked changes or unexpected artifacts; ignored interpreter caches and tool download caches do not represent skill installation.

## Gotchas

- Cold `uvx` and `npx` caches require downloads. A network failure is not a repository test failure; retain the command's error and report the blocked check.
- The Makefile is authoritative for pinned tool versions and the check sequence.
- Installer discovery asserts the current canonical name set against a temporary local source, not a remote fetch or consumer installation.
- `make validate` is not a promise to run every skill's own runtime test suite; invoke the affected skill's tests separately.
