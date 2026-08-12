---
name: fuzzing
description: Coverage-guided fuzzing for implementation and test work on input-processing and memory-safety boundaries. Use when a feature or bug touches parsers, lexers, decoders, deserializers, codecs, file formats, protocol handlers, malformed, chunked, or adversarial input, unsafe or FFI code, or crash, hang, and resource-exhaustion risks; also use when designing or running fuzz targets, engines, oracles, seeds and corpora, coverage campaigns, crash minimization, and regression conversion.
---

# Fuzzing

A fuzz target combines generated input, coverage feedback, a tight harness, and an oracle. The campaign is useful only when failures reproduce and the harness can reach the behavior at risk.

## Route the engine

- Rust with cargo-fuzz and libFuzzer — read [cargo-fuzz](references/cargo-fuzz.md).
- C or C++ with libFuzzer or AFL++ — read [C and C++ fuzzing](references/c-cpp-libfuzzer-afl-plus-plus.md).
- Go's native `testing.F` — read [Go native fuzzing](references/go-native-fuzzing.md).
- Broad generated values or operation sequences where coverage feedback is not the search signal — load `property-based-testing` instead.

Use more than one engine only when their instrumentation, mutation strategy, or platform support creates a concrete benefit. Do not multiply campaigns by default.

## 1. Frame the campaign

Write the campaign contract before the harness:

```text
Target: <narrow production entry point>
Risk: <crash, undefined behavior, hang, or semantic defect>
Input model: <bytes, structured value, or operation sequence>
Oracle: <observable failure condition>
Engine: <existing project tool or justified choice>
Budget: <local smoke, bounded campaign, or continuous service>
Regression path: <where minimized failures will live>
```

Good targets include parsers, decoders, protocol and file-format handlers, compression or serialization code, unsafe memory operations, and FFI boundaries. Business logic can also benefit when coverage-guided mutation and its oracle fit better than direct examples or property generators; choose by search mechanism, not category labels.

**Complete when:** every field is concrete and the target owns enough behavior to expose the risk without booting an unrelated system.

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

Run ordinary regression tests first; seed replay should already be green. Start with a short smoke campaign, then use a bounded local or CI budget. Use the engine's documented worker model rather than launching ad hoc copies that corrupt or duplicate state.

Record the source revision, engine and compiler versions, sanitizer or instrumentation mode, target, corpus, dictionary, worker count, maximum input size, timeout, and random seed or replay command where available. Preserve logs needed to distinguish product failure, harness failure, timeout, and infrastructure exhaustion.

Coverage is a diagnostic for target reach, not proof of correctness. Compare coverage only across compatible builds and corpora. Optimize executions per second only after confirming that the faster harness preserves the same relevant behavior and oracle.

**Complete when:** another developer can reproduce the campaign configuration and replay its corpus without the active fuzzer.

## 6. Triage every failure

1. Reproduce with the original target, build mode, options, and input.
2. Minimize the failing input with the engine's supported minimizer.
3. Classify product defect, harness defect, unsupported resource case, flaky execution, or infrastructure failure.
4. Deduplicate by root cause and meaningful stack, not filename or input bytes alone.
5. Show that the minimized input fails before the fix and passes after it.
6. Keep a durable regression: a normal focused test when it communicates the contract, plus the minimized corpus input when engine replay remains valuable.

A sanitizer report names an observed failure, not automatically its root cause. Inspect the first relevant frame and the violated contract before changing production code.

**Complete when:** the failure is minimized, reproducible, classified, fixed or tracked, and replayed by the project's normal or scheduled test path.

## 7. Operate continuously

For security-sensitive or heavily exposed targets, run minimized corpora as ordinary regression inputs and use a continuous fuzzing service when the project can support its toolchain and triage load. Replay useful corpora under compatible sanitizers. Track reach, unique actionable failures, time-to-reproduce, and stale targets; raw corpus size and crash count are not health metrics.

## Review checklist

- [ ] Target, risk, oracle, engine, budget, and regression path are named.
- [ ] The harness is deterministic, bounded, isolated, and tolerant of malformed input.
- [ ] Semantic failures have an independent oracle and counterfeit.
- [ ] Seeds and structure help reach behavior without excluding malformed cases.
- [ ] Coverage and throughput changes preserve the target's meaning.
- [ ] Campaign configuration and failures replay outside the active fuzzer.
- [ ] Minimized failures become durable regression evidence.
