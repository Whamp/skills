---
name: session-recap
description: Recover what we were doing, whether it is finished, and which questions remain open.
disable-model-invocation: true
license: MIT
---

# Session recap

Answer the user's reorientation request:

> Remind me what we were doing here. Did we finish, or do we have unresolved questions?

## Recover the state

1. Establish what "here" refers to from the current conversation and project context.
   Identify the user's goal, agreed scope, and most recent work.
   Complete when you can explain the objective and why it mattered in plain language.
2. Recover decisions, actions, and outcomes from the conversation and available project
   records. If context was compacted or interrupted, use the environment's history or
   memory tools to fill material gaps. Keep retrieval scoped to this task.
   Complete when you can distinguish planned work, attempted work, and confirmed results.
3. Verify completion claims against available evidence: checks, artifacts, repository
   state, or live task and PR status as appropriate. Separate implementation,
   verification, and delivery; code written is not necessarily tested, merged, or deployed.
   If evidence is unavailable or stale, label the affected claim unverified.
   Complete when each agreed deliverable is classified as complete, incomplete, or unverified.
4. Reconcile open questions against later decisions. Distinguish unresolved choices,
   blockers, unfinished work, and optional follow-ups. For each unresolved choice, state
   what needs deciding and give a recommendation when the evidence supports one.
   Complete when only genuinely outstanding items remain.

## Brief the user

Give a concise, self-contained recap for someone who has not read the underlying files:

- **What we were doing:** the goal and essential context.
- **Where we landed:** key decisions and confirmed results, with brief supporting evidence.
- **Are we finished?** a direct verdict: finished, partially finished, blocked, or unverified,
  and what that verdict covers.
- **Still open:** unresolved questions or remaining required work; say "None" when appropriate.
- **Next step:** the recommended action, who needs to act, or "No further action needed."

Use links for traceability, not as a substitute for explaining the state.
Keep optional improvements separate from requirements so they do not make completed work
appear unfinished. If the record cannot establish the state, explain the gap and the
smallest next check needed.

This is a recap, not authorization to resume implementation, change files, merge work,
or start background tasks. Finish when the user can understand the current state and
choose whether to continue.
