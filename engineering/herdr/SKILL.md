---
name: herdr
description: "Use Herdr sidecars for persistent or continuously observable work when `HERDR_ENV=1`. Also use when asked to control panes, layout, workspaces, or coding agents through Herdr."
---

# Herdr

Run persistent, observable work as a Herdr **sidecar**, independent of the main agent turn.

## 1. Confirm the session

Before controlling Herdr, check `test "${HERDR_ENV:-}" = 1`. Under `HERDR_ENV=1`, prefer native `herdr_layout`, `herdr_pane`, and `herdr_agent` tools when available. In other sessions, use ordinary execution tools.

Before issuing any Herdr CLI control command, read [`CLI-REFERENCE.md`](CLI-REFERENCE.md).

This step is complete when the available control surface and caller context are known.

## 2. Choose the execution surface

- Keep short, bounded commands in the ordinary command tool.
- Proactively move persistent or continuously observable work into a background pane.
- Use the pane surface for shells and ordinary processes. Use the agent surface for a recognized interactive coding agent.

This step is complete when each planned command is assigned to ordinary, pane, or agent execution.

## 3. Create a sidecar

Absent an explicit topology request, create a fresh tab in the caller's current workspace and working directory. Preserve UI focus. Use a pane split when the user requests one or tightly coupled processes need to remain visible together.

Read the new tab and root pane IDs from the creation response. Target the pane ID thereafter. Reuse an existing pane only after confirming its shell is the foreground process.

This step is complete when a shell-ready pane exists in the intended topology and the caller's focus is unchanged.

## 4. Run and observe

Start the command in the shell-ready pane. Bind readiness to the current launch: prefer a direct health signal, or use a unique exact-line marker emitted only after readiness. For bounded jobs, wait for completion or another expected marker. Read logs from unwrapped recent output.

Keep the main turn available for other work while the sidecar runs.

This step is complete when a bounded job completes or fails, or a persistent sidecar produces readiness evidence or fails explicitly.

## Coding-agent sidecars

When the work requires a recognized coding agent, create its shell pane first. Start the agent through the agent surface. Before prompting an existing agent, wait for it to settle; treat `idle` and `done` as ready, inspect `blocked`, and investigate `unknown`. Prompt atomically, wait for the next settled state, then capture the response. After a stalled prompt, read the agent and establish whether it consumed the prompt before retrying.

This step is complete when `idle` or `done` is paired with a captured response, or when a blocked input or failure is clear. A settled lifecycle state alone does not prove that the intended response was captured.

## Handoff and safety

- Maintain a ledger of sidecars created or moved, updating each opaque pane ID from mutation responses so targeting remains independent of UI focus.
- Keep useful services and monitors running. At handoff, report each sidecar's pane ID, command, observed state or evidence, and whether it remains active.
- Retire an owned sidecar through the foreground process's normal shutdown path, wait for the shell to return, then close its pane and refresh the ledger.
- Keep server and session changes on a live-handoff or confirmed graceful-shutdown path. `herdr update --handoff` attempts to preserve live panes; if handoff is unavailable or fails, obtain explicit confirmation before `herdr server stop` or any action that can end pane processes. Manage the main Herdr process through Herdr lifecycle commands rather than host process kills.

Handoff is complete when every sidecar is accounted for and every still-useful persistent process remains running.

When Herdr is upgraded or this guidance appears stale, read [`MAINTENANCE.md`](MAINTENANCE.md) before changing the skill.
