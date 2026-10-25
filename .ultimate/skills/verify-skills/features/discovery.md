# Published collection discovery

An installer user lists the canonical collection and can find both model-invoked and user-only skills.

## Sub-features

- `discovery-canonical`: every canonical manifest directory is listed exactly once.
- `discovery-boundary`: local installation surfaces and project verification tooling are absent.

## How to get to it (user POV)

The root README documents `npx skills add Whamp/skills --full-depth --list`. Verify the candidate revision using the same pinned installer against a canonical-only local source; this avoids substituting the remote default branch for the changes under test.

## Driving it with Bash

Preconditions: parent launch and doctor completed; structural validation passes so manifest names match their directories. This is a local-source discovery proof, not a remote GitHub fetch or consumer installation proof.

- **Stage the published source.** Copy only category directories into this run's scratch state:

  ```bash
  mkdir "$RUN_ROOT/catalog"
  cp -R engineering productivity personal "$RUN_ROOT/catalog/"
  find "$RUN_ROOT/catalog" -name SKILL.md -type f -print |
    while IFS= read -r manifest; do basename "$(dirname "$manifest")"; done |
    LC_ALL=C sort > "$EVIDENCE_ROOT/discovery.expected.txt"
  ```

- **List through the installer.** Capture the following command and its exit status. Require exit 0 before comparing names:

  ```bash
  npx --yes skills@1.5.22 add "$RUN_ROOT/catalog" --full-depth --list \
    > "$EVIDENCE_ROOT/discovery.log" 2>&1
  ```

- **Assert the complete set.** Strip terminal escape codes from the pinned CLI's list output, extract its skill-name rows and compare against canonical directories:

  ```bash
  uv run python -c '
  import pathlib, re, sys
  raw = pathlib.Path(sys.argv[1]).read_text()
  plain = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", raw)
  names = re.findall(r"^│    ([a-z0-9][a-z0-9-]*)\s*$", plain, re.M)
  expected = pathlib.Path(sys.argv[2]).read_text().splitlines()
  pathlib.Path(sys.argv[3]).write_text("\n".join(sorted(names)) + "\n")
  missing = sorted(set(expected) - set(names))
  unexpected = sorted(set(names) - set(expected))
  print(f"missing={missing}; unexpected={unexpected}; listed={len(names)}")
  sys.exit(0 if expected and sorted(names) == expected else 1)
  ' "$EVIDENCE_ROOT/discovery.log" \
    "$EVIDENCE_ROOT/discovery.expected.txt" \
    "$EVIDENCE_ROOT/discovery.actual.txt"
  ```

  Capture the assertion output and exit code. Require no missing or unexpected names and no duplicates; the expected set is derived from this revision, not a fixed count. `lane` and `verify-skills` must not appear. Check `git status --short` to confirm no consumer lockfile or installation was created in the checkout.

## Gotchas

- Omitting `--full-depth` can stop at an installation-surface skill and suppress discovery of categories.
- Full-depth scanning of the entire development checkout also sees local tooling. Use canonical-only staging for the published-name assertion.
- `disable-model-invocation: true` does not mean undiscoverable. Include user-only skills in the expected set.
- The parser intentionally targets `skills@1.5.22` list formatting. A CLI upgrade must reverify the format; empty extraction fails rather than silently passing.
- `--list` still uses `npx`, which can contact the registry. This recipe proves listing without authorizing consumer installation or updates.
