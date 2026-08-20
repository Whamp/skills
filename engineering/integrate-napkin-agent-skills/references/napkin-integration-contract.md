# Napkin integration contract

This reference records behavior verified against `napkin-ai` 0.9.2 at git commit `bbea2920374829ca351a1290ad3d794eb0d6f903` and `pi-napkin` 0.3.0 at git commit `15aa0f32d660cbd7c3936b8f538ccc543251c817`. A disposable project-local install and extension load also passed under Pi 0.84.2.

When installed versions differ, treat current `--help`, installed source, and temporary-vault probes as authoritative. Recheck every behavior below that affects the planned edit.

## Vault discovery mutates

The `Napkin` constructor walks upward from its starting directory for:

1. `.napkin/`
2. `.obsidian/.napkin/`

When neither exists, it creates a bare vault in the starting directory. Creation includes `.napkin/config.json`, `.obsidian/`, and an empty `NAPKIN.md`. Most CLI commands construct `Napkin`, including `vault`, `overview`, `search`, `read`, and `config`.

Safe pre-discovery commands are `napkin --version`, `napkin --help`, command-specific `--help`, and `napkin init --list --json`.

The global `--vault <path>` option supplies the constructor's starting directory. It does not make a missing path read-only.

## Layouts

Napkin supports:

- sibling: `.napkin/`, `.obsidian/`, and content share one project root; config has `vault.root: ".."`
- nested: config lives at `.obsidian/.napkin/`; content remains at the project root
- legacy embedded: config lacks `vault.root`; content lives inside `.napkin/`

Invalid or missing config on an existing `.napkin/` falls back to the legacy embedded interpretation.

`napkin vault --json` reports the resolved content root in `path`. Use it instead of guessing from directory names.

## Initialization

`napkin init` uses sibling layout. Existing vault initialization is idempotent. Supplying a template later composes missing folders and files into the vault. Existing files, including `NAPKIN.md`, are preserved.

An existing `.obsidian/` is adopted. Napkin preserves existing `app.json` keys, sets `alwaysUpdateLinks: true`, and writes `daily-notes.json` plus `templates.json`.

Built-in templates:

| Template | Main folders |
| --- | --- |
| `coding` | `decisions`, `architecture`, `guides`, `changelog`, `daily` |
| `personal` | `people`, `projects`, `areas`, `references`, `daily` |
| `research` | `papers`, `concepts`, `questions`, `experiments`, `daily` |
| `company` | `people`, `projects`, `runbooks`, `infrastructure`, `onboarding`, `daily` |
| `product` | `features`, `roadmap`, `research`, `specs`, `releases`, `daily` |

Each template adds `_about.md` files, note templates, and a Level 0 skeleton only when those paths do not already exist.

## Progressive disclosure and indexing

Napkin's retrieval sequence is:

1. `NAPKIN.md`: Level 0 project context
2. `napkin overview`: Level 0 plus folder map
3. `napkin search <query>`: ranked Markdown results
4. `napkin read <file>`: full file

`NAPKIN.md` is returned as `overview.context`. It is excluded from overview folder counts and keywords but remains searchable.

Overview also excludes the configured templates folder and every `_about.md`. Search includes them because it indexes every Markdown file returned by the general file walker.

The file walker skips `.obsidian`, `.git`, `.trash`, `.nanny`, `.napkin`, and `node_modules`. Version 0.9.2 has no path-exclusion config. As a result, repository Markdown such as `AGENTS.md`, `CLAUDE.md`, and `docs/agents/*.md` is searchable and may influence overview keywords.

Overview and search caches use file fingerprints. Adding, removing, or touching vault files invalidates the relevant cache.

Wikilink-style reads resolve a unique Markdown basename case-insensitively. Ambiguous names require a full path. Search ranking combines BM25, backlink count, and recency.

## Config ownership

`.napkin/config.json` is the source of truth for overview, search, daily notes, templates, graph rendering, and vault layout. Saving config synchronizes selected settings into `.obsidian/`.

The 0.9.2 core config has no `distill` schema, but it preserves unknown keys through deep merge. The separate pi-napkin extension reads `distill` directly.

## Pi package scope

Pi installs a trusted project package with `pi install <source> -l --approve`, recording it in `.pi/settings.json`. A first project install can also create `.pi/npm/.gitignore`, `.pi/npm/package.json`, `.pi/npm/package-lock.json`, and ignored `.pi/npm/node_modules/`. `pi config -l --approve` changes project resource filters, and `pi remove <source> -l --approve` removes only the project entry. `pi list --approve` includes trusted project packages; without approval, a subprocess can show only user packages and produce a false absence.

A project package takes precedence over the same user-global package. This skill uses project-local pi-napkin only so the repository declares its integration and trusted collaborators can reproduce it. A global installation is detection evidence only and remains unchanged.

## Pi integration

pi-napkin 0.3.0 adds two independent extensions:

- context extension: injects the full Napkin overview on session start and registers `kb_search` plus `kb_read`
- distill extension: optionally forks the current session on a timer or `/distill` and writes notes through a background Pi process

Its local resolver checks only `.napkin/`, then falls back to `~/.pi/agent/napkin.json`. It does not detect `.obsidian/.napkin/`. A nested local vault can therefore be missed or replaced by global fallback context.

Automatic distillation defaults to off. When enabled without an explicit model, version 0.3.0 uses `anthropic/claude-sonnet-4-6`. The background process has a ten-minute timeout. Keep it off unless the configured provider and model are available and the user explicitly wants automatic writes.

## Command inventory

The 0.9.2 CLI exposes 57 command/help leaves across:

- setup and retrieval: `init`, `overview`, `graph`, `vault`, `update`, `read`, `search`
- file writes: `create`, `append`, `prepend`, `move`, `rename`, `delete`
- file metadata: `file info`, `list`, `folder`, `folders`, `outline`, `wordcount`
- daily notes: `daily today`, `path`, `read`, `append`, `prepend`
- metadata: `tag`, `property`, `task`, and `link` subcommands
- structured content: `base`, `canvas`, `template`, and `bookmark` subcommands
- configuration: `config show`, `get`, and `set`

This integration uses only initialization, configuration inspection, progressive retrieval, word count, and link checks. The remaining commands do not change the setup boundary.
