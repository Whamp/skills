---
name: repo-cleanup
description: Audit and safely remove obsolete Git worktrees, repository-owned temporary artifacts, and inactive development databases.
disable-model-invocation: true
compatibility: Requires Git. GitHub PR classification additionally requires the gh CLI. Service and process checks depend on host tooling.
---

# Repository Cleanup

Inventory first, approve exact targets second, delete last. Treat cleanup as preservation work: a clean directory is not disposable until its commits, data, ownership, and runtime use are accounted for.

## Scope

Resolve the target repository from the user's argument or current directory. Read its applicable agent instructions before inspecting it. If the target is not one Git repository, stop and ask which repository to clean.

The default scope is:

- registered Git worktrees and their local branches;
- repository-owned build, debug, benchmark, and temporary artifacts;
- repository-owned inactive database generations or copies;
- matching temporary artifacts outside the repository only when ownership is evidenced by an exact project name, configured path, manifest, log, or process command.

Keep unrelated system caches, other repositories, live databases, user documents, and unfamiliar paths outside the plan. Route broad machine cleanup to a system disk-cleanup workflow instead.

## Audit

Make no deletions, branch changes, service changes, or database writes during this turn.

1. Establish the repository root, Git common directory, integration branch, remotes, current status, registered worktrees, and filesystem usage. Refresh remote refs without pruning when repository policy and network access allow it; otherwise label remote and merge conclusions stale.
2. Read [the cleanup classification reference](references/classification.md). Inventory every registered worktree, including the primary checkout. For each, record:
   - exact path and apparent size;
   - HEAD, branch or detached state, and upstream;
   - tracked changes, untracked files, and in-progress Git operations;
   - ahead/behind state and commit reachability from local branches, tags, and remote refs;
   - open, merged, or closed PR evidence when the host and CLI are available;
   - processes whose command or working directory uses the worktree.
3. Inventory repository-owned artifact roots. Inspect configuration, manifests, symlinks, service definitions, process arguments, and project documentation before classifying databases or generated directories. Enumerate database-like files explicitly; never infer inactivity from an extension or old timestamp alone.
4. Measure candidate paths individually. Distinguish logical bytes (`du -x -s -B1 --apparent-size`), allocated file blocks (`du -x -s -B1`), and available bytes on each affected filesystem (`df -B1 PATH`). Follow the classification reference's space rules for shared/sparse/snapshotted data. A successful removal or summed directory size is not proof of physical recovery.
5. Assign stable item IDs and classify each item as:
   - **recommended** — removal is evidenced and recoverability is explicit;
   - **optional** — removable, but retaining it has a plausible purpose;
   - **keep** — active, dirty, unique, forensic, or otherwise valuable;
   - **uncertain** — evidence is incomplete or contradictory.

Audit completion requires every registered worktree and every discovered database copy to have one classification. List rejected candidates as well as recommended ones so silence cannot hide missed state.

## Approval gate

Lead with at most five evidence-backed recommendations, then group optional, kept, and unresolved items. Use the classification reference's decision table: exact ID/path/action, file size, physical-recovery estimate and basis, evidence, consequence, and recovery. State separately whether branch refs will be retained. Resolve large uncertain candidates instead of stopping at small cache wins.

Recommend exact IDs. Ask the user to approve those IDs or the uniquely named recommended set, then end the turn. General permission to "clean the repo" is permission to audit, not permission to delete. Never bundle branch deletion with worktree or artifact cleanup.

## Apply

Apply only the approved IDs. Before each action, revalidate the evidence that made it safe:

- the path resolves to the same object and remains inside its approved root;
- a worktree is still registered, clean, operation-free, and unused by a process;
- its branch or detached commit still has the recorded recovery path;
- an artifact is still repository-owned and not referenced by current config, manifests, services, or processes;
- a database is still inactive and is not the target of an active pointer, writer, scheduled job, or rollback policy.

A changed or failed precondition rejects that item without widening approval to another item.

Use the owning cleanup command when one exists. Remove worktrees with `git worktree remove` without force and retain branch refs by default. State permanent removal and its recovery source before approval. A move to Trash is reversible staging, not space recovery; emptying it needs separate approval covering its existing contents. Stop a writer or scheduler only when an approved item requires it, wait for the running operation to settle, and restore the prior service state afterward.

## Verify

After application:

1. Re-list worktrees and verify retained dirty, detached, and primary worktrees are unchanged.
2. Verify every promised branch, tag, or remote recovery ref still exists.
3. Re-inventory database generations, active pointers, configuration, and preserved forensic or rollback artifacts.
4. Verify affected services and timers returned to their prior state. Do not start an expensive maintenance job solely as a smoke test. If a normal job starts during verification, let it settle and report its real result.
5. Measure available space again on each affected filesystem. Report the observed change, not a per-item attribution: shared extents, snapshots, open files, delayed reclamation, and concurrent writes affect it. Do not sum repeated views of the same filesystem.
6. Report each approved ID as removed, moved to Trash, skipped, or failed, with the reason, plus everything intentionally preserved.

Cleanup is complete only when all approved IDs are accounted for, preservation promises are verified, and the repository remains usable.
