---
name: grok-worker
description: Delegate implementation or debugging to a one-shot Grok 4.6 worker for model-family diversification. Use when a diagnosis remains uncertain or a fix failed, a competing implementation could expose a material tradeoff, or correlated OpenAI and GLM assumptions would be costly.
compatibility: Requires an authenticated Cursor Agent CLI with an available Grok 4.6 model.
---

# Grok worker

Run a one-shot **Grok worker** in the current task worktree. The worker may edit files and run commands, but its output is a candidate change. You remain the delivery owner responsible for verification, commits, pushes, and the final report.

## 1. Bound the candidate task

Name the uncertainty or alternative that model-family diversification should resolve. The delegating model chooses what prior reasoning and context to include. The prompt must state one bounded outcome, its known constraints, and acceptance evidence.

Include this execution contract:

- work directly in the supplied workspace;
- implement or debug the bounded task and run useful checks;
- leave commits and pushes to the delivery owner;
- finish with changed files, commands run, results, and remaining risks.

This step is complete when the prompt names the outcome, constraints, acceptance evidence, and execution contract.

## 2. Pin the current task worktree

Run synchronously in the caller's existing task worktree. Confirm that the current directory is the caller's already-established task worktree and keep it as Grok's target. Read its repository guidance and record the starting state:

```bash
git rev-parse HEAD
git status --porcelain=v1 -uall
git diff --binary | sha256sum
git diff --cached --binary | sha256sum
```

Keep the delegating agent idle while Grok runs so both agents never edit the worktree concurrently. Preserve all pre-existing changes; the baseline distinguishes them from Grok's candidate change.

This step is complete when the workspace, guidance, `HEAD`, and dirty-state fingerprint are known and no concurrent editor is active.

## 3. Derive the one-shot launch

Run `agent --help` and `agent --list-models` before each launch. Verify that print mode, permission flags, workspace selection, and a Grok 4.6 model are currently available. Default to `cursor-grok-4.6-xhigh`; the delegating model may choose any available Grok 4.6 profile.

Use native YOLO by default. It forces command approval while retaining the configured sandbox and MCP controls:

```bash
agent --print \
  --output-format text \
  --model "$grok_model" \
  --yolo --trust \
  --workspace "$PWD" \
  "$(cat "$prompt_file")" >"$result_file"
```

The delegating model may choose unrestricted execution by adding the current equivalents of:

```text
--sandbox disabled --approve-mcps
```

Derive the actual flags from installed help rather than assuming this interface remains stable. Keep prompt and result files outside the repository and remove them after delivery.

This step is complete when current CLI evidence supports the selected model, execution envelope, and exact command.

## 4. Run and recover the worker

Launch the command in the foreground and retain its exit status, standard error, and result file. Read the complete result after the process exits.

A failed, interrupted, or timed-out process may still have changed the worktree. Inspect the repository before retrying, and retry only after accounting for the first attempt's changes.

This step is complete when the process has settled and both its report and resulting workspace state are available to the delivery owner.

## 5. Own delivery

Resume responsibility immediately after Grok settles:

1. Compare `HEAD`, status, staged state, and diffs with the baseline.
2. Inspect every candidate change and reconcile it with the task and repository guidance.
3. Run the repository's required tests, checks, and runtime validation independently. Grok's reported checks are evidence to inspect, not a substitute for delivery-owner verification.
4. Resolve failures or incomplete work before presenting the task as complete.
5. Commit and push when the surrounding task requires them.
6. Report the selected Grok model and permission envelope, candidate changes, independent verification, commit or push state, and remaining risks.

The delegation is complete when the delivery owner—not the Grok worker—has verified and delivered the resulting change.
