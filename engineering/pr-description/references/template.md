# PR body template

Copy only the contents of this fence into the body file. Fill every placeholder. Remove the optional screenshot or snippet placeholder unless it helps; replace it with a Markdown image or a short fenced CLI output block when it does. The opening paragraph remains first.

```markdown
{{OPENER: one short paragraph, one or two sentences, problem then result}}

{{OPTIONAL_SCREENSHOT_OR_SHORT_CLI_SNIPPET}}

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
