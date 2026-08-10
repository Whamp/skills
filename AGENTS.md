# Agent Skills Repository

This repository is the canonical public source for Will-authored agent skills. Consumer directories such as `~/.agents/skills/` are installation surfaces, not source trees. Make durable skill changes here, merge them, then update consumer installations through their skill installer.

## Repository Navigation

- Engineering skills: `engineering/<skill-name>/`
- Productivity skills: `productivity/<skill-name>/`
- Personal skills: `personal/<skill-name>/`
- Repository validator: `scripts/validate_skill_repository.py`
- Validator tests: `tests/test_validate_skill_repository.py`
- CI entry point: `make validate`

Each skill starts at `SKILL.md`. Keep branch-specific instructions, examples, scripts, and assets inside that skill's directory. A skill must remain usable when installed without the rest of this repository.

## Domain Vocabulary

Use these terms consistently in filenames, documentation, and maintenance work:

| Canonical term | Meaning | Avoid |
| --- | --- | --- |
| canonical source | The reviewed skill directory in this repository | master copy, repo copy |
| installation surface | A consumer-managed copy or link created from the canonical source | source skill |
| category | An organizational directory containing independent skills | package, namespace |
| invocation policy | Whether a harness may invoke a skill autonomously or only after a user request | visibility |
| provenance | The authorship, upstream origin, and license basis for publishing a skill | inspiration |

## Publishing Rules

- Publish work Will authored or has the right to redistribute. Record material third-party origins and license terms inside the affected skill.
- Keep skills portable. Replace personal paths, private infrastructure, secrets, and machine-specific assumptions with documented inputs or explicit compatibility requirements.
- Keep a skill self-contained. Local links from its Markdown files must resolve inside its directory unless they deliberately point to a stable public source.
- Use the folder name as the frontmatter `name`. Skill names are unique across categories.
- Keep the repository root free of `SKILL.md`; nested manifests let installers discover every independent skill.
- Keep consumer lockfiles, installation links, and machine-specific policy overlays in the consumer's configuration repository.

## Editing Skills

Read the `writing-for-agents` guidance before changing a skill or its invocation policy. Preserve one source of truth for each instruction, disclose branch-specific material behind links from `SKILL.md`, and give ordered work checkable completion criteria.

A model-invoked skill keeps a trigger-focused `description` and omits `disable-model-invocation`. A user-only skill sets `disable-model-invocation: true` and uses its description as a concise human-facing summary. Harness-specific policy overlays may intentionally narrow that public default at installation time.

When adding or migrating a skill:

1. Establish its provenance and license basis.
2. Place the complete skill directory under the best existing category.
3. Update the root catalog and that category's README.
4. Run `make validate`.
5. After merge, update consumer installations through their installer and update the consumer's ownership inventory.

Migration is complete when the canonical source is merged, repository validation passes, the consumer reports this repository as its update source, and no divergent hand-maintained installation remains.

## Expected Absences

- A root `SKILL.md` is intentionally absent because each nested skill is independently installable.
- A repository-level skills lock is intentionally absent because consumers own installation state.
- Machine-specific invocation overlays are intentionally absent because they belong to consumer configuration.
- Release artifacts and per-skill packages are intentionally absent; Git history and consumer lock metadata identify installed revisions.
