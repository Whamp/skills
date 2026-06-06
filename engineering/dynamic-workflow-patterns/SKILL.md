---
name: dynamic-workflow-patterns
description: Use when the user asks for a workflow, dynamic workflow, fan-out, multi-agent orchestration, ultracode-style work, large-scale verification, adversarial review, tournament selection, or decomposable research/refactor tasks. Teaches when to use Pi's workflow tool and which orchestration pattern to choose.
---

# Dynamic Workflow Patterns

## Purpose

Use this skill to decide whether to call Pi's `workflow` tool and to design the workflow script well.

A dynamic workflow is a small deterministic JavaScript harness that coordinates subagents. The workflow script holds the loop, branching, fan-out, and intermediate results. Subagents do the file reads, shell commands, research, edits, and verification.

## First Decision: Should This Be a Workflow?

Use a workflow when the task benefits from isolated subagent contexts, parallelism, or explicit quality gates.

Good fits:

- Codebase audits across many files, modules, endpoints, or tests
- Multi-perspective review: security, product, architecture, performance, UX
- Large refactors or migrations that can split by file, module, callsite, or failing test
- Deep research where sources or claims need independent cross-checking
- Root-cause investigation with competing hypotheses
- Triage or sorting at scale
- Naming, design, or strategy exploration with a rubric
- Verification where self-preferential bias would be risky

Poor fits:

- A single file read, small edit, or routine shell check
- Tasks that require many mid-run user decisions
- Work that cannot tolerate higher token use
- Anything better handled by a specialized built-in tool or focused skill

If the user explicitly asks for a workflow, use one unless it would be unsafe or nonsensical. If the user did not ask for a workflow, prefer ordinary tools unless the task is clearly decomposable and high-value.

## Pi Workflow Tool Contract

Call the `workflow` tool with one raw JavaScript string. No Markdown fences.

The script must start with literal metadata:

```js
export const meta = {
  name: 'short_snake_case',
  description: 'Human-readable purpose',
  phases: [
    { title: 'Discover' },
    { title: 'Analyze' },
    { title: 'Synthesize' },
  ],
}
```

Available globals inside the script:

- `agent(prompt, opts)` — spawn an isolated Pi subagent. Returns text, or a validated object when `opts.schema` is present.
- `parallel(thunks)` — run independent `() => agent(...)` thunks concurrently. Pass functions, not promises.
- `pipeline(items, ...stages)` — run each item through sequential stages while items fan out.
- `phase(title)` — create/update progress groups.
- `log(message)` — add workflow-level logs.
- `args` — optional JSON passed through the tool call.
- `cwd`, `process.cwd()` — current working directory.
- `budget` — rough token budget tracker.

Rules:

- Every workflow must call `agent()` at least once.
- Use plain JavaScript only. Do not use TypeScript syntax.
- Do not use imports, `require`, `fs`, network APIs, `Date.now()`, `new Date()`, or `Math.random()`.
- Return a compact JSON-serializable value.
- Include a final synthesis/assertion agent when combining multiple subagent results.
- Give every agent a unique short label, 2-5 words.
- Subagents do not inherit parent context. Put the needed paths, criteria, and task details in each prompt.
- Check for `null` results from failed `agent`, `parallel`, or `pipeline` branches.

Current Pi package limitations to remember:

- No persisted/resumable workflow runs yet.
- No `/workflows` manager yet.
- No saved workflow command manager yet.
- `opts.model` and `opts.isolation: 'worktree'` are passed as guidance, not guaranteed runtime enforcement.

## Pattern Catalog

### 1. Fan-Out and Synthesize

Use when the task splits into independent slices.

Examples: inspect modules, audit endpoints, review files, research source categories.

Shape:

```js
phase('Fan out')
const results = await parallel(items.map((item, index) => () => agent(
  'Analyze this item against the rubric.\nItem: ' + JSON.stringify(item),
  { label: 'slice ' + index, schema: resultSchema },
)))

phase('Synthesize')
const final = await agent(
  'Synthesize these findings. Remove duplicates and call out uncertainty.\n' + JSON.stringify(results),
  { label: 'final synthesis', schema: finalSchema },
)
return { ok: true, pattern: 'fan_out_and_synthesize', final }
```

Use this as the default pattern for broad but separable work.

### 2. Classify and Act

Use when items need different handling.

Examples: triage issues, route files by language, split bugs by severity, choose between code/research/docs agents.

Shape:

1. Classifier agent assigns each item a category and reason.
2. Script routes each category to the right prompt or stage.
3. Synthesis checks category coverage and unresolved items.

Prefer structured output for classifications.

### 3. Adversarial Verification

Use when correctness matters and self-review may be biased.

Examples: security claims, migration completeness, root-cause hypotheses, factual reports, release blockers.

Shape:

1. Producer agents generate findings or fixes.
2. Verifier agents independently challenge each result against a rubric.
3. Final synthesis reports only findings that survive verification, plus disputed items.

Verifier prompt requirements:

- Do not assume the producer is right.
- Check evidence directly when possible.
- Mark unsupported, incomplete, or ambiguous claims.
- Return `pass`, `fail`, or `uncertain` with reasons.

### 4. Generate and Filter

Use for ideation plus quality control.

Examples: names, designs, strategies, test ideas, refactor approaches.

Shape:

1. Several generator agents propose options from different angles.
2. A filter agent deduplicates and scores options against a rubric.
3. Optional verifier checks the top options for feasibility or conflicts.

Always provide a rubric. Without a rubric, taste-based workflows drift.

### 5. Tournament

Use when comparative judgment is more reliable than absolute scoring.

Examples: selecting names, ranking candidates, choosing designs, comparing plans.

Shape:

1. Generate candidates.
2. Pair candidates.
3. Judge each pair with the rubric.
4. Advance winners until top choices remain.
5. Synthesize final ranking and tradeoffs.

Keep each comparison small. Pairwise comparison often beats asking one agent to rank a huge list at once.

### 6. Loop Until Done

Use when the amount of work is unknown.

Examples: reproduce flaky test, mine recurring issues until no new clusters appear, inspect logs until no new hypotheses survive.

Shape:

1. Run a pass.
2. Synthesize what changed and whether the stop condition is met.
3. Continue while there are new findings, failing checks, or untested hypotheses.
4. Stop at a hard cap to avoid runaway cost.

Always define:

- Stop condition
- Maximum iterations
- Evidence required to stop
- What to return if the cap is hit

### 7. Pipeline

Use when each item needs the same sequence of stages.

Examples: identify claim → verify claim → summarize claim; locate callsite → propose edit → review edit.

Shape:

```js
const outputs = await pipeline(
  items,
  async (item, original, index) => agent('Stage 1 prompt for ' + JSON.stringify(item), { label: 'stage1 ' + index }),
  async (stage1, original, index) => agent('Stage 2 prompt. Original: ' + JSON.stringify(original) + '\nPrior: ' + stage1, { label: 'stage2 ' + index }),
)
```

Use `pipeline` instead of hand-written nested loops when each item has ordered stages.

## Prompting Checklist for Workflow Scripts

Before calling `workflow`, decide:

- Objective: What exact result should the workflow produce?
- Pattern: Which pattern above fits best?
- Slices: What are the independent units of work?
- Evidence: What must subagents inspect or cite?
- Rubric: What makes a result good, bad, risky, or uncertain?
- Stop condition: When is the workflow done?
- Budget: How many agents and how much token use is acceptable?
- Safety: Which branches read untrusted content, and which may take actions?

For untrusted inputs, use quarantine: agents that read untrusted public content should only summarize or classify. Separate trusted agents should decide whether to act.

## Workflow Skeleton

```js
export const meta = {
  name: 'task_workflow',
  description: 'Solve the task with parallel analysis and verified synthesis',
  phases: [
    { title: 'Discover' },
    { title: 'Analyze' },
    { title: 'Verify' },
    { title: 'Synthesize' },
  ],
}

const input = args || {}

phase('Discover')
const discovery = await agent(
  'Inspect the task context and identify independent work slices. Return concise JSON-compatible text.\nInput: ' + JSON.stringify(input),
  { label: 'discover slices' },
)

phase('Analyze')
const items = Array.isArray(input.items) ? input.items : [discovery]
const analyses = await parallel(items.map((item, index) => () => agent(
  'Analyze this slice. Include evidence, risks, and open questions.\nSlice: ' + JSON.stringify(item),
  { label: 'analyze ' + index },
)))

phase('Verify')
const verifications = await parallel(analyses.map((analysis, index) => () => agent(
  'Adversarially verify this analysis. Check unsupported claims and missing evidence.\nAnalysis: ' + JSON.stringify(analysis),
  { label: 'verify ' + index },
)))

phase('Synthesize')
const synthesis = await agent(
  'Synthesize the analyses and verifications. Return only conclusions that survive evidence checks. Include uncertainties and next steps.\nAnalyses: ' + JSON.stringify(analyses) + '\nVerifications: ' + JSON.stringify(verifications),
  { label: 'final synthesis' },
)

return {
  ok: true,
  pattern: 'fan_out_with_adversarial_verification',
  synthesis,
  counts: {
    items: items.length,
    analyses: analyses.filter(Boolean).length,
    verifications: verifications.filter(Boolean).length,
  },
}
```

## How to Explain the Choice to the User

When you use a workflow, briefly state the pattern and why:

- “I’ll use fan-out-and-synthesize because the audit splits cleanly by route file.”
- “I’ll add adversarial verification because the output is security-sensitive.”
- “I’ll use a tournament because pairwise comparison is better for choosing among subjective options.”

Do not over-explain. The workflow progress and final synthesis should carry the detail.
