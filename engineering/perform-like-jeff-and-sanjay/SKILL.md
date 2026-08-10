---
name: perform-like-jeff-and-sanjay
description: >-
  Performance engineering for a single binary. Use when designing or reviewing performance-sensitive code, estimating resource costs, diagnosing a measured bottleneck or flat profile, implementing a performance change, or validating a claimed speedup.
license: Apache-2.0
---

# Perform like Jeff and Sanjay

Engineer performance by changing the amount, frequency, placement, representation, or coordination of work—and proving the effect at the scope that matters.

## Scope

This skill covers performance within a **single binary**. Route distributed-systems performance and ML-hardware tuning to domain-specific methods.

Think about performance during design. Take simple faster choices when they preserve readability and local reasoning. Require estimates and measurements before a consequential optimization or a material performance-versus-simplicity tradeoff.

Treat every optimization as a **gated move**. A named technique is not a recommendation until its precondition is supported. If the gate is unknown, collect the missing evidence or decline the move.

Concrete C++ and Protocol Buffer mechanisms are conditional examples, not portable defaults.

## Process

Route to the requested decision rather than running the whole lifecycle unconditionally:

- **Estimate:** Steps 1–2, then Step 8.
- **Diagnose a bottleneck or flat profile:** Steps 1–4, then Step 8.
- **Design a performance change:** Steps 1–2, take the applicable Step 3 branch, then Steps 4–5 and Step 8.
- **Review a proposed change:** reconstruct Steps 1–5 from available evidence, then apply Steps 7–8.
- **Implement:** Steps 1–7, then Step 8.
- **Validate a claimed speedup:** reconstruct Steps 1–6, then apply Steps 7–8.

Use existing trustworthy artifacts rather than repeating completed work. Enter Step 6 only when implementation is requested or authorized, and stop after reporting the requested decision.

### 1. Frame the performance job

Inspect the applicable project rules, target code, callers, tests, deployment shape, and existing performance artifacts. Record:

- **Code class:** test, setup/initialization, repeated application path, or shared library.
- **Outcome:** latency, throughput, aggregate CPU, I/O, allocations, copied bytes, resident memory, cache behavior, lock wait/hold time, binary size, build/link time, or observability quality.
- **Decision threshold:** the smallest target-scope improvement worth the shifted costs, or the decision owner and evidence needed to set it.
- **Workload:** input-size and cardinality distributions, common and failure cases, concurrency, object lifetimes, reuse, and hardware/runtime constraints.
- **Guardrails:** correctness, API compatibility, ownership, ordering, error detail, synchronization, memory, fallback latency, code size, and diagnostics.
- **Scale:** executions per request, request rate, object population, expected lifetime of the software, and number of downstream users.

Use the code class to set effort, not to dismiss cost. Slow tests lengthen development cycles; setup can still dominate short-lived tools; library defaults multiply across unknown callers.

**Complete when:** every field above is either grounded in evidence or marked unknown with a concrete way to obtain it, and the target remains inside the single-binary scope.

### 2. Estimate the causal budget

Build a back-of-the-envelope model before choosing an implementation:

```text
operation count × approximate unit cost = aggregate resource demand
```

Separate terms for CPU operations, bytes moved, I/O, allocations, lock operations, cache-line traffic, code emitted, or other relevant resources. Then model observed latency or throughput separately:

```text
aggregate demand + serial dependencies + contention + scheduling + variance
  constrained by available CPU, memory bandwidth, and I/O capacity
  = observed latency and throughput
```

State dominant assumptions and their source. Hardware tables and historical benchmark numbers are contextual inputs, never constants. Refine only the terms that could change the decision. Name the observation that would falsify the estimate.

**Complete when:** operation counts, unit costs, overlap assumptions, dominant term, uncertainty, and falsifier are explicit enough to reject at least one implausible direction or justify what must be measured next.

### 3. Establish the applicable evidence baseline

**Existing-target branch:** measure an optimized, production-relevant build with enough symbols or metadata to interpret profiles. Exercise representative data, size distributions, concurrency, and configuration. Record hardware, runtime/compiler, build mode, benchmark command, warmup, sample count, variance, and system load when available.

Collect evidence for the suspected resource:

- CPU profile and dynamic call stacks for executed work.
- Allocation/heap profile for count, bytes, and retention.
- Lock profile for acquisition count, hold time, and wait time.
- Hardware counters for cache, branch, TLB, or bandwidth hypotheses.
- I/O and scheduler evidence for blocking, handoffs, and context switches.
- Symbol or binary-size evidence for emitted-code hypotheses.
- A stable microbenchmark when the mechanism can be isolated without misrepresenting the system.

Use profiling as codebase reconnaissance: read loops and routines high in the dynamic stack, not only the hottest leaves.

**Flat profile branch:** inspect high-stack loops, repeated boundary crossings, allocations, contention, cache misses, I/O, and code size. A flat CPU profile does not identify the cause of a slowdown. Treat possible causes as hypotheses until before-and-after measurements confirm them. Do not use a function's CPU percentage as a hard limit on its latency impact; waiting, contention, and serial dependencies can amplify it.

**Pre-implementation design branch:** when the target does not yet exist, use the Step 2 estimate, workload bounds, and comparable measurements when available. Cite each comparable and its material differences. Mark the expected effect unmeasured. Specify the instrumentation or measurement hook, benchmark, and target-scope measurement that will validate the hypothesis after implementation. Do not claim a speedup.

**Complete when:** an existing-target baseline is reproducible, directly measures the relevant resource, and has low enough noise to distinguish the expected effect; or a pre-implementation design records bounded assumptions, labeled estimates, relevant comparables, and a concrete validation plan. Otherwise report what evidence is missing instead of making an optimization claim.

### 4. Write one gated causal hypothesis

Use this record:

```text
BOTTLENECK: observed or estimated constrained resource and scope; label the evidence class
MULTIPLIER: frequency, probability, cardinality, contention, or emitted copies
MOVE: proposed transformation
GATE: evidence that its precondition holds
LOSE-CONDITION: workload or constraint under which it gets worse
SHIFTED COST: setup, memory, miss path, latency, code size, complexity, or observability
FALSIFIER: result that disproves the mechanism
CONTRACTS: semantics and operational properties that must remain true
```

Using the measured or pre-implementation evidence from Step 3, choose the portable move from [technique gates](references/technique-gates.md). Then, before naming a concrete facility, load only the matching specialized branch: [C++ representations and containers](references/cpp-and-protobuf-gates.md#c-representations-and-containers), [C++ ownership and lifecycle](references/cpp-and-protobuf-gates.md#c-ownership-and-lifecycle), [C++ code size and compiler controls](references/cpp-and-protobuf-gates.md#c-code-size-and-compiler-controls), or [Protocol Buffers](references/cpp-and-protobuf-gates.md#protocol-buffers).

Prefer, subject to evidence:

1. remove work;
2. reduce its frequency or probability;
3. expose whole-input or bulk structure;
4. improve the algorithm or maintained invariant;
5. repair an API or representation that forces waste;
6. reduce allocation, copying, and locality costs;
7. reduce coordination or safely overlap work;
8. specialize a demonstrated common subset;
9. assist the compiler or use hardware-specific operations.

A lower rung may come first when the available evidence identifies it as the actual or expected constraint. Reject named types or tricks whose mechanism, gate, and lose-condition cannot be stated for this workload.

**Complete when:** one move has stronger causal evidence than its alternatives, all record fields are filled, the measured or estimated gain meets the Step 1 decision threshold at the target scope, and every unmeasured effect is explicitly labeled.

### 5. Set the implementation boundary

Prefer the smallest change behind an existing deep-module boundary. Before editing, specify:

- the public behavior and resource contract that remain stable;
- whether a new bulk, view, workspace, cache, or synchronization contract changes ownership, lifetime, ordering, errors, partial completion, atomicity, or observability;
- the common path and complete fallback;
- cache invalidation, object reset, or lock-free reclamation where applicable;
- the correctness oracle and the benchmark that exercise the proposed mechanism;
- the feature or workload guard that limits blast radius.

Keep general behavior available unless the narrower contract is intentional and approved. Convert recoverable errors or production checks into preconditions only when callers establish the invariant and the semantic change is explicit.

**Complete when:** the seam, preserved contracts, changed contracts, fallback, correctness oracle, and blast-radius guard are all named before the implementation changes.

### 6. Implement the hypothesis, not a bundle of guesses

Make the smallest coherent change that tests the causal mechanism. Preserve attribution by separating independent moves when practical. If techniques must combine, retain per-mechanism counters or benchmarks and label the result as bundled.

Keep low-level code inside a tested module. Inspect generated code before manual unrolling, forced inline/no-inline directives, raw-pointer rewrites, or architecture-specific instructions. Treat logging, tracing, checks, clocks, and statistics as production work while preserving the observability budget established in Step 1.

**Complete when:** the implementation maps directly to the hypothesis, uncommon and fallback behavior remain exercised, and unrelated speculative tweaks are absent or independently justified.

### 7. Validate from mechanism to system

Run all applicable levels:

1. **Correctness:** existing tests plus edge, failure, fallback, ownership, ordering, and concurrency cases.
2. **Mechanism:** verify that the predicted event changed—operations, allocations, copied bytes, cache misses, lock waits, I/O, emitted text, or another direct counter.
3. **Micro:** compare stable local benchmarks with enough samples to separate signal from noise.
4. **Scale:** test relevant sizes, cardinalities, contention, prior limits, and saturated-resource cases.
5. **Macro:** measure the subsystem and end-to-end workload against the Step 1 outcome.
6. **Regressions:** check aggregate CPU, wall time, memory/retention, code size, uncommon latency, contention, observability, and maintenance complexity.

Compare resource cost and elapsed time separately. Parallelism can reduce wall time while leaving or increasing aggregate work. A local gain can disappear end to end; complementary bundled changes can amplify one another.

Reject or revert when the result is noise, the workload is unrepresentative, the predicted resource does not move, a lose-condition occurs, or the system gain does not justify the shifted costs.

**Complete when:** correctness passes; mechanism, micro, and macro evidence are either measured or explicitly marked unavailable; relevant scaling and regressions are covered; and the final decision follows from those results.

### 8. Report bounded evidence

Report the fields produced by the selected route. Mark unperformed lifecycle stages as outside the requested route instead of inventing evidence.

```text
Context: code class, workload, environment, target outcome
Baseline: measurements and scope
Estimate: dominant terms and assumptions
Hypothesis: move, gate, lose-condition, shifted cost, falsifier
Change: implementation boundary and contracts
Evidence: mechanism, micro, scale, macro, regressions
Attribution: isolated or bundled
Decision: keep, revise, revert, or gather more evidence
Uncertainty: missing or weak evidence
```

Keep each number attached to its hardware, build, workload, sample size, and measurement scope. Describe historical examples as evidence for their named case, not promised gains.

**Complete when:** a cold reader can reproduce the performed estimate, diagnosis, review, or comparison; distinguish fact from estimate; see every material tradeoff; and decide the next action without reading the patch first.

## Source basis

This skill is an original adaptation of Jeffrey Dean and Sanjay Ghemawat's *Performance Hints*. See [provenance, source coverage, license, and non-endorsement](PROVENANCE.md).
