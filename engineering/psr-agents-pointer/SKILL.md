---
name: psr-agents-pointer
description: Add the concise pi-session-recall pointer to a project's AGENTS.md.
disable-model-invocation: true
---

# PSR AGENTS.md Pointer

Write the canonical snippet below into a project's agent instructions so every agent in that repository knows the `pi-session-recall` tool exists and when to reach for it.

## Precondition

The pointer describes an installed tool, not a setup step. Add it only where the reading agents run Pi with the pi-session-recall extension installed. If the extension is absent, point the user at the pi-session-recall README instead.

## Canonical snippet

Insert this block verbatim:

```md
## Session recall

Use the `pi-session-recall` tool when a task depends on past Pi conversations, decisions, or command output absent from current context. Scope defaults to the current project; pass scope `global` for cross-project evidence. Results cite session JSONL paths and line ranges; set `source` true only for complete raw payloads. The tool is read-only; standalone `psr index` runs refresh the index. Run `psr index --rebuild` only after the user approves twice — an initial explicit approval and a separate confirmation when you state you are about to run it. A full rebuild can exceed 12 hours.
```

The snippet is the single source of truth for this guidance. Reproduce it whole rather than paraphrasing: a behavior change stays a one-place edit here and a findable string in every consumer.

## Placement

1. Find the file agents actually read in the target repository — `AGENTS.md`, or `CLAUDE.md` where that is the convention. Read it fully first.
2. If session-recall guidance already exists anywhere in the file, replace it with the canonical snippet rather than adding a second copy. Duplicated guidance drifts.
3. Add the block as its own section alongside other tool or environment notes.
4. Keep any project-specific additions as separate lines outside the canonical block so the canonical text stays greppable.

Complete when the file contains exactly one copy of the canonical snippet and no other session-recall guidance.
