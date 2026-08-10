---
name: worktree-first
description: Use worktree-first isolation for substantive implementation in project repositories. Use before starting a feature, nontrivial fix, or substantial refactor, including implementation handed off by another skill or workflow.
---

# Worktree-First Development

For new substantive implementation work in a project repository—features, nontrivial fixes, and substantial refactors—use a dedicated Git worktree at `<repo>/.worktrees/<task-slug>`. Read-only investigation and trivial documentation or metadata edits may remain in the current checkout.

Before editing:

1. Inspect the repository status, existing branches, and existing worktrees. Reuse a branch or worktree already dedicated to the task.
2. Preserve the primary checkout and its uncommitted changes.
3. Ensure `.worktrees/` is ignored through the repository-local Git exclude file. Avoid changing the project’s committed `.gitignore` solely for local worktrees.
4. Fetch `origin` and create a dedicated task branch from `origin/main`. If `origin/main` is unavailable, use local `main`; if the repository has no `main`, use its default integration branch. Report any fallback.
5. Follow the repository’s branch-naming convention; otherwise use a descriptive task slug.
6. Perform implementation and verification in the task worktree. Report its path, branch, and base revision.

Worktree setup is complete when the task worktree is on the intended branch, `.worktrees/` is ignored, and the primary checkout remains unchanged. If safe setup is unavailable, report the blocker and proposed fallback before editing.

Retain the worktree through review and integration. Remove it after the work is safely integrated or Will requests cleanup.
