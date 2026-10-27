---
name: omarchy-free-disk-space
description: Audit Omarchy storage and prepare evidence-backed, individually approved cleanup decisions.
disable-model-invocation: true
---

# Omarchy free disk space

Recover useful headroom, not a cosmetically clean directory tree. Inventory,
recommend, approve, apply, then measure. A cleanup request authorizes discovery;
it does not authorize deletion.

## 1. Inventory

Set `SKILL_DIR` to this directory. Run `"$SKILL_DIR/scripts/audit.sh" audit`.
The default branch is read-only and creates no manifest. Add each bounded
workspace with `--workspace-root "/absolute/path"`; report excluded roots.

Identify the pressured filesystem, root/home mount layout, installed Omarchy
workflow, snapshot policy, and permission gaps. Distinguish apparent file sizes,
owner-reported bytes, and filesystem available space. The script's name-matched
project artifacts are investigation leads, not proof of obsolete development.

**Complete when:** every discovered category has evidence or an explicit unknown,
and the largest candidates on the pressured filesystem are identified.

## 2. Resolve the useful candidates

Read [cleanup-policy.md](references/cleanup-policy.md) for classification and
supported actions. For Btrfs, shared storage, sparse files, or a gap between file
sizes and available space, read
[space-accounting.md](references/space-accounting.md). Inspect selected paths with:

```bash
"$SKILL_DIR/scripts/measure.sh" "/exact/candidate/path"
```

Establish project ownership, reproducibility, runtime use, and rebuild cost.
For worktrees, inspect dirty/untracked files, Git operations, commit recovery,
merge/task status, registration, and live users. Age alone proves none of these.
Investigate a large uncertain item instead of repeatedly clearing tiny caches.

**Complete when:** each leading candidate is recommended, optional, keep, or
investigate, with the evidence and removal consequence stated.

## 3. Prepare a decision report

Generate a fresh plan: `"$SKILL_DIR/scripts/plan.sh" quick` for bounded caches,
or `deep` to include development, Docker, downloads, and recovery-related items.
Recheck the evidence against its exact IDs. Audit IDs start with `A` and cannot
be applied; plan IDs start with `Q` or `D`.

Lead with the top recommendations, then separate optional, preserved, and
unresolved items. Use the policy's decision table. Rank by likely benefit on the
pressured filesystem, evidence, and regeneration cost; label file-size rankings
as such. Candidate totals overlap and are not additive physical savings.

Moving to Trash normally releases **zero** space. Emptying Trash is a separate,
permanent decision, including any files already there.

Ask for exact IDs or individually named items, then end the turn. Apply only in
a later turn. General permission to clean everything is not item approval.

## 4. Apply and verify

After approval, revalidate project/Git/runtime evidence yourself; the executor
checks filesystem identity and allowlisted actions, not project inactivity.

```bash
"$SKILL_DIR/scripts/apply.sh" \
  --manifest "/exact/manifest/path" \
  --approve "D004"
```

Manifests expire after 15 minutes. Leave their binary contents unchanged. Add
`--space-path "/actual/tool/storage"` for a tool-owned store on another mount.
A rejected item does not widen approval. Use the normal elevation approval flow
for the exact approved system action, or show its manual command.

Report each approved ID as removed, moved to Trash, skipped, or failed. Show
available-space changes per affected filesystem, without attributing concurrent
writes or delayed Btrfs reclamation to individual items. Keep snapshots and unique
state report-only under the policy. Updates, new safety snapshots, and changes to
retention require separate approval; they can consume space or pin artifacts.

**Complete when:** every approved ID and preservation promise is accounted for,
the observed space change and remaining unknowns are clear, and the requested
headroom is reached or the next meaningful decision is presented.
