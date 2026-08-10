---
name: model-routing
description: Route delegated model portfolios. Use when selecting models for delegated roles, structuring paired review and synthesis, or adding family diversity to frontend work and alternative implementations.
---

# Model Routing

Route a **portfolio**: an OpenAI primary lane supplies the capability baseline; a GLM diversity lane supplies an independent perspective. Plan every role before delegation.

## 1. Classify the roles

Assign each role exactly one route class:

- **Throughput** — value comes from breadth, attempts are independent, and a weak result is cheap to discard.
- **Routine** — correctness, coherence, or sustained reasoning matters, including difficult first attempts.
- **Reviewer** — independently assess work against one review axis.
- **Synthesis** — consolidate completed review reports without performing another review.

Mark these diversity triggers where they apply:

- **Frontend** — visual direction, interaction design, composition, or polish.
- **Alternative candidate** — a competing approach, implementation, interface proposal, design, or prototype.

Routine is the default. Route depth-dependent work as Routine regardless of cost. High-stakes work requires explicit review axes, paired OpenAI and GLM coverage on each axis, and a separate Synthesis role.

This step is complete when every role has one route class, every Frontend and Alternative candidate is marked, and every high-stakes task has explicit review axes and a Synthesis role.

## 2. Route the OpenAI lane

Use these starting routes:

- **Throughput:** `openai-codex/gpt-5.6-luna:xhigh`
- **Routine:** `openai-codex/gpt-5.6-sol:high`
- **Reviewer:** `openai-codex/gpt-5.6-sol:high`
- **Synthesis:** `openai-codex/gpt-5.6-sol:medium`

Sol `xhigh` and `max` are escalation routes. Use Sol `xhigh` after a Sol `high` attempt produces concrete evidence that its reasoning is insufficient for the same task. Use Sol `max` after Sol `xhigh` also proves insufficient. Evidence follows the task across delegations.

When OpenAI is unavailable, substitute `zai/glm-5.2:max` for each affected OpenAI role and record the substitution. Preserve the portfolio's roles when a subscription pool is temporarily exhausted.

When comparing models or revising this policy, read [`MODEL-PROFILES.csv`](MODEL-PROFILES.csv) and [`BENCHMARK-METHODOLOGY.md`](BENCHMARK-METHODOLOGY.md) for metrics, cost semantics, effort aliases, subscription facts, provenance, and refresh instructions. Runtime routing follows the routes and escalation sequence above.

This step is complete when every OpenAI-lane role has an exact model and effort, or an explicitly mapped workflow tier, and every fallback is recorded.

## 3. Add the GLM diversity lane

Route every GLM role to `zai/glm-5.2:max`:

- **Review:** pair each OpenAI Reviewer with a GLM Reviewer on the same axis.
- **Code review:** invoke `$code-review` twice without modifying it—once with all reviewers routed to Sol `high` and once with all reviewers routed to GLM-5.2 `max`.
- **Frontend:** add a GLM second opinion on design taste and execution.
- **Alternatives:** when the design path is unclear or competing approaches could expose useful tradeoffs, route at least one candidate through GLM.

Use available Z.ai subscription capacity proactively; a plausible benefit from diversity is enough to add the lane. Preserve the OpenAI lane.

For alternative approaches, the delegating agent returns one recommended result synthesized from both families. After paired reviews, a separate Sol `medium` Synthesis agent consolidates same-axis findings across families, preserves disagreements and provenance, and keeps different review axes separate.

When GLM is unavailable, retain the OpenAI roles and record the unavailable tool or quota.

This step is complete when every review axis, Frontend role, and Alternative candidate has the required GLM coverage or a concrete availability reason, and every completed paired review has a Sol `medium` Synthesis agent or a recorded fallback.
