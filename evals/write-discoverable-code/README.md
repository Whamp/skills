# Write-discoverable-code eval

Measure whether applying the skill makes existing code easier for a fresh agent
to find and explain with Bash, literal search, and filename search.

Start with **six model sessions**: two writers and four readers. No API keys,
model SDK, evaluation service, or automatic model calls are required. The runner
uses Python 3.10+, Git, and ripgrep. Preservation checks also use uv and Python
3.12. Run the model sessions through a harness you already use.

## What is measured

| Measure | Rule |
| --- | --- |
| Correctness | All rubric facts and executable-code citations must be correct for a task to pass. |
| Search effort | Shell tool calls and UTF-8 bytes of stdout plus stderr returned to the reader. Count failed searches too. |
| Time | Wall seconds from receiving the question to the final answer, rounded up. |
| Preservation | Existing tests must pass in both versions. Inspect the diff for behavior, API, error-text, and licence changes. |
| Fixed-query replay | Save full output, returned line count, and bytes for each prewritten literal query or filename glob. |

The scorer reports effort savings only when **both readers answer every task
correctly**, both versions pass preservation review, and both readers stay
within 12 shell tool calls and 600 seconds. Correctness failures remain visible.
Missing evidence or unfinished grades cause an error instead of a score.

Replay measures retrieval and noise. It does not measure query choice or whether
the returned lines explain the implementation. A filename hit or fewer returned
bytes is not an automatic success. Fresh readers supply that evidence.

## 1. Prepare the experiment

Run from this repository's root. Use a new directory outside any checkout so its
files cannot appear in repository search. Supply the exact skill candidate you
want to measure; its installed location is not assumed.

```bash
eval_runner="$PWD/scripts/eval_discoverable_code.py"
eval_run="$(mktemp -d)/discovery"
python3 "$eval_runner" prepare "$eval_run" \
  --skill /absolute/path/to/write-discoverable-code/SKILL.md \
  --reader-config 'Record exact model, effort, harness version, tools and context limit'
```

Replace the reader configuration description with actual settings. Keep the same
model, effort, system instructions, tools, and limits for all four readers. Use
the same writer settings for both writers and record them in `private/writers.txt`.

The [suite](suite.json) pins ItsDangerous 2.2.0 and Werkzeug 3.1.3 by full commit
SHA. Each has one small target module and two questions: a behavior question and
a real error-message question. The questions, queries, and code-based rubrics
are written before the rewrite. The runner saves the suite and skill bytes and
their SHA-256 hashes under `private/`.

## 2. Rewrite and check behavior

Start one fresh writer session for each `private/writer-*.txt` prompt. Give each
writer access only to its assigned checkout and the saved `private/skill.txt`.
Keep questions, queries, rubrics, and sibling checkouts out of its context.
Save the writer transcripts under `private/`.

The writer may change the target module and necessary Python imports under
`src/`, including a module move. Public APIs and error text must stay stable.
Tests remain unchanged. Review the complete diff and new source files; a passing
test suite alone cannot prove equivalence. A rewrite that breaks behavior fails
the experiment rather than becoming a reader speed win.

Run the suite's `test_command` in each original and rewritten checkout. For
example, this records the exact command, full output, and exit status for all
four checks:

```bash
python3 - "$eval_run" <<'PY'
import json
import pathlib
import shlex
import subprocess
import sys

run = pathlib.Path(sys.argv[1])
suite = json.loads((run / 'private/suite.json').read_text())
failed = False
for target in suite['targets']:
    for arm in ('original', 'skill'):
        log = run / 'private' / f"validation-{target['id']}-{arm}.txt"
        with log.open('w') as output:
            output.write(target['test_command'] + '\n')
            output.flush()
            result = subprocess.run(
                shlex.split(target['test_command']),
                cwd=run / 'private' / arm / target['id'],
                stdout=output, stderr=subprocess.STDOUT, check=False,
            )
            output.write(f'\nexit_code={result.returncode}\n')
        failed |= result.returncode != 0
        print(log.name, result.returncode)
sys.exit(int(failed))
PY
```

These commands install pinned test tools in an isolated uv environment. The
repository commits are fixed; transitive test dependencies are not fully locked.
Retain resolved package versions if comparing runs on different machines.

## 3. Freeze the reader inputs and replay searches

```bash
python3 "$eval_runner" readers "$eval_run" --seed 0
python3 "$eval_runner" replay "$eval_run"
```

`readers` saves full repositories at neutral `readers/rNN/repo` paths, without
Git history or local test caches. It checks the base commits and rewrite scope,
saves snapshot hashes, and creates reader prompts. The private assignment key
maps reader names to repository and treatment. Tracked diffs are also saved;
new source files are preserved in full in the snapshots. Run this stage once,
after all source edits. Replay results go to `private/replay.json`.

Run one **fresh, isolated reader session** per `readers/rNN/prompt.txt`, in that
prompt's directory. Mount only that reader's `repo` and provide the prompt. Use
an empty harness profile without ambient skills, repository instructions from
this checkout, memory, or earlier conversation. Directory naming and prompt
instructions do not enforce isolation; the controller must configure it. Give
readers the whole repository, including tests and docs, with identical tools and
exclusions. Keep the skill, rewrite diff, replay output, and treatment labels
private. Run in the generated order; never reuse one session across arms.

Save the final answer to `readers/rNN/answer.txt` and the complete model/tool
transcript to `readers/rNN/transcript.txt`. The controller records elapsed time,
shell tool calls, and output bytes from the transcript. Include all reader
commands, even failed ones and batched shell commands. Each shell tool call
counts once. Sum the UTF-8 bytes of the stdout and stderr actually returned to
the model, without JSON envelopes. Record harness output caps and truncation in
the configuration; output bytes are an effort proxy, not model token usage.

## 4. Grade and score

Grade answers against every fact in `private/suite.json` and the exact reader
snapshot. Cite the supporting source lines and explain each pass or failure in
the grade's `reason`. Grade by neutral reader ID before looking at the treatment
key. This is a manual semantic grade, not a keyword-match judge.

Complete `private/grades.json`, which starts with null grades and metrics:

- `tasks`: set each `correct` to true or false and write a source-backed `reason`.
- `commands`, `output_bytes`, `elapsed_seconds`: enter observed nonnegative integers.
- `preservation_passed`: true only after the test log and diff review pass.
- `validation_log`: enter the matching log path relative to the run directory.

```bash
python3 "$eval_runner" score "$eval_run"
```

The runner checks evidence presence, task completeness, and unchanged reader
source. It trusts the controller's semantic grades, transcript counts, and test
review; it does not parse arbitrary harness transcripts or prove equivalence.
`private/score.json` shows correct task counts, preservation and budget gates,
raw effort, and absolute savings for each eligible pair. Negative savings mean
the rewrite cost more effort. Keep the entire run directory as the receipt.

## Interpretation and skill changes

This is a smoke test, not statistical evidence of a general gain. A clean pair
can still show zero improvement or higher search cost. Both targets are Python
libraries from Pallets. They do not test the skill's branded IDs, capability
types, or state modeling rules. Two questions in one reader session can share
context; their order is identical in both arms.

The original-versus-skill comparison includes the effect of doing any rewrite.
To attribute a gain to the skill itself, add a generic rewrite with the same
scope and writer budget, then a fresh reader per target: four more sessions.
Do this after the small experiment shows useful signal.

To shorten or improve the skill, change one rule group, prepare a new run, replay
the frozen queries, and spend fresh-reader sessions on promising candidates.
Keep these two targets as development cases; validate the final choice on a new
repository with questions written before its rewrite. More repeated readers
are needed before treating a small effort change as reliable. Never choose a
shorter skill solely because it uses fewer tokens when answer correctness falls.
