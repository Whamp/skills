# Portable skill validation

A skill author receives a successful validation for a self-contained skill and an actionable failure for a broken reference.

## Sub-features

- `portable-valid`: a matching manifest name and reachable local reference pass.
- `portable-broken-link`: a missing reference fails with the offending path.

## How to get to it (user POV)

Run `uv run python scripts/validate_skill_repository.py <repository-root>` directly when checking a candidate collection. The normal repository path is also reached through `make validate`.

## Driving it with Bash

Preconditions: parent launch and doctor completed. Use the file-writing tool to create these two files under `RUN_ROOT/portable/example/`, using the actual scratch path:

- `SKILL.md`: YAML frontmatter bounded by `---`, with `name: example` and `description: Validate a portable fixture skill.` Its body has the H1 `Example` and an ordinary Markdown link with label `Reference` and target `reference.md`.
- `reference.md` containing `# Reference` and a final newline.

- **Accept valid input.** Capture `uv run python scripts/validate_skill_repository.py "$RUN_ROOT/portable"`. Require exit 0 and `Skill repository validation passed.` Retain copies of the fixture files in `EVIDENCE_ROOT/portable-valid/`.
- **Reject a broken link.** Use the editing tool to change `reference.md` to `missing.md` in the manifest's link target, leaving the reference file untouched. Capture the same validator command. Require exit 1 and a diagnostic naming `missing.md` as a missing local link target. The now-unreachable reference may produce an additional diagnostic. Retain the broken fixture and complete output under `EVIDENCE_ROOT/portable-broken/`.
- **Prove isolation.** Capture `git status --short`; these fixtures must exist only in scratch state and retained evidence, not in the canonical categories.

## Gotchas

- Expecting a nonzero status is part of the negative proof. Preserve that status before cleanup instead of allowing shell error handling to strand the worktree.
- Structural validation does not judge instruction quality, provenance or license compliance; those still require review.
- Keep both valid and broken inputs with their outputs so the failure can be reproduced after scratch cleanup.
