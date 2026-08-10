# Technique gates

Load this reference after the baseline identifies a resource. Each move stays conditional: check its gate, name its lose-condition, and measure the predicted mechanism.

## Algorithms, whole inputs, and APIs

### Replace the algorithm or maintained invariant

- **Mechanism:** reduce asymptotic work, remove a scaling cliff, improve hash discrimination, or establish an invariant once instead of maintaining it incrementally.
- **Gate:** input scale reaches the costly regime; required operations match the replacement; ordering, stability, worst-case behavior, and memory needs are explicit.
- **Loses when:** constants dominate at real sizes, hashing is poor or adversarial, extra memory is unacceptable, or the old structure provides required semantics.
- **Verify:** benchmark across increasing sizes and previous limits; measure operation count, time, space, collision distribution, and end-to-end impact.

### Expose whole-input or bulk work

- **Mechanism:** amortize calls, checks, locks, setup, decoding, and allocation; enable heap construction, graph ordering, vectorized work, or another whole-input algorithm.
- **Gate:** callers naturally possess a batch or complete input; batching latency and memory fit the workload.
- **Loses when:** work is truly online, batches delay individual results, lock hold time grows, or partial failure and ordering become awkward.
- **Verify:** specify output sizing, ordering, partial completion, errors, atomicity, and lock scope; compare scalar and bulk paths at realistic batch sizes.

### Deepen the API boundary

- **Mechanism:** keep algorithm, storage, allocation, caching, and synchronization changes behind a narrow interface; remove guarantees callers do not need.
- **Gate:** caller requirements are known and a stable encapsulation boundary exists.
- **Loses when:** a narrowed interface hides needed control or removing an established guarantee breaks users.
- **Verify:** audit callers for ownership, pointer/iterator stability, ordering, error detail, concurrency, and incremental-update requirements.

### Accept views, workspace, or precomputed context

- **Mechanism:** reuse caller knowledge or storage to avoid copies, allocations, time queries, parsing, or classification.
- **Gate:** the caller already has an equivalent value or suitable storage; the callee need not retain ownership.
- **Loses when:** a view dangles, workspace aliases a later mutation, context becomes stale, or parameters spread low-level concerns through callers.
- **Verify:** state lifetime, freshness, mutation, thread-safety, and retention contracts; test delayed use and oversized inputs.

### Place synchronization by typical use

- **Mechanism:** keep general-purpose types externally synchronized so unshared callers avoid locking, or internalize synchronization when shared access is the normal case and the module should own future sharding.
- **Gate:** concurrency expectations are a durable API contract rather than an observation about current callers.
- **Loses when:** external locking is omitted by callers, internal locking duplicates caller locks, or synchronization policy leaks through the interface.
- **Verify:** audit every caller and documented contract; measure uncontended overhead and contended behavior; keep synchronization changes behind the module boundary.

## Avoid work

### Delete or reject work early

- **Mechanism:** remove work with no required outcome, or use a cheap conservative discriminator before expensive parsing, hashing, traversal, formatting, allocation, or I/O.
- **Gate:** the outcome is unnecessary or the discriminator is cheaper and selective; false negatives are impossible.
- **Loses when:** the guard runs on nearly every case without skipping work, summary state becomes inconsistent, or deleted diagnostics were operationally required.
- **Verify:** measure skip rate and guard cost; test boundary cases; preserve a complete fallback. Conservative false positives may fall back.

### Precompute or hoist invariants

- **Mechanism:** move stable derivation from each item or iteration to construction, initialization, a module boundary, or an outer loop.
- **Gate:** inputs remain stable for the reuse period and setup amortizes over enough uses.
- **Loses when:** metadata becomes stale, initialization or memory grows, pointer validity changes inside the loop, or the compiler already performs the transformation.
- **Verify:** name ownership and invalidation; inspect assembly when compiler behavior matters; measure setup and steady-state effects.

### Defer or reorder work

- **Mechanism:** compute on first demand, shrink eager provisioning, or run the stage most likely to eliminate downstream work first.
- **Gate:** many operations never need the result; delayed latency is acceptable; reordering preserves semantics.
- **Loses when:** demand is frequent, lazy work repeats, miss latency is critical, growth becomes common, or the new first stage has weak elimination power.
- **Verify:** measure demand probability, miss latency, growth, and expected total CPU/I/O—not merely stage size.

### Cache repeated derivations

- **Mechanism:** reuse an expensive parsed or computed result under a stable identity.
- **Gate:** reuse is frequent; identity, lifetime, synchronization, invalidation, and memory bounds are defined.
- **Loses when:** hit rate is low, keys collide or become stale, locking dominates, entries retain too much memory, or invalidation complexity exceeds recomputation.
- **Verify:** measure hit/miss rate, lookup and lock cost, retained memory, eviction/invalidation behavior, and miss-path latency.

### Specialize a common subset

- **Mechanism:** replace general parsing, formatting, matching, dispatch, error wrapping, or container behavior with a narrower common path and general fallback.
- **Gate:** the subset is common, stable, explicitly bounded, and semantically equivalent.
- **Loses when:** code paths drift, rare values dominate, duplicated logic grows, or a wider fast path increases code and instruction-cache pressure.
- **Verify:** differential-test against the generic path at boundaries; benchmark common and fallback cases plus emitted code. Test both broader and narrower fast-path boundaries.

### Budget observability

- **Mechanism:** remove unused telemetry, gate logging, hoist enablement checks, sample events, or defer statistics.
- **Gate:** the retained signal still supports operations, debugging, and incident response.
- **Loses when:** sampling biases the data, configuration must change within an operation, or reduced detail hides failures.
- **Verify:** inventory consumers, preserve required alerts and diagnostics, measure telemetry cost and statistical quality, and state the accepted information loss.

## Representation, allocation, and locality

### Compact and arrange hot data

- **Mechanism:** narrow fields, reduce padding, co-locate fields read together, separate hot/cold and read-only/mutable data, or encapsulate packed storage.
- **Gate:** object population or cache footprint is material; value bounds and access groupings are known.
- **Loses when:** packing adds decode cost or under-alignment, compact mutable fields create false sharing, or indirection makes common access worse.
- **Verify:** measure bytes, cache lines, misses, bandwidth, alignment, and contended writes. Reserve bit packing for a tested module with material savings.

### Use dense or bounded-domain representations

- **Mechanism:** replace maps or sets with arrays, vectors, bitsets, matrices, or dense IDs.
- **Gate:** the key domain is bounded and sufficiently dense; sentinel and index semantics are valid.
- **Loses when:** the domain is huge or sparse, bounds can grow, or ordered/sparse operations are required.
- **Verify:** enforce bounds; measure occupancy, memory, lookup, iteration, and set-operation costs at real densities.

### Use contiguous, batched, or indexed storage

- **Mechanism:** replace per-element nodes and pointers with flat/chunked storage and smaller indices.
- **Gate:** element count fits the index width; relocation and index invalidation are manageable; node stability is not required.
- **Loses when:** mutation invalidates handles, values are expensive to move, stable addresses are contractual, or chunk slack dominates.
- **Verify:** audit handle lifetime and mutation; measure allocation count, bytes, cache misses, and traversal.

### Reduce allocation lifecycle work

- **Mechanism:** avoid unnecessary allocations; reserve expected capacity; reuse scratch objects; allocate scope-bounded small objects on the stack; use static/shared immutable defaults with oversized fallback.
- **Gate:** expected sizes and reset semantics are known; lifetime and concurrency are safe.
- **Loses when:** stack frames grow too large, shared state is mutable, reserve overprovisions, or reused containers retain a pathological high-water mark.
- **Verify:** distinguish allocation count, allocated bytes, initialization, destruction/GC, and retained capacity. Reconstruct reused storage periodically when measured retention justifies it.

### Use inline storage or arenas

- **Mechanism:** keep usually-small collections inside their owner, or allocate many similarly lived subobjects from shared chunks.
- **Gate:** cardinality or lifetime distributions match the representation.
- **Loses when:** inline elements enlarge every owner, collections usually overflow, short-lived values enter a long-lived arena, or bulk release retains too much memory.
- **Verify:** measure cardinality and lifetime distributions, object size, fallback frequency, allocation count, locality, and peak/steady memory.

### Avoid copying and movement

- **Mechanism:** move consumed values, borrow stable objects, sort indices, serialize into caller scratch, or choose an algorithm without internal copies.
- **Gate:** ownership can transfer or the owner outlives every borrow; ordering semantics remain correct.
- **Loses when:** sources are needed after a move, owners relocate, scratch-backed views escape, or replacing stable operations changes observable order.
- **Verify:** test lifetime and aliasing; count copied bytes and allocations; state whether stable ordering is required.

### Choose flat or nested hierarchy from repetition

- **Mechanism:** flatten nested maps to remove intermediate allocations and lookups, or retain nesting to store a large repeated prefix once.
- **Gate:** compound-key repetition and access grouping are measured.
- **Loses when:** flattening duplicates large prefixes or nesting adds many tiny maps and pointer traversals.
- **Verify:** measure key duplication, allocation count, bytes, and grouped versus random access. Neither shape is a default.

## Static code and compiler behavior

### Shrink emitted code

- **Mechanism:** keep a tiny common path inline; move failure, allocation, registration, and uncommon work out of line; share type-independent template machinery; replace nonvaluable compile-time dimensions with runtime arguments; batch repeated container operations. When call overhead and emitted footprint are both material, test a tiny discriminator and common action with a shared out-of-line fallback rather than assuming that more or less inlining wins.
- **Gate:** call-site or instantiation duplication is material and specialization provides little speed benefit.
- **Loses when:** added calls or runtime branches land on a genuinely hot path, or sharing blocks useful optimization.
- **Verify:** measure symbols, call-site bytes, binary size, build/link time, hot and fallback runtime, and instruction-cache counters where available.

### Assist the compiler

- **Mechanism:** expose stable pointers or locals, reduce aliasing uncertainty, isolate cold paths, hand-unroll a proven loop, or use wide/hardware-specific operations.
- **Gate:** profiles identify the routine and annotated assembly shows a compiler miss.
- **Loses when:** code size grows, safety or portability weakens, compiler versions change, or manual code blocks vectorization.
- **Verify:** inspect generated code before and after; benchmark multiple architectures/builds where supported; keep bounds and page-safety proofs explicit.

## Concurrency and coordination

### Parallelize independent batches

- **Mechanism:** partition independent work, schedule batches, and join results to overlap execution.
- **Gate:** spare CPU or execution resources exist; memory bandwidth and downstream resources are not saturated; results combine safely.
- **Loses when:** task dispatch dominates, bandwidth saturates, contention rises, or aggregate CPU cost is unacceptable.
- **Verify:** compare wall time and aggregate CPU across worker counts and realistic load; include saturated cases and error/join behavior.

### Amortize locks or shorten critical sections

- **Mechanism:** acquire once for a compound operation, or snapshot protected state and move remote work, allocation, pointer traversal, and destructor work outside the lock.
- **Gate:** atomicity permits the change; longer batching does not increase contention; copied state remains valid.
- **Loses when:** lock hold time grows, moved work observes stale state, or hidden callees/destructors still serialize the path.
- **Verify:** measure acquisition count, hold time, wait time, and cache/TLB work separately; inspect full callee and destructor lifetimes.

### Shard contended state

- **Mechanism:** partition state and locks by a stable key so independent operations proceed concurrently.
- **Gate:** no cross-shard invariant requires atomic global updates; keys distribute evenly.
- **Loses when:** workloads skew, global operations dominate, shard selection consumes hash entropy needed downstream, or memory/complexity grows.
- **Verify:** audit invariants and hash-bit reuse; measure per-shard load, wall time, aggregate CPU, and global-operation cost.

### Repair false sharing

- **Mechanism:** place independently mutated fields on separate cache lines.
- **Gate:** coherence evidence shows unrelated threads repeatedly invalidate a shared line.
- **Loses when:** padding enlarges many objects or separates fields commonly read together.
- **Verify:** measure coherence/cache events and object memory before and after; use target-platform cache-line information.

### Remove scheduling handoffs or add pipeline buffering

- **Mechanism:** run small work inline instead of dispatching it, or buffer a producer/consumer channel to permit overlap.
- **Gate:** dispatch cost is material or rendezvous is unintentionally serializing pipeline stages; backpressure semantics are understood.
- **Loses when:** inline work blocks a latency-sensitive caller, buffers increase memory/staleness, or unbounded production overwhelms consumers.
- **Verify:** benchmark the crossover threshold, context switches, queue depth, latency distribution, memory, and backpressure.

### Use lock-free structures

- **Mechanism:** remove conventional read-side locking with a proven high-level concurrent structure.
- **Gate:** workload matches the structure and memory ordering, lifetime, epochs/hazards, and reclamation are designed.
- **Loses when:** writes are frequent, retries spin under contention, reclamation stalls, or direct atomics make correctness unauditable.
- **Verify:** use established abstractions; test concurrent schedules; measure retries, tail latency, memory retention, and reclamation progress.

## Bulk instructions and formats

### Process several values per operation

- **Mechanism:** share tags or setup, use SIMD, perform wide loads/stores with safe fixup, or co-design a grouped encoding and decoder.
- **Gate:** items are regular, volume amortizes setup, alignment and boundary safety are established, and format compatibility is controlled.
- **Loses when:** tails dominate, architecture support differs, wide access can cross unsafe boundaries, or the new format fragments compatibility.
- **Verify:** prove allocation/page bounds, test tails and all alignments, benchmark realistic group sizes, and keep scalar fallback where required.
