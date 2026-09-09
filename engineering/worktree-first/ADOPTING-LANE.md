# Adopt Lane in a repository

If the task is deliberate repository adoption, use this guide. `lane init` always writes to the primary worktree, even when you run it from a linked worktree. Use a clean standalone clone so the existing primary worktree remains unchanged.

1. Read the repository's isolation and landing instructions.
2. Create a standalone clone from the fresh intended base.
3. Create a dedicated adoption branch in that clone.
4. Run `command lane init`.
5. Run `command lane install skill`.
6. Review `.lane/`, the marked `AGENTS.md` block, `.agents/skills/lane/`, and `.claude/skills/lane`.
7. Run `command lane init` again.
8. Run `command lane install skill` again.
9. Confirm that the second run of each command changes no bytes.
10. Commit the generated files and link as one adoption change.
11. Send the adoption branch through the repository's review path.

Adoption setup is complete when both repeated commands change no bytes and the adoption branch contains the generated policy files and link.

`command lane install hooks` is optional for each clone. Keep clone-local hook setup separate from the committed adoption change.
