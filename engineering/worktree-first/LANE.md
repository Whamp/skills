# Use Lane in an adopted repository

This guide owns isolation and landing safety. The repository's `.agents/skills/lane/SKILL.md` owns Lane memory and note handling.

## Create or resume a lane

1. Require the `lane` command. If it is unavailable, stop. Report the blocker.
2. Read the repository's `AGENTS.md` files and `.agents/skills/lane/SKILL.md`. If the repository-local Lane skill is missing, stop. Report the blocker.
3. Run `command lane ls --json`. If an existing lane belongs to this task, reuse it.
4. For remote review, use the fetched remote-tracking integration ref as the base.
5. For local landing, use a local integration branch as the base. If it has a remote, verify that both refs resolve to the same commit.
6. Choose one creation case.
   - If the task includes the exact uncommitted changes in the primary worktree, run `lane_path=$(command lane new <task-slug> --base <base-ref> --dirty)`.
   - For a new clean task branch, run `lane_path=$(command lane new <task-slug> --base <base-ref>)`.
   - For a dedicated task branch that already exists, run `lane_path=$(command lane new <task-branch>)`. Lane rejects `--base` when it adopts an existing branch.
7. Run `cd "$lane_path"`.
8. If Lane adopted an existing branch, rebase it onto the selected base before editing.
9. Report the lane path, task branch, base ref, and base commit.

Setup is complete when the lane uses the intended base and the primary worktree remains unchanged. Follow the repository-local Lane skill during implementation.

## Send a lane for remote review

Complete an explicit rebase before `command lane push`. If Lane's internal rebase conflicts, Lane can push from the previous fork.

1. Fetch the intended remote again.
2. Run `git rebase <remote>/<integration-branch>`.
3. If the rebase conflicts, resolve it and continue the rebase, or abort and stop. Continue only after `git rebase` succeeds.
4. Run `command lane check`.
5. Resolve every reported problem under the repository-local Lane skill.
6. Establish ownership of the remote task branch. If the branch is shared or ownership is unknown, pause for explicit approval.
7. Run `command lane push --base <remote>/<integration-branch>`. Lane rebases and force-pushes the task branch with lease protection.
8. Retain the lane through review.

Remote review setup is complete when the push succeeds and the lane remains available for follow-up work.

After the remote merge:

1. Record the primary worktree with `primary_worktree=$(command lane exit)`.
2. Run `cd "$primary_worktree"`.
3. Run `command lane prune`.

Cleanup is complete when Lane no longer lists the merged lane.

## Land a lane locally

Pass only a local integration branch to `command lane merge`. A remote-tracking ref can create or update a wrongly named local branch instead of the integration branch.

1. Finish review before landing.
2. If the intended remote exists, fetch it.
3. If the local integration branch has a remote, verify that both refs resolve to the same commit.
4. Run `command lane check`.
5. Resolve every reported problem under the repository-local Lane skill.
6. Record the primary worktree with `primary_worktree=$(command lane exit)`.
7. Run `command lane merge --base <integration-branch>` with the verified local branch.
8. After Lane removes the lane, run `cd "$primary_worktree"`.

Local landing is complete when the local integration branch contains the reviewed commits and the lane is removed.

Treat `command lane rm --force` as destructive. Obtain explicit approval before running it.
