---
name: herdr-grok-review
description: Run an independent Grok 4.6 Extra High reviewer in Herdr when the user asks for a debug review, adversarial race probes, or an evidence-backed merge verdict.
compatibility: Requires HERDR_ENV=1, native Herdr tools, and the Cursor agent CLI.
---

# Herdr Grok review

Run a **debug review**: give Grok unrestricted local inspection and probe capability while keeping the target checkout byte-for-byte unchanged.

## 1. Pin the target

Resolve the repository or worktree, review fixed point, and `HEAD`. Use the user's fixed point; ask when none is available. Record:

- resolved fixed-point and `HEAD` hashes;
- `git diff <fixed-point>...HEAD` and commit list;
- originating request or spec;
- applicable repository guidance and coding-standard paths;
- known baseline failures or unrelated dirty files.

Capture this checkout fingerprint before launch:

- `git rev-parse HEAD`;
- `git symbolic-ref --quiet HEAD` or detached-HEAD state;
- `git status --porcelain=v1 -uall`;
- `git diff --binary | sha256sum`;
- `git diff --cached --binary | sha256sum`;
- `git config --local --null --list | sha256sum`;
- `git ls-files --others --exclude-standard -z | sort -z | xargs -0 -r sha256sum -- | sha256sum`.

Use Git read-only throughout the review. Preserve `HEAD`, the index, branch metadata, local Git configuration, and all pre-existing worktree content. Stop on a bad ref or empty diff.

This step is complete when the reviewer brief names one exact diff, its behavioral contract, its standards, its baseline exceptions, and one reproducible checkout fingerprint.

## 2. Derive the launch from the environment

Confirm `HERDR_ENV=1`, inspect the caller with `herdr_layout`, then create a fresh tab in the caller's workspace with the target checkout as `cwd` and `focus: false`. Keep its pane ID as the sidecar target.

Run `agent --help` in that pane and read the pane output. Then run `agent --list-models` and verify the available Grok 4.6 Extra High identifier. Derive the launch from this evidence on every run.

Select:

- the exact Grok 4.6 Extra High model identifier;
- default execution mode, which permits investigation and probes;
- every current flag required for forced command approval, disabled sandboxing, MCP approval, and workspace trust.

When current help matches today's interface, the native argument vector is `--model cursor-grok-4.6-xhigh --force --sandbox disabled --approve-mcps --trust`.

A wrapper error about expected JSON does not prove the shell command failed; read the pane transcript. If `agent --help` exposes no debug flag, use the review contract for debug behavior instead of inventing a flag.

This step is complete when current pane evidence proves the model identifier and unrestricted launch flags.

## 3. Start the reviewer

Use `herdr_agent start` in the fresh shell pane:

- `kind: cursor`;
- a unique review name;
- the model and permission arguments proven in step 2.

Use default execution mode so the reviewer can run tests and throwaway probes. Full permissions authorize investigation, not checkout changes.

This step is complete when Herdr reports the named agent as `idle` in the target checkout.

## 4. Submit the review contract

Read [REVIEW-PROMPT.md](REVIEW-PROMPT.md), replace every placeholder, and submit it atomically with `herdr_agent prompt`, `wait: true`, and a generous bounded timeout.

Fill the focus section with change-specific invariants and interactions between changed mechanisms. The template already carries the generic review boundaries; do not repeat them. Include known baseline failures so the reviewer can test causality instead of misattributing noise.

For a re-review, populate the prior-findings field with every earlier finding and its reproduction. The template requires Grok to rerun those probes and review the complete updated diff for new interactions.

This step is complete when the prompt call is accepted and Herdr observes a post-submission lifecycle change rather than `agent_prompt_stalled`.

## 5. Recover the complete result

A wait timeout bounds observation; it does not mean the review failed.

- On timeout, call `herdr_agent get`.
- If `working`, wait again while output shows progress.
- If `done` or `idle`, read `recent-unwrapped` with enough lines for the full review.
- If `blocked`, inspect and supply only the missing input.
- If alternate-screen history remains incomplete, ask the reviewer to write its complete response to a temporary Markdown file, then read that file directly.

This step is complete when every finding, evidence block, grade, merge verdict, and checkout fingerprint has been captured.

## 6. Audit and hand off

Recompute the checkout fingerprint and compare every value with the baseline. Confirm throwaway probes were deleted and the target checkout is unchanged. Preserve unrelated pre-existing changes.

Triage the report before relaying it:

- verify every proposed blocker or high finding against cited source and reproduction evidence;
- label pre-existing defects separately from regressions in the reviewed diff;
- reproduce any claimed baseline failure at the fixed point, or label its baseline status unverified;
- treat “not safe to merge as-is” as a merge blocker even if the reviewer used a weaker severity label;
- report unsupported or internally contradictory claims as disputed;
- summarize passed checks without presenting them as proof of uncovered paths.

Return the launch configuration, actionable findings, merge verdict, verification status, and the Herdr agent name, pane, and state. Leave the review sidecar open unless the user asks to retire it.

The review is complete when the user can decide whether to merge or fix without reading the raw transcript, and every post-review fingerprint value matches its baseline.
