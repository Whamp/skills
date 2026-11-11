# Write-discoverable-code eval

Measure whether applying the skill makes existing code easier for a fresh agent
to find and explain with Bash search. The runner now uses Pi with a verified,
minimal profile and automatic collection of model-visible output.

The bank has **eight questions across four pinned repositories**. Each question
gets a fresh reader process in each condition. The six development questions use
ItsDangerous, Werkzeug, and Cockatiel. Two PQueue questions are held out by
default. Only `run-writers` and `run-readers` call models.

With `--generic`, a development run uses six writers and 18 readers (24 model
sessions). The full bank uses eight writers and 24 readers (32 sessions).
Without the generic condition, those totals are 15 and 20 sessions. Task subsets
reduce cost without changing a question or sharing its reader history.

## Requirements

- Python 3.11+, Git, ripgrep, Node.js 24, npm, and a managed Pi installation.
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

To run a cheap development subset, select questions at preparation time:

```bash
python3 "$eval_runner" prepare "$eval_run" \
  --skill /absolute/path/to/write-discoverable-code/SKILL.md --generic \
  --tasks itsdangerous/expiry cockatiel/delay
```

Use a new run directory for each preparation. Add `--include-held-out` only for
a final evaluation of a fixed skill candidate. That flag includes all eight
questions unless `--tasks` also selects a subset. A held-out task cannot be
selected without the explicit flag. This is an evaluation split, not a secret:
the task definitions are public, but keep their results out of skill tuning.

| Target / task | Entry point given to the reader | Main evidence required |
| --- | --- | --- |
| `itsdangerous/expiry` | A signed timestamp ahead of the server clock | Age units, rejection boundary, disabled checks |
| `itsdangerous/fallback` | Expired data with fallback signers configured | Throw site and signer-loop exception path |
| `werkzeug/path` | Joining a user filename returns None | Normalization, rejection, empty base |
| `werkzeug/hash` | Exact PBKDF2 error text | Argument parsing and executable defaults |
| `cockatiel/delay` | Initial delay and cap, jitter disabled | Four delays and whether exponent affects them |
| `cockatiel/defaults` | Handled failures retry without a supplied limit | Default factory, delay, stop branch, invocation count |
| `p-queue/events` (held out) | Completed events and a non-throwing timeout | Payload, omitted events, running-slot release |
| `p-queue/priority` (held out) | Three waiting jobs with equal/different priorities | Insertion helper, tie order, dequeue and start branch |

The [suite](suite.json) pins the repositories by full commit SHA. Preparation
freezes the skill, questions, queries, rubrics, and condition list, and verifies
that every search oracle resolves in the baseline. The generic and skill writers
receive the same task and budget; only the skill writer receives the skill text.
Neither writer receives the discovery questions. Each writer gets 50 tool calls
and 15 minutes. Writes are limited to its own checkout; snapshot preparation
rejects edits outside each target's declared source globs, edits to colocated
`*.test.*` files, or changes to the original.

`validate` runs the frozen existing-test command in every condition and records
its exit code and source hash. Review each rewrite for API, error-text, and
behavior preservation too. Tests do not prove equivalence. Finish all edits and
validation before freezing the reader snapshots. The TypeScript commands install
local test dependencies with lifecycle scripts disabled, then run existing tests
and compile the source. Cockatiel uses its committed npm lock. PQueue has no
committed lock; its dependency ranges are resolved at validation time, so its
receipt is evidence for that installed environment, not a fully locked dependency
reproduction. No new tests or dependency files are added to benchmark sources.
Generated `dist/`, `node_modules/`, and `.nyc_output/` directories are excluded
from hashes and reader snapshots.

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

Readers get full repositories under neutral names, exactly one question, the same
model settings, and a limit of 12 tool calls and 600 seconds per question. A fresh process and
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

Scoring produces a row for each target/question pair and requires exactly one
reader per selected question and condition. Scoring re-collects the raw events and checks the entered metrics, matching
reader profiles, frozen inputs, unchanged snapshots, and test receipts for the
exact source. Effort savings require every condition to answer every task
correctly, preserve behavior, and stay within budget. With the generic condition,
results include savings against both the original and generic rewrite.
Older run formats remain readable and are marked `harness_verified: false`.

## Interpretation and skill changes

Each query is assigned to one task and names its expected implementation through
a Python symbol, a library call inside its owning function, or a reviewed unique
source range. TypeScript ranges use exact `start` and `end` anchors plus a source
`glob`; they are not inferred by parsing braces. Missing, duplicated, or reordered
anchors leave the oracle unresolved. They permit module moves while the anchors
remain unchanged. Review anchors against executable code before freezing a suite. Replay reports `direct`, `file_only`,
`indirect`, `miss`, or `oracle_unresolved`, plus direct and other hit counts.
A match in an exception declaration is not a direct match on the age-check
implementation. Function and module moves can still resolve; the library-call
oracle also permits private-function renames. More extensive changes can require
an explicitly reviewed oracle update in a new suite.

Replay is a cheap development check. Fresh readers still measure query choice,
recovery after misses, and interpretation. Keep correctness first; fewer returned
bytes from an empty or irrelevant search is not an improvement.

This remains a small Python and TypeScript discovery test. It does not measure
the compiler benefits of branded IDs, capability types, or state modeling. Generic rewrites improve
attribution, but repeated readers and a held-out target are needed before calling
small changes reliable. Avoid adding more cases until the existing search
oracles expose useful differences. Preserve the full run directory as evidence.

## Maintenance

The CLI remains `scripts/eval_discoverable_code.py`. Supporting modules keep
each part independently checkable:

- `scripts/discovery_readers.py`: isolated question assignments and neutral snapshots.
- `scripts/discovery_pi.py`: clean profiles, sandboxed shells, and raw-event collection.
- `scripts/discovery_corpus.py`: frozen input types, source hashes, and search oracles.
- `scripts/discovery_results.py`: validation receipts, profile matching, and scoring.
