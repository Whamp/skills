---
name: omarchy-free-disk-space
description: Safely audit and reclaim disk space on Omarchy and Arch Linux systems. Use when asked to free up disk space, clean an Omarchy computer, find what is using storage, audit disk usage, clean Arch package caches, or check Snapper disk usage.
disable-model-invocation: true
---

# Omarchy free disk space

Audit first, approve exact targets second, apply last. Treat free-space recovery as
forensics: allocated filesystem blocks, apparent file sizes, and snapshot-pinned
extents are different measurements.

## Run the correct branch

Set `SKILL_DIR` to this skill directory.

- **Audit (default):** run `"$SKILL_DIR/scripts/audit.sh" audit`. This branch is
  read-only and creates no manifest.
- **Quick cleanup request:** run
  `"$SKILL_DIR/scripts/plan.sh" quick`. It discovers low-risk candidates and
  writes a short-lived manifest.
- **Deep cleanup request:** run
  `"$SKILL_DIR/scripts/plan.sh" deep`. It adds developer artifacts, Git,
  Docker, downloads, kernels, application caches, and model stores.

Pass each additional workspace as
`--workspace-root "/absolute/path"` to `audit.sh` or `plan.sh`. Use only
reasonable roots on the same filesystem; never scan every mounted filesystem.

## Audit

Run the audit command and report its table plus:

- filesystem usage before;
- Omarchy version, channel, update workflow, and migration evidence;
- Btrfs mounts, allocation, Snapper configs, snapshot evidence, and timers;
- optional tools that were unavailable or permission-limited;
- categories intentionally left alone.

Call directory measurements **apparent size**. Call `df` and
`btrfs filesystem usage` results **allocated/available space**. Never call
`du` output snapshot-exclusive usage. If Snapper or Btrfs information needs
elevation, say that the audit is incomplete and provide the exact read-only
manual command instead of guessing.

An audit completes when every category in the table has a size or an explicit
`unknown`, a safety level, a mechanism, and a consequence. It makes no changes.

## Plan and approval gate

Read [references/cleanup-policy.md](references/cleanup-policy.md) before
presenting a cleanup plan. Render the plan’s exact item IDs in a concise table.
Explain that estimates do not add up to guaranteed free-space growth on Btrfs.

Ask for approval naming exact IDs or individually named items. End the
interaction at that question. Do not apply in the discovery turn. “Clean
everything” is not sufficient approval.

The manifest is NUL-delimited, mode `0600`, machine/boot-bound, and expires
after 15 minutes. Do not edit it, translate it into shell, or execute content
from it.

## Apply in a later turn

After explicit approval, run:

```bash
"$SKILL_DIR/scripts/apply.sh" \
  --manifest "/exact/manifest/path" \
  --approve "Q001" \
  --approve "Q004"
```

There is no blanket-approval option. `apply.sh` revalidates type, canonical
path, symlink components, device, mount, apparent size, and modification time.
It dispatches only hardcoded actions. A rejected or failed item does not widen
the remaining approval.

If a system action needs elevation, use the harness’s normal approval flow to
rerun the exact approved action. Otherwise show the exact manual command.
`omarchy update` is a separate maintenance operation and needs separate
approval.

After application, report:

- disk space before and after, with the measured change;
- each approved action and its result;
- failures and their reasons;
- data intentionally left alone;
- snapshot pinning that may delay visible Btrfs reclamation.

## Omarchy and recovery guardrails

- Use `omarchy update`, never a raw Arch upgrade, when updating the system.
- Prefer the installed Omarchy workflow and migrations over remote branch
  assumptions.
- Prefer Snapper cleanup. Keep snapshots, Docker volumes, kernels, model
  weights, datasets, databases, browser profiles, application state,
  repositories, worktrees, documents, media, and unfamiliar directories
  report-only by default.
- Present direct `btrfs subvolume delete` only as an exceptional repair when
  Snapper metadata and real subvolumes are demonstrably inconsistent. Require
  individual confirmation and explain lost rollback points.
- Inspect Git worktree cleanliness, untracked files, unique/unpushed commits,
  merge state, and registration before suggesting removal. Never force-delete
  a branch.
- Separate Docker containers, images, build cache, and volumes. Never combine
  volumes into a general prune.
- Prefer owning cleanup commands. For ordinary files, use `gio trash` when
  available; otherwise disclose permanent deletion and ask again.
