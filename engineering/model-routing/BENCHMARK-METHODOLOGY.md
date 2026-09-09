# Model-routing evidence

Read this reference when interpreting scores, auditing routing policy, or refreshing benchmark data. Runtime routes and subscription decisions live in [`SKILL.md`](SKILL.md).

## Keep the indices separate

### Model Coding Index

A model-level Artificial Analysis score. It equally weights Terminal-Bench v2.1 and SciCode. `MODEL-PROFILES.csv` stores this score under `Model Coding Index`.

### Agentic Index

A model-level score for tool use, planning, autonomy, and multi-step execution. Artificial Analysis equally weights GDPval-AA v2 agentic knowledge work and τ³-Banking tool-using customer interactions. The free API does not publish this score for every model. A blank cell means unpublished, not zero.

### Intelligence Index v4.3

Artificial Analysis changed the Intelligence Index methodology on 2026-09-07. Version 4.3 weights Agents at 30%, Coding at 20%, General at 30%, and Scientific Reasoning at 20%. AutomationBench-AA replaced τ³-Banking at 5%, and Terminal-Bench v4.0 replaced Terminal-Bench v2.1 at 10%. Private questions or answers now account for 45% of the index.

The Intelligence Index's non-hallucination component measures factual behavior on AA-Omniscience. It does not measure scope control, unnecessary implementation, or whether an agent accurately reports work it performed.

### Coding Agent Index

A model-plus-harness score. The current index combines DeepSWE, Terminal-Bench v2.1, and SWE-Atlas-QnA. Rows vary the agent harness, provider, model, and settings. `MODEL-PROFILES.csv` excludes this index because the routing policy needs model-profile evidence rather than a blended harness comparison.

## Keep benchmark cost and capacity separate

`Cost Per Task` is Artificial Analysis' estimated pay-per-token API cost for one Intelligence Index task. It does not report the caller's marginal cost or remaining subscription capacity. A blank cell means the free API did not publish a usable estimate.

Token counts and per-run currency telemetry describe settled usage. They do not establish remaining quota. A zero charge may represent plan-included use, bring-your-own-key billing, or credit. Shared consumption also prevents guaranteed reservations from an earlier observation.

Runtime routing treats each provider, account, and pool tuple as independent. Important separations include:

- OpenAI Codex subscription, direct OpenAI pay-as-you-go, and Cursor-hosted OpenAI models;
- Z.ai coding subscription, direct Z.ai pay-as-you-go, and Cursor-hosted GLM models;
- direct xAI access and Cursor Models for Grok, and Cursor Other Models for Fable;
- caller-configured local inference resources.

Personal plan names, limits, quota multipliers, prices, and freshness rules belong in the caller's local profile. The public policy accepts profile or caller observations without prescribing a private path or collection tool.

## GLM-5.3 effort aliases

Z.ai documents these coding-subscription mappings:

| Requested | Effective |
| --- | --- |
| `none`, `minimal`, `low` | `low` |
| `medium`, `high` | `high` |
| `xhigh`, `max` | `max` |

GLM-5.3 requires thinking. Z.ai documents `max` as its default and recommended effort. Runtime routing uses explicit `:max` selectors for GLM-5.3 and GLM-5.3-Flash.

## Snapshot limits

`MODEL-PROFILES.csv` is a 2026-09-09 snapshot of selected Artificial Analysis free-API profiles. Every row uses Intelligence Index version 4.3. It covers the active policy routes for Luna, Sol, Astra, GLM-5.3, GLM-5.3-Flash, Grok 4.6, Fable 5.1 Medium, and Qwen3.8-Flash-Next. Grok appears once for direct xAI and once for Cursor Models. Both rows reuse the same model-level benchmark profile because provider separation adds capacity, not family diversity.

Artificial Analysis does not publish an Agentic Index or estimated task cost for Qwen3.8-Flash-Next. It also omits task-cost estimates for Luna Low, Medium, and High in this snapshot. The refresh program permits only these named omissions and still requires every selected model's Intelligence and Coding scores.

The Qwen row's `local-profile/qwen3.8-flash-next` value is a logical policy route, not a universal Pi registry selector. The caller profile supplies the installed model ID, endpoint, vision support, concurrency limit, and aggregate context budget. Benchmark scores describe Artificial Analysis' tested model, not a caller's quantized deployment.

Artificial Analysis names the Fable profile `Adaptive Reasoning, Medium Effort, Default Fallback`. Its score describes that published profile. It does not prove that a Cursor SDK run has identical provider behavior or harness settings.

The `Access Pool` and `Model ID` fields connect benchmark profiles to current policy routes. They do not prove authentication, inference availability, quota, or billing eligibility.

## Runtime evidence

The current model roles and routes live only in [`SKILL.md`](SKILL.md). They combine benchmark data with maintainer experience, caller constraints, measured local behavior, and subscription capacity. Benchmark rank alone does not determine a route.

Cursor documents its SDK as an agent SDK rather than a raw model-inference API. Local runs execute the agent loop in the caller's Node process; cloud runs execute in Cursor-hosted environments. SDK usage follows Cursor plan pools and billing. The normal policy route uses the installed Pi Cursor provider rather than a shell invocation of the Cursor CLI.

## Provenance

Primary public sources:

- Artificial Analysis free API: <https://artificialanalysis.ai/api/v2/language/models/free>
- API documentation: <https://artificialanalysis.ai/data-api/docs#overview-hero>
- Intelligence Index v4.3 announcement: <https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-3>
- Capability indices: <https://artificialanalysis.ai/methodology/capability-indices>
- Intelligence methodology: <https://artificialanalysis.ai/methodology/intelligence-benchmarking>
- Coding Agent methodology: <https://artificialanalysis.ai/methodology/coding-agents-benchmarking>
- Z.ai GLM-5.3: <https://docs.z.ai/guides/llm/glm-5.3>
- Z.ai reasoning effort: <https://docs.z.ai/guides/capabilities/thinking>
- Z.ai coding subscriptions: <https://docs.z.ai/devpack/overview>
- xAI Grok 4.6: <https://docs.x.ai/developers/grok-4-6>
- xAI reasoning effort: <https://docs.x.ai/developers/model-capabilities/text/reasoning>
- Cursor TypeScript SDK: <https://cursor.com/docs/sdk/typescript>
- Cursor models and pricing: <https://cursor.com/docs/models-and-pricing>

`MODEL-PROFILES.csv` records benchmark status, retrieval date, source, and index version on every row. Current account capacity remains outside the public snapshot.

## Refresh

Run from the model-routing skill directory with `ARTIFICIAL_ANALYSIS_KEY` available:

```bash
python refresh-aa-model-profiles.py
python tests/test_refresh_cli.py
```

The refresh command fetches every free-API page, selects configured profiles, validates required and explicitly optional metrics, and atomically replaces `MODEL-PROFILES.csv`. Update the checked-in fixture when selected upstream profiles change.

A refresh is complete when the CLI test passes, every row has one retrieval date and index version, required metrics are finite, and only configured optional cells are blank.
