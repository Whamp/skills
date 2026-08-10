---
name: explain-diff-html
description: Build an interactive HTML explainer of a code change (a diff, branch, or PR). Use when the user wants a rich walkthrough of what changed and why.
disable-model-invocation: true
---

# Explain Diff

Produce one self-contained HTML **explainer** of the specified change. Write it in **classic style** — the register of Martin Kleppmann: clear, engaging, flowing smoothly from one section to the next. The file is done only when all four sections below are complete and every check in **Format** holds.

## Sections

Produce these four, in order. Each ends on its own completion bar.

- **Background** — Explain the system the change sits in. Explore the surrounding code broadly first, then give a **two-tier** background: a deep, beginner-friendly layer (the reader's on-ramp), then a narrow layer aimed squarely at this change. *Done when:* both tiers are present and a reader new to the codebase could locate where this change lives.
- **Intuition** — Explain the *essence* of the change, not its full detail. Use **toy data** and concrete examples; lean on figures and diagrams. *Done when:* a reader who skipped Background and Code could still state, in one sentence, what the change is for.
- **Code** — Walk through the changes at a high level, grouped and ordered so the reader can follow. *Done when:* every modified file or hunk in the diff is accounted for in the walkthrough.
- **Quiz** — Five multiple-choice questions that test real understanding of this change: medium difficulty — answerable only from the substance of the PR, never from gotchas. Each question tells the reader whether they were right and gives feedback. *Done when:* exactly five questions exist, each with a correctness check and feedback.

## Diagrams

Pick a small number of **reusable diagram families** and apply them across the explainer. Two reliable kinds:

- A simplified version of the UI the user sees, for UI changes.
- A system diagram showing data flow or communication between components — always with example data.

Render every diagram in HTML (styled `div`s for shapes, HTML lists for lists). **Never ASCII art.**

## Code blocks

Always use `<pre>` tags for code. If you must use a custom styled `div` instead, its CSS **must** include `white-space: pre-wrap`, or the browser collapses every newline into one line. Before saving, scan each code block in the HTML source and confirm its CSS has `white-space: pre` or `pre-wrap`.

## Callouts

Use callouts to lift key concepts, definitions, and important edge cases out of the prose.

## Format

The output is one self-contained HTML file — CSS and JavaScript inlined, one long page (no top-level tabs), with section headers and a table of contents. Add basic responsive styling so it reads on a phone.

Write it to a global location **outside** the code repo, filename prefixed with today's date in `YYYY-MM-DD-` format (keeps files time-sorted and out of version control), e.g. `/tmp/2026-01-12-explanation-<slug>.html`.
