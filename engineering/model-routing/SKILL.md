---
name: model-routing
description: Route delegated model portfolios across independent provider and subscription pools. Use when selecting models for delegated roles, planning multi-family review and synthesis, handling quota pressure, watching long-running work, or adding family diversity to implementation, debugging, visual work, and adversarial review.
---

# Model routing

Route a portfolio. Sol is the dependable default. Luna, GLM-5.3-Flash, and a caller-configured local Flash-class model supply inexpensive volume. GLM-5.3 and Grok supply independent review families. Astra and Fable supply escalation capacity. The parent chooses the model, authority, tools, context, and isolation for each child.

## 1. Classify each role

Assign each role one route class:

- **Throughput**: breadth matters, attempts are independent, and a weak result is cheap to discard.
- **Routine**: correctness, coherence, or sustained reasoning matters, including difficult first attempts.
- **Watcher**: observe a long-running process and report completion, stalls, or named anomalies.
- **Reviewer**: independently assess work against one review axis.
- **Synthesis**: consolidate completed reports without repeating their reviews.
- **Escalation**: attack a difficult unresolved problem or a task suited to a specialist model.

Mark these triggers when they apply:

- **Vision**: image, video frame, rendered interface, computer-use, or 3D evidence matters.
- **Alternative candidate**: a competing approach, implementation, interface, or prototype could expose a useful tradeoff.
- **Grok diversification**: diagnosis remains uncertain, a fix failed, or correlated OpenAI and GLM assumptions would be costly.
- **Adversarial review**: failure-oriented debugging, race or concurrency analysis, assumption challenge, or a merge gate.

Routine is the default. Model choice does not imply child authority. The parent separately decides whether a child may edit, which tools it receives, whether it needs a worktree, and what validation it must return.

For high-stakes work, define independent **Standards** and **Spec** axes plus narrower risk axes where needed. Give each required axis independent OpenAI and non-OpenAI coverage. Assign Grok to the highest-risk axis when its trigger applies. Judge findings by evidence, not votes.

Record the role, axis, requested and resolved model, family, provider, account, pool, runtime, and any substitution. Two provider routes from one model family still count as one family.

This step is complete when every child has one route class, relevant triggers are marked, high-stakes axes have independent family coverage, and authority is explicit rather than inferred from the model.

## 2. Check capacity before substantial fanout

Collect one observation for every candidate access pool. Preserve the source-reported capacity state or remaining value. Each observation includes:

- `provider`
- `account`
- `pool`
- `window`
- `resetAt`
- `observedAt`
- `source`

Also preserve caller-profile concurrency limits, context budgets, and model-specific quota multipliers when supplied. Use an opaque account label, not credentials. Preserve `unknown` rather than inventing a value.

An observation establishes spare capacity only when its source is current under the caller's freshness rule and explicitly reports room. Unknown or stale telemetry permits bounded use of an otherwise authorized route, but does not prove headroom or clear known exhaustion. A model listing proves catalog presence, not authentication, quota, or billing eligibility.

Keep distinct pools separate:

- OpenAI Codex subscription, direct OpenAI pay-as-you-go, and Cursor-hosted OpenAI models;
- Z.ai coding subscription, direct Z.ai pay-as-you-go, and Cursor-hosted GLM models;
- Cursor Models for Grok and Cursor Other Models for Fable;
- local inference resources described by the caller's profile.

Token counts, API-price estimates, and per-run currency telemetry do not report remaining quota. Shared consumption also means a capacity observation cannot reserve future work.

Schedule required roles before optional breadth. Under pressure, reduce redundant passes and route required work through another authorized, capable pool while preserving its axis and family requirement. Never activate overage, buy credit, upgrade a plan, or enable a different execution runtime to obtain capacity. Report an irreplaceable role as blocked.

After a quota or local-resource failure, capture the failure evidence and replan work that has not launched.

This step is complete when every candidate pool has a current observation or explicit unknown state, local resource limits are known or marked unknown, and every substitution or blocked route has a reason.

## 3. Route the core OpenAI lane

Use these starting routes:

- **Routine:** `openai-codex/gpt-5.6-sol:high`
- **Reviewer:** `openai-codex/gpt-5.6-sol:high`
- **Synthesis:** `openai-codex/gpt-5.6-sol:medium`
- **Throughput:** `openai-codex/gpt-5.6-luna:xhigh`
- **Watcher:** `openai-codex/gpt-5.6-luna:low`

Use Luna `max` for difficult bounded throughput work when the OpenAI pool has room. Use Luna `medium` instead of `low` when a watcher must interpret behavior across components rather than recognize named signals.

Sol `xhigh` and `max` are escalation routes. Raise effort only after the preceding level produces concrete evidence that its reasoning was insufficient for the same task. Evidence follows the task across delegations.

When an OpenAI route cannot launch, use another authorized capable pool. Record the substitution and preserve required family diversity.

When comparing models or changing policy, read [`MODEL-PROFILES.csv`](MODEL-PROFILES.csv) and [`BENCHMARK-METHODOLOGY.md`](BENCHMARK-METHODOLOGY.md). Runtime routing follows this file rather than historical access labels in the CSV.

This step is complete when every core role has an exact route or recorded substitution and lost family coverage has a replacement or blocked-role report.

## 4. Add inexpensive volume

Mix these Throughput and Watcher routes according to capability, quota, local resources, and desired family diversity:

- `openai-codex/gpt-5.6-luna:xhigh` for capable inexpensive work, or Luna `max` for harder bounded work.
- `zai/glm-5.3-flash:max` for high-volume text or vision work. Require evidence for claims because weak results are cheap to discard.
- The caller-profile local Flash-class route for general implementation, review, vision, investigation, and watching. Local inference is also useful when inputs contain secrets.

Treat a capable local Flash-class model as a general-purpose peer of GLM-5.3-Flash, not a privacy-only specialist. Choose child tools from the task. Local inference does not by itself prevent a tool from sending supplied content elsewhere.

For local fanout, obey the caller profile's concurrency and aggregate context budget. Prefer tested operating points over the largest technically accepted fanout. For Z.ai, preserve any profile-reported model concurrency and quota multiplier, but launch only as many independent attempts as the task can use.

A Watcher launch states the process or log source, expected healthy signals, anomalies, deadline, and notification condition. Run it asynchronously. Use Luna `low`, Luna `medium`, GLM-5.3-Flash, or the local Flash-class route according to interpretation difficulty, quota, and data locality.

This step is complete when each selected volume pool has an assigned launch or explicit exclusion reason, each local launch fits its resource budget, and each watcher has explicit signals and a deadline.

## 5. Add independent families

Use `zai/glm-5.3:max` as the default non-OpenAI Reviewer and alternative-candidate route. For high-stakes work, pair it with the OpenAI Reviewer on the same axis. The parent may substitute GLM-5.3-Flash or the local Flash-class family when the role remains within that model's demonstrated capability, but records the change in strength and family.

Use `cursor/grok-4.6:slow:high` for:

- every role marked with the Grok diversification trigger;
- the highest-risk review axis on high-stakes work;
- adversarial race, concurrency, resource-lifetime, and merge-safety analysis;
- a final challenge when correlated assumptions would be costly.

`:slow` selects the non-Fast Cursor profile. `:high` selects reasoning effort. Keep Cursor Models capacity separate from Cursor Other Models capacity.

After multi-family review, route a separate Sol `medium` Synthesis child. It preserves disagreements and route provenance rather than resolving findings by vote.

This step is complete when every required review axis has independent family evidence, each triggered Grok role has a result or blocked-role report, and completed multi-family reviews have separate synthesis.

## 6. Escalate with Astra and Fable

The parent may invoke either model automatically when task difficulty or fit justifies it. Escalation does not imply read-only work.

Use `openai-codex/gpt-6-astra:high` for stalled reasoning, independent ideas, and visual, computer-use, or 3D work. Treat its output as another evidence-bearing candidate. The parent decides whether Astra investigates, reviews, or implements.

Use `cursor/claude-fable-5-1@300k:medium` for the hardest unresolved work. Medium is the default and may be selected automatically. Higher Fable effort requires a special caller request. Fable is neither routine review coverage nor a silent fallback for an unavailable pool.

Give Fable adequate working context:

- Use forked context when the current conversation contains relevant evidence and may be shared with the provider.
- Use fresh context when the conversation is noisy, oversized, or contains material that should not be sent to the provider.
- Preserve primary artifacts and paths. Let Fable inspect the repository and adjacent causes instead of compressing the task into the parent's current theory.

Keep Fable's Cursor Other Models capacity separate from Grok's Cursor Models capacity. If the pool lacks capacity, report the escalation as unavailable.

Opus and other catalog models have no active route. Catalog presence does not add them to policy.

This step is complete when each escalation records why the model fits, Fable uses the 300K Medium route unless specially requested otherwise, and the child receives enough context and authority for its assigned work.

## 7. Launch Cursor models through Pi

Before launching any `cursor/*` route, read [`CURSOR-SUBAGENTS.md`](CURSOR-SUBAGENTS.md). It gives the exact Pi child shape and distinguishes it from the separate Cursor CLI agents.

This step is complete when each Cursor child uses a normal Pi role plus an exact `cursor/*` model selector, and its result records the resolved provider, model, runtime, and tool contract.
