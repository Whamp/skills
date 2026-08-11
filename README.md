# Agent Skills

Public source for agent skills authored and maintained by [Will Hampson](https://github.com/Whamp).

Each skill is an independent directory containing a `SKILL.md` manifest and any references, scripts, or assets it needs. The category directories organize discovery; they do not create runtime dependencies between skills.

## Install

List the available skills:

```bash
npx skills add Whamp/skills --list
```

Install one skill:

```bash
npx skills add Whamp/skills --skill property-based-testing
```

Use `--global` for a user-level installation or the installer's `--agent` option to select specific harnesses.

## Skills

### Engineering

- [`ban-type-assertions`](engineering/ban-type-assertions/) — bans TypeScript assertions with oxlint and replaces them safely.
- [`codegraph`](engineering/codegraph/) — scouts structural code graphs before targeted source reads and changes.
- [`docs-to-types`](engineering/docs-to-types/) — converts approved domain decisions into typed architecture before business behavior is implemented.
- [`dynamic-workflow-patterns`](engineering/dynamic-workflow-patterns/) — selects and structures multi-agent workflow patterns for decomposable work.
- [`e2e-testing`](engineering/e2e-testing/) — designs and operates Playwright tests for critical user journeys.
- [`explain-diff-html`](engineering/explain-diff-html/) — creates interactive HTML explainers for code changes.
- [`fuzzing`](engineering/fuzzing/) — builds and operates fuzzing harnesses for Rust, C/C++, and Go.
- [`herdr`](engineering/herdr/) — operates persistent sidecar agents and observable terminal work through Herdr.
- [`integration-testing`](engineering/integration-testing/) — tests behavior across API, database, service, filesystem, queue, and contract boundaries.
- [`javascript-testing-expert`](engineering/javascript-testing-expert/) — supplies idiomatic JavaScript and TypeScript testing patterns.
- [`model-routing`](engineering/model-routing/) — selects delegated model portfolios for specialized roles.
- [`nvidia-cuda-performance`](engineering/nvidia-cuda-performance/) — applies gated CUDA performance engineering with RTX 3090/SM86, LLM inference, and intra-host multi-GPU branches.
- [`omarchy-free-disk-space`](engineering/omarchy-free-disk-space/) — safely reclaims disk space on Omarchy and Arch Linux.
- [`perform-like-jeff-and-sanjay`](engineering/perform-like-jeff-and-sanjay/) — applies gated, evidence-driven performance engineering within a single binary.
- [`property-based-testing`](engineering/property-based-testing/) — designs, reviews, and operates counterexample-searching tests for broad domains, independent oracles, stateful APIs, and concurrent schedules.
- [`rust-testing-expert`](engineering/rust-testing-expert/) — supplies idiomatic Rust testing patterns and tooling.
- [`sideshow`](engineering/sideshow/) — publishes rich work to a hosted visual review and feedback loop.
- [`worktree-first`](engineering/worktree-first/) — isolates substantive repository changes in dedicated Git worktrees.

### Productivity

- [`clear-writing`](productivity/clear-writing/) — writes and revises durable human-facing prose with plain force.
- [`distilling-skills`](productivity/distilling-skills/) — finds, evaluates, and combines related skills into a concentrated replacement.
- [`first-principles`](productivity/first-principles/) — separates facts, assumptions, constraints, analogies, and unknowns before rebuilding an approach.

The [`personal`](personal/) category is reserved for portable personal workflows and is currently empty.

## Source and installation model

This repository is the canonical source. Agent directories such as `~/.agents/skills/` are consumer-managed installation surfaces. Changes should be reviewed and merged here before consumers update through their installer; hand-editing an installed copy creates an untracked fork.

The repository contains public invocation defaults. Consumers may apply machine-specific invocation overlays without changing the canonical skill.

## Contributing

Before publishing a skill, confirm it is Will-authored or materially transformed rather than a substantially verbatim third-party copy, preserve any notices required for redistribution, remove private infrastructure and personal paths, and keep every required file inside the skill directory. Repository maintenance rules live in [`AGENTS.md`](AGENTS.md).

Run the full repository check before opening a pull request:

```bash
make validate
```

The check runs validator tests, audits manifests and local reference links, lints Markdown, and verifies that the standard skills installer discovers the collection.

## License

MIT unless a skill includes its own license or states different terms in its frontmatter.
