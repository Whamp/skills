---
name: model-routing
description: Choose delegated models using task capability, subscription permissions, live availability, and quota priorities. Use when selecting reviewers or workers, handling quota pressure or launch failures, or planning multi-family review.
---

# Model routing

Choose a capable route from the pools the caller permits. Start ordinary work with Luna Max or GLM-5.3-Flash, not the most expensive model. Model preferences never grant spending permission or make one provider indispensable.

## 1. Establish the routing contract

Read the caller's subscription profile and current task instructions before selecting models. Keep these decisions separate:

- **Permission:** which provider, account, pool, model, and runtime may be used, including any user-message-only approval requirement.
- **Availability:** authentication, supported selector, executable child and tools, quota windows, and local service readiness.
- **Task fit:** required capabilities, review axes, family independence, context, and write authority.
- **Preference:** pools to preserve or consume first, quota efficiency, reset order, and model strengths.

Apply permission and task requirements first. Exclude known-unavailable routes. Rank the remaining routes by the caller's spending priorities, then quota efficiency and task fit. Use reset order as a tie-breaker among interchangeable routes, not as an override of a preserve-pool instruction.

A role table, skill, project instruction, automation workflow, catalog entry, or escalation recommendation is not an explicit user message. When a pool requires that approval, record the user's authorizing message and its scope before launching. A request to improve routing policy is not permission to exercise restricted routes.

Assign each child a role: Routine, Throughput, Watcher, Reviewer, Synthesis, or Escalation. Routine includes well-specified implementation. Mark vision or adversarial analysis when needed, but do not turn a model's specialty into a mandatory model assignment.

Complete when each planned child has a task contract and an eligible route, or a specific unsatisfied requirement.

## 2. Check the relevant pools

Before substantial delegation, collect or reuse current observations for candidate pools using the caller's usage tool and freshness rules. Record provider, opaque account label, pool, window, used or remaining value and unit, reset time, observation time, source, and uncertainty. Respect every known limiting window, concurrency cap, context budget, and model-specific quota multiplier.

Keep Codex separate from OpenAI API billing; Z.ai coding separate from direct API billing; direct xAI separate from Cursor; Cursor Models separate from Cursor Other Models and paid overage; Kimi Code separate from other Moonshot access; and local inference separate from subscription pools.

Unknown or stale telemetry permits bounded use of an otherwise authorized route. It does not prove headroom or clear known exhaustion. A model listing proves catalog presence, not authentication, capacity, or permission. API prices, session tokens, and zero-cost displays do not measure remaining subscription allowance.

Treat user-reported maintenance or reservation of a local service as unavailability for that work. Do not send review traffic to a model currently under test merely because its endpoint answers. A subscription scheduled for cancellation remains a temporary option only while active; record its end date as unknown when none was supplied and recheck before relying on it.

Do not hard-code transient percentages, maintenance states, or example spending priorities into durable policy. A nearly exhausted pool may still be the preferred pool to consume. Do not switch to a protected pool merely because it has a lower used percentage.

Absent a caller preference, use the earlier-resetting usable pool among routes with equivalent capability and required family coverage. If resets match, prefer the higher used percentage. An unknown reset does not outrank a known upcoming reset. Reorder after a reset or failure. Observations are not reservations against other sessions' consumption.

Complete when candidate pools have observations or explicit unknown states, and exclusions distinguish permission, quota, service, and runtime failures.

## 3. Choose the least costly capable route

These are starting preferences, conditional on steps 1 and 2, not required launches:

| Work | Starting routes | Escalation condition |
| --- | --- | --- |
| Well-specified implementation, investigation, bounded review, ordinary synthesis | `openai-codex/gpt-5.6-luna:max` or `zai/glm-5.3-flash:max` | Concrete complexity, unresolved ambiguity, or insufficient evidence from the first attempt |
| Independent throughput attempts | Luna `xhigh` or GLM-5.3-Flash `max` | Use Luna `max` when the bounded task needs more reasoning |
| Watcher | Luna `low` or `medium`, GLM-5.3-Flash, or an available local route | Interpretation across components rather than recognition of named signals |
| Difficult or high-stakes review | `zai/glm-5.3:max` or `openai-codex/gpt-5.6-sol:high` | Choose the family needed for independence and the pool the caller prefers |
| Alternative independent reviewer | Caller-authorized Kimi Code, Grok, or local family | Capability and availability fit the review axis |
| Unresolved hard reasoning or specialist visual work | `openai-codex/gpt-6-astra:high` | Explain why cheaper eligible routes are insufficient |

GLM-5.3-Flash is a routine worker and bounded reviewer, not just disposable volume. Luna Max is a routine OpenAI default, not just a throughput exception. Neither a Standards label nor a synthesis step automatically requires Sol. Keep Sol for ambiguous, contested, or high-stakes work that warrants it. Raise Sol to `xhigh` or `max` only after evidence that the preceding effort was insufficient for the same task.

Use the caller's exact Kimi Code selector when authorized. Kimi supplies an independent family and subscription pool; missing usage telemetry is unknown capacity, not exclusion. Do not infer its vision support, quota, or retirement date from its name.

A caller-configured local Flash-class model may implement, review, investigate, use supported vision, or watch logs. Obey its tested concurrency and aggregate context limits rather than treating free tokens as unlimited throughput. Local inference does not stop a child's tools from transmitting inputs elsewhere.

For watchers, specify the process or log source, healthy signals, anomalies, deadline, and notification condition. Use asynchronous execution when supported. Launch only as much optional breadth as the task can use. Schedule required work before optional breadth. Under quota pressure, reduce redundant passes before consuming a pool the caller wants to preserve.

Read [`MODEL-PROFILES.csv`](MODEL-PROFILES.csv) and [`BENCHMARK-METHODOLOGY.md`](BENCHMARK-METHODOLOGY.md) when comparing model evidence or revising policy. Benchmark prices and historical access labels do not authorize routes or establish subscription cost.

Complete when each child has an exact supported selector, a pool, and a task-based reason for any stronger route.

## 4. Preserve review independence without model lock-in

When running Standards and Spec reviews, use different families. The implementer's family must not be the only reviewing family. For high-stakes work, define the required risk axes and independent family coverage before launch. Preserve any explicit review contract; do not silently weaken it to fit capacity.

Grok is useful for adversarial reasoning, concurrency, resource lifetime, and challenging correlated assumptions. It is an option, not a required reviewer. GLM, Kimi, or another capable independent family can perform the same review axis. GLM-5.3 and GLM-5.3-Flash are one family; direct xAI and Cursor Grok are one family despite separate pools.

The standard Grok selectors are `xai/grok-4.6:high` and `cursor/grok-4.6:slow:high`. Verify selectors against the current runtime catalog rather than guessing suffix variations. Before any Cursor launch, read [`CURSOR-SUBAGENTS.md`](CURSOR-SUBAGENTS.md).

Consolidate completed reviews without rerunning them. The parent may synthesize; launch a separate synthesis child only when the review contract or report volume warrants it. Preserve disagreements and evidence rather than deciding by vote.

Complete when required axes and family coverage have evidence, or the precise missing requirement is reported. An unavailable preferred brand alone is not a missing requirement.

## 5. Recover launch failures within the permitted contract

Separate model or pool failures from child tool-profile failures. Inspect the installed delegation contract and executable agents. A missing tool in a reviewer profile does not show the selected model is unavailable. Use an existing compatible read-only role, or a supported profile adjustment within the task's authority, while preserving the review restrictions. Do not claim unsupported per-call tool overrides work.

After a quota, authentication, selector, local-resource, or runtime failure, record the evidence and replan only unlaunched or failed work. Retain completed reviews. Reapply steps 1 through 3 to the remaining permitted candidates and substitute without asking the user when the task contract remains satisfied. Record requested and resolved model, family, provider, pool, runtime, and reason.

Do not switch execution runtimes, activate overage, buy credit, upgrade plans, or cross an approval boundary to recover. Ask only when no permitted capable route can satisfy a required contract, or when the needed remedy itself requires user authority. State what remains blocked, not that the entire task failed because one route did.

Complete when work resumes through an eligible route or a concrete unmet requirement and exhausted alternatives are reported.

## 6. Gate restricted escalation before selection

Astra and Fable are capability options, not exceptions to permission rules. The caller profile decides whether either may be selected automatically. If the profile requires explicit user-message approval for Cursor API models, Fable remains excluded until that approval exists. Neither difficult work nor another document's recommendation supplies it.

When explicitly authorized and supported, the Fable starting selector is `cursor/claude-fable-5-1@300k:medium`. Higher effort needs a specific request. Keep its Cursor Other Models allowance separate from Grok's Cursor Models allowance. Provide primary artifacts and enough context to investigate beyond the parent's hypothesis; use fresh context when the conversation contains irrelevant or provider-restricted material.

Complete when any restricted escalation has approval evidence within scope, verified route eligibility, and a task-based reason. Otherwise use an eligible alternative.

Check policy changes against [ROUTING-CASES.md](ROUTING-CASES.md).
