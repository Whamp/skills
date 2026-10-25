# Safe cleanup boundaries

The disk-cleanup skill's fixture suite verifies approval and filesystem protections without performing live-machine cleanup.

## Sub-features

- `cleanup-read-only`: audit and planning stay read-only against fixtures.
- `cleanup-approval`: applying fixture cleanup requires exact approval.
- `cleanup-protected`: stale manifests, protected roots, symlinks and changed targets are rejected.

## How to get to it (user POV)

A maintainer runs `bash engineering/omarchy-free-disk-space/tests/run.sh`. The same suite is included in `make test` and therefore `make validate`.

## Driving it with Bash

Preconditions: parent launch and doctor completed. Read the suite before running it if its implementation changed, confirming it still uses temporary fixtures rather than live cleanup targets.

- **Exercise safety.** Capture `bash engineering/omarchy-free-disk-space/tests/run.sh`, including the exit code. Require exit 0 and `All fixture tests passed`; inspect the preceding named fixture groups rather than only that final line.
- **Check side effects.** Capture `git status --short` and require no source changes or unexpected artifacts. Review any changed cleanup logic against the fixture assertions before claiming it is protected.

## Gotchas

- This is a fixture-level safety proof, not an end-to-end Omarchy installation proof.
- Run only the test harness for this journey. Real cleanup application needs its own explicit targets and approvals; a verification task does not authorize deleting live caches, packages, models or containers.
- Tests and their fixtures are maintained by the canonical skill. Keep this map as the pointer, rather than duplicating its safety implementation.
