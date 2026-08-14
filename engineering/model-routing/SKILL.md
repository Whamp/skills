---
name: model-routing
description: Route delegated model portfolios across Pi/API and CLI-only access. Use when selecting models for delegated roles, structuring multi-family review and synthesis, or adding family diversity to frontend work, alternative implementations, debugging, and adversarial review.
---

# Model Routing

Route a **portfolio**: an OpenAI primary lane supplies the capability baseline, a GLM lane supplies general family diversity, and a Grok lane supplies implementation, debugging, and adversarial diversity. Plan every role before delegation.

## 1. Classify the roles

Assign each role exactly one route class:

- **Throughput** — value comes from breadth, attempts are independent, and a weak result is cheap to discard.
- **Routine** — correctness, coherence, or sustained reasoning matters, including difficult first attempts.
- **Reviewer** — independently assess work against one review axis.
- **Synthesis** — consolidate completed review reports without performing another review.

Mark these diversity triggers where they apply:

- **Frontend** — visual direction, interaction design, composition, or polish.
- **Alternative candidate** — a competing approach, implementation, interface proposal, design, or prototype.
- **Grok worker** — a diagnosis remains uncertain or a fix failed, a competing implementation could expose a material tradeoff, or correlated OpenAI and GLM assumptions would be costly.
- **Adversarial review** — failure-oriented review, debugging, race or concurrency analysis, assumption challenge, or a merge gate.

Routine is the default. Route depth-dependent work as Routine regardless of cost. High-stakes work requires explicit review axes, paired OpenAI and GLM coverage on each axis, a Grok adversarial pass on the highest-risk axis, and a separate Synthesis role.

This step is complete when every role has one route class, every diversity trigger is marked, and every high-stakes task has explicit review axes, Grok's highest-risk axis, and a Synthesis role.

## 2. Route the OpenAI lane

Use these starting routes:

- **Throughput:** `openai-codex/gpt-5.6-luna:xhigh`
- **Routine:** `openai-codex/gpt-5.6-sol:high`
- **Reviewer:** `openai-codex/gpt-5.6-sol:high`
- **Synthesis:** `openai-codex/gpt-5.6-sol:medium`

Sol `xhigh` and `max` are escalation routes. Use Sol `xhigh` after a Sol `high` attempt produces concrete evidence that its reasoning is insufficient for the same task. Use Sol `max` after Sol `xhigh` also proves insufficient. Evidence follows the task across delegations.

When OpenAI is unavailable, substitute `zai/glm-5.3:max` for each affected OpenAI role and record the substitution. Preserve the portfolio's roles when a subscription pool is temporarily exhausted.

When comparing models or revising this policy, read [`MODEL-PROFILES.csv`](MODEL-PROFILES.csv) and [`BENCHMARK-METHODOLOGY.md`](BENCHMARK-METHODOLOGY.md) for metrics, cost semantics, effort aliases, subscription facts, provenance, and refresh instructions. Runtime routing follows the routes and escalation sequence above.

This step is complete when every OpenAI-lane role has an exact model and effort, or an explicitly mapped workflow tier, and every fallback is recorded.

## 3. Add the GLM diversity lane

Route every GLM role through Pi's normal model access to `zai/glm-5.3:max`:

- **Review:** pair each OpenAI Reviewer with a GLM Reviewer on the same axis.
- **Code review:** invoke `$code-review` twice without modifying it—once with all reviewers routed to Sol `high` and once with all reviewers routed to GLM-5.3 `max`.
- **Frontend:** add a GLM diversification pass on design taste and execution.
- **Alternatives:** when the design path is unclear or competing approaches could expose useful tradeoffs, route at least one candidate through GLM.

Use available Z.ai subscription capacity proactively; a plausible benefit from diversity is enough to add the lane. Preserve the OpenAI lane. For alternative approaches, the delegating agent returns one recommended result synthesized from both families.

When GLM is unavailable, retain the OpenAI roles and record the unavailable provider or quota.

This step is complete when every review axis, Frontend role, and Alternative candidate has GLM-5.3 coverage or a concrete availability reason.

## 4. Add the Grok diversification lane

Default Grok roles to `cursor-grok-4.6-xhigh` through Cursor's `agent` CLI. Grok uses a Cursor CLI-only route: launch a separate process and return its result to the delegating or Synthesis agent. The delegating model may select any available Grok 4.6 profile until stronger effort-routing evidence exists. Keep Pi and workflow model fields for Pi-accessible routes such as OpenAI and GLM.

### Mutable implementation and debugging

For each role marked with the Grok worker trigger, invoke `$grok-worker`. That skill owns the mutable one-shot launch and delivery contract.

This branch is complete when the delegating agent has delivered the candidate change or recorded a concrete CLI availability reason.

### Read-only review

For a direct read-only review launch, run `agent --help` and `agent --list-models`; verify the current Grok model identifier and derive flags from installed help. With the current interface:

```bash
agent --print --mode ask \
  --model cursor-grok-4.6-xhigh \
  --trust --workspace "$PWD" \
  "$(cat "$prompt_file")"
```

Use read-only Grok review for:

- the highest-risk review axis on every high-stakes task;
- adversarial review triggers, especially race, concurrency, resource-lifetime, and merge-safety analysis;
- a final challenge to a chosen approach when correlated assumptions across the OpenAI and GLM lanes would be costly.

When the user requests a probe-capable Grok debug review in Herdr, invoke `$herdr-grok-review` instead of recreating its launch and checkout-preservation contract.

After multi-family reviews, a separate Sol `medium` Synthesis agent receives the completed reports, consolidates same-axis findings, preserves disagreements and model provenance, and keeps different review axes separate. When the CLI or Grok model is unavailable, preserve the OpenAI and GLM roles and record the failed availability check.

This branch is complete when every Adversarial review and high-stakes task has a captured Grok report or availability reason, and every completed multi-family review has a Sol `medium` Synthesis agent or a recorded fallback.
