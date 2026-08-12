# Cleanup classification

Use this reference during the audit and the apply-time revalidation. Evidence accumulates; no single age, size, name, or clean status proves disposability.

## Worktrees

### Recommended

A worktree may be recommended for removal when all of these are true:

- it is not the primary checkout;
- `git status --porcelain` is empty and no merge, rebase, cherry-pick, bisect, or sequencer operation is in progress;
- no live process has the path as its working directory or command target;
- its HEAD has a named recovery path: a retained local branch, tag, remote ref, merged integration history, or another explicitly verified ref;
- any associated PR is merged/closed or the user has otherwise completed or abandoned that task;
- no repository instruction requires retaining it.

Remove the worktree, not its branch. Branch deletion is a separate decision.

### Optional

A clean worktree is optional rather than recommended when its branch is still active, its prototype remains useful, or its purpose is unclear but recoverability is sound. Removing it saves files while retaining its branch and commits.

### Keep

Keep a worktree when any of these applies:

- tracked or untracked changes exist;
- a Git operation is in progress;
- its detached HEAD or commits have no verified recovery ref;
- a process, service, editor, or agent is using it;
- an open task or repository instruction says to retain it;
- it is the primary checkout.

### Uncertain

Use uncertain when remote refs are stale, host PR evidence is unavailable, commit reachability is ambiguous, filesystem access is incomplete, or process ownership cannot be checked. State the exact read-only command or source needed to resolve it.

## Branches and commits

Worktree removal and branch deletion are different operations. The cleanup default is:

- retain local branches;
- retain tags and remote refs;
- never force-delete a branch;
- never delete a detached worktree until its HEAD is reachable from a named preserved ref or the user separately approves losing it.

Ahead/behind counts describe one upstream comparison, not total reachability. Check local branches, tags, and remote refs before calling commits unique or preserved.

## Temporary and generated artifacts

### Recommended artifacts

Recommend repository-owned artifacts when all of these hold:

- provenance is clear from project naming, configuration, manifests, logs, or the command that created them;
- they are reproducible, already published elsewhere, or explicitly disposable evidence;
- no live process, service, config, symlink, active pointer, or scheduled job references them;
- deleting them cannot expose a partial runtime state;
- their exact paths and consequences can be named before approval.

Common candidates include completed benchmark scratch, abandoned build output, old test fixtures created under temporary roots, duplicate downloaded artifacts whose canonical release is verified, and inactive generated indexes that the owning application can rebuild.

### Keep artifacts

Keep canonical source, unique reports, checksums, receipts, forensic archives, rollback evidence, user configuration, ignored policy, credentials, active caches required for offline operation, and unfamiliar artifacts without clear ownership.

Treat dependency directories and compiler caches as optional unless the user requested space recovery; they are reproducible but may make the next build expensive.

## Databases and indexes

A database copy is recommended only after proving it inactive. Establish:

- the active pointer or configured database path;
- all candidate/generation directories;
- open file handles or writer processes;
- service and timer targets;
- maintenance, rollback, retention, and forensic policy;
- whether the copy is complete, corrupt, staged, inactive, or disposable;
- the recovery source if removed.

Keep the sole active database, active WAL/sidecar files, rollback copies still inside their promised window, staged candidates awaiting certification, and forensic samples. A database that looks old but remains the configured rollback source is active policy state, not clutter.

## External temporary roots

Search outside the repository narrowly. Include a path only when its ownership is evidenced by an exact repository name, configured scratch root, manifest, log, process command, or known tool prefix. Report broad `/tmp` glob matches as uncertain until ownership is established.

Temporary-directory cleanup is permanent unless the platform provides a trash mechanism. Revalidate that no matching process remains immediately before deletion.

## Reporting

Use one row per independently approvable item or homogeneous set. A set is homogeneous only when every member has the same evidence, consequence, recovery path, and action. Expand mixed sets.

Recommended report columns:

| ID | Type | Exact path | Apparent size | Class | Evidence | Consequence and recovery |
| --- | --- | --- | ---: | --- | --- | --- |

End the audit with:

- total recommended apparent size;
- optional apparent size;
- dirty, unique, active, and forensic items preserved;
- unresolved evidence;
- exact IDs recommended for approval.
