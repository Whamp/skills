---
name: pr-description
description: Write, open, or update a pull request description in Will Hampson's details-summary style, with a short human-facing opener and model-attributed details.
---

# PR description

Give a human enough information to decide whether the PR deserves their attention, with the full agent-written description available on expansion.

## Workflow

1. Read the final diff and actual verification results. Draft the problem, solution, and verification from that evidence. Include material limitations and assumptions; do not claim checks you did not run.
2. Extract the single most important point, often already buried in that draft. Open with the shortest plain-language paragraph that explains the problem and result in one or two sentences. No heading, bullets, preamble, title repetition, or multiple paragraphs. Use the [opener examples](references/examples.md) when choosing what to keep.
3. Immediately after the opener, optionally add one screenshot or a short CLI or `--help` snippet, only when it shows the change faster than words.
4. Use the [ready-to-fill template](references/template.md) to place the full Problem / Solution / Verification write-up inside `<details>` and `</details>`. Put `<summary>MODEL EFFORT</summary>` immediately after the opening tag. Preserve a blank line after `</summary>` and before `</details>` so GitHub renders the Markdown inside. Remember **details-summary**: two syllables then three; details wraps the summary and the expanded text.
5. Replace `MODEL EFFORT` with the exact model and reasoning effort that wrote the description, such as `GPT-6.1 Sol High` or `Claude Opus 5.5 Medium`. Use the actual runtime identity, never an example by default. If either value is unknown, ask when possible or label it honestly, such as `Model unknown; effort unknown`.
6. For an authorized GitHub create or update, follow the [GitHub workflow](references/github.md). At handoff, flag the opener as a draft for Will to approve or edit before merge. It promises human judgement; an agent draft is not evidence of human approval. Keep that handoff note out of the opening paragraph.

Complete when the opener stands alone, the optional visual earns its space, the expanded write-up is factual and model-attributed, and the published body retains both tags and blank lines when publication is in scope.

## Source and provenance

Will-authored, materially transformed guidance drawing on Simon Willison's [Hide your slop PR descriptions behind details-summary](https://simonwillison.net/2026/Nov/9/details-summary/), published 9 November 2026. The [examples](references/examples.md) attribute the five supplied excerpts to Simon; the workflow and template are maintained here.
