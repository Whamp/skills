# NVIDIA CUDA technique gates

Load this reference after a baseline identifies the constrained resource. A technique remains a hypothesis until its gate is supported and its predicted mediator changes.

## Remove or reduce demand

### Delete, skip, or reduce work

- **Mechanism:** remove an unnecessary operation, reject work with a cheap conservative test, reduce execution frequency, or hoist a stable derivation.
- **Gate:** semantics prove the result unnecessary or reusable; the guard or setup costs less than the work skipped.
- **Loses when:** the guard rarely skips work, reused state becomes stale, setup does not amortize, or removed diagnostics were required.
- **Risks:** changed accumulation, ordering, error, or observability behavior.
- **Verify:** count operations and skips; measure guard/setup cost, direct demand, and end-to-end time; test the complete fallback.

### Batch small operations

- **Mechanism:** amortize host API, launch, transfer, allocation, synchronization, or library setup costs.
- **Gate:** fixed cost is material and operations can be grouped without violating latency or ordering.
- **Loses when:** batching delays critical work, increases memory, reduces useful concurrency, or creates poorly shaped kernels.
- **Risks:** changed boundaries, partial failures, ordering, and queueing policy.
- **Verify:** show fewer submissions or transfers and shorter critical-path time; a longer queue delay alone is not failure.

### Fuse compatible operations

- **Mechanism:** avoid intermediate global-memory materialization, submissions, launches, and ordering boundaries.
- **Gate:** adjacent operations exchange a material intermediate and can share a legal execution boundary.
- **Loses when:** registers, shared memory, synchronization, code size, or reduced parallelism outweigh saved work.
- **Risks:** aliasing, numerical order, synchronization, and divergent fallback behavior.
- **Verify:** measure intermediate bytes, kernel count, resource use, kernel time, and unprofiled end-to-end time.

## Repair representation and movement

### Change layout or placement

- **Mechanism:** place data where it is consumed, make the common access contiguous, separate hot and cold fields, or choose a representation that avoids conversion.
- **Gate:** measured movement, indirection, conversion, fragmentation, or cache traffic is consequential.
- **Loses when:** the new layout damages another common access, adds transpose/conversion cost, or duplicates too much state.
- **Risks:** alignment, padding, indexing, ownership, serialization, and compatibility.
- **Verify:** name the memory interface; compare logical and transferred bytes, conversions, footprint, cache traffic, and target outcome.

### Reduce allocation lifecycle work

- **Mechanism:** reuse storage, pool compatible lifetimes, reserve expected capacity, or use stream-ordered allocation.
- **Gate:** allocation/free or allocation-induced synchronization is material and lifetime/order contracts are known.
- **Loses when:** allocation is infrequent, retained high-water memory grows, or ordering machinery costs more than reuse saves.
- **Risks:** use-after-free, cross-stream dependency bugs, stale contents, and memory retention.
- **Verify:** measure API time, synchronization gaps, allocation count, retained memory, and end-to-end time; exercise cross-stream ordering.

### Reduce host-device and device-device transfers

- **Mechanism:** keep data resident, transfer only required fields, batch small copies, or overlap a necessary transfer.
- **Gate:** transfer time or bytes lie on the critical path.
- **Loses when:** pinning/setup costs dominate, memory pressure rises, or batching increases latency.
- **Risks:** asynchronous buffer lifetime, stale replicas, direction errors, and incomplete transfer use.
- **Verify:** count bytes and operations at the named interface; measure achieved bandwidth, timeline placement, correctness, and complete result time.

## Repair memory traffic

### Coalesce global access

- **Mechanism:** align adjacent thread accesses so requests use fewer memory sectors.
- **Gate:** requested sectors per useful byte exceed the architecture-appropriate access pattern and the traffic is consequential.
- **Loses when:** accesses are already efficient, reordering adds more work, or edge handling dominates.
- **Risks:** misalignment, partial tiles, index errors, and changed layout contracts.
- **Verify:** inspect instructions, requests, sectors, and bytes at the chosen cache/memory boundary; compare effective bandwidth and kernel time.

### Tile and stage in shared memory

- **Mechanism:** reuse a tile or transform an inefficient global layout through lower-latency shared storage.
- **Gate:** reuse or access repair saves enough global traffic; the tile fits resource and synchronization budgets.
- **Loses when:** reuse is weak, shared-memory traffic or barriers dominate, bank conflicts remain, or residency falls below what the kernel needs.
- **Risks:** races, missing barriers, edge tiles, bank assumptions, and dynamic-shared-memory launch requirements.
- **Verify:** show reduced global traffic or repaired sectors, acceptable shared-memory conflicts, resource use, and end-to-end gain.

### Use asynchronous global-to-shared staging

- **Mechanism:** overlap later-tile movement with current-tile computation and avoid an intermediate register where the hardware path permits.
- **Gate:** target hardware and generated code support the path; alignment and copy widths are legal; independent computation can hide latency.
- **Loses when:** computation is too short, waits dominate, alignment falls back, or pipeline state consumes too many resources.
- **Risks:** reading before completion, false alignment assertions, divergent pipeline commits, and premature stage reuse.
- **Verify:** prove the expected instruction and dispatch, compare synchronous and asynchronous variants, measure stage waits, traffic, kernel time, and macro time.

### Add double buffering or multistage pipelines

- **Mechanism:** let producer movement and consumer computation use different stages concurrently.
- **Gate:** producer and consumer work can overlap and one-stage execution exposes movement latency.
- **Loses when:** stages remain empty or full, acquire/wait frequently blocks, or shared-memory/register demand removes useful residency.
- **Risks:** stage-order errors, unmatched acquire/commit/wait/release, divergence, and buffer reuse races.
- **Verify:** sweep stage count; measure wait time, overlap, resources, kernel time, and the workload regimes where the winner changes.

## Repair execution efficiency

### Tune decomposition and launch geometry

- **Mechanism:** map work to blocks, warps, and threads so the GPU has enough useful parallel work without excessive tails, imbalance, or resource pressure.
- **Gate:** traces and kernel metrics show underfilled work, poor load balance, excessive tails, or a resource-limited launch.
- **Loses when:** more blocks duplicate work, smaller tiles reduce locality, larger blocks increase tails, or the scheduler already has enough eligible work.
- **Risks:** incomplete coverage, integer overflow, shape-specific failures, and changed reduction order.
- **Verify:** sweep representative shapes and launch choices; record active blocks, resident and eligible warps, issue rate, tails, and target time.

### Change occupancy-limiting resources

- **Mechanism:** reduce registers, spills, shared memory, threads, or blocks when resource limits leave too few eligible warps to hide relevant latency.
- **Gate:** a named resource suppresses residency, issue capacity is unused during consequential latency, and more eligible warps are plausibly useful.
- **Loses when:** current occupancy already hides latency or resource reduction causes spills, extra instructions, or worse locality.
- **Risks:** compiler instability, hidden local-memory traffic, and architecture-specific thresholds.
- **Verify:** connect resource limit to residency, eligibility, issue, and time. Raising occupancy without shortening time rejects the move.

### Reduce divergence and imbalance

- **Mechanism:** regroup similar work, remove avoidable branches, compact active items, or balance partitions.
- **Gate:** divergent or imbalanced work creates measured inactive lanes, stragglers, or synchronization wait on the critical path.
- **Loses when:** regrouping and compaction cost more than inactive work or destroy locality.
- **Risks:** unstable ordering, dropped work, changed exception paths, and new prefix-sum/compaction bugs.
- **Verify:** measure active lanes, branch efficiency, partition durations, compaction overhead, and end-to-end time.

### Reduce synchronization and ordering edges

- **Mechanism:** remove an unnecessary dependency, narrow synchronization scope, use events for precise ordering, or move independent work apart.
- **Gate:** a specific wait or ordering edge delays the critical path beyond the semantic dependency.
- **Loses when:** the edge enforces correctness, reduced ordering increases interference, or event management adds more overhead.
- **Risks:** data races, memory-order violations, early consumption, and nondeterminism.
- **Verify:** state the memory and ordering contract; run sanitizer and stress checks; show the edge disappears and the target interval shortens.

### Repair instruction mix or generated code

- **Mechanism:** reduce redundant or low-throughput instructions, expose a supported Tensor Core path, or remove compiler obstacles such as harmful alias uncertainty.
- **Gate:** a consequential kernel's generated code and throughput metrics identify the instruction path as limiting.
- **Loses when:** code size, conversions, spills, or portability costs exceed instruction savings.
- **Risks:** numerical changes, undefined alias/alignment assumptions, compiler-version sensitivity, and unsupported instructions.
- **Verify:** inspect the executed artifact before and after; measure instruction mix, resource effects, kernel time, correctness, and macro time.

## Expose legal overlap

### Use streams and asynchronous execution

- **Mechanism:** expose independent kernels or copies so the runtime may overlap them on available engines and resources.
- **Gate:** dependencies permit concurrency, hardware supports the needed engines, and serialized work lies on the critical path.
- **Loses when:** operations compete for the same limiting resource, dependencies serialize them, or overlap increases tail latency.
- **Risks:** missing events, legacy-default-stream semantics, buffer lifetime, and early result consumption.
- **Verify:** prove overlap on a system timeline and a shorter critical path. Asynchronous API use alone proves neither.

### Pipeline producer and consumer phases

- **Mechanism:** buffer independent stages to reduce rendezvous and hide one stage behind another.
- **Gate:** stage dependencies and backpressure permit overlap; both stages have enough work.
- **Loses when:** imbalance, queueing, memory, or staleness grows, or one stage requires all resources.
- **Risks:** boundedness, shutdown, failure propagation, and ownership across stages.
- **Verify:** measure stage times, queue depth, waiting, memory, tails, and sustained throughput.

## Amortize runtime costs

### Use CUDA Graphs

- **Mechanism:** instantiate a repeated dependency graph and replay it with less host submission work.
- **Gate:** launch/API overhead is consequential and the operation topology is capturable or legally updateable.
- **Loses when:** construction, update, graph variants, or fallbacks dominate; device work or communication is already limiting.
- **Risks:** capture restrictions, stale pointers, shape mismatch, and changed dependency order.
- **Verify:** record graph hits and fallbacks, API/launch intervals, device work, and unprofiled iteration time across shapes.

### Reuse library plans, workspaces, and prepared formats

- **Mechanism:** amortize algorithm search, layout conversion, packing, or workspace allocation.
- **Gate:** the prepared artifact is reused under a stable shape, datatype, device, and version contract.
- **Loses when:** workload variation causes churn, memory retention is excessive, or preparation only shifts startup cost.
- **Risks:** stale plan keys, incompatible artifacts, concurrency, and hidden version coupling.
- **Verify:** separate startup from steady state; measure hit/reuse rate, retained memory, fallback, and target outcome.

## Specialize a demonstrated regime

### Autotune or specialize shapes

- **Mechanism:** choose tile, stage, warp, or implementation parameters for a recurring input class.
- **Gate:** input variation changes the measured optimum and enough reuse amortizes tuning and code size.
- **Loses when:** keys omit relevant variation, tuning costs recur, or variants fragment instruction cache and maintenance.
- **Risks:** mutated inputs during tuning, stale caches, unsupported tails, and nondeterministic selection.
- **Verify:** differential-test every candidate, benchmark every supported key class, retain fallback, and record the selected artifact.

### Use a persistent or cooperative kernel

- **Status:** research-only until a target-specific case establishes scheduling, residency, progress, and lose-conditions.
- **Potential mechanism:** retain state, reuse data, or replace repeated launches with long-lived work distribution.
- **Minimum gate:** repeated work and launch/state setup are consequential; resident blocks can make progress without starving required work.
- **Risks:** deadlock, unfairness, reduced coexistence, teardown complexity, and architecture-specific occupancy.
- **Verify:** require a nonpersistent baseline, progress/correctness stress tests, sustained workload traces, and end-to-end attribution.

## Change precision or implementation

### Quantize or use reduced precision

- **Mechanism:** reduce storage and traffic or use a higher-throughput supported arithmetic path.
- **Gate:** hardware, library, kernel, shape, and dispatch support the format; conversion/scaling cost and application quality are acceptable.
- **Loses when:** dequantization, scaling, calibration, or conversion erases the gain; the phase is compute-bound elsewhere; quality crosses its limit.
- **Risks:** overflow, underflow, clipping, NaN/Inf, double quantization, and task-quality regression.
- **Verify:** prove selected instructions/kernel, conversion cost, bytes, kernel and macro time, memory/capacity, and task-level quality.

### Substitute a tuned library or operator

- **Mechanism:** use a maintained implementation with architecture-specific algorithms, fusion, and dispatch.
- **Gate:** semantics, shape, layout, precision, workspace, reproducibility, and version support match the target.
- **Loses when:** conversion, workspace, unsupported shapes, or fallback costs exceed the custom path.
- **Risks:** numerical behavior, nondeterminism, opaque dispatch, and version-specific plans.
- **Verify:** compare complete costs across the workload distribution; inspect dispatch and preserve exact build/library versions.

### Change compiler or code-generation controls

- **Mechanism:** select the intended target, preserve device link-time information, control optimization, or expose source-to-SASS correspondence.
- **Gate:** artifact inspection identifies a build or code-generation cause.
- **Loses when:** code size, compile time, numerical behavior, compatibility, or another architecture regresses.
- **Risks:** PTX JIT differences, missing cubins, fast-math changes, and debug/profiling artifacts affecting code.
- **Verify:** retain build provenance; inspect fatbin, PTX, cubin, and SASS as applicable; benchmark all supported architectures and configurations.

## Core sources

- [CUDA C++ Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html)
- [CUDA Programming Guide: asynchronous execution](https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/asynchronous-execution.html)
- [CUDA Programming Guide: asynchronous copies](https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/async-copies.html)
- [CUDA Programming Guide: pipelines](https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/pipelines.html)
- [CUDA Programming Guide: CUDA Graphs](https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/cuda-graphs.html)
- [Nsight Systems User Guide](https://docs.nvidia.com/nsight-systems/UserGuide/index.html)
- [Nsight Compute Profiling Guide](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html)
- [Compute Sanitizer](https://docs.nvidia.com/compute-sanitizer/ComputeSanitizer/index.html)
- [CUDA Binary Utilities](https://docs.nvidia.com/cuda/cuda-binary-utilities/index.html)
