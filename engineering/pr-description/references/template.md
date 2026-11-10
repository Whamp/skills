# PR body template

Before filling the opener or choosing an image, video, or snippet, complete the [required clear-writing step](../SKILL.md#workflow).

Copy only the contents of this fence into the body file. Fill every placeholder. Remove the optional image, video, or snippet placeholder unless it helps; replace it with an image, video, or short fenced CLI output block when it does. The opening paragraph remains first.

```markdown
{{OPENER: one short paragraph, one or two sentences, problem then result; apply clear-writing first}}

{{OPTIONAL_IMAGE_VIDEO_OR_SHORT_CLI_SNIPPET}}

<details>
<summary>{{EXACT_MODEL_AND_EFFORT}}</summary>

## Problem

{{What was wrong or missing, and who it affected.}}

## Solution

{{What changes for the reader, with implementation details needed for review.}}

## Verification

{{Commands actually run and observed results; proof links, limitations, and assumptions.}}

</details>
```
