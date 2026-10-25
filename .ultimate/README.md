# Skills project setup

The landing gate runs `make validate` before Ultimate advances the destination branch. No automatic push is configured. Tools are invoked on demand by the Makefile; worktrees need `make`, Git, Bash, `uv`, Node.js and npm on `PATH`, but no application bootstrap, database or server.

For changes coordinated through Ultimate, create a Lane from the coordinator's branch with `lane new <name> --base <coordinator-branch>`. Read path memories, commit, run `lane check`, reconcile notes and `lane merge` into that coordinator branch. Then submit the coordinator through Ultimate for the final checked integration. This keeps Lane's memory handling without landing the same work into `main` twice. Standalone Lane work continues to follow the repository's `AGENTS.md`.

Use the project-local [verify-skills skill](skills/verify-skills/SKILL.md) to drive repository validation, canonical installer discovery and safe fixture tests with retained terminal evidence. It is verification tooling, not a published collection skill. It loads when this project's configuration is trusted.

The installer-discovery step in `make validate` stages only canonical skill content and requires the pinned CLI to list every canonical name exactly once. See the verification map for evidence requirements and the limits of this local-source listing proof; it does not verify remote fetching or consumer installation.
