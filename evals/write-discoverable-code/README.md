# Write-discoverable-code eval

Measure whether applying the skill makes existing code easier for a fresh agent
to find and explain with Bash search. The runner now uses Pi with a verified,
minimal profile and automatic collection of model-visible output.

With `--generic`, the comparison uses **10 sessions**: four writers and six
readers across two pinned repositories. Without that flag it uses the original
six-session smoke test. Only `run-writers` and `run-readers` call models.

## Requirements

- Python 3.10+, Git, ripgrep, Node.js, and a managed Pi installation.
- Pi with `-ne`, `-ns`, `-np`, `-nc`, `--no-mcp`, and the audit API. Verified with Pi 1.5.2.
- Linux with working bubblewrap (`bwrap`). Isolation failures stop the run.
- Existing Pi authentication for the explicitly selected provider and model.
- uv and Python 3.12 for the existing repository tests.

The harness uses the managed Pi installation. It creates an agent directory per
subject, links only its local `auth.json`, and supplies its own shell settings.
It does not inherit global settings, custom model definitions, or packages.
No normal Pi installation or package configuration is changed.

## Run the comparison

Run from this repository's root. Choose a new run directory outside checkouts.
The example uses the existing OpenAI subscription route; use only a route
already authorized for the work. There is no automatic provider or model fallback.

```bash
eval_runner="$PWD/scripts/eval_discoverable_code.py"
eval_run="/absolute/path/to/a/new-run"
python3 "$eval_runner" prepare "$eval_run" \
  --skill /absolute/path/to/write-discoverable-code/SKILL.md --generic

python3 "$eval_runner" run-writers "$eval_run" \
  --provider openai --model gpt-6.1-sol --thinking medium
python3 "$eval_runner" validate "$eval_run"
python3 "$eval_runner" readers "$eval_run" --seed 0
python3 "$eval_runner" replay "$eval_run"
python3 "$eval_runner" run-readers "$eval_run" \
  --provider openai --model gpt-6.1-sol --thinking medium
```

Add `--preflight-only` to either model command to inspect all selected subjects
without calling a model. Add `--only r01` for a reader, or
`--only generic-itsdangerous` for a writer, to run one subject. A completed session
is never overwritten; use a new run for another trial.

The [suite](suite.json) pins the repositories by full commit SHA. Preparation
freezes the skill, questions, queries, rubrics, and condition list, and verifies
that every search oracle resolves in the baseline. The generic and skill writers
receive the same task and budget; only the skill writer receives the skill text.
Neither writer receives the discovery questions. Each writer gets 50 tool calls
and 15 minutes. Writes are limited to its own checkout; snapshot preparation
rejects edits outside Python source under `src/` or changes to the original.

`validate` runs the frozen existing-test command in every condition and records
its exit code and source hash. Review each rewrite for API, error-text, and
behavior preservation too. Tests do not prove equivalence. Finish all edits and
validation before freezing the reader snapshots.

## What the preflight verifies

The runner uses `-ne -ns -np -nc --no-mcp --no-themes --no-approve --no-session`,
only `bash`, and a fixed system prompt. The sole explicit extension is the
repository's small [audit extension](pi-audit.mjs). Its inspection command reports
Pi's actual effective prompt, tool set, model, thinking level, context files,
skills, and history count. Ambient context, extra tools, and route substitutions
are rejected. The actual run must match its preflight.

Model-issued shell commands run through bubblewrap with only OS binaries and the
assigned repository available. Reader repositories are mounted read-only;
writers get a writable checkout. Other experiment directories and authentication
files are not mounted, and shell commands have no network. The Pi provider
process retains native access to its configured model service. Preflight probes
check the working directory, sibling-file isolation, and the reader write block.

Readers get full repositories under neutral names, the same questions, the same
model settings, and a limit of 12 tool calls and 600 seconds. A fresh process and
profile is used for every subject. The recorded seed controls condition order.

## Collection and grading

Each subject's `pi/` directory contains:

- `preflight.json`: actual prompt, route, tools, version, audit hash, and scope.
- `events.jsonl` and `stderr.txt`: raw Pi events and audit output.
- `execution.json`: exact command, prompt hash, exit code, and elapsed time.
- `metrics.json` and `answer.txt`: collected measurements and the final answer.

The collector counts final `message_end` tool-result text once. It excludes
streaming updates, full-output copies, result metadata, and JSON envelopes.
UTF-8 bytes therefore reflect text actually returned to the model, including
truncation notices. Failed tool calls count too. Model token usage is recorded
separately. Missing results, an unsettled or failed run, extra tools, and changed
runtime profiles prevent collection. Time is process wall time, rounded up for
the budget gate; it includes Pi startup and provider latency.

`run-readers` automatically fills counts and saves answers and transcripts.
To rebuild measurements from already captured events:

```bash
python3 "$eval_runner" collect "$eval_run" --reader r01
```

Grade answers by neutral reader ID against every rubric fact and executable-code
citation, before consulting the condition key. Complete `tasks` in
`private/grades.json` with `correct` and a source-backed `reason`. Set
`preservation_passed` after reviewing the rewrite, and point `validation_log` to
its existing test log. Those judgements remain manual; collection does not fill
them in.

```bash
python3 "$eval_runner" score "$eval_run"
```

Scoring re-collects the raw events and checks the entered metrics, matching
reader profiles, frozen inputs, unchanged snapshots, and test receipts for the
exact source. Effort savings require every condition to answer every task
correctly, preserve behavior, and stay within budget. With the generic condition,
results include savings against both the original and generic rewrite.
Older run formats remain readable and are marked `harness_verified: false`.

## Interpretation and skill changes

Each query names its expected implementation through a Python symbol or a
library call inside its owning function. Replay reports `direct`, `file_only`,
`indirect`, `miss`, or `oracle_unresolved`, plus direct and other hit counts.
A match in an exception declaration is not a direct match on the age-check
implementation. Function and module moves can still resolve; the library-call
oracle also permits private-function renames. More extensive changes can require
an explicitly reviewed oracle update in a new suite.

Replay is a cheap development check. Fresh readers still measure query choice,
recovery after misses, and interpretation. Keep correctness first; fewer returned
bytes from an empty or irrelevant search is not an improvement.

This remains a small test of two Python libraries from Pallets. It does not test
branded IDs, capability types, or state modeling. Generic rewrites improve
attribution, but repeated readers and a held-out target are needed before calling
small changes reliable. Avoid adding more cases until the existing search
oracles expose useful differences. Preserve the full run directory as evidence.

## Maintenance

The CLI remains `scripts/eval_discoverable_code.py`. Supporting modules keep
each part independently checkable:

- `scripts/discovery_pi.py`: clean profiles, sandboxed shells, and raw-event collection.
- `scripts/discovery_corpus.py`: frozen input types, source hashes, and search oracles.
- `scripts/discovery_results.py`: validation receipts, profile matching, and scoring.
