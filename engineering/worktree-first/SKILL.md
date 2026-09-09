---
name: worktree-first
description: Worktree-first isolation routes substantive implementation through Lane in adopted repositories and a plain Git worktree elsewhere. Use before a feature, nontrivial fix, substantial refactor, delegated implementation, or deliberate Lane adoption.
---

# Worktree-first development

Start every substantive implementation in one task-owned worktree from a fresh, explicit base. Keep the primary worktree and its uncommitted changes unchanged. Read-only investigation and trivial documentation or metadata edits may remain in the current worktree.

Before setup, read the repository instructions for isolation and landing. If they define a repository-specific workflow, follow it instead of the generic routes below. If that workflow cannot preserve task isolation, stop before editing. Report the conflict.

Do not run `lane init` during unrelated implementation. For deliberate adoption, follow [Adopt Lane in a repository](ADOPTING-LANE.md).

## Safety gate

1. Inspect the repository status, branches, and worktrees.
2. If an existing branch or worktree belongs to this task, reuse it.
3. Preserve the primary worktree and its uncommitted changes.
4. If a remote exists, fetch the intended remote. Select the integration branch and an explicit base ref.
5. Resolve and record the base commit. Report every fallback from the repository's normal integration branch.
6. Follow the repository's branch convention. If none exists, use a descriptive task slug.

The safety gate is complete when the task owns its branch, the base ref and commit are recorded, and the primary worktree remains unchanged.

Choose one route after completing the safety gate:

- If the repository root contains `.lane/`, follow [Use Lane in an adopted repository](LANE.md).
- Otherwise, use the plain Git route below.

## Plain Git route

1. Resolve the repository root.
2. Ensure `/.worktrees/` is ignored through the repository-local Git exclude file. Do not change the committed `.gitignore` solely for local worktrees.
3. Choose one creation case.
   - For a new task branch, run `git worktree add -b <task-branch> <repo>/.worktrees/<task-slug> <base-ref>`.
   - For a dedicated task branch that already exists, run `git worktree add <repo>/.worktrees/<task-slug> <task-branch>`.
4. Enter the task worktree.
5. If Git attached an existing branch, rebase it onto the selected base before editing.
6. Report the worktree path, task branch, base ref, and base commit.

Setup is complete when `/.worktrees/` is locally ignored, the task worktree uses the intended base, and the primary worktree remains unchanged. Perform implementation and verification only in the task worktree.

Retain the worktree through review and integration. Remove it after safe integration or an explicit cleanup request. When the task branch is no longer needed, delete it.
