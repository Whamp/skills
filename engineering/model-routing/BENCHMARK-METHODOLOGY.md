# Model-routing evidence

Read this reference when interpreting scores, auditing routing policy, or preparing a benchmark refresh. Runtime routes and subscription decisions live in [`SKILL.md`](SKILL.md).

## Keep the indices separate

### Model Coding Index

A model-level Artificial Analysis score. It is the equal-weighted average of Terminal-Bench v2.1 and SciCode. This is the coding score stored in `MODEL-PROFILES.csv`.

### Agentic Index

A model-level Artificial Analysis score for tool use, planning, autonomy, and multi-step execution. It equally weights GDPval-AA v2 agentic knowledge work and τ³-Banking tool-using customer interactions. It is distinct from the model-plus-harness Coding Agent Index below.

### Intelligence Index coding category

In Artificial Analysis Intelligence Index v4.1, Terminal-Bench v2.1 contributes 16% and SciCode contributes 8% of the overall Intelligence Index. Together they form its 24% coding category. This category is not a separate harness benchmark.

### Coding Agent Index

A model-plus-harness score. Version 1.1 combines DeepSWE, Terminal-Bench v2, and SWE-Atlas-QnA. Model-plus-harness rows vary the harness and provider as well as the model, so `MODEL-PROFILES.csv` excludes them.

## Keep cost and capacity separate

`Cost Per Task` is Artificial Analysis' estimated API cost per Intelligence Index task. It compares economic efficiency under public token pricing. It does not report a caller's marginal expenditure or remaining subscription capacity.

Token counts and per-run currency telemetry describe settled usage. They cannot establish quota remaining. A zero charge may represent plan-included use, bring-your-own-key billing, or a credit grant. Shared concurrent consumption also prevents guaranteed reservations based on an earlier balance observation.

Runtime routing treats each provider, account, and pool tuple as independent. Important separations include:

- OpenAI Codex subscription, direct OpenAI pay-as-you-go, and Cursor-hosted OpenAI models;
- Z.ai coding subscription, direct Z.ai pay-as-you-go, and Cursor-hosted GLM models;
- Cursor's first-party Grok pool and its third-party Fable pool.

Personal plan names, prices, allowance amounts, and freshness rules belong in the caller's local profile. The public policy accepts timestamped profile or caller observations without prescribing a private path, quota collector, or fixed allowance.

## GLM-5.3 effort aliases

Z.ai documents these coding-subscription mappings:

| Requested | Effective |
| --- | --- |
| `none`, `minimal`, `low` | `low` |
| `medium`, `high` | `high` |
| `xhigh`, `max` | `max` |

GLM-5.3 requires thinking. Z.ai documents `max` as the default and recommended reasoning effort. Runtime routing uses the explicit Pi route `zai/glm-5.3:max`.

## Historical snapshot limits

`MODEL-PROFILES.csv` is a benchmark and access snapshot dated 2026-08-14. Artificial Analysis had not published GLM-5.3 or Grok 4.6 profiles on that date. Their rows therefore have `Benchmark Status` set to `pending`, with metric and index-version fields blank. Do not carry forward predecessor scores or infer replacements.

Preserve the snapshot's measurements and provenance. Its `Access Pool`, model ID, and `Source` fields record the access route checked at that time, not current routing policy. In particular, the `cursor-grok-4.6-xhigh` CLI row is historical. The current normal Grok route is the Pi Cursor-provider route named in `SKILL.md`. Fable 5.1 is an explicit-user route, not a benchmarked default, and Opus has no active policy route.

## Local evidence and policy claims

Maintainer experience supports GLM as a frontend-diversity family and Grok as an adversarial family, especially for debugging and race analysis. These are routing priors rather than benchmark scores. Keep model family, provider, runtime, and subscription pool in result provenance so later evidence can confirm or change them.

A registry listing is catalog evidence only. It does not prove authentication, inference availability, remaining quota, or billing eligibility. Cursor SDK execution also has a different runtime and tool contract from an ordinary Pi model call. Routing reports must preserve that distinction.

## Provenance

Primary public sources:

- Artificial Analysis free API: <https://artificialanalysis.ai/api/v2/language/models/free>
- API documentation: <https://artificialanalysis.ai/data-api/docs#overview-hero>
- Model Coding Index: <https://artificialanalysis.ai/models/capabilities/coding>
- Agentic Index: <https://artificialanalysis.ai/models/capabilities/agentic/>
- Capability-indices methodology: <https://artificialanalysis.ai/methodology/capability-indices>
- Intelligence methodology: <https://artificialanalysis.ai/methodology/intelligence-benchmarking>
- Coding Agent methodology: <https://artificialanalysis.ai/methodology/coding-agents-benchmarking>
- Z.ai GLM-5.3: <https://docs.z.ai/guides/llm/glm-5.3>
- Z.ai deep thinking and reasoning effort: <https://docs.z.ai/guides/capabilities/thinking>
- Z.ai Chat Completion API: <https://docs.z.ai/api-reference/llm/chat-completion>
- Z.ai coding subscriptions: <https://docs.z.ai/devpack/overview>
- Cursor SDK usage and billing: <https://cursor.com/docs/sdk/typescript#usage-and-billing>
- Cursor models and pricing: <https://cursor.com/docs/models-and-pricing>

`MODEL-PROFILES.csv` records benchmark status, retrieval date, and source on every row. Published rows also record the Artificial Analysis index version. Current account capacity is deliberately absent.

## Refresh

The checked-in CSV remains a historical snapshot. A future benchmark refresh must first review the pending-profile configuration in `refresh-aa-model-profiles.py`; it still emits the historical Grok access identifier and source. Update that configuration only with separately approved route evidence, then run from the repository root with `ARTIFICIAL_ANALYSIS_KEY` available:

```bash
python engineering/model-routing/refresh-aa-model-profiles.py
python engineering/model-routing/tests/test_refresh_cli.py
```

The refresh command fetches every free-API page, selects configured published profiles, appends configured pending access profiles, and atomically replaces `MODEL-PROFILES.csv`. When Artificial Analysis publishes a pending model, move it into the benchmark-profile configuration and add its API response to the test fixture. Completion requires a passing CLI test, one retrieval date across all rows, and an index version on every `published` row.
