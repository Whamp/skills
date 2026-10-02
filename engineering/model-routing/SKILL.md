---
name: model-routing
description: Select delegated models or recover failed routes while preserving permissions, capacity limits, and review independence.
---

# Model routing

The parent chooses each child's model explicitly; children need not load this policy.

1. **Policy.** Read the caller's private routing profile for preferred models, task-appropriate thinking, authorized accounts, and fallback rules. Keep permission, availability, and task fit separate: a catalog entry or role assignment is not spending authorization. Explicit-request-only routes stay excluded from automatic selection, including parent-model inheritance and failure recovery.
2. **Role.** Read the requested workflow role from the caller's current configuration, not a remembered table. Use its selector and thinking suffix unless the caller's policy, capacity, or current instructions require a substitution. Without a matching role, use the profile's task defaults. Verify the exact selector and supported thinking level, then pass the model explicitly at launch.
3. **Capacity.** Before substantial delegation, check or reuse recent observations for candidate pools. Respect every limiting window, concurrency, shared context budget, and reservation. Unknown telemetry permits bounded use of an authorized route; it neither proves headroom nor clears known exhaustion. Different models can share one pool; different providers can serve one family.
4. **Recovery.** Use the profile's eligible backups and diversifiers. Skip exhausted pools, not just the failed model. Preserve required tools, runtime, context, write authority, isolation, and review axes. Missing child tools are not model unavailability. Retain completed work and report substitutions. Ask when no permitted capable route satisfies the task; paid overage and approval boundaries remain closed.
5. **Independence.** Preserve the workflow's required family coverage. Another provider serving the implementer's family is not an independent reviewer. Capacity pressure does not authorize silently dropping or duplicating a required review family.

## Pstack roles

Read `pstack/models.json` under `PI_CODING_AGENT_DIR` (default `~/.pi/agent`) and use the v2 `roles` map even when Poteto Mode or `skillsEnabled` is off. Preserve selector suffixes, list order, and duplicate entries except for policy-governed substitutions.

Follow the workflow's cardinality: `single` launches one child; `repeat` reuses one selector; `fanout` launches one child per list entry; `pick-one` chooses one listed selector. Lists are not interchangeable fallback chains.

A missing role, `inherit-parent`, or `auto` resolves to the parent model explicitly, subject to the same permission and capacity rules. If JSON is absent, check `pstack-models.md` in the same agent directory; absent configuration uses Pstack's inherit-parent default. For legacy or invalid configuration, inspect `/pstack status` and resolve diagnostics before delegation rather than guessing or rewriting assignments.

Complete when every child has an explicit eligible selector, supported thinking, and the required coverage, or the unmet requirement has been reported.
