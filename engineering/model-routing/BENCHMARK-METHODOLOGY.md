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

A model-plus-harness score. Version 1.1 combines DeepSWE, Terminal-Bench v2, and SWE-Atlas-QnA. Rows such as Codex + GPT-5.6 and Claude Code + GLM-5.2 vary the harness and provider as well as the model, so they are excluded from `MODEL-PROFILES.csv`.

## Cost semantics

`Cost Per Task` is Artificial Analysis' estimated API cost per Intelligence Index task. It is evidence about economic efficiency under token pricing, not Will's marginal expenditure while an included subscription has capacity.

The routing portfolio has two independent access pools:

- OpenAI Codex subscription.
- Z.ai Coding Plan Pro, already configured in Pi. Z.ai documents approximate limits of 400 prompts per rolling five hours and 2,000 prompts per week. One prompt may contain an estimated 15–20 model calls.

## GLM-5.2 effort aliases

Z.ai documents these effective reasoning levels:

| Requested | Effective |
| --- | --- |
| `none`, `minimal` | thinking disabled |
| `low`, `medium` | `high` |
| `high` | `high` |
| `xhigh`, `max` | `max` |

Artificial Analysis currently publishes GLM-5.2 model results for non-reasoning and max, not high. The unsuffixed Pi route `zai/glm-5.2` uses the configured model default; Z.ai documents max as the API default reasoning effort.

## Local evidence

Will's prior experience is that GLM models have stronger frontend design taste than earlier OpenAI models. GPT-5.6 is reported to improve frontend work, but Will's direct experience with it remains limited. The diversity overlay turns paired OpenAI/GLM work into continuing local evidence without replacing the OpenAI baseline.

## Provenance

Primary sources:

- Artificial Analysis free API: <https://artificialanalysis.ai/api/v2/language/models/free>
- API documentation: <https://artificialanalysis.ai/data-api/docs#overview-hero>
- Model Coding Index: <https://artificialanalysis.ai/models/capabilities/coding>
- Agentic Index: <https://artificialanalysis.ai/models/capabilities/agentic/>
- Capability-indices methodology: <https://artificialanalysis.ai/methodology/capability-indices>
- Intelligence methodology: <https://artificialanalysis.ai/methodology/intelligence-benchmarking>
- Coding Agent methodology: <https://artificialanalysis.ai/methodology/coding-agents-benchmarking>
- Z.ai Chat Completion API: <https://docs.z.ai/api-reference/llm/chat-completion>
- Z.ai Coding Plan: <https://docs.z.ai/devpack/overview>

`MODEL-PROFILES.csv` records its index version, retrieval date, and source on every row.

## Refresh

With `ARTIFICIAL_ANALYSIS_KEY` available in the environment, run:

```bash
python ~/.agents/skills/model-routing/refresh-aa-model-profiles.py
python ~/.agents/skills/model-routing/tests/test_refresh_cli.py
```

The refresh command fetches every free-API page, selects the configured OpenAI and Z.ai profiles, and atomically replaces `MODEL-PROFILES.csv`. Completion requires a passing CLI test and a CSV whose rows share the current index version and retrieval date.
