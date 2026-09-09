---
name: pastlight-agents-pointer
description: Add the concise Pastlight pointer to a project's AGENTS.md.
disable-model-invocation: true
---

# Pastlight AGENTS.md pointer

Write the canonical snippet below into a project's agent instructions so its agents know when and how to search Pastlight.

## Precondition

The pointer describes an installed tool, not a setup step. Add it only where agents run Pi with Pastlight installed. Otherwise, point the user to the Pastlight installation instructions.

Pastlight uses these paths:

- Configuration: `${XDG_CONFIG_HOME:-$HOME/.config}/pastlight/recall.json`
- Recall data: `${XDG_DATA_HOME:-$HOME/.local/share}/pastlight/recall`
- Models: `${XDG_DATA_HOME:-$HOME/.local/share}/pastlight/models`
- Logs: `${XDG_STATE_HOME:-$HOME/.local/state}/pastlight/logs`

Pi still owns session discovery and stores sessions in its existing location. Pastlight does not move Pi sessions.

## Canonical snippet

Insert this block verbatim:

```md
## Session recall

Use `search_agent_session_history` when a task depends on past agent conversations, decisions, or command output absent from the current context. Set `query` to what you need to find. `scope` defaults to `project`. Use `global` to search every indexed project. `search_mode` defaults to `index`. Set `search_mode` to `source` only when you need complete original tool results, command output, or omitted payloads. Source mode scans session files and is slow. `max_results` defaults to 5 and cannot exceed 10. Each result cites its source session path and line range. The tool is read-only. Run `pastlight index` to refresh the index. Run `pastlight index --rebuild` only after two separate explicit approvals. Get an initial approval to rebuild. Then state that you are about to run it and get a separate confirmation. A full rebuild can exceed 12 hours.
```

The snippet is the single source of truth for this guidance. Reproduce it whole so a behavior change remains a one-place edit and every copy stays findable.

## Placement

1. Read the agent-instruction file used by the target repository. Use `AGENTS.md`, or `CLAUDE.md` where that is the convention.
2. Replace existing session-recall guidance with the canonical snippet. Keep one copy.
3. Add the block as its own section beside other tool or environment notes.
4. Put project-specific additions outside the canonical block so the canonical text stays searchable.

Complete when the file contains exactly one copy of the canonical snippet and no other session-recall guidance.
