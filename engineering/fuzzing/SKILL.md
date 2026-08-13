---
name: fuzzing
description: Fuzzing for coverage-guided input search, target and campaign design, failure minimization, and regression replay. Use to assess or execute fuzzing at input-processing, protocol, file-format, unsafe-code, FFI, or memory-safety boundaries; also use for existing fuzz targets, campaigns, corpora, and discovered failures.
---

# Fuzzing

A fuzz target combines generated input, coverage feedback, a tight harness, and an oracle. The campaign is useful only when failures reproduce and the harness can reach the behavior at risk.

## 1. Commit or return

Inspect the relevant production entry point and existing toolchain before
committing to a campaign. Write one outcome:

```text
Commit:
Target: <direct production entry point>
Risk: <crash, hang, resource, memory-safety, or semantic defect>
Input model: <bytes or structured input>
Feedback: <why coverage-guided mutation is useful>
Oracle: <observable failure condition>
Engine: <supported project tool>
Budget: <CPU, memory, workers, and wall time>
Regression path: <where minimized failures will live>
```

or:

```text
Return: Use <Examples | Property-based testing> because <why fuzzing lacks leverage>.
```

Return when meaningful cases form a small table, structured generation is the
better search signal, the available oracle cannot observe the dominant risk, or
the harness requires unrelated system startup or unauthorized dependencies.

After Commit, read the matching adapter when one is listed:

- Rust with cargo-fuzz and libFuzzer — [cargo-fuzz](references/cargo-fuzz.md)
- C or C++ with libFuzzer or AFL++ — [C and C++ fuzzing](references/c-cpp-libfuzzer-afl-plus-plus.md)
- Go's native `testing.F` — [Go native fuzzing](references/go-native-fuzzing.md)
- Another ecosystem — use the project's supported engine and its upstream documentation.

Use more than one engine only when their instrumentation, mutation strategy, or
platform support creates a concrete benefit.

**Complete when:** every Commit field is concrete and fuzzing owns the search, or
Return names why fuzzing lacks leverage and transfers the risk.

## 2. Build a tight harness

A tight harness is:

- deterministic for the same input and build
- independent between invocations, with global and persistent state reset
- bounded in input size, memory, time, recursion, and output
- tolerant of malformed and empty input unless rejection itself violates the contract
- free of avoidable logging, network, GUI, process startup, and durable writes in the hot loop
- responsible for releasing resources on every path

Call the production entry point directly. Replace a slow network or UI adapter with the underlying parser or handler rather than mocking the logic under test. Never call `exit()` from the harness.

Do not bypass checks merely to inflate coverage. When an expensive checksum, signature, or envelope prevents deeper search, prefer a lower production seam that accepts validated input. If a fuzz-only bypass is necessary, preserve the assumptions the skipped check established and make the build flag impossible to enable in production.

Run the harness over empty, smallest-valid, malformed, and representative seed inputs before starting the engine. A harness crash, leak, or nondeterministic result is a harness defect until shown otherwise.

**Complete when:** seeds replay deterministically, malformed input is handled as specified, and persistent iterations leave no relevant state behind.

## 3. Choose an oracle

A target that only ignores a return value can find panics, sanitizer findings, timeouts, and process crashes; it cannot detect silent wrong answers. Add the strongest independent observation the contract supports:

- **Safety oracle** — no crash, undefined behavior, leak, resource exhaustion, or forbidden hang
- **Semantic oracle** — a successful result satisfies a public invariant or validator
- **Differential oracle** — optimized, unsafe, new, or alternate implementation agrees with an independent reference
- **Metamorphic oracle** — a transformed input preserves a stated relation, such as encode/decode roundtrip or normalization idempotence

Name a counterfeit defect for every semantic oracle. Keep the reference path simpler and independent; comparing two wrappers around the same implementation adds no discrimination.

**Complete when:** the target detects its named risk and each semantic assertion rejects a plausible counterfeit.

## 4. Design the input search

Seed with a small set of valid and boundary examples that reach distinct behavior. Keep coverage-contributing regression inputs; minimize rather than accumulate a large opaque corpus. Merge corpora from compatible campaigns through the engine's supported command.

Use a dictionary for stable tokens, delimiters, magic bytes, or keywords when the engine supports one. Use structure-aware generation or mutation when byte mutations are rejected before reaching meaningful logic. Preserve malformed-input exploration too: a generator that produces only valid values cannot challenge rejection paths.

When coverage stalls, inspect the corpus replay rather than the corpus count. Look for:

- an entry point the harness never calls
- an early validation wall
- unsupported input sizes or missing tokens
- nondeterminism that makes coverage unstable
- slow or stateful code consuming the budget
- an oracle that cannot observe deeper failures

Change one search constraint at a time and remeasure reach.

**Complete when:** risk-bearing regions are reachable or every remaining barrier has a recorded reason and next experiment.

## 5. Run and record the campaign

Run ordinary regression tests first and replay representative seeds. When the
ordinary suite is unavailable or already red, use current base-revision or CI
evidence when available and record the limitation; do not let a narrower green
result hide an affected failure. Demonstrate safely that the oracle can reject
its named counterfeit, or record why that failure path cannot be exercised
directly.

Run the smallest justified worker count under the declared CPU, memory, and wall
budget. Use the engine's supported worker model. Record the exact command,
revision, engine and compiler versions, instrumentation, target, corpus,
dictionary, worker count, input limit, timeout, elapsed time, and replay command
where available.

A clean local smoke establishes harness acceptance only. Report its conclusion
as: no failure found within the recorded campaign. Stop after the declared local
budget unless new reach or failure evidence identifies a distinct experiment.

Coverage measures target reach, not correctness. Compare it only across
compatible builds and corpora.

When another skill or plan owns the parent evidence, return the result to its
final audit.

**Complete when:** seeds replay; the ordinary regression result is green or
accounted for; the oracle's failure path has been exercised or its limitation
recorded; the campaign stays within its declared resources; another developer
can reproduce the command and corpus replay without the active fuzzer; and any
parent evidence is closed.

## 6. If the campaign finds a failure

1. Reproduce with the original target, build mode, options, and input.
2. Minimize the failing input with the engine's supported minimizer.
3. Classify product defect, harness defect, unsupported resource case, flaky execution, or infrastructure failure.
4. Deduplicate by root cause and meaningful stack, not filename or input bytes alone.
5. Show that the minimized input fails before the fix and passes after it.
6. Keep a durable regression: a normal focused test when it communicates the contract, plus the minimized corpus input when engine replay remains valuable.

A sanitizer report names an observed failure, not automatically its root cause. Inspect the first relevant frame and the violated contract before changing production code.

**Complete when:** the failure is minimized, reproducible, classified, fixed or tracked, and replayed by the project's normal or scheduled test path.

## 7. If continuous operation is warranted

For security-sensitive or heavily exposed targets, run minimized corpora as ordinary regression inputs and use a continuous fuzzing service when the project can support its toolchain and triage load. Replay useful corpora under compatible sanitizers. Track reach, unique actionable failures, time-to-reproduce, and stale targets; raw corpus size and crash count are not health metrics.
