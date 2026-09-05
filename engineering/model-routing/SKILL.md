---
name: model-routing
description: Route delegated model portfolios across independent provider and subscription pools. Use when selecting models for delegated roles, planning multi-family review and synthesis, handling quota pressure, or adding family diversity to frontend work, alternative implementations, debugging, and adversarial review.
---

# Model routing

Route a portfolio. OpenAI supplies the capability baseline, GLM supplies broad family diversity, and Grok supplies implementation, debugging, and adversarial diversity. The parent chooses a model for each launch. Keep ticket role configurations model-neutral.

## 1. Classify the roles

Assign each role exactly one route class:

- **Throughput**: breadth matters, attempts are independent, and a weak result is cheap to discard.
- **Routine**: correctness, coherence, or sustained reasoning matters, including difficult first attempts.
- **Reviewer**: independently assess work against one review axis.
- **Synthesis**: consolidate completed review reports without performing another review.

Mark these diversity triggers where they apply:

- **Frontend**: visual direction, interaction design, composition, or polish.
- **Alternative candidate**: a competing approach, implementation, interface proposal, design, or prototype.
- **Grok diversification**: a diagnosis remains uncertain or a fix failed, a competing implementation could expose a material tradeoff, or correlated OpenAI and GLM assumptions would be costly.
- **Adversarial review**: failure-oriented review, debugging, race or concurrency analysis, assumption challenge, or a merge gate.

Routine is the default. Route depth-dependent work as Routine regardless of cost. For high-stakes work, define at least these independent axes:

- **Standards**: repository guidance, engineering rules, safety constraints, and maintainability.
- **Spec**: the user contract, acceptance criteria, and required behavior.

Add narrower axes when the change needs them. Each required axis gets independent OpenAI and GLM coverage. Assign Grok to the highest-risk axis, then give the completed reports to a separate Synthesis role.

Record the role, axis, requested and resolved model, model family, provider, account, pool, runtime, and any substitution. Judge findings by evidence. Do not use majority voting. Two routes from the same model family still count as one family after a fallback.

This step is complete when every role has a route class, every diversity trigger is marked, every high-stakes task has Standards and Spec coverage plus its highest-risk Grok axis, and the provenance fields are ready to capture at launch.

## 2. Check capacity before fanout

Before launching a fanout, collect one observation for every candidate access pool. Preserve the source-reported capacity state or remaining value. Each observation also contains:

- `provider`
- `account`
- `pool`
- `window`
- `resetAt`
- `observedAt`
- `source`

Use an opaque account label, not credentials. Accept observations supplied by the caller or a local profile. The policy does not require a particular collection tool. Preserve `unknown` values rather than inventing them.

An observation establishes spare capacity only when its source is current under the caller or profile's freshness rule and explicitly reports room in the named window. Unknown, stale, or unavailable observations do not establish spare capacity. Record retrieval time separately when source observation time is unknown. Missing telemetry alone need not block useful work: use an otherwise authorized capable route with bounded concurrency, without claiming headroom or clearing known exhaustion. A model listing proves catalog presence, not authentication, quota, or billing eligibility.

Keep pools separate even when names overlap:

- OpenAI Codex subscription, direct OpenAI pay-as-you-go, and Cursor-hosted OpenAI models;
- Z.ai coding subscription, direct Z.ai pay-as-you-go, and Cursor-hosted GLM models;
- Cursor's first-party Grok pool and its third-party Fable pool.

Token counts, API-price estimates, and per-run currency telemetry do not report remaining quota. A zero charge may have several causes. Shared concurrent consumption also means a fresh capacity observation cannot reserve future work.

Schedule required roles before optional fanout. Under pressure, reduce optional alternatives and redundant passes. Route required work through another already-authorized, capable pool while preserving its axis and family requirement. The explicit-user Fable rule below still applies; fallback never authorizes Fable. Never activate overage, buy credit, upgrade a plan, or enable a fallback execution mode to complete the route. If no allowed route can perform a required role, report that role as blocked with its latest capacity observation instead of silently dropping it.

After a real quota failure, capture the same provider, account, pool, window, reset, observation time, and source fields from the failure evidence. Replan work that has not launched; do not treat earlier capacity as a reservation.

This step is complete when every candidate pool has a source observation or an explicit unknown state with retrieval time, required roles are scheduled ahead of optional fanout, and every non-spare or blocked route has an explicit reason.

## 3. Route the OpenAI lane

Use these starting routes:

- **Throughput:** `openai-codex/gpt-5.6-luna:xhigh`
- **Routine:** `openai-codex/gpt-5.6-sol:high`
- **Reviewer:** `openai-codex/gpt-5.6-sol:high`
- **Synthesis:** `openai-codex/gpt-5.6-sol:medium`

Sol `xhigh` and `max` are escalation routes. Use Sol `xhigh` after a Sol `high` attempt produces concrete evidence that its reasoning is insufficient for the same task. Use Sol `max` after Sol `xhigh` also proves insufficient. Evidence follows the task across delegations.

When an OpenAI route cannot launch, use an already-authorized capable pool. `zai/glm-5.3:max` is the default capability fallback. Record the substitution, and do not count it as a second family when the portfolio already has GLM coverage. Use an available authorized family such as Grok for a still-required diversity role; otherwise report that role as blocked.

When comparing models or revising this policy, read [`MODEL-PROFILES.csv`](MODEL-PROFILES.csv) and [`BENCHMARK-METHODOLOGY.md`](BENCHMARK-METHODOLOGY.md) for metrics, cost semantics, effort aliases, access-snapshot limits, and provenance. Runtime routing follows this file rather than historical access labels in the CSV.

This step is complete when every OpenAI-lane role has an exact model and effort, or a recorded substitution, and any lost family coverage has a replacement or blocked-role report.

## 4. Add the GLM diversity lane

Route GLM roles through Pi's normal model access to `zai/glm-5.3:max`:

- **Review:** pair each OpenAI Reviewer with a GLM Reviewer on the same axis.
- **Code review:** invoke `$code-review` twice without modifying it. The parent routes all reviewers to Sol `high` for one run and GLM-5.3 `max` for the other.
- **Frontend:** add a GLM pass on design taste and execution.
- **Alternatives:** when competing approaches could expose useful tradeoffs, route at least one candidate through GLM.

Use observed spare Z.ai coding-subscription capacity proactively. Preserve the OpenAI lane. For alternatives, the parent returns one recommendation synthesized from the independent candidates. Frontend and alternative passes may be optional; Standards and Spec coverage is required for high-stakes work.

When the GLM route cannot launch, use an already-authorized capable route from another non-OpenAI family and record the substitution. If none is available, keep the other roles and report the GLM diversity role as blocked.

This step is complete when every required review axis has GLM or another non-OpenAI family, every selected Frontend or Alternative role has its planned coverage, and every substitution preserves family provenance.

## 5. Add the Grok diversification lane

Use `cursor/grok-4.6:slow:xhigh` through the existing Pi Cursor provider. `:slow` selects the non-Fast Grok profile and `:xhigh` selects reasoning effort. This is the normal Grok route. Use observed spare capacity in Cursor's first-party Grok pool proactively for:

- every role marked with the Grok diversification trigger;
- the highest-risk review axis on high-stakes work;
- adversarial review, especially race, concurrency, resource-lifetime, and merge-safety analysis;
- a final challenge when correlated OpenAI and GLM assumptions would be costly.

The provider runs a Cursor SDK agent loop, so record the requested and resolved provider, model, runtime, and tool contract with the result. Do not infer ordinary Pi tool behavior from the provider name.

The standalone Cursor CLI skills are historical explicit routes, not automatic fallbacks. Invoke `$grok-worker` only when the user explicitly requests its CLI worker route. Invoke `$herdr-grok-review` only when the user explicitly requests its Herdr probe-capable CLI review. If the normal Cursor provider route is unavailable, use another allowed pool or report the Grok role as blocked. Do not switch to a CLI route on your own.

After multi-family reviews, a separate Sol `medium` Synthesis agent consolidates findings on the same axis, preserves disagreements and route provenance, and keeps different axes separate.

This step is complete when every required Grok role has a captured provider result or a blocked-role report, and every completed multi-family review has a separate Synthesis result or recorded substitution.

## 6. Honor explicit Fable requests

Fable is user-requested only. When the user explicitly requests Fable, route through the Cursor third-party pool to one of the current Fable 5.1 models:

- `cursor/claude-fable-5-1@300k`
- `cursor/claude-fable-5-1@1m`

Choose the context size from the task's input requirement. Never select Fable autonomously or use it as a fallback for OpenAI, GLM, or Grok. Opus has no active route in this policy. Keep Fable capacity separate from Cursor's first-party Grok capacity.

This step is complete when an explicit user request authorizes Fable and the parent records its selected Fable 5.1 context route and third-party pool observation, or no Fable role exists.
