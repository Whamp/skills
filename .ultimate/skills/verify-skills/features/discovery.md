# Published collection discovery

An installer user lists the canonical collection and can find both model-invoked and user-only skills.

## Sub-features

- `discovery-canonical`: every canonical manifest directory is listed exactly once.
- `discovery-boundary`: local installation surfaces and project verification tooling are absent.

## How to get to it (user POV)

The root README documents `npx skills add Whamp/skills --full-depth --list`. Verify the candidate revision through `make validate`, which uses the pinned installer against a canonical-only local source rather than the remote default branch.

## Driving it with Bash

Preconditions: parent launch and doctor completed; structural validation passes so manifest names match their directories. This is a local-source discovery proof, not a remote GitHub fetch or consumer installation proof.

- **Run the real gate.** Capture `make validate` using the parent's evidence-capture pattern and require exit 0. If the quality-gate journey already captured this command at the same revision, reuse that evidence.
- **Inspect discovery evidence.** Read the installer section and final diagnostics from `scripts/validate_skill_installer_discovery.py`. Require a nonempty canonical catalog, a nonempty listing, empty missing/unexpected/duplicate lists and the success summary. Expected names come from the candidate's canonical manifest directories; the runner stages their content with category paths preserved, invokes `--full-depth --list`, and removes its temporary source. The CLI version comes from the Makefile.
- **Check boundaries.** Confirm the listed names include user-only canonical skills and exclude local tooling such as `lane` and `verify-skills`. Capture `git status --short` and require no consumer lockfile or installation created in the checkout. Record the temporary source path from the CLI output and confirm it no longer exists after the command.

## Gotchas

- Omitting `--full-depth` can stop at an installation-surface skill and suppress discovery of categories.
- Full-depth scanning of the entire development checkout also sees local tooling. The runner copies canonical skill content only, excluding hidden local tooling; copying the whole checkout is not equivalent.
- `disable-model-invocation: true` does not mean undiscoverable. The CLI filters `metadata.internal`, not user-only invocation policy; user-only canonical skills belong in the expected set.
- The runner strips ANSI escapes even when `NO_COLOR` is set and intentionally targets the pinned CLI's ungrouped name rows. A CLI upgrade must reverify the format; empty extraction fails rather than silently passing.
- `--list` still uses `npx`, which can contact the registry. This recipe proves listing without authorizing consumer installation or updates.
