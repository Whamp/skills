---
name: verify-skills
description: Verify this skills repository after manifest, reference, installer-discovery, or validation changes. Drive the real CLI checks in an isolated checkout and retain terminal evidence.
---

# Verify skills

This repository's primary surface is its installable skill collection and contributor CLI checks, not a running app. Read the [feature map](features/README.md), select the affected journeys and report their individual outcomes. Canonical skills live under `engineering/`, `productivity/` and `personal/`; project tooling is separate.

## Launch

Use Bash. First commit the candidate changes: this recipe verifies a revision, not uncommitted edits. Start from that candidate's checkout and retain these variables in the same shell session:

```bash
SOURCE_ROOT=$(git rev-parse --show-toplevel)
REVISION=$(git rev-parse HEAD)
RUN_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/verify-skills.XXXXXX")
EVIDENCE_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/verify-skills-evidence.XXXXXX")
git -C "$SOURCE_ROOT" worktree add --detach "$RUN_ROOT/checkout" "$REVISION"
cd "$RUN_ROOT/checkout"
printf 'revision=%s\ncheckout=%s\nevidence=%s\n' \
  "$REVISION" "$PWD" "$EVIDENCE_ROOT" | tee "$EVIDENCE_ROOT/run.txt"
```

Completion: the checkout's `HEAD` equals `REVISION` and the evidence path has been recorded. Each run has a separate worktree and scratch root; concurrent runs share only tool download caches. There is no server, port, login, seed data or database to initialize. `uvx` and `npx` may need network access on cold caches. Never run installation commands against real consumer directories for this proof.

## Doctor

Run this read-only check before driving, and repeat it if the environment looks wrong:

```bash
for tool in git make bash uv node npm npx; do
  command -v "$tool" || exit 1
done
test "$(git rev-parse HEAD)" = "$REVISION" || exit 1
git status --short
uv --version
node --version
npm --version
```

Completion: every command exists, the revision matches and the scratch checkout is clean. Stop and report a dirty or unexpected checkout rather than cleaning another run's files. Tool existence does not prove downloads or network access will work.

## Drive

Follow the selected feature's commands from the scratch checkout:

- [Contributor quality gate](features/quality-gate.md): the documented `make validate` path.
- [Published collection discovery](features/discovery.md): canonical-only staging and exact installer names.
- [Manifest and reference validation](features/portable-skill.md): valid and deliberately broken portable fixtures.
- [Safe cleanup boundaries](features/cleanup-safety.md): fixture-only disk-cleanup tests.

Completion: every selected entry point has an observed exit status and the expected observable result. An unmet precondition is a failure or an explicitly unverified path, not a reason to weaken its assertion.

## Evidence

Capture the command, stdout, stderr, revision and exit code under `EVIDENCE_ROOT`. For a command whose failure must be inspected rather than aborting cleanup, use this pattern:

```bash
printf '%s\n' 'make validate' > "$EVIDENCE_ROOT/quality-gate.command.txt"
status=0
make validate > "$EVIDENCE_ROOT/quality-gate.log" 2>&1 || status=$?
printf '%s\n' "$status" > "$EVIDENCE_ROOT/quality-gate.exit.txt"
```

Inspect the log with the file-reading tool, including the installer's listed names and the discovery runner's exact-name comparison. Observe scratch files and Git status where the journey expects side effects. Exercise actual validator/installer commands; mocks do not establish installer behavior. Listing can contact the package registry but must not install skills into a consumer surface.

Completion: report each feature ID, command, revision, outcome, limitations and absolute artifact paths. This skill supplies no helper scripts.

## Cleanup

Run after successful and failed attempts. Inspect scratch changes first; validation may leave ignored caches. Confirm the worktree belongs to this run with `git worktree list --porcelain`. If it has unexpected changes, report them and retain it for inspection. Otherwise:

```bash
cd "$SOURCE_ROOT"
git worktree remove "$RUN_ROOT/checkout"
# Remove only the scratch state created by this run, not its separate evidence.
case "$RUN_ROOT" in
  "${TMPDIR:-/tmp}"/verify-skills.*) rm -rf -- "$RUN_ROOT" ;;
  *) exit 1 ;;
esac
test -d "$EVIDENCE_ROOT" && test -s "$EVIDENCE_ROOT/run.txt"
```

Completion: this run's worktree is no longer registered, its scratch state is gone, and its evidence files remain readable. Never force-remove a worktree, remove backing dependencies or kill unrelated processes. Retain artifacts until their recipient has reviewed them.

For map maintenance as the repository changes, use `/skill:maintain-verification-skill` when that skill is installed in the active harness.
