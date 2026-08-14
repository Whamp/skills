# Model-routing evidence

Read this reference when interpreting scores, auditing routing policy, or refreshing `MODEL-PROFILES.csv`.

## Keep the indices separate

### Model Coding Index

A model-level Artificial Analysis score: the equal-weighted average of Terminal-Bench v2.1 and SciCode. This is the coding score stored in `MODEL-PROFILES.csv`.

### Agentic Index

A model-level Artificial Analysis score for agentic workflows involving tool use, planning, autonomy, and multi-step execution. It equally weights GDPval-AA v2 agentic knowledge work and τ³-Banking tool-using customer interactions. It is distinct from the model-plus-harness Coding Agent Index below.

### Intelligence Index coding category

In Artificial Analysis Intelligence Index v4.1, Terminal-Bench v2.1 contributes 16% and SciCode contributes 8% of the overall Intelligence Index. Together they form its 24% coding category; this category is not a separate harness benchmark.

### Coding Agent Index

A model-plus-harness score. Version 1.1 combines DeepSWE, Terminal-Bench v2, and SWE-Atlas-QnA. Model-plus-harness rows vary the harness and provider as well as the model, so they are excluded from `MODEL-PROFILES.csv`.

## Cost semantics

`Cost Per Task` is Artificial Analysis' estimated API cost per Intelligence Index task. It is evidence about economic efficiency under token pricing, not Will's marginal expenditure while an included subscription has capacity.

The routing portfolio has three independent access pools:

- OpenAI Codex subscription through Pi.
- Z.ai Coding Plan Pro through Pi's normal model API. Z.ai documents approximate limits of 400 prompts per rolling five hours and 2,000 prompts per week. One prompt may contain an estimated 15–20 model calls.
- Cursor subscription through the `agent` CLI. Grok 4.6 is not a Pi or workflow model route in this environment.

## GLM-5.3 effort aliases

Z.ai documents these Coding Plan mappings:

| Requested | Effective |
| --- | --- |
| `none`, `minimal`, `low` | `low` |
| `medium`, `high` | `high` |
| `xhigh`, `max` | `max` |

GLM-5.3 requires thinking. Z.ai documents `max` as the default and recommended reasoning effort. Runtime routing uses the explicit Pi route `zai/glm-5.3:max`.

## Pending benchmark profiles

Artificial Analysis had not published GLM-5.3 or Grok 4.6 profiles when the snapshot was refreshed on 2026-08-14. Their `MODEL-PROFILES.csv` rows record verified local access with `Benchmark Status` set to `pending`; all metric and index-version fields remain blank. Do not carry forward predecessor scores or infer replacements.

## Local evidence

Will's prior experience is that GLM models have stronger frontend design taste than earlier OpenAI models. GPT-5.6 is reported to improve frontend work, but Will's direct experience with it remains limited. Grok's local role is adversarial review, especially debugging and race analysis. The diversity overlay turns multi-family work into continuing local evidence without replacing the OpenAI baseline.

## Provenance

Primary sources:

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
- Z.ai Coding Plan: <https://docs.z.ai/devpack/overview>
- Local access checks: `pi --list-models zai` and `agent --list-models`

`MODEL-PROFILES.csv` records benchmark status, retrieval date, and source on every row. Published rows also record the Artificial Analysis index version.

## Refresh

With `ARTIFICIAL_ANALYSIS_KEY` available in the environment, run:

```bash
python ~/.agents/skills/model-routing/refresh-aa-model-profiles.py
python ~/.agents/skills/model-routing/tests/test_refresh_cli.py
```

The refresh command fetches every free-API page, selects the configured published profiles, appends the pending access profiles, and atomically replaces `MODEL-PROFILES.csv`. When Artificial Analysis publishes either pending model, move it into the benchmark-profile configuration and add its API response to the test fixture. Completion requires a passing CLI test, one retrieval date across all rows, and an index version on every `published` row.
