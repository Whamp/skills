# Herdr CLI Reference

Read this reference before issuing any Herdr CLI control command. The installed binary is the syntax authority.

## Discover commands safely

```bash
herdr --help
herdr pane --help
herdr agent --help
herdr workspace --help
herdr tab --help
```

Use `herdr <group> --help` to find commands and `herdr <group> <command> --help` for exact syntax. Bare `herdr` launches or attaches the TUI. Most control commands return JSON; take IDs and state from the response.

## Caller context and targets

Herdr injects:

```bash
printf '%s\n' "$HERDR_WORKSPACE_ID" "$HERDR_TAB_ID" "$HERDR_PANE_ID"
```

Resolve the caller once, then use its explicit pane ID for layout and mutation commands:

```bash
caller=$(herdr pane current | jq -r '.result.pane.pane_id')
```

Agent targets are unique live names or pane IDs currently hosting agents. Detected agents may be unnamed; target them by pane ID. Assigned names are cleared when the agent exits, is released, or is replaced, so keep pane IDs in the sidecar ledger. IDs are opaque. Creation responses provide the next target: workspace creation returns a workspace, tab, and root pane; tab creation returns a tab and root pane; pane splitting returns the new pane.

## Create and run a background tab

Create a tab in the caller's workspace, preserve the working directory, and keep focus unchanged:

```bash
herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd "$PWD" --no-focus
herdr pane process-info --pane <root-pane-id>
herdr pane run <root-pane-id> "<command>"
```

Read the tab and root pane IDs from the creation response. A shell-ready process snapshot has a `shell_pid` that also appears as a foreground-process `pid`; create a fresh tab when that invariant is absent.

When the user requests a split or tightly coupled processes need to remain visible together, inspect the target pane's geometry and split right or down:

```bash
herdr pane layout --pane <pane-id>
herdr pane split --pane <pane-id> --direction right --cwd "$PWD" --no-focus
```

Read the new pane ID from the split response. Use `down` when it produces the more usable layout.

Bind readiness to this launch. Prefer a direct health probe. For terminal output, use a fresh pane and a line-anchored regex; when a wrapper emits readiness, generate a per-launch token and print it as its own line only after the health check succeeds:

```bash
herdr pane wait-output <pane-id> --regex '^<unique-ready-line>$' --timeout <milliseconds>
herdr pane read <pane-id> --source recent-unwrapped --lines 120
```

`wait-output` checks the existing snapshot before polling. Use `--match` when an intentional substring match is sufficient, and `--raw` when ANSI escapes belong in the match.

## Read pane and agent output

Read sources:

- `visible`: rendered viewport;
- `recent`: rendered output with soft wraps;
- `recent-unwrapped`: logs and transcripts with soft wraps joined;
- `detection`: bottom-buffer text used for agent detection.

Use `--format ansi` when terminal styling is evidence.

For a recognized idle agent at the bottom of its transcript, text reads from `recent` or `recent-unwrapped` automatically collect alternate-screen history when the requested line count exceeds the visible screen, then restore the viewport. The same behavior applies to `pane read` when that pane contains the agent. It remains passive for `visible`, `detection`, or ANSI reads; waits and subscriptions; manually scrolled agents; direct attachments; and applications without mouse-wheel support. An explicit agent history read can return `agent_not_idle` while the agent is working, blocked, or unknown.

Socket/API read results include `truncated`; ordinary `herdr pane read` and `herdr agent read` print text without that field. If automatic collection is unavailable or completeness remains uncertain, ask the agent to write the response to a temporary Markdown file and read that file.

## Start and control an agent

`agent start` needs an existing pane at an interactive shell prompt and returns after the new agent is ready. Settle an existing agent before submitting another turn:

```bash
herdr agent start <name> --kind <kind> --pane <pane-id>
herdr agent wait <name> --timeout <milliseconds>
herdr agent prompt <name> "<prompt>" --wait --timeout <milliseconds>
herdr agent get <name>
herdr agent read <name> --source recent-unwrapped --lines 120
```

Pass native agent arguments after `--`. `working` is busy and excluded from the default settle. A normal wait settles on `idle`, `done`, or `blocked`; `idle` and `done` are both ready, while `done` means the tab has not been seen since background work finished. Focusing the tab marks it seen; CLI reads do not. Inspect and resolve `blocked` before prompting. Use `--until` only for an exact state. Treat `unknown` as uncertain.

`agent prompt --wait` matches the first settled state observed after submission, not a specific turn. If the agent was already working, that turn's completion may satisfy the wait.

For a prompt submitted from a non-working state, Herdr requires a lifecycle change within five seconds. Otherwise it returns `agent_prompt_stalled`; a shorter `--timeout` can return `timeout` first. Prompt consumption remains unproven after either error. Herdr supplies its own text-to-Enter delay. Use `herdr agent send-keys <target> esc` or `ctrl+c` for intentional UI control.

## Move and retire sidecars

`pane move` changes focus by default. Pass `--no-focus`, then replace the old target with `.result.move_result.pane.pane_id`. A cross-workspace move can also close an emptied source tab or workspace. The reported `previous_pane_id` resolves only through the moved process's inherited caller context; do not use it as a general target.

Retire an owned sidecar through the foreground process's normal shutdown path, then poll `pane process-info --pane <pane-id>` with a finite deadline until the shell PID is foreground. If the deadline expires, inspect the process and leave the pane open until the user explicitly approves force termination. Refresh the ledger from the resulting layout because closing the last pane or tab can collapse its enclosing tab or workspace. In a worktree group, `pane close` can return `confirmation_required`; keep the pane open until the user explicitly confirms closing the owning workspace or group.

For worktree removal, resolve the workspace with `herdr worktree list` and verify its checkout path and branch. Run removal without `--force`. If Herdr reports a dirty checkout, inspect its Git status and obtain an explicit discard decision before force-removing it.

## CLI boundaries

Timeouts bound each wait; they do not prove task failure. Use a documented or previously observed startup or turn bound when available. Otherwise start with 30 seconds, inspect output when it expires, and extend only while output shows active startup or work.

CLI syntax errors exit with status 2. Server errors are JSON on stderr with status 1. `server_not_running` means no live server is available at the selected socket; treat it as a session-level failure, not a pane-local failure.
