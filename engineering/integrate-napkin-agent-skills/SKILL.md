---
name: integrate-napkin-agent-skills
description: Integrate a Napkin vault with the files created by setup-matt-pocock-skills.
disable-model-invocation: true
compatibility: Requires napkin-ai for vault operations. Run after setup-matt-pocock-skills.
---

# Integrate Napkin with agent skills

Run this immediately after `setup-matt-pocock-skills`. Add Napkin project memory without duplicating the issue tracker, triage labels, domain glossary, or ADR rules.

This is prompt-driven. Explore, present findings, take one answer at a time where a choice exists, show exact drafts, then write only after approval.

## 1. Guarded preflight

Read [the Napkin integration contract](references/napkin-integration-contract.md) before the first Napkin command. It records the mutation, layout, indexing, template, Pi-extension, and version-drift branches.

Establish the repository root and inspect:

- `AGENTS.md` and `CLAUDE.md`
- `docs/agents/issue-tracker.md`, `docs/agents/domain.md`, and optional `docs/agents/triage-labels.md`
- `NAPKIN.md`
- `.napkin/` and `.obsidian/.napkin/` in the current directory and each ancestor
- `.obsidian/`
- root README, manifests, existing domain docs, and the folders that reveal the repository's purpose
- `command -v napkin` and `napkin --version`

`napkin --version`, `napkin --help`, and `napkin init --list --json` are safe before vault discovery. Other Napkin commands can create a bare vault when none exists, so do not run them yet.

The Matt setup is complete only when one instruction file contains `## Agent skills` and `docs/agents/issue-tracker.md` plus `docs/agents/domain.md` exist. If this evidence is absent, stop and ask the user to run `setup-matt-pocock-skills` first.

Choose the instruction file with the same rule as that setup:

1. `CLAUDE.md` when it exists.
2. Otherwise `AGENTS.md` when it exists.
3. If neither exists, stop. Do not create one here.

If Napkin is unavailable, recommend `npm install -g napkin-ai` and ask whether to install it. Installation is the only action after that answer.

Completion criterion: the setup output, instruction file, Napkin executable, and nearest local-vault marker are each identified without creating files.

## 2. Resolve the vault branch

### Existing local vault

A local vault marker is either `.napkin/` or `.obsidian/.napkin/`. After finding one, run:

```bash
napkin vault --json
napkin config show --json
napkin overview --json
napkin file list --json
napkin template list --json
```

Use `napkin vault --json` as the authority for the content root. Derive the Level 0 note path from that root:

- sibling or nested layout: `<content-root>/NAPKIN.md`
- legacy embedded layout: `<repo>/.napkin/NAPKIN.md`

If the resolved content root is above the repository, recommend a repository-local vault. Ask whether to use the ancestor vault or initialize a local one before continuing.

If the config has no `vault.root`, report the legacy embedded layout. Keep it for this integration unless the user separately asks to migrate it. Note that repository files outside `.napkin/` are not searchable in that layout.

### No local vault

Explain that initialization creates `.napkin/config.json`, `.obsidian/`, and optionally template files. If `.obsidian/` already exists, Napkin preserves existing settings, adds its daily/template config, and sets `alwaysUpdateLinks`.

Recommend one template from repository evidence:

- `coding` for software source repositories
- `research` for papers, concepts, questions, or experiments
- `product` for features, roadmap, specs, or releases
- `company` for people, runbooks, infrastructure, or onboarding
- `personal` for personal projects, areas, people, or references
- no template when an established vault structure should stay unchanged

Ask one question with the recommended answer: whether to initialize and which template to use. On approval, run exactly one of:

```bash
napkin init --path "<repo-root>" --template <template> --json
napkin init --path "<repo-root>" --json
```

Then run the existing-vault inspection commands.

Completion criterion: the user has selected the vault, and its content root, config path, layout, template structure, and Level 0 note path are known.

## 3. Inspect integration state

Read the Level 0 note directly. Classify it as:

- absent or empty
- untouched template skeleton
- substantive and current
- substantive but stale
- substantive but too long for Level 0 orientation

Treat authored content as authoritative. A template skeleton still contains prompts such as "Brief description", "What are you studying?", or empty list items instead of repository facts.

Capture a before-state link report:

```bash
napkin link unresolved --json
```

Check Pi integration with `pi list --approve` when `pi` exists. Also inspect package entries in global `~/.pi/agent/settings.json` and project `.pi/settings.json` when present so scope and filters are not guessed. The approval flag is required for the subprocess to include trusted project settings.

Classify the result by scope:

- active project-local `pi-napkin`: session startup injects the overview and provides `kb_search` and `kb_read`
- project-local but filtered: the package exists in `.pi/settings.json`, but its context extension is disabled
- global-only: report it as ambient state, not an installed project integration
- absent: agents currently need the CLI retrieval path
- nested `.obsidian/.napkin/`: pi-napkin 0.3.0 cannot resolve this local layout, even when installed

Inspect the resolved config file for `distill.enabled`. If it is enabled, surface its interval, provider, and model. The pi-napkin 0.3.0 default is `anthropic/claude-sonnet-4-6`; treat that default as unverified until current provider readiness confirms it.

### Choose the Pi integration mode

Report the detected state and ask the user to choose one mode:

1. **CLI only**: keep Napkin retrieval in repository instructions without installing an extension. Recommend this when the user wants the smallest integration or the vault uses nested layout.
2. **Project-local Pi context tools**: install or enable project-local pi-napkin for overview injection plus `kb_search` and `kb_read`. Keep automatic distillation off.
3. **Project-local Pi context tools and automatic distillation**: install or enable project-local pi-napkin, then configure a supported model and interval before enabling background writes.

If a project-local package is already active, offer to preserve it as the recommended answer. Treat a user-global installation as ambient state, not the integration target: report it, leave it unchanged, and recommend an explicit project-local entry when the user selects a Pi mode. If the user chooses CLI only while project-local pi-napkin is active, ask whether to leave it installed, disable its project resources with `pi config -l --approve`, or remove its project entry with `pi remove npm:pi-napkin -l --approve`. Never change the global package or remove or disable the project package implicitly.

For nested layout, explain that pi-napkin 0.3.0 may inject a configured global fallback instead of the local vault. Offer CLI only or a separately approved migration to sibling layout. Do not install or enable pi-napkin under the assumption that nested layout works.

### Install or enable project-local pi-napkin

Pi packages execute code with full user permissions. Before installing an absent package:

1. Read the current `pi-napkin` package metadata and source or repository summary.
2. Compare its version with the audited behavior in the integration contract.
3. Report the source, version, extension behaviors, and any material drift.
4. Ask for explicit installation approval.

Install pi-napkin at project scope only:

```bash
pi install npm:pi-napkin -l --approve
```

Make the boundary explicit before approval: this writes the package entry to `.pi/settings.json` and may create or update `.pi/npm/.gitignore`, `.pi/npm/package.json`, and `.pi/npm/package-lock.json`; installed dependencies remain under the ignored `.pi/npm/node_modules/`. These project files make the dependency reproducible for trusted collaborators. The command does not modify `~/.pi/agent/settings.json`. Every pi-napkin install command in this skill must include `-l`.

If the project package is installed but filtered, use `pi config -l --approve`. Enable the context extension for modes 2 and 3, and enable the distill extension for mode 3. In mode 2, keep distillation disabled whether its extension is loaded or filtered. Preserve unrelated project filters. If only a global package exists, leave it unchanged and add the project-local entry only after approval; Pi gives the project entry precedence.

After installation or enablement, run `pi list --approve` again and inspect `.pi/settings.json`. Explain that context injection and `kb_search`/`kb_read` become available in a new or reloaded Pi session; their absence from the current session is not an installation failure.

### Configure automatic distillation

Mode 3 is a separate write-capability opt-in. Before enabling it:

1. Run `pi --list-models` and apply the current model-routing policy.
2. Offer only configured, available models that satisfy the repository's provider policy.
3. Ask the user to select the provider/model and interval in minutes.
4. Explain that pi-napkin forks the conversation on that interval and may create or append vault notes.
5. Show the exact config changes and ask for approval.

Set provider, model, and interval first. Set `distill.enabled` last:

```bash
napkin config set --key distill.model.provider --value "<provider>" --json
napkin config set --key distill.model.id --value "<model-id>" --json
napkin config set --key distill.intervalMinutes --value <minutes> --json
napkin config set --key distill.enabled --value true --json
napkin config show --json
```

For mode 2, keep `distill.enabled` false. If it was already true, show and confirm the change before setting it false.

Completion criterion: the current Level 0 quality, unresolved-link baseline, package scope and filter state, selected retrieval mode, and explicit distillation state are known. Any installation or background-write capability has separate user approval.

## 4. Draft the integration

### Level 0 context

`NAPKIN.md` owns project orientation and active direction. Draft or revise it only when the current note is absent, skeletal, stale, or too broad.

Keep it near 200 words or less. Include only facts supported by repository files:

- what the project is trying to accomplish
- the current experiment, product direction, or active work
- constraints or invariants that change decisions
- where deeper authoritative material lives
- open threads that remain genuinely active

Keep these meanings in their existing sources of truth:

- actionable work in the configured issue tracker
- triage vocabulary in `docs/agents/triage-labels.md`
- canonical domain terms in `CONTEXT.md` or files named by `CONTEXT-MAP.md`
- architecture decisions in ADRs
- durable findings and reusable procedures in ordinary Napkin notes

A substantive, accurate `NAPKIN.md` may need no edit.

### Instruction-file pointer

Add one `### Project memory` subsection inside the existing `## Agent skills` block. Update an existing `Project memory`, `Research vault`, or `Napkin` subsection in place instead of adding a duplicate.

When mode 2 or 3 has a verified, unfiltered project-local package and the layout is supported, draft this shape:

```markdown
### Project memory

For project orientation, prior findings, or research history, use the injected Napkin overview, then `kb_search` and `kb_read` for deeper retrieval.

Use Napkin notes for durable knowledge and the configured issue tracker for actionable work.
```

Otherwise draft this shape:

```markdown
### Project memory

For project orientation, prior findings, or research history, read `<level-0-path>`. Retrieve deeper context with `napkin overview --json`, then `napkin search "<topic>" --json`, then `napkin read "<file>" -q` as needed.

Use Napkin notes for durable knowledge and the configured issue tracker for actionable work.
```

Use `NAPKIN.md` as `<level-0-path>` for the normal sibling layout. Use the repository-relative path for other layouts.

The standard integration stops at the Level 0 note and one instruction pointer. Add a separate Napkin agent doc only when repository-specific rules exceed that block.

Show the exact proposed `NAPKIN.md` and instruction subsection. Mark unchanged files explicitly. Ask for approval or edits before writing.

Completion criterion: the user has approved exact file contents and can see which existing sources remain authoritative.

## 5. Write without duplication

Apply the approved changes:

- create or edit the resolved Level 0 note
- insert or replace only the Napkin subsection inside `## Agent skills`
- preserve every surrounding user-authored section
- leave `docs/agents/*.md`, `CONTEXT.md`, `CONTEXT-MAP.md`, and ADRs unchanged unless the user approved a separate correction

Completion criterion: one Level 0 note and one project-memory pointer exist, with no duplicate heading or duplicated policy.

## 6. Verify

Run:

```bash
napkin file wordcount NAPKIN --json
napkin overview --json
napkin search "<project-specific core topic>" --json --limit 5
napkin link unresolved --json
git status --short
git diff -- .pi/settings.json .pi/npm/package.json .pi/npm/package-lock.json <instruction-file> <level-0-path>
```

For modes 2 and 3, also run `pi list --approve` and inspect the project settings entry. For mode 3, inspect `napkin config show --json` after all writes.

Verify all of the following:

- the Level 0 note is close to or below 200 words
- `overview.context` matches the note
- the search smoke test reaches relevant project knowledge
- the final unresolved-link set contains no link introduced by this integration
- exactly one Napkin subsection exists in the chosen instruction file
- issue-tracker, triage, and domain pointers still match their approved setup
- the instruction pointer matches the selected CLI or Pi retrieval mode
- pi-napkin has the approved scope and is not unexpectedly filtered
- automatic distillation exactly matches the approved enabled state, provider, model, and interval
- unrelated working-tree and settings changes remain untouched

Napkin 0.9.2 indexes all Markdown outside its fixed skipped-directory list. `AGENTS.md`, `CLAUDE.md`, and `docs/agents/*.md` therefore appear in search, and agent docs may appear in overview keywords. Report this behavior. Preserve the setup paths and use only exclusion settings supported by the installed version. For another Napkin version, recheck this behavior before reporting it.

Finish with the paths changed, selected retrieval mode, package scope and state, distillation state, verification evidence, and any pre-existing broken links or indexing noise left untouched. If pi-napkin was installed or enabled, tell the user that a new or reloaded Pi session is required to exercise injected context and tools. Mention that future direction changes belong in `NAPKIN.md`, while durable findings belong in normal vault notes.
