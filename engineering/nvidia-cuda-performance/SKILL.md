---
name: nvidia-cuda-performance
description: >-
  NVIDIA CUDA performance engineering. Use when estimating, diagnosing, designing, reviewing, implementing, or validating GPU performance for CUDA kernels, CUDA-backed applications, RTX 3090 or SM86 targets, LLM inference, or intra-host multi-GPU scaling.
license: MIT
---

# NVIDIA CUDA performance

Shorten the declared result path by changing measured work, movement, placement, scheduling, or representation—and prove the effect outside the profiler.

## Scope

Use this skill for NVIDIA CUDA kernels and CUDA-backed applications, including RTX 3090/SM86 specialization, LLM inference, and intra-host multi-GPU execution.

Route a CPU-only or ordinary single-binary bottleneck to `$perform-like-jeff-and-sanjay`. Route multi-node networking, storage fabrics, and general ML training to domain-specific methods. Keep host inventories, measurements, and winning configurations in the target project rather than this portable skill.

Treat every optimization as a **gated move**. A technique becomes a candidate only after evidence supports its precondition. Counters such as utilization, occupancy, stalls, cache hit rate, queue time, roofline position, and NCCL bandwidth are clues—not diagnoses.

Use these evidence labels:

- **SOURCE GAP:** a stable technical claim lacks adequate primary evidence.
- **INSTANCE VALUE:** the answer depends on the target host, build, artifact, or runtime dispatch.
- **EMPIRICAL OPTIMUM:** the winner depends on the measured workload.

## Process

Route to the requested decision instead of running every step:

- **Estimate or plan:** Steps 1–2, the pre-implementation branch of Step 3, then Steps 4 and 8.
- **Diagnose:** Steps 1–4, then Step 8.
- **Design:** Steps 1–5, then Step 8.
- **Review:** reconstruct Steps 1–5 from available evidence, then apply Steps 7–8.
- **Implement:** Steps 1–7, then Step 8.
- **Validate a claimed gain:** reconstruct Steps 1–6, then apply Steps 7–8.

Reuse trustworthy artifacts. Enter Step 6 only when implementation is requested or authorized. When hardware access is unavailable, stop at the applicable design or review decision and record the deferred measurements.

### 1. Declare the performance decision

Record:

- **Target boundary:** the exact start and the condition under which the useful result is consumable.
- **Outcome:** latency, throughput, TTFT, inter-token latency, tail latency, capacity, energy, or another user-visible target.
- **Threshold:** the smallest improvement worth the shifted costs, or the evidence needed to set it.
- **Workload:** input shapes and distributions, batch or concurrency, cache state, precision, model, phase, and warmup state.
- **Guardrails:** correctness, numerical tolerance, quality, determinism, ordering, memory, power, thermals, compatibility, and fallback behavior.
- **Environment:** GPU identity and compute capability, host topology, driver, CUDA, compiler, libraries, build artifact, launch configuration, clocks, and power policy.

Mark each missing field as **SOURCE GAP**, **INSTANCE VALUE**, or **EMPIRICAL OPTIMUM**, with a concrete collection step. Product names and published benchmarks do not fill target-environment fields.

**Complete when:** the result boundary, outcome, threshold, workload, guardrails, and environment are either evidenced or paired with a collection step, and the request remains inside this skill's scope.

### 2. Build the causal budget

Model six objects:

1. **Target boundary:** the result interval from Step 1.
2. **Work graph:** semantic operations and required precedence.
3. **Demand vector:** operations, bytes at named interfaces, launches, allocations, transfers, collectives, and capacity footprint.
4. **Machine model:** execution resources, memory interfaces, residency limits, engines, links, topology, clocks, and installed software support.
5. **Realized schedule:** observed placement, queueing, overlap, contention, waits, and imbalance.
6. **Causal hypothesis:** a feasible intervention and its predicted mediator and target outcome.

Use dependency span and resource demand as lower bounds, not runtime predictions:

```text
observed time >= max(dependency span, demand(resource) / capacity(resource))
```

Name every boundary. Host API time, queue delay, device execution, synchronization wait, and end-to-end latency are different intervals. Logical bytes, requested sectors, cache traffic, link traffic, and storage footprint are different quantities.

Estimate only enough to reject implausible causes or choose the next measurement. State the assumptions and an observation that would falsify the dominant term.

**Complete when:** the work graph, dominant demand, relevant machine limits, overlap assumptions, uncertainty, and falsifier are explicit enough to reject at least one direction or select the next evidence collection.

### 3. Establish the evidence baseline

Start with correctness. Record a trusted output, application quality criterion, or numerical tolerance. Run applicable Compute Sanitizer checks for memory, shared-memory races, initialization, and synchronization; these checks cover named defect classes rather than proving correctness.

For an existing target:

1. Preserve an unprofiled end-to-end baseline with declared warmup, samples, workload, environment, and variance.
2. Use Nsight Systems to locate consequential host intervals, launches, kernels, transfers, collectives, waits, and idle gaps. Add NVTX ranges when the timeline cannot identify application phases.
3. Select kernels by critical-path consequence, not by impressive counters or total duration alone.
4. Use Nsight Compute on selected kernels with the smallest metric set that tests the hypothesis. Inspect the installed tool's sets and sections instead of assuming a preset's contents.
5. Record profiler overhead, replay mode, clock/cache controls, and any behavior changed by instrumentation.

For a target that cannot be run, use source, build configuration, artifact metadata, bounded estimates, and comparable measurements. Label the result unmeasured. Specify the system trace, kernel profile, benchmark, and correctness check that will validate it later.

A **bottleneck** is a causal constraint for which a feasible intervention is predicted—and then shown—to improve the declared outcome. Low occupancy, high utilization, or a roofline classification alone does not meet that definition.

**Complete when:** the baseline is reproducible and discriminates the expected effect, or the unavailable-hardware branch records bounded evidence and an executable validation plan without claiming a gain.

### 4. Write one gated causal hypothesis

Use this record:

```text
OUTCOME: target metric and threshold
CRITICAL SEGMENT: dependency-connected interval that can affect the outcome
EVIDENCE: observation, estimate, and evidence label
MOVE: one proposed transformation
GATE: evidence that its precondition holds
ARCHITECTURE/RUNTIME GATE: required hardware, build, feature, shape, and dispatch
PREDICTED MEDIATOR: direct event expected to change
LOSE-CONDITION: workload or constraint under which the move gets worse
SHIFTED COST: setup, memory, traffic, code size, latency, complexity, or observability
FALSIFIER: result that disproves the mechanism
CONTRACTS: correctness, numerical, quality, ordering, and operational invariants
```

Load [CUDA technique gates](references/nvidia-cuda-gates.md) after the baseline identifies the constrained resource. Then load only the branches that apply:

- RTX 3090, GA102, or compute capability 8.6: [SM86 and RTX 3090 gates](references/sm86-rtx3090.md).
- LLM serving or generation: [LLM inference gates](references/llm-inference.md).
- More than one GPU: [multi-GPU gates](references/multi-gpu.md).

Prefer, subject to evidence:

1. prove the critical path;
2. remove or reduce demand;
3. repair representation, placement, fragmentation, and avoidable movement;
4. repair measured memory access and traffic;
5. repair execution efficiency;
6. expose legal overlap;
7. amortize fixed runtime costs;
8. specialize a demonstrated regime;
9. change precision or encoding after dispatch and quality gates;
10. distribute only after the best simpler baseline.

**Complete when:** one move has stronger causal support than its alternatives, every field is filled, the predicted target gain can meet Step 1's threshold, and every unmeasured effect is labeled.

### 5. Set the implementation boundary

Choose the smallest existing module or kernel boundary that can test the hypothesis. Specify:

- the public and numerical behavior that stays stable;
- ownership, lifetime, aliasing, layout, alignment, ordering, stream, and synchronization contracts;
- supported shapes, precision, compute capability, build target, and runtime fallback;
- the selected-kernel or SASS evidence required when the claim depends on a specific instruction path;
- the correctness oracle and direct mechanism measurement;
- the feature, shape, architecture, or workload guard that limits blast radius.

Keep a general fallback unless the narrower contract is deliberate and approved. A source guard such as `__CUDA_ARCH__ >= 800`, a packaged cubin, or a startup candidate list proves eligibility or packaging—not runtime dispatch or performance.

**Complete when:** the seam, preserved contracts, supported regime, dispatch proof, fallback, oracle, mechanism measurement, and scope guard are named before implementation.

### 6. Implement the hypothesis

Make the smallest coherent change that tests the predicted mediator. Separate independent moves when practical. If moves must combine, retain per-mechanism evidence and label attribution as bundled.

Keep architecture-specific code behind the Step 5 guard. Preserve build provenance, inspect generated artifacts when instruction choice matters, and keep profiling annotations out of the measured path unless their overhead is shown negligible.

**Complete when:** the implementation maps directly to the hypothesis, the supported regime and fallback are exercised, and unrelated tuning guesses are absent or independently justified.

### 7. Validate from mechanism to result

Run all applicable levels:

1. **Correctness:** reference outputs, tolerances, quality, race/synchronization checks, edge shapes, fallbacks, and rank or stream orderings.
2. **Build and dispatch:** runtime compute capability, artifact target, selected kernel, and expected instructions when material.
3. **Mechanism:** predicted changes in operations, launches, bytes, sectors, spills, waits, occupancy limit, graph replay, acceptance, imbalance, or another direct mediator.
4. **Kernel:** stable local timing and hypothesis-specific counters, with profiler overhead excluded from performance claims.
5. **Scale:** representative shapes, batches, contexts, concurrency, cache states, device counts, and sustained thermal conditions.
6. **Macro:** unprofiled end-to-end comparison against the declared outcome and threshold.
7. **Attribution:** revert or ablate the move and confirm that the improvement disappears.
8. **Regressions:** memory, quality, tails, energy, uncommon paths, portability, observability, and maintenance cost.

Reject or revise when correctness fails, the mediator does not move, the critical path does not shorten, the result is noise, a lose-condition occurs, or the system gain does not justify shifted costs. If performance improves without the predicted mediator, report an empirical gain with unknown attribution.

**Complete when:** correctness, dispatch, mechanism, kernel, scale, macro, attribution, and regressions are measured or explicitly unavailable, and the decision follows from the evidence rather than one counter.

### 8. Report bounded evidence

Report only the stages performed:

```text
Context: target boundary, workload, environment, outcome, threshold
Baseline: correctness and measurements
Model: work graph, dominant demand, machine limit, realized schedule
Hypothesis: move, gates, mediator, lose-condition, shifted cost, falsifier
Boundary: contracts, supported regime, dispatch proof, fallback
Evidence: correctness, dispatch, mechanism, kernel, scale, macro, attribution
Decision: keep, revise, revert, or gather evidence
Deferred: unavailable hardware, tests, profiles, or source gaps
```

Attach each number to its hardware, build, artifact, workload, warmup, sample count, and measurement scope. Published examples justify experiments for their named case; they do not predict gains on a different GPU or workload.

**Complete when:** a cold reader can distinguish facts, estimates, and measurements; reproduce the performed work; see every material tradeoff; and decide the next action without first reading the implementation.

## Source basis

This skill is an original synthesis of NVIDIA documentation, implementation sources, and GPU-systems research. See [provenance and source canon](PROVENANCE.md).
